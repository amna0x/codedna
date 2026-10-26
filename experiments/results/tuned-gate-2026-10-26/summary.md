# Tuned-threshold gate (B13) against the gated product

Rules fixed in docs/TUNED_GATE_PROTOCOL.md before results. Exploratory.

| Project | Gate blocks | B13 blocks | Product time | Product miss | Product safety | B13 time | B13 miss | B13 safety | Thresholds |
|---|---|---|---|---|---|---|---|---|---|
| hikaricp | 0 | 5 | 1.0000 | 0.0000 | 1.0000 | 0.7130 | 0.0098 | 0.9136 | 0.02, 0.02, 0.02, 0.02, 0.02 |
| jade4j | 1 | 1 | 0.9838 | 0.0000 | 1.0000 | 0.9179 | 0.0000 | 1.0000 | full, full, 0.1, full, full |
| littleproxy | 1 | 1 | 0.9976 | 0.0000 | 1.0000 | 0.9971 | 0.0000 | 1.0000 | full, full, full, 0.1, full |
| wicket-bootstrap | 5 | 5 | 0.9414 | 0.0049 | 0.9919 | 0.7737 | 0.0146 | 0.9758 | 0.05, 0.3, 0.5, 0.5, 0.2 |

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

Verdict: **B13 saves time**

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
      "estimate": -0.1303,
      "ci": [
        -0.1388,
        -0.1221
      ]
    },
    "recall": {
      "estimate": -0.0084,
      "ci": [
        -0.0147,
        -0.0033
      ]
    },
    "safety": {
      "estimate": -0.0256,
      "ci": [
        -0.0424,
        -0.0106
      ]
    }
  },
  "projects_keeping_target": {
    "b13": 4,
    "needed": 3,
    "product": 4
  },
  "tuned_blocks": {
    "commits": 1181,
    "miss_rate": 0.01100762066045724,
    "wilson_upper": 0.017237222698405906
  },
  "verdict": "B13 saves time",
  "pooled_commits": {
    "b13": {
      "time": 0.7797849150141642,
      "recall": 0.9979521310636119,
      "safety": 0.9670886075949368,
      "miss_rate": 0.009206798866855524
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
