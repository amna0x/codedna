# Partial-feedback follow-up: input feasibility (2026-10-27)

## Decision

Proceed to a small, protocol-first development pilot using the four existing
structural datasets. Do not launch the nine-project evaluation or present the
follow-up as independent confirmation. The required inputs largely exist;
the policy-specific observation engine and leakage-proof validation do not.
No new selector performance experiment was run by this assessment.

## What exists

| Project | Labelled class rows | Commits | Commits with failures | Dependency-reachable rows |
|---|---:|---:|---:|---:|
| hikaricp | 20,206 | 1,427 | 123 | 8,921 |
| jade4j | 10,913 | 314 | 59 | 4,088 |
| littleproxy | 4,575 | 262 | 60 | 2,213 |
| wicket-bootstrap | 34,791 | 820 | 323 | 3,170 |

These four study11 CSVs contain dependency reachability/distance/confidence,
test-file changes, outcome labels and recorded durations. Their SQLite stores
contain changed-file paths, supporting recomputation of observed co-failure
history. All four recorded repository directories exist. Git objects were
checked for first/middle/last HikariCP snapshots. CSV chronology, binary labels
and finite nonnegative durations passed this read-only inventory. Original
files were not rewritten; the audit records raw CSV hashes.

The nine confirmatory CSVs were prepared with `structural: false`; none has
the three dependency columns. Reusing them as-is cannot evaluate a genuine
dependency-floor ablation. Their history/cost rows remain useful, but adding
structural evidence would be separate preparation with its own provenance.

## Current-selector extraction probe

The existing production dependency selector was called on HikariCP's first,
middle and last eligible labelled commit with a parent. Snapshot choice used
commit order, not outcomes. No project code, test run or model fit occurred.
All three plans were available, taking 3.172, 5.469 and 4.078 seconds locally.
Discovered universes matched the reference classes exactly: 1, 16 and 21.
Selected counts were 1, 1 and 21. These are feasibility counts, not safety or
speedup estimates. A warning identified one non-default test class on the
later snapshots; it was not silently inserted into the benchmark universe.

Three snapshots do not establish coverage over the full history or other
projects. Legacy CSV dependency features are not a complete snapshot of the
current brake: conservative full-suite fallbacks, project policy and analysis
availability also matter. A faithful current-brake comparison needs a separate
code-only plan sidecar per evaluated commit, including reasons and unknowns.
The structural plan must remain independent of outcome labels.

## Required implementation before the study

1. Freeze a protocol: class-level zero-omission safety primary; build escape
   and missed-class fraction secondary; fixed cohorts, chronological splits,
   warm-up, audit/retraining schedules and statistical analysis.
2. Create one observed state per policy. Only selected results and completed
   full audits update it. Freeze feature vectors at decision time; never treat
   a skipped outcome as passed or reuse the CSV's full-history outcome features.
   Recompute past counts, failures, streaks, durations and co-failure history.
3. Keep evaluator truth separate. Policies may know code/discovered test IDs,
   not hidden labels or current recorded runtimes. Use observed duration
   estimates for decisions; current recorded duration is evaluation cost only.
4. Compare full-reference execution, history-only stopping, structural-only
   selection and their union. Keep the existing default and risk thresholds;
   any B10/CRC method choice must be fixed before evaluating, not chosen from
   whichever produces favorable results.
5. Record proposed statistical selection separately from final required tests.
   Include policy pins, audits, repeated executions and measured analysis/model
   overhead. Report test-time cost and CPU overhead separately; no CI wall-time
   claim follows from adding recorded serial durations.
6. Validate source/test-universe mapping and structural-plan availability on
   every evaluated commit. Unknown or unmatched units require an explicit
   conservative rule; they must not become unreachable/passing by default.
   Historical CI records do not independently certify complete suite truth.
7. Prove non-interference: changing still-hidden outcomes must not change
   decisions before those outcomes are observed. Test delayed audits, missing
   histories, single-class fits and audit insufficiency. Keep full-suite refusal.

First versus recurring failures are evaluator-only categories. A policy cannot
be given an oracle flag telling it that a hidden failure is the first one.

## Go/no-go and scope

Start with a bounded development pilot; do not rebuild already completed
studies. Proceed to the four-project follow-up only after observation-isolation
tests, complete mapping/status accounting and a measured runtime estimate pass.
Do not choose evaluation commits by whether the structural floor catches their
failures. Record exclusion and fallback rates, including projects with too few
failing audit commits. No failing commits means conditional safety is undefined.

Every available project has previously been studied. The follow-up is an
exploratory, protocol-frozen re-evaluation of a new information assumption,
not an untouched confirmatory benchmark. A new external confirmation would
require a genuinely unused cohort. Preserve all previous negative findings.

If faithful mapping or observation isolation cannot be established within the
bounded pilot, retain the retrospective system claim and report this limitation.
The software FYP should not depend on manufacturing a positive new result.

Evidence: [input audit](PARTIAL_FEEDBACK_INPUT_AUDIT_2026-10-27.json) and
[structural probes](STRUCTURAL_FEASIBILITY_PROBES_2026-10-27.json).
