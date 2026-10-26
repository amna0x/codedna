"""Risk-aware test selection with an uncertainty fallback (Milestone 5, D-026).

Input: one commit's candidate tests with (ideally calibrated) failure
probabilities ``p`` and *estimated* costs (historical mean duration — the
real duration of this run is unknown when selecting).

1. Tests are ordered by ``p / cost`` (most risk removed per second first),
   or by a caller-supplied order (e.g. a simple rule such as recent failures
   first, so the probabilities only decide *how many* tests to run);
   changed test classes and ``always`` tests (must-run policy, D-050) are
   always selected; they count as run when the skip risk is computed.
2. **Budget**: take the prefix that fits ``budget × total estimated time``.
3. **Risk target**: estimated *skip risk* = probability that at least one
   skipped test fails, ``1 − Π(1 − p)`` over skipped tests. This assumes
   failures are independent, which they are not always (one bug can fail
   several tests) — the experiments measure how well the estimate holds.
4. **Fallback** (when enabled):
   * if the skip risk after the budget is above the target, keep adding tests
     until it is not (possibly running everything);
   * run everything when the model is on unfamiliar ground: non-Java files
     changed (not analysed), or most candidate tests have no history.

Every decision carries human-readable reasons.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from codedna.test_history.features import Row


@dataclass
class RiskPolicy:
    budget: float | None = 0.5  # fraction of estimated total time; None = no budget
    risk_target: float | None = None  # max acceptable estimated skip risk
    fallback: bool = False
    non_java_fallback: bool = True
    max_unknown_test_share: float = 0.5


@dataclass
class SelectionDecision:
    selected: list[str]
    skipped: list[str]
    estimated_skip_risk: float
    expected_missed_failures: float
    estimated_time_fraction: float
    fallback: bool = False
    reasons: list[str] = field(default_factory=list)


def decide(rows: list[Row], probabilities: list[float], policy: RiskPolicy, *,
           order: list[str] | None = None,
           always: frozenset[str] | set[str] = frozenset()) -> SelectionDecision:
    if not rows:
        return SelectionDecision([], [], 0.0, 0.0, 0.0)
    prob = {row.test_id: min(max(p, 0.0), 1.0) for row, p in zip(rows, probabilities)}
    cost = _estimated_costs(rows)
    total_cost = sum(cost.values())
    reasons: list[str] = []

    if policy.fallback:
        reason = _unfamiliar(rows, policy)
        if reason:
            return _decision(rows, set(prob), prob, cost, total_cost, True,
                             [f"fallback to retest-all: {reason}"])

    if order is None:
        order = sorted(rows, key=lambda r: (-prob[r.test_id] / cost[r.test_id],
                                            -prob[r.test_id], r.test_id))
    else:
        by_id = {r.test_id: r for r in rows}
        order = [by_id[t] for t in order if t in by_id]
        reasons.append("tests taken in the given order")
    selected = {r.test_id for r in rows if r.features.get("test_file_changed")}
    if selected:
        reasons.append(f"{len(selected)} changed test class(es) always run")
    pinned = {t for t in always if t in prob} - selected
    if pinned:
        selected |= pinned
        reasons.append(f"{len(pinned)} must-run test class(es) always run")

    spent = sum(cost[t] for t in selected)
    if policy.budget is not None:
        limit = policy.budget * total_cost
        for row in order:
            if row.test_id not in selected and spent + cost[row.test_id] <= limit + 1e-12:
                selected.add(row.test_id)
                spent += cost[row.test_id]
        reasons.append(f"filled {policy.budget:.0%} time budget by risk per second")

    fallback = False
    target = policy.risk_target
    if target is not None and _skip_risk(prob, selected) > target:
        before = _skip_risk(prob, selected)
        if policy.budget is None or policy.fallback:
            for row in order:
                if _skip_risk(prob, selected) <= target:
                    break
                selected.add(row.test_id)
            if policy.budget is None:
                reasons.append(f"added tests until estimated skip risk ≤ {target:.3f}")
            else:
                fallback = True
                reasons.append(f"fallback: estimated skip risk {before:.3f} exceeded target "
                               f"{target:.3f} within the budget; selection broadened")
        else:
            reasons.append(f"estimated skip risk {before:.3f} is above target {target:.3f} "
                           "(fallback disabled)")
    return _decision(rows, selected, prob, cost, total_cost, fallback, reasons)


def _unfamiliar(rows: list[Row], policy: RiskPolicy) -> str | None:
    features = rows[0].features
    if policy.non_java_fallback and features.get("non_java_files_changed", 0) > 0:
        return f"{int(features['non_java_files_changed'])} non-Java file(s) changed (not analysed)"
    unknown = sum(1 for r in rows if r.features.get("past_runs", 0) == 0) / len(rows)
    if unknown > policy.max_unknown_test_share:
        return f"{unknown:.0%} of tests have no history"
    return None


def _estimated_costs(rows: list[Row]) -> dict[str, float]:
    known = sorted(r.features.get("mean_duration", 0.0) for r in rows
                   if r.features.get("mean_duration", 0.0) > 0)
    default = known[len(known) // 2] if known else 1.0  # median for tests without history
    return {r.test_id: r.features.get("mean_duration", 0.0) or default for r in rows}


def _skip_risk(prob: dict[str, float], selected: set[str]) -> float:
    log_survive = sum(math.log1p(-min(p, 1 - 1e-12)) for t, p in prob.items() if t not in selected)
    return 1 - math.exp(log_survive)


def _decision(rows, selected, prob, cost, total_cost, fallback, reasons) -> SelectionDecision:
    ordered = [r.test_id for r in rows]
    return SelectionDecision(
        selected=[t for t in ordered if t in selected],
        skipped=[t for t in ordered if t not in selected],
        estimated_skip_risk=round(_skip_risk(prob, set(selected)), 6),
        expected_missed_failures=round(sum(p for t, p in prob.items() if t not in selected), 6),
        estimated_time_fraction=round(sum(cost[t] for t in selected) / total_cost, 6)
        if total_cost else 1.0,
        fallback=fallback, reasons=reasons,
    )
