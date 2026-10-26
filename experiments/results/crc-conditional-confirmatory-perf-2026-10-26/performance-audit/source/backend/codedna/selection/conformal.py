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
