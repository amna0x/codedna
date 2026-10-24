# Cross-project transfer study

Source train and calibration exclude the target project. The target's latest
20% of commits are tested; past target history remains available as features.
Cross-project source history is restricted to a chronological prefix strictly
older than the target test window's earliest Git committer date. This is a
conservative timestamp check, not proof that CI jobs had completed by then.

Projects and seeds were fixed before results were inspected. All directions
and within-project controls are reported; the best source is not selected on
target test results. No target recalibration or target-specific tuning is done.

## Target test windows

The skip-all rate is the share of commits with any failure. When this is
below 5%, even running no tests meets the observed unconditional miss
target. Target attainment alone therefore does not prove useful transfer;
recall, safety and the matched-cost comparison remain necessary.

| Target | Test commits | With failures | Skip-all miss rate |
|---|---|---|---|
| hikaricp | 286 | 20 | 0.0699 |
| littleproxy | 53 | 5 | 0.0943 |
| jade4j | 63 | 2 | 0.0317 |
| wicket-bootstrap | 164 | 87 | 0.5305 |

## Calibrated B10: source-trained probabilities, rules order, 5% risk target

Means over seeds. n/a denotes an unavailable model/calibrator or metric.

| Source | Target | Seeds | Time | Recall | Safety | Estimated risk | Observed miss | Target held | ECE | PR-AUC |
|---|---|---|---|---|---|---|---|---|---|---|
| hikaricp (within control) | hikaricp | 5/5 | 0.1333 | 0.7273 | 0.5000 | 0.0444 | 0.0350 | yes | 0.0137 | 0.0322 |
| hikaricp | littleproxy | 5/5 | 0.2926 | 0.0000 | 0.0000 | 0.0440 | 0.0943 | no | 0.0065 | 0.0022 |
| hikaricp | jade4j | 5/5 | 0.0727 | 0.5000 | 0.5000 | 0.0468 | 0.0159 | yes | 0.0017 | 0.0016 |
| hikaricp | wicket-bootstrap | 5/5 | 0.7251 | 0.9996 | 0.9885 | 0.0389 | 0.0061 | yes | 0.2905 | 0.3056 |
| littleproxy | hikaricp | 5/5 | 0.7879 | 0.6446 | 0.6500 | 0.0146 | 0.0245 | yes | 0.0178 | 0.0225 |
| littleproxy (within control) | littleproxy | 5/5 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | yes | 0.0382 | 0.0034 |
| littleproxy | jade4j | 5/5 | 0.9722 | 1.0000 | 1.0000 | 0.0003 | 0.0000 | yes | 0.0668 | 0.0016 |
| littleproxy | wicket-bootstrap | 5/5 | 0.7082 | 0.9830 | 0.6897 | 0.0348 | 0.1646 | no | 0.2727 | 0.5732 |
| jade4j | hikaricp | 0/5 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| jade4j | littleproxy | 0/5 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| jade4j (within control) | jade4j | 5/5 | 0.2264 | 0.5000 | 0.5000 | 0.0330 | 0.0159 | yes | 0.0026 | 0.0069 |
| jade4j | wicket-bootstrap | 0/5 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| wicket-bootstrap | hikaricp | 5/5 | 0.9784 | 0.9917 | 0.9600 | 0.0002 | 0.0028 | yes | 0.3270 | 0.0287 |
| wicket-bootstrap | littleproxy | 5/5 | 0.9944 | 1.0000 | 1.0000 | 0.0004 | 0.0000 | yes | 0.3740 | 0.0180 |
| wicket-bootstrap | jade4j | 5/5 | 0.9996 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | yes | 0.2543 | 0.0053 |
| wicket-bootstrap (within control) | wicket-bootstrap | 5/5 | 0.7513 | 0.9971 | 0.9862 | 0.0149 | 0.0073 | yes | 0.0990 | 0.5500 |

## Calibrated B10 versus rules at matched actual test time

Pairwise 95% hierarchical bootstrap intervals: resample a seed, then target
commits. Intervals crossing zero do not establish a gain. Matching is approximate.

| Source → target | Time difference | Safety difference [95% CI] |
|---|---|---|
| hikaricp → hikaricp | 0.0019 | 0.0500 [-0.1250, 0.2222] |
| hikaricp → littleproxy | 0.0004 | -0.2000 [-0.6667, 0.0000] |
| hikaricp → jade4j | 0.0010 | 0.0000 [0.0000, 0.0000] |
| hikaricp → wicket-bootstrap | 0.0000 | 0.1034 [0.0449, 0.1711] |
| littleproxy → hikaricp | 0.0315 | -0.1500 [-0.3684, 0.0556] |
| littleproxy → littleproxy | 0.0000 | 0.0000 [0.0000, 0.0000] |
| littleproxy → jade4j | -0.0278 | 0.0000 [0.0000, 0.0000] |
| littleproxy → wicket-bootstrap | 0.0002 | 0.3218 [0.1852, 0.4598] |
| jade4j → jade4j | 0.0000 | 0.0000 [0.0000, 0.0000] |
| wicket-bootstrap → hikaricp | -0.0216 | -0.0400 [-0.2000, 0.0000] |
| wicket-bootstrap → littleproxy | -0.0056 | 0.0000 [0.0000, 0.0000] |
| wicket-bootstrap → jade4j | -0.0004 | 0.0000 [0.0000, 0.0000] |
| wicket-bootstrap → wicket-bootstrap | 0.0046 | 0.3402 [-0.0241, 0.9545] |

## Ordering quality (raw model probability order)

| Source | Target | ML APFDc | Rules APFDc |
|---|---|---|---|
| hikaricp | hikaricp | 0.5342 | 0.7528 |
| hikaricp | littleproxy | 0.3823 | 0.5337 |
| hikaricp | jade4j | 0.4940 | 0.5198 |
| hikaricp | wicket-bootstrap | 0.2375 | 0.8242 |
| littleproxy | hikaricp | 0.5219 | 0.7528 |
| littleproxy | littleproxy | 0.4584 | 0.5337 |
| littleproxy | jade4j | 0.4824 | 0.5198 |
| littleproxy | wicket-bootstrap | 0.6196 | 0.8242 |
| jade4j | hikaricp | 0.6524 | 0.7528 |
| jade4j | littleproxy | 0.6946 | 0.5337 |
| jade4j | jade4j | 0.6469 | 0.5198 |
| jade4j | wicket-bootstrap | 0.6120 | 0.8242 |
| wicket-bootstrap | hikaricp | 0.5039 | 0.7528 |
| wicket-bootstrap | littleproxy | 0.7189 | 0.5337 |
| wicket-bootstrap | jade4j | 0.6094 | 0.5198 |
| wicket-bootstrap | wicket-bootstrap | 0.7321 | 0.8242 |

## Limits

- Four pre-selected projects only; no universal transfer claim
- Git committer dates proxy time; CI completion dates are unavailable
- Prior target-project history is available; this is not cold-start prediction
- Fixed chronological target split; seeds vary models, not time periods
- Bootstrap treats target commits as independent; serial correlation is ignored
- Source-target directions share projects and are statistically dependent

## Warnings

- jade4j -> hikaricp: Source calibration unavailable: calibration data needs both failing and passing examples
- jade4j -> littleproxy: Source calibration unavailable: calibration data needs both failing and passing examples
- jade4j -> wicket-bootstrap: Source calibration unavailable: calibration data needs both failing and passing examples
