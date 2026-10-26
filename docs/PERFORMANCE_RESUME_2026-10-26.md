# Performance continuation of the nine-project studies - 2026-10-26

The owner authorized fixing and resuming a long-running B13 job after a
nonblocking profile found 142/149 samples (95.3%) inside `_skip_risk`.
The old `decide` risk-target loop recomputed the risk over all remaining
candidates after each selected test: quadratic work on large suites.

The replacement binary-searches the shortest acceptable prefix in the
same order, calling the unchanged `_skip_risk` arithmetic at every probe.
It uses O(log n) full risk scans. Pins, changed tests, budgets, incomplete
orders, fallback reasons, risk thresholds, and returned report fields are
unchanged. This is a performance repair, not a new stopping method or a
change to the research success criteria.

Validation: 59 focused tests passed, including 480 randomized exact
whole-decision comparisons against the original forward scan, threshold
and adjacent-float cases, duplicates and incomplete orders, and a 10,000-test
bound on risk-scan count. A 4,000-test synthetic benchmark produced exactly
the same complete decision: 6.6218564 s original vs 0.0299045 s optimized
(221.43x in this benchmark, not a prediction of whole-study speedup).
The full Maven-inclusive suite is required before the continuation starts;
its exact result is in the continuation provenance and validation log.

Original folder `tuned-gate-confirmatory-2026-10-26` remains unchanged.
Seven completed project files are copied byte-for-byte into
`tuned-gate-confirmatory-perf-2026-10-26`; only unfinished work is evaluated.
`performance-resume-provenance.json` distinguishes original reused reports
from new reports and records both code fingerprints. All source files in
the original config are archived locally alongside their hashes.

The remaining B12f, B11 and B13f jobs are sequential, use separate `-perf-`
output folders and the original protocols and inputs. Read the B12f verdict
using the 7-of-9 rule from HANDOFF.md, not the novelty branch's old 3-project
rule. No positive research verdict is implied by this optimization.
No merge, push, or stash operation is part of this repair.
