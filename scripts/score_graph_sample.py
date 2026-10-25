"""Precision per confidence label from labelled graph samples (M2).

Reads CSVs written by ``scripts/sample_graph_edges.py`` after a person filled
in ``label``. Precision counts ``correct`` among ``correct`` + ``incorrect``;
``unclear`` rows are reported separately and left out. The interval is a
two-sided 95 % Wilson score interval. Rows without a label stop the script.

Usage:
    python scripts/score_graph_sample.py SAMPLE.csv [SAMPLE.csv ...]
"""

from __future__ import annotations

import csv
import json
import sys
from math import sqrt
from pathlib import Path

Z = 1.959963984540054


def wilson(correct: int, total: int) -> list[float] | None:
    if total == 0:
        return None
    p = correct / total
    centre = (p + Z * Z / (2 * total)) / (1 + Z * Z / total)
    half = Z * sqrt(p * (1 - p) / total + Z * Z / (4 * total * total)) / (1 + Z * Z / total)
    return [round(centre - half, 4), round(centre + half, 4)]


def score(paths: list[Path]) -> dict:
    groups: dict[str, dict[str, int]] = {}
    for path in paths:
        for row in csv.DictReader(open(path, encoding="utf-8")):
            label = row["label"].strip()
            if label not in ("correct", "incorrect", "unclear"):
                raise SystemExit(f"{path} row {row['row']}: label must be correct, incorrect "
                                 f"or unclear, not {label!r}")
            for key in (row["confidence"], "all"):
                counts = groups.setdefault(key, {"correct": 0, "incorrect": 0, "unclear": 0})
                counts[label] += 1
    result = {}
    for key, counts in groups.items():
        judged = counts["correct"] + counts["incorrect"]
        result[key] = {**counts, "precision": round(counts["correct"] / judged, 4) if judged else None,
                       "wilson_95": wilson(counts["correct"], judged)}
    return {"samples": [str(p) for p in paths], "by_confidence": result}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print(json.dumps(score([Path(p) for p in sys.argv[1:]]), indent=2))
