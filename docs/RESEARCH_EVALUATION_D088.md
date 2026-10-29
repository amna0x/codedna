# D088: independent evaluation preparation

Status: selection protocol; no effectiveness results. Application source is
frozen at a30ce70. D087 full-suite validation must finish and any failure must
be resolved before behavioral evaluation. Preserve the failed invocation.

## Moonshot

Source: GitBug-Java metadata commit fe986fb7919be62c2a6f611ee16659e849646798
(https://github.com/gitbugactions/gitbug-java). This is a documented real-bug
source, unlike the earlier educational algorithm history. Benchmark labels
are evidence to verify, not an infallible correctness oracle.

Group by repository before splitting. Rank repositories by SHA256 of
`codedna-d088-20261029:` followed by the repository ID. Exclude adoble/adr-j
because its metadata/test evidence was inspected during feasibility discovery.
The first six repositories are development; the next twelve are held out.
Within each repository take the earliest fixing timestamp, breaking ties by
fix SHA. Do not replace unsupported or unreproducible cases. Publish the
selection manifest and input hashes before fetching their source or measuring
Moonshot. No held-out algorithm changes after observing outcomes.

Stage 1 audits exact changed source, method identity, external dependencies,
applicable regression tests and buggy/fixed provenance. Record every refusal.
Do not silently rewrite classes, synthesize expected outputs from the fixed
version, guess renamed method correspondence or treat PASS_PASS as bug proof.
Benchmark test evidence must establish the selected behavior failed before and
passed after; otherwise label bug confirmation unavailable.

Stage 2 compares guided and simple search with seeds 7, 19, 41; 32 inputs,
four reduction attempts and 120 seconds per case/mode/seed. Alternate mode
order by case index and seed index. Both receive identical source and budgets.
Known triggering inputs are reserved for oracle verification, never injected
into either search. Supplied-expectation demonstrations are a separate analysis.
Independently compile/run every exported reproducer. Preserve exceptions,
timeouts, compilation errors and partial outputs separately from no difference.

Report all eighteen cases and held-out results separately: support coverage,
confirmed bugs exposed, paired detection counts, time-to-witness and replay
success. Report differences without verified bug oracles separately. Three
seeds are repeated trials, not independent bugs. No production-generalization
claim follows from a small or mostly unsupported sample.

## AI brake

Candidate independent source: LRTS ISSTA 2024 artifact
(https://github.com/lrtsuser/LRTS). Pin its commit and raw data checksums before
analysis. ActiveMQ is chosen now, before inspecting its outcomes. Do not switch
to another project based on favorable results. First verify it was not used in
previous CodeDNA studies and that source identities, chronology, complete test
inventories and outcomes can be reconstructed. Missing provenance stops this
study; it must not be replaced with guessed structural features.

Use the first 1,500 eligible chronological source-identified full-suite builds:
1,000 training/development, 250 audit, 250 untouched evaluation. Group jobs of
the same commit before splitting; never mix PR branches into a claimed linear
ancestry. If fewer builds or insufficient failing audit commits exist, report
insufficient evidence and retain the full-suite fallback. Do not extend the
window after looking at misses. No future build/test outcomes become features.

Compare full suite, structural-only, the existing simple history ordering,
B10 and CRC at risk target 0.05 with existing eligibility and mandatory-test
rules. Freeze model/config/feature hashes before evaluation. Primary outcomes
are missed failing changes and total observed cost; retain failing-test counts
separately. Preserve raw failures, including flaky failures. Filtered LRTS labels
are sensitivity analysis only, never a way to erase inconvenient failures.

Historical class durations produce estimated execution cost, not measured CI
speedup. Measure analysis wall cost directly. An actual net-CI-time claim
requires matched full and selected executions with retries/audits/launch costs,
verified identical source/toolchain and explicit build consent. LRTS reports
long suites; assess laptop feasibility before promising those executions.

Publish sample sizes, refusal frequency, all misses and uncertainty. Confidence
intervals do not establish exchangeability. Never change alpha to obtain wins.
Old D076/D086 results remain immutable. New development, feasibility and final
evaluation evidence must remain separately named.
