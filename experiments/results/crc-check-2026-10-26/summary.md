# Conformal-risk-control stopping (B12) against B10 and the gated product

Rules fixed in docs/CRC_STOP_PROTOCOL.md before results.

| Project | B10 time | B10 miss | B12 time | B12 miss | B12 safety | Product time | Product miss | Thresholds |
|---|---|---|---|---|---|---|---|---|
| hikaricp | 0.3392 | 0.0196 | 0.1098 | 0.0560 | 0.5062 | 1.0000 | 0.0000 | 0.5, 0.1, 0.1, 0.2, 0.05 |
| jade4j | 0.9147 | 0.0000 | 0.7001 | 0.0127 | 0.9286 | 0.9838 | 0.0000 | full, 0.2, 0.1, 0.5, 0.5 |
| littleproxy | 0.9128 | 0.0840 | 0.9320 | 0.0000 | 1.0000 | 0.9976 | 0.0000 | 0.005, 0.02, 0.02, 0.1, 0.5 |
| wicket-bootstrap | 0.9414 | 0.0049 | 0.7283 | 0.0146 | 0.9758 | 0.9414 | 0.0049 | 0.2, 0.3, 0.5, 0.5, 0.2 |

## confirmatory

Verdict: **inconclusive**

```json
{
  "projects": [],
  "verdict": "inconclusive"
}
```

## exploratory

Verdict: **B12 saves time**

```json
{
  "projects": [
    "hikaricp",
    "jade4j",
    "littleproxy",
    "wicket-bootstrap"
  ],
  "b12_minus_product": {
    "time": {
      "estimate": -0.3632,
      "ci": [
        -0.379,
        -0.3478
      ]
    },
    "recall": {
      "estimate": -0.1432,
      "ci": [
        -0.1731,
        -0.1043
      ]
    },
    "safety": {
      "estimate": -0.1453,
      "ci": [
        -0.1849,
        -0.1098
      ]
    }
  },
  "projects_keeping_target": {
    "b10": 3,
    "b12": 3,
    "product": 4
  },
  "verdict": "B12 saves time",
  "pooled_commits": {
    "b10": {
      "time": 0.6248976828385228,
      "recall": 0.995105370496261,
      "safety": 0.928,
      "miss_rate": 0.01955104996379435
    },
    "b12": {
      "time": 0.43130927762039656,
      "recall": 0.9829770894662742,
      "safety": 0.8784810126582279,
      "miss_rate": 0.0339943342776204
    },
    "product": {
      "time": 0.980972521246459,
      "recall": 0.9997440163829515,
      "safety": 0.9949367088607595,
      "miss_rate": 0.00141643059490085
    }
  },
  "note": "previously inspected projects; exploratory only"
}
```
