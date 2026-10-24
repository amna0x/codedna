"""DANTE-H approximation and the DANTE-H / calibrated-stopping check (D-040)."""

from __future__ import annotations

import pytest

from codedna.selection.dante import dante_scores, order_by_dante, wilson
from codedna.test_history.features import Dataset, Row
from test_risk_calibration import synthetic_dataset


def history(outcomes: dict[str, list[int]], durations: dict[str, float] | None = None) -> Dataset:
    durations = durations or {}
    commits = [f"c{i:02d}" for i in range(len(next(iter(outcomes.values()))))]
    rows = [Row(sha, i, test, labels[i], 1.0,
                {"mean_duration": durations.get(test, 1.0)})
            for i, sha in enumerate(commits) for test, labels in outcomes.items()]
    return Dataset(rows=rows, feature_names=["mean_duration"], commits=commits)


def test_wilson_interval_by_hand():
    low, high = wilson(5, 10)
    assert low == pytest.approx(0.2366, abs=1e-4)
    assert high == pytest.approx(0.7634, abs=1e-4)
    assert wilson(0, 0) == (0.0, 1.0)


def test_scores_use_only_earlier_commits():
    scores = dante_scores(history({"a": [0, 1, 0], "b": [0, 0, 0]}))
    # Nothing failed before c01, so a's own failure there cannot raise its score.
    assert scores[("c01", "a")] == 0.0
    assert scores[("c02", "a")] > 0.0
    assert scores[("c02", "b")] == 0.0


def test_sticky_test_ranks_above_one_off_failure():
    outcomes = {"sticky": [1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0],
                "flaky": [0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0],
                "clean": [0] * 14}
    dataset = history(outcomes)
    scores = dante_scores(dataset)
    last = [r for r in dataset.rows if r.commit == "c13"]
    assert scores[("c13", "sticky")] > scores[("c13", "flaky")] > scores[("c13", "clean")]
    assert order_by_dante(scores, last) == ["sticky", "flaky", "clean"]


def test_cost_divides_and_ties_go_to_shorter_tests():
    dataset = history({"slow": [1, 0], "fast": [1, 0], "never": [0, 0]},
                      durations={"slow": 10.0, "fast": 1.0, "never": 0.5})
    scores = dante_scores(dataset)
    rows = [r for r in dataset.rows if r.commit == "c01"]
    assert scores[("c01", "fast")] == pytest.approx(10 * scores[("c01", "slow")])
    assert order_by_dante(scores, rows) == ["fast", "slow", "never"]


def test_dante_check_reports_matched_comparisons():
    pytest.importorskip("sklearn")
    from codedna.models.dante_check import dante_check

    report = dante_check(synthetic_dataset(commits=30), seed=0)
    assert set(report["policies"]) == {"D2_dante_stop", "B10_hybrid"}
    assert set(report["cost_matched"]) == {"D1@D2", "B3@D2", "B3@B10"}
    assert "D2 − D1 at same time" in report["bootstrap"]["differences"]
    assert report["overhead"]["rows"] == 30 * 6
    assert "DANTE-H" in report["config"]["dante"]["variant"]
    again = dante_check(synthetic_dataset(commits=30), seed=0)
    again["overhead"] = report["overhead"]  # wall-clock timings differ run to run
    assert again == report
