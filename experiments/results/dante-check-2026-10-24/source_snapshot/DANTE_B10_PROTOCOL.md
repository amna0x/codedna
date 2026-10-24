# Fixed DANTE-H / B10 extension protocol — 2026-10-24

Status: specified before this extension's model results. This is an exploratory
extension: original study and transfer test outcomes have already been inspected.
It is not a new untouched confirmation of the original hypothesis.

Working claim: CodeDNA evaluates whether calibrated stopping improves the testing
trade-off across history-based orderings and identifies unreliable risk estimates.
No universal-ordering, superiority, first-system or safety-guarantee claim.

## Independent baseline and attribution

DANTE: Reale et al., ICST 2026, doi:10.1109/ICST69053.2026.00080;
https://re.public.polimi.it/handle/11311/1309638 and author artifact
https://zenodo.org/records/18900675.

DANTE-H here is an independently designed, DANTE-inspired history-only
approximation, NOT the authors' algorithm or a reproduction of published results.
It omits commit/test relevance, LRTS preprocessing and the published stickiness
formula. It tracks per-test passing/failing transitions, with a Beta(1,1) global
transition prior and two prior observations for each local transition. Predictions
are emitted before each commit is observed; only then are counts updated. Order
by transition score / historical estimated duration; tie by test ID. These scores
are ranking heuristics, not calibrated omission probabilities. Comparison against
this baseline cannot establish superiority to full DANTE. Authors' published
implementation remains a future stronger external comparison.

## Fixed experiment

Use the four restored datasets HikariCP, LittleProxy, jade4j, wicket-bootstrap;
seeds 0–4. Original chronological 60/20/20 split, balanced histogram GB, isotonic
calibration on validation only. Latest 20% is the evaluation window; earlier test
window outcomes can update history features/ranking after their prediction.
No parameter selection on these test results. Record missing fits explicitly.

D1: DANTE-H ordering, 50% estimated-duration budget, changed tests always run.
D2: same DANTE-H ordering, B10 stopping at estimated 5% skip risk; separately raw
and calibrated model probabilities. Compare with recent-failure ordering + the
same B10 raw/calibrated probabilities. Match D1's mean actual test-time cost to
D2 using the existing budget-matching method; report residual cost differences.

Report recall, safety conditional on failing commits, unconditional miss rate,
estimated skip risk, runtime, raw-model ordering APFDc, target failure counts,
and paired bootstrap intervals. Aggregate seeds within project then equal weight
projects. 2000 hierarchical resamples, seed 0. Four projects are four units, not
20 independent projects. Commit resampling ignores serial correlation; intervals
are exploratory and do not adjust for multiple comparisons. No universal claim.

Record dataset, source, protocol and output hashes and package versions. Refuse
to resume if fingerprints differ. Record fit and scoring/selection overhead;
CSV extraction and CI startup are excluded, so no end-to-end CI speedup claim.

## Operational gate (separate from this retrospective experiment)

For live use, fit only older target history: first 50% training, next 25%
calibration, latest 25% audit. Frozen GB/isotonic model, recent-failure order,
5% skip-risk target. Accept only when the prior audit has a one-sided 95% Wilson
miss-rate upper bound <= target, at least 10 failure-bearing commits and >=90%
failing-test recall. These conservative engineering thresholds are fixed before
live deployment, not tuned to make this extension pass. Serial dependence means
the bound is an evidence screen, not a deployment guarantee.

Require repository/ancestry binding, current history at BASE, no current/future
labels, and evidence for every current candidate. Unsupported changes, uncovered
tests, invalid/missing calibration or failed audit produce full-suite selection
and risk-unvalidated status. Keep audit risk distinct from the selected full
suite's residual risk. Full-suite audits must refresh history; selected-only runs
cannot establish absence of missed failures. No universal transfer is enabled.
