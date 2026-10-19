"""Prioritisation metrics for one commit's test ordering.

Inputs are the ordered list of tests (first = run first), which of them fail,
and each test's real duration at that commit.

* APFD  — Rothermel et al.: ``1 - sum(TF_i) / (n*m) + 1/(2n)``, where TF_i is the
  1-based position of the i-th failing test, n tests, m failing tests.
* APFDc — cost-cognizant APFD (Elbaum et al.) with equal fault severities:
  ``sum_i (sum_{j >= TF_i} t_j - t_{TF_i}/2) / (sum_j t_j * m)``.
* recall@budget — share of failing tests found when running the prefix of the
  ordering whose total time fits in ``budget × total time``.
* time to first failure — share of total time spent until the first failing
  test has finished.

All return ``None`` when undefined (no failing tests, or zero total time).
"""

from __future__ import annotations


def apfd(order: list[str], failing: set[str]) -> float | None:
    positions = [i + 1 for i, test in enumerate(order) if test in failing]
    n, m = len(order), len(positions)
    if n == 0 or m == 0:
        return None
    return 1 - sum(positions) / (n * m) + 1 / (2 * n)


def apfdc(order: list[str], failing: set[str], times: dict[str, float]) -> float | None:
    costs = [max(times.get(test, 0.0), 0.0) for test in order]
    total = sum(costs)
    positions = [i for i, test in enumerate(order) if test in failing]
    if not positions or total <= 0:
        return None
    suffix = [0.0] * (len(costs) + 1)
    for i in range(len(costs) - 1, -1, -1):
        suffix[i] = suffix[i + 1] + costs[i]
    return sum(suffix[i] - costs[i] / 2 for i in positions) / (total * len(positions))


def recall_at_budget(order: list[str], failing: set[str], times: dict[str, float],
                     budget: float) -> float | None:
    if not failing & set(order):
        return None
    total = sum(max(times.get(t, 0.0), 0.0) for t in order)
    limit = budget * total
    spent, found = 0.0, 0
    for test in order:
        spent += max(times.get(test, 0.0), 0.0)
        if spent > limit + 1e-12:
            break
        found += test in failing
    return found / len(failing & set(order))


def time_to_first_failure(order: list[str], failing: set[str],
                          times: dict[str, float]) -> float | None:
    total = sum(max(times.get(t, 0.0), 0.0) for t in order)
    if total <= 0 or not failing & set(order):
        return None
    spent = 0.0
    for test in order:
        spent += max(times.get(test, 0.0), 0.0)
        if test in failing:
            return spent / total
    return None
