# Larger-scale evaluation outcome

See experiments/results/larger-history-d091-2026-10-29/FINDINGS.md for exact
project-level records, acquisition limits and scope. The study screened 6,726
heads from Hadoop, Hive, Jackrabbit Oak and Kafka and replayed all 1,348 fixed
evaluation outcomes. Recorded ground truth contains 766 failing commits and
4,502 failing-class occurrences.

With the unchanged live first-parent/latest-BASE requirements, 1,305 targets lack
current BASE history, 35 have insufficient audit evidence even in the best case,
and eight have unavailable source identities. Thus no skipping benefit was
established: 1,340 full-suite recommendations and eight source-blocked cases.
This is not a fitted-model accuracy result or measured CI-wall-time comparison.

The limitation is operational history compatibility in this frozen-history
experiment. Build volume alone did not solve it. A faithful independent follow-up
would require main-branch sequential CI outcomes and a prespecified rolling update
rule, not another outcome-driven project/window search or weaker safety target.
Previous evaluation outcomes were not rolled forward here, so these findings do
not establish that the live brake can never provide savings in deployment.

The application stayed unchanged at a02d20f (780 tests passed with Maven and
Gradle). No features, thresholds, case replacements or old findings were changed
to produce positive remarks. No code push/merge or installer replacement.
