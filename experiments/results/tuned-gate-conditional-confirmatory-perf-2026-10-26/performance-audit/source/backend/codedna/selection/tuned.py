"""Fixed-sequence search for the stopping threshold (B13; docs/TUNED_GATE_PROTOCOL.md).

The D-041 gate checks one threshold and falls back to the full suite when it
fails. Here the same check is applied to each threshold from the strictest
upwards, stopping at the first failure (fixed-sequence testing, as in
Learn-then-Test). Each threshold is tested only after every stricter one
passed, so the family keeps the gate's own level.
"""

from __future__ import annotations

from codedna.selection.validation import validate_outcomes

FULL = None  # run every test
GRID = (0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5)


def search(outcomes_at, risk_target: float = 0.05, grid=GRID):
    """Largest threshold passing the D-041 check with every stricter one, else ``FULL``.

    ``outcomes_at(value)`` returns the audit outcomes ``(time, failing, missed)``
    of stopping at estimated skip risk ``value``. Returns the chosen threshold
    and the evidence of every threshold tested, in order.
    """
    best, tested = FULL, []
    for value in sorted(grid):
        evidence = validate_outcomes(outcomes_at(value), risk_target)
        tested.append((value, evidence))
        if not evidence.accepted:
            break
        best = value
    return best, tested
