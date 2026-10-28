# D-076 observation-isolated development pilot

**Verdict:** implementation/mapping verification completed; no demonstrated
risk-gated reduction. This is one development prefix of previously inspected
HikariCP data, not independent confirmation or a deployment safety guarantee.

Protocol v2 was frozen in `1965665` before evaluation. Engine/source checkpoint:
`72e6043`; full input/code fingerprints are in [manifest.json](manifest.json).
All 360 source snapshots matched the reference test universe exactly. The
pilot uses 240 common full-suite warm-up commits and 120 evaluation commits,
with a scheduled full audit every tenth evaluation commit (12 per policy).
Ancestry-scoped earlier observations alone enter features and fitting.

| Policy | Reduced evaluation suites | Failing commits with no omission | Missed failing classes | Recorded evaluation test seconds | Recorded seconds including warm-up |
|---|---:|---:|---:|---:|---:|
| full | 0/120 | 3/3 | 0/4 | 1050.442 | 2068.276 |
| history | 0/120 | 3/3 | 0/4 | 1050.442 | 2068.276 |
| structural | 40/120 | 3/3 | 0/4 | 889.509 | 1907.343 |
| combined | 0/120 | 3/3 | 0/4 | 1050.442 | 2068.276 |

Only three evaluation commits failed, with four failing class outcomes. No
policy had a build escape. There was one first-recorded failing class outcome
and three recurring outcomes; none was missed. These tiny denominators do not
establish 95% future safety or superiority.

## Why the risk gate refused reduction

History and combined each refused all 108 ordinary evaluation decisions; the
other 12 were scheduled full-suite audits. In their first prior audit, the
candidate missed six of 60 audit commits and seven of 11 failing class outcomes
(failure recall 36.36%, all-commit miss-rate upper bound 18.19%). Subsequent
refusals also included fewer than ten failure-bearing audit commits. Keep
these refusal criteria; removing them merely to obtain savings is not a fix.

Both gated policies therefore observed complete outcomes at all 360 commits.
This real-data pilot does **not** demonstrate the performance of a selectively
learning risk policy under feedback starvation. The synthetic mutation tests
exercise that isolation; this pilot verifies mapping, accounting and refusal.
Structural-only had 40 partial observations, but its decisions do not train a
history model. Do not present that as validation of partial-feedback ML.

## Cost and runtime

Structural-only saved 160.933 recorded evaluation test seconds (15.32%) and
7.78% including the common warm-up. It reduced 40/120 suites. Risk-gated history
and combined saved no recorded test seconds. Audits replace the reduced run;
no additional repeated executions are simulated. These costs include selected,
mandatory and warm-up test classes exactly once.

Measured structural-analysis function time was 1164.203 seconds
over the 120 evaluation snapshots. This exceeds the recorded test seconds saved,
but baseline discovery overhead was not separately timed, so it is not a
matched net-slowdown estimate. Most mapping overlapped other local validation.
Startup, failed attempts and checkpoint I/O are excluded. No net CI speedup is
established. Measure matched cold/warm analysis before claiming a speed benefit
or scaling this pilot into a large run.

An initial extraction at reference index 329 exceeded its unchanged 90-second
deadline. The retry reused 329 verified mappings and completed. [STOP.json](STOP.json)
retains that initial diagnostic; [progress.json](progress.json) is the newer
completed state. No source, threshold, input, cohort or outcome-driven setting
was changed to complete the retry.

## Evidence and next engineering work

[summary.json](summary.json) recomputes trace counts and recorded durations from
the original reference truth and verifies mapping hashes/floors/audit timing.
[results.json](results.json) contains the four complete policy traces. Original
studies and inputs remain unchanged. No analysed project was built in this pilot.

The source passed 591 tests with Maven/Gradle included and zero skips. This
supports software correctness, not a new scientific safety claim. Next: measure
and improve analysis overhead, then implement bounded per-operation cancellation
and progress. Keep B10 as default and CRC opt-in. Broader risk-gated effectiveness
remains unestablished; do not tune this prefix until a positive result appears.

Verification method: run `python experiments/results/partial-feedback-pilot-d076-2026-10-27/verify_traces.py`
from the repository environment with the original pinned inputs available. The
checker verifies existing summaries without overwriting them or rerunning models.
