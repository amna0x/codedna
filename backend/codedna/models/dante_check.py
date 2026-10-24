"""DANTE-H vs calibrated stopping (D-040, docs/DANTE_B10_PROTOCOL.md).

Policies on the test split (same split, model and calibrator as
``run_experiment``):

* ``D1`` DANTE-H order, time budget matched to D2's real time;
* ``D2`` DANTE-H order, add tests until calibrated skip risk ≤ target;
* ``B3`` rules order, budget matched to D2 (and to B10 for comparison 3);
* ``B10`` rules order, calibrated stopping.
"""

from __future__ import annotations

import time

from codedna.calibration.calibrators import Calibrator
from codedna.models.evaluate import chronological_split
from codedna.models.experiment import _measure, _outcomes, _rounded, _rules_policy
from codedna.models.rankers import MLRanker
from codedna.models.uncertainty import bootstrap, match_budget
from codedna.models.uncertainty import metrics as outcome_metrics
from codedna.selection.dante import WINDOWS, dante_scores, order_by_dante
from codedna.selection.risk import RiskPolicy, decide
from codedna.test_history.features import Dataset


def dante_check(dataset: Dataset, *, model: str = "gradient_boosting",
                calibration: str = "isotonic", risk_target: float = 0.05,
                seed: int = 0) -> dict:
    started = time.perf_counter()
    scores = dante_scores(dataset)
    scoring_seconds = time.perf_counter() - started

    splits = chronological_split(dataset)
    by_commit = dataset.rows_by_commit()
    rows_of = lambda split: [r for sha in splits[split] for r in by_commit.get(sha, [])]  # noqa: E731
    train, valid = rows_of("train"), rows_of("validation")
    test_commits = [by_commit[sha] for sha in splits["test"] if sha in by_commit]
    warnings: list[str] = []
    report = {
        "config": {"model": model, "calibration": calibration, "risk_target": risk_target,
                   "seed": seed, "dante": {"variant": "DANTE-H (history only, no TF-IDF relevance)",
                                           "windows": list(WINDOWS)},
                   "splits": {k: len(v) for k, v in splits.items()}},
        "warnings": warnings,
        "note": "computed from the stored history only; protocol fixed in docs/DANTE_B10_PROTOCOL.md",
    }

    ranker = MLRanker(model, dataset.feature_names, seed=seed)
    try:
        ranker.fit(train)
    except ValueError as exc:
        warnings.append(f"model not trained: {exc}")
        return report
    try:
        calibrator = Calibrator(calibration).fit(ranker.predict_proba(valid),
                                                 [r.label for r in valid])
    except ValueError as exc:
        warnings.append(f"calibrator not fitted ({exc}); raw probabilities used")
        calibrator = Calibrator("none")

    memo: dict[str, list[float]] = {}

    def probabilities(rows):
        commit = rows[0].commit if rows else ""
        if commit not in memo:
            memo[commit] = calibrator.transform(ranker.predict_proba(rows))
        return memo[commit]

    def dante_policy(policy: RiskPolicy):
        def choose(rows):
            decision = decide(rows, probabilities(rows), policy,
                              order=order_by_dante(scores, rows))
            return decision.selected, decision
        return choose

    stop = RiskPolicy(budget=None, risk_target=risk_target)
    policies = {"D2_dante_stop": dante_policy(stop), "B10_hybrid": _rules_policy(probabilities, stop)}
    for rows in test_commits:  # warm the probability cache so timing covers decisions only
        probabilities(rows)
    started = time.perf_counter()
    for rows in test_commits:
        policies["D2_dante_stop"](rows)
    decide_ms = (time.perf_counter() - started) * 1000 / max(len(test_commits), 1)

    outcomes = {name: _outcomes(test_commits, fn) for name, fn in policies.items()}
    measured = {name: _measure(test_commits, fn) for name, fn in policies.items()}
    budgeted = {
        "D1": lambda b: _outcomes(test_commits, dante_policy(RiskPolicy(budget=b))),
        "B3": lambda b: _outcomes(test_commits, _rules_policy(probabilities, RiskPolicy(budget=b))),
    }
    matched = {}
    for key, baseline, target_policy in (("D1@D2", "D1", "D2_dante_stop"),
                                          ("B3@D2", "B3", "D2_dante_stop"),
                                          ("B3@B10", "B3", "B10_hybrid")):
        target = outcome_metrics(outcomes[target_policy])["time"]
        budget, same_time = match_budget(budgeted[baseline], target)
        outcomes[key] = same_time
        matched[key] = {"budget": budget, **_rounded(outcome_metrics(same_time))}
    pairs = {"D2 − D1 at same time": ("D2_dante_stop", "D1@D2"),
             "D2 − B10": ("D2_dante_stop", "B10_hybrid"),
             "B10 − B3 at same time": ("B10_hybrid", "B3@B10"),
             "D1 − B3 at D2 time": ("D1@D2", "B3@D2")}
    report["policies"] = measured
    report["cost_matched"] = matched
    report["bootstrap"] = bootstrap(outcomes, pairs, seed=seed)
    report["overhead"] = {"dante_scoring_seconds_all_rows": round(scoring_seconds, 3),
                          "rows": len(dataset.rows),
                          "d2_decide_ms_per_test_commit": round(decide_ms, 3)}
    report["per_commit"] = {"fields": ["time_ratio", "failing", "missed"],
                            **{name: [list(o) for o in values] for name, values in outcomes.items()}}
    return report
