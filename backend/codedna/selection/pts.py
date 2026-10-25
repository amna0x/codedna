"""Predictive Test Selection baseline (B11; docs/PTS_BASELINE_PROTOCOL.md).

After Machalica et al., "Predictive Test Selection", ICSE-SEIP 2019: tests
whose score reaches a score cutoff, plus the N highest-scoring tests, with
both cutoffs tuned on held-out commits to an *aggregate* test-recall and
change-recall target. Changed test classes are always selected, as in every
CodeDNA policy. Research baseline only: it gives no per-commit risk.
"""

from __future__ import annotations

from dataclasses import dataclass

from codedna.test_history.features import Row

TEST_RECALL = 0.95
CHANGE_RECALL = 0.999


@dataclass(frozen=True)
class Cutoffs:
    score: float  # select tests with score >= this; > 1 selects none by score
    count: int    # also select the ``count`` highest-scoring tests


def select(rows: list[Row], scores: list[float], cutoffs: Cutoffs) -> list[str]:
    """Selected test ids, in row order. Ties at the count cutoff are all selected."""
    ranked = sorted(scores, reverse=True)
    count_floor = ranked[cutoffs.count - 1] if 0 < cutoffs.count <= len(ranked) else (
        float("-inf") if cutoffs.count > len(ranked) else float("inf"))
    return [r.test_id for r, s in zip(rows, scores)
            if r.features.get("test_file_changed") or s >= cutoffs.score or s >= count_floor]


def tune(commits: list[tuple[list[Row], list[float]]], *, test_recall: float = TEST_RECALL,
         change_recall: float = CHANGE_RECALL) -> Cutoffs:
    """Cutoffs from held-out ``(rows, scores)`` commits.

    The score cutoff is the largest score at which test recall, with no count
    cutoff, reaches ``test_recall``; the count cutoff is the smallest N at which
    change recall, with no score cutoff, reaches ``change_recall``.
    Raises ``ValueError`` when the commits hold no failing test.
    """
    failing = [(rows, scores) for rows, scores in commits if any(r.label for r in rows)]
    if not failing:
        raise ValueError("no failing tests in the tuning commits")
    return Cutoffs(_score_cutoff(failing, test_recall), _count_cutoff(failing, change_recall))


def _score_cutoff(failing, target: float) -> float:
    # A failing row is caught by its own score or by a changed test class.
    free = sum(1 for rows, _ in failing for r in rows if r.label and r.features.get("test_file_changed"))
    scored = sorted((s for rows, scores in failing for r, s in zip(rows, scores)
                     if r.label and not r.features.get("test_file_changed")), reverse=True)
    total = free + len(scored)
    if free >= target * total or not scored:
        return float("inf")
    needed = target * total - free
    caught = 0
    for s in scored:
        caught += 1
        if caught >= needed - 1e-9:
            return s
    return scored[-1]


def _count_cutoff(failing, target: float) -> int:
    # Per failing commit: the rank (1-based, ties counted at their first place)
    # of its best failing test; 0 when a changed failing test class catches it.
    ranks = []
    for rows, scores in failing:
        if any(r.label and r.features.get("test_file_changed") for r in rows):
            ranks.append(0)
            continue
        best = max(s for r, s in zip(rows, scores) if r.label)
        ranks.append(1 + sum(1 for s in scores if s > best))
    ranks.sort()
    needed = target * len(ranks)
    for i, rank in enumerate(ranks, start=1):
        if i >= needed - 1e-9:
            return rank
    return ranks[-1]
