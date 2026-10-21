"""Tests for calibration, risk-aware selection with fallback, and the experiment (Milestone 5).

All data here is synthetic and only checks behaviour; it says nothing about
how CodeDNA performs on real projects.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codedna.calibration.calibrators import Calibrator
from codedna.calibration.metrics import brier_score, expected_calibration_error, reliability_bins
from codedna.cli import EXIT_ANALYSIS_ERROR, EXIT_OK, main
from codedna.models.experiment import run_experiment
from codedna.selection.risk import RiskPolicy, decide
from codedna.test_history.features import (
    CHANGE_FEATURES,
    HISTORY_FEATURES,
    STRUCTURAL_FEATURES,
    TEST_FEATURES,
    Dataset,
    Row,
)
from codedna.test_history.mining import mine_history
from codedna.test_history.store import HistoryStore

ALL_FEATURES = CHANGE_FEATURES + TEST_FEATURES + STRUCTURAL_FEATURES + HISTORY_FEATURES


# --- calibration -----------------------------------------------------------------------


def miscalibrated(copies=1):
    """Raw scores 0.1 / 0.5 / 0.9 whose true failure rates are 0 / 10 % / 20 %."""
    scores, labels = [], []
    for score, failures in ((0.1, 0), (0.5, 1), (0.9, 2)):
        for i in range(10 * copies):
            scores.append(score)
            labels.append(int(i % 10 < failures))
    return scores, labels


def test_calibration_metrics_by_hand():
    probabilities, labels = [0.0, 1.0, 0.5, 0.5], [0, 1, 1, 0]
    assert brier_score(probabilities, labels) == pytest.approx(0.125)
    assert expected_calibration_error(probabilities, labels) == pytest.approx(0.0)
    assert expected_calibration_error([0.9, 0.9], [0, 0]) == pytest.approx(0.9)
    bins = reliability_bins([0.05, 0.95, 0.96], [0, 1, 0])
    assert bins == [
        {"bin": [0.0, 0.1], "count": 1, "mean_predicted": 0.05, "observed_rate": 0.0},
        {"bin": [0.9, 1.0], "count": 2, "mean_predicted": 0.955, "observed_rate": 0.5},
    ]
    assert brier_score([], []) is None


@pytest.mark.parametrize("method", ["platt", "isotonic"])
def test_calibration_improves_held_out_reliability(method):
    fit_scores, fit_labels = miscalibrated()
    test_scores, test_labels = miscalibrated(copies=2)

    raw = Calibrator("none").fit(fit_scores, fit_labels).transform(test_scores)
    calibrated = Calibrator(method).fit(fit_scores, fit_labels).transform(test_scores)

    assert brier_score(calibrated, test_labels) < brier_score(raw, test_labels)
    assert expected_calibration_error(calibrated, test_labels) < \
        expected_calibration_error(raw, test_labels)


def test_calibrator_errors():
    with pytest.raises(ValueError, match="unknown calibration"):
        Calibrator("magic")
    with pytest.raises(ValueError, match="both failing and passing"):
        Calibrator("isotonic").fit([0.1, 0.2], [0, 0])
    with pytest.raises(RuntimeError, match="not fitted"):
        Calibrator("platt").transform([0.5])


# --- risk-aware selection -----------------------------------------------------------------


def candidate(test, cost=1.0, **features):
    base = {"mean_duration": cost, "past_runs": 5.0, "test_file_changed": 0.0,
            "non_java_files_changed": 0.0}
    return Row("c", 0, test, 0, cost, {**base, **features})


def test_budget_picks_most_risk_per_second():
    rows = [candidate("cheap_risky", 1.0), candidate("slow_risky", 4.0), candidate("safe", 1.0)]
    decision = decide(rows, [0.4, 0.5, 0.01], RiskPolicy(budget=0.5))

    assert decision.selected == ["cheap_risky", "safe"]  # 0.5 / 4 per second loses
    assert decision.estimated_time_fraction == pytest.approx(2 / 6)
    assert decision.estimated_skip_risk == pytest.approx(0.5)
    assert decision.expected_missed_failures == pytest.approx(0.5)
    assert not decision.fallback


def test_changed_tests_always_run():
    rows = [candidate("changed", 10.0, test_file_changed=1.0), candidate("other", 1.0)]
    decision = decide(rows, [0.0, 0.9], RiskPolicy(budget=0.0))
    assert decision.selected == ["changed"]
    assert "always run" in decision.reasons[0]


def test_risk_target_without_budget_adds_until_risk_is_low():
    rows = [candidate(f"t{i}") for i in range(4)]
    decision = decide(rows, [0.3, 0.2, 0.02, 0.01], RiskPolicy(budget=None, risk_target=0.05))
    assert decision.selected == ["t0", "t1"]
    assert decision.estimated_skip_risk == pytest.approx(1 - 0.98 * 0.99)


def test_fallback_broadens_when_budget_leaves_too_much_risk():
    rows = [candidate(f"t{i}") for i in range(4)]
    probabilities = [0.3, 0.3, 0.3, 0.01]

    plain = decide(rows, probabilities, RiskPolicy(budget=0.25, risk_target=0.05))
    with_fallback = decide(rows, probabilities,
                           RiskPolicy(budget=0.25, risk_target=0.05, fallback=True))

    assert len(plain.selected) == 1 and not plain.fallback
    assert "fallback disabled" in plain.reasons[-1]
    assert with_fallback.fallback and with_fallback.selected == ["t0", "t1", "t2"]
    assert with_fallback.estimated_skip_risk <= 0.05


def test_unfamiliar_changes_fall_back_to_retest_all():
    rows = [candidate("a", non_java_files_changed=2.0), candidate("b", non_java_files_changed=2.0)]
    decision = decide(rows, [0.0, 0.0], RiskPolicy(budget=0.1, fallback=True))
    assert decision.fallback and decision.selected == ["a", "b"]
    assert "non-Java" in decision.reasons[0]

    new_tests = [candidate("a", past_runs=0.0), candidate("b", past_runs=0.0), candidate("c")]
    decision = decide(new_tests, [0.0, 0.0, 0.0], RiskPolicy(budget=0.1, fallback=True))
    assert decision.fallback and "no history" in decision.reasons[0]


# --- experiment ----------------------------------------------------------------------------


def synthetic_dataset(commits=20, tests=6, failures=True):
    rows = []
    for i in range(commits):
        failing = f"t{i % tests}" if failures and i % 2 == 0 else None
        for j in range(tests):
            test = f"t{j}"
            hot = test == failing
            features = {name: 0.0 for name in ALL_FEATURES}
            features.update({"mean_duration": float(j + 1), "past_runs": float(i + 1),
                             "recent_failures": 2.0 if hot else 0.0,
                             "failure_rate": 0.5 if hot else 0.0,
                             "dep_reachable": 1.0 if hot else 0.0,
                             "files_changed": 3.0})
            rows.append(Row(f"c{i:02d}", i, test, int(hot), float(j + 1), features))
    return Dataset(rows=rows, feature_names=list(ALL_FEATURES),
                   commits=[f"c{i:02d}" for i in range(commits)])


def test_experiment_reports_policies_calibration_sweeps_and_ablations():
    dataset = synthetic_dataset()
    report = run_experiment(dataset, model="logistic_regression", calibration="platt",
                            budget=0.3, risk_target=0.05)

    policies = report["policies"]
    assert set(policies) == {"B0_retest_all", "B4_dependency", "B6_change_only_ml",
                             "B7_ml_uncalibrated", "B8_ml_calibrated", "B9_calibrated_fallback",
                             "B9r_risk_target_only", "B9n_unfamiliar_rule_only"}
    assert len(report["risk_coverage"]["B9r_risk_target_sweep"]) == 6
    retest = policies["B0_retest_all"]
    assert (retest["mean_time_ratio"], retest["failing_test_recall"], retest["missed_failures"]) == \
        (1.0, 1.0, 0)
    assert policies["B4_dependency"]["failing_test_recall"] == 1.0  # synthetic: failures reachable
    assert policies["B8_ml_calibrated"]["mean_time_ratio"] < 1.0
    for name in ("B7_ml_uncalibrated", "B8_ml_calibrated", "B9_calibrated_fallback"):
        assert policies[name]["mean_estimated_skip_risk"] is not None
    assert set(report["calibration"]["methods"]) == {"none", "platt", "isotonic"}
    assert len(report["risk_coverage"]["B8_budget_sweep"]) == 10
    assert report["risk_coverage"]["B8_budget_sweep"][-1]["failing_test_recall"] == 1.0
    assert set(report["ablations"]) == {"all_features", "without_change", "without_structural",
                                        "without_history"}
    assert report["config"]["splits"] == {"train": 12, "validation": 4, "test": 4}


def test_experiment_is_reproducible():
    first = run_experiment(synthetic_dataset(), sweeps=False, ablations=False)
    second = run_experiment(synthetic_dataset(), sweeps=False, ablations=False)
    assert first["reproducibility"]["dataset_sha256"] == second["reproducibility"]["dataset_sha256"]
    assert first["policies"] == second["policies"]


def test_experiment_without_failures_only_runs_non_ml_policies():
    report = run_experiment(synthetic_dataset(failures=False))
    assert set(report["policies"]) == {"B0_retest_all", "B4_dependency"}
    assert report["policies"]["B0_retest_all"]["failing_test_recall"] is None
    assert any("not trained" in w for w in report["warnings"])
    assert report["calibration"] is None


def test_experiment_rejects_unknown_calibration():
    with pytest.raises(ValueError, match="unknown calibration"):
        run_experiment(synthetic_dataset(), calibration="magic")


def test_history_experiment_command(repo, tmp_path, capsys):
    repo.write("a.txt", "0\n")
    shas = [repo.commit("c0")]
    for i in range(1, 10):
        repo.write("a.txt", f"{i}\n")
        shas.append(repo.commit(f"c{i}"))
    db = tmp_path / "h.db"
    with HistoryStore(db) as store:
        mine_history(repo.path, store)
        for i, sha in enumerate(shas):
            store.add_result(sha, "a.FlakyTest", "failed" if i % 3 == 0 else "passed", 1.0, "t")
            store.add_result(sha, "a.StableTest", "passed", 2.0, "t")

    code = main(["history", "experiment", "--db", str(db), "--repo", str(repo.path),
                 "--no-structural", "--no-ablations", "--no-sweeps",
                 "--model", "logistic_regression", "--budget", "0.4"])

    assert code == EXIT_OK
    report = json.loads(capsys.readouterr().out)
    assert "B4_dependency" not in report["policies"]
    assert report["config"]["budget"] == 0.4
    assert any("structural features missing" in w for w in report["warnings"])

    with pytest.raises(SystemExit):
        main(["history", "experiment", "--db", str(db), "--budget", "1.5"])
    assert main(["history", "experiment", "--db", str(tmp_path / "none.db")]) == EXIT_ANALYSIS_ERROR


def test_fallback_variants_separate_the_two_triggers():
    dataset = synthetic_dataset()
    for row in dataset.rows:
        if row.seq % 3 == 0:  # every third commit also changes a non-Java file
            row.features["non_java_files_changed"] = 1.0
    policies = run_experiment(dataset, model="logistic_regression", sweeps=False,
                              ablations=False, budget=0.3, risk_target=0.05)["policies"]

    unfamiliar = policies["B9n_unfamiliar_rule_only"]
    risk_only = policies["B9r_risk_target_only"]
    assert unfamiliar["fallback_rate"] > 0           # the non-Java rule fires
    assert unfamiliar["mean_estimated_skip_risk"] is not None
    # Without the rule, fallback can only come from the estimated risk; with a
    # well-separated synthetic signal the budget already covers it.
    assert risk_only["fallback_rate"] <= unfamiliar["fallback_rate"]
    assert policies["B9_calibrated_fallback"]["fallback_rate"] >= unfamiliar["fallback_rate"]


def test_dataset_csv_round_trip(tmp_path):
    dataset = synthetic_dataset(commits=6)
    path = tmp_path / "dataset.csv"
    dataset.to_csv(path)

    loaded = Dataset.from_csv(path)

    assert loaded.commits == dataset.commits
    assert loaded.feature_names == dataset.feature_names
    assert [(r.commit, r.test_id, r.label, r.duration, r.features) for r in loaded.rows] == [
        (r.commit, r.test_id, r.label, r.duration, r.features) for r in dataset.rows]
    bad = tmp_path / "bad.csv"
    bad.write_text("a,b" + chr(10), encoding="utf-8")
    with pytest.raises(ValueError, match="not a CodeDNA dataset"):
        Dataset.from_csv(bad)


def test_cli_reuses_a_saved_dataset(tmp_path, capsys):
    path = tmp_path / "dataset.csv"
    synthetic_dataset().to_csv(path)

    assert main(["history", "experiment", "--from-dataset", str(path), "--no-sweeps",
                 "--no-ablations", "--model", "logistic_regression"]) == EXIT_OK
    assert "B9r_risk_target_only" in json.loads(capsys.readouterr().out)["policies"]
    assert main(["history", "evaluate", "--from-dataset", str(path),
                 "--rankers", "random"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["protocol"]["rows"] == 120
    assert main(["history", "evaluate"]) == EXIT_ANALYSIS_ERROR
    assert "--db or --from-dataset" in capsys.readouterr().err


def test_study_runner_aggregates_seeds_and_projects(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_study", Path(__file__).resolve().parents[2] / "scripts" / "run_study.py")
    study = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(study)
    for name in ("alpha", "beta"):
        (tmp_path / name).mkdir()
        synthetic_dataset().to_csv(tmp_path / name / "dataset.csv")  # reused, so no DB needed
        study.run_project(name, "unused.db", str(tmp_path), [0, 1])

    summary = study.summarise(tmp_path, ["alpha", "beta"], [0, 1])
    markdown = study.to_markdown(summary)

    b0 = summary["projects"]["alpha"]["policies"]["B0_retest_all"]
    assert b0["failing_test_recall"] == {"mean": 1.0, "sd": 0.0}
    assert summary["pooled"]["policies"]["B9r_risk_target_only"]["mean_time_ratio"]["projects"] == 2
    assert (tmp_path / "alpha" / "experiment-seed1.json").is_file()
    assert "| B9n_unfamiliar_rule_only |" in markdown and "## Ablations" in markdown
