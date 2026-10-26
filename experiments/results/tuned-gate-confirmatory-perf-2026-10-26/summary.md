# Tuned-threshold gate (B13) against the gated product

Rules fixed in docs/TUNED_GATE_PROTOCOL.md before results. Exploratory.

| Project | Gate blocks | B13 blocks | Product time | Product miss | Product safety | B13 time | B13 miss | B13 safety | Thresholds |
|---|---|---|---|---|---|---|---|---|---|
| buck | 0 | 4 | 1.0000 | 0.0000 | 1.0000 | 0.3953 | 0.0118 | 0.9704 | full, 0.001, 0.005, 0.01, 0.02 |
| cloudify | 0 | 5 | 1.0000 | 0.0000 | 1.0000 | 0.5544 | 0.0077 | 0.8716 | 0.005, 0.005, 0.01, 0.0002, 0.0005 |
| deeplearning4j | 1 | 5 | 0.8839 | 0.0069 | 0.9854 | 0.7734 | 0.0206 | 0.9561 | 0.05, 0.02, 0.01, 0.002, 0.01 |
| dspace | 1 | 3 | 0.9763 | 0.0011 | 0.9831 | 0.6127 | 0.0053 | 0.9153 | full, 0.002, 0.002, 0.5, full |
| jetty.project | 0 | 0 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | full, full, full, full, full |
| okhttp | 3 | 5 | 0.6910 | 0.0187 | 0.9118 | 0.4766 | 0.0258 | 0.8782 | 0.05, 0.02, 0.02, 0.05, 0.05 |
| sling | 2 | 5 | 0.9119 | 0.0085 | 0.9789 | 0.7371 | 0.0228 | 0.9439 | 0.02, 0.02, 0.1, 0.05, 0.01 |
| sonarqube | 0 | 5 | 1.0000 | 0.0000 | 1.0000 | 0.8179 | 0.0038 | 0.9483 | 0.0002, 0.005, 0.005, 0.005, 0.01 |
| titan | 1 | 4 | 0.9672 | 0.0052 | 0.9811 | 0.9605 | 0.0052 | 0.9811 | full, 0.02, 0.05, 0.01, 0.002 |

## confirmatory

Verdict: **inconclusive**

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
  "b13_minus_product": {
    "time": {
      "estimate": -0.2336,
      "ci": [
        -0.2399,
        -0.2277
      ]
    },
    "recall": {
      "estimate": -0.0312,
      "ci": [
        -0.0397,
        -0.0235
      ]
    },
    "safety": {
      "estimate": -0.0417,
      "ci": [
        -0.0534,
        -0.031
      ]
    }
  },
  "projects_keeping_target": {
    "b13": 9,
    "needed": 7,
    "product": 9
  },
  "tuned_blocks": {
    "commits": 7355,
    "miss_rate": 0.012236573759347382,
    "wilson_upper": 0.014531750893857708
  },
  "verdict": "inconclusive",
  "pooled_commits": {
    "b13": {
      "time": 0.637434209533392,
      "recall": 0.9699362283631947,
      "safety": 0.9337748344370861,
      "miss_rate": 0.011319330901773362
    },
    "product": {
      "time": 0.9385656521192303,
      "recall": 0.9896750683267537,
      "safety": 0.9764532744665195,
      "miss_rate": 0.004024650987297196
    }
  },
  "note": "exploratory: the B13 design used the confirmatory gate evidence"
}
```

## exploratory

Verdict: **inconclusive**

```json
{
  "projects": [],
  "verdict": "inconclusive",
  "note": "exploratory: the B13 design used the confirmatory gate evidence"
}
```
