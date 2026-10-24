"""The transfer runner reports unavailable directions rather than hiding them."""

import importlib.util
import json
from pathlib import Path
import sqlite3

from codedna.test_history.features import Dataset, Row


def test_runner_keeps_unavailable_calendar_direction_and_can_resume(repo):
    project_root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("cross_runner", project_root / "scripts/run_cross_project.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    # The helper/code hashes intentionally refer to the real project, whereas
    # all synthetic datasets and generated reports stay in the throwaway repo.
    (repo.path / "scripts").mkdir()
    (repo.path / "backend/codedna/models").mkdir(parents=True)
    for relative in runner.CODE_PATHS:
        (repo.path / relative).parent.mkdir(parents=True, exist_ok=True)
        (repo.path / relative).write_bytes((project_root / relative).read_bytes())
    names = ["early", "late"]
    for name, offset in (("early", 0), ("late", 100)):
        names_features = ["mean_duration", "past_runs", "failure_rate", "recent_failures", "test_file_changed"]
        commits = [f"{name}-{i}" for i in range(20)]
        rows = [Row(sha, i, f"Test{j}", int(j == 0 and i % 2 == 0), float(j + 1), {
                    "mean_duration": float(j + 1), "past_runs": float(i + 1),
                    "failure_rate": .5 if j == 0 else 0., "recent_failures": float(j == 0),
                    "test_file_changed": 0.})
                for i, sha in enumerate(commits) for j in range(4)]
        path = repo.path / f"experiments/results/study11-2026-10-21/{name}/dataset.csv"
        path.parent.mkdir(parents=True)
        Dataset(rows, names_features, commits).to_csv(path)
        db = repo.path / f"experiments/datasets/derived/{name}.db"
        db.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db) as conn:
            conn.execute("CREATE TABLE commits (sha TEXT, committed_at INTEGER)")
            conn.executemany("INSERT INTO commits VALUES (?, ?)", [(sha, offset + i) for i, sha in enumerate(commits)])
    out = repo.path / "transfer-results"
    summary = runner.run(repo.path, out, names, [0])
    assert summary["pairs"]["late -> early"]["runs"] == 0
    assert summary["pairs"]["early -> late"]["runs"] == 1
    assert len(summary["pairs"]) == 4
    assert summary["targets"]["late"]["test_commits"] == 4
    assert summary["targets"]["late"]["skip_all_miss_rate"] == .5
    assert summary["transfer_macro"]["expected_directions"] == 2
    assert summary["transfer_macro"]["complete_calibrated_directions"] == 1
    assert summary["transfer_macro"]["contributing_targets"] == 1
    assert runner.run(repo.path, out, names, [0]) == summary
    report = json.loads((out / "early/late-seed0.json").read_text())
    assert report["protocol"]["project_calendars_aligned"] is True
    assert report["protocol"]["target_test_labels_used_for_fitting"] is False
