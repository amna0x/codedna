"""Project run browsing and causal history preparation, without executing builds.

Only successful build invocations covering exactly the discovered default test
classes can contribute labels. Partial, skipped, foreign and future runs remain
visible but never become assumed passes. Repeated complete runs merge through
the existing store's failure-wins policy.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from codedna.git_analysis.git import CodeDNAGitError, resolve_commit, resolve_repository, run_git
from codedna.test_history.features import build_dataset
from codedna.test_history.mining import mine_history
from codedna.test_history.store import HistoryStore
from codedna.test_mapping.discovery import discover_tests
from codedna.test_mapping.results import TestRunResult, save_json

_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_SHA = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")


class ProjectHistoryError(CodeDNAGitError):
    """A recorded run cannot be used as project history."""


def _load(path):
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
    if run.tool not in ("maven", "gradle"):
        raise ValueError("only Maven and Gradle results are supported")
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



def ensure_local_output_ignore(repo):
    """Keep untracked generated outputs out of WORKTREE snapshots, locally only."""
    try:
        run_git(repo, "check-ignore", "--quiet", "--no-index", ".codedna/")
        return
    except CodeDNAGitError:
        pass
    exclude = Path(run_git(repo, "rev-parse", "--git-path", "info/exclude").strip())
    if not exclude.is_absolute():
        exclude = repo / exclude
    exclude.parent.mkdir(parents=True, exist_ok=True)
    old = exclude.read_bytes() if exclude.exists() else b""
    rule = b"/.codedna/"
    if rule not in old.splitlines():
        with exclude.open("ab") as stream:
            stream.write((b"\n" if old and not old.endswith(b"\n") else b"")
                         + b"# CodeDNA local run/history outputs\n" + rule + b"\n")


def _reason(run, repo, ancestors):
    if Path(run.repository).resolve() != repo:
        return "Recorded for another repository; import it explicitly to bind a clone's results."
    if run.commit not in ancestors:
        return "Outside the selected BASE first-parent history window."
    if not run.exit_codes or any(run.exit_codes):
        return "Build did not complete successfully or its exit code was not recorded."
    if not run.tests:
        return "No test outcomes were recorded."
    if any(t.status == "skipped" for t in run.tests.values()):
        return "Some test classes were skipped; their outcomes are unknown."
    return None


def _context(repo_path, base, max_commits):
    if type(max_commits) is not int or not 1 <= max_commits <= 2000:
        raise ProjectHistoryError("History window must be between 1 and 2000 commits")
    repo = resolve_repository(repo_path)
    tip = resolve_commit(repo, base)
    ancestors = run_git(repo, "rev-list", "--first-parent", f"--max-count={max_commits}", tip).splitlines()
    return repo, tip, ancestors


def _scan(repo, ancestors):
    root = repo / ".codedna" / "runs"
    paths = sorted(root.glob("*/results.json"), key=lambda p: p.stat().st_mtime_ns, reverse=True)
    records, loaded = [], {}
    for path in paths[:1000]:
        if not _ID.fullmatch(path.parent.name):
            continue
        item = {"id": path.parent.name, "commit": None, "tests": 0, "failures": 0,
                "duration_seconds": 0., "recorded_at": datetime.fromtimestamp(
                    path.stat().st_mtime, timezone.utc).isoformat(),
                "result_path": path.relative_to(repo).as_posix(),
                "candidate": False, "reason": None}
        try:
            run, digest = _load(path)
            reason = _reason(run, repo, ancestors)
            item.update(commit=run.commit, tests=len(run.tests), failures=len(run.failing_tests),
                        duration_seconds=run.duration_seconds, candidate=reason is None,
                        reason=reason, sha256=digest)
            loaded[item["id"]] = run
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            item["reason"] = f"Unreadable saved run: {exc}"
        records.append(item)
    return records, loaded, len(paths) > 1000


def _complete(run, expected):
    return bool(expected) and set(run.tests) == expected


def project_history(repo_path, base, *, max_commits=500):
    repo, tip, ancestors = _context(repo_path, base, max_commits)
    records, loaded, truncated = _scan(repo, set(ancestors))
    expected = {t.id for t in discover_tests(repo, tip).tests if t.runs_by_default}
    base_ready = any(item["candidate"] and item["commit"] == tip
                     and _complete(loaded[item["id"]], expected) for item in records)
    return {"repository": str(repo), "base_commit": tip, "max_commits": max_commits,
            "commits_considered": len(ancestors), "runs": records,
            "candidate_commits": len({r["commit"] for r in records if r["candidate"]}),
            "base_has_complete_run": base_ready, "base_tests": len(expected),
            "history_csv": str(repo / ".codedna/history.csv")
            if (repo / ".codedna/history.csv").is_file() else None,
            "warnings": ["Only the latest 1000 saved runs are shown."] if truncated else [],
            "note": "Coverage is checked against statically discovered default test classes; "
                    "preparing history does not itself validate a risk estimate."}


def run_detail(repo_path, run_id):
    repo = resolve_repository(repo_path)
    if not isinstance(run_id, str) or not _ID.fullmatch(run_id):
        raise ProjectHistoryError("Invalid saved run identifier")
    folder = repo / ".codedna/runs" / run_id
    try:
        run, _ = _load(folder / "results.json")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ProjectHistoryError(f"Cannot read saved run: {exc}") from exc
    if Path(run.repository).resolve() != repo:
        raise ProjectHistoryError("Saved run belongs to another repository")
    logs = [p.relative_to(repo).as_posix() for p in sorted((folder / "logs").glob("*.log"))][:50]
    return {"id": run_id, "results": run.to_dict(), "logs": logs,
            "result_path": (folder / "results.json").relative_to(repo).as_posix()}


def import_project_run(repo_path, source):
    repo = resolve_repository(repo_path)
    source = Path(source).expanduser()
    if source.is_dir():
        source = source / "results.json"
    try:
        run, digest = _load(source)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ProjectHistoryError(f"Cannot import results.json: {exc}") from exc
    original_repository = run.repository
    run.commit = resolve_commit(repo, run.commit)
    run.repository = str(repo)  # explicit import binds another clone's path to this repo
    ensure_local_output_ignore(repo)
    folder = repo / ".codedna/runs" / uuid4().hex
    save_json(run.to_dict(), folder / "results.json")
    save_json({"kind": "explicit-import", "source": str(source.resolve()),
               "source_sha256": digest, "source_repository": original_repository,
               "imported_at": datetime.now(timezone.utc).isoformat()}, folder / "record.json")
    return {"id": folder.name, "commit": run.commit, "tests": len(run.tests),
            "failures": len(run.failing_tests), "result_path": str(folder / "results.json")}


def prepare_project_history(repo_path, base, *, max_commits=500):
    repo, tip, ancestors = _context(repo_path, base, max_commits)
    records, loaded, truncated = _scan(repo, set(ancestors))
    expected, accepted, excluded = {}, [], []
    for item in records:
        if not item["candidate"]:
            excluded.append({"id": item["id"], "reason": item["reason"]})
            continue
        commit = item["commit"]
        if commit not in expected:
            expected[commit] = {t.id for t in discover_tests(repo, commit).tests if t.runs_by_default}
        if not _complete(loaded[item["id"]], expected[commit]):
            excluded.append({"id": item["id"],
                             "reason": "Run does not cover exactly the discovered default test classes."})
            continue
        accepted.append(item)
    if not any(item["commit"] == tip for item in accepted):
        raise ProjectHistoryError("No complete recorded run at BASE. Run the full suite at that commit "
                                  "or choose a BASE with recorded full-suite results.")
    ensure_local_output_ignore(repo)
    snapshot = repo / ".codedna/history-exports" / uuid4().hex
    snapshot.mkdir(parents=True)
    with HistoryStore(snapshot / "history.db") as store:
        mine_history(repo, store, revision=tip, max_commits=max_commits)
        for item in accepted:
            store.add_run(loaded[item["id"]], item["id"])
        dataset = build_dataset(store, repo, structural=False)
    csv = snapshot / "history.csv"
    dataset.to_csv(csv)
    report = {"repository": str(repo), "base_commit": tip, "rows": len(dataset.rows),
              "commits": len(dataset.commits), "failing_commits": sum(
                  any(r.label for r in rows) for rows in dataset.rows_by_commit().values()),
              "imported_runs": len(accepted), "excluded": excluded,
              "csv_path": str(csv), "database_path": str(snapshot / "history.db"),
              "automatic_csv_path": str(repo / ".codedna/history.csv"),
              "sources": [{"id": x["id"], "sha256": x["sha256"]} for x in accepted],
              "warnings": dataset.warnings + (["Saved runs were limited to the latest 1000."]
                                                if truncated else []),
              "note": "Only observed complete runs were imported. No tests were executed. "
                      "Repeated complete runs merge conservatively: a failure wins. "
                      "The recommendation gate still has to validate this history."}
    save_json(report, snapshot / "manifest.json")
    automatic = repo / ".codedna/history.csv"
    if automatic.exists():
        shutil.copy2(automatic, snapshot / "previous-history.csv")
    temporary = automatic.with_name(f"history-{snapshot.name}.csv.partial")
    shutil.copy2(csv, temporary)
    temporary.replace(automatic)
    return report
