# D093 findings: controlled witnesses and live brake compatibility

Application source stayed fixed at a02d20f throughout evaluation. Its separate
full Maven/Gradle validation remains 780 passed, zero failures/skips. Ten offline
research-only tests passed in 7.56 seconds; they are not added to that count.

## Moonshot controlled benchmark

Pinned QuixBugs commit 4257f44b0ff1181dedaedee6a447e133219fcebf. All forty Java
programs were retained. Only corrected package declarations were normalized;
method bodies were unchanged and original/adapted hashes were recorded. This is
an educational benchmark, not a production-change effectiveness study.

Seven programs fit the existing source contract; thirty-three were unsupported.
Each mode used seed 7, at most sixteen inputs, four reductions, sixty seconds
whole-search budget and the existing shorter per-invocation limits. Mode order
alternated. Published triggering inputs were withheld until both automatic modes
finished for each program. No application changes or threshold tuning occurred.

| Outcome per mode | Guided | Simple |
|---|---:|---:|
| Reproducible difference | 2 | 2 |
| No difference observed within budget | 1 | 1 |
| Inconclusive | 4 | 4 |
| Unsupported at source selection | 33 | 33 |

All eighty planned records completed; fourteen searches actually ran. Four
exports were independently compiled and replayed successfully using the JDK.
Both modes found Levenshtein at ["a", "a"] and maximum-subarray sum at [-1, 1].
Separate published expectation checks confirmed a correction in both programs:
Levenshtein ("electron", "neutron") expects 3, and maximum-subarray sum
[4,-5,2,1,-1,3] expects 5. These separate checks are not automatic-search wins
and do not make every observed difference a proved regression.

BITCOUNT and FIND_FIRST_IN_SORTED hit invocation limits; GCD and POSSIBLE_CHANGE
retained exceptional executions and remained inconclusive. LIS had no observed
difference; this does not establish equivalence. Unsuccessful records were kept.
The search-trial wrapper time totaled 233.44 seconds, excluding separate oracle
checks; it is not production CI wall-time or a speedup measurement.

Positive result: existing Moonshot can reproduce two documented controlled
corrections without injected oracle inputs. Neither mode outperformed the other.
Do not pool this adapted single-seed benchmark with D086/D090 or claim independent
production superiority. Earlier unsupported and negative results remain intact.

## Live brake and CI source compatibility

On Oak build 3012, exact source discovery found 1972 default tests while the
published CI report contained 2363 classes. The sets differ in both directions.
No name/profile mappings were guessed. The actual CRC live recommendation had no
target history and returned unvalidated, retaining every discovered test.
This validates fallback behavior, not fitted-model accuracy or CI coverage.
The mismatch remains an obstacle to valid selective replay on this CI job.

The immutable public CI collector is now running locally every six hours. It
seeded already-inspected reports, found no new ones on its first fetch, and
preserves missing/failing evidence. It needs the laptop running and does not
restart after Windows restarts. See CI_EVIDENCE_COLLECTOR_D093.md for logs and
stop/restart instructions. Archiving alone does not solve source/profile mismatch
or guarantee enough continuous first-parent history for model evaluation.

## Next research requirement

Before estimating brake savings, establish an explicit, validated CI execution
profile/test identity mapping, or acquire a project whose source/default test
universe already matches its complete sequential reports. Then run the fixed
completion-aware protocol without tuning inspected outcomes. Keep Moonshot
witnesses separate from skip permission. No broad research claim or complete
roadmap milestone follows from this limited controlled result.

Evidence: experiments/quixbugs-d093.json; results under
experiments/results/quixbugs-controlled-d093-2026-10-29/; source-universe and
ci-archive D093 JSON files. No push, merge, installer or website changes.
