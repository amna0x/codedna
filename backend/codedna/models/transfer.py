"""Project-disjoint transfer using source-only training and calibration.

The source uses the existing 60/20/20 chronological split: train on its
oldest 60%, calibrate on the next 20%, and do not use its final 20% for
fitting. Score the target's final 20%. Target history features are allowed,
but target labels never fit or calibrate the transferred model. This is a
cross-repository study. The runner restricts cross-project source history
using source_prefix_before, before the target test window's earliest Git
committer timestamp. Git dates are a proxy, not CI completion timestamps.
"""

from __future__ import annotations

from dataclasses import dataclass

from codedna.calibration.calibrators import Calibrator
from codedna.calibration.metrics import brier_score, expected_calibration_error
from codedna.models.evaluate import _ordering_metrics, chronological_split
from codedna.models.experiment import (
    _hybrid_vs_rules, _measure, _ml_policy, _reproducibility, _rules_policy,
)
from codedna.models.rankers import MLRanker, order_by_baseline
from codedna.selection.risk import RiskPolicy
from codedna.test_history.features import Dataset


@dataclass
class FittedProject:
    project: str
    ranker: MLRanker
    calibrator: Calibrator | None
    features: list[str]
    provenance: dict
    warnings: list[str]


def source_prefix_before(dataset: Dataset, commit_times: dict[str, int], cutoff: int) -> Dataset:
    """Keep a chronological source prefix strictly older than a target cutoff.

    Stop at the first ineligible commit, rather than keeping later commits
    whose historical features could incorporate an excluded observation.
    """
    prefix = []
    for sha in dataset.commits:
        if sha not in commit_times:
            raise ValueError(f"Missing source commit timestamp: {sha}")
        if commit_times[sha] >= cutoff:
            break
        prefix.append(sha)
    keep = set(prefix)
    return Dataset([row for row in dataset.rows if row.commit in keep],
                   list(dataset.feature_names), prefix, list(dataset.warnings))


def fit_project(project: str, dataset: Dataset, *, model: str = "gradient_boosting",
                calibration: str = "isotonic", seed: int = 0) -> FittedProject:
    """Fit only source train/validation rows; accept no target dataset."""
    if not project:
        raise ValueError("Source project needs a nonempty name")
    if calibration not in ("platt", "isotonic"):
        raise ValueError("Transfer calibration must be platt or isotonic")
    splits = chronological_split(dataset)
    by_commit = dataset.rows_by_commit()
    train = [row for sha in splits["train"] for row in by_commit[sha]]
    valid = [row for sha in splits["validation"] for row in by_commit[sha]]
    ranker = MLRanker(model, dataset.feature_names, seed=seed)
    ranker.fit(train)
    warnings = []
    calibrator = None
    try:
        calibrator = Calibrator(calibration).fit(ranker.predict_proba(valid), [r.label for r in valid])
    except ValueError as exc:
        # Raw results remain measurable, but must not be labelled calibrated.
        warnings.append(f"Source calibration unavailable: {exc}")
    provenance = {**_reproducibility(dataset, seed), "model": model, "calibration": calibration,
                  "train_commits": splits["train"], "calibration_commits": splits["validation"],
                  "unused_source_test_commits": splits["test"],
                  "train_rows": len(train), "calibration_rows": len(valid)}
    return FittedProject(project, ranker, calibrator, list(dataset.feature_names), provenance, warnings)


def evaluate_target(fitted: FittedProject, target_name: str, target: Dataset, *,
                    budget: float = .5, risk_target: float = .05) -> dict:
    """Evaluate a fitted source model; never fit anything on the target."""
    from sklearn.metrics import average_precision_score

    if set(target.feature_names) != set(fitted.features):
        raise ValueError("Source and target feature schemas differ")
    if not 0 <= budget <= 1 or not 0 <= risk_target <= 1:
        raise ValueError("Budget and risk target must lie in [0, 1]")
    snapshot = _reproducibility(target, fitted.provenance["seed"])
    if fitted.project != target_name and snapshot["dataset_sha256"] == fitted.provenance["dataset_sha256"]:
        raise ValueError("Identical datasets cannot be presented as different projects")
    splits = chronological_split(target)
    test_shas = splits["test"]
    fitting = set(fitted.provenance["train_commits"] + fitted.provenance["calibration_commits"])
    if fitting.intersection(test_shas):
        raise ValueError("Target test commits overlap source fitting commits")
    by_commit = target.rows_by_commit()
    test_commits = [by_commit[sha] for sha in test_shas]
    rows = [row for group in test_commits for row in group]
    if not rows:
        raise ValueError("Target has no test-split rows")
    labels = [row.label for row in rows]
    raw = fitted.ranker.predict_proba(rows)
    keys = [(row.commit, row.test_id) for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Target contains duplicate (commit, test) rows")

    report = {
        "source": fitted.project, "target": target_name,
        "evaluation": "within_project" if fitted.project == target_name else "cross_project",
        "source_fitting": fitted.provenance,
        "target_data": {**snapshot, "test_commits": test_shas,
                        "test_rows": len(rows), "test_failing_rows": sum(labels)},
        "protocol": {"budget": budget, "risk_target": risk_target,
                     "target_test_labels_used_for_fitting": False,
                     "target_project_labels_used_for_fitting": fitted.project == target_name,
                     "target_past_history_allowed": True,
                     "project_calendars_aligned": False,
                     "note": "Retrospective transfer; not a no-history or calendar-aligned deployment test"},
        "warnings": list(fitted.warnings) + list(target.warnings),
        "probability": {}, "ordering": {}, "policies": {},
        "b10": {}, "per_commit": {"fields": ["time_ratio", "failing", "missed"]},
    }
    report["policies"]["retest_all"] = _measure(test_commits, lambda group: ([r.test_id for r in group], None))
    report["ordering"]["rules"] = _ordering_metrics(
        test_commits, lambda group: order_by_baseline("recent_failures", group))
    variants = {"raw": raw}
    if fitted.calibrator is not None:
        variants["calibrated"] = fitted.calibrator.transform(raw)
    raw_lookup = dict(zip(keys, raw))
    report["ordering"]["ml_raw"] = _ordering_metrics(
        test_commits, lambda group: [row.test_id for row in sorted(
            group, key=lambda r: (-raw_lookup[(r.commit, r.test_id)], r.test_id))])
    for variant, scores in variants.items():
        lookup = dict(zip(keys, scores))

        def probabilities(group):
            return [lookup[(row.commit, row.test_id)] for row in group]

        report["probability"][variant] = {
            "pr_auc": float(average_precision_score(labels, scores)) if any(labels) else None,
            "positive_rate": sum(labels) / len(labels),
            "brier": brier_score(scores, labels), "ece": expected_calibration_error(scores, labels)}
        report["policies"][f"ml_budget_{variant}"] = _measure(
            test_commits, _ml_policy(probabilities, RiskPolicy(budget=budget)))
        report["b10"][variant] = _hybrid_vs_rules(
            report["per_commit"], variant, test_commits, probabilities, risk_target)
        if "rules_budget" not in report["policies"]:
            report["policies"]["rules_budget"] = _measure(
                test_commits, _rules_policy(probabilities, RiskPolicy(budget=budget)))
    return report
