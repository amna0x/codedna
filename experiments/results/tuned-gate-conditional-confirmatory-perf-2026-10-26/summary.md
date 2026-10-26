# Tuned-threshold gate (B13f) against the gated product

Rules fixed in docs/TUNED_GATE_CONDITIONAL_PROTOCOL.md before results. Exploratory.

| Project | Gate blocks | B13 blocks | Product time | Product miss | Product safety | B13f time | B13f miss | B13f safety | Thresholds |
|---|---|---|---|---|---|---|---|---|---|
| buck | 0 | 3 | 1.0000 | 0.0000 | 1.0000 | 0.7652 | 0.0047 | 0.9882 | full, full, 0.002, 0.01, 0.0002 |
| cloudify | 0 | 3 | 1.0000 | 0.0000 | 1.0000 | 0.8365 | 0.0033 | 0.9459 | 0.0005, 0.002, 0.0005, full, full |
| deeplearning4j | 1 | 3 | 0.8839 | 0.0069 | 0.9854 | 0.8083 | 0.0138 | 0.9707 | 0.05, 0.02, 0.005, full, full |
| dspace | 1 | 0 | 0.9763 | 0.0011 | 0.9831 | 1.0000 | 0.0000 | 1.0000 | full, full, full, full, full |
| jetty.project | 0 | 0 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | full, full, full, full, full |
| okhttp | 3 | 4 | 0.6910 | 0.0187 | 0.9118 | 0.7421 | 0.0027 | 0.9874 | 0.005, 0.005, 0.005, 0.01, full |
| sling | 2 | 3 | 0.9119 | 0.0085 | 0.9789 | 0.9571 | 0.0014 | 0.9965 | 0.002, 0.01, full, full, 0.0002 |
| sonarqube | 0 | 2 | 1.0000 | 0.0000 | 1.0000 | 0.9963 | 0.0000 | 1.0000 | full, full, 0.0005, 0.0001, full |
| titan | 1 | 0 | 0.9672 | 0.0052 | 0.9811 | 1.0000 | 0.0000 | 1.0000 | full, full, full, full, full |

## confirmatory

Verdict: **B13f saves time**

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
      "estimate": -0.0361,
      "ci": [
        -0.0414,
        -0.0308
      ]
    },
    "recall": {
      "estimate": 0.0053,
      "ci": [
        -0.0026,
        0.0153
      ]
    },
    "safety": {
      "estimate": 0.0054,
      "ci": [
        -0.0025,
        0.0142
      ]
    }
  },
  "projects_keeping_target": {
    "b13": 8,
    "needed": 7,
    "product": 8
  },
  "tuned_blocks": {
    "commits": 3941,
    "miss_rate": 0.005074854097944684,
    "wilson_upper": 0.007306264027031162,
    "failing_commits": 745,
    "failing_miss_rate": 0.026845637583892617,
    "failing_wilson_upper": 0.038430082001398747
  },
  "verdict": "B13f saves time",
  "pooled_commits": {
    "b13": {
      "time": 0.8854911583448624,
      "recall": 0.9939265107804434,
      "safety": 0.9852832965415746,
      "miss_rate": 0.002515406867060747
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
