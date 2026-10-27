# Blueprint completion ledger - 2026-10-27

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


This is the current task list. Historical HANDOFF.md rows about running studies,
PR #21/#22 publication approval or applying old edits are superseded. Preserve
all stashes and backups. Base main is 45821b4908bf3c17ff60cea28fd934c0dd55d8f1.
Current review branch: codex/blueprint-completion. The owner has now authorized
the engineering follow-up in DEFERRED_FEATURES.md; installation is deferred last.

## Milestone status

Milestone 5 implementation and studies are present. Report assembly and
supervisor review prevent calling the whole research milestone closed. Java
and Python already exist; additional languages are a future product expansion.
Milestones 6/7 still have acceptance and distribution work.

## Blueprint reconciliation

| Item | Current disposition |
|---|---|
| 0.5/3/17 integration | #21 and #22 merged; #8 already closed. Do not merge stacked heads again. |
| 4 laptop preservation | Old local commits and all stashes preserved; original data backed up. |
| 6.1 studies | Nine-project runs finished; findings and hashes saved. Missing pre-run addendum cannot be repaired retrospectively. |
| 6.2 default decision | D-067: retain B10; CRC opt-in. No threshold retuning. |
| 6.3/6.5 live CRC/demo | Already implemented/tested in D-068. |
| 6.4 structural plan | Already implemented in D-070; required tests include structural and policy tests. |
| 7 bugs 2/4/5 | Python/mixed full-suite fallback, structural plan and live CRC fixed on merged main. |
| 7 bug 3 unsupported files | Conservative full-suite fallback retained for build/resources/non-Java changes; no unvalidated broadening of the model domain. |
| 7 bug 6 cache | Fixed: Python forwards cache; core passes optional cache by capability, including legacy compatibility. |
| 7 bug 7 Ant discovery | Explicit unsupported-build limitation; not fabricated as working. |
| 7 bug 8 graph precision | Owner declines further labelling. Attribute the original AI audit and Gemini cross-check accurately; no independent human validation claim. |
| 7 bug 9 wording | Tests view uses neutral test wording for Java classes and Python modules. |
| 7 bug 10 installer | D-074 packaged optional installation is complete and validated; later installer refresh and clean-PC evidence are deferred last. |
| 7 bug 11 IDE | Manual acceptance in progress; use IDE_MANUAL_TEST.md. |
| 7 bug 12 hosting | Website/catalogue source exists. Public hosting and wheel URLs remain unavailable; do not expose the private source repository. |
| 7 bugs 13-16 limits | 15 live vs 19 retrospective features, serial dependence, incomplete CI history and dependency warning remain disclosed. |
| 7 bug 17 stale docs | Current overrides, roadmap and report limitations refreshed in this branch. |
| 8 regression coverage | Existing cases retained; skipped required tests/history preservation, cache compatibility, packaged interpreter, PR demo and CRC CLI smoke added. |
| 9 shared risk interface | Do not give Python a Java-trained risk model. Conservative fallback remains correct until separate validation. |
| 9 CRC CI smoke | Tiny synthetic CRC CLI test is in the regular pytest CI suite. No real study reruns. |
| 9 advanced graph/coverage | Gradle per-test coverage and method-level call resolution remain explicit limits/future work. |
| 10 report | System/evaluation/agent chapters and final assembly tracked; no fabricated independent confirmation. |
| 11 defence | DEFENCE_CHECKLIST.md prepared; human rehearsal/recording still required. |

## Verified fixes in this branch

- The brake returns incomplete if any required class/module was skipped, even
  when other required tests passed. A real failure still returns blocked.
- Skipped required tests cannot overwrite complete project history.
- Python discovery reuses graph parses without breaking plugins lacking a cache argument.
- Project `.venv` is preferred for pytest. A frozen core cannot masquerade as
  Python when no project/external interpreter exists.
- The read-only PR workflow exports a plan and explicitly says tests were not
  executed; it does not post messages or run an analysed project's build.

## Validation evidence

- Focused brake/history/plugin suite: 95 passed, 1 existing warning, 253.67 s.
- Python cache/interpreter subset: 6 passed, 9.39 s.
- PR demo and CRC CLI smoke: 2 passed, 40.91 s.
- IDE TypeScript compile passed; Node workflow 8 passed; runtime 3 passed.
- Full Maven-inclusive suite: 562 passed, zero failed/skipped, 1513.49 s. Production IDE and installer built; 1,389 packaged core hashes verified. Installer unsigned; clean-PC installation remains unverified.

## Remaining owner/external evidence

A real clean Windows environment, independent student graph labels, supervisor
sign-off and defence recording cannot be truthfully replaced with local unit
tests or AI assertions. Public hosting needs a suitable release destination;
keep the private repository private. These remain open until evidence exists.

Additional completed evidence: the frozen core loads Java/Python, runs real
passing and failing pytest checks through MCP, refuses a missing interpreter
without launching itself, and verifies all 1,389 bundle-file hashes. This is a
restricted-PATH local smoke, not a clean-PC installation. Java diagnostics show
the deliberate String-to-int error and clear after correction. The rebuilt IDE
discovers a Python test alongside two Java classes in WORKTREE and recommends
all three with risk unvalidated. Both synthetic probes were hash-checked and
removed. Final suite and package proof is in RELEASE_VALIDATION_2026-10-27.json.

## Owner follow-up now active

The current automated completion batch passed. Continue with the queued brake
improvement and website/Extensions work from DEFERRED_FEATURES.md. Human/external
checks remain open; do not describe the entire blueprint as fully signed off.

## D-072/D-073 continuation - 2026-10-27

Owner confirmed: fix presentation and defects without weakening risk validation.
Full Maven-inclusive suite after D-072: 563 passed, zero failed/skipped, 2437.48 s.
No completed studies, thresholds, defaults, saved project history or stashes changed.
D-073 is frontend-only: show runner-supplied individual check names/outcomes,
explain same-change/future-history refusal without asserting that foreign data
exists, make saved-run clicks reveal their details above the list and scroll
them into view, display the analysed project path, and add a real study-folder
browser with disabled empty submission. Research replay and project history
are explicitly distinguished. Earlier saved results without cases still render.
TypeScript compile and all 18 IDE Node regression tests pass (zero skipped).
Website acquisition tests: 13 passed; desktop runtime tests: 3 passed previously.
Frozen-core smoke: Java/Python load, actual MCP passing/failing pytest and missing
external interpreter handling passed; all 1,389 bundle hashes match.

Final production/installer rebuild includes D-073 and uses compression level 3
instead of the packager's level 9 to avoid wasting laptop time. This affects
archive size only. Package verification/friend kit remains pending until the
final installer completes. Previous D-071 installer is preserved in backups.
The public catalogue URL still returns 404; installed bundled Java/Python work,
but optional online acquisition and frozen optional-wheel installation are not
validated public release capabilities. Do not expose the private repository.
Detailed website handoff: WEBSITE_BLUEPRINT.md; local preview port 8769.
Clean-PC installation, independent human graph labels, university supervisor
review and defence recording remain external acceptance, not AI-completed work.


## D-073 observed desktop acceptance - 2026-10-27

The rebuilt source IDE with the frozen core was opened on C:/Users/hp/codedna-demo.
Extensions was visible after restart and listed installed Java/Python despite
the online catalogue 404. Project history loaded automatically, displayed the
canonical demo path, and selecting View results revealed and scrolled to both
classes and all six actual saved JUnit check outcomes. No project tests were
executed and no saved history was changed by this acceptance check.

History replay showed a disabled Load results for empty input. Browse opened a
folder-only native picker and populated the chosen actual path. Loading
experiments/results/study11-2026-10-21 succeeded: 55 compatible reports across
11 projects appeared. Reports without trace SHAs are labelled accordingly.
The rolling-evidence and other research summaries use a different format and
are not currently replay inputs; an existing directory alone is insufficient.
This remains a documented format limitation, not a reason to rerun studies.


The desktop risk recommendation was also checked after D-073: it retained
Risk unvalidated, the original chronological-history reason and both required
demo test classes, while showing the new same-change explanation. Only the
read-only Suggest tests action was used; no test execution or history recording
was triggered. Existing stashes retain their original object IDs.


## Final local release handoff - 2026-10-27

Source checkpoint: e16cbb5. Final production browser/node/Electron build and
Windows NSIS installer completed successfully. Installer: 339848642 bytes;
SHA-256 `7d3f469e63d8557682c4b95ec696b477ab49f35301a1e375bc77789fb9a33315`; unsigned. Every one of the 1,389
packaged core hashes matches; current D-073 UI text exists in the packaged
application. Evidence: RELEASE_VALIDATION_D072_D073_2026-10-27.json.

The friend test kit is prepared under build/friend-test-kit and its archive
integrity was checked. It includes the exact installer/hash, verifier,
instructions and tiny Java/Python Git demos. No kit was sent to anyone and
no clean-PC installation result is claimed. Previous installers are preserved.

Both plugin wheels were built without network/dependency installation and
their declared Java/Python entry points loaded from an isolated target. See
PLUGIN_RELEASE_CANDIDATES_2026-10-27.json. This advances release preparation;
no public URLs, frozen optional-wheel support or website publication is claimed.

The remaining gates are real clean-PC feedback, independent student graph
labels, university supervisor/report review, defence rehearsal/video, public
catalogue/release publication and frozen optional-plugin installation support.
The deferred novelty/features backlog remains deferred, and original studies
are unchanged. Do not rebuild completed CRC, dependency union or Python fallback.


## Owner scope update - 2026-10-27

The owner declines independent student graph labelling. Do not keep requesting
it or treat it as an active owner task. Existing labels remain AI-generated;
no independent validation or human precision result is claimed. Supervisor
review is deferred until the owner supplies their next message. The pasted
supervisor-style assessment is preliminary and has not reviewed the five files.
Catalogue hosting and frozen optional-plugin installation remain genuine
distribution work, separate from the bundled Java/Python functionality.


## D-074 candidate - actual frozen plugin installation fixed

The production frozen core now stages optional wheels per user, validates them
and atomically activates them for restart. Source pip behavior remains intact.
Actual executable installation/update/removal/restart and fallback checks pass
without Python/pip on PATH; 1,451 core hashes match. See
FROZEN_PLUGIN_VALIDATION_D074_2026-10-27.json and DESKTOP_PLUGIN_INSTALLATION.md.
Final full-suite and NSIS verification remain in progress. This supersedes
earlier statements that frozen optional installation is unimplemented; it does
not turn the separate public catalogue 404 or clean-PC acceptance into success.
No research changes were made. The owner reports Gemini agreed with the graph
labels; that is a second AI cross-check, not independent human validation.


## D-074 completed local release - 2026-10-27

Frozen-desktop optional plugin installation is implemented and verified, not
an outstanding engineering gate. Source checkpoint 70626d8. Final production
IDE/NSIS build completed; full Maven-inclusive suite: 576
passed, zero failed/skipped, 2234.48 seconds. Nineteen
IDE checks and all seven actual frozen-core plugin checks pass. All
1,451 packaged core hashes match the tested candidate.
Installer is unsigned, 340489443 bytes, SHA-256 `1cd872fe7dc1b44abb96fa6ff161ed7cb3a0021e183af0e0ec4d0c802b8ee7ed`.
Evidence: RELEASE_VALIDATION_D074_2026-10-27.json.

The new D074 friend kit and installer backup are prepared separately; older
kits/installers are preserved. A real clean-PC installation remains unverified.
The public catalogue still returns 404 and public wheels are unpublished;
that separate distribution task is not fixed by changing the installation
runtime. No new source push/merge; both original stashes are preserved.

Owner now authorizes discretion after the revised ChatGPT review. Next is
report correction and a read-only data-feasibility check, then a bounded study
protocol if justified. The new study is required for a stronger partial-feedback
claim, rather than unconditionally for a bounded retrospective FYP. Preserve
all old study results. Gemini's graph check is another AI review, not human
ground truth. Do not require further independent labelling from the owner.


## D-075 report corrections and feasibility completed

The revised report has current dated validation, explicit AI-audit provenance,
distinct safety metrics and honest retrospective/cost limits. All chapter
sources and report dependencies are included in the corrected review pack.
See REPORT_REVISION_NOTES_D075.md and REPORT_REVISION_QA_D075_2026-10-27.json.

The read-only input audit and three HikariCP static probes support a bounded
development pilot on the four older structural datasets. No closed-loop study
has run; the nine-project CSVs lack dependency features. Next is a frozen pilot
protocol and leakage-proof policy-observation engine, not another model/language.
Independent labels remain unavailable; the Gemini check is AI cross-checking.
Public hosting and real clean-PC feedback remain separate from the finished
frozen-plugin implementation. Original studies and stashes are preserved.


## D-076 / D-077 active continuation

The effective D-076 development protocol was frozen before real evaluation.
The replay engine and checkpoint runner are in 72e6043; 15 focused tests pass.
Real source mapping and the Maven-inclusive full suite are in progress. The
pilot does not change the live policy or turn reused inputs into confirmation.

D-077 in 4c5767c adds source check names, history/evidence recovery guidance and
an explicitly saved JSON decision record. TypeScript and 27 Node UI/workflow
checks pass. These are source changes; they are not in a rebuilt installer yet.
Per-operation cancellation, broader progress and measured cache acceptance
remain next. Source push readiness awaits full validation; no new push/merge.

The owner explicitly moved installation, public catalogue delivery and actual
clean-PC work to the very end. Do not resume these while engineering is active.
No further independent-label task is requested; disclose AI provenance instead.
