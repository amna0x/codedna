# Tuned-threshold gate (B13f) against the gated product

Rules fixed in docs/TUNED_GATE_CONDITIONAL_PROTOCOL.md before results. Exploratory.

| Project | Gate blocks | B13 blocks | Product time | Product miss | Product safety | B13f time | B13f miss | B13f safety | Thresholds |
|---|---|---|---|---|---|---|---|---|---|
| hikaricp | 0 | 0 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | full, full, full, full, full |
| jade4j | 1 | 0 | 0.9838 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | full, full, full, full, full |
| littleproxy | 1 | 0 | 0.9976 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | full, full, full, full, full |
| wicket-bootstrap | 5 | 4 | 0.9414 | 0.0049 | 0.9919 | 0.7957 | 0.0098 | 0.9839 | full, 0.3, 0.5, 0.5, 0.02 |

## confirmatory

Verdict: **inconclusive**

```json
{
  "projects": [],
  "verdict": "inconclusive",
  "note": "exploratory: the B13 design used the confirmatory gate evidence"
}
```

## exploratory

Verdict: **B13f saves time**

```json
{
  "projects": [
    "hikaricp",
    "jade4j",
    "littleproxy",
    "wicket-bootstrap"
  ],
  "b13_minus_product": {
    "time": {
      "estimate": -0.0318,
      "ci": [
        -0.0371,
        -0.0266
      ]
    },
    "recall": {
      "estimate": -0.0002,
      "ci": [
        -0.0006,
        0.0001
      ]
    },
    "safety": {
      "estimate": -0.002,
      "ci": [
        -0.007,
        0.0029
      ]
    }
  },
  "projects_keeping_target": {
    "b13": 4,
    "needed": 3,
    "product": 4
  },
  "tuned_blocks": {
    "commits": 328,
    "miss_rate": 0.012195121951219513,
    "wilson_upper": 0.026885425996917126,
    "failing_commits": 205,
    "failing_miss_rate": 0.01951219512195122,
    "failing_wilson_upper": 0.04275259999752353
  },
  "verdict": "B13f saves time",
  "pooled_commits": {
    "b13": {
      "time": 0.9406722379603399,
      "recall": 0.9991040573403303,
      "safety": 0.9898734177215189,
      "miss_rate": 0.0028328611898017
    },
    "product": {
      "time": 0.980972521246459,
      "recall": 0.9997440163829515,
      "safety": 0.9949367088607595,
      "miss_rate": 0.00141643059490085
    }
  },
  "note": "exploratory: the B13 design used the confirmatory gate evidence"
}
```
