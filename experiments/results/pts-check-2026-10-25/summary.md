# B10 against a Predictive Test Selection baseline (B11)

Rules fixed in docs/PTS_BASELINE_PROTOCOL.md before results.

| Project | B10 time | B10 safety | B11 matched safety | B11 paper time | B11 paper test recall | B11 paper safety | B10 miss rate | B11 miss rate | B11 est. skip risk | Risk AUC |
|---|---|---|---|---|---|---|---|---|---|---|
| hikaricp | 0.3392 | 0.8272 | 0.7037 | 0.9731 | 0.9488 | 0.8889 | 0.0196 | 0.0126 | 0.0030 | 0.8194 |
| jade4j | 0.9147 | 1.0000 | 0.8750 | 0.7063 | 0.8750 | 0.8750 | 0.0000 | 0.0079 | 0.1631 | 0.5600 |
| littleproxy | 0.9128 | 0.7105 | 0.9474 | 0.9157 | 0.9847 | 0.9474 | 0.0840 | 0.0153 | 0.1052 | 0.6415 |
| wicket-bootstrap | 0.9414 | 0.9919 | 0.9758 | 0.8332 | 0.9513 | 0.9274 | 0.0049 | 0.0439 | 0.1748 | 0.9020 |

## confirmatory

Verdict: **inconclusive**

```json
{
  "projects": [],
  "verdict": "inconclusive"
}
```

## exploratory

Verdict: **inconclusive**

```json
{
  "projects": [
    "hikaricp",
    "jade4j",
    "littleproxy",
    "wicket-bootstrap"
  ],
  "b10_minus_b11_matched": {
    "time": {
      "estimate": -0.0962,
      "ci": [
        -0.1112,
        -0.0807
      ]
    },
    "recall": {
      "estimate": 0.025,
      "ci": [
        -0.0226,
        0.1013
      ]
    },
    "safety": {
      "estimate": 0.0069,
      "ci": [
        -0.0633,
        0.0912
      ]
    }
  },
  "safety_positive_projects": 3,
  "verdict": "inconclusive",
  "pooled_commits": {
    "b11_paper": {
      "time": 0.9017539464156409,
      "recall": 0.9517335146159075,
      "safety": 0.92
    },
    "b10": {
      "time": 0.6248976828385228,
      "recall": 0.995105370496261,
      "safety": 0.928
    }
  },
  "note": "previously inspected projects; exploratory only"
}
```
