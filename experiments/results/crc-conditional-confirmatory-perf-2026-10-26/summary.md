# Conformal-risk-control stopping (B12f) against B10 and the gated product

Rules fixed in docs/CRC_CONDITIONAL_PROTOCOL.md before results.

| Project | B10 time | B10 miss | B12f time | B12f miss | B12f safety | Product time | Product miss | Thresholds |
|---|---|---|---|---|---|---|---|---|
| buck | 0.0734 | 0.0498 | 0.4344 | 0.0118 | 0.9704 | 1.0000 | 0.0000 | full, 0.001, 0.005, 0.01, 0.01 |
| cloudify | 0.0475 | 0.0321 | 0.6884 | 0.0073 | 0.8784 | 1.0000 | 0.0000 | 0.002, 0.002, 0.002, full, 0.0002 |
| deeplearning4j | 0.5188 | 0.0390 | 0.7789 | 0.0229 | 0.9512 | 0.8839 | 0.0069 | 0.1, 0.02, 0.01, 0.002, 0.002 |
| dspace | 0.4736 | 0.0385 | 0.9589 | 0.0000 | 1.0000 | 0.9763 | 0.0011 | full, 0.0001, 0.0002, 0.02, full |
| jetty.project | 0.5942 | 0.0729 | 0.8241 | 0.0104 | 0.9884 | 1.0000 | 0.0000 | 0.005, 0.05, 0.1, 0.005, 0.01 |
| okhttp | 0.4001 | 0.0320 | 0.6272 | 0.0080 | 0.9622 | 0.6910 | 0.0187 | 0.01, 0.01, 0.01, 0.02, 0.02 |
| sling | 0.5992 | 0.0427 | 0.7776 | 0.0142 | 0.9649 | 0.9119 | 0.0085 | 0.02, 0.02, 0.01, 0.005, 0.002 |
| sonarqube | 0.2110 | 0.0304 | 0.9223 | 0.0013 | 0.9828 | 1.0000 | 0.0000 | full, 0.002, 0.001, 0.005, 0.002 |
| titan | 0.7712 | 0.0105 | 0.9605 | 0.0052 | 0.9811 | 0.9672 | 0.0052 | 0.01, 0.02, 0.05, full, 0.002 |

## confirmatory

Verdict: **B12f saves time**

```json
{
  "projects": [
    "buck",
    "cloudify",
    "deeplearning4j",
    "dspace",
    "jetty.project",
    "okhttp",
    "sling",
    "sonarqube",
    "titan"
  ],
  "b12_minus_product": {
    "time": {
      "estimate": -0.162,
      "ci": [
        -0.1687,
        -0.1553
      ]
    },
    "recall": {
      "estimate": -0.0173,
      "ci": [
        -0.0253,
        -0.0095
      ]
    },
    "safety": {
      "estimate": -0.0179,
      "ci": [
        -0.0272,
        -0.0084
      ]
    }
  },
  "projects_keeping_target": {
    "b10": 1,
    "b12": 8,
    "product": 8
  },
  "verdict": "B12f saves time",
  "pooled_commits": {
    "b10": {
      "time": 0.27553303272352486,
      "recall": 0.5768115942028986,
      "safety": 0.7980480480480481,
      "miss_rate": 0.03465601649059521
    },
    "b12": {
      "time": 0.765771751980883,
      "recall": 0.9817795323413301,
      "safety": 0.9587932303164092,
      "miss_rate": 0.007043139227770092
    },
    "product": {
      "time": 0.9385656521192303,
      "recall": 0.9896750683267537,
      "safety": 0.9764532744665195,
      "miss_rate": 0.004024650987297196
    }
  }
}
```

## exploratory

Verdict: **inconclusive**

```json
{
  "projects": [],
  "verdict": "inconclusive",
  "note": "previously inspected projects; exploratory only"
}
```
