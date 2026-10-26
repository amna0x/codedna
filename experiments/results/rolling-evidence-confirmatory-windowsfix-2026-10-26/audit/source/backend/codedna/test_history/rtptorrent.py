"""Import RTPTorrent (Mattis et al., MSR 2020) into a CodeDNA history store (D-032).

RTPTorrent v1.1 (Zenodo 4046180, CC BY 4.0) layout, from its readme.md::

    rtp-torrent/
      tr_all_built_commits.csv          tr_job_id, git_commit_id  (n:m)
      repo/<user>@<project>/            bare Git repository
      <user>@<project>/<user>@<project>.csv
          travisJobId, testName, index, duration, count, failures, errors, skipped

How the import maps CI data onto the store:

* **Tested commit** of a job = the tip of the commits it built (a push can
  contain several). Jobs whose commits are missing from the repository, or
  whose commits have more than one tip, are skipped and counted.
* **Order**: tested commits are sequenced by the first job that tested them
  (Travis job ids increase over time), i.e. real CI time order.
* **Change base** of a tested commit = the first-parent ancestor just before
  the whole push (walk first parents from the tip while inside the job's
  commit set). Changed files and structural features compare base → tip, so
  every commit of the push is covered.
* **Results**: one row per (tested commit, test class, job). A class run
  several times in one job (e.g. once per module) is merged first: counts and
  durations are summed, so a failure in any run counts. Status: failed if
  failures + errors > 0, skipped if every executed method was skipped,
  otherwise passed. Negative durations (runner defects) count as 0 s.

Nothing from the analysed project is built or executed.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from codedna.git_analysis.git import resolve_repository, run_git, run_git_bytes
from codedna.test_history.store import CommitRecord, FileChange, HistoryStore

BUILT_COMMITS_FILE = "tr_all_built_commits.csv"
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
_CHUNK = 400  # SHAs per git command line (Windows command-line length limit)


class RtpTorrentError(ValueError):
    """The dataset folder or project is not laid out as RTPTorrent describes."""


@dataclass
class ImportReport:
    project: str
    repository: str
    jobs: int = 0
    jobs_imported: int = 0
    jobs_without_commits: int = 0
    jobs_with_missing_commits: int = 0
    jobs_with_several_tips: int = 0
    tested_commits: int = 0
    result_rows: int = 0
    failing_rows: int = 0
    negative_durations: int = 0
    merged_runs: int = 0  # repeated runs of a class within one job, merged into one row
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return dict(self.__dict__)


def list_projects(dataset_dir: str | Path) -> list[str]:
    root = _root(dataset_dir)
    return sorted(p.name for p in root.iterdir()
                  if p.is_dir() and "@" in p.name and (p / f"{p.name}.csv").is_file())


def import_rtptorrent(dataset_dir: str | Path, project: str, store: HistoryStore, *,
                      max_commits: int | None = None) -> ImportReport:
    root = _root(dataset_dir)
    results_file = root / project / f"{project}.csv"
    repo_dir = root / "repo" / project
    if not results_file.is_file():
        raise RtpTorrentError(f"no results file {results_file}; projects: {list_projects(root)}")
    if not repo_dir.is_dir():
        raise RtpTorrentError(f"no repository {repo_dir}")
    repo = resolve_repository(repo_dir)
    report = ImportReport(project=project, repository=str(repo))

    rows_by_job = _read_results(results_file)
    report.jobs = len(rows_by_job)
    commits_by_job = _read_built_commits(root / BUILT_COMMITS_FILE, set(rows_by_job))

    all_shas = sorted({sha for shas in commits_by_job.values() for sha in shas})
    existing = _existing_commits(repo, all_shas)
    meta = _commit_meta(repo, sorted(existing))  # sha -> (first parent, committed_at)

    # Pick the tested commit (tip) and the change base for every job.
    tip_by_job: dict[int, str] = {}
    base_by_tip: dict[str, str | None] = {}
    tips_cache: dict[frozenset[str], list[str]] = {}
    for job in sorted(rows_by_job):
        shas = commits_by_job.get(job)
        if not shas:
            report.jobs_without_commits += 1
            continue
        if not shas <= existing:
            report.jobs_with_missing_commits += 1
            continue
        key = frozenset(shas)
        if key not in tips_cache:
            tips_cache[key] = _tips(repo, sorted(shas)) if len(shas) > 1 else list(shas)
        tips = tips_cache[key]
        if len(tips) != 1:
            report.jobs_with_several_tips += 1
            continue
        tip = tips[0]
        tip_by_job[job] = tip
        if tip not in base_by_tip:
            base_by_tip[tip] = _push_base(tip, shas, meta)

    # Sequence tested commits by the first job that tested them.
    first_job: dict[str, int] = {}
    for job, tip in tip_by_job.items():
        first_job[tip] = min(job, first_job.get(tip, job))
    ordered = sorted(first_job, key=lambda sha: first_job[sha])
    if max_commits is not None:
        ordered = ordered[-max_commits:]  # most recent window
    keep = set(ordered)

    history = []
    for seq, sha in enumerate(ordered):
        base = base_by_tip[sha]
        history.append((CommitRecord(sha, seq, base, meta[sha][1]), _changed_files(repo, base, sha)))
    store.replace_commits(history)
    store.set_meta("repository", str(repo))
    store.set_meta("source", "rtptorrent")
    store.set_meta("rtptorrent_project", project)

    batch = []
    for job, tip in tip_by_job.items():
        if tip not in keep:
            continue
        report.jobs_imported += 1
        for row in rows_by_job[job]:
            status = _status(row)
            report.negative_durations += row["negative"]
            report.merged_runs += row["runs"] - 1
            batch.append((tip, row["test"], status, row["duration"], f"travis:{job}"))
            report.failing_rows += status in ("failed", "error")
    store.add_results(batch)
    report.result_rows = len(batch)

    report.tested_commits = len(ordered)
    skipped = report.jobs_without_commits + report.jobs_with_missing_commits + report.jobs_with_several_tips
    if skipped:
        report.warnings.append(
            f"{skipped} of {report.jobs} jobs skipped: {report.jobs_without_commits} without built "
            f"commits, {report.jobs_with_missing_commits} with commits missing from the repository, "
            f"{report.jobs_with_several_tips} with several unrelated tips")
    if report.negative_durations:
        report.warnings.append(f"{report.negative_durations} negative durations clamped to 0")
    if report.merged_runs:
        report.warnings.append(f"{report.merged_runs} repeated runs of a test class within a job "
                               "were merged (counts summed; any failure wins)")
    return report


# --- reading the dataset ----------------------------------------------------------


def _root(dataset_dir: str | Path) -> Path:
    path = Path(dataset_dir)
    for candidate in (path, path / "rtp-torrent"):
        if (candidate / BUILT_COMMITS_FILE).is_file():
            return candidate
    raise RtpTorrentError(f"{path} is not an RTPTorrent folder (no {BUILT_COMMITS_FILE})")


def _read_results(path: Path) -> dict[int, list[dict]]:
    """Rows per job, with repeated runs of the same test class in one job merged.

    A job can run one class several times (e.g. once per Maven module); the
    counts are summed so a failure in any run marks the class as failed.
    Negative durations are counted in ``negative`` and contribute 0 s.
    """
    merged: dict[int, dict[str, dict]] = defaultdict(dict)
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        expected = {"travisJobId", "testName", "duration", "count", "failures", "errors", "skipped"}
        if not expected <= set(reader.fieldnames or ()):
            raise RtpTorrentError(f"{path}: expected columns {sorted(expected)}, got {reader.fieldnames}")
        for record in reader:
            duration = float(record["duration"] or 0)
            row = merged[int(record["travisJobId"])].setdefault(record["testName"], {
                "test": record["testName"], "duration": 0.0, "count": 0, "failures": 0,
                "errors": 0, "skipped": 0, "negative": 0, "runs": 0})
            row["duration"] += max(duration, 0.0)
            row["negative"] += duration < 0
            row["runs"] += 1
            for key in ("count", "failures", "errors", "skipped"):
                row[key] += int(record[key] or 0)
    return {job: list(tests.values()) for job, tests in merged.items()}


def _read_built_commits(path: Path, jobs: set[int]) -> dict[int, set[str]]:
    commits: dict[int, set[str]] = defaultdict(set)
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        if header[:2] != ["tr_job_id", "git_commit_id"]:
            raise RtpTorrentError(f"{path}: unexpected header {header}")
        for job_text, sha in reader:
            job = int(job_text)
            if job in jobs:
                commits[job].add(sha)
    return commits


def _status(row: dict) -> str:
    if row["failures"] + row["errors"] > 0:
        return "failed"
    if row["count"] > 0 and row["skipped"] >= row["count"]:
        return "skipped"
    return "passed"


# --- Git ----------------------------------------------------------------------------


def _existing_commits(repo: Path, shas: list[str]) -> set[str]:
    if not shas:
        return set()
    output = run_git_bytes(repo, "cat-file", "--batch-check",
                           stdin="".join(f"{sha}\n" for sha in shas).encode("ascii"))
    existing = set()
    for line in output.decode("ascii", errors="replace").splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[1] == "commit":
            existing.add(parts[0])
    return existing


def _commit_meta(repo: Path, shas: list[str]) -> dict[str, tuple[str | None, int]]:
    meta: dict[str, tuple[str | None, int]] = {}
    for start in range(0, len(shas), _CHUNK):
        chunk = shas[start:start + _CHUNK]
        output = run_git(repo, "log", "--no-walk=unsorted", "--format=%H %ct %P", *chunk)
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                meta[parts[0]] = (parts[2] if len(parts) > 2 else None, int(parts[1]))
    return meta


def _tips(repo: Path, shas: list[str]) -> list[str]:
    """Commits of ``shas`` that are not ancestors of another one in the set."""
    if not shas:
        return []
    if len(shas) <= _CHUNK:
        return run_git(repo, "merge-base", "--independent", *shas).split()
    # A push can contain thousands of commits. Supplying those as argv exceeds
    # Windows CreateProcess limits. Walk the same ancestry via stdin instead:
    # a candidate is independent exactly when no reachable commit names it as
    # a parent. Walking all ancestors also covers gaps between input commits.
    output = run_git_bytes(repo, "rev-list", "--parents", "--stdin",
                           stdin="".join(f"{sha}\n" for sha in shas).encode("ascii"))
    ancestors = {parent for line in output.splitlines() for parent in line.split()[1:]}
    return [sha for sha in dict.fromkeys(shas) if sha.encode("ascii") not in ancestors]


def _push_base(tip: str, pushed: set[str], meta: dict[str, tuple[str | None, int]]) -> str | None:
    """Walk first parents from ``tip`` while inside the pushed commits."""
    current: str | None = tip
    seen = 0
    while current is not None and current in pushed and seen <= len(pushed):
        current = meta.get(current, (None, 0))[0]
        seen += 1
    return current


def _changed_files(repo: Path, base: str | None, tip: str) -> list[FileChange]:
    output = run_git(repo, "diff", "--numstat", "-z", "--no-renames", "--no-ext-diff",
                     "--no-textconv", base or EMPTY_TREE, tip)
    files = []
    for entry in output.split("\0"):
        if not entry.strip():
            continue
        added, deleted, path = entry.split("\t", 2)
        files.append(FileChange(path, None if added == "-" else int(added),
                                None if deleted == "-" else int(deleted)))
    return files
