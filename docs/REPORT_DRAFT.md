# CodeDNA: evaluation chapter (draft)

Draft of the methods, results and threats-to-validity chapters for the FYP
report (the other chapters are in [REPORT_SYSTEM_DRAFT.md](REPORT_SYSTEM_DRAFT.md)), covering research questions RQ1 to RQ5 (docs/RESEARCH_PLAN.md).
Every number comes from files under `experiments/results/`; the source of
each table is named. Status: evaluation draft with reproducible figures, 2026-10-24.

## 1. Research questions

- **RQ1.** How accurately do structural, change and historical features
  predict regression-test failures?
- **RQ2.** How much test execution time can be saved at given empirical
  failure-detection targets?
- **RQ3.** Does probability calibration improve the reliability of
  test-risk estimates?
- **RQ4.** Does uncertainty-aware fallback improve the safety/cost
  trade-off?
- **RQ5.** Do graph-derived features improve prediction enough to justify
  their cost?

## 2. Method

### 2.1 Data

We use RTPTorrent v1.1 (Mattis, Rein, Dürsch and Hirschfeld, MSR 2020;
Zenodo record 4046180, CC BY 4.0; archive md5
`1f7fa822b0cf155bd007a94d1a24a336`). It holds Travis CI test results at
test-class level for 20 open-source Java projects (2007 to 2016), the links
from CI jobs to Git commits, and the projects' Git repositories. Using
recorded CI outcomes means no third-party code is built or executed.

`codedna history import-rtptorrent` imports one project at a time. A CI job
can cover several commits; the tested commit is the single tip of the job's
commits, and its change is measured against the state before the push. A
test class can appear several times in one job (one run per module); those
runs are merged, and the class counts as failed if any run failed. A commit
counts as failing if any of its jobs records a failure (D-021). Eleven
projects were imported; their job counts match Table 2 of the RTPTorrent
paper (docs/DATASET_PLAN.md).

### 2.2 Features

Each (commit, test class) pair in the original structural study becomes a
row with 19 features (D-023). Change/structural features describe the current
code change; historical outcome features use stored earlier results, not the
current result. This is retrospective full-history availability, not yet a
policy-specific partial-feedback history:

| Group | Features |
|---|---|
| Change (6) | files, Java files, non-Java files and test files changed; lines added and deleted |
| Test (1) | whether the test class itself changed |
| Structural (3) | whether the dependency graph reaches the test from the change, the distance, and whether the path is confirmed |
| History (9) | past runs, past failures, failure rate, failures in the last 5 runs, failed last run, commits since last failure, mean and last duration, co-failures |

The structural features come from CodeDNA's dependency graph: Java files are
parsed with tree-sitter, class-level edges (extends, implements, uses,
imports, static access) are labelled confirmed or heuristic, and impact is a
reverse breadth-first search over the merged before/after graphs.

### 2.3 Split, models and seeds

Commits are split chronologically: oldest 60 % train, next 20 %
validation, latest 20 % test. Nothing is shuffled. Two classifiers are
trained on the training split with scikit-learn: logistic regression and
histogram gradient boosting, both with balanced class weights (the rare
failing rows are up-weighted). Selection experiments use gradient boosting.
A separate check trains the same model without class weights, as a stricter
uncalibrated baseline for RQ3 (D-037). Calibrators (Platt scaling and isotonic
regression) are fitted on the validation split only. Every experiment is run
with five seeds (0 to 4); seeds change model randomness only, not the split.

### 2.4 Orderings and selection policies

Orderings (RQ1): random (B1), shortest first (B2), recent failures then
shortest (B3), failure history (B5), logistic regression and gradient
boosting.

Selection policies (RQ2, RQ4), each applied to every test commit:

| Policy | Rule |
|---|---|
| B0 | run every test |
| B4 | dependency only: tests the graph reaches from the change, plus changed tests |
| B6 | change-only model, 50 % time budget |
| B7 | full model, uncalibrated, 50 % budget |
| B8 | full model, calibrated, 50 % budget |
| B9 | B8 plus risk target 0.05 with fallback, plus the unfamiliar-change rule |
| B9r | B8 plus risk-target fallback only |
| B9n | B8 plus unfamiliar-change rule only (non-Java files changed, or most tests without history, means run everything) |
| B3 | rules order (recent failures, then shortest), 50 % budget |
| B10 | hybrid: rules order, no budget; add tests until the calibrated estimated skip risk is at most 0.05 |

Model-based policies take tests in order of probability per second of
expected run time. The estimated skip risk of a selection is
1 − Π(1 − p) over the skipped tests, which assumes independent failures.

### 2.5 Metrics

- Ordering: APFD and APFDc (cost-aware), failing-test recall at 25 % and
  50 % of test time.
- Prediction: PR-AUC.
- Calibration: Brier score and expected calibration error (ECE, 10
  equal-width bins); per commit, the mean absolute gap between estimated
  skip risk and observed miss rate.
- Selection: test-time ratio (selected test time / full run time),
  failing-test recall, and commit safety (share of failing commits where
  every failing test was selected).

The primary safety endpoint is **failure-conditional zero-omission safety**.
For failing test-class set F and selected class set S at a commit:

| Measure | Definition | Interpretation |
|---|---|---|
| Zero-omission safety (primary) | failing commits with F contained in S / failing commits | Every recorded failing class was selected |
| Build escape (secondary) | failing commits with no element of F in S / failing commits | No selected class detects the recorded failure |
| Missed-test fraction (secondary) | total omitted failing classes / total failing classes | Complement of micro-averaged failing-test recall on the same cohort |

Safety and build escape are undefined when the cohort has no failing commits;
such projects cannot supply evidence of failure-conditional safety. The test
unit in these Java datasets is a class, not an individual JUnit method.
Selecting nine of ten failing classes avoids a build escape but fails the
zero-omission criterion. Build escape must not be inferred from zero-omission
safety alone; historical tables that do not contain it do not claim to measure it.

The B10 gate's original audit criterion uses misses over all audit commits;
failure-conditional CRC uses failing audit commits. Neither denominator should
be silently substituted for the primary endpoint. Statistical bounds apply
under their stated assumptions, not as certainty about the next change.

### 2.6 Fair comparison and uncertainty

A policy that runs more tests usually catches more failures. To separate
better decisions from more testing, each policy of interest is compared
with a baseline whose budget is tuned by bisection so that it spends the
same real test time (D-035): B9, B9r, B9n and B10 against B8, and B10 also
against B3.

Point estimates are means over the five seeds. 95 % intervals come from a
hierarchical percentile bootstrap: pick a seed, then resample that seed's
test commits (paired between policy and baseline). Pooled results average
the projects with equal weight, resampling within each project, and report
how many projects contribute (a project without failing test commits has no
recall or safety).

### 2.7 Figure provenance

The five figures are generated from saved reports by
`scripts/make_study_figures.py` (D-038), without retraining or rebuilding the
feature datasets. Their exact values and project cohorts are in
`experiments/results/study11-2026-10-21/figures/figure-data.json`; the adjacent
`manifest.json` fingerprints the input reports, exporter and artifacts.
Raw/calibrated comparisons use common project cohorts. No confidence intervals
are derived from standard deviations over random seeds.

### 2.8 Operational cost and claim boundary

Historical test-time ratios charge the recorded selected-class durations.
They are not end-to-end CI speedup or complete deployment costs. Full-suite
audit collection, mandatory structural/policy tests, repeated executions,
feature extraction and model/selector overhead must be included or separately
reported in any new operational comparison. Unmeasured costs are unknown,
not zero. Post-hoc equal-time matching describes the recorded benchmark;
it is not a deployable controller with knowledge of future runtimes.

The current contribution is an implemented, inspectable system and its
retrospective tradeoffs. A stronger claim about closed-loop partial-feedback
performance requires a separate policy-specific evaluation. A bounded study
is recommended if input feasibility is established; it is not claimed already
completed, and the bounded retrospective FYP does not depend on inventing one.

## 3. Data actually available

Source: `experiments/results/study11-2026-10-21/summary.md`.

| Project | Test commits | With failures | Failing rows |
|---|---|---|---|
| graylog2-server | 879 | 0 | 0.0 % |
| jOOQ | 258 | 0 | 0.0 % |
| jcabi-github | 118 | 52 | 0.7 % |
| optiq | 91 | 4 | 0.14 % |
| Achilles | 101 | 1 | 0.01 % |
| HikariCP | 286 | 20 | 2.0 % |
| LittleProxy | 53 | 5 | 0.26 % |
| jade4j | 63 | 2 | 0.12 % |
| jsprit | 52 | 7 | 0.52 % |
| wicket-bootstrap | 164 | 87 | 30.4 % |
| dynjs | 75 | 1 | 0.02 % |

graylog2-server and jOOQ have no failing test commits: their CI logs record
far fewer test classes in the test period (about 1 and 7 per commit), which
we attribute to changes in the projects' CI rather than to the importer
(stored and derived failure counts agree). They contribute to time and
calibration results but not to recall or safety, so those pooled results
use n = 9 projects. Several of the nine have fewer than ten failing test
commits, so per-project results for them are close to anecdotes.

## 4. Results

### 4.1 RQ1: predicting failures

Gradient boosting with all 19 features reaches a pooled PR-AUC of 0.138
(n = 9), far above the failure base rate on most projects (for example
jcabi-github 0.163 against 0.007, optiq 0.357 against 0.0014, HikariCP 0.039
against 0.020, wicket-bootstrap 0.635 against 0.304). The features carry
real signal.

Ablations (pooled PR-AUC; `summary.md`, "Ablations"): all features 0.138,
without history 0.080, without change 0.098, without structural 0.119.
History features matter most. On projects with very few failures the
ablations are unstable (on jade4j the model *without* history scores
0.251 against 0.016 with all features), a sign of overfitting to a handful
of failing rows.

Turning predictions into an *ordering* is a different matter (source:
`summary.md`, "Ordering", n = 9):

| Ordering | APFD | APFDc | Recall at 25 % time | Recall at 50 % time |
|---|---|---|---|---|
| Recent failures, then shortest (B3) | 0.511 | **0.759** | 0.578 | 0.714 |
| Shortest first (B2) | 0.427 | 0.739 | 0.572 | 0.702 |
| Random (B1) | 0.627 | 0.652 | 0.505 | 0.635 |
| Logistic regression | **0.644** | 0.637 | 0.428 | 0.619 |
| Gradient boosting | 0.612 | 0.576 | 0.378 | 0.527 |
| Failure history (B5) | 0.588 | 0.484 | 0.263 | 0.418 |

Logistic regression has the best APFD, which ignores test duration. Once
duration counts (APFDc, recall at a time budget), the time-aware rules win
and both learned models are at or below random. The best ordering by APFDc
is a simple rule on six of the nine projects.

![Figure 1. APFDc of the saved orderings; n is the number of projects with a defined metric.](../experiments/results/study11-2026-10-21/figures/rq1-ordering.png)

Figure 1. APFDc of the saved orderings; n is the number of projects with a defined metric.

**Answer to RQ1.** The features predict failures well above chance, mainly
through test history. The learned models do not order tests better than
simple time-aware rules on this data.

### 4.2 RQ2: time saved at a detection target

Pooled budget sweep of the calibrated selector B8 (mean over projects of the
mean over seeds; `experiment-seed*.json`, `risk_coverage`):

| Budget | Time | Recall | Safety |
|---|---|---|---|
| 0.3 | 0.36 | 0.78 | 0.63 |
| 0.5 | 0.50 | 0.84 | 0.68 |
| 0.6 | 0.60 | 0.90 | 0.73 |
| 0.8 | 0.75 | 0.93 | 0.83 |
| 0.9 | 0.82 | 0.98 | 0.91 |

To catch 90 % of failing tests the selector needs about 60 % of the full
test time (a 40 % saving); to run every failing test on 90 % of failing
commits it needs about 82 % (an 18 % saving). The hybrid B10 (section 4.4)
reaches recall 0.94 and safety 0.88 at 61 % of the time with a 1 % risk
target, but that pooled comparison is not cost-matched per project and is
driven by wicket-bootstrap.

![Figure 2. B8 detection rates against actual mean test time. Time pools eleven projects; recall and safety pool nine. These pooled curves are descriptive, not per-project cost-matched comparisons.](../experiments/results/study11-2026-10-21/figures/rq2-budget.png)

Figure 2. B8 detection rates against actual mean test time. Time pools eleven projects; recall and safety pool nine. These pooled curves are descriptive, not per-project cost-matched comparisons.

**Answer to RQ2.** Savings of about 40 % are possible at 90 % recall, but
much smaller savings if every failing commit must be fully caught. The
curve is project-specific: wicket-bootstrap only becomes safe above about
80 % of the test time.

### 4.3 RQ3: calibration

| | Uncalibrated | Platt | Isotonic |
|---|---|---|---|
| ECE (pooled) | 0.100 (n = 11) | 0.022 (n = 9) | 0.021 (n = 9) |
| ECE, same 9 projects | 0.118 | 0.022 | 0.021 |
| Brier (pooled) | 0.075 (n = 11) | 0.021 (n = 9) | 0.022 (n = 9) |

Achilles and jsprit have no failures in their validation split, so no
calibrator could be fitted. On the nine others ECE fell on eight and stayed
equal on one (jade4j). At commit level, the mean absolute gap between the
estimated skip risk and the observed miss rate fell from 0.274 (B7,
uncalibrated) to 0.078 (B8, calibrated), improving on 7 of 11 projects and
getting worse on LittleProxy (0.22 to 0.27).

The balanced class weights used for training push raw probabilities up,
so the uncalibrated column above is a weak baseline. Training the same
model without class weights gives a stricter one (`class-weight-summary.md`,
same 9 projects, mean over 5 seeds):

| | Balanced, raw | Balanced, isotonic | Unweighted, raw | Unweighted, isotonic |
|---|---|---|---|---|
| ECE | 0.118 | 0.021 | 0.030 | 0.021 |
| Brier | 0.090 | 0.022 | 0.029 | 0.023 |
| Skip-risk gap, 50 % budget | 0.306 | 0.067 | 0.054 | 0.071 |
| PR-AUC (n = 9) | 0.138 | | 0.103 | |

The unweighted model is already well calibrated. Calibrating it lowers ECE
on 5 of 9 projects and raises it on 4; the clear gains are on the two
projects with the most failures (wicket-bootstrap 0.171 to 0.102, HikariCP
0.020 to 0.013). Its commit-level risk estimate is as close to the observed
miss rate as any calibrated variant. Balanced weights, on the other hand,
rank failures better (PR-AUC 0.138 against 0.103, much of it from optiq,
which has four failing test commits).

The ECE comparison does not show how the probabilities behave in a
decision. The same check therefore ran the hybrid policy B10 (section 4.4:
rules order, stop when the estimated skip risk is at most 0.05) with each
model's raw and isotonic probabilities (`class-weight-summary.md`):

| B10 (target 0.05), same 9 projects | Time | Recall (n = 7) | Safety (n = 7) | Est. risk | Observed miss | Within 5 % |
|---|---|---|---|---|---|---|
| Balanced, isotonic (the study's model) | 0.36 | 0.80 | 0.72 | 0.023 | 0.031 | 8 of 9 |
| Balanced, raw | 0.56 | 0.71 | 0.65 | 0.011 | 0.024 | 7 of 9 |
| Unweighted, raw | 0.26 | 0.50 | 0.46 | 0.018 | 0.044 | 6 of 9 |
| Unweighted, isotonic | 0.35 | 0.80 | 0.68 | 0.023 | 0.031 | 8 of 9 |

With the unweighted model's raw probabilities B10 stops far too early: it
spends 26 % of the test time, is safe on only 46 % of failing commits, and
misses failures on 4.4 % of commits while estimating 1.8 %, breaking the
target on 3 of 9 projects. Calibrating the same model restores the target
on 8 of 9 and matches the study's model almost exactly. A stopping rule
sums the small probabilities of every skipped test, so a slight
underestimate of rare failures, invisible in ECE, becomes a large
underestimate of commit risk.

![Figure 3. Calibration and B10 stopping on matching nine-project cohorts. Labels count projects within the 5% target; a pooled mean below target does not imply that every project met it.](../experiments/results/study11-2026-10-21/figures/rq3-calibration.png)

Figure 3. Calibration and B10 stopping on matching nine-project cohorts. Labels count projects within the 5% target; a pooled mean below target does not imply that every project met it.

**Answer to RQ3.** Calibration makes the class-weighted model's
probabilities and commit-level risk estimates far more reliable (ECE 0.118
to 0.021, risk gap 0.306 to 0.067). Most of the ECE gain undoes the class
weighting: a model trained on the natural failure rate has a low ECE
without a calibrator. Calibration is nevertheless what makes the risk
estimate usable for decisions: without it, a risk-target stopping rule
breaks its target on a third of the projects; with it, the target holds on
8 of 9, whichever way the model was trained.

### 4.4 RQ4: fallback and risk-based stopping

At default settings the fallback policies look much safer than B8 (pooled
safety 0.68 for B8; 0.84 B9r, 0.85 B9n, 0.93 B9), but they also spend more
time (0.50 against 0.61, 0.77, 0.82). At the same test time
(`summary.md`, "Policies vs baselines at the same test time"):

| Comparison (same time) | Safety Δ [95 % CI] | Recall Δ [95 % CI] |
|---|---|---|
| B9r (risk fallback) − B8 | +0.074 [0.000, 0.149] | +0.003 [−0.005, 0.013] |
| B9n (unfamiliar-change rule) − B8 | −0.006 [−0.109, 0.109] | −0.018 [−0.114, 0.092] |
| B9 (both) − B8 | +0.048 [−0.032, 0.146] | +0.009 [−0.067, 0.096] |
| B10 (hybrid) − B8 | +0.075 [−0.055, 0.224] | +0.012 [−0.086, 0.074] |
| B10 (hybrid) − B3 (rules) | +0.075 [−0.001, 0.202] | +0.017 [−0.012, 0.063] |

B9r equals B8 on eight of nine projects; all its gain comes from
wicket-bootstrap, where one expensive test fails repeatedly and a plain
budget only becomes safe above about 80 % of the time. The unfamiliar-change
rule helps jcabi-github (+0.15) and HikariCP (+0.15) and hurts
wicket-bootstrap (−0.30).

The hybrid B10 (rules order, calibrated stopping, D-036) is never lower in
safety than the rules at the same time on any project (higher on four,
equal on five), and with a 5 % target its observed miss rate stays within
5 % on 10 of 11 projects (pooled observed 2.8 %, estimated 2.6 %). The
exception is jcabi-github (observed 20 %, estimated 4.4 %). With stricter
targets (1 to 2 %) the estimates are too optimistic on four projects.

![Figure 4. Saved pooled safety differences and hierarchical bootstrap 95% intervals. Intervals touching or crossing zero do not establish an improvement.](../experiments/results/study11-2026-10-21/figures/rq4-cost-matched.png)

Figure 4. Saved pooled safety differences and hierarchical bootstrap 95% intervals. Intervals touching or crossing zero do not establish an improvement.

**Answer to RQ4.** Fallback does not reliably improve the trade-off once
cost is matched; it helps only where failures are frequent and concentrated
(wicket-bootstrap). The best use of the calibrated model is as a stopping
rule on top of a simple ordering (B10): it is consistently at least as good
as the alternatives and gives a risk statement that mostly holds, but its
pooled advantage is not statistically clear.

### 4.5 RQ5: the dependency graph

Removing the three structural features lowers PR-AUC on jcabi-github
(−0.072, 4 of 5 seeds), optiq (−0.080, 5 of 5) and HikariCP (−0.013, 5 of 5)
and changes it by at most 0.001 elsewhere. On the test split, the share of
failing (commit, test) rows that the graph reaches from the change, against
the share of all rows, is 0.96 against 0.21 on jsprit and 0.66 against 0.49
on HikariCP, but 0.05 against 0.16 on jcabi-github and 0.04 against 0.04 on
wicket-bootstrap. Graph-only selection (B4) does well on jsprit (time 0.41,
safety 0.86, against B8's 0.35 and 0.71) and catches almost nothing on
jcabi-github and wicket-bootstrap (safety 0.06 and 0.04).

![Figure 5. Reachability among all and failing test rows. n counts failing rows; estimates with very few failures are unstable. Reachability alone does not establish the cause of a failure.](../experiments/results/study11-2026-10-21/figures/rq5-graph-signal.png)

Figure 5. Reachability among all and failing test rows. n counts failing rows; estimates with very few failures are unstable. Reachability alone does not establish the cause of a failure.

**Answer to RQ5.** Graph features help on some projects, while reachability
is weak on others. These associations do not identify failure causes. The
graph is a useful component, not a decisive one, on this data.

### 4.6 Additional validation: cross-project transfer (D-039)

The original eleven-project study trains a separate model for each project.
A new, pre-specified check tests actual model transfer on HikariCP, LittleProxy,
jade4j and wicket-bootstrap. All 12 directions and four fresh within-project
controls use five seeds (80 raw evaluations). Source fitting is restricted to
history older than target testing by Git committer date; calibration uses source
labels only. Prior target outcomes remain available as historical features.

Only nine transfer directions have usable source calibration; jade4j's three
eligible source calibration windows lack both classes. Seven of those nine meet
the observed 5% miss target. HikariCP to LittleProxy misses all recorded target
failures (9.43% observed miss, estimated 4.40%). LittleProxy to wicket-bootstrap
has 16.46% observed miss against estimated 3.48%, despite 98.30% failure recall.
Wicket-bootstrap to the other projects uses 97.84–99.96% of full test time.
Raw-model ordering beats rules in only three of twelve directions, and source
calibration worsens target ECE in six of nine available directions.

There are useful individual pairs: HikariCP to wicket-bootstrap uses 72.51% time
with 98.85% commit safety and 0.61% observed miss; its safety gain against rules
at matched time is +0.1034 [0.0449, 0.1711]. This pairwise interval has no
multiple-comparison correction. Some transfer can work, but there is no reliable
general transfer result. All four within-project controls meet the observed
miss target, though one runs the whole suite and jade4j has only two failing
commits among 63; even skipping all its tests meets the unconditional 5% target.

The project should retain target-project validation before trusting a transferred
stopping-risk estimate. This limits deployment claims rather than invalidating
the original within-project findings. Source:
`experiments/results/cross-project-2026-10-24/summary.json` and `FINDINGS.md`;
protocol, all pair/seed reports, recovered-data hashes and package versions are
saved alongside them. Original study reports remain unchanged.

### 4.7 Additional validation: stopping across historical orderings (D-040)

A separately fixed four-project/five-seed extension applies B10 to a history-only
adaptation of the DANTE author artifact’s score. It retains historical failure
rate, inverse-lag conditional stickiness and CCH density, while omitting commit
relevance and using observed test-class lags. This is an independently implemented
adaptation, not full-DANTE reproduction. A preliminary transition proxy is also
archived; both extensions reuse previously inspected windows and are exploratory.

Calibrated stopping meets the observed unconditional 5% miss target on all four
projects for both adapted and rules orders. Raw stopping with the adapted order
fails on HikariCP (5.59%) and wicket-bootstrap (9.64%). Adapted-order calibrated
stopping versus a same-order budget baseline at matched actual cost has pooled
safety difference +0.0460 [-0.0500, 0.2806], and recall difference -0.0056
[-0.0420, 0.0312]. These intervals do not establish a benefit. HikariCP spends
29.39% time under the adapted calibrated order versus 13.33% under rules, with
71.90% versus 72.73% recall. Simple rules therefore remain the live default.

The results support evaluating stopping separately from ordering, but cannot
establish reliability for arbitrary orders or superiority over published DANTE.
Small failure counts, dependent commits and non-confirmatory reuse remain limits.
Source: `experiments/results/dante-history-check-2026-10-24/summary.json` and
`FINDINGS.md`. The separate live 15-feature evidence gate is an engineering
addition, not an empirically demonstrated abstention improvement from this study.

### 4.8 Additional validation: rolling-origin study (D-042, exploratory)

The comparisons above use one fixed chronological split. A rolling-origin
study, with its rules fixed in `docs/EVIDENCE_STUDY_PROTOCOL.md` before it
ran, refits on five successive blocks over the later half of each history
and compares B10 with the rules order B3 under a budget matched to B10's
actual test time. Only the four previously inspected projects were
available, so by protocol this run is exploratory and gives no confirmatory
verdict (source: `experiments/results/rolling-evidence-2026-10-24/`).

| Project | Failing commits | Gate accepted blocks | B10 safety | B3 safety, matched time | Product time | Product commit miss rate |
|---|---|---|---|---|---|---|
| HikariCP | 81 | 0 / 5 | 0.827 | 0.753 | 1.000 | 0.000 |
| jade4j | 28 | 1 / 5 | 1.000 | 1.000 | 0.984 | 0.000 |
| LittleProxy | 38 | 1 / 5 | 0.711 | 0.789 | 0.998 | 0.000 |
| wicket-bootstrap | 248 | 5 / 5 | 0.992 | 1.000 | 0.941 | 0.005 |

B10 minus matched B3, equal project weight, hierarchical bootstrap: safety
−0.003 [−0.036, 0.029], recall +0.008 [−0.005, 0.020]. By the protocol's rule
this is **no meaningful difference**. B10 is less safe than the matched rule
on LittleProxy and wicket-bootstrap, so the earlier wicket-bootstrap gain
does not replicate in rolling blocks.

The validation gate behaves as designed. In the 7 accepted blocks (467
commits) B10 missed a failure on 0.43 % of commits (Wilson upper bound
1.29 %); in the 12 rejected blocks (914 commits) it would have missed 2.74 %
(upper bound 3.77 %). The cost is that the product saves little time: about
6 % on wicket-bootstrap and 0–2 % elsewhere, and five of the seven accepted
blocks come from that one project. The subsequent nine-project confirmation
and completed follow-ups are reported in sections 4.11/4.12; this paragraph
describes the earlier four-project study, not the current completion status.

### 4.9 Additional validation: a Predictive Test Selection baseline (D-061, exploratory)

The closest prior work, Predictive Test Selection [9 in the system
chapters], also stops at a target, but an aggregate one. To measure rather
than argue the difference, B11 implements its rule inside the rolling-origin
design: tests whose uncalibrated score reaches a score cutoff, plus the N
highest-scoring tests, plus changed test classes, with both cutoffs tuned on
the calibration window to test recall 0.95 and change recall 0.999. The rules
were fixed in `docs/PTS_BASELINE_PROTOCOL.md` before the run; B10 reproduced
the rolling study's outcomes exactly (source:
`experiments/results/pts-check-2026-10-25/`).

| Project | B10 time | B10 safety | B11 time (matched) | B11 safety (matched) | B11 test recall at its target | B10 miss rate (target 0.05) |
|---|---|---|---|---|---|---|
| HikariCP | 0.339 | 0.827 | 0.757 | 0.704 | 0.949 | 0.020 |
| jade4j | 0.915 | 1.000 | 0.911 | 0.875 | 0.875 | 0.000 |
| LittleProxy | 0.913 | 0.711 | 0.913 | 0.947 | 0.985 | 0.084 |
| wicket-bootstrap | 0.941 | 0.992 | 0.912 | 0.976 | 0.951 | 0.005 |

At matched time, B10 minus B11 is +0.007 [−0.063, 0.091] in safety, which
the protocol rates **inconclusive**. The comparison is project-dependent.
On HikariCP, B11's count cutoff alone costs more time than B10 uses, so the
two could not be matched: B10 is both cheaper (0.339 against 0.757) and
safer. On LittleProxy, B11 is clearly safer at the same time.

The stated targets differ more than the selections do. Tuned on a short
holdout, B11 kept its 0.95 test-recall target on 2 of 4 projects and its
0.999 change-recall target on none (0.875 to 0.996). B10 kept its 5 %
commit-miss target on 3 of 4 (LittleProxy: 8.4 %). CodeDNA's calibrated skip
risk computed for B11's selections ranks the commits where B11 missed a
failure above the others on all four projects (AUC 0.56 to 0.90), but its
level is wrong for those selections: it is mostly far too high. The
probabilities are informative about which commits are risky; their level is
trustworthy only where it was checked.

### 4.10 Additional validation: conformal risk control for the stop (D-063, exploratory)

Conformal risk control [26 in the system chapters] chooses a threshold from
held-out outcomes so that the expected loss on new data is at most α,
assuming only exchangeability. Here the threshold is B10's stopping risk λ,
chosen on a fixed grid from `fit_audited`'s audit window, with the loss 1
when a commit misses any failure. Two protocols were each committed before
their run: B12 bounds misses over all commits
(`docs/CRC_STOP_PROTOCOL.md`); B12f, written after B12's result, bounds
misses among failing commits only (`docs/CRC_CONDITIONAL_PROTOCOL.md`).

| Project | B10 safety / time | B12 safety / time | B12f safety / time | Gated product safety / time |
|---|---|---|---|---|
| HikariCP | 0.827 / 0.339 | 0.506 / 0.110 | 1.000 / 1.000 | 1.000 / 1.000 |
| jade4j | 1.000 / 0.915 | 0.929 / 0.700 | 1.000 / 0.965 | 1.000 / 0.984 |
| LittleProxy | 0.711 / 0.913 | 1.000 / 0.932 | 1.000 / 0.998 | 1.000 / 0.998 |
| wicket-bootstrap | 0.992 / 0.941 | 0.976 / 0.728 | 0.976 / 0.774 | 0.992 / 0.941 |

B12 kept its target (at most 5 % of all commits missing a failure) on 3 of
4 projects and cut test time by 36 % against the gated product
([−0.379, −0.348] in time ratio). The target itself was the problem: only
11 % of HikariCP's commits fail, so 5 % of all commits allowed half its
failing commits to be missed. B10's 5 % target shares this weakness.

B12f fixes the target. It kept commit safety at or above 0.95 on all four
projects, where B10 did so on two. It used slightly less time than the
gated product: −0.047 [−0.054, −0.040], almost all of it on
wicket-bootstrap. On the other projects B12f ran nearly the whole suite,
because at least 19 failing audit commits are needed before it allows any
skipping. B12f therefore replaces a hand-picked gate with a stated
statistical rule that behaved at least as well here, but it does not make
selection cheap where failures are rare. Time-ordered commits are not
exchangeable, so the bound is an assumption checked on four projects, not a
guarantee.

### 4.11 Nine-project confirmation of B10 and the gate

The frozen nine-project study found no meaningful safety difference between
B10 and the recent-failure ordering B3 at matched recorded test time:
-0.72 percentage points, 95% interval [-3.39, +1.79]. Failing-test recall
was lower by 9.22 points [-11.30, -7.28]. The observed-rate gate criterion
was supported: accepted blocks missed failures on 2.52% of all
evaluation commits, with one-sided Wilson upper bound 3.35%. This is an
all-commit miss rate, not conditional failing-commit safety.
Eight blocks accepted, 36 rejected, and one DSpace block could not fit.
The gated product's equal-project mean recorded test-time fraction was
93.67%. None of this establishes future calibration or CI wall-clock savings.

The source report and all denominators are in
`docs/CONFIRMATORY_RESULTS_2026-10-26.md` and
`experiments/results/rolling-evidence-confirmatory-windowsfix-2026-10-26/`.

### 4.12 Nine-project follow-ups: B12f, B11, B13 and B13f (D-067)

Four fixed-method follow-ups completed on the nine datasets. The original
protocols, code/input hashes, raw outcomes and exact findings are under
`experiments/results/*confirmatory-perf-2026-10-26/`. B13 and B13f are
exploratory because their design used the B10 confirmation evidence.
The CRC/PTS nine-project addendum requested by the handoff was not committed
before these runs. The four-project method protocols existed, but this
does not justify calling every subsequent decision preregistered.

| Comparison | Recorded time difference (pp) | Safety difference (pp) | Interpretation |
|---|---|---|---|
| B12f - gated product | -16.20 [-16.87, -15.53] | -1.79 [-2.72, -0.84] | More savings with lower mean safety |
| B13 - gated product | -23.36 [-23.99, -22.77] | -4.17 [-5.34, -3.10] | Exploratory; non-inferiority criterion inconclusive |
| B13f - gated product | -3.61 [-4.14, -3.08] | +0.54 [-0.25, +1.42] | Exploratory savings; safety advantage not established |
| B10 - attempted matched B11 | -31.10 [-32.51, -29.73] | -16.13 [-19.03, -13.12] | Cost match failed; not a same-time comparison |

Intervals are the saved 95% bootstrap intervals, with equal project weight
and the existing serial-dependence/multiplicity limitations. These time
fractions exclude model fitting, feature extraction, compilation and startup.

B12f achieved conditional commit safety >=0.95 on 8/9 projects, exceeding
the handoff's 7/9 rule. The novelty branch's saved script still used >=3;
the findings apply the corrected count without changing frozen reports.
Pooled B12f safety was 95.88%, while Cloudify achieved only 87.84%.
The pooled point is not a lower confidence bound or a per-project guarantee.
Because of the missing addendum/absolute-safety interval and the observed
safety decrease, D-067 keeps B10 as default and CRC opt-in under D-068.

B13's all-commit miss target and failing-commit safety use different
denominators; passing the former on nine projects does not establish the
latter. B13f met the conditional target on 8/9, with Cloudify below 95%.
PTS tuning hit the lowest tested recall cutoff on all nine projects and
left large residual costs: its machine verdict `harms` cannot be described
as evidence at equal test time. The complete residuals remain in its findings.

One DSpace fit failure was recorded in each run. The risk/gate policies
fell back to the full suite; the PTS comparison excluded the unfit block.
A performance repair replaced the quadratic prefix scan with binary search
using the unchanged risk arithmetic. B13 reuses seven byte-identical old
reports, with both source versions disclosed; a real-project full-report
replay was exactly identical. All other new jobs used the optimized code.
No model, threshold grid, split or success rule was tuned after these results.

### 4.13 Observation-isolated development pilot (D-076)

Before evaluation, protocol v2 was frozen in commit `1965665`. The first 360
reference commits of the previously inspected HikariCP dataset were replayed:
240 common full-suite warm-up commits, followed by 120 evaluation commits.
Each policy saw only its own executed outcomes from earlier commits ancestral
to the current push base. Complete observed commits alone entered model
fit/calibration/audit; decision-time feature vectors were frozen before reveal.
A fixed full audit every tenth evaluation commit replaced reduced execution.
All 360 code snapshots matched the recorded test universe exactly.

| Policy | Reduced suites | Zero-omission safe failing commits | Missed failing class outcomes | Evaluation recorded test seconds | Recorded seconds with warm-up |
|---|---:|---:|---:|---:|---:|
| Full suite | 0/120 | 3/3 | 0/4 | 1050.442 | 2068.276 |
| Audited B10 history | 0/120 | 3/3 | 0/4 | 1050.442 | 2068.276 |
| Dependency structure | 40/120 | 3/3 | 0/4 | 889.509 | 1907.343 |
| B10 plus structural floor | 0/120 | 3/3 | 0/4 | 1050.442 | 2068.276 |

The two risk-gated policies refused all 108 ordinary evaluation decisions;
12 other decisions were scheduled audits. The first prior candidate audit
missed six of 60 commits and seven of 11 failing class outcomes (36.36%
failure recall; 18.19% all-commit miss-rate upper bound). Later refusals also
included fewer than ten failure-bearing audit commits. The gate therefore
demonstrated abstention, not useful risk-gated reduction, on this prefix.

Dependency selection saved 15.32% of recorded evaluation test seconds (7.78%
including warm-up), but only three evaluation commits failed. This establishes
neither 95% future safety nor comparative superiority. All policies caught the
four failing class outcomes, including one first-recorded and three recurring
outcomes; no build escape occurred. These are separate diagnostic endpoints.

Measured structural-analysis function time was 1164.203 seconds over the 120
evaluation snapshots. Full-suite analysis overhead was not separately timed;
most mapping overlapped local validation. Worker startup, failed attempts and
checkpoint I/O are excluded. A net CI speedup or precise matched net slowdown
cannot be inferred by summing these timings with historical test durations.
One extraction exceeded the fixed 90-second deadline; a retry reused 329 saved
mappings and completed under unchanged source, inputs, cohort and thresholds.

The gated policies observed complete outcomes at every commit, so this pilot
does not establish their selective-learning behavior under feedback starvation.
Synthetic mutation tests verify observation isolation; structural-only had 40
partial observations but does not train a history model. This is a development
implementation/mapping check on inspected data, not independent confirmation.
The next engineering priority is measured analysis overhead and caching,
followed by bounded cancellation/progress; no favorable result is assumed.

Source traces, independent accounting checks and refusal counts:
[D-076 findings](../experiments/results/partial-feedback-pilot-d076-2026-10-27/FINDINGS.md),
[summary](../experiments/results/partial-feedback-pilot-d076-2026-10-27/summary.json),
[raw traces](../experiments/results/partial-feedback-pilot-d076-2026-10-27/results.json).

## 5. Threats to validity

- **Construct.** Results are per test class, not per test method. "Commit
  safety" counts a commit as safe only if every failing class was run; a
  flaky failure counts like a real one, because RTPTorrent does not mark
  flakiness.
- **Calibration baseline.** Both models are trained with balanced class
  weights, which pushes raw probabilities upwards. Section 4.3 therefore
  also reports an unweighted model; most of the calibration gain turns out
  to correct the class weighting. B10 was also run with the unweighted
  model: it needs calibration to keep its target (section 4.3).
- **Independence.** The skip-risk formula assumes test failures are
  independent; one bug often breaks several tests. Bootstrap intervals treat
  test commits as independent, but neighbouring commits are correlated, so
  the intervals are somewhat optimistic.
- **Internal.** Splits are chronological and features use only earlier
  commits, so no future information leaks. Seeds change only model
  randomness; the fixed split means intervals do not cover other periods.
- **Transfer.** The added four-project check includes only one model/protocol,
  historical target features and fixed target windows. Source-only calibration
  is unavailable in three directions and violates its observed miss target in
  two others. Target risk must be validated rather than inferred from source
  calibration.
- **External.** Eleven open-source Java projects from 2007 to 2016 on
  Travis CI. Two have no evaluable failures, several have very few, and one
  project (wicket-bootstrap) drives most selection differences. The results
  may not transfer to modern or industrial CI.
- **Comparison with prior work.** B11 (section 4.9) follows the published
  Predictive Test Selection rule but uses CodeDNA's 15 live features, not
  Facebook's, and omits its deployment check. The commercial tools [11, 12
  in the system chapters] are closed and are compared by documentation only.
  B11 was first run on four exploratory projects; its nine-project follow-up
  did not achieve equal test time (section 4.12).
- **Reliability.** Every number comes from the stored data and saved reports;
  dataset hashes, package versions and commands are recorded
  in each report, and rerunning the experiments reproduced earlier numbers
  exactly.

## 6. Conclusion

CodeDNA combines change-impact analysis, test selection, and an explicit
refusal to skip tests without target-project evidence. Its research does
not establish that ML orders tests better than simple rules, or that B10
improves safety over recent-failure ordering at matched time: the nine-project
confirmation found no meaningful safety difference and lower test recall.
The audited gate's observed miss-rate criterion held, at the cost of modest
recorded-test-time savings. These observations are not guarantees of future
safety or measured CI wall-clock speedup.

Failure-conditional CRC B12f reached 95% safety on eight of nine follow-up
projects and saved more recorded test time, but mean safety was lower than
the gated product and Cloudify missed the target. It remains an implemented
opt-in method, not the default. B13f is promising exploratory evidence;
the attempted PTS match leaves a large cost gap and cannot answer an
equal-time comparison. The missing nine-project addendum and existing
statistical limitations are explicit. Cross-project model transfer remains
unestablished. The contribution is a working, inspectable brake with honest
fallbacks and documented limits, not a universal fast or guaranteed selector.


## Additional validity limit: feedback available after selection

The retrospective feature builder correctly excludes current/future outcomes.
It nevertheless uses all stored earlier results. In deployment, a skipped test
may remain unobserved, so subsequent history features and audit eligibility can
differ. Existing results describe full-history retrospective replay, not a
validated closed-loop partial-feedback deployment. Live recording accepts only
complete full-suite evidence; a passing subset is not a fully passing commit.
D-076 adds an observation-isolated development pilot (§4.13), but its risk
policies never reduced a suite. Broader selective-learning performance remains
unvalidated; the prior full-history studies are not recast as closed-loop evidence.

Safety definitions also differ across prior work: CodeDNA counts a failing
commit as safe only when no failing test was omitted. Build-escape measures
count a miss only when no failure was caught. These numbers are not directly
comparable. See NOVELTY_REVIEW_2026-10-27.md for the source comparison.
