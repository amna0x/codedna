# Rolling-origin evidence study

Rules fixed in docs/EVIDENCE_STUDY_PROTOCOL.md before results.

| Project | Set | Failing commits | Accepted blocks | Fit failures | B10 time | B10 safety | B3 safety | Product time | Product miss |
|---|---|---|---|---|---|---|---|---|---|
| buck | confirmatory | 169 | 0 | 0 | 0.0734 | 0.8757 | 0.9349 | 1.0000 | 0.0000 |
| cloudify | confirmatory | 148 | 0 | 0 | 0.0475 | 0.4662 | 0.5743 | 1.0000 | 0.0000 |
| deeplearning4j | confirmatory | 205 | 1 | 0 | 0.5188 | 0.9171 | 0.8293 | 0.8839 | 0.0069 |
| dspace | confirmatory | 59 | 1 | 1 | 0.4736 | 0.0938 | 0.1875 | 0.9763 | 0.0011 |
| jetty.project | confirmatory | 86 | 0 | 0 | 0.5942 | 0.9186 | 0.9302 | 1.0000 | 0.0000 |
| okhttp | confirmatory | 238 | 3 | 0 | 0.4001 | 0.8487 | 0.8739 | 0.6910 | 0.0187 |
| sling | confirmatory | 285 | 2 | 0 | 0.5992 | 0.8947 | 0.8877 | 0.9119 | 0.0085 |
| sonarqube | confirmatory | 116 | 0 | 0 | 0.2110 | 0.5862 | 0.4483 | 1.0000 | 0.0000 |
| titan | confirmatory | 53 | 1 | 0 | 0.7712 | 0.9623 | 0.9623 | 0.9672 | 0.0052 |

## confirmatory

Verdict: **no meaningful difference**; gate: **gate supported**

```json
{
  "eligible_projects": [
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
  "b10_minus_b3": {
    "time": {
      "estimate": 0.0,
      "ci": [
        -0.0099,
        0.0101
      ]
    },
    "recall": {
      "estimate": -0.0922,
      "ci": [
        -0.113,
        -0.0728
      ]
    },
    "safety": {
      "estimate": -0.0072,
      "ci": [
        -0.0339,
        0.0179
      ]
    }
  },
  "safety_positive_projects": 3,
  "gate": {
    "accepted": {
      "blocks": 8,
      "commits": 1270,
      "observed_miss_rate": 0.025196850393700787,
      "wilson_upper": 0.033502299411224
    },
    "rejected": {
      "blocks": 36,
      "commits": 6492,
      "observed_miss_rate": 0.03650646950092421,
      "wilson_upper": 0.04053228364168052
    },
    "verdict": "gate supported"
  }
}
```

## exploratory

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
  },
  "note": "previously inspected projects; replication only, not verdict evidence"
}
```
