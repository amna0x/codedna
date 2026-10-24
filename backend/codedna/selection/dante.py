"""DANTE-H: history-only approximation of DANTE (ICST 2026), D-040.

DANTE scores each test by ``FV = V · f / t`` with
``V = norm(HistoryScore) + norm(RelevanceScore)``. CodeDNA approximates only
the history part; the TF-IDF change/test relevance is **not** implemented
(RelevanceScore = 0), so this is labelled DANTE-H everywhere.

* ``THFR`` — failures / executions over all earlier runs of the test;
* ``StickyScore`` — for each look-back window ``n`` in ``WINDOWS`` whose
  precondition holds now (the test failed at least once in its last ``n``
  runs), the historical estimate ``p̂_n = P(fail | a failure in the previous
  n runs)``, averaged with weights ``1 − (U − L)`` from its 95 % Wilson
  interval;
* ``f`` — failures in the last ``max(WINDOWS)`` runs; ``t`` — historical mean
  duration (the cost estimate all policies use).

A "build" is an earlier commit in the dataset at which the test ran. Every
quantity uses only commits strictly before the scored one.
"""

from __future__ import annotations

import math
from collections import defaultdict, deque

from codedna.test_history.features import Dataset, Row

WINDOWS = tuple(range(1, 11))
Z = 1.959964  # 95 % two-sided


def wilson(failures: int, trials: int) -> tuple[float, float]:
    if trials == 0:
        return 0.0, 1.0
    p = failures / trials
    denominator = 1 + Z * Z / trials
    centre = (p + Z * Z / (2 * trials)) / denominator
    half = Z * math.sqrt(p * (1 - p) / trials + Z * Z / (4 * trials * trials)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


class _State:
    def __init__(self) -> None:
        self.runs = 0
        self.fails = 0
        self.recent: deque[int] = deque(maxlen=max(WINDOWS))  # newest last
        self.cond = [0] * len(WINDOWS)  # runs preceded by a failure within n runs
        self.cond_fail = [0] * len(WINDOWS)

    def _failed_within(self) -> list[bool]:
        seen, flags = False, []
        recent = list(self.recent)
        for n in WINDOWS:
            seen = seen or (len(recent) >= n and recent[-n] == 1)
            flags.append(seen)
        return flags

    def history_score(self) -> tuple[float, int]:
        thfr = self.fails / self.runs if self.runs else 0.0
        weighted = weights = 0.0
        for i, holds in enumerate(self._failed_within()):
            if holds and self.cond[i]:
                low, high = wilson(self.cond_fail[i], self.cond[i])
                confidence = 1 - (high - low)
                weighted += self.cond_fail[i] / self.cond[i] * confidence
                weights += confidence
        sticky = weighted / weights if weights else 0.0
        return thfr + sticky, sum(self.recent)

    def update(self, label: int) -> None:
        for i, holds in enumerate(self._failed_within()):
            if holds:
                self.cond[i] += 1
                self.cond_fail[i] += label
        self.runs += 1
        self.fails += label
        self.recent.append(label)


def dante_scores(dataset: Dataset) -> dict[tuple[str, str], float]:
    """``FV`` for every (commit, test) row, from strictly earlier commits only."""
    states: dict[str, _State] = defaultdict(_State)
    by_commit = dataset.rows_by_commit()
    scores: dict[tuple[str, str], float] = {}
    for sha in dataset.commits:
        rows = by_commit.get(sha, [])
        history = {r.test_id: states[r.test_id].history_score() for r in rows}
        values = [h for h, _ in history.values()]
        low, high = (min(values), max(values)) if values else (0.0, 0.0)
        for row in rows:
            h, recent_failures = history[row.test_id]
            normalised = (h - low) / (high - low) if high > low else 0.0
            cost = row.features.get("mean_duration", 0.0) or 1.0
            scores[(sha, row.test_id)] = normalised * recent_failures / cost
        for row in rows:  # update only after the whole commit is scored
            states[row.test_id].update(row.label)
    return scores


def order_by_dante(scores: dict[tuple[str, str], float], rows: list[Row]) -> list[str]:
    key = lambda r: (-scores.get((r.commit, r.test_id), 0.0),  # noqa: E731
                     r.features.get("mean_duration", 0.0), r.test_id)
    return [r.test_id for r in sorted(rows, key=key)]
