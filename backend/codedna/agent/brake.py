"""Test brake for AI coding agents (D-059).

An agent edits the working tree and then asks two questions before it says
it is done:

* ``plan`` — which tests must run for this change, and how risky is skipping
  the others? This is the product's own risk recommendation (D-041) with the
  project's must-run policy (D-050): without validated history every test is
  listed, so the brake never skips on a guess. The labelled structural
  dependency plan is returned separately and can only broaden required tests.
* ``check`` — run exactly those tests and give one verdict:

  - ``passed``: every listed test class has a result and none failed;
  - ``blocked``: at least one listed test class failed;
  - ``incomplete``: some listed class has no result, the build exited with
    an error or timed out, or a listed class was skipped, so nothing can
    be concluded;
  - ``nothing_to_run``: validated history says no test needs to run for this
    change (the skipped tests and the estimated risk are in the plan);
  - ``no_tests``: the project has no tests the build runs, so nothing was
    checked.

  Running tests executes project code, so ``check`` needs
  ``allow_build=True``; the MCP server passes it only when the person
  started it with ``--allow-build`` for one repository. An agent cannot turn
  that on.

This module is language-neutral: tests are discovered, chosen and run by the
language plugin (Java first).
"""

from __future__ import annotations

from pathlib import Path
from time import monotonic
from uuid import uuid4

from codedna.git_analysis.git import reuse_git_validation
from codedna.dependency_graph.cache import reuse_parse_cache
from codedna.git_analysis.git import WORKTREE, resolve_repository
from codedna.selection import SelectionError


@reuse_git_validation
@reuse_parse_cache
def plan(repo_path: str | Path, *, base: str = "HEAD", head: str = WORKTREE,
         risk_target: float = 0.05, must_run: list[str] | None = None,
         language: str | None = None, method: str = "b10") -> dict:
    """Tests that must run for BASE..HEAD (default: uncommitted changes)."""
    from codedna.selection.live import recommend

    result = recommend(resolve_repository(repo_path), base, head, risk_target=risk_target,
                       must_run=must_run, language=language, method=method)
    from codedna.selection import select_tests

    # Both views use the recommendation's immutable revisions, even if an
    # agent edits WORKTREE again while this request is in progress.
    structural = select_tests(result["repository"], result["base_commit"],
                              result["head_commit"], "dependency").to_dict()
    selected = {item["test"]: {**item, "reasons": list(item["reasons"])}
                for item in result["selected"]}
    added = []
    for item in structural["selected"]:
        test = item["test"]
        if test not in selected:
            selected[test] = {**item, "reasons": list(item["reasons"])}
            added.append(test)
        else:
            selected[test]["reasons"].extend(
                reason for reason in item["reasons"] if reason not in selected[test]["reasons"])
    remaining = [test for test in result["skipped"] if test not in selected]
    risk = {**result["risk"], "reasons": list(result["risk"]["reasons"])}
    validated = risk["status"] == "validated_history"
    if added and validated:
        # More tests cannot increase skip risk. The original estimate is a
        # conservative bound; it is not silently relabelled as a new fit.
        if not remaining:
            risk["estimated_skip_risk"] = 0.0
        else:
            risk["estimate_is_conservative"] = True
            risk["reasons"].append(
                "Structural tests broadened the risk plan; its original skip-risk "
                "estimate is a conservative bound for the remaining tests.")
    result = {**result, "selected": list(selected.values()), "skipped": remaining, "risk": risk}
    warnings = list(dict.fromkeys([*result["warnings"], *structural["warnings"]]))
    return {
        "repository": result["repository"],
        "base_commit": result["base_commit"],
        "head_commit": result["head_commit"],
        "structural_plan": {**structural, "note": "structural only, no probability"},
        "must_run": [item["test"] for item in result["selected"]],
        "reasons": {item["test"]: item["reasons"] for item in result["selected"]},
        "skipped": result["skipped"],
        "total_tests": result["total_tests"],
        "pinned_by_policy": result["policy"]["pinned"] if result.get("policy") else [],
        "risk": {
            "status": risk["status"],
            "method": risk.get("method", method),
            "target": risk["target"],
            "estimated_skip_risk": risk["estimated_skip_risk"],
            "reasons": risk["reasons"],
            "objective": "omit_any_failing_test",
            "note": ("Historical evidence supports a selection rule, not a guarantee for "
                     "this change or a proof that the patch is correct."),
            "audit": _audit_summary(risk),
            **({"conformal": risk["conformal"]} if risk.get("conformal") else {}),
            **({"estimate_is_conservative": True} if risk.get("estimate_is_conservative") else {}),
        },
        "summary": _plan_summary(result, validated),
        "warnings": warnings,
    }


def check(repo_path: str | Path, *, base: str = "HEAD", head: str = WORKTREE,
          risk_target: float = 0.05, must_run: list[str] | None = None,
          timeout: int = 1800, language: str | None = None, method: str = "b10",
          maven_command: list[str] | None = None,
          gradle_command: list[str] | None = None,
          python_command: list[str] | None = None, allow_build: bool = False,
          shadow: bool = False, attempts: int = 1) -> dict:
    """Run the planned tests and return one verdict. Executes project code."""
    from codedna.plugins.languages import run_tests
    from codedna.test_history.recording import ignore_outputs, record_run

    if not allow_build:
        raise SelectionError("check runs the project's build; pass allow_build=True to consent")
    if not isinstance(shadow, bool):
        raise SelectionError("shadow must be a boolean")
    if isinstance(attempts, bool) or not isinstance(attempts, int) or not 1 <= attempts <= 3:
        raise SelectionError("attempts must be an integer between 1 and 3")
    started = monotonic()
    repo = resolve_repository(repo_path)
    planned = plan(repo, base=base, head=head, risk_target=risk_target, must_run=must_run,
                   language=language, method=method)
    tests = planned["must_run"]
    if shadow:
        tests = sorted(set(tests) | set(planned["skipped"]))
        if len(tests) != planned["total_tests"]:
            raise SelectionError("shadow requires a complete discovered test inventory")
    analysis_seconds = monotonic() - started
    if not tests:
        if planned["skipped"]:
            message = (f"validated history: none of {planned['total_tests']} test class(es) "
                       "needs to run for this change; nothing was run")
            verdict = _verdict("nothing_to_run", message)
        else:
            verdict = _verdict("no_tests", "the build runs no tests here; nothing was checked")
        return {**verdict, "plan": planned, "results": None, "output_dir": None,
                "recording": None, "cost": {"analysis_seconds": analysis_seconds,
                    "execution_seconds": 0.0, "total_seconds": monotonic() - started,
                    "scope": "inside_check_no_project_execution"}}
    ignore_outputs(repo)
    output = repo / ".codedna/runs" / uuid4().hex
    options = {"timeout": timeout}
    if maven_command:
        options["maven_command"] = maven_command
    if gradle_command:
        options["gradle_command"] = gradle_command
    if python_command:
        options["python_command"] = python_command
    execution_started = monotonic()
    run, _ = run_tests(repo, planned["head_commit"], output, allow_build=True,
                              selected_tests=None if shadow else tests, **options)
    execution_seconds = monotonic() - execution_started
    observed_tests = sorted(set(tests) | set(run.tests)) if shadow else tests
    verdict = _run_verdict(observed_tests, run)
    runs = [run]
    attempt_reports = [{"verdict": verdict, "results": run.to_dict(), "output_dir": str(output)}]
    repeat_error = None
    for index in range(1, attempts):
        remaining = int(timeout - (monotonic() - execution_started))
        if remaining < 1:
            repeat_error = "repeat budget exhausted; remaining attempts were not executed"
            break
        next_output = repo / ".codedna/runs" / uuid4().hex
        try:
            repeated, _ = run_tests(repo, planned["head_commit"], next_output, allow_build=True,
                selected_tests=None if shadow else tests, **{**options, "timeout": remaining})
        except (OSError, ValueError, RuntimeError) as exc:
            repeat_error = str(exc)[:1000]
            break
        required = sorted(set(tests) | set(repeated.tests)) if shadow else tests
        current = _run_verdict(required, repeated)
        runs.append(repeated)
        attempt_reports.append({"verdict": current, "results": repeated.to_dict(), "output_dir": str(next_output)})
    if shadow:
        # Discovery can miss generated/dynamic tests. Once any full run observes
        # a test, require its result in every repeat instead of hiding dropout.
        observed_tests = sorted(set(tests).union(*(set(r.tests) for r in runs)))
        for item, observed_run in zip(attempt_reports, runs):
            item["verdict"] = _run_verdict(observed_tests, observed_run)
        verdict = attempt_reports[0]["verdict"]
    failed = sorted({t for item in attempt_reports for t in item["verdict"].get("failed", [])})
    signatures = [{"tests": {t: outcome.status for t, outcome in r.tests.items()},
                   "exit_codes": list(r.exit_codes)} for r in runs]
    unstable = any(s != signatures[0] for s in signatures[1:])
    if attempts > 1:
        if failed:
            verdict = _verdict("blocked", "A test failed in at least one attempt; passing repeats do not erase failures", failed=failed)
        elif repeat_error or any(item["verdict"]["verdict"] != "passed" for item in attempt_reports):
            verdict = _verdict("incomplete", "Repeated execution was incomplete; inspect every attempt")
    execution_seconds = monotonic() - execution_started
    recording = None
    if (shadow or not planned["skipped"]) and (attempts == 1 or (
            not unstable and not repeat_error and not any(
            item["verdict"]["verdict"] == "incomplete" for item in attempt_reports))):
        recording = record_run(repo, run, expected_tests=tests)
    elif (shadow or not planned["skipped"]) and attempts > 1:
        recording = {"recorded": False, "reason": "unstable or incomplete repeated execution is not training history"}
    result = {**verdict, "plan": planned, "results": run.to_dict(), "output_dir": str(output),
              "recording": recording, "cost": {"analysis_seconds": analysis_seconds,
                  "execution_seconds": execution_seconds, "total_seconds": monotonic() - started,
                  "execution_attempts": len(runs),
                  "scope": "inside_check_includes_planning_execution_and_recording_not_server_startup",
                  "note": "Measured elapsed cost of this operation, not counterfactual savings or estimated per-class duration sums."}}
    if attempts > 1:
        result["repeat_evidence"] = {"requested": attempts, "completed": len(runs),
            "unstable_observed": unstable, "attempts": attempt_reports, "error": repeat_error,
            "note": "Disagreement indicates observed instability; it does not prove which cause is responsible. No failing attempt is erased."}
    if shadow:
        result["shadow"] = {
            "mode": "full_suite_observation", "skipping_authorized": False,
            "recommended_tests": list(planned["must_run"]), "expected_tests": tests,
            "observed_failures_outside_recommendation": sorted({
                t for r in runs for t, outcome in r.tests.items()
                if outcome.failed and t not in planned["must_run"]}),
            "missing_results": sorted({t for r in runs for t in observed_tests if t not in r.tests}),
            "skipped_by_build": sorted({t for r in runs for t in tests if t in r.tests and r.tests[t].status == "skipped"}),
            "exit_codes": [code for r in runs for code in r.exit_codes],
            "analysis_seconds": analysis_seconds, "execution_seconds": execution_seconds,
            "total_seconds": monotonic() - started,
            "note": "Observed failures are evidence, not a validated miss probability. Missing/skipped results and build errors limit interpretation. Full-suite cost does not measure the counterfactual selected-run cost.",
        }
    return result


def _run_verdict(tests: list[str], run) -> dict:
    # Some build configurations execute additional tests despite the requested
    # selection. An observed failure still blocks, even outside that selection.
    failed = sorted(t for t, outcome in run.tests.items() if outcome.failed)
    missing = sorted(t for t in tests if t not in run.tests)
    build_errors = [code for code in run.exit_codes if code != 0]
    not_run = sorted(t for t in tests if t in run.tests and run.tests[t].status == "skipped")
    if failed:  # a failing test is decisive even if the build also reported errors
        return _verdict("blocked", f"{len(failed)} observed test class(es) failed",
                        failed=failed)
    if missing:
        return _verdict("incomplete", f"{len(missing)} of {len(tests)} test class(es) have no "
                        "result; the build may have stopped early", missing=missing,
                        build_warnings=run.warnings)
    if build_errors:
        return _verdict("incomplete", "the build exited with an error or timed out "
                        f"(exit codes {run.exit_codes}); the results may be partial",
                        build_warnings=run.warnings)
    if not_run:
        return _verdict("incomplete", f"{len(not_run)} of {len(tests)} required test "
                        "class(es) or module(s) were skipped by the build; required checks "
                        "remain unverified", skipped_by_build=not_run)
    return _verdict("passed", f"all {len(tests)} required test class(es) or module(s) passed",
                    skipped_by_build=[])


def _verdict(name: str, message: str, **details) -> dict:
    return {"verdict": name, "message": message, **details}


def _plan_summary(result: dict, validated: bool) -> str:
    selected, total = len(result["selected"]), result["total_tests"]
    if total == 0:
        return "No tests found that the build runs; a check cannot verify this change."
    if validated:
        risk = result["risk"]["estimated_skip_risk"]
        crc = result["risk"].get("conformal")
        conservative = result["risk"].get("estimate_is_conservative", False)
        estimate_label = "conservative model skip-risk bound" if conservative else "estimated skip risk"
        if crc:
            return (f"Run {selected} of {total} test classes. Conformal stop: at most "
                    f"{crc['alpha']:.0%} of this project's {crc['failing_audit_commits']} past "
                    f"failing commits would have missed a failure (corrected bound "
                    f"{crc['corrected_bound']:.1%}); {estimate_label} {risk:.1%}.")
        if conservative:
            return (f"Run {selected} of {total} test classes. Conservative bound on the model's "
                    f"skip-risk estimate after structural broadening: {risk:.1%}.")
        return (f"Run {selected} of {total} test classes. Estimated chance that a skipped "
                f"class would fail: {risk:.1%} (validated on this project's history).")
    return (f"Run all {total} test classes: skipping is not validated for this project "
            f"({result['risk']['reasons'][0] if result['risk']['reasons'] else 'no reason given'}).")


def _audit_summary(risk: dict) -> dict | None:
    """Expose the active method's evidence without mixing all/failing denominators."""
    if risk.get("method") == "crc":
        crc = risk.get("conformal")
        if crc is None:
            return None
        return {"method": "crc", "denominator": "failing_audit_commits",
                "sample_size": crc["failing_audit_commits"],
                "observed_miss_rate": crc["audit_miss_rate"],
                "corrected_expected_risk_bound": crc["corrected_bound"],
                "assumption": "past and future failing commits are exchangeable",
                "future_guarantee": False}
    validation = risk.get("validation")
    if validation is None:
        return None
    return {"method": "wilson_evidence_screen", "denominator": "all_audit_commits",
            "sample_size": validation["commits"],
            "failing_commits": validation["failing_commits"],
            "observed_miss_rate": validation["observed_miss_rate"],
            "historical_miss_upper_bound": validation["miss_upper_bound"],
            "accepted": validation["accepted"], "future_guarantee": False}
