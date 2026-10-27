# D-076: bounded partial-feedback development pilot

Frozen before implementation/evaluation, 2026-10-27. Machine-readable settings:
[PARTIAL_FEEDBACK_PILOT_D076.json](PARTIAL_FEEDBACK_PILOT_D076.json). Record its
canonical JSON hash and the protocol Git commit in every output. This is a
development pilot on previously inspected data, not a confirmatory study.

## Inputs and scope

Use the first 360 chronological HikariCP reference commits: 240 common full-run
warm-up commits and 120 evaluation commits. Use the CSV and SQLite hashes in
the JSON. Do not choose commits by failures or a favorable policy result.
Source dependency plans are generated without outcomes. Warm-up uses the
full-reference selection; evaluation uses the current dependency selector.
Require exact discovered/reference class-universe mapping. On a mismatch,
stop with a diagnostic; do not silently discard classes or substitute a proxy.
Record unknowns, warnings and mapping failures. Plans may be checkpointed, but
resumption must verify input/config/code fingerprints and cached plan hashes.
No project test/build is executed. Execution is simulated from recorded class
outcomes, conditional on the available reference records being the benchmark
truth; they do not independently certify real CI suite completeness.

## Four policies

1. Full reference: every recorded test class on every commit.
2. History-only: existing audited B10 stopping, without the structural floor.
3. Structural-only: current dependency selection, changed tests, conservative
   fallbacks and project pins; no claimed risk probability.
4. Combined: union of history-only stopping and the structural/policy floor.

All receive the same warm-up and scheduled full audits every tenth evaluation
commit, chosen by index before outcomes are revealed. Full audits execute the
whole reference set once, replacing a reduced execution; no duplicate execution
is introduced by the schedule. On audit/warm-up commits no counterfactual
selection is needed. Record proposed versus final sets on ordinary decisions.
Unknown structural availability forces full selection for structural policies.
Do not change released defaults, risk target, gate thresholds or models.

## Information separation

The evaluator retains labels and current runtimes; decision objects do not.
Every policy owns its history and model. Each decision vector uses current
code metadata and histories rebuilt only from that policy's executed results.
Never copy full-history failure/duration features from the CSV. A skipped
result stays unknown. Freeze features at decision time before revealing
outcomes; later model fits may not rebuild old features using future knowledge.
Current runtimes are used for evaluation cost, not ordering/stopping inputs.
First/recurring-failure categories are evaluator-only, never policy features.

Both risk policies refit every 20 evaluation commits, starting after warm-up.
Fit/calibration/audit use only complete observed reference commits, with the
existing chronological 50/25/25 split, gradient boosting, isotonic calibration,
seed 0 and B10 target 0.05. Selected-only observations still update history
features but are not treated as complete calibration/audit commits. This is
deliberately conservative: no missing outcomes are filled in. If fitting or
the existing audit is inadequate, run all classes and log the reason. An
actual full execution, including fallback, supplies complete observed history.
Data remain temporally dependent; no new statistical safety guarantee is claimed.

## Endpoints and cost

Primary: evaluation commits with failures on which no failing class is omitted,
divided by evaluation commits with failures. Undefined when none fail.
Secondary: build-escape rate, micro failing-class recall/missed-class fraction,
first-failure versus recurring-failure capture and reduced-suite coverage.
Report raw numerators/denominators, audit counts, gate refusals, proposed/final
selection sizes and per-policy complete-observation history sizes.

Count all recorded selected-class seconds, including warm-up, scheduled audits
and mandatory classes. Also show evaluation-only cost; do not hide warm-up.
No additional repeated runs are simulated; the source durations may already
include merged original CI reruns. Report source-plan extraction and local
replay/model overhead separately. Historical CI seconds and current laptop
analysis seconds are not a measured common-hardware CI wall-clock speedup.
Unmeasured build/discovery costs remain unknown. No "matched total cost" claim
is justified merely by adding these components.

## Acceptance and stopping rules

Before real data: mutation tests must prove that still-hidden labels/durations
cannot affect choices until observed; original CSV history features must not
affect choices; each policy must have isolated state; audit timing must not
depend on hidden failures. Test unknown data, empty selections, policy pins,
full audit overrides and single-class/insufficient-history fallback.

This pilot assesses implementation, leakage prevention and runtime. It does not
test a superiority hypothesis or establish 95% deployed safety. All-full-suite
behavior is a legitimate result, not grounds for tuning thresholds until a
gain appears. Record whether reduced risk decisions actually occurred.
Do not automatically run the nine-project set (it lacks structural columns).
Choose any larger exploratory follow-up only after this pilot's data/mapping,
invariance and runtime checks pass. Preserve all previous studies and findings.
If faithful input mapping is infeasible, narrow the thesis to its retrospective
claim rather than manufacturing a successful closed-loop result.
