# Performance engineering — D-083

The goal is lower analysis cost with the same safety policy. Accuracy and
latency are separate outcomes. D076 remains completed negative/mixed evidence.
No historical report, default target or acceptance gate is retuned here.

## What changes

1. Optional synchronous timing records cover Git, plugin graph/test work,
   parsing, history loading, model setup/training/calibration and fresh audit.
   Stage records contain calls, inclusive seconds and self seconds. Parent
   stages overlap their children; do not sum inclusive values. Unmeasured
   work remains in total time without being attributed to a guessed stage.
2. Each read-only job can opt in with `?profile=true`. The job record includes
   optional `metrics`; worker startup is separate from its core operation.
   Cancellation has no fabricated completed timing. Failed jobs may keep
   measured work without publishing a successful result. Ordinary requests
   keep their prior result schema.
3. MCP accepts `profile: true` for impact, plan and consented check. It adds
   `operation_timings` with `analysis_only` or `includes_test_execution` scope.
   Profiling never grants permission to execute project code.
4. Reuse immutable parses within an operation, keyed by blob and partitioned
   by repository/plugin identity. Exit, exception or another thread cannot
   carry that operation's cache into a later decision.
5. Reuse fitted model/calibrator copies only in explicit process-local scopes.
   Two-entry LRU and 300-second TTL limit retained entries. Complete dataset
   fingerprints include commit/order, labels, durations and feature values.
   Feature order, target and implementation identities also invalidate reuse.
   Models are never loaded from a disk cache. Audit evidence, eligibility,
   conformal threshold, selected sets and verdicts are always recomputed.
6. Audit row inference is batched; per-commit policy, order and validation
   remain unchanged. Parse/hash the same CSV bytes so provenance describes
   the actual data used even if the original file changes concurrently.
7. When policy already requires all tests, avoid history loading and fitting.
   Explain the mandatory suite without inventing a probability or suggesting
   more history will shorten a plan that policy already fixes.

The IDE shows collapsed timing details and exports allowlisted timing fields
alongside decision evidence. It drops unknown labels and fields. Existing
decision evidence still contains local paths/test names and must be reviewed
before sharing; timing records themselves do not include source or environment.

## Examples

Use the existing authenticated local job API, for example:

```text
POST /api/analysis-jobs/risk-select?profile=true
{ "repo": "C:/my/project", "base": "HEAD", "head": "WORKTREE" }
```

Poll its returned job ID using `GET /api/analysis-jobs/{id}`. Metrics appear
only when actually measured. Do not treat inclusive stage seconds as a
percentage-complete indicator or combine worker startup with overlapping work.

For a running repository-bound MCP server:

```json
{"name":"codedna_plan_tests","arguments":{"profile":true}}
```

The optional `profile` property does not expose `codedna_check` on a server
started without `--allow-build`.

## Measurements and practical limits

The inspected HikariCP dataset contains 20206 rows and 1427 commits. Its
SHA-256 is recorded in D083_FIT_PROFILE_2026-10-28.json and
D083_MATCHED_KERNEL_2026-10-28.json. A cold fit/calibrate/audit profile took
4.741 seconds, including 2.898 seconds in model setup/import. This motivated
measurement of cold and warm paths separately; nested stage times are inclusive.

Three interleaved trials per variant, with imports warmed equally, produced:

| Fit/calibrate/audit variant | Median seconds |
| --- | ---: |
| Original per-commit inference | 1.779 |
| Batched inference, fresh fit | 1.403 |
| Batched inference, fitted copies reused | 0.516 |

Raw trials are retained. A separate post-hoc check compared all 7495 audit
probabilities and all 357 per-commit decisions exactly, including selected/
skipped sets, estimates and evidence. See D083_AUDIT_EQUIVALENCE_2026-10-28.json.
This is one dataset/laptop, not independent confirmation. The benchmark excludes
CSV loading, Git, graph analysis, worker startup and project test execution.
The API deliberately creates an isolated process per job, so fitted-model reuse
does not survive separate jobs. A long-lived MCP server can reuse unchanged
fitted copies; even then it reruns the audit. No net CI speedup is established.

## Validation and release boundary

Focused tests cover fingerprint invalidation, TTL/bounds, defensive copies,
thread/exception isolation, fresh audit, current policy/eligibility, CSV race
provenance, unreadable history fallback, optional failed-job metrics and UI
redaction. Source 1a45664 passed 664 Maven-inclusive tests with zero skips;
TypeScript, 48 UI tests and three desktop runtime checks pass. The actual D083
frozen candidate passed 23 plugin/cancellation/restart/timing/brake checks,
including real Maven outcomes and fresh audit on model reuse. All 1458 manifest
files verified. See ENGINEERING_VALIDATION_D083_2026-10-28.json and
FROZEN_CORE_VALIDATION_D083_2026-10-28.json. The installed IDE, updated installer
and clean-PC acceptance are separate gates; D082's earlier proof stays intact.
