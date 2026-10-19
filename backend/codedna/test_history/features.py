"""Build the (commit, test) dataset for failure prediction (D-023).

Commits with stored test results are processed oldest first. For each commit
``c`` and each test class ``t`` that ran at ``c``, one row is produced:

* **label** — ``t`` failed (status failed/error) at ``c``;
* **change features** — size of the change ``parent(c) → c``;
* **structural features** — from ``impact`` on ``parent(c) → c``: whether the
  static graph reaches ``t`` from a changed type, at what distance, and
  whether through confirmed edges only;
* **history features** — computed only from results of commits *before* ``c``
  (the state is updated after the row is emitted), so nothing from ``c`` or
  later leaks into its own features.

``duration`` is the test's real time at ``c``; it is used only as the *cost*
when evaluating orderings, never as a feature.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from codedna.git_analysis.git import CodeDNAGitError, resolve_repository
from codedna.impact_analysis import compute_impact
from codedna.test_history.store import HistoryStore

RECENT_WINDOW = 5
NEVER = 10_000  # "commits since last failure" when the test never failed

CHANGE_FEATURES = ["files_changed", "java_files_changed", "non_java_files_changed",
                   "test_files_changed", "lines_added", "lines_deleted"]
TEST_FEATURES = ["test_file_changed"]
STRUCTURAL_FEATURES = ["dep_reachable", "dep_distance", "dep_confirmed"]
HISTORY_FEATURES = ["past_runs", "past_failures", "failure_rate", "recent_failures",
                    "failed_last_run", "commits_since_failure", "mean_duration",
                    "last_duration", "co_failures"]


@dataclass
class Row:
    commit: str
    seq: int
    test_id: str
    label: int
    duration: float
    features: dict[str, float]


@dataclass
class Dataset:
    rows: list[Row]
    feature_names: list[str]
    commits: list[str]  # in chronological order
    warnings: list[str] = field(default_factory=list)

    def rows_by_commit(self) -> dict[str, list[Row]]:
        grouped: dict[str, list[Row]] = defaultdict(list)
        for row in self.rows:
            grouped[row.commit].append(row)
        return grouped

    def to_csv(self, path: str | Path) -> None:
        import csv
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["commit", "seq", "test_id", "label", "duration", *self.feature_names])
            for row in self.rows:
                writer.writerow([row.commit, row.seq, row.test_id, row.label, row.duration,
                                 *(row.features[name] for name in self.feature_names)])


@dataclass
class _TestState:
    runs: int = 0
    failures: int = 0
    recent: deque = field(default_factory=lambda: deque(maxlen=RECENT_WINDOW))
    last_failure_index: int | None = None
    total_time: float = 0.0
    last_time: float = 0.0


def build_dataset(store: HistoryStore, repo_path: str | Path | None = None, *,
                  structural: bool = True) -> Dataset:
    """Turn stored history + results into labelled rows (see module docstring)."""
    repo = resolve_repository(repo_path or store.get_meta("repository") or ".")
    with_results = store.commits_with_results()
    commits = [c for c in store.commits() if c.sha in with_results]
    names = CHANGE_FEATURES + TEST_FEATURES + (STRUCTURAL_FEATURES if structural else []) \
        + HISTORY_FEATURES
    dataset = Dataset(rows=[], feature_names=names, commits=[c.sha for c in commits])
    if not commits:
        dataset.warnings.append("no commits with test results; import or collect results first")
        return dataset

    states: dict[str, _TestState] = defaultdict(_TestState)
    # path -> test -> number of failures of that test at commits touching path
    file_failures: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for index, commit in enumerate(commits):
        files = store.changed_files(commit.sha)
        paths = [f.path for f in files]
        change = {
            "files_changed": len(files),
            "java_files_changed": sum(p.endswith(".java") for p in paths),
            "non_java_files_changed": sum(not p.endswith(".java") for p in paths),
            "test_files_changed": sum(_is_test_path(p) for p in paths),
            "lines_added": sum(f.added or 0 for f in files),
            "lines_deleted": sum(f.deleted or 0 for f in files),
        }
        impacted = _structural(repo, commit, dataset.warnings) if structural else None

        results = [r for r in store.results(commit.sha) if r.status != "skipped"]
        for result in results:
            state = states[result.test_id]
            features = dict(change)
            features["test_file_changed"] = float(any(_is_file_of(result.test_id, p) for p in paths))
            if structural:
                hit = (impacted or {}).get(result.test_id)
                features["dep_reachable"] = float(hit is not None)
                features["dep_distance"] = float(hit[0]) if hit else -1.0
                features["dep_confirmed"] = float(bool(hit and hit[1]))
            features.update(_history_features(state, index))
            features["co_failures"] = float(sum(file_failures[p].get(result.test_id, 0)
                                                for p in paths))
            dataset.rows.append(Row(commit.sha, commit.seq, result.test_id,
                                    int(result.failed), result.time, features))

        # Only now does commit `index` become history for later commits.
        for result in results:
            state = states[result.test_id]
            state.runs += 1
            state.failures += int(result.failed)
            state.recent.append(int(result.failed))
            state.total_time += result.time
            state.last_time = result.time
            if result.failed:
                state.last_failure_index = index
                for path in paths:
                    file_failures[path][result.test_id] += 1

    failing = sum(1 for rows in dataset.rows_by_commit().values() if any(r.label for r in rows))
    if failing < 10:
        dataset.warnings.append(f"only {failing} commit(s) with failing tests; results will be "
                                "unreliable — collect more history or use a fault dataset")
    return dataset


def _history_features(state: _TestState, index: int) -> dict[str, float]:
    return {
        "past_runs": float(state.runs),
        "past_failures": float(state.failures),
        "failure_rate": state.failures / state.runs if state.runs else 0.0,
        "recent_failures": float(sum(state.recent)),
        "failed_last_run": float(state.recent[-1]) if state.recent else 0.0,
        "commits_since_failure": float(index - state.last_failure_index)
        if state.last_failure_index is not None else float(NEVER),
        "mean_duration": state.total_time / state.runs if state.runs else 0.0,
        "last_duration": state.last_time,
    }


def _structural(repo: Path, commit, warnings: list[str]) -> dict[str, tuple[int, bool]] | None:
    """test id -> (graph distance, reached through confirmed edges only)."""
    if commit.parent is None:
        return None
    try:
        report = compute_impact(repo, commit.parent, commit.sha)
    except CodeDNAGitError as exc:
        warnings.append(f"{commit.sha[:12]}: structural features unavailable ({exc})")
        return None
    reached: dict[str, tuple[int, bool]] = {}
    for seed in report.seeds:
        reached[seed.node.removeprefix("type:")] = (0, True)
    for node in report.impacted:
        reached.setdefault(node.node.removeprefix("type:"),
                           (node.distance, node.confidence == "confirmed"))
    return reached


def _is_test_path(path: str) -> bool:
    stem = PurePosixPath(path).stem
    return path.endswith(".java") and ("src/test/" in f"/{path}" or stem.endswith(("Test", "Tests")))


def _is_file_of(test_id: str, path: str) -> bool:
    return path.endswith("/" + test_id.replace(".", "/") + ".java") \
        or path == test_id.replace(".", "/") + ".java"
