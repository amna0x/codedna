# D092: completion-aware rolling main-branch replay

Purpose: repair the frozen-history evaluation mismatch, without changing the
application, model settings, risk target or old results. D091 is now inspected
and cannot become fresh confirmation. Reuse existing observation-isolation
concepts from partial_feedback.py; do not duplicate or replace the live brake.

Availability phase, before test outcomes: inspect public Apache Jenkins main,
master and trunk jobs under the observed Jackrabbit, James, Kafka and Karaf
folders. Exclude PR, release and non-Java jobs. Keep every availability failure.
Select the lexicographically first job with at least 240 completed retained builds
and SCM identity metadata. If none qualifies, retain the initially selected Oak
trunk job as an engineering pilot only and report insufficient research history.
No job is selected because it has attractive failure/savings numbers.

Freeze raw job metadata and chosen build identities before fetching reports.
Record exact SHA, first parent, branch, build start and completion times. Require
first-parent source identity and source-discovered test inventories before a
selective model decision; a test report is not a decision-time candidate list.
Do not infer main-branch provenance from a job name alone.

For each build, emit and persist its decision before loading that build's test
outcomes. History includes only earlier completed full observations whose finish
time is no later than the decision's start time. Overlapping runs cannot reveal
future results. Reveal each result after its decision and release it to later
decisions only on completion. Keep reruns and every failure; do not silently
overwrite an earlier failed attempt with a passing one. A missing, skipped or
partial report never becomes complete history.

Apply existing first-parent/latest-BASE and evidence rules at every step. A
full-suite selection means all observed reference tests; it is not a model
accuracy win. If counts could permit skipping, actual existing live model/feature
and source-inventory checks are required; otherwise mark pending rather than
invent scores or weaken safeguards. Seed/settings remain unchanged.

Compare full-suite reference, simple ordering and CRC only where valid inputs
exist. Prespecify any matched execution subset before observing runtime results.
Historical duration sums are estimates, not measured CI savings. Fifteen current
Oak builds cannot establish a calibrated risk advantage; report that limitation
instead of manufactured bugs or retroactively relabeled historical passes.
