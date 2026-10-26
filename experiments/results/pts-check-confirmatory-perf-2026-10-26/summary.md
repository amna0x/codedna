# B10 against a Predictive Test Selection baseline (B11)

Rules fixed in docs/PTS_BASELINE_PROTOCOL.md before results.

| Project | B10 time | B10 safety | B11 matched safety | B11 paper time | B11 paper test recall | B11 paper safety | B10 miss rate | B11 miss rate | B11 est. skip risk | Risk AUC |
|---|---|---|---|---|---|---|---|---|---|---|
| buck | 0.0734 | 0.8757 | 0.9112 | 0.6648 | 0.9442 | 0.9408 | 0.0498 | 0.0237 | 0.0005 | 0.5198 |
| cloudify | 0.0475 | 0.4662 | 0.9459 | 0.8669 | 0.9684 | 0.9662 | 0.0321 | 0.0020 | 0.0066 | 0.4996 |
| deeplearning4j | 0.5188 | 0.9171 | 0.8878 | 0.7494 | 0.9519 | 0.9317 | 0.0390 | 0.0321 | 0.0883 | 0.7309 |
| dspace | 0.4736 | 0.0938 | 0.5938 | 0.8714 | 0.9645 | 0.5938 | 0.0385 | 0.0172 | 0.0891 | 0.2915 |
| jetty.project | 0.5942 | 0.9186 | 0.9535 | 0.9865 | 0.9934 | 0.9884 | 0.0729 | 0.0104 | 0.0053 | 0.8947 |
| okhttp | 0.4001 | 0.8487 | 0.9328 | 0.7869 | 0.9358 | 0.9328 | 0.0320 | 0.0142 | 0.0107 | 0.4372 |
| sling | 0.5992 | 0.8947 | 0.9649 | 0.6182 | 0.9714 | 0.9684 | 0.0427 | 0.0128 | 0.0266 | 0.5919 |
| sonarqube | 0.2110 | 0.5862 | 0.9569 | 0.9765 | 0.9658 | 0.9655 | 0.0304 | 0.0025 | 0.0019 | 0.4539 |
| titan | 0.7712 | 0.9623 | 0.8679 | 0.9785 | 0.9239 | 0.8868 | 0.0105 | 0.0314 | 0.0261 | 0.8090 |

## confirmatory

Verdict: **harms**

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
  "b10_minus_b11_matched": {
    "time": {
      "estimate": -0.311,
      "ci": [
        -0.3251,
        -0.2973
      ]
    },
    "recall": {
      "estimate": -0.204,
      "ci": [
        -0.2269,
        -0.1831
      ]
    },
    "safety": {
      "estimate": -0.1613,
      "ci": [
        -0.1903,
        -0.1312
      ]
    }
  },
  "safety_positive_projects": 2,
  "verdict": "harms",
  "pooled_commits": {
    "b11_paper": {
      "time": 0.8421765137851069,
      "recall": 0.9594202898550724,
      "safety": 0.9414414414414415
    },
    "b10": {
      "time": 0.27553303272352486,
      "recall": 0.5768115942028986,
      "safety": 0.7980480480480481
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
