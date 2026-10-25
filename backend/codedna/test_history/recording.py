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
    repo = resolve_repository(repo_path)
    csv_path, db_path = repo / HISTORY_CSV, repo / HISTORY_DB

    def skipped(reason: str) -> dict:
        return {"recorded": False, "reason": reason, "history_csv": str(csv_path)}

    if not expected_tests:
        return skipped("no test classes were expected; nothing to record")
    missing = sorted(set(expected_tests) - set(run.tests))
    if missing:
        return skipped(f"{len(missing)} expected test class(es) have no result "
                       f"(e.g. {missing[0]}); only complete runs are recorded")
    line = set(run_git(repo, "rev-list", "--first-parent", "HEAD").split())
    if run.commit not in line:
        return skipped("the tested commit is not on the current branch's first-parent "
                       "history (e.g. uncommitted changes); it is not recorded")
    foreign = skipped(f"{HISTORY_CSV} was not written by CodeDNA's recording; "
                      "it is left unchanged")
    if csv_path.is_file() and not db_path.is_file():
        return foreign
    ignore_outputs(repo)
    with HistoryStore(db_path) as store:
        if csv_path.is_file() and _digest(csv_path) != store.get_meta(_CSV_DIGEST):
            return foreign
        mine_history(repo, store, revision="HEAD")
        store.add_run(run, SOURCE)
        dataset = build_dataset(store, repo, structural=False)
        partial = csv_path.with_name(csv_path.name + ".partial")
        dataset.to_csv(partial)
        os.replace(partial, csv_path)
        store.set_meta(_CSV_DIGEST, _digest(csv_path))
        commits = len(dataset.commits)
    return {"recorded": True, "reason": None, "history_csv": str(csv_path),
            "commit": run.commit, "commits_with_results": commits}


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()
