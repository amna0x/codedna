# CodeDNA — Research Plan

> No results exist yet. Everything below is a plan. Do not quote numbers
> until experiments have actually been run and recorded under
> `experiments/results/`.

## What is *not* novel

Changed-file detection, dependency graphs, affected-test selection, ML-based
test prioritisation and history-based ranking are all established (e.g.
Ekstazi, STARTS, Predictive RTS, industrial systems at Google/Facebook). CodeDNA
builds on them and must cite them.

## Candidate contribution

Can a **hybrid structural + historical** regression-test selector reduce
execution cost while giving **better-calibrated** estimates of the risk of
skipping tests? Can an **uncertainty-aware fallback** policy reduce missed
failures compared with ordinary ML selection?

## Research questions (hypotheses to test)

- **RQ1** — How accurately do structural, change and historical features
  predict regression-test failures?
- **RQ2** — How much test execution time can be saved at given empirical
  failure-detection targets?
- **RQ3** — Does probability calibration improve the reliability of test-risk
  estimates?
- **RQ4** — Does uncertainty-aware fallback improve the safety/cost trade-off?
- **RQ5 (optional)** — Do graph-derived features improve prediction or
  explainability enough to justify their cost?

## Baselines

| ID | Baseline |
|----|----------|
| B0 | Retest all |
| B1 | Random ordering |
| B2 | Shortest test first |
| B3 | Recent failures + short duration |
| B4 | Dependency-only selection |
| B5 | Historical-failure-only ranking |
| B6 | Change-only ML |
| B7 | Hybrid ML, uncalibrated |
| B8 | Hybrid ML, calibrated |
| B9 | Hybrid ML, calibrated + fallback |

Implemented so far: B0 and B4 (`codedna select`/`compare`, plus a
coverage-based variant), B1/B2/B3/B5 and two hybrid ML rankers without
calibration (B7: logistic regression, gradient boosting) in
`codedna history evaluate`. Not yet implemented: B6 (the same models
restricted to change features) and B8/B9 (Milestone 5).

## Metrics

- **Failure detection:** failing-test recall, missed failing tests,
  commit-level safety rate.
- **Efficiency:** selection ratio, test-time reduction, end-to-end CI time
  reduction, analysis + inference overhead.
- **Prioritisation:** APFD, APFDc, time to first failure.
- **Prediction:** precision, recall, PR-AUC.
- **Calibration:** Brier score, Expected Calibration Error, reliability
  diagrams, risk–coverage curves.
- **Graph correctness:** precision on manually checked samples, unresolved-edge
  rate, build time.

## Protocol

- **Chronological splits only**: oldest 60 % of commits train, next 20 %
  validation/calibration, latest 20 % test. No random shuffling.
- No information from future commits in features (e.g. failure counts are
  computed only from commits strictly before the one being predicted).
- Ground truth = full-suite outcomes where available.
- Fixed random seeds; record dataset versions, tool versions and commands.
- Report negative and null results honestly.

## Prior art to study (verify URL, licence, maintenance before reuse)

Predictive RTS, Ekstazi, Fine-Ekstazi, RTSTester, Defects4J, LRTS, RTPTorrent,
JaCoCo, Maven Surefire, JavaParser, Tree-sitter Java, Cytoscape.js. See
CODEDNA_STARTER.md §9.
