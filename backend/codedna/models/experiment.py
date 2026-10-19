"""Milestone 5 experiment: calibration, risk-aware selection and fallback (D-027).

On the chronological split (D-023):

* the failure model is trained on **train**, the calibrator fitted on
  **validation**, and everything below is measured on **test** only;
* ``calibration`` compares no calibration, Platt and isotonic (Brier, ECE,
  reliability bins) — RQ3;
* ``policies`` compares selection policies per test commit — RQ2/RQ4:

  ===  ==============================================================
  B0   retest all
  B4   dependency-only: tests reachable from the change, or changed
  B6   change-only model (change + test-changed features), budget
  B7   full model, uncalibrated, budget
  B8   full model, calibrated, budget
  B9   full model, calibrated, budget + risk target + fallback
  ===  ==============================================================

  measured by selection ratio, real-time ratio, failing-test recall,
  missed failures, commit safety rate, fallback rate, and — for policies
  with probabilities — mean estimated skip risk vs observed miss rate;
* ``risk_coverage`` sweeps the budget (B8) and the risk target (B9);
* ``ablations`` retrains without each feature group — RQ1/RQ5.

Nothing is assumed: every number comes from the stored history.
"""

from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import asdict
from importlib.metadata import PackageNotFoundError, version
from statistics import mean

from codedna.calibration.calibrators import METHODS, Calibrator
from codedna.calibration.metrics import brier_score, expected_calibration_error, reliability_bins
from codedna.models.evaluate import chronological_split
from codedna.models.rankers import MLRanker
from codedna.selection.risk import RiskPolicy, decide
from codedna.test_history.features import (
    CHANGE_FEATURES,
    HISTORY_FEATURES,
    STRUCTURAL_FEATURES,
    TEST_FEATURES,
    Dataset,
    Row,
)

FEATURE_GROUPS = {"change": CHANGE_FEATURES, "structural": STRUCTURAL_FEATURES,
                  "history": HISTORY_FEATURES}
BUDGET_SWEEP = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
RISK_SWEEP = (0.01, 0.02, 0.05, 0.1, 0.2, 0.3)


def run_experiment(dataset: Dataset, *, model: str = "gradient_boosting",
                   calibration: str = "isotonic", budget: float = 0.5,
                   risk_target: float = 0.05, seed: int = 0, sweeps: bool = True,
                   ablations: bool = True) -> dict:
    if calibration not in METHODS:
        raise ValueError(f"unknown calibration {calibration!r}; choose from {METHODS}")
    splits = chronological_split(dataset)
    by_commit = dataset.rows_by_commit()
    rows_of = lambda split: [r for sha in splits[split] for r in by_commit.get(sha, [])]  # noqa: E731
    train, valid = rows_of("train"), rows_of("validation")
    test_commits = [by_commit[sha] for sha in splits["test"] if sha in by_commit]
    test_rows = [r for group in test_commits for r in group]
    warnings = list(dataset.warnings)
    report = {
        "config": {"model": model, "calibration": calibration, "budget": budget,
                   "risk_target": risk_target, "seed": seed,
                   "splits": {k: len(v) for k, v in splits.items()}},
        "reproducibility": _reproducibility(dataset, seed),
        "warnings": warnings,
        "note": "computed from the stored history only; no numbers are assumed",
    }
    has_structural = all(f in dataset.feature_names for f in STRUCTURAL_FEATURES)

    full = _fit(model, dataset.feature_names, train, seed, warnings, "full model")
    change_only = _fit(model, [f for f in CHANGE_FEATURES + TEST_FEATURES
                               if f in dataset.feature_names], train, seed, warnings,
                       "change-only model (B6)")
    calibrator = None
    if full is not None:
        try:
            calibrator = Calibrator(calibration).fit(full.predict_proba(valid),
                                                     [r.label for r in valid])
        except ValueError as exc:
            warnings.append(f"calibrator not fitted ({exc}); B8/B9 use raw probabilities")
            calibrator = Calibrator("none")

    def probabilities(rows, *, calibrated=True, ranker=None):
        ranker = ranker or full
        raw = ranker.predict_proba(rows)
        return calibrator.transform(raw) if calibrated and calibrator else raw

    report["calibration"] = _calibration_section(full, valid, test_rows, warnings) \
        if full is not None else None

    policies: dict[str, object] = {"B0_retest_all": lambda rows: (
        [r.test_id for r in rows], None)}
    if has_structural:
        policies["B4_dependency"] = lambda rows: (
            [r.test_id for r in rows if r.features["dep_reachable"] or r.features["test_file_changed"]],
            None)
    else:
        warnings.append("structural features missing (--no-structural); B4 not evaluated")
    budget_policy = RiskPolicy(budget=budget)
    if change_only is not None:
        policies["B6_change_only_ml"] = _ml_policy(
            lambda rows: change_only.predict_proba(rows), budget_policy)
    if full is not None:
        policies["B7_ml_uncalibrated"] = _ml_policy(
            lambda rows: probabilities(rows, calibrated=False), budget_policy)
        policies["B8_ml_calibrated"] = _ml_policy(probabilities, budget_policy)
        policies["B9_calibrated_fallback"] = _ml_policy(
            probabilities, RiskPolicy(budget=budget, risk_target=risk_target, fallback=True))
    report["policies"] = {name: _measure(test_commits, fn) for name, fn in policies.items()}

    if sweeps and full is not None:
        report["risk_coverage"] = {
            "B8_budget_sweep": [
                {"budget": b, **_summary(_measure(test_commits, _ml_policy(
                    probabilities, RiskPolicy(budget=b))))} for b in BUDGET_SWEEP],
            "B9_risk_target_sweep": [
                {"risk_target": t, **_summary(_measure(test_commits, _ml_policy(
                    probabilities, RiskPolicy(budget=budget, risk_target=t, fallback=True))))}
                for t in RISK_SWEEP],
        }
    if ablations and full is not None:
        report["ablations"] = _ablations(model, dataset.feature_names, train, test_commits,
                                         budget, seed, warnings)
    return report


# --- models ---------------------------------------------------------------------------


def _fit(model: str, features: list[str], rows: list[Row], seed: int, warnings: list[str],
         label: str) -> MLRanker | None:
    if not features:
        warnings.append(f"{label}: no features available")
        return None
    ranker = MLRanker(model, features, seed=seed)
    try:
        ranker.fit(rows)
    except ValueError as exc:
        warnings.append(f"{label} not trained: {exc}")
        return None
    return ranker


def _calibration_section(full: MLRanker, valid: list[Row], test: list[Row],
                         warnings: list[str]) -> dict:
    labels = [r.label for r in test]
    raw_valid, raw_test = full.predict_proba(valid), full.predict_proba(test)
    section = {"test_rows": len(test), "test_failure_rate":
               round(sum(labels) / len(labels), 4) if labels else None, "methods": {}}
    for method in METHODS:
        try:
            calibrated = Calibrator(method).fit(raw_valid, [r.label for r in valid]).transform(raw_test)
        except ValueError as exc:
            warnings.append(f"calibration {method} skipped: {exc}")
            continue
        brier, ece = brier_score(calibrated, labels), expected_calibration_error(calibrated, labels)
        section["methods"][method] = {
            "brier": round(brier, 4) if brier is not None else None,
            "ece": round(ece, 4) if ece is not None else None,
            "reliability": reliability_bins(calibrated, labels),
        }
    return section


# --- policies ---------------------------------------------------------------------------


def _ml_policy(probability_fn, policy: RiskPolicy):
    def choose(rows: list[Row]):
        decision = decide(rows, probability_fn(rows), policy)
        return decision.selected, decision
    return choose


def _measure(test_commits: list[list[Row]], choose) -> dict:
    per_commit = []
    for rows in test_commits:
        selected, decision = choose(rows)
        chosen = set(selected)
        failing = {r.test_id for r in rows if r.label}
        total_time = sum(r.duration for r in rows)
        per_commit.append({
            "tests": len(rows), "selected": len(chosen),
            "time_ratio": sum(r.duration for r in rows if r.test_id in chosen) / total_time
            if total_time else len(chosen) / len(rows),
            "failing": len(failing), "missed": len(failing - chosen),
            "fallback": bool(decision and decision.fallback),
            "estimated_risk": decision.estimated_skip_risk if decision else None,
        })
    failing_commits = [c for c in per_commit if c["failing"]]
    total_failing = sum(c["failing"] for c in per_commit)
    risks = [c["estimated_risk"] for c in per_commit if c["estimated_risk"] is not None]
    return {
        "commits": len(per_commit),
        "commits_with_failures": len(failing_commits),
        "mean_selection_ratio": _avg([c["selected"] / c["tests"] for c in per_commit if c["tests"]]),
        "mean_time_ratio": _avg([c["time_ratio"] for c in per_commit]),
        "failing_test_recall": round(1 - sum(c["missed"] for c in per_commit) / total_failing, 4)
        if total_failing else None,
        "missed_failures": sum(c["missed"] for c in per_commit),
        "commit_safety_rate": _avg([float(c["missed"] == 0) for c in failing_commits]),
        "fallback_rate": _avg([float(c["fallback"]) for c in per_commit]),
        "mean_estimated_skip_risk": _avg(risks) if risks else None,
        "observed_miss_rate": _avg([float(c["missed"] > 0) for c in per_commit]),
    }


def _summary(metrics: dict) -> dict:
    keys = ("mean_time_ratio", "mean_selection_ratio", "failing_test_recall",
            "commit_safety_rate", "fallback_rate", "mean_estimated_skip_risk",
            "observed_miss_rate")
    return {k: metrics[k] for k in keys}


def _ablations(model: str, features: list[str], train: list[Row], test_commits, budget: float,
               seed: int, warnings: list[str]) -> dict:
    from sklearn.metrics import average_precision_score

    test_rows = [r for group in test_commits for r in group]
    labels = [r.label for r in test_rows]
    results = {}
    variants = {"all_features": features}
    for group, names in FEATURE_GROUPS.items():
        kept = [f for f in features if f not in names]
        if len(kept) < len(features):
            variants[f"without_{group}"] = kept
    for name, kept in variants.items():
        ranker = _fit(model, kept, train, seed, warnings, f"ablation {name}")
        if ranker is None:
            continue
        scores = ranker.predict_proba(test_rows)
        metrics = _measure(test_commits, _ml_policy(ranker.predict_proba, RiskPolicy(budget=budget)))
        results[name] = {
            "features": len(kept),
            "pr_auc": round(float(average_precision_score(labels, scores)), 4) if any(labels) else None,
            "brier": round(brier_score(scores, labels), 4) if labels else None,
            "failing_test_recall_at_budget": metrics["failing_test_recall"],
            "commit_safety_rate_at_budget": metrics["commit_safety_rate"],
        }
    return results


# --- reproducibility --------------------------------------------------------------------


def _reproducibility(dataset: Dataset, seed: int) -> dict:
    digest = hashlib.sha256()
    for row in dataset.rows:
        digest.update(json.dumps(asdict(row), sort_keys=True).encode())
    return {
        "dataset_sha256": digest.hexdigest(),
        "rows": len(dataset.rows),
        "commits": len(dataset.commits),
        "first_commit": dataset.commits[0] if dataset.commits else None,
        "last_commit": dataset.commits[-1] if dataset.commits else None,
        "seed": seed,
        "python": platform.python_version(),
        "packages": {name: _version(name) for name in ("codedna", "scikit-learn", "numpy")},
    }


def _version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _avg(values: list[float]) -> float | None:
    return round(mean(values), 4) if values else None
