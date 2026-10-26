"""Conformal risk control for the stopping threshold (B12; docs/CRC_STOP_PROTOCOL.md).

After Angelopoulos, Bates, Fisch, Lei and Schuster, "Conformal Risk Control"
(ICLR 2024): for a loss that can only fall as the threshold falls, choose the
largest threshold whose corrected held-out risk ``(n·R̂ + 1) / (n + 1)`` is at
most ``alpha``. If held-out and new commits are exchangeable, the expected
loss on a new commit is then at most ``alpha``. Commits ordered in time are
not strictly exchangeable, so the bound is checked, not assumed.
"""

from __future__ import annotations

FULL = None  # run every test; loss 0 by definition
GRID = (FULL, 0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2,
        0.3, 0.5)


def threshold(losses: dict[float | None, list[float]], alpha: float = 0.05) -> float | None:
    """Largest threshold whose bound holds for it and every smaller one, else ``FULL``.

    ``losses`` maps each threshold to per-commit losses in [0, 1] on held-out
    commits (the same commits for every threshold). Scanning upwards and
    stopping at the first violation keeps the choice valid even if the
    empirical loss is not exactly monotone.
    """
    best = FULL
    for value in sorted(v for v in losses if v is not FULL):
        row = losses[value]
        if not row or (sum(row) + 1) / (len(row) + 1) > alpha:
            break
        best = value
    return best


MIN_FAILING = 19  # with fewer, (0 + 1) / (n + 1) > 0.05 and only the full suite qualifies


def stopper(ranker, calibrator, value):
    """Recent-failures order, stopping at estimated skip risk ``value``; ``FULL`` runs all.

    One function for the offline check (``scripts/run_crc_check.py``) and the
    live brake, so both pick the same tests for the same threshold.
    """
    from codedna.models.rankers import order_by_baseline
    from codedna.selection.risk import RiskPolicy, decide

    def choose(rows):
        if value is FULL:
            return [r.test_id for r in rows], None
        d = decide(rows, calibrator.transform(ranker.predict_proba(rows)),
                   RiskPolicy(budget=None, risk_target=value),
                   order=order_by_baseline('recent_failures', rows))
        return d.selected, d
    return choose


def failing_commit_threshold(audit, ranker, calibrator, alpha=0.05):
    """B12f: the threshold bounding misses among *failing* audit commits (D-063, D-068).

    ``audit`` is a list of per-commit row lists from the held-out audit window.
    Returns ``(threshold, evidence)``; ``threshold`` is ``FULL`` when no grid
    value keeps the corrected bound at or below ``alpha``.
    """
    from codedna.models.experiment import _outcomes

    failing = [rows for rows in audit if any(r.label for r in rows)]
    losses = {v: [float(o[2] > 0) for o in _outcomes(failing, stopper(ranker, calibrator, v))]
              for v in GRID}
    chosen = threshold(losses, alpha)
    n = len(failing)
    row = losses[chosen] if chosen is not FULL else []
    bound = (sum(row) + 1) / (n + 1) if chosen is not FULL else None
    return chosen, {
        'failing_audit_commits': n, 'alpha': alpha,
        'threshold': chosen,
        'audit_miss_rate': (sum(row) / n) if chosen is not FULL and n else None,
        'corrected_bound': bound,
        'reason': None if chosen is not FULL else (
            f'fewer than {MIN_FAILING} failing audit commits' if n < MIN_FAILING
            else 'no stopping threshold keeps the corrected miss bound at or below the target'),
    }
