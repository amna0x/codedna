# D092: completion-aware main-branch replay engineering

The research runner now separates decision, persistence, truth retrieval and
completion-time availability. It does not add product features or change the
existing application, model settings, risk target or source/history gates.

## Implemented behavior

- Sort CI decisions by actual start time and build identity.
- Give a decision only immutable prior observations whose runs have finished.
- Persist its decision before loading the current report.
- Release a newly observed result to later decisions only at its completion time.
- Preserve reruns independently. Conflicting repetitions cannot erase a failure
  or count as several independent historical commits.
- Reject incomplete/unknown report data as training evidence. Verify Maven root
  counts against child results instead of inventing an omitted pass count.
- Require actual source features/test-universe validation and the existing live
  model before any selective decision; this pilot does not invent probabilities.

This timing/orchestration layer reuses existing validation logic and the project's
observation-isolation design. It is not a second implementation of model fitting,
test selection or conformal stopping.

## Fresh main-branch data availability

Inspected 26 public Apache main/master/trunk jobs under Jackrabbit, James, Kafka
and Karaf. None met the prespecified 240 completed SCM-identified retained-build
criterion. The initially chosen Oak trunk job retained 15 completed builds.
No job was chosen because it offered favorable failure or savings outcomes.

The first availability request had URL-encoding errors and returned HTTP 400;
that acquisition report is preserved separately. Corrected requests produced
the actual counts. HTTP errors were not treated as zero-build research results.

Pinned all 15 Oak identities before report retrieval. Every revision was verified
on the fetched public trunk first-parent history, with branch metadata and parent
identity. These are genuine main-branch CI records, not substituted PR snapshots.
Retained builds span April 2024 to October 2026, with large gaps: they are not a
continuous, representative history of every tested commit. Retention bias is
unknown and no failure-rate generalization is justified.

## Actual pilot and adapter correction

All 15 decisions were saved before accessing their corresponding reports. Eight
reports were downloadable; seven returned 404. The first parser incorrectly
expected a top-level pass count on Maven aggregated reports. Jenkins exposes that
count in child results. The tested correction sums complete child counts and
checks every exposed root count. A mismatch still refuses completeness.

The initial run is retained unchanged. The corrected run replays exactly the
same cached inputs, with zero new report-download bytes, preserving the seven
initial unavailable reports. It is explicitly an engineering replay of inspected
data, not an independent second experiment. All eight available reports validate
as published; seven contain observed failing classes. No observed failure count
changed between adapters. Complete-as-published does not establish that the
source-discovered default test universe was fully run; that validation is pending.

All 15 decisions required full suites because no completed usable result existed
at the requested immediate BASE in this sparse retained sample. No model fits,
selective decisions, new builds, calibrated benefit or net-CI saving were measured.
This is a working rolling-order pilot, not the requested large effectiveness
demonstration. More complete sequential main-branch CI data is still required.

## Verification and reproducibility

Seven offline tests passed in 5.20 seconds, using temporary Git repositories.
They verify decision-before-truth persistence, overlapping-run isolation,
future-label mutation invariance until completion, failure-preserving reruns,
duplicate identity refusal and Maven aggregate count checks. Actual pilot traces
were checked independently against completion timestamps.

Eight raw reports and 26 availability metadata snapshots are preserved in 34
SHA256-checked gzip inputs totaling 1,664,862 compressed bytes. The original
reports contain 25,546,933 bytes. See the corrected result folder's input manifest.
The uncompressed duplicates are locally retained but ignored by Git.

The original application remains a02d20f, with its recorded 780-test full
Maven-inclusive pass. Research-only changes do not imply a new application test
count or installer build. Earlier D090/D091 studies, stashes, website and releases
remain unchanged. No push or merge.
