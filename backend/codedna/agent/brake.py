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
from uuid import uuid4

from codedna.git_analysis.git import WORKTREE, resolve_repository
from codedna.selection import SelectionError


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
          python_command: list[str] | None = None, allow_build: bool = False) -> dict:
    """Run the planned tests and return one verdict. Executes project code."""
    from codedna.plugins.languages import run_tests
    from codedna.test_history.recording import ignore_outputs, record_run

    if not allow_build:
        raise SelectionError("check runs the project's build; pass allow_build=True to consent")
    repo = resolve_repository(repo_path)
    planned = plan(repo, base=base, head=head, risk_target=risk_target, must_run=must_run,
                   language=language, method=method)
    tests = planned["must_run"]
    if not tests:
        if planned["skipped"]:
            message = (f"validated history: none of {planned['total_tests']} test class(es) "
                       "needs to run for this change; nothing was run")
            verdict = _verdict("nothing_to_run", message)
        else:
            verdict = _verdict("no_tests", "the build runs no tests here; nothing was checked")
        return {**verdict, "plan": planned, "results": None, "output_dir": None,
                "recording": None}
    ignore_outputs(repo)
    output = repo / ".codedna/runs" / uuid4().hex
    options = {"timeout": timeout}
    if maven_command:
        options["maven_command"] = maven_command
    if gradle_command:
        options["gradle_command"] = gradle_command
    if python_command:
        options["python_command"] = python_command
    run, _ = run_tests(repo, planned["head_commit"], output, allow_build=True,
                              selected_tests=tests, **options)
    verdict = _run_verdict(tests, run)
    recording = None
    if not planned["skipped"]:  # a whole-suite run is project history (D-053)
        recording = record_run(repo, run, expected_tests=tests)
    return {**verdict, "plan": planned, "results": run.to_dict(), "output_dir": str(output),
            "recording": recording}


def _run_verdict(tests: list[str], run) -> dict:
    failed = sorted(t for t in tests if t in run.tests and run.tests[t].failed)
    missing = sorted(t for t in tests if t not in run.tests)
    build_errors = [code for code in run.exit_codes if code != 0]
    not_run = sorted(t for t in tests if t in run.tests and run.tests[t].status == "skipped")
    if failed:  # a failing test is decisive even if the build also reported errors
        return _verdict("blocked", f"{len(failed)} of {len(tests)} test class(es) failed",
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
