# DANTE-H / B10 stopping experiment: fixed protocol

Frozen 2026-10-24, **before** any result was computed. Any later change gets a
new dated section below; this section is not edited.

## Question

Does the calibrated stopping rule (B10's "add tests until estimated skip risk
≤ 5%") improve the cost / failure-detection trade-off when it sits on a
second, stronger history-based ordering (a DANTE approximation), compared with
that ordering alone at the same real test time?

## DANTE-H: what is approximated

**DANTE-H is an approximation of DANTE, history component only.** It is not a
reproduction.

- Kept: HistoryScore = THFR + StickyScore, with Wilson 95% confidence weights
  over look-back windows W = {1, …, 10} (the paper's suggested range, not tuned
  here), Min–Max normalisation within the commit, FV = V · f / t.
- Dropped: the TF-IDF change/test relevance score (RelevanceScore = 0). So
  V = normalised HistoryScore only.
- "Build" = an earlier commit in the dataset at which the test ran. RTPTorrent
  rows are per test class, not per test method.
- f = failures of the test in its last 10 runs; t = historical mean duration
  (the same cost estimate every other policy uses). Ties: shorter first, then
  test id.
- All quantities come from commits strictly before the scored commit.

## Data and setup

- Projects: HikariCP, LittleProxy, jade4j, wicket-bootstrap. These are the only
  four whose `dataset.csv` is currently restored; the other seven are absent.
- Same chronological 60/20/20 split, gradient boosting, isotonic calibration
  fitted on validation, risk target 0.05, seeds 0–4 (as study11).
- Seeds only change model randomness. DANTE-H itself is deterministic.

## Policies

| Id | Order | Stop |
|---|---|---|
| D1 | DANTE-H | time budget (matched) |
| D2 | DANTE-H | calibrated skip risk ≤ 0.05, no budget |
| B3 | Rules (recent failures, shortest) | time budget (matched) |
| B10 | Rules | calibrated skip risk ≤ 0.05, no budget |

Changed test classes always run, as in every existing policy.

## Comparisons (paired, same test commits)

1. **Primary:** D2 − D1, with D1 at the budget giving the same mean real time as D2.
2. D2 − B10 (both unbudgeted).
3. B10 − B3 at the same time (replication of D-036 on these four projects).
4. D1 − B3 at the same time as D2 (is DANTE-H a stronger ordering here?).

## Metrics

Per project, mean over seeds, with the existing percentile bootstrap over test
commits (1,000 resamples, seed = run seed):

- mean real time ratio (savings = 1 − time),
- failing-test recall, commit safety rate,
- observed miss rate vs mean estimated skip risk; **risk-target failure** =
  observed miss rate > 0.05,
- analysis overhead: wall-clock seconds to compute DANTE-H scores for the whole
  dataset, and mean milliseconds per test commit to score and decide.

## Decision rule (fixed in advance)

- **Supported** ("calibrated stopping helps across these two orderings"):
  D2 − D1 safety estimate ≥ 0 on all four projects, the bootstrap interval
  excludes 0 on at least two, and D2 meets the 0.05 target on at least three.
- **Not supported:** the D2 − D1 safety interval is entirely below 0 on any
  project, or D2 fails the target on two or more projects.
- Otherwise **inconclusive**, reported as such.

jade4j has very few failing test commits, so its intervals may be undefined.
That counts as "interval does not exclude 0", not as a failure.

## Not allowed

No tuning of W, the risk target, or the model on these test results. No
dropping of projects or seeds after seeing results. All runs are reported.
