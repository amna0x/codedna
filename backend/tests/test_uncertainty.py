"""Tests for cost matching, bootstrap intervals and the bounded parse cache."""

from __future__ import annotations

import pytest

from codedna.dependency_graph import build_graph
from codedna.dependency_graph.builder import BoundedParseCache, build_graph_for_commit
from codedna.git_analysis.git import resolve_commit, resolve_repository
from codedna.models.experiment import run_experiment
from codedna.models.uncertainty import bootstrap, match_budget, metrics
from test_risk_calibration import synthetic_dataset


def test_outcome_metrics():
    outcomes = [(0.5, 2, 1), (1.0, 0, 0), (0.25, 1, 0)]
    m = metrics(outcomes)
    assert m["time"] == pytest.approx((0.5 + 1.0 + 0.25) / 3)
    assert m["recall"] == pytest.approx(1 - 1 / 3)
    assert m["safety"] == pytest.approx(0.5)
    assert metrics([(0.3, 0, 0)])["recall"] is None
    assert metrics([])["time"] is None


def test_match_budget_finds_the_same_time():
    def measure(budget):  # time = budget², a monotone stand-in for the selector
        return [(budget ** 2, 1, 0)]
    budget, outcomes = match_budget(measure, 0.25)
    assert budget == pytest.approx(0.5, abs=1e-3)
    assert metrics(outcomes)["time"] == pytest.approx(0.25, abs=1e-3)


def test_bootstrap_intervals_and_paired_differences():
    a = [(0.5, 1, 0)] * 30 + [(0.5, 1, 1)] * 10
    b = [(0.4, 1, 1)] * 20 + [(0.4, 1, 0)] * 20
    result = bootstrap({"a": a, "b": b, "a_copy": list(a)},
                       {"a − b": ("a", "b"), "a − a_copy": ("a", "a_copy")}, resamples=500, seed=1)

    low, high = result["policies"]["a"]["safety"]
    assert low <= 0.75 <= high
    diff = result["differences"]["a − b"]["safety"]
    assert diff["estimate"] == pytest.approx(0.25)
    assert diff["ci"][0] <= 0.25 <= diff["ci"][1]
    assert result["differences"]["a − a_copy"]["safety"]["ci"] == [0.0, 0.0]  # paired resampling
    assert bootstrap({"a": a, "b": b}, {"a − b": ("a", "b")}, resamples=200, seed=1) == \
        bootstrap({"a": a, "b": b}, {"a − b": ("a", "b")}, resamples=200, seed=1)


def test_bootstrap_reports_no_interval_without_failures():
    calm = [(0.5, 0, 0)] * 30
    result = bootstrap({"x": calm}, {}, resamples=100)
    assert result["policies"]["x"]["safety"] is None


def test_experiment_reports_cost_matched_bootstrap_and_per_commit():
    report = run_experiment(synthetic_dataset(), model="logistic_regression", sweeps=False,
                            ablations=False, budget=0.3)
    matched = report["cost_matched"]["B9_calibrated_fallback"]
    assert matched["b8_same_time"]["time"] == pytest.approx(matched["policy"]["time"], abs=0.05)
    assert "B9r_risk_target_only − B8 at same time" in report["bootstrap"]["differences"]
    per_commit = report["per_commit"]
    assert per_commit["fields"] == ["time_ratio", "failing", "missed"]
    assert len(per_commit["B8_ml_calibrated"]) == report["config"]["splits"]["test"]
    assert "B8@B9r_risk_target_only" in per_commit


def test_bounded_cache_gives_identical_graphs(repo):
    repo.write("a/Core.java", "package a;\npublic class Core {}\n")
    repo.write("a/Service.java", "package a;\nclass Service { Core c; }\n")
    first = repo.commit("one")
    repo.write("a/Api.java", "package a;\nclass Api { Service s; }\n")
    second = repo.commit("two")
    path = resolve_repository(repo.path)

    tiny = BoundedParseCache(max_entries=1)
    graphs = [build_graph_for_commit(path, resolve_commit(path, sha), cache=tiny)
              for sha in (first, second, first)]

    assert len(tiny) == 1
    assert graphs[0].to_dict()["edges"] == graphs[2].to_dict()["edges"]
    assert graphs[1].to_dict()["edges"] == build_graph(repo.path, second).to_dict()["edges"]
