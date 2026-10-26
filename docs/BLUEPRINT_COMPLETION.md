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
