# D086: improve existing brake and witness methods

Status: implementation in progress, not a validated release. Owner authorized
the previous improvement ideas and clarified that the objective is better
measured performance of the existing features, rather than product expansion.
Website work and the D085 friend kit remain separate and unchanged.

## Work and acceptance criteria

1. Live shadow checking: retain the original recommendation, execute the full
   suite, identify observed failures outside it, retain missing/skipped/build
   outcomes and measure analysis/execution/whole-operation cost. Shadow results
   never authorize skipping and an uncommitted snapshot never becomes training
   history. Six new focused fixture checks passed; full validation pending.
2. Improve input allocation: prioritize changed boundaries instead of spending
   a small budget on unrelated unchanged constants. This is syntax guidance;
   no instrumented branch-coverage or feedback-directed-search claim is made.
   Further search/reduction changes require equal-budget comparisons.
3. Extend supported scenarios gradually, with explicit contracts, deterministic
   serialization, bounded execution and standalone reproduction. Preserve
   unsupported and inconclusive results. Do not infer purity from syntax.
4. Interpret differences only against an explicit applicable expectation.
   A JUnit draft must not silently use the base implementation as an oracle.
   Keep observed behavior separate from risk-based permission to skip tests.
5. Preserve all attempts when checking unstable outcomes. A later passing
   observation cannot erase an earlier failure. Fault-inject incomplete output,
   interruption and failed writes; uncertainty remains visible.
6. Freeze source, scenarios, seeds, budgets and outcome criteria before new
   comparisons. Existing synthetic cases are development data; never reclassify
   them as independent real-world evidence. Audit fresh real-change feasibility
   without selecting only changes with favorable observed results. Retain old
   studies and thresholds, including mixed/negative findings.

## Validation schedule

Use focused inexpensive regression checks while implementing each component.
After the complete implementation batch is stable, run one full Maven-inclusive
suite and then validate a newly built executable/installer. Do not repeat full
suites for documentation-only changes or unchanged source. A failure requires
repair and appropriate revalidation, not suppressing or relabelling the test.
Performance comparisons and real-project evaluations have separate questions
and run after their protocols and implementations are frozen. Report measured
analysis plus execution/audit costs; shadow full-suite duration alone cannot
establish counterfactual selected-run savings. No positive outcome is promised.

## Workspace

Git worktree: C:/Users/hp/OneDrive/Documents/ChatGPT/codedna/.worktrees/core-evidence
Branch: codex/core-evidence-improvements, based on merged PR #23.
Use the existing checkout's virtualenv with this worktree's backend and plugin
directories on PYTHONPATH. No new dependencies or independent implementation.


## Frozen implementation and actual feasibility outcome

Engineering source frozen at 0bdee655f2944283e3c61ef1106d26429e73d36c.
Explicit helper support is now implemented: at most three distinct repository-
relative Java sources, supplied on both immutable revisions, compiled without
processors/build scripts, exported and independently fingerprint-verified.
Its real Java reproduction/tamper check passed. Typed Unicode/string marker
reproduction checks passed after correcting an invalid test fixture.

The pinned 24-case real-change feasibility comparison completed all 48 mode/case
entries: each mode had five no-difference observations and 19 unsupported source
contracts. Zero witnesses; no real-change superiority or speedup established.
See experiments/results/moonshot-real-feasibility-d086-2026-10-29/FINDINGS.md.
Retain every case. This result is not a reason to retune thresholds or replace
cases after seeing outcomes. A broader research evaluation remains a distinct
protocol/data question, not a claim fulfilled by these engineering checks.

ONE final Maven-inclusive source suite is active, session 32868. Log:
C:/Users/hp/OneDrive/Documents/ChatGPT/codedna/.diagnostics/d086-full-maven.log.
Collected 755 tests. Do not start a duplicate. All source edits are frozen while
it runs. Documentation/helper preparation may proceed. An isolated D086 core
build helper explicitly requires 755 passed with zero failures/skips first.
Frozen plugin/jobs/brake/witness regression helpers and the three-new-evidence
helper are prepared in pointer .diagnostics, not yet executed. No D086 installer
or full-suite pass is claimed until evidence exists. D085 kit remains untouched.


## Source correction and executable validation completed

The full source run finished: 754 passed, one failed, zero skipped, one existing
warning, 2623.82 seconds. The failure occurred before JVM readiness: the cleanup
fixture's 12-second total setup budget expired during startup/compilation. Only
that fixture's timeout-case setup allowance changed to 60 seconds; production
limits and every frozen application hash stayed unchanged. Both actual timeout
and cancellation descendant checks then passed (26.43 seconds). Preserve the
failed full log; do not call this a clean single full-run pass. Evidence:
ENGINEERING_VALIDATION_D086_2026-10-29.json.

The isolated D086 core then built successfully. All 35 actual frozen checks
passed: seven plugin, eight lifecycle, eight real-Maven brake, nine original
witness, three new typed/helper/expectation/shadow evidence contracts. All 1463
bundle hashes verified. See FROZEN_CORE_VALIDATION_D086_2026-10-29.json.

ONE installer package operation is active, session 32398, log pointer
.diagnostics/d086-electron-package.log. It reuses the unchanged IDE frontend and
copies the new core into build/desktop-D086-2026-10-29/installer. Do not start a
duplicate or overwrite D085. NEXT: verify actual installer payload with prepared
verify_d086_installer_payload.py, restricted-PATH unpacked smoke, record final
proof and preserve the honest research limitations. New real-project brake
reliability/net-CI superiority is not established by these engineering fixtures.

## D086 engineering release candidate verified — 2026-10-29

Source frozen at 0bdee655f2944283e3c61ef1106d26429e73d36c. Full Maven-inclusive
run: 754 passed, one timeout cleanup fixture failed before readiness, zero skips,
one existing warning. Only fixture setup allowance changed; actual timeout and
cancellation descendant checks then both passed. All application hashes stayed
unchanged. Do not relabel this as a clean single 755-pass run.

All 35 actual frozen executable checks passed; all 1463 bundle hashes verified.
Separate D086 installer built. Its embedded core was extracted and all hashes
matched; restricted-PATH unpacked smoke passed without external Python and with
both bundled languages. No D086 GUI/full installation/clean-PC claim.
See ENGINEERING_VALIDATION_D086_2026-10-29.json,
FROZEN_CORE_VALIDATION_D086_2026-10-29.json and
RELEASE_VALIDATION_D086_2026-10-29.json for exact commands, hashes and limitations.

Installer: build/desktop-D086-2026-10-29/installer/CodeDNA IDE D086 0.1.0 Setup.exe
SHA-256: a8a000c926a7f7f89171a886550f27b998294efc6b86bd12e5d4377bd7bb669e
Bytes: 317727783. Signature: NotSigned.
D085 friend kit is unchanged. No push, merge or public publication performed.

Implemented method improvements: full-suite shadow evidence; bounded repeated
checks preserving every failure/incomplete outcome; measured check cost; edited
numeric-boundary priority; one/two int/boolean/bounded-String arguments; structured
input reduction; explicit small helper sources; expectation-backed JUnit drafts
and independently hash-checked reproduction. Risk thresholds/fallbacks unchanged.

Pinned real-change feasibility completed all 48 entries: each mode had five
no-difference results and 19 unsupported cases; zero witnesses. Preserve these
results. They do not demonstrate improved real-change detection, safety or speed.
Fresh-project brake reliability/net-CI superiority remains unestablished. More
research needs its own fixed protocol, not retuning this sample for positives.
