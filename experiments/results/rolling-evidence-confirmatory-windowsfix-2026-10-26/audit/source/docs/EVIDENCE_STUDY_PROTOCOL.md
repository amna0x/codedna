# Rolling-origin evidence study protocol — 2026-10-24

Status: fixed and committed before any result of this study was computed.
Changes after the first result require a new dated protocol and output folder;
this file is never edited to fit results.

## Question

Working claim under test: calibrated stopping (B10) improves the testing
trade-off over a same-order fixed budget (B3) at matched actual test time, and
the live evidence gate (D-041) identifies when the risk estimates cannot be
trusted. Both parts may fail; failure is reported as the result.

## Data and project sets

Source: RTPTorrent v1.1 (zenodo record 4046180), converted with the existing
pipeline (`scripts/fetch_rtptorrent_subset.py`, `scripts/run_study.py`
dataset extraction). Record each dataset's SHA-256 and the pipeline commit.

- **Confirmatory set:** RTPTorrent v1.1 projects not among the eleven projects
  of `study11-2026-10-21` (achilles, dynjs, graylog2-server, hikaricp, jade4j,
  jcabi-github, jooq, jsprit, littleproxy, optiq, wicket-bootstrap). Only these
  count towards the verdict.
- **Exploratory set:** the eleven study11 projects. Their later windows were
  already inspected, so their results are a replication check, never evidence
  for the verdict. HikariCP, LittleProxy, jade4j and wicket-bootstrap were also
  inspected in the DANTE extensions.

Eligibility (both sets), decided from labels only before fitting any model: at
least 20 failure-bearing commits in the evaluation region. Ineligible projects
are listed with their counts and excluded from pooled results.

## Rolling-origin design

Commits are in dataset (chronological) order. The evaluation region is the last
50% of commits, cut into 5 consecutive blocks of near-equal size. For block k,
the history is every commit before the block's first commit. On that history,
run the unchanged live fitting `selection.live.fit_audited` with
`plugins.java_live.LIVE_FEATURES` (50/25/25 train/calibrate/audit, balanced
gradient boosting, isotonic calibration, seed 0, recent-failure order, 5% risk
target, gate thresholds of D-041). The block's labels are never used for
fitting, calibration, the gate, or ordering of the block. Feature values in the
CSV are computed from prior commits only (existing extractor).

No parameter is tuned. If fitting fails (for example no failing training rows),
record the reason; the product policy for that block is the full suite and the
block is excluded from the B10/B3 comparison with the count reported.

## Policies per block

- **B10:** recent-failure order, stop at estimated 5% skip risk using the
  block's calibrated probabilities.
- **B3:** the same order with one fixed duration budget per project, matched to
  B10's mean actual time over that project's compared blocks with the existing
  `match_budget` bisection. Report the residual time difference.
- **Gated product:** B10 when the block's gate accepted, otherwise full suite.
- **Full suite:** reference (zero misses, time 1).

## Primary analysis

Metric: commit safety (share of failure-bearing commits with no missed failing
test), B10 minus matched B3. Secondary: failing-test recall difference and
time. Pool by equal project weight. 95% percentile interval from a hierarchical
bootstrap (projects as fixed units, commits resampled within project), 2000
draws, seed 0, via `run_study._hierarchical_draws`. Commit resampling ignores
serial dependence and there is no multiplicity correction; intervals are
indicative.

Verdict on the confirmatory set, fixed now (margin 0.05 in safety):

- **helps:** interval lower bound > 0 and point estimate > 0 in a majority of
  eligible projects;
- **harms:** interval upper bound < 0;
- **no meaningful difference:** interval inside [-0.05, 0.05];
- **inconclusive:** anything else, or fewer than 3 eligible projects.

## Gate analysis

For accepted and for rejected blocks separately, report blocks, commits,
observed commit miss rate of B10 (missed-failure commits / all commits) and its
one-sided 95% Wilson upper bound. Fixed reading:

- **gate supported:** pooled observed miss rate on accepted blocks <= 0.05, and
  it is not higher than the rejected-block rate;
- **gate not supported:** accepted-block observed miss rate > 0.05;
- **gate unexercised:** fewer than 3 accepted blocks in total. A gate that
  always falls back is safe but saves no time; report the time cost honestly.

Also report the gated product's mean time and observed miss rate per project.

## Reporting and reproducibility

Report every eligible project, block, fit failure and fallback. Record input,
code and protocol SHA-256, Python and package versions; refuse to resume when
they differ. Run with one worker (thread oversubscription made parallel runs
impractically slow). No end-to-end CI speedup claim: overhead excludes feature
extraction, compilation and CI startup. No universal claim beyond the projects
measured.
