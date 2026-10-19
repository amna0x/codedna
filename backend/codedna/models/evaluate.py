"""Chronological evaluation of test-ordering strategies (D-023).

Commits with results are split by time: oldest 60 % train, next 20 %
validation (reserved for calibration in Milestone 5), latest 20 % test.
ML models are fitted on the train split only. Prioritisation metrics are
averaged over commits that have at least one failing test; probability
metrics (PR-AUC, Brier score) are computed over all rows of a split.
"""

from __future__ import annotations

from statistics import mean

from codedna.models.metrics import apfd, apfdc, recall_at_budget, time_to_first_failure
from codedna.models.rankers import BASELINES, ML_MODELS, MLRanker, order_by_baseline
from codedna.test_history.features import Dataset, Row

SPLITS = (("train", 0.6), ("validation", 0.2), ("test", 0.2))
BUDGETS = (0.25, 0.5)


def chronological_split(dataset: Dataset) -> dict[str, list[str]]:
    commits = dataset.commits
    n = len(commits)
    train_end = int(round(n * SPLITS[0][1]))
    valid_end = train_end + int(round(n * SPLITS[1][1]))
    return {"train": commits[:train_end], "validation": commits[train_end:valid_end],
            "test": commits[valid_end:]}


def evaluate(dataset: Dataset, *, rankers: list[str] | None = None, seed: int = 0) -> dict:
    rankers = list(rankers or (*BASELINES, *ML_MODELS))
    unknown = [r for r in rankers if r not in BASELINES and r not in ML_MODELS]
    if unknown:
        raise ValueError(f"unknown rankers {unknown}; choose from {BASELINES + ML_MODELS}")
    splits = chronological_split(dataset)
    by_commit = dataset.rows_by_commit()
    warnings = list(dataset.warnings)
    if len(dataset.commits) < 5:
        warnings.append("fewer than 5 commits with results; splits are too small to mean much")

    models: dict[str, MLRanker] = {}
    train_rows = [row for sha in splits["train"] for row in by_commit.get(sha, [])]
    for name in rankers:
        if name in ML_MODELS:
            model = MLRanker(name, dataset.feature_names, seed=seed)
            try:
                model.fit(train_rows)
                models[name] = model
            except ValueError as exc:
                warnings.append(f"{name} not trained: {exc}")

    report = {"protocol": {"splits": {k: len(v) for k, v in splits.items()},
                           "split_fractions": dict(SPLITS), "seed": seed,
                           "features": dataset.feature_names, "rows": len(dataset.rows)},
              "results": {}, "warnings": warnings,
              "note": "computed from the stored history only; no numbers are assumed"}
    for split in ("validation", "test"):
        commit_rows = [by_commit[sha] for sha in splits[split] if sha in by_commit]
        failing_commits = sum(1 for rows in commit_rows if any(r.label for r in rows))
        split_report = {"commits": len(commit_rows), "commits_with_failures": failing_commits,
                        "rankers": {}}
        for name in rankers:
            if name in ML_MODELS and name not in models:
                continue
            order_fn = models[name].order if name in models else \
                (lambda rows, n=name: order_by_baseline(n, rows))
            entry = _ordering_metrics(commit_rows, order_fn)
            if name in models:
                entry.update(_probability_metrics(models[name], commit_rows))
            split_report["rankers"][name] = entry
        report["results"][split] = split_report
    return report


def _ordering_metrics(commit_rows: list[list[Row]], order_fn) -> dict:
    values: dict[str, list[float]] = {"apfd": [], "apfdc": [], "ttff": [],
                                      **{f"recall_at_{int(b * 100)}pct_time": [] for b in BUDGETS}}
    for rows in commit_rows:
        failing = {r.test_id for r in rows if r.label}
        if not failing:
            continue
        order = order_fn(rows)
        times = {r.test_id: r.duration for r in rows}
        for key, value in (("apfd", apfd(order, failing)), ("apfdc", apfdc(order, failing, times)),
                           ("ttff", time_to_first_failure(order, failing, times))):
            if value is not None:
                values[key].append(value)
        for budget in BUDGETS:
            value = recall_at_budget(order, failing, times, budget)
            if value is not None:
                values[f"recall_at_{int(budget * 100)}pct_time"].append(value)
    return {f"mean_{k}": round(mean(v), 4) if v else None for k, v in values.items()} | {
        "evaluated_commits": len(values["apfd"])}


def _probability_metrics(model: MLRanker, commit_rows: list[list[Row]]) -> dict:
    from sklearn.metrics import average_precision_score, brier_score_loss

    rows = [row for group in commit_rows for row in group]
    if not rows:
        return {"pr_auc": None, "brier": None}
    labels = [row.label for row in rows]
    scores = model.predict_proba(rows)
    return {
        "pr_auc": round(float(average_precision_score(labels, scores)), 4) if any(labels) else None,
        "brier": round(float(brier_score_loss(labels, scores)), 4),
        "positive_rate": round(sum(labels) / len(labels), 4),
    }
