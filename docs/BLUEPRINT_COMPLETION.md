# Blueprint completion ledger - 2026-10-27

This is the current task list. Historical HANDOFF.md rows about running studies,
PR #21/#22 publication approval or applying old edits are superseded. Preserve
all stashes and backups. Base main is 45821b4908bf3c17ff60cea28fd934c0dd55d8f1.
Current review branch: codex/blueprint-completion. Extra proposals are deferred
by the owner: DEFERRED_FEATURES.md.

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
| 7 bug 8 graph precision | Blinded 40-edge form prepared in graph-human-review/; independent student labels still required. |
| 7 bug 9 wording | Tests view uses neutral test wording for Java classes and Python modules. |
| 7 bug 10 installer | Current core rebuilt; production IDE/installer build and smoke validation in progress. |
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
