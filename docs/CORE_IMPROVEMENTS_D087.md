# D087: targeted support and measured brake performance

Status: development begun, no new positive-result claim. Preserve D086 source,
release artifacts, failed/corrected test logs and all feasibility results.

Source-only diagnosis of the 19 refused historical cases: eight integer-vararg
cases, four long-valued BinaryToDecimal cases, three private-method cases, one
int-to-long signature change, one renamed method, and two absent source files.
This dataset is now development data. Any new comparison using it must disclose
reuse and must not become independent confirmation or replace D086 outcomes.

Priorities: bounded long/integer-array transport, search and shrinking with
correct JVM numeric semantics; explicit method/path mapping where justified;
retain genuine added-method refusals; independently replay every export.
For the brake, preserve audit/threshold/required-test decisions and measure
complete operation cost before optimizing a specific bottleneck. Do not lower
thresholds or select favorable evaluation cases to satisfy requested positives.
Independent performance/accuracy claims require separately frozen real inputs.

Use focused inexpensive regressions during development. One stable-batch full
Maven-inclusive run and isolated executable validation follow implementation.
Website integration remains deferred. Do not overwrite D085/D086 installers.

## D087 numeric witnesses and repeat completeness — 2026-10-29

Supersedes the D086 in-progress status above: D086 validation and all 48
feasibility searches completed. See CORE_IMPROVEMENTS_D086.md and its evidence
JSONs. Each feasibility mode retained five no-difference and 19 unsupported
outcomes; none yielded a witness. Preserve these results unchanged.

D087 development adds signed Java long inputs/results and bounded integer
arrays/varargs (eight elements maximum), declared-type validation, width-aware
literal guidance, array shrinking that preserves method arity, and long-valued
standalone reproducer observations. Private methods, absent sources and ambiguous
renames remain unsupported; no automatic identity guesses were introduced.

Full-suite repeated brake checks now use the union of tests observed in all
attempts. A generated test disappearing from another attempt makes that attempt
incomplete, and the run cannot enter stable training history. Any observed failure
still blocks. Risk targets, audit requirements and skip authority are unchanged.
D087 is source development, not a new release or independent research result.

## D087 focused validation — 2026-10-29

Implemented bounded long/int-array witnesses and repeat test-inventory completeness
in the isolated core worktree. Focused check: 69 passed, 25 deselected, one existing
Starlette warning in 319.97 seconds. This is not the full Maven-inclusive suite.
Numeric suite with real JVM and standalone replay: 5 passed in 57.10 seconds.
An earlier numeric invocation had one incorrect test assertion comparing the
structured outcome object to an integer; corrected to inspect its value. The
actual overflow observation was correct. Initial numeric support also passed
three checks in 89.26 seconds. Preserve separate invocation counts; do not sum
these as unique tests or claim a full-suite pass. Graphify AST refreshed locally.
D087 release rebuild, full-suite validation and independent research remain pending.
No push or merge. D085/D086 installers unchanged. See CORE_IMPROVEMENTS_D087.md.
