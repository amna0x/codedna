"""Saved test runs of a project, and adding them to its recorded history (D-057).

Every run CodeDNA starts is saved under ``.codedna/runs/<id>/results.json``.
Whole-suite runs started from the IDE are recorded as history straight away
(D-053); this module covers the rest:

* ``list_runs`` shows every saved run and whether it can be history, with the
  reason when it cannot (the same rules as D-053, ``recording.refusal``);
* ``record_saved_runs`` adds every eligible saved run to the one project
  history (``.codedna/history.db`` and ``history.csv``), e.g. runs saved by
  an older version of CodeDNA, or imported from a clone;
* ``import_run`` copies a ``results.json`` from another clone of the same
  project into this one, binding it to this repository;
* ``run_detail`` returns one saved run and its log files.

Nothing here runs a build. A saved run is evidence only if its file is valid,
it names an immutable commit of this repository, and it is complete: a
partial run never becomes "the other tests passed".
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from codedna.git_analysis.git import CodeDNAGitError, resolve_commit, resolve_repository
from codedna.plugins.languages import discover_tests
from codedna.test_history.recording import (NOT_ON_LINE, first_parent_line, ignore_outputs,
                                            record_runs, refusal)
from codedna.test_mapping.results import RESULTS_FILE, TestRunResult, save_json

RUNS = ".codedna/runs"
MAX_RUNS = 1000
_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_SHA = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")
# Runner names from the shared result model: one plugin's ("maven", "pytest")
# or several joined by "+" for a mixed repository ("maven+pytest", D-060).
_TOOL = re.compile(r"^[a-z][a-z0-9_-]*(?:\+[a-z][a-z0-9_-]*)*$")


class ProjectHistoryError(CodeDNAGitError):
    """A saved run cannot be read or used as project history."""


def load_saved_run(path: Path) -> tuple[TestRunResult, str]:
    """Read and check a saved ``results.json``; returns the run and the file's SHA-256."""
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    entries = data.get("tests", [])
    if not isinstance(entries, list) or len({x["id"] for x in entries}) != len(entries):
        raise ValueError("test outcomes must have distinct class identifiers")
    run = TestRunResult.from_dict(data)
    if not isinstance(run.commit, str) or not _SHA.fullmatch(run.commit):
        raise ValueError("run must name an immutable commit SHA")
    if not isinstance(run.repository, str) or not run.repository:
        raise ValueError("run has no repository identity")
    if not isinstance(run.tool, str) or not _TOOL.fullmatch(run.tool):
        raise ValueError("run does not name the test runner that produced it")
    if not math.isfinite(float(run.duration_seconds)) or float(run.duration_seconds) < 0:
        raise ValueError("invalid run duration")
    run.duration_seconds = float(run.duration_seconds)
    for test in run.tests.values():
        if (not isinstance(test.id, str) or not test.id
                or test.status not in ("passed", "failed", "error", "skipped")
                or not math.isfinite(float(test.time)) or float(test.time) < 0):
            raise ValueError("invalid test outcome or duration")
        test.time = float(test.time)
    if (not isinstance(run.exit_codes, list)
            or any(type(code) is not int for code in run.exit_codes)):
        raise ValueError("invalid build exit codes")
    return run, hashlib.sha256(raw).hexdigest()


def _same_repository(run: TestRunResult, repo: Path) -> bool:
    try:
        return Path(run.repository).resolve() == repo
    except OSError:
        return False


def _scan(repo: Path) -> tuple[list[dict], dict[str, TestRunResult], bool]:
    """Saved runs, oldest first, with what could be read of each."""
    paths = sorted((repo / RUNS).glob(f"*/{RESULTS_FILE}"), key=lambda p: p.stat().st_mtime_ns)
    truncated = len(paths) > MAX_RUNS
    records, loaded = [], {}
    for path in paths[-MAX_RUNS:]:
        if not _ID.fullmatch(path.parent.name):
            continue
        item = {"id": path.parent.name, "commit": None, "tests": 0, "failures": 0,
                "duration_seconds": 0.0, "result_path": path.relative_to(repo).as_posix(),
                "recorded_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                "candidate": False, "reason": None}
        try:
            run, digest = load_saved_run(path)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            item["reason"] = f"unreadable saved run: {exc}"
        else:
            item.update(commit=run.commit, tests=len(run.tests), failures=len(run.failing_tests),
                        duration_seconds=run.duration_seconds, sha256=digest)
            if _same_repository(run, repo):
                loaded[item["id"]] = run
            else:
                item["reason"] = ("saved for another repository; import it explicitly "
                                  "to use a clone's results here")
        records.append(item)
    return records, loaded, truncated


def _check(repo: Path, records: list[dict], loaded: dict[str, TestRunResult]):
    """Mark each record with the D-053 rules; returns (run, expected tests) pairs that pass."""
    line = first_parent_line(repo)
    expected: dict[str, list[str]] = {}
    eligible = []
    for item in records:
        run = loaded.get(item["id"])
        if run is None:
            continue
        if run.commit not in line:
            item["reason"] = NOT_ON_LINE
            continue
        if run.commit not in expected:
            expected[run.commit] = [t.id for t in discover_tests(repo, run.commit).tests
                                    if t.runs_by_default]
        item["reason"] = refusal(run, expected[run.commit], line)
        item["candidate"] = item["reason"] is None
        if item["candidate"]:
            eligible.append((item, run, expected[run.commit]))
    return eligible


def list_runs(repo_path: str | Path) -> dict:
    """Every saved run (newest first) and whether it can become history."""
    repo = resolve_repository(repo_path)
    records, loaded, truncated = _scan(repo)
    _check(repo, records, loaded)
    history = repo / ".codedna/history.csv"
    return {"repository": str(repo), "runs": records[::-1],
            "candidate_runs": sum(r["candidate"] for r in records),
            "candidate_commits": len({r["commit"] for r in records if r["candidate"]}),
            "history_csv": str(history) if history.is_file() else None,
            "warnings": [f"Only the latest {MAX_RUNS} saved runs are listed."] if truncated else [],
            "note": "A run can be history when every test class the build runs by default at "
                    "its commit has a result and the commit is on the current branch. "
                    "Runs with failing tests count; partial runs never do."}


def record_saved_runs(repo_path: str | Path) -> dict:
    """Add every eligible saved run to the project history (one rebuild, oldest first)."""
    repo = resolve_repository(repo_path)
    records, loaded, truncated = _scan(repo)
    eligible = _check(repo, records, loaded)
    report = record_runs(repo, [(run, expected) for _, run, expected in eligible])
    for (item, _, _), result in zip(eligible, report["runs"]):
        item["candidate"] = result["recorded"]
        item["reason"] = result["reason"]
    return {"repository": str(repo), "recorded_runs": report["recorded"],
            "commits_with_results": report["commits_with_results"],
            "history_csv": report["history_csv"],
            "skipped": [{"id": r["id"], "reason": r["reason"]} for r in records
                        if r["reason"] is not None],
            "warnings": [f"Only the latest {MAX_RUNS} saved runs were considered."] if truncated else [],
            "note": "Only complete saved runs were added; no tests were executed. "
                    "The risk gate still has to validate this history before it is used."}


def run_detail(repo_path: str | Path, run_id: str) -> dict:
    repo = resolve_repository(repo_path)
    if not isinstance(run_id, str) or not _ID.fullmatch(run_id):
        raise ProjectHistoryError("invalid saved run identifier")
    folder = repo / RUNS / run_id
    try:
        run, _ = load_saved_run(folder / RESULTS_FILE)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ProjectHistoryError(f"cannot read saved run: {exc}") from exc
    if not _same_repository(run, repo):
        raise ProjectHistoryError("saved run belongs to another repository")
    logs = [p.relative_to(repo).as_posix() for p in sorted((folder / "logs").glob("*.log"))][:50]
    return {"id": run_id, "results": run.to_dict(), "logs": logs,
            "result_path": (folder / RESULTS_FILE).relative_to(repo).as_posix()}


def import_run(repo_path: str | Path, source: str | Path) -> dict:
    """Copy a ``results.json`` (file or run folder) into this repository's saved runs.

    The commit must exist here, so results from another project fail; the
    original path and file hash are kept in ``record.json``. Importing does not
    record history by itself (``record_saved_runs`` does).
    """
    repo = resolve_repository(repo_path)
    source = Path(source).expanduser()
    if source.is_dir():
        source = source / RESULTS_FILE
    try:
        run, digest = load_saved_run(source)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ProjectHistoryError(f"cannot import {RESULTS_FILE}: {exc}") from exc
    commit = resolve_commit(repo, run.commit)
    if commit.lower() != run.commit.lower():
        raise ProjectHistoryError("the run's commit is not in this repository")
    original = run.repository
    run.repository = str(repo)
    ignore_outputs(repo)
    folder = repo / RUNS / uuid4().hex
    save_json(run.to_dict(), folder / RESULTS_FILE)
    save_json({"kind": "explicit-import", "source": str(source.resolve()),
               "source_sha256": digest, "source_repository": original,
               "imported_at": datetime.now(timezone.utc).isoformat()}, folder / "record.json")
    return {"id": folder.name, "commit": run.commit, "tests": len(run.tests),
            "failures": len(run.failing_tests),
            "result_path": (folder / RESULTS_FILE).relative_to(repo).as_posix()}
