"""Calibration metrics: Brier score, Expected Calibration Error, reliability bins."""

from __future__ import annotations


def brier_score(probabilities: list[float], labels: list[int]) -> float | None:
    if not labels:
        return None
    return sum((p - y) ** 2 for p, y in zip(probabilities, labels)) / len(labels)


def reliability_bins(probabilities: list[float], labels: list[int], bins: int = 10) -> list[dict]:
    """Equal-width bins over [0, 1]: mean predicted probability vs observed failure rate."""
    groups: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
    for p, y in zip(probabilities, labels):
        groups[min(int(p * bins), bins - 1)].append((p, y))
    table = []
    for index, group in enumerate(groups):
        if not group:
            continue
        table.append({
            "bin": [round(index / bins, 4), round((index + 1) / bins, 4)],
            "count": len(group),
            "mean_predicted": round(sum(p for p, _ in group) / len(group), 4),
            "observed_rate": round(sum(y for _, y in group) / len(group), 4),
        })
    return table


def expected_calibration_error(probabilities: list[float], labels: list[int],
                               bins: int = 10) -> float | None:
    """ECE = sum over bins of (bin share) × |observed rate − mean predicted|."""
    if not labels:
        return None
    total = len(labels)
    return sum(b["count"] / total * abs(b["observed_rate"] - b["mean_predicted"])
               for b in reliability_bins(probabilities, labels, bins))
