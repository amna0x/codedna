"""Cost-matched comparisons and bootstrap confidence intervals (D-035).

A fallback policy spends more test time than a plain budgeted selector, so
comparing them at their default settings mixes "smarter" with "ran more".
``match_budget`` finds the budget at which the calibrated selector (B8) spends
the same real test time as a given policy, and the comparison is made there.

Uncertainty comes from resampling **test commits** with replacement
(percentile bootstrap, fixed seed). Differences between two policies are
*paired*: both are evaluated on the same resampled commits. Commits are
treated as independent, which ignores correlation between neighbouring
commits — the intervals are therefore somewhat optimistic.

Per-commit outcomes are compact triples ``(time_ratio, failing, missed)``.
"""

from __future__ import annotations

import random
from typing import Callable

Outcome = tuple[float, int, int]  # (time ratio, failing tests, missed failing tests)
METRICS = ("time", "recall", "safety")


def metrics(outcomes: list[Outcome]) -> dict[str, float | None]:
    if not outcomes:
        return {"time": None, "recall": None, "safety": None}
    failing = sum(o[1] for o in outcomes)
    failing_commits = [o for o in outcomes if o[1]]
    return {
        "time": sum(o[0] for o in outcomes) / len(outcomes),
        "recall": 1 - sum(o[2] for o in outcomes) / failing if failing else None,
        "safety": sum(o[2] == 0 for o in failing_commits) / len(failing_commits)
        if failing_commits else None,
    }


def match_budget(measure: Callable[[float], list[Outcome]], target_time: float,
                 iterations: int = 14) -> tuple[float, list[Outcome]]:
    """Budget in [0, 1] whose mean real time ratio is closest to ``target_time``.

    Time grows (weakly) with the budget, so a bisection works; the closest
    point seen is returned.
    """
    low, high = 0.0, 1.0
    best = (abs(metrics(measure(1.0))["time"] - target_time), 1.0)
    for _ in range(iterations):
        middle = (low + high) / 2
        time = metrics(measure(middle))["time"]
        best = min(best, (abs(time - target_time), middle))
        if time < target_time:
            low = middle
        else:
            high = middle
    budget = round(best[1], 4)
    return budget, measure(budget)


def bootstrap(outcomes: dict[str, list[Outcome]], pairs: dict[str, tuple[str, str]], *,
              resamples: int = 1000, seed: int = 0, level: float = 0.95) -> dict:
    """Percentile intervals for each policy's metrics and for paired differences.

    ``outcomes`` maps policy → per-commit outcomes in the same commit order;
    ``pairs`` maps a comparison name → (policy A, policy B), reported as A − B.
    """
    names = list(outcomes)
    n = len(next(iter(outcomes.values()), []))
    samples: dict[str, dict[str, list[float]]] = {name: {m: [] for m in METRICS} for name in names}
    diffs: dict[str, dict[str, list[float]]] = {pair: {m: [] for m in METRICS} for pair in pairs}
    rng = random.Random(seed)
    for _ in range(resamples if n else 0):
        index = [rng.randrange(n) for _ in range(n)]
        values = {name: metrics([outcomes[name][i] for i in index]) for name in names}
        for name in names:
            for metric in METRICS:
                if values[name][metric] is not None:
                    samples[name][metric].append(values[name][metric])
        for pair, (a, b) in pairs.items():
            for metric in METRICS:
                if values[a][metric] is not None and values[b][metric] is not None:
                    diffs[pair][metric].append(values[a][metric] - values[b][metric])
    return {
        "method": f"percentile bootstrap over test commits, {resamples} resamples, seed {seed}",
        "level": level,
        "policies": {name: {m: _interval(samples[name][m], level) for m in METRICS} for name in names},
        "differences": {
            pair: {m: {"estimate": _difference(outcomes[a], outcomes[b], m),
                       "ci": _interval(diffs[pair][m], level)} for m in METRICS}
            for pair, (a, b) in pairs.items()},
    }


def _difference(a: list[Outcome], b: list[Outcome], metric: str) -> float | None:
    x, y = metrics(a)[metric], metrics(b)[metric]
    return None if x is None or y is None else round(x - y, 4)


def _interval(values: list[float], level: float) -> list[float] | None:
    if len(values) < 20:
        return None  # too few valid resamples (e.g. almost no failing commits)
    values = sorted(values)
    tail = (1 - level) / 2
    low = values[int(tail * (len(values) - 1))]
    high = values[int((1 - tail) * (len(values) - 1))]
    return [round(low, 4), round(high, 4)]
