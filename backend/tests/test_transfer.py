"""Transfer models fit source data only; targets remain held out."""

from dataclasses import replace

import pytest

from codedna.models import transfer
from codedna.models.evaluate import chronological_split
from codedna.test_history.features import (
    CHANGE_FEATURES, HISTORY_FEATURES, STRUCTURAL_FEATURES, TEST_FEATURES, Dataset, Row,
)


def dataset(prefix, count=20):
    names = CHANGE_FEATURES + TEST_FEATURES + STRUCTURAL_FEATURES + HISTORY_FEATURES
    rows = []
    commits = [f"{prefix}{i:02d}" for i in range(count)]
    for i, sha in enumerate(commits):
        for j in range(4):
            features = dict.fromkeys(names, 0.0)
            features.update(mean_duration=j + 1., past_runs=i + 1.,
                            failure_rate=.7 if j == 0 else .05, recent_failures=float(j == 0))
            rows.append(Row(sha, i, f"Test{j}", int(j == 0 and i % 2 == 0), j + 1., features))
    return Dataset(rows, names, commits)


class SpyRanker:
    instances = []

    def __init__(self, *args, **kwargs):
        self.fit_rows = []
        self.predict_calls = []
        self.instances.append(self)

    def fit(self, rows):
        self.fit_rows.extend(rows)

    def predict_proba(self, rows):
        self.predict_calls.append([row.commit for row in rows])
        return [row.features["failure_rate"] for row in rows]


def test_transfer_fits_only_source_and_ignores_target_labels_for_decisions(repo, monkeypatch):
    source, target = dataset("source"), dataset("target")
    monkeypatch.setattr(transfer, "MLRanker", SpyRanker)
    fitted = transfer.fit_project("source", source, calibration="platt")
    splits = chronological_split(source)
    assert {row.commit for row in fitted.ranker.fit_rows} == set(splits["train"])
    assert set(fitted.ranker.predict_calls[0]) == set(splits["validation"])
    before_calls = len(fitted.ranker.fit_rows)
    first = transfer.evaluate_target(fitted, "target", target)
    flipped = Dataset([replace(row, label=1 - row.label) for row in target.rows],
                      target.feature_names, target.commits)
    second = transfer.evaluate_target(fitted, "target", flipped)
    assert len(fitted.ranker.fit_rows) == before_calls
    assert first["protocol"]["target_test_labels_used_for_fitting"] is False
    assert first["b10"]["calibrated"]["time"] == second["b10"]["calibrated"]["time"]
    assert first["b10"]["calibrated"]["estimated_skip_risk"] == second["b10"]["calibrated"]["estimated_skip_risk"]
    assert first["probability"]["raw"]["brier"] != second["probability"]["raw"]["brier"]


def test_unavailable_calibration_is_not_relabelled_as_calibrated(repo, monkeypatch):
    source = dataset("source")
    validation = set(chronological_split(source)["validation"])
    source.rows = [replace(row, label=0) if row.commit in validation else row for row in source.rows]
    monkeypatch.setattr(transfer, "MLRanker", SpyRanker)
    fitted = transfer.fit_project("source", source)
    assert fitted.calibrator is None
    report = transfer.evaluate_target(fitted, "target", dataset("target"))
    assert set(report["b10"]) == {"raw"}
    assert report["warnings"]


def test_calendar_filter_stops_at_first_excluded_commit(repo):
    source = dataset("source", count=4)
    times = dict(zip(source.commits, [1, 2, 10, 3]))
    eligible = transfer.source_prefix_before(source, times, 5)
    assert eligible.commits == source.commits[:2]
    assert len(eligible.rows) == 8
    assert source.commits == ["source00", "source01", "source02", "source03"]
    with pytest.raises(ValueError, match="Missing source commit timestamp"):
        transfer.source_prefix_before(source, {}, 5)


def test_identical_data_cannot_be_passed_as_two_projects(repo, monkeypatch):
    source = dataset("source")
    monkeypatch.setattr(transfer, "MLRanker", SpyRanker)
    fitted = transfer.fit_project("source", source)
    with pytest.raises(ValueError, match="Identical datasets"):
        transfer.evaluate_target(fitted, "different-name", source)


def test_target_schema_and_commit_overlap_are_checked(repo, monkeypatch):
    source, target = dataset("source"), dataset("target")
    monkeypatch.setattr(transfer, "MLRanker", SpyRanker)
    fitted = transfer.fit_project("source", source)
    bad = Dataset(target.rows, target.feature_names[:-1], target.commits)
    with pytest.raises(ValueError, match="schemas differ"):
        transfer.evaluate_target(fitted, "target", bad)
    old = target.commits[-1]
    leaked = fitted.provenance["train_commits"][0]
    bad = Dataset([replace(row, commit=leaked) if row.commit == old else row for row in target.rows],
                  target.feature_names, target.commits[:-1] + [leaked])
    with pytest.raises(ValueError, match="overlap source fitting"):
        transfer.evaluate_target(fitted, "target", bad)


def test_real_model_transfer_is_reproducible(repo):
    source, target = dataset("source"), dataset("target")
    a = transfer.evaluate_target(transfer.fit_project("source", source, model="logistic_regression"),
                                 "target", target)
    b = transfer.evaluate_target(transfer.fit_project("source", source, model="logistic_regression"),
                                 "target", target)
    assert a["policies"] == b["policies"]
    assert a["probability"] == b["probability"]
    assert a["target_data"]["test_commits"] == chronological_split(target)["test"]
