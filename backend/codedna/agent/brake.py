"""Test brake for AI coding agents (D-059).

An agent edits the working tree and then asks two questions before it says
it is done:

* ``plan`` — which tests must run for this change, and how risky is skipping
  the others? This is the product's own risk recommendation (D-041) with the
  project's must-run policy (D-050): without validated history every test is
  listed, so the brake never skips on a guess.
* ``check`` — run exactly those tests and give one verdict:

  - ``passed``: every listed test class has a result and none failed;
  - ``blocked``: at least one listed test class failed;
  - ``incomplete``: some listed class has no result, or the build stopped
    (a compile error, a timeout), so nothing can be concluded;
  - ``no_tests``: the project has no tests the build runs, so nothing was
    checked.

  Running tests executes project code, so ``check`` works only when the
  person started the server with ``--allow-build`` for one repository. An
  agent cannot turn that on.

This module is language-neutral: tests are discovered, chosen and run by the
language plugin (Java first).
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from codedna.git_analysis.git import WORKTREE, resolve_repository


def plan(repo_path: str | Path, *, base: str = "HEAD", head: str = WORKTREE,
         risk_target: float = 0.05, must_run: list[str] | None = None,
         language: str = "java") -> dict:
    """Tests that must run for BASE..HEAD (default: uncommitted changes)."""
    from codedna.selection.live import recommend

    result = recommend(resolve_repository(repo_path), base, head, risk_target=risk_target,
                       must_run=must_run, language=language)
    risk = result["risk"]
    validated = risk["status"] == "validated_history"
    return {
        "repository": result["repository"],
        "base_commit": result["base_commit"],
        "head_commit": result["head_commit"],
        "must_run": [item["test"] for item in result["selected"]],
        "reasons": {item["test"]: item["reasons"] for item in result["selected"]},
        "skipped": result["skipped"],
        "total_tests": result["total_tests"],
        "pinned_by_policy": result["policy"]["pinned"] if result.get("policy") else [],
        "risk": {
            "status": risk["status"],
            "target": risk["target"],
            "estimated_skip_risk": risk["estimated_skip_risk"],
            "reasons": risk["reasons"],
        },
        "summary": _plan_summary(result, validated),
        "warnings": result["warnings"],
    }


def check(repo_path: str | Path, *, base: str = "HEAD", head: str = WORKTREE,
          risk_target: float = 0.05, must_run: list[str] | None = None,
          timeout: int = 1800, language: str = "java", maven_command: list[str] | None = None,
          gradle_command: list[str] | None = None) -> dict:
    """Run the planned tests and return one verdict. Executes project code."""
    from codedna.plugins import load_plugins
    from codedna.selection import SelectionError
    from codedna.test_history.recording import ignore_outputs, record_run

    repo = resolve_repository(repo_path)
    planned = plan(repo, base=base, head=head, risk_target=risk_target, must_run=must_run,
                   language=language)
    tests = planned["must_run"]
    if not tests:
        return {**_verdict("no_tests", "the build runs no tests here; nothing was checked"),
                "plan": planned, "results": None, "output_dir": None}
    plugin = load_plugins().get(language)
    if plugin is None:
        raise SelectionError(f"language plugin {language!r} is not installed")
    ignore_outputs(repo)
    output = repo / ".codedna/runs" / uuid4().hex
    options = {"timeout": timeout}
    if maven_command:
        options["maven_command"] = maven_command
    if gradle_command:
        options["gradle_command"] = gradle_command
    run, _ = plugin.run_tests(repo, planned["head_commit"], output, allow_build=True,
                              selected_tests=tests, **options)
    failed = sorted(t for t in tests if t in run.tests and run.tests[t].failed)
    missing = sorted(t for t in tests if t not in run.tests)
    if failed:
        verdict = _verdict("blocked", f"{len(failed)} of {len(tests)} test class(es) failed",
                           failed=failed)
    elif missing:
        verdict = _verdict("incomplete", f"{len(missing)} of {len(tests)} test class(es) have "
                           "no result; the build may have stopped early", missing=missing)
    else:
        not_run = sorted(t for t in tests if run.tests[t].status == "skipped")
        note = f"; {len(not_run)} class(es) were skipped by the build" if not_run else ""
        verdict = _verdict("passed", f"all {len(tests)} planned test class(es) passed{note}",
                           skipped_by_build=not_run)
    recording = None
    if not planned["skipped"]:  # a whole-suite run is project history (D-053)
        recording = record_run(repo, run, expected_tests=tests)
    return {**verdict, "plan": planned, "results": run.to_dict(), "output_dir": str(output),
            "recording": recording}


def _verdict(name: str, message: str, **details) -> dict:
    return {"verdict": name, "message": message, **details}


def _plan_summary(result: dict, validated: bool) -> str:
    selected, total = len(result["selected"]), result["total_tests"]
    if total == 0:
        return "No tests found that the build runs; a check cannot verify this change."
    if validated:
        risk = result["risk"]["estimated_skip_risk"]
        return (f"Run {selected} of {total} test classes. Estimated chance that a skipped "
                f"class would fail: {risk:.1%} (validated on this project's history).")
    return (f"Run all {total} test classes: skipping is not validated for this project "
            f"({result['risk']['reasons'][0] if result['risk']['reasons'] else 'no reason given'}).")
