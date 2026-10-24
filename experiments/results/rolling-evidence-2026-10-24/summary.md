# Rolling-origin evidence study

Rules fixed in docs/EVIDENCE_STUDY_PROTOCOL.md before results.

| Project | Set | Failing commits | Accepted blocks | Fit failures | B10 time | B10 safety | B3 safety | Product time | Product miss |
|---|---|---|---|---|---|---|---|---|---|
| hikaricp | exploratory | 81 | 0 | 0 | 0.3392 | 0.8272 | 0.7531 | 1.0000 | 0.0000 |
| jade4j | exploratory | 28 | 1 | 1 | 0.9147 | 1.0000 | 1.0000 | 0.9838 | 0.0000 |
| littleproxy | exploratory | 38 | 1 | 0 | 0.9128 | 0.7105 | 0.7895 | 0.9976 | 0.0000 |
| wicket-bootstrap | exploratory | 248 | 5 | 0 | 0.9414 | 0.9919 | 1.0000 | 0.9414 | 0.0049 |

## confirmatory

Verdict: **inconclusive**; gate: **gate unexercised**

```json
{
  "eligible_projects": [],
  "gate": {
    "accepted": {
      "blocks": 0,
      "commits": 0,
      "observed_miss_rate": null,
      "wilson_upper": null
    },
    "rejected": {
      "blocks": 0,
      "commits": 0,
      "observed_miss_rate": null,
      "wilson_upper": null
    },
    "verdict": "gate unexercised"
  }
}
```

## exploratory

Verdict: **no meaningful difference**; gate: **gate supported**

```json
{
  "eligible_projects": [
    "hikaricp",
    "jade4j",
    "littleproxy",
    "wicket-bootstrap"
  ],
  "b10_minus_b3": {
    "time": {
      "estimate": -0.0147,
      "ci": [
        -0.0265,
        -0.0035
      ]
    },
    "recall": {
      "estimate": 0.0082,
      "ci": [
        -0.0054,
        0.0196
      ]
    },
    "safety": {
      "estimate": -0.0032,
      "ci": [
        -0.0362,
        0.0294
      ]
    }
  },
  "safety_positive_projects": 1,
  "gate": {
    "accepted": {
      "blocks": 7,
      "commits": 467,
      "observed_miss_rate": 0.004282655246252677,
      "wilson_upper": 0.01285781615090635
    },
    "rejected": {
      "blocks": 12,
      "commits": 914,
      "observed_miss_rate": 0.02735229759299781,
      "wilson_upper": 0.03771747566862529
    },
    "verdict": "gate supported"
  },
  "note": "previously inspected projects; replication only, not verdict evidence"
}
```
