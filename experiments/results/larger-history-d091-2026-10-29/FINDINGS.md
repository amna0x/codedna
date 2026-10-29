# D091: four larger frozen-history cohorts

Application a02d20f, risk target 0.05, all original gates unchanged. Cohorts were
committed before interpreting labels: 6,726 selected heads, 1,348 evaluation
heads. ActiveMQ/D090 remains unchanged and is not pooled into these results.

| Project | Selected heads | Evaluation | Missing latest BASE history | Audit floor requires all | Source blocked | Recorded failing commits |
|---|---:|---:|---:|---:|---:|---:|
| Hadoop | 1,793 | 360 | 357 | 3 | 0 | 131 |
| Hive | 1,485 | 297 | 292 | 5 | 0 | 152 |
| Jackrabbit Oak | 1,448 | 291 | 287 | 4 | 0 | 132 |
| Kafka | 2,000 | 400 | 369 | 23 | 8 | 351 |
| Total | 6,726 | 1,348 | 1,305 | 35 | 8 | 766 |

All 1,348 evaluation outcomes were acquired and read; they contain 4,502
failing-class occurrences. These are recorded CI ground truth, not new builds
or failures predicted by a model. Raw failures were not filtered away.

## What the exact operational check found

The live brake requires history on the first-parent chain and outcomes at the
immediate BASE commit. Most CI rows are PR snapshots; many earlier snapshots
are sibling changes or are not the current BASE. A large number of project
builds does not establish usable operational history.

Only 35 targets have a recorded current BASE in the frozen outer history. Their
verified first-parent audit windows contain at most 18 commits. At 0.05, CRC
needs at least 19 FAILING audit commits even with zero misses. B10's zero-miss
Wilson bound also exceeds its target at these sample sizes. No fitted model
could authorize skipping using these verified inputs. The other 1,305 targets
fail freshness first; eight Kafka source identities cannot be verified.

Therefore 1,340 targets require full suites and eight are source-blocked. The
blocked targets are NOT successful test executions. Full-suite fallback has no
test-selection saving. Zero missed recorded tests on full-suite recommendations
would follow by construction; it would not measure predictive discrimination.
No new CI wall-time advantage or future-risk guarantee was established.

## Preliminary screens are not the final operational conclusion

The initial general-DAG necessary-gate screen made Jackrabbit's CRC counts look
numerically feasible. It intentionally left model decisions/outcomes pending.
The subsequent exact first-parent/latest-BASE check invalidates that apparent
feasibility. Both files are retained; operational-results files are authoritative
for the application setting. General ancestry is not a substitute for the live
first-parent contract. No model probabilities or structural features were invented.

## Limits and interpretation

This is a FROZEN-HISTORY eligibility replay, not a complete model/baseline or
prequential deployment study. Previous evaluation outcomes were not rolled into
later model history. A rolling deployment with newly completed BASE outcomes
could have different eligibility. Shallow ancestry and unavailable commits
remain unresolved; missing links are not proof that qualifying history could
never exist. These results do not show that large projects are intrinsically
unsuitable, or that the failure model itself is ineffective.

The selected PR snapshots/fixed-history setup does not demonstrate useful CI
savings under the current operational contract. A faithful follow-up needs
sequential main-branch CI records with outcomes available at each decision's
BASE, a prespecified prequential update rule, and independent evaluation data.
Do not retune on these now-inspected outcomes and call another run independent.

Structural/simple baseline executions, fitted-model discrimination, new project
builds and matched net-CI wall-time measurements were not performed. Gate proof
already rules out skipping on the verified frozen inputs; more fitting cannot
change that. Historical duration sums are not wall time.

## Execution and acquisition

Exact Git identities were fetched without blobs/build scripts, depth 256. Missing
public refs were retained: 123 selected Jackrabbit heads and 12 selected Kafka
heads were unavailable; only eight of these fall in the evaluation partitions.
Large revision lists were passed on stdin to avoid Windows command limits.

Compressed inventories were CRC/SHA256 verified with bounded ranges. The original
Kafka acquisition exhausted its 256 MiB budget due to coarse block overfetch;
its report was preserved. A smaller-block pass was stopped when exact gate proof
made remaining training acquisition unnecessary. A bounded concurrent range pass
then completed all 1,446 fixed Kafka evaluation inventory members with zero
acquisition errors. Other projects had all selected inventory members available.
Byte counts are attempt-specific; the interrupted attempt's total is not claimed.
Whole-archive checksums were not verified and no complete 3 GB ZIP was downloaded.

Application source did not change. Its existing full validation remains 780 passed,
zero failures/skips. Four research-only selection/ancestry/freshness/floor tests
passed in 0.25 seconds. No installer rebuild, website changes, push or merge.
