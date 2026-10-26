"""Record full-suite runs as project test history, so risk selection can turn on (D-053).

The live risk gate (D-041) needs complete, chronological outcomes of the
project's own tests. Most projects have no such record, so every run of the
whole suite that CodeDNA starts is kept:

1. the result is stored in ``.codedna/history.db`` (first-parent history is
   mined again, so new commits are included);
2. ``.codedna/history.csv`` is rebuilt from the database (no structural
   replay; the live predictor does not use those features).

A run is recorded only when it is real, complete evidence:

* its commit is on HEAD's first-parent line (not a working-tree snapshot and
  not another branch);
* every expected test class has a result, so the build did not stop early.

Partial (selected) runs are never recorded: the gate audits complete
outcomes, and a skipped test's outcome is unknown. A ``history.csv`` that
CodeDNA did not write here (e.g. the HikariCP demo history) is never
overwritten.

CodeDNA's outputs are kept out of Git with a self-ignoring
``.codedna/.gitignore`` (written only if the project has none), so they never
show up as the user's uncommitted changes; a committed ``policy.toml`` is
unaffected.
"""

from __future__ import annotations

import os
from hashlib import sha256
from pathlib import Path

from codedna.git_analysis.git import resolve_repository, run_git
from codedna.test_history.features import build_dataset
from codedna.test_history.mining import mine_history
from codedna.test_history.store import HistoryStore
from codedna.test_mapping.results import TestRunResult

HISTORY_DB = ".codedna/history.db"
HISTORY_CSV = ".codedna/history.csv"
SOURCE = "codedna-run"
_CSV_DIGEST = "recorded_csv_sha256"
OUTPUTS = ("runs/", "history.db", "history.csv", "history.csv.partial")


def ignore_outputs(repo: Path) -> None:
    """Write ``.codedna/.gitignore`` for CodeDNA's outputs unless one exists."""
    path = repo / ".codedna/.gitignore"
    if not path.exists():
        path.parent.mkdir(exist_ok=True)
        lines = ["# CodeDNA outputs (this file ignores itself)", "/.gitignore",
                 *(f"/{name}" for name in OUTPUTS)]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def record_run(repo_path: str | Path, run: TestRunResult, *, expected_tests: list[str]) -> dict:
    """Store ``run`` as history when it is a complete full-suite run; say why not otherwise."""
    report = record_runs(repo_path, [(run, expected_tests)])
    result = report["runs"][0]
    if result["recorded"]:
        return {"recorded": True, "reason": None, "history_csv": report["history_csv"],
                "commit": run.commit, "commits_with_results": report["commits_with_results"]}
    return {"recorded": False, "reason": result["reason"], "history_csv": report["history_csv"]}


def refusal(run: TestRunResult, expected_tests: list[str], line: set[str]) -> str | None:
    """Why ``run`` cannot be history (``None`` if it can); ``line`` is HEAD's first-parent line.

    A run with failing tests is complete evidence: Maven and Gradle exit
    non-zero when a test fails, so the exit code is not a refusal reason.
    """
    if not expected_tests:
        return "no test classes were expected; nothing to record"
    missing = sorted(set(expected_tests) - set(run.tests))
    if missing:
        return (f"{len(missing)} expected test class(es) have no result "
                f"(e.g. {missing[0]}); only complete runs are recorded")
    if run.commit not in line:
        return NOT_ON_LINE
    return None


NOT_ON_LINE = ("the tested commit is not on the current branch's first-parent "
               "history (e.g. uncommitted changes); it is not recorded")


def first_parent_line(repo: Path) -> set[str]:
    return set(run_git(repo, "rev-list", "--first-parent", "HEAD").split())


def record_runs(repo_path: str | Path, runs: list[tuple[TestRunResult, list[str]]]) -> dict:
    """Record several runs (oldest first) with one history rebuild.

    Each entry pairs a run with the test classes its build runs by default at
    that commit. A later run of the same commit replaces an earlier one.
    """
    repo = resolve_repository(repo_path)
    csv_path, db_path = repo / HISTORY_CSV, repo / HISTORY_DB
    line = first_parent_line(repo)
    results = [{"commit": run.commit, "recorded": False,
                "reason": refusal(run, expected, line)} for run, expected in runs]
    report = {"history_csv": str(csv_path), "runs": results, "recorded": 0,
              "commits_with_results": None, "reason": None}
    accepted = [run for (run, _), result in zip(runs, results) if result["reason"] is None]
    if not accepted:
        return report
    foreign = f"{HISTORY_CSV} was not written by CodeDNA's recording; it is left unchanged"
    if csv_path.is_file() and not db_path.is_file():
        return _refuse_all(report, accepted, foreign)
    ignore_outputs(repo)
    with HistoryStore(db_path) as store:
        if csv_path.is_file() and _digest(csv_path) != store.get_meta(_CSV_DIGEST):
            return _refuse_all(report, accepted, foreign)
        mine_history(repo, store, revision="HEAD")
        for run in accepted:
            store.add_run(run, SOURCE)
        dataset = build_dataset(store, repo, structural=False)
        partial = csv_path.with_name(csv_path.name + ".partial")
        dataset.to_csv(partial)
        os.replace(partial, csv_path)
        store.set_meta(_CSV_DIGEST, _digest(csv_path))
        report["commits_with_results"] = len(dataset.commits)
    for result in results:
        result["recorded"] = result["reason"] is None
    report["recorded"] = len(accepted)
    return report


def _refuse_all(report: dict, accepted: list[TestRunResult], reason: str) -> dict:
    for result in report["runs"]:
        if result["reason"] is None:
            result["reason"] = reason
    report["reason"] = reason
    return report


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()
