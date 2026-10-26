# Conformal-risk-control stopping (B12f) against B10 and the gated product

Rules fixed in docs/CRC_CONDITIONAL_PROTOCOL.md before results.

| Project | B10 time | B10 miss | B12f time | B12f miss | B12f safety | Product time | Product miss | Thresholds |
|---|---|---|---|---|---|---|---|---|
| hikaricp | 0.3392 | 0.0196 | 0.9995 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | full, 0.01, 0.005, 0.01, 0.005 |
| jade4j | 0.9147 | 0.0000 | 0.9651 | 0.0000 | 1.0000 | 0.9838 | 0.0000 | full, 0.1, full, full, full |
| littleproxy | 0.9128 | 0.0840 | 0.9980 | 0.0000 | 1.0000 | 0.9976 | 0.0000 | full, 0.02, 0.02, full, full |
| wicket-bootstrap | 0.9414 | 0.0049 | 0.7737 | 0.0146 | 0.9758 | 0.9414 | 0.0049 | 0.05, 0.3, 0.5, 0.5, 0.2 |

## confirmatory

Verdict: **inconclusive**

```json
{
  "projects": [],
  "verdict": "inconclusive"
}
```

## exploratory

Verdict: **B12f saves time**

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
      "estimate": -0.0467,
      "ci": [
        -0.0541,
        -0.0403
      ]
    },
    "recall": {
      "estimate": -0.0003,
      "ci": [
        -0.0006,
        -0.0
      ]
    },
    "safety": {
      "estimate": -0.004,
      "ci": [
        -0.0083,
        -0.001
      ]
    }
  },
  "projects_keeping_target": {
    "b10": 2,
    "b12": 4,
    "product": 4
  },
  "verdict": "B12f saves time",
  "pooled_commits": {
    "b10": {
      "time": 0.6248976828385228,
      "recall": 0.995105370496261,
      "safety": 0.928,
      "miss_rate": 0.01955104996379435
    },
    "b12": {
      "time": 0.9299636685552408,
      "recall": 0.9988480737232817,
      "safety": 0.9848101265822785,
      "miss_rate": 0.00424929178470255
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
