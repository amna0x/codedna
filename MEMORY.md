# MEMORY.md: handoff notes for the next agent

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

## D086 engineering batch in progress — 2026-10-29

Continue on codex/core-evidence-improvements in the isolated core worktree.
Website changes and the validated D085 friend kit remain untouched. Implemented:
full-suite shadow observations, measured check cost, up to three bounded repeats
that preserve failures and reject unstable training evidence; edited-boundary
input priority; one/two int/boolean/bounded-String inputs; structured reduction;
caller-supplied expectations and JUnit drafts; up to three explicit helper source
files with independent hash-checked reproduction. Default risk thresholds,
full-suite fallback and required-test authority are unchanged.

Focused checks: brake component 28 passed (one existing warning), then one extra
unexpected-test-failure regression passed. Typed JVM replay, literal-marker and
helper-tamper checks passed individually. Full-batch tests and performance claims
remain pending. Preserve old studies. A pinned 24-case real-change feasibility
set has 5 narrow source-contract cases and 19 unsupported cases; no behavioral
outcomes have been observed yet. See CORE_IMPROVEMENTS_D086.md. Do not rerun old
studies or promise positive results. One full Maven-inclusive suite and an
isolated packaged validation follow the stable engineering batch.

## GitHub private-email push repair — 2026-10-28

Owner authorized repairing unpublished commit identities. Saved local-only backup
keep/private-email-backup-20261028-399d9c3; never push this private-email backup.
Rewrote the 35 commits after origin/main using the GitHub-verified amna0x account
ID and its ID-based noreply address, preserving every commit tree, message, name,
date and both stashes. Repository-local user.email now uses that noreply address;
global Git and GitHub privacy settings are unchanged. No push/merge performed.
Old source IDs inside hashed validation artifacts intentionally remain intact;
resolve them through docs/COMMIT_IDENTITY_REPAIR_2026-10-28.json. Artifact bytes
and source code did not change. Latest user website/cache commit is retained.
This notes/map commit is metadata documentation, not a new source validation run.


## D-085 source, pilot, executable and installer verified; friend kit prepared — 2026-10-28

Corrected source 4d359419ad68874c374a45d83732845327aeed41 passed the complete
Maven-inclusive suite: 714 passed, zero failures/skips, one existing warning,
2300.22s. See ENGINEERING_VALIDATION_D085_2026-10-28.json and hashed logs.
The earlier 711-test invocation on bd8c6d8 was deliberately interrupted around
12 percent for JDK17 Cp1252/UTF8 correction; never count it as a pass.

Implemented optional Java witness CLI and --moonshot --allow-build --repo MCP
capability. Self-contained public static int(int), bounded guided/simple inputs,
fresh JVM confirmation, reduction, independent JDK-only source reproducer,
explicit UTF-8 source/runtime assumptions, actual timeout/Ctrl+C descendant
cleanup. Unconfirmed cleanup blocks later witness/MCP checking, while planning
stays available. Base is not an oracle; no witness is not equivalence/skip-risk
validation. Existing test/risk policy remains intact. D084 demo /target/ ignore
also passed its Git regression and all four demo checks with real Maven.

The fixed engineering comparison COMPLETED all 48 searches; all 15 emitted
reproducers independently reproduced. Eight illustrative synthetic cases, three
seeds/mode, not independent projects/bugs. Guided: 12 difference, 3 no-difference,
6 inconclusive, 3 unsupported; simple: 3/12/6/3 respectively. Median whole-call
costs 11.234s guided / 10.057s simple: no speedup claim. Boundary cases were
constructed to favor guidance. See experiments/results/moonshot-engineering-pilot-d085-2026-10-28/FINDINGS.md
and MOONSHOT_ENGINEERING_PILOT_D085_2026-10-28.json. All report/export hashes checked.
Do not rerun/retune this pilot or old D076; no new accuracy/novelty confirmation.

The isolated D085 core build completed. All 32 actual executable checks pass:
seven plugin, eight worker/restart, eight real-Maven brake and nine witness checks.
All 1462 bundle files were hash-verified. See
FROZEN_CORE_VALIDATION_D085_2026-10-28.json and its hashed logs. Failed required
tests block, passing required tests pass, skipped required tests remain incomplete;
model reuse still performs a fresh audit. Optional witness reproduction, UTF-8,
timeout and parent-termination descendant cleanup pass in the actual executable.

D085 installer packaging completed. The actual embedded core was extracted;
all 1462 file hashes matched. Restricted-PATH unpacked smoke passed with no
external Python and both bundled languages. Three new packaged GUI checks pass:
isolated launch, Java/Python display and Language plugins restored on restart.
The unchanged D083 frontend was reused; its full 12-flow GUI test was not repeated.
Both owned D085 windows were closed. No app was installed.
See RELEASE_VALIDATION_D085_2026-10-28.json for hashes, logs and scope.

Installer: build/desktop-D085-2026-10-28/installer/CodeDNA IDE D085 0.1.0 Setup.exe
SHA-256: c0ad4d0fc2485b3b3763876c81d7a951bcee643980f06f9a0bdc67d53744ab0b
Unsigned, 317705578 bytes. Local friend kit prepared and hash/ZIP
verified: build/desktop-D085-2026-10-28/CodeDNA-D085-Friend-Kit.zip.
Includes a two-commit Java brake demo, optional witness demo and manual checklist.
Prepared is not sent/installed/clean-PC verified. D083 remains preserved.

NEXT: friend-PC/manual acceptance and official catalogue hosting remain external
release gates. Research performance follow-up remains protocol-first and not run;
the completed synthetic pilot does not replace independent real-change evidence.
No research claim was strengthened, no new language, rename, push or merge.

Stable D083 evidence is below. Preserve both stashes, unrelated website changes,
untracked MOONSHOT.md and all original research outputs. No new push/merge/public
hosting. Official catalogue was rechecked and still returns 404; read-only log
pointer .diagnostics/d085-live-catalogue.log. No additional language plugin.

## D-083 desktop candidate validated — 2026-10-28

Current stable source: 1a45664. Full Maven-inclusive suite 664/zero skips,
TypeScript, 48 UI tests and three runtime checks pass. Actual updated frozen
core: 23 checks pass; 1458 manifest files verified. Theia production compiled;
the isolated NSIS installer built after one retained failed packaging attempt.
Its actual embedded core was extracted and all 1458 hashes matched.
See RELEASE_VALIDATION_D083_2026-10-28.json and the source/frozen proof JSONs.

Actual packaged GUI checks passed: real measured timings, full-suite cold-history
fallback, Cancel kills both worker/child, recovery, test-check explanations and
source opening, build-consent cancellation, actual Maven six-check run reporting
the failed discount check, refusal to train from the uncommitted run, Java/Python
listed and Language plugins restored after restart. Only isolated owned app
profiles/fixtures were used; those app windows are now closed. Current installed
app is intact. Official catalogue 404, full clean-PC and other manual acceptance
remain open. No new language plugin was delivered; slow-probe is a test fixture.

Installer: build/desktop-D083-2026-10-28/installer-r2/CodeDNA IDE Setup 0.1.0.exe
317665899 bytes; SHA-256 c9386e51cda0730c5bed196450dfe22fa3e089283cb9267a1b9e686b4ae5b752.
It is unsigned. Do not claim it was installed or validated on a clean computer.
This stable source/candidate is ready for private review; no push/merge performed.

NEXT owner-authorized work: fix standalone demo target/ ignore (editor builds
otherwise pollute its snapshot), then implement/evaluate the focused Java Moonshot
pilot using MOONSHOT_PILOT_PROTOCOL.md. Research performance follow-up is planned,
not run; old studies and mixed findings stay intact. Preserve both stashes,
unrelated website changes and the untracked MOONSHOT.md. No public hosting.

## Current owner-approved work - D-082/D-083, 2026-10-28

User explicitly asked to test the rebuilt .exe's cancellation, plugin changes/
restarts and AI brake, then improve engineering/research performance. All 20
actual frozen checks passed in an isolated candidate: seven plugin checks,
seven worker/restart checks, six brake checks using real Maven. Worker and child
ended, unrelated fixture survived; failed tests block, passed tests pass and
skipped required tests remain incomplete. See FROZEN_CORE_VALIDATION_D082_2026-10-28.json.
The candidate is build/desktop-D082-2026-10-28/core/dist/codedna-core. All 1456
manifest files were verified. Installed app/old installer were not overwritten.
This is not clean-PC or actual new Theia acceptance. Prior full source: 636/zero
skips; Node43 and TypeScript pass. Don't repeat old studies or that completed run.

NEXT authorized D-083: measure real stage costs, safely reuse unchanged fitted
models/parses, improve fallback diagnostics and evaluate a pre-analysis cost
fast path. Never cache selected sets or accepted risk; revalidate eligibility
and audit every decision. A cost switch after analysis is already paid cannot
recover that sunk cost. Avoid serializing/loading Python models from disk.
Do not claim improved safety/recall from latency or engineering test results.
After changes: focused tests, full Maven-inclusive suite and updated frozen
candidate/release verification. A separate research performance follow-up must
be protocol-first, keep prior outputs intact and disclose reused data.

Owner also approved the FOCUSED Moonshot version: deterministic Java paired
execution, meaningful difference and small reproducer export, integrated with
existing core/brake. See MOONSHOT_SCOPE.md. It follows current engineering and
does not authorize the full twelve-month proposal, concurrency lab, automatic
repair or extra languages. Preserve untracked MOONSHOT.md; Java/Python only.
No new push/merge/public hosting; preserve both stashes. New performance work
must not be described as already present in the tested D082 candidate.

## Verified continuation - D-080/D-081, 2026-10-28

Source checkpoint 912f4c9 passed the complete Maven-inclusive suite: 636 tests,
zero failures/skips, one existing warning, 1086.89 seconds. TypeScript and
43 Node workflows pass. See ENGINEERING_VALIDATION_D080_D081_2026-10-28.json
and its hashed logs. D-079's earlier 601-test full proof remains separate.
Do not rerun either completed validation or any original research study.

Implemented: bounded read-only analysis jobs and real owned process-tree cancel;
stage/elapsed controls in Tests and Changes; immutable change/impact snapshots;
canonical file navigation with visible errors; relative API path preservation;
plugin activation pinned across worker and consented API restarts. Existing
B10/CRC defaults, thresholds, refusals and research findings remain unchanged.
The earlier 635-test invocation was deliberately interrupted to fix the new
relative-path regression and is not counted as a pass.

This is a source checkpoint, not a new installed desktop. Actual rebuilt frozen
execution, installer refresh, official catalogue hosting and clean-PC evidence
remain deferred to the final installation batch. Impact graph/replay/history
keep their existing sync UI; ordinary analysis has no restart resume. The D076
pilot is completed negative/mixed evidence, not a study to retune or resume.
No new push or merge; preserve stashes and the untracked MOONSHOT.md proposal.
Source is ready for private review; publication still requires owner instruction.

## Current checkpoint - D-080/D-081, 2026-10-28

D-079 is fully validated: 601 passed/zero skips, proof JSON saved. D-080 source
was saved in f4ec9cf. Its later 635-test full invocation was intentionally
stopped around 18 percent after a new regression exposed relative API paths
being resolved in the worker's trusted directory. That run is not a pass.
The regression failed before the fix; all eight API tests now pass. Anchor
repo/history/coverage/duration paths to the API context before dispatch while
preserving empty optional defaults and keeping workers out of analysed repos.

D-081 extends cancellation/progress to Changes and fixes snapshot consistency:
analyse once, then compute impact from that result's immutable base/head rather
than separately resnapshotting WORKTREE. Drop stale responses and duplicate
requests, bind source navigation to the canonical analysed repository, disclose
working-file/line differences and show file-open errors. Tests and Changes now
use job capability version 1; other views retain sync behavior. TypeScript and
43 Node workflows pass. Eight actual API checks pass; earlier integrated worker
suite 33 and later four cleanup checks passed. Full combined validation is next
(expected 636 tests), not yet a pass. Freeze code during it.

No installer rebuilt, new frozen binary validated, project code executed through
analysis, public hosting, source push, merge or stash operation. Installation
and clean-PC acceptance remain last. Existing B10/CRC decisions and research
findings are unchanged. MOONSHOT.md remains unrelated and untracked.

## Current engineering - D-080 integrated, 2026-10-28

D-079 full validation completed: 601 passed, zero skips, one existing warning,
1324.42 seconds. See ENGINEERING_VALIDATION_D079_2026-10-28.json. Do not rerun it.

D-080 source now mounts authenticated typed read-only analysis jobs: one active,
two queued, 300-second worker deadline, bounded in-memory results and owned
process-tree cancellation. Tests recommendation uses real stage/elapsed updates
and Cancel analysis when capability version 1 is advertised; older installed
cores retain synchronous behavior. Other views retain their existing sync UI.
No build, test execution, plugin mutation or history writing is routed through
the cancellation API. Risk defaults/thresholds/refusals remain unchanged.

Frozen worker dispatch and optional-plugin activation are pinned before work.
The IDE backend also retains activation across the consented API restart for
build execution, so pending plugin changes still require an application restart.
Source/frozen-entry contract tests passed; actual new packaged binary validation
and installer refresh remain deferred to the final installation batch.

Focused integrated Python suite: 33 passed; after cleanup review, four targeted
checks passed (including one additional case). TypeScript and all 35 Node
workflows pass. Full D-080 Maven-inclusive suite is the next validation; do not
call this release complete from focused checks. There should be 635 tests.
No new push/merge, research rerun, default changes, languages or stash operations.
MOONSHOT.md remains unrelated and untracked. Staged integration scripts have
already been applied; do not run them again.

## Engineering continuation - D-079/D-080, 2026-10-28

D-079 source is local commit a46f222. Its first full-suite invocation left an
empty log and no live pytest process; it is not a pass. One replacement run is
active: 601 collected tests, Maven included, verbose saved progress in pointer
.diagnostics/d079-full-suite-retry.log. Do not start a duplicate. The previous
591-test result still describes the earlier source checkpoint.

D-080 is in progress, not a completed release. New independent worker modules
support one active read-only operation, two queued requests, bounded retention,
owned Windows Job Object termination and deadlines. Sixteen focused process/job
checks pass, including actual descendants, unrelated-process survival, startup
cancellation and exact sync/worker JSON on temporary Git fixtures. IDE TypeScript
compilation and 32 Node workflows pass. The source UI is capability-gated; the
new routes and frozen-plugin bootstrap are staged for integration after D-079's
full validation. Do not claim they are mounted or present in the installed app.

Continue from ANALYSIS_JOB_PLAN.md. Staging helpers are in the pointer checkout's
.diagnostics; inspect before applying, as some helpers assert one-time changes.
The current API remains synchronous. Installation/hosting remain last. No push,
merge, research rerun, threshold changes or stash operations were performed.
MOONSHOT.md remains the owner's separate untracked proposal.

## Current engineering - D-079, 2026-10-28

D-076 is finished and committed in 27d9b43; do not resume or rerun it. Raw results,
360 source mappings, findings, summary and verifier are preserved. The report's
section 4.13 records no risk-gated reduction and only three failing evaluation
commits. Last validated source batch: 591 tests, zero skips; Node 27; viewer 8.

D-079 adds operation-local immutable Git validation reuse and fixes Java live
risk features using a newer WORKTREE than the selected snapshot. Seventy-two
focused risk/brake tests passed; ten final scope/snapshot checks passed. Three
real snapshots retain identical selection JSON with four fewer Git launches each.
Full new Maven-inclusive suite is running; do not claim it passed yet. See pointer
.diagnostics/d079-full-suite.log. No default/threshold changes or new dependencies.

Next is bounded per-operation cancellation/progress, not more models/languages.
Read ANALYSIS_JOB_PLAN.md, including frozen-plugin activation pinning across worker
restart. Installation remains last. MOONSHOT.md belongs to a separate proposal;
leave it untracked and do not implement it. No new push/merge; preserve stashes.


## Latest continuation - D-076 completed, 2026-10-27

The pilot completed all 360 mappings and four observed-only traces. Read
experiments/results/partial-feedback-pilot-d076-2026-10-27/FINDINGS.md and summary.json.
B10/history and combined refused all 108 ordinary evaluation decisions; no
risk-gated savings. Structural-only reduced 40 of 120 suites and missed 0 of 4 failing outcomes
across 3 failing commits; recorded savings were 15.32% in evaluation and 7.78%
including warm-up. This is tiny
development evidence, not proof of 95% safety or closed-loop ML effectiveness.
The one 90-second extraction timeout resumed from 329 cached mappings and completed
without input/source/threshold changes. STOP.json is a retained earlier diagnostic.
Full source validation: 591 Python tests/zero skips (Maven+Gradle), 27 Node tests,
TypeScript, 8 viewer checks. See ENGINEERING_VALIDATION_D076_D078_2026-10-27.json.
Next: measure matched cold/warm analysis and improve existing cache use, then
bounded analysis jobs/cancellation per ANALYSIS_JOB_PLAN.md. Do not rerun old
studies or tune this prefix for gains. Installation remains last; no new push/merge.


## Active checkpoint - D-076 / D-077, 2026-10-27

D-076 source is local commit 72e6043; protocol v2 is frozen in 1965665.
Fifteen focused tests pass. The source-mapping pilot stopped at reference index
329 on its 90-second extraction deadline; 329 valid plans are preserved and no
outcome evaluation occurred. See STOP.json under
experiments/results/partial-feedback-pilot-d076-2026-10-27. Let the full suite
finish, then retry only unfinished work once under the same limit. Do not
restart from scratch or change fingerprinted Python source during that retry.
Full suite with Maven/Gradle completed: 591 passed, zero failed/skipped,
4749.24s; one existing Starlette warning. See
docs/ENGINEERING_VALIDATION_D076_D078_2026-10-27.json. The one bounded pilot retry
is now running from the 329 preserved mappings; log d076-pilot-retry.log.
D-077 IDE source adds static check explanations, evidence-health guidance and
explicit JSON evidence save, excluding source/raw logs. TypeScript and 27 Node
tests pass (.diagnostics/d077-node-final.log). Live thresholds are unchanged.
D-078 adds scripts/Watch-PartialFeedback.ps1 (read-only stage bar; eight offline
checks passed). Per-operation IDE cancellation remains next; do not claim it is built.
Installation is deferred to the end. Owner wants to push for a friend to see;
notify when a validated checkpoint is ready, without assuming push/merge consent.
No new push/merge; preserve all old stashes. Read the newest notes first.


## Owner priorities - engineering follow-up, 2026-10-27

Owner explicitly authorized the proposed engineering improvements: explain test
purpose/source/selection/results; evidence health and provenance; progress,
cancellation and checkpoint recovery; diagnostics export; end-to-end project
workflow acceptance tests. Reuse existing implementations rather than duplicating
them. Finish the active D-076 bounded research check first. Installation, public
catalogue delivery and clean-PC testing are deferred to the very end by the
owner's latest instruction. More languages remain deferred. Source push is
separate from merge/release; no new push authorization has been given.


## Current continuation - D-075, 2026-10-27

D-074 plugin installation is complete: full suite 576 passed, zero skips;
19 IDE tests; seven actual frozen plugin checks; 1451 packaged hashes verified.
Installer and D074 friend kit are ready; source commits 70626d8/500c998 remain
local, no new push/merge, all stashes preserved. Do not rebuild this feature.
D-075 report corrections and read-only feasibility are complete. Read
docs/REPORT_REVISION_NOTES_D075.md and docs/PARTIAL_FEEDBACK_FEASIBILITY.md. Four older
datasets have structural evidence; the nine-project CSVs do not. Three HikariCP
code-only snapshots mapped exactly. No new selector study has run. Next is a
bounded protocol-first pilot; reused data is not independent confirmation.
The owner's technical reviewer is ChatGPT and labels were cross-checked with
Gemini; do not keep asking for human labels or claim independent validation.


## Current override - D-074 completed, 2026-10-27

The frozen desktop plugin-installation fix is complete and validated. Read
docs/DESKTOP_PLUGIN_INSTALLATION.md and docs/RELEASE_VALIDATION_D074_2026-10-27.json.
All final tests, bundled hashes and the new installer/friend kit are recorded
there. Earlier notes calling this feature unimplemented are superseded.
Source checkpoint 70626d8; no new push/merge; preserve stashes and old studies.
Next authorized work: correct the report and assess feasibility of a bounded
partial-feedback/structural-floor follow-up. The latest review makes that study
conditional on a stronger claim. Public hosting and real clean-PC feedback are
separate; do not repeat the completed plugin implementation.


## Active work - D-074 frozen plugin installation, 2026-10-27

Owner explicitly asks to finish this fix first; do not start research, hosting
or language work yet. Source is on codex/blueprint-completion, after 1b95d85.
New desktop_store.py implements offline wheel staging, dependency/tag/RECORD
checks, isolated child factory validation, atomic per-user activation and
restart loading/removal. Registry preserves a bundled fallback after a damaged
optional override. PyPA installer 0.7.0 was installed only in the build venv and
declared with packaging in desktop/dev extras. Source pip behavior is retained.
30 manager/install tests, 8 build tests, 18 IDE tests and final 22 focused
registry/store tests passed. Final frozen rebuild and all seven executable smoke checks passed; 1,451 hashes
match. Final Maven suite and NSIS installer build/verification remain running. See DESKTOP_PLUGIN_INSTALLATION.
No new push/merge; all stashes preserved. User's Gemini label cross-check is a
second AI review. ChatGPT is the user's technical reviewer; review attachment
efca63b5-725e-4ccb-9907-4b1e6353773d/Pasted text.txt requires later partial-feedback
protocol/replay and structural ablation. Only discuss that agenda for now.


## Active checkpoint - D-072/D-073, 2026-10-27

Continue on codex/blueprint-completion; preserve all stashes. D-071 is local
commit 8b0d478. The branch contains the reviewed D-072/D-073 source checkpoint; inspect git log for its commit. Full Maven suite
563 passed, zero skipped; latest TypeScript compile and 18 IDE tests passed.
Risk thresholds/fallbacks unchanged. Individual recorded checks, clear history
selection and replay folder browsing fix the owner's demo feedback. See
docs/BLUEPRINT_COMPLETION.md for exact validation and remaining external gates.
Final D-072/D-073 installer and friend test kit are built and verified;
see docs/RELEASE_VALIDATION_D072_D073_2026-10-27.json. Clean-PC acceptance remains pending. Website source and detailed blueprint are ready locally;
public catalogue/wheel hosting remains unavailable. No new push/merge yet.


## Current continuation - 2026-10-27 (supersedes older status)

PR #22 merged as 45821b4 after owner authorization and green checks. D-068 and
D-070 are already on main. The studies are finished; preserve their reports.
Work now continues on codex/blueprint-completion. Read
[the current completion ledger](docs/BLUEPRINT_COMPLETION.md) for remaining work
and validation, and [the deferred backlog](docs/DEFERRED_FEATURES.md). The owner
asked to save extra proposals for later, not implement them now. Preserve all
stashes. Publication/merge-pending notes below are historical, not current.


Read this first, then AGENTS.md (rules), docs/ROADMAP.md (status) and
docs/DECISIONS.md (decision history and tradeoffs).
Last updated: 2026-10-26 (completed studies and PR #21 integration review).

## Current verified state - 2026-10-26

PR #21 merged to main as 8183d2d139b3b64b83cfd0456a632ef2ee6f36c2.
All seven integration CI checks and all seven merged-main CI checks passed.
Full local Maven-inclusive suite: 533 passed, zero skipped before merge
(961.26s) and after pull (833.36s); one existing Starlette warning. Complete
IDE rebuild passed and start.bat reached a ready workbench. Extension
compile and 3 runtime + 8 workflow Node tests passed. Installer/clean-PC
acceptance remains separate. #8 was already closed. #15/#16/#20 are marked
merged; stacked #17/#18/#19 remain open against their old base branches,
although all six PR heads are ancestors of main. Do not create extra merges.

All four nine-project follow-ups are complete and published under
`experiments/results/*confirmatory-perf-2026-10-26/`; 125 artifact hashes
verified. B12f reaches 95% safety on 8/9 but decreases mean safety against
the gated product; missing pre-run nine-project addendum is disclosed.
B10 remains default, CRC opt-in. B13/B13f exploratory; PTS cost match failed.
See report 4.11/4.12 and D-067/D-069. Never rerun these completed studies
or overwrite original reports to change their machine verdicts.

Current build branch: codex/brake-structural-python (D-070), adds the
structural_plan union and explicit Python/mixed full-suite fallback with
neutral execution dispatch. Implementation and focused tests are done;
full branch suite passed 554 tests with zero skips, Maven included (1953.04s). The branch was not pushed: automatic approval review requires explicit owner approval to publish its private source/tests/docs/Graphify outputs. No feature CI or review PR exists yet. Prepare the PR after that approval; do not merge it without separate authorization.
Do not rebuild the CRC opt-in/end-to-end demo; they already exist (D-068).
No authorization to merge the new feature PR is implied by permission for #21.

All stashes are preserved: never pop, apply or drop them. Old local main
ca7fac6/97c3be7 is preserved by keep/local-main-before-pr21-20261026 and
keep/graphify-97c3be7. Original local confirmation files are backed up at
C:/Users/hp/codedna-backup-2026-10-26/original-confirmatory-before-pr21
with 45 file hashes verified. Do not restore old buggy edits into main.
Historical notes and validation counts below describe older checkouts.

Branch `claude/project-thread-info38` (PR #17, stacked on #16): full suite
`python -m pytest --run-maven` on Linux: 388 passed, 7 skipped (Windows-only
start.bat tests, run by Windows CI), 2026-10-25. The counts below (334, 322,
315 ...) were reported by Codex on the laptop's older uncommitted tree; they
were not reproduced on this branch. Codex's first project-history draft
dropped failing runs, kept a second history and edited .git/info/exclude;
D-057 replaced it, so do not port those parts back from the laptop.

2026-10-26: Codex's later laptop work is ported as D-065 (Windows-safe Git
ancestry for big RTPTorrent pushes; the old run failed at Sling with WinError
206) and D-066 (IDE opens discovered test files, ignores stale responses).
The live confirmatory run now uses
`experiments/datasets/confirmatory-windowsfix-2026-10-26`, results to
`experiments/results/rolling-evidence-confirmatory-windowsfix-2026-10-26`;
the old `confirmatory-live-2026-10-25` status says failed and is superseded.

Codex's laptop notes (2026-10-25):
Latest full validation: **334 passed, zero skipped**, Maven and Gradle included;
897.94 seconds, one existing Starlette/httpx deprecation warning. Three Node
runtime tests also passed. No commits or pushes were requested/performed.

## Historical next step (superseded) — fresh-project continuation was queued

- The installer remains at `ide/electron-app/dist/CodeDNA IDE Setup 0.1.0.exe`
  (339,622,119 bytes, SHA-256
  `88d486030d66a450edd1763df68f611aaa8806104a9ec92dd6fabc6f96140f93`, unsigned).
  Exact packaged-core checks passed without external Python: Java analysis,
  synthetic model/calibration, API, risk fallback, real Maven passing tests and
  a deliberate regression with exactly one requested failing class executed.
  All 1,354 core file hashes matched. Pinned editor VSIXs matched 577 shipped
  files; one TypeScript declaration is deliberately removed by the packager.
- D-056: `prepare_confirmatory --no-structural` avoids three unused graph
  columns while preserving all 15 live model inputs. Verified row by row on
  all 70,485 existing four-project rows. Preparation guards project identity,
  inspected-project exclusion, output-name collisions, extractor/profile drift.
- An earlier `prepare_confirmatory.py` producer was already running for all
  nine fresh projects under `experiments/datasets/confirmatory/raw` (base
  Python PID 17936, launcher 19284 when inspected). Preserve that producer.
  It had verified 41/74 entries, about 2.5 GB, and was downloading the next
  repository pack. Zenodo transfers are slow. The duplicate fetch started in
  this session was stopped after two raw result CSVs; it produced no new DBs
  or feature CSVs. Its old config is preserved as
  `preparation-duplicate-fetch-stopped.json` in the separate live-output folder.
- `scripts/continue_confirmatory.py --wait` is now running as a ONE-TIME local
  continuation (PID 17704 when queued; exec session 74625). No AI service,
  notifications, recurring scheduler, duplicate HTTP download or third-party
  build is used. It waits for all 74 entries including the last shared map,
  rechecks every SHA-256, reuses raw files read-only through `raw_dir`, builds
  all nine DBs and 16-column feature CSVs in the separate live-output folder,
  then runs the unchanged fixed D-042 rolling study. No fresh verdict exists yet.
- Status: `experiments/datasets/confirmatory-live-2026-10-25/continuation-status.json`.
  Log: `build/confirmatory-continuation.log`. Expected final results:
  `experiments/results/rolling-evidence-confirmatory-2026-10-25/summary.md`.
  The source download must finish; if it stops, resume that producer first.
- IMPORTANT: `continuation-code.json` freezes relevant preparation/model/code,
  the fixed protocol, Python/ML-library versions and equivalence proof. Changing
  those files/versions before fitting causes a safe failure and requires a new
  output folder; do not silently alter the queued study. The OS output lock is
  released automatically on exit. Do not start a duplicate worker or downloader.
- Details: `docs/CONFIRMATORY_PREPARATION_2026-10-25.md` and implementation handoff.
  Latest full suite: 334 passed / 0 skipped / 897.94 s. New preparation/continuation
  tests: 15 passed. Final Graphify AST refresh: 2,138 nodes, 5,373 edges,
  123 communities; no document semantic extraction.
- Interactive editor/progress acceptance and clean-machine installer testing
  remain unverified. Computer Use recovery returned minimized-window / user
  input detected errors; do not claim UI click-through passed. Final report,
  manual graph-precision review and supervisor sign-off remain roadmap work.

## Initial review batch — 2026-10-25

- Started from clean HEAD `97c3be7`, with the newer graph, replay, WORKTREE,
  multi-module, launcher and website changes already merged. Earlier notes
  describing those features as remaining or remote authentication as broken
  are historical; use the roadmap for current scope.
- Replay readers now reject malformed/non-finite/impossible outcomes with
  ReplayError (API 400); discovery skips invalid files. Saved study results
  are not edited. Added 15 offline regression cases; replay suite: 32 passed.
- `npm run build:extension` passed. Full Maven-inclusive suite: 315 passed, 1 skipped (missing Gradle at collection),
  1 existing Starlette/httpx warning, 690.91 seconds. The skipped Gradle test
  subsequently passed after installing its runtime, covering all 316 tests.
- Graphify refreshed locally with AST-only extraction: 2,063 nodes, 5,201 edges,
  120 communities. Documents were not semantically re-extracted.
- Installed portable Gradle 8.14.3 from the official distribution, verified
  SHA-256 `bd71102213493060956ec229d946beee57158dbd89d0e62b91bca0fa2c5f3531`.
  Runtime metadata: `C:/Users/hp/.codex/tools/gradle/runtime.json`.
  Add `C:/Users/hp/.codex/tools/gradle/gradle-8.14.3/bin` to the process PATH
  for future full runs; set GRADLE_USER_HOME to its sibling `cache` folder.
  The previously skipped Gradle multi-project integration test passed separately
  in 193.76 seconds (all tests, selected tests, build-excluded test reporting).
- No commit or push requested or performed in this review.

## Desktop continuation — 2026-10-25

- Owner requested continued autonomous work while AFK, with careful validation;
  additional languages remain deferred. No commit or push was requested.
- Completed D-055 bundled Windows core, verified a full NSIS build and preserved
  explicit executable overrides. New build-only extra: `.[desktop]` pins
  PyInstaller 6.22.0. See `docs/IMPLEMENTATION_HANDOFF.md` for details.
- The final installer is `ide/electron-app/dist/CodeDNA IDE Setup 0.1.0.exe`,
  339,622,119 bytes, SHA-256
  `88d486030d66a450edd1763df68f611aaa8806104a9ec92dd6fabc6f96140f93` (unsigned).
  Packaged-core hashes verified: 1,354 files. Local evidence: `dist/validation.json`.
- Frozen core and the exact packaged copy passed Java analysis, synthetic
  model/calibration fitting, API graph, risk fallback and actual sample Maven
  execution without Python on child PATH. Proof under `build/desktop-core/`.
- Packaged app reached the ready workbench and deployed two Java extensions.
  Interactive UI acceptance remains unverified: repeated minimized-window and
  user-input-detected errors persisted through Computer Use recovery. Do not
  claim Java completion, progress controls or clean-machine installation passed.
- Launcher now loads portable Gradle metadata/cache and preserves custom cache
  paths; six launcher tests passed. Metadata reads avoid quoting user paths into
  PowerShell source. The no-JDK/no-completion warning was corrected.
- Full suite after the desktop helpers: 320 passed, zero skipped, one existing
  Starlette/httpx warning, 4960.82 seconds. Final validation after the launcher
  changes: 322 passed, zero skipped, 814.16 seconds, one existing warning.
  OMP/OPENBLAS/MKL thread counts were set to 1 for the final run.
- Graphify code refresh before the final launcher additions: 2,099 nodes,
  5,264 edges, 126 communities. Final refresh including launcher tests:
  2,102 nodes, 5,270 edges, 129 communities (AST only).
- The obsolete IDE-only packaging attempt and broad scientific test-suite
  freezing attempt were stopped, not completed. The later bundled installer
  build and exact packaged-core smoke checks are the valid results.

## What the project is

CodeDNA is a university Final Year Project (software engineering only, no
security scope). It analyses Java code changes, estimates their impact,
selects and orders regression tests, and estimates the risk of skipping the
rest. Research track (Python core + experiments) has priority over the
product track (Theia IDE in `ide/`, later a website and plugin catalogue).
Deadline: approximately May or June (presumed 2027 from the current October 2026 date), with the owner preferring to finish sooner. November 2026 is not the deadline.

## How the owner works

- The owner has a limited budget for paid AI and wants quicker, concrete progress.
  Work in focused implementation batches, reuse existing code and saved results,
  avoid redundant research or checks, and leave concise handoff notes so future
  sessions can continue without redoing work. Multi-language support remains a
  desired product goal, but the owner now explicitly defers it until the Java
  software workflow is complete. Do not promise dates without estimating work.

- Commit and push **only when the user asks**. After every push, check CI
  (`gh run list` / `gh run watch <id>`) and report the job results.
- Git identity is repo-local: mohibk0004-del. Remote: github.com/mohibk0004-del/codedna (private).
  Commit messages end with a `Co-Authored-By:` line for the AI model used.
- Never fabricate numbers. Every result must come from files under
  `experiments/results/`. Report negative results honestly.
- The owner explicitly requests Maven coverage in full local validation.
  Run `python -m pytest --run-maven`; see the current review/desktop continuation
  for the latest local results. Real Maven/JaCoCo and Gradle integration are
  included when their runtimes are on PATH.
- Update FINDINGS / DECISIONS / ROADMAP / report draft when results change.
- `docs/PROGRESS_REPORT.md` and `.pdf` are a plain-language report the user
  forwards. They are **local only** (listed in `.git/info/exclude`); keep
  them in sync with findings but never commit them.

## Environment (Windows 11)

- Python 3.12 venv at `.venv` (`.venv/Scripts/python`). Install:
  `pip install -e ".[ml,api,dev]"`, then the Java plugin:
  `pip install -e plugins/codedna-java` (D-054; start.bat does it if missing).
  Java code (parser, graph builder, discovery, Maven runner, live risk) now
  lives in `plugins/codedna-java/codedna_java/`; the core reaches it only via
  `codedna.plugins.languages`.
- Python plugin: `pip install -e plugins/codedna-python` (D-060; start.bat
  installs it too). Stdlib `ast` only. Mixed Java + Python repos: the core
  runs every installed plugin (`plugins.languages`: `commit_graph`,
  `commit_tests`, `run_tests`); no cross-language edges. The PyInstaller
  desktop bundle must include `codedna_python` as well as `codedna_java`.
- Set `PYTHONIOENCODING=utf-8` when scripts print "−" or "Δ".
- In Git Bash, heredocs containing apostrophes sometimes fail ("unexpected
  EOF"); write a Python script to a file and run it instead.
- tree-sitter is pinned `>=0.25,<0.26` in `plugins/codedna-java/pyproject.toml`:
  0.26.0 crashes (D-033).
- IDE builds need `env -u NODE_USE_SYSTEM_CA` (certificate issue).
- Markdown to PDF: render HTML with the `markdown` package, then
  `chrome.exe --headless=new --no-pdf-header-footer --print-to-pdf=...`.

## Data

- RTPTorrent v1.1 selective four-project subset in `experiments/datasets/raw/`
  (git-ignored). The full 5 GB archive and other seven projects are not restored.
- Per-project history DBs in `experiments/datasets/derived/*.db`
  (git-ignored), built with `codedna history import-rtptorrent`.
- Study folder: `experiments/results/study11-2026-10-21/` holds per-project
  `dataset.csv` (git-ignored, slow to rebuild: up to 2 h per project),
  `evaluate-seed*.json`, `experiment-seed*.json`, `class-weight-seed*.json`,
  `summary.md/json`, `class-weight-summary.md/json`, `FINDINGS.md`.
- Projects: graylog2-server, jooq, jcabi-github, optiq, achilles, hikaricp,
  littleproxy, jade4j, jsprit, wicket-bootstrap, dynjs. graylog2-server and
  jOOQ have no failing test commits (CI recording gaps), so recall/safety
  pool over 9 projects.

## Key commands

```bash
python -m pytest
python scripts/run_study.py --out experiments/results/study11-2026-10-21 --seeds 0 1 2 3 4 --workers 6 name=experiments/datasets/derived/name.db ...
python scripts/class_weight_check.py --out experiments/results/study11-2026-10-21 --seeds 0 1 2 3 4 --workers 6 graylog2-server jooq ...
```

`run_study.py` reuses `dataset.csv` and skips report files that exist;
delete `experiment-seed*.json` to rerun experiments. Rerunning reproduces
earlier numbers exactly (fixed seeds, chronological split).

## Results so far (study11, 11 projects x 5 seeds)

- RQ1: features predict failures above chance (pooled PR-AUC 0.138), mostly
  via history; ML ordering does **not** beat simple rules (APFDc: recent
  failures 0.76, shortest 0.74, random 0.65, LR 0.64, GB 0.58).
- RQ2: B8 needs ~60 % of test time for 90 % recall, ~82 % for 0.91 safety.
- RQ3: calibrating the class-weighted model cuts ECE 0.118 to 0.021, but an
  unweighted model is already at 0.030 (D-037), so the ECE drop mostly
  undoes class weighting. However, B10 with the unweighted *raw* model
  stops too early (target held on 6 of 9 projects); calibrated, 8 of 9.
  Calibration matters for decisions, not for the ECE number.
- RQ4: fallback (B9/B9r/B9n) gives no reliable gain at the same test time.
  Hybrid B10 (rules order + calibrated stopping at 5 % risk, D-036) is never
  less safe than rules at the same time and meets its target on 10 of 11
  projects; pooled gain +0.075 [-0.001, 0.202], not significant.
- RQ5: dependency graph helps on jsprit/HikariCP/optiq, blind on
  jcabi-github/wicket-bootstrap.
- Thesis claim: calibrated, checked risk estimates used as a stopping rule
  on a simple ordering, evaluated at equal test time. Not "ML beats rules";
  calibration's value is in the decision, not in the ECE drop.

## GitHub retry and research next steps (2026-10-24)

Remote read/API access now succeeds. Claude's original PR #1 is open at
https://github.com/mohibk0004-del/codedna/pull/1, head c9d81829d28ea6939dfa5238a23cf3b9a1446fd4;
all seven remote CI checks succeeded for that branch. It was fetched into
`origin/claude/dante-b10-stopping` without checkout or local overwrites.
The newer local implementation remains uncommitted/unpushed; reconcile both
before publication. No merge or PR modification was made in this retry.
See `docs/CLAUDE_PR_REVIEW.md`. Earlier auth-block notes below describe the
historical failure, not the current access status.

Observed same-cost adapted-order stopping safety gains: zero on three projects,
+0.1839 on wicket-bootstrap. Pooled +0.0460 [-0.0500, 0.2806] remains uncertain.
More seeds cannot replace independent projects/failure evidence. Predefine new
evaluation before collecting/testing; never tune until a desired positive result.
C++ Build Tools 17.14.42 and Windows SDK 26100 are installed and resolved.

## Current implementation handoff (2026-10-24)

Read `docs/IMPLEMENTATION_HANDOFF.md` and `docs/JAVA_WORKFLOW.md`. D-040/D-041
complete the interrupted research/risk/selected-execution slice. The final
`dante-history-check-2026-10-24` study has 20 runs and verified controls/hashes:
all four calibrated observed targets hold; matched-time safety +0.0460
[-0.0500, 0.2806] is not significant. It is a history-only adaptation of author
score structure, not full DANTE reproduction. Initial Markov-proxy results and
source snapshots remain in `dante-check-2026-10-24` for transparency.

Live risk uses a separate 15-feature 50/25/25 model/calibration/audit. Core gate
requires sufficient failing audit commits, >=90% recall and a miss-rate upper
bound <= target; Java-specific features are in the Java plugin. Unknown/stale,
future/unrelated or incomplete data yield risk-unvalidated/full-suite selection.
No formal guarantee or universal pretrained transfer is enabled.

IDE now shows risk/audit evidence and executes recommended classes only after
explicit consent. Full native `npm run build` passed after installing signature-
verified Microsoft Build Tools 17.14.42 / Windows SDK 26100 and rebuilding the
host FFmpeg addon. Live demo verified a passing run and two real failures after
a deliberate regression. Final suite: 245 passed, zero skipped, 499.39 seconds.
See the study's `validation.json`. The app is open on a disposable TEMP demo.

GitHub rejected the saved credentials; Claude's remote branch was inaccessible.
No source commit, push or PR was made. Code/graph/doc changes remain local,
alongside prior uncommitted work. Do not claim remote CI or supervisor approval.
Next original scope: graph view, Java editor support, progress, packaging and
report review. Multi-language work is deferred by the owner.

## Earlier research context / next

0. Owner requested a cross-project transfer test on 2026-10-24 (D-039).
   Pre-selected HikariCP, LittleProxy, jade4j and wicket-bootstrap; five seeds,
   all twelve source-target directions plus four within-project controls.
   Completed all 80 raw runs. Source calibration is usable in 9/12 transfer
   directions; 7/9 meet observed 5% miss, and three lack calibration. General
   transfer is not established: HikariCP to LittleProxy misses all failures;
   LittleProxy to wicket-bootstrap has 16.46% observed miss; Wicket transfers
   run almost everything. See `experiments/results/cross-project-2026-10-24/FINDINGS.md`
   and `docs/CROSS_PROJECT_PROTOCOL.md`. Keep target validation central; no
   runtime/IDE defaults changed. Future target adaptation needs a separate,
   pre-specified study, not tuning on these target test results.

1. Done 2026-10-24: B10 needs calibration (see RQ3 above).
   `graphify-out/` is the local navigation graph. Existing graph artifacts
   are tracked in this checkout; generated updates remain uncommitted.
2. Saved-study figures now have a reproducible exporter (D-038):
   `python scripts/make_study_figures.py --study experiments/results/study11-2026-10-21`.
   Five PNG/SVG figures, exact values and SHA-256 provenance are under the
   study's `figures/`. Existing result reports are unchanged. Finish and review
   `docs/REPORT_DRAFT.md`; user to check the claim with the supervisor.
3. Rest of the report.
4. Risk display and selected execution are now implemented and live-checked
   (D-041). Remaining demo work includes graph view and packaging/installers;
   website and additional languages remain later scope.
5. Optional: Defects4J check, manual graph-precision check.


## Local Graphify tooling (2026-10-24)

The owner requested local Graphify (`graphifyy` from PyPI) throughout this
project. Version 0.9.95 is installed in an isolated tool environment at
`C:/Users/hp/.codex/tools/graphify/`; the Codex skill and references are at
`C:/Users/hp/.codex/skills/graphify/`. Use the full executable path from
`AGENTS.md` when it is not on PATH. Consult the local graph before codebase
searches, verify findings against current source, and refresh after code edits.
The local graph was updated with AST-only extraction, excluding generated
`experiments/results/**`; no semantic document extraction was performed by
this setup. The local tool does not require a Graphify Cloud workspace.


## Current checkout environment

This checkout is `C:/Users/hp/OneDrive/Documents/GitHub/codedna`.
The older Codex workspace at `Documents/ChatGPT/codedna` only points here.
The Python 3.12 `.venv` has been restored with `.[dev]` and Matplotlib;
future figure setup can use `pip install -e ".[dev,plots]"`.
Validation: `.venv/Scripts/python -m pytest --run-maven -q` passed all 245
tests with zero skipped; the existing Starlette/httpx deprecation warning
remains. All 12 exported artifacts reproduced byte-for-byte, and
112 input report hashes were checked.
A verified RTPTorrent raw subset for HikariCP, LittleProxy, jade4j and
wicket-bootstrap is present. All four history databases and feature CSVs are
rebuilt and verified against original study digests: 20,206 / 4,575 / 10,913 /
34,791 rows. Recovery completed; no preparation writer remains active.
`experiments/datasets/derived/transfer-preparation.json` records completion;
a shareable snapshot is in the transfer study's `data-recovery.json`. Other
seven projects' raw/derived data are still absent. All 112 original saved
figure-input report hashes still match. The transfer study contains 80 raw
reports, of which 65 have calibrated results (45 cross-project, 20 controls).


## Portable Java/Maven runtime

JDK 17.0.20+8 and Maven 3.10.0 are checksum-verified under
`C:/Users/hp/.codex/tools/`. Their exact paths/checksums are in
`C:/Users/hp/.codex/tools/java-maven.json`. No system-wide PATH was changed.
For full local tests, load this JSON in PowerShell, set `JAVA_HOME` to its
`java_home`, prepend `java_home/bin`, `maven_home/bin` and the bundled Git
`C:/Users/hp/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd`
to PATH, and run `.venv/Scripts/python -m pytest --run-maven -q`.
The local Maven cache is `C:/Users/hp/.codex/tools/maven-repository`, selected
with `MAVEN_OPTS=-Dmaven.repo.local=C:/Users/hp/.codex/tools/maven-repository`.
The passing integration test checks per-test JaCoCo mapping and verifies that
the expected failing tests are caught after intentionally injecting a regression.


## Owner scope update - 2026-10-27

The owner declines independent student graph labelling. Do not keep requesting
it or treat it as an active owner task. Existing labels remain AI-generated;
no independent validation or human precision result is claimed. Supervisor
review is deferred until the owner supplies their next message. The pasted
supervisor-style assessment is preliminary and has not reviewed the five files.
Catalogue hosting and frozen optional-plugin installation remain genuine
distribution work, separate from the bundled Java/Python functionality.


## Website design merge - 2026-10-28

The owner approved merging UNIVERSAL-WEBSITE-DESIGN.md into the existing
website. The four static pages share the new poster/typography/palette system;
site.js adds accessible navigation, filters and optional reveals. Existing
plugins.js, catalogue/index.json and original catalogue tests are byte-identical.
Original eight files are preserved in the checksummed ZIP recorded by
website/README.md. All 18 website tests pass. Real Chrome checks pass for all
four pages at 375/768/1440, including filters, menu Escape/focus, offline
catalogue, no-JS fallback and zero page errors/overflow. All 94 local links
resolve. Graphify code refresh: 3847 nodes, 9498 edges, 225 communities.
Proof: .diagnostics/website-redesign-2026-10-28.json. Backend validation was
not rerun per current instruction; no backend/research/policy changes. No
commit, push, public deployment or installer rebuild. Local checkout preview
was served on 127.0.0.1:8772; it is not public hosting.

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

## D088 independent research feasibility — 2026-10-29

Owner authorized the real-bug/fresh-history evaluation. Pinned a GitBug-Java
repository-level split (six development/twelve held-out); 85,611,832 bytes of
metadata downloaded. All six development cases have published failing-to-passing
evidence, but zero changed same-identity methods meet the current public static
numeric contract. This is a source-coverage finding, not a bug-detection trial.
Held-out sources/test outcomes remain unaudited. Do not replace refused cases.

LRTS public archive inspected with byte ranges; only its 20,592,181-byte metadata
CSV downloaded and CRC/SHA256 verified. ActiveMQ has 446 suite rows/391 distinct
heads, insufficient for the predefined 1,500-build cohort. PR target branches do
not establish ancestry. No model/risk replay/CI speedup claim. See
experiments/results/research-feasibility-d088-2026-10-29/FINDINGS.md and
RESEARCH_EVALUATION_D088.md. Development-source parser adapter error was fixed;
initial diagnostic retained under build/d088-inputs (not a product refusal).

D087 full validation session 21241 still running, log in pointer
.diagnostics/d087-full-maven.log. It reported a failure at the obsolete long-return
rejection fixture. Changed only that fixture to double; five corrected refusal
checks passed (35 deselected, 10.19s). Await original full trace/totals before
calling it the only failure. Two research-harness checks passed in 0.12s.
Application source remains a30ce70; new research scripts/test fixture are separate.
Do not launch duplicate full tests, push, merge, or overwrite friend installers.

## D089 implemented receiver/array support; brake cohort repaired — 2026-10-29

Application extension committed at 2c54145 (later wording-only reduction description
fix). Public no-argument fresh receivers and int-array results <=128 now work in
Moonshot, report/export and supplied-requirement JUnit drafts. Input arrays remain
<=8 elements. Preserve exceptional inputs; continue budgeted normal-return search,
but report inconclusive if only exceptional/no witness results remain. No private
access override, arbitrary objects, dates, callbacks or void-output inference.

All six development refusals diagnosed. One now eligible; five remain unsupported.
Published stock-span trigger reproduced three times/version: [10,10,10,10] gives
[1,2,3,4] before and published expected [1,1,1,1] after. Automatic guided and simple
searches independently found [0,0] without supplied oracle inputs; both exported
JDK reproducers passed. This is one known development bug, not held-out superiority
or automatic bug classification. Twelve reserved repositories remain untouched.

ActiveMQ/main revised outcome-blind cohort: 223 train/74 audit/75 evaluation heads.
All 75 evaluation heads have 62 known training and 38-39 known audit ancestors.
All 372 raw inventories acquired; hash/CRC/structure/duration/executed-count checks
pass. Published executed counts do not prove no skipped classes or risk acceptance.
Risk targets, existing model/audit rules and mandatory tests remain unchanged.
No new model-effectiveness, miss-rate or actual net-CI-time result is claimed.

D087 full test run was intentionally stopped after stalled Gradle daemon handshake;
partial log and obsolete long-return rejection failure preserved. Never call it
completed/passed. Real Gradle prerequisite now passes with GRADLE_OPTS disabling
forking: 1 pass/1 deselected,106.68s. Focused integration 12 passed (16.54s), numeric/
refusal/exception 19 passed (26 deselected,85.17s), cohort integrity 5 passed (4.49s).
One final Maven-inclusive suite on the saved batch is next; do not run duplicates.
See CORE_IMPROVEMENTS_D089.md and RESEARCH_EVALUATION_D089.md. Source/research
preparation only; no installer replacement, push or merge authorized/performed.
