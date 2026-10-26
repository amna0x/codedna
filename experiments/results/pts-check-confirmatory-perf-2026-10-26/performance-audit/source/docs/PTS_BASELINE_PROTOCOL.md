# Predictive Test Selection baseline protocol — 2026-10-25

Status: fixed and committed before any result of this check was computed.
Changes after the first result need a new dated protocol and output folder;
this file is never edited to fit results.

## Question

The report argues that CodeDNA's per-commit risk estimate (B10) differs from
the aggregate recall targets of Predictive Test Selection (PTS; Machalica et
al., ICSE-SEIP 2019). This check measures that difference instead of arguing
it:

1. At the same actual test time, does B10's stopping rule keep more failing
   commits safe than PTS-style cutoffs?
2. Out of sample, does each method keep the target it states? PTS states an
   aggregate test recall of 0.95 and change recall of 0.999; B10 states a
   per-commit miss risk of at most 0.05.
3. Does CodeDNA's calibrated skip risk tell in advance which PTS selections
   will miss a failure?

Any of these may come out against CodeDNA; that is then the result.

## Data and design

Exactly the rolling-origin design of `docs/EVIDENCE_STUDY_PROTOCOL.md`: the
same datasets (SHA-256 recorded), the last 50 % of commits in 5 blocks, and
for each block the unchanged `selection.live.fit_audited` with
`plugins.java_live.LIVE_FEATURES` fitted on the commits before the block.
Its 50/25/25 split gives a training window, a calibration window and an
audit window. The block's own labels are never used for fitting or tuning.

Only the four previously inspected projects (HikariCP, jade4j, LittleProxy,
wicket-bootstrap) are available, so this check is **exploratory**. It gives no
confirmatory verdict. When the confirmatory datasets exist, the same script
is rerun on them into a new folder.

The study scripts frozen by the running confirmatory job are not edited; the
check is a separate script, `scripts/run_pts_check.py`, with the selection
rule in `codedna.selection.pts`.

## B11: PTS-style selection

Following section III of Machalica et al.:

- **Score:** the block model's *uncalibrated* failure probability (PTS does
  not calibrate).
- **Selected set:** changed test classes (as in every CodeDNA policy) ∪
  tests with score ≥ `score_cutoff` ∪ the `count_cutoff` highest-scoring
  tests. Ties at a cutoff are all selected.
- **Tuning, on the calibration window only** (the window B10 uses for its
  calibrator, so both methods see the same data):
  - `score_cutoff` is the largest score at which test recall (selected
    failing test rows / failing test rows), with `count_cutoff` = 0, is at
    least the test-recall target (0.95);
  - `count_cutoff` is the smallest N at which change recall (failing commits
    with at least one failing test selected / failing commits), with no score
    cutoff, is at least the change-recall target (0.999).
- If the calibration window has no failing rows, B11 cannot be tuned. The
  block is excluded from B11 comparisons and the count is reported.

PTS's weekly deployment check (selection rate under 0.3 at 0.9 recall) is
specific to Facebook's suite and is not applied: B11 has no gate and no
fallback, as in the paper.

## Analyses

- **Primary (question 1).** Per project, one test-recall target `t` in [0, 1]
  (change-recall target fixed at 0.999) is matched to B10's mean actual time
  over the compared blocks, using the existing `match_budget` bisection, as
  B3 is matched in the rolling-origin study. Report the residual time.
  B10 minus matched B11 in commit safety, pooled with equal project weight by
  the same hierarchical bootstrap (2000 draws, seed 0). The verdict uses the
  rolling-origin rules unchanged: *helps* if the interval's lower end is above
  0 and more than half the projects are positive; *harms* if its upper end is
  below 0; *no meaningful difference* if the interval lies inside ±0.05;
  otherwise *inconclusive*; fewer than 3 projects is *inconclusive*.
- **Question 2 (descriptive).** B11 at its paper targets (0.95, 0.999):
  pooled out-of-sample test recall, change recall, commit safety and time.
  B10: observed commit miss rate against 0.05. Per project and pooled.
- **Question 3 (descriptive).** For each test commit of B11 at its paper
  targets, the calibrated skip risk `1 − Π(1 − p)` of the tests B11 skipped,
  using the block's calibrator. Report the mean estimate against the observed
  share of commits where B11 missed a failure, and the AUC of the estimate for
  predicting a miss (undefined when a project has no misses or only misses).

## Outputs

`experiments/results/pts-check-2026-10-25/`: `config.json` (code and input
hashes), one JSON per project, `summary.json`, `summary.md`, `FINDINGS.md`
(written by hand from the saved numbers only).
