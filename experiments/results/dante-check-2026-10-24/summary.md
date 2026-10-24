# DANTE-H / B10 exploratory extension

Independent history-only adaptation; NOT a reproduction of published DANTE.
Protocol fixed before these results; original/transfer outcomes were already inspected.

| Project | Policy | Time | Recall | Safety | Estimated risk | Observed miss |
|---|---|---|---|---|---|---|
| hikaricp | D1_50pct | 0.4614 | 0.8512 | 0.6000 | 0.0264 | 0.0280 |
| hikaricp | DANTE-H_raw | 0.0415 | 0.1322 | 0.2000 | 0.0087 | 0.0559 |
| hikaricp | rules_raw | 0.0373 | 0.1405 | 0.2000 | 0.0090 | 0.0559 |
| hikaricp | DANTE-H_calibrated | 0.2135 | 0.7769 | 0.5500 | 0.0410 | 0.0315 |
| hikaricp | rules_calibrated | 0.1333 | 0.7273 | 0.5000 | 0.0444 | 0.0350 |
| littleproxy | D1_50pct | 0.2834 | 0.8000 | 0.8000 | 0.5115 | 0.0189 |
| littleproxy | DANTE-H_raw | 0.7367 | 0.6000 | 0.6000 | 0.0138 | 0.0377 |
| littleproxy | rules_raw | 0.8184 | 0.8000 | 0.8000 | 0.0121 | 0.0189 |
| littleproxy | DANTE-H_calibrated | 0.9960 | 1.0000 | 1.0000 | 0.0009 | 0.0000 |
| littleproxy | rules_calibrated | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| jade4j | D1_50pct | 0.8850 | 1.0000 | 1.0000 | 0.0126 | 0.0000 |
| jade4j | DANTE-H_raw | 0.0867 | 0.5000 | 0.5000 | 0.0045 | 0.0159 |
| jade4j | rules_raw | 0.0968 | 0.5000 | 0.5000 | 0.0051 | 0.0159 |
| jade4j | DANTE-H_calibrated | 0.2338 | 0.5000 | 0.5000 | 0.0335 | 0.0159 |
| jade4j | rules_calibrated | 0.2264 | 0.5000 | 0.5000 | 0.0330 | 0.0159 |
| wicket-bootstrap | D1_50pct | 0.4903 | 0.8537 | 0.0575 | 0.6191 | 0.5000 |
| wicket-bootstrap | DANTE-H_raw | 0.4996 | 0.9479 | 0.8230 | 0.0198 | 0.0939 |
| wicket-bootstrap | rules_raw | 0.5161 | 0.9482 | 0.8230 | 0.0188 | 0.0939 |
| wicket-bootstrap | DANTE-H_calibrated | 0.7356 | 0.9973 | 0.9908 | 0.0182 | 0.0049 |
| wicket-bootstrap | rules_calibrated | 0.7513 | 0.9971 | 0.9862 | 0.0149 | 0.0073 |

## Stopping minus same-order budget baseline at matched actual time

Hierarchical bootstrap: seeds within equally weighted projects, then commits; 2000 draws.
Intervals are exploratory, assume independent commits and have no multiplicity correction.

- DANTE-H_raw: {"time": {"estimate": 0.0001, "ci": [-0.0321, 0.0325]}, "recall": {"estimate": -0.1174, "ci": [-0.2713, 0.0006]}, "safety": {"estimate": 0.0414, "ci": [-0.103, 0.1759]}}
- rules_raw: {"time": {"estimate": -0.0005, "ci": [-0.0289, 0.0259]}, "recall": {"estimate": -0.0309, "ci": [-0.1648, 0.0609]}, "safety": {"estimate": 0.1289, "ci": [0.009, 0.2346]}}
- DANTE-H_calibrated: {"time": {"estimate": -0.0013, "ci": [-0.0253, 0.0223]}, "recall": {"estimate": 0.0138, "ci": [-0.0305, 0.0547]}, "safety": {"estimate": 0.1652, "ci": [-0.0136, 0.3556]}}
- rules_calibrated: {"time": {"estimate": 0.0016, "ci": [-0.0229, 0.0263]}, "recall": {"estimate": 0.0045, "ci": [-0.0242, 0.0347]}, "safety": {"estimate": 0.0975, "ci": [-0.0197, 0.2914]}}

## Limits

- DANTE-inspired adaptation, not published DANTE reproduction
- Exploratory reuse of inspected historical windows; no universal ordering claim
- Few failing commits, four projects, serial dependence ignored by bootstrap
- No end-to-end CI speedup claim; overhead excludes feature extraction and build startup
