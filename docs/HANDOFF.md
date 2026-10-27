# CodeDNA — full handoff blueprint (2026-10-26)

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


## Current continuation - D-075, 2026-10-27

D-074 plugin installation is complete: full suite 576 passed, zero skips;
19 IDE tests; seven actual frozen plugin checks; 1451 packaged hashes verified.
Installer and D074 friend kit are ready; source commits 70626d8/500c998 remain
local, no new push/merge, all stashes preserved. Do not rebuild this feature.
D-075 report corrections and read-only feasibility are complete. Read
REPORT_REVISION_NOTES_D075.md and PARTIAL_FEEDBACK_FEASIBILITY.md. Four older
datasets have structural evidence; the nine-project CSVs do not. Three HikariCP
code-only snapshots mapped exactly. No new selector study has run. Next is a
bounded protocol-first pilot; reused data is not independent confirmation.
The owner's technical reviewer is ChatGPT and labels were cross-checked with
Gemini; do not keep asking for human labels or claim independent validation.


## Current override - D-074 completed, 2026-10-27

The frozen desktop plugin-installation fix is complete and validated. Read
DESKTOP_PLUGIN_INSTALLATION.md and RELEASE_VALIDATION_D074_2026-10-27.json.
All final tests, bundled hashes and the new installer/friend kit are recorded
there. Earlier notes calling this feature unimplemented are superseded.
Source checkpoint 70626d8; no new push/merge; preserve stashes and old studies.
Next authorized work: correct the report and assess feasibility of a bounded
partial-feedback/structural-floor follow-up. The latest review makes that study
conditional on a stronger claim. Public hosting and real clean-PC feedback are
separate; do not repeat the completed plugin implementation.


## Active checkpoint - D-072/D-073, 2026-10-27

Continue on codex/blueprint-completion; preserve all stashes. D-071 is local
commit 8b0d478. The branch contains the reviewed D-072/D-073 source checkpoint; inspect git log for its commit. Full Maven suite
563 passed, zero skipped; latest TypeScript compile and 18 IDE tests passed.
Risk thresholds/fallbacks unchanged. Individual recorded checks, clear history
selection and replay folder browsing fix the owner's demo feedback. See
BLUEPRINT_COMPLETION.md for exact validation and remaining external gates.
Final D-072/D-073 installer and friend test kit are built and verified;
see RELEASE_VALIDATION_D072_D073_2026-10-27.json. Clean-PC acceptance remains pending. Website source and detailed blueprint are ready locally;
public catalogue/wheel hosting remains unavailable. No new push/merge yet.


## Current continuation - 2026-10-27 (supersedes older status)

PR #22 merged as 45821b4 after owner authorization and green checks. D-068 and
D-070 are already on main. The studies are finished; preserve their reports.
Work now continues on codex/blueprint-completion. Read
[the current completion ledger](BLUEPRINT_COMPLETION.md) for remaining work
and validation, and [the deferred backlog](DEFERRED_FEATURES.md). The owner
asked to save extra proposals for later, not implement them now. Preserve all
stashes. Publication/merge-pending notes below are historical, not current.


This is the plan for finishing CodeDNA without the Claude project threads.
It is written for Amna and Mohib, and for any AI coding agent (Codex, GPT,
Claude) that picks the work up. Every claim below was checked against the
code on the integration branch `claude/project-thread-lo3rpw` on
2026-10-26, unless it says "not verified".

Read in this order: §0 (one page), §1 (rules), §3 (merging), §4 (laptop),
§6 (the novelty work that is still missing). The rest is reference.

---

## Latest verified override - 2026-10-26 (read first)

PR #21 is merged as main 8183d2d. Both CI runs are green (7/7 each).
Post-pull full suite: 533 passed, zero skipped, Maven included; the full
IDE rebuild/start succeeded. #8 was already closed. Stacked #17/#18/#19
still show open against old bases, but their heads are included in main.
No further merges of those PRs are required. Preserve every stash.

All four nine-project laptop runs finished and their findings/hashes are
published in *confirmatory-perf-2026-10-26 folders. D-067 keeps B10 default,
CRC opt-in (D-068), with missing protocol addendum and negative results
explicit. The older rows and opening "B12f absent" claim are superseded.

Next build is implemented on codex/brake-structural-python (D-070): section
6.4 structural_plan plus Python/mixed full-suite fallback and neutral
execution. Full branch validation passed (554, zero skips, Maven included). Automatic approval review blocked its private-source push; obtain explicit owner approval, then publish its review PR, and await
separate authorization before merging that PR. Do not repeat the studies,
CRC implementation, or the dependency/Python implementation once validated.

## 0. One-page summary

**What CodeDNA is.** A tool that looks at a Java (and now Python) code
change, works out which code it can affect, picks which regression tests to
run, and says how risky it is to skip the rest. It refuses to skip anything
unless the project's own recorded history passes an audit. It has a Python
core, language plugins, a desktop IDE (Eclipse Theia + Electron), a local
API, and an MCP server so AI coding agents can use it as a "test brake".

**The honest headline (use this framing in the report and the defence).**
CodeDNA is *safe, and honest about when it cannot save time*. It is not
"fast" and its stopping rule does **not** beat the simple recent-failures
rule (B3):

- Confirmatory study on 9 new projects (PR #20): stopping rule B10 minus
  matched-time B3, safety −0.7 points, 95 % interval −3.4 to +1.8. No
  meaningful difference. Do not claim B10 beats B3.
- The audit gate works: blocks it accepted missed failures on 2.5 % of all evaluation commits
  (one-sided Wilson upper bound 3.35 %), under the 5 % target. Rejected
  blocks fall back to the full suite, so the product miss rate is at most
  1.87 % in every project.
- Savings are small: okhttp runs 69.1 % of its test time, sling 91.2 %,
  deeplearning4j 88.4 %; 5 of 9 projects always run 100 %.
- Agent brake study on public SWE-bench Java agent patches: the
  dependency plan caught exactly as many broken patches as the full suite
  (primary 47 of 143; post-hoc follow-up 108 of 149, 108 of 108 without
  lombok), while needing a median 18 % of druid's tests.
- Conformal risk control stop B12f (exploratory, 4 old projects): kept
  safety ≥ 0.95 on 4 of 4 projects against 2 of 4 for B10.

**Lead the report with:** the gate's safety, the AI-brake study and the
conformal stop B12f, in that order.

**Historical three-item gap list (resolved by D-067/D-068/D-070; retained below as context, not current tasks):**

1. **B12f is not in the product.** The live brake (`codedna mcp`, IDE,
   `risk-select`) still uses B10 + the Wilson gate (`selection/live.py`,
   `codedna_java/live.py`). `selection/conformal.py` is used only by
   `scripts/run_crc_check.py`. The claim "a conformal-risk-controlled test
   brake for AI agents" is therefore *not yet true end to end*. §6 says
   exactly how to make it true.
2. **B12f and the PTS baseline have not been rerun on the confirmatory
   data.** `run_crc_check.py` used to hard-code "at least 3 projects keep
   the target" (the 4-project rule), which would call 3 of 9 a success;
   this branch changes it to 75 % of projects, rounded up (3 of 4, 7 of 9),
   and adds `--protocol`. Write the protocol addendum **before** running
   (§6.1).
3. **The brake study measured a plan the brake never returns.** The study
   scored `select_tests(..., "dependency")` (the dependency plan, "A2").
   `codedna_plan_tests` returns either the full suite (no validated
   history) or a risk-ordered subset; the dependency plan only appears in
   `codedna_impact`'s `candidate_tests`. §6.3 fixes this.

**Why the savings are small.** A count of the saved gate reasons (§6b)
shows the gate rejects blocks mainly because B10 misses too many failing
commits in the audit, not because history is too short (only 1 of 44
blocks had too few failing audit commits). B12f targets exactly that.

**Merging.** All six open PRs (#15, #18, #16, #17, #19, #20) were merged
locally in that order on this branch, with the conflicts resolved and four
cross-PR breakages fixed. Result: `python -m pytest --run-maven` gives
**475 passed, 8 skipped** (the 8 are Windows-only `start.bat` tests), the
3 Maven integration tests pass, the IDE extension compiles, and its 3 + 8
Node tests pass. The simplest route is to merge this one PR (§3.1).

---

## 0.5 START HERE - current continuation, 2026-10-27

| Task | State | Next action |
|---|---|---|
| Integration/original studies | #21/#22 merged; nine-project findings/hashes preserved | Do not repeat merges or old studies. Preserve every stash. |
| D-071 through D-074 | Completed and verified, including frozen optional-plugin installation; D-074 full suite 576 passed, zero skips | Do not rebuild installation now. It is deferred to the end by owner instruction. |
| D-075 report/feasibility | Complete; corrected portable review pack and read-only feasibility audit saved | Read REPORT_REVISION_NOTES_D075.md and PARTIAL_FEEDBACK_FEASIBILITY.md. |
| D-076 development research | Completed: all 360 source mappings; 120 evaluation commits; no risk-gated reduction; full source suite 591 passed/zero skips | Read the new pilot FINDINGS.md. Measure overhead before scaling; do not retune for a positive result. |
| D-077 engineering | Local 4c5767c: source check explanations, evidence-health guidance, explicit decision evidence export; TypeScript and 27 Node tests pass | Continue operation cancellation/progress and broader workflow acceptance without weakening gates. No new installer yet. |
| Labels/review | Owner uses ChatGPT for technical review; Gemini cross-check is a second AI judgement | No further owner labelling task. Keep provenance honest; no human-ground-truth claim. |
| Website/distribution/clean PC | Website blueprint/source prepared; catalogue hosting and actual clean-PC evidence still open | Defer these installation/distribution tasks to the end; keep source private. |
| Source sharing | Owner notified: validated source-review checkpoint ready; no push/merge performed | Owner may push codex/blueprint-completion for private review. Keep release/merge decisions separate. |

Historical instructions below are reference, not a request to reapply old
edits, repeat integration or retune until a favorable research result appears.
The authorized engineering follow-up is recorded in DEFERRED_FEATURES.md.

### Click-by-click: merging on GitHub

**Route A (one PR, recommended).**
1. Open the repository on github.com → **Pull requests** → the PR titled
   "Integrate PRs #15–#20 in order, fix cross-PR breakage, add the handoff blueprint".
2. Scroll to the bottom. Wait until the checks show green ticks (all
   7 jobs). If one is red, do not merge; give the failing job's log to the
   next agent.
3. Click the arrow next to the green button and choose **Create a merge
   commit** (not squash, not rebase). Click **Merge pull request**, then
   **Confirm merge**.
4. Open #15, #16, #17, #18, #19 and #20. Each should now say **Merged**
   (GitHub notices their commits are in `main`). If one still says Open,
   it got new commits after the integration; see the "Integration" row
   above.
5. Open #8 → **Close pull request** with the comment "Included in #16".

**Route B (one at a time).** For each PR in the order #15, #18, #16, #17,
#19, #20: open it, check its **base** at the top ("wants to merge into
`main`"). If the base is not `main`, retarget it (below). If GitHub says
"This branch has conflicts", stop and let an agent resolve them as §3.3
describes. When checks are green: **Create a merge commit** → **Confirm
merge**.

**Retargeting a stacked PR's base** (needed for #18 after #15, and for #17
and #19 after #16): open the PR → click **Edit** next to the title → the
**base** dropdown appears under the title → choose `main` → confirm
**Change base**. If the old base branch was deleted after its merge,
GitHub usually retargets automatically. A draft PR (#17) needs **Ready for
review** first.

---

## 1. Ground rules (read before touching anything)

1. **Never commit, push or merge GPT/Codex's uncommitted laptop edits.**
   Codex edited the laptop's working tree directly (base `ecd4f54`). Its
   project-history rewrite has three bugs that must never come back:
   - it drops every run whose build exit code is non-zero. Maven and
     Gradle exit 1 whenever a test fails, so all failure evidence
     disappears and the risk model only ever sees passes;
   - it writes a second history file and then overwrites
     `.codedna/history.csv`, which the D-053 recorder then refuses as foreign;
   - it edits the user's `.git/info/exclude`.
   The fixed versions are in PR #17 (D-057) and guarded by
   `backend/tests/test_project_history.py`. Codex has no view of GitHub and
   reuses decision numbers (its D-050..D-054 clash with ours). Compare by
   content, never by number. Port by hand into a branch.
2. AGENTS.md rules still hold: tests for every feature (temporary Git repos,
   no internet); graph edges labelled confirmed / heuristic / unresolved;
   Git only through `codedna.git_analysis.git.run_git`, never `shell=True`;
   `codedna run-tests --allow-build` only when the user passes it; plugins
   only from the official catalogue with SHA-256 and pinned versions; the
   API listens on 127.0.0.1 only.
3. **Never fabricate numbers.** Every number in the report must come from a
   file under `experiments/results/`. Report negative results. Label post-hoc
   runs as post hoc. The primary brake-study number (47/143) stays the main
   number; 108/149 is the labelled follow-up.
4. **Fix the protocol first, then run.** Every new study gets a protocol
   file in `docs/` committed before the run (pattern:
   `docs/CRC_CONDITIONAL_PROTOCOL.md`). New output folder every time; never
   overwrite a results folder.
5. Run `python -m pytest --run-maven` before claiming anything is done, and
   report the real counts.
6. Git identity: Amna's commits use Amna's own GitHub no-reply email (not
   Mohib's). Commit `97c3be7` on the laptop is blocked by GitHub's email
   privacy check (see §4.4). AI commits use
   `-c user.name=Claude -c user.email=noreply@anthropic.com` or the agent's
   own identity.
7. Never say "first" about the novelty. Say "to our knowledge" and cite the
   closest work (§5.4).
8. Security features wait until after the defence (owner decision,
   2026-10-25). The must-run policy hook (D-050) is where they will plug in.
9. The website is Amna's. Keep the PR #7 pages, do not build more.
10. Graphify is the project's navigation tool. On the laptop it is not on
    PATH (§13).

---

## 2. Where everything stands (verified 2026-10-26)

### 2.1 Feature status

| Area | Status | Where | Notes |
|---|---|---|---|
| Change analysis (M1) | ✅ | `backend/codedna/git_analysis/`, `codedna_java/mapping.py` | method-level, unresolved recorded |
| Dependency graph (M2) | ✅ | `codedna_java/builder.py`, `references.py` | precision 160/160 on a sample (D-058); labels were AI-made, **student spot-check pending** |
| Method-level call edges | ⏳ | — | deferred (D-010); say so in limitations |
| Test discovery (M3) | ✅ | `codedna_java/discovery.py` | JUnit 3/4/5, TestNG flagged, multi-module Maven, Gradle (D-045, D-064). **Ant builds unsupported** (lombok) |
| Maven/Gradle execution, JaCoCo | ✅ | `codedna_java/maven.py`, `build.py` | only with `--allow-build` |
| History, features, models (M4) | ✅ | `backend/codedna/test_history/`, `models/` | RTPTorrent import |
| Calibration, risk stop, gate (M5) | ✅ | `calibration/`, `selection/risk.py`, `selection/validation.py`, `selection/live.py` | B10 + Wilson gate is what ships |
| PTS baseline B11 | ✅ exploratory | `selection/pts.py`, `scripts/run_pts_check.py` | 4 old projects only |
| Conformal stop B12 / B12f | ✅ exploratory, **not in product** | `selection/conformal.py`, `scripts/run_crc_check.py` | §6 |
| Confirmatory study (9 projects) | ✅ | PR #20, `experiments/results/rolling-evidence-confirmatory-windowsfix-2026-10-26/` | B10 ≈ B3; gate supported |
| Must-run policy | ✅ | `selection/policy.py`, `.codedna/policy.toml` (D-050) | hook for later security checks |
| Record-as-you-go history | ✅ | `test_history/recording.py`, `project.py` (D-053, D-057) | gate needs hundreds of recorded commits with failures |
| Agent brake (`codedna mcp`) | ✅ (B10 gate) | `backend/codedna/agent/brake.py`, `mcp_server.py`, `docs/AGENT_BRAKE.md` | Java-only risk path (§7) |
| SWE-bench brake study | ✅ | `scripts/swebench_brake_study.py`, `experiments/results/agent-brake-swebench-2026-10-25/` | measured the dependency plan (§6.3) |
| Java plugin package | ✅ | `plugins/codedna-java/` (D-054) | core has no Java imports |
| Python plugin | ✅ | `plugins/codedna-python/` (D-060) | stdlib `ast`, pytest; **no risk selection** |
| Plugin manager (CLI/API/IDE view) | ✅ | `backend/codedna/plugins/manager.py`, IDE *Language plugins* view | catalogue **hosting blocked**: repo is private (D-048) |
| IDE views | ✅ built | `ide/codedna-extension/` | Changes, Tests to run, Impact graph, Project history, History replay, Language plugins. **Windows click-through not verified** |
| Desktop installer with bundled core | ✅ built, **unverified on a clean PC** | `scripts/build_desktop_core.py`, `ide/electron-app/` (D-055) | unsigned |
| Website + catalogue JSON | ✅ static pages | `website/` (D-047) | Amna's; not hosted yet |
| GitHub PR demo / bot | ⏳ | — | roadmap M6 |
| Report | 🔄 drafts | `docs/REPORT_SYSTEM_DRAFT.md` (~4.9k words), `REPORT_DRAFT.md` (~5.3k), `REPORT_AGENT_BRAKE.md` | §10 |

### 2.2 Decision numbers in use

D-001…D-066, with D-060 = Python plugin, D-061 = PTS, D-062 = brake study,
D-063 = CRC, D-064 = JUnit 3/Gradle discovery, D-065 = Windows Git ancestry,
D-066 = IDE test links, D-068 = conformal stop as an opt-in live method. **D-067 is reserved for the B12f default decision (§6.2); the next free number is D-069.** (Commit
`d54f2cb`'s message says "D-054" for the graph precision work; the decision
record correctly calls it D-058.)

---

## 3. The open PRs and how to merge them

### 3.1 PR bases (checked on GitHub, 2026-10-26)

| PR | Branch | Base | Content | CI |
|---|---|---|---|---|
| #15 | `claude/project-thread-dfhix3` | `main` | report chapters, graph precision D-058, agent brake D-059, brake study D-062/D-064 | green |
| #18 | `claude/project-thread-71arlo` | **#15's branch** (at `5aae3f9`) | related work, PTS D-061, CRC D-063 | green |
| #16 | `claude/java-plugin-split` | `main` | `codedna-java` package, plugin manager, D-054 (includes #8) | green |
| #17 | `claude/project-thread-info38` (draft) | **#16's branch** | bundled core D-055, confirmatory prep D-056, project history D-057, D-065, D-066 | green |
| #19 | `claude/python-plugin` | **#16's branch** | Python plugin D-060 | green |
| #20 | `claude/confirmatory-results-2026-10-26` | `main` | confirmatory results | — |
| #8 | `claude/plugin-manager` | `main` | old plugin manager | **close as included in #16** |
| this PR | `claude/project-thread-lo3rpw` | `main` | all of the above merged in order + fixes + this file | — |

**The one exact order:** #15 → #18 → #16 → #17 → #19 → #20.
#18 must follow #15 (stacked). #17 and #19 must follow #16 (stacked).
#20 has no code and no conflicts, so it can go anywhere; it goes last.

### 3.2 Route A (recommended): merge this one integration PR

This branch contains every PR merged in that order with merge commits,
plus the fixes in §3.4. Merging it lands everything in one step, and GitHub
marks #15, #16, #17, #18, #19 and #20 as merged automatically because their
head commits become part of `main`. Then close #8 as included.

Before merging, check that none of the six PR branches got new commits
after 2026-10-26 09:00Z. If one did: `git merge origin/<that-branch>` into
this branch, resolve, rerun the tests, push.

Acceptance after merge (on a fresh clone of `main`):

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[ml,api,dev]" -e plugins/codedna-java -e plugins/codedna-python
python -m pytest --run-maven          # expect ~470 passed, Windows-only skips on Linux
cd ide && npm ci --ignore-scripts && npm run build:extension \
  && npm run test:runtime --workspace electron-app && npm test --workspace codedna-extension
```

### 3.3 Route B: merge the PRs one by one

Use a **merge commit** every time (never squash, never rebase; #17 and #19
are stacked and lose their base if #16 is squashed).

1. Merge **#15**. Clean.
2. GitHub retargets #18 to `main` when #15's branch is deleted; if not,
   edit #18's base to `main`. Merge **#18**. It lacks #15's last two
   commits (`807d70c`, `0635813`) but those are already on `main`.
3. **#16 conflicts with the new main** in three files. Merge `main` into
   `claude/java-plugin-split` and resolve:
   - `backend/codedna/selection/baselines.py`: keep both sides — the
     registry (`registry = load_plugins(); java = require("java", registry)`)
     and #15's parse cache (`cache=cache` passed to `discover_tests` and to
     `compute_impact(..., cache=cache, changes=changes, registry=registry)`).
   - `docs/ARCHITECTURE.md`: take #16's layout (Java files moved to the
     plugin). In the plugin section change "JUnit 4/5" to "JUnit 3/4/5".
   - `docs/DECISIONS.md`: keep D-054 first, then D-058…D-064.
   Then apply §3.4 item 1 (imports). Push, wait for green, merge **#16**.
4. Retarget **#17** to `main`. Conflicts: `.gitignore` (keep both
   `swebench-multilingual/` and `confirmatory-*/` lines, and both trailing
   blocks) and `docs/DECISIONS.md` (order D-055, D-056, D-057, D-058…D-064,
   D-065, D-066). Mark it ready for review, merge.
5. Retarget **#19** to `main`. Conflicts in five files:
   - `selection/baselines.py`: `discovery = commit_tests(repo, head_sha, registry=registry, cache=cache)`
     and give `plugins/languages.py:commit_tests` an optional `cache`
     argument that it passes to the Java plugin only (the Python plugin's
     `discover_tests` has no `cache`);
   - `api/app.py`: keep `python_command=python_command` **and** #17's
     `save_json(selection, output / 'selection.json')`;
   - `ide/codedna-extension/src/browser/tests-view-widget.tsx`: take #19's
     trust message (mentions pytest) and #17's `const execution = …`,
     `openTest(report, item.test)` code; drop #19's `testPath()` guess
     (#17's discovery-based link works for Python too because discovery
     returns `file`);
   - `ide/README.md`: keep #17's bundled-core paragraph and Project history
     bullet, add "Java and Python are bundled (D-060)", install both plugins;
   - `docs/DECISIONS.md`: D-060 goes before D-061.
   Then §3.4 item 2 (desktop bundle). Merge.
6. Merge **#20**. Clean.
7. Close **#8** as included in #16.

### 3.4 Breakages fixed on this branch (Route B must repeat them)

1. After #16, four scripts imported modules that no longer exist, so
   `test_crc_check.py` and `test_pts_check.py` failed on import:
   - `scripts/run_pts_check.py`, `scripts/run_crc_check.py`:
     `from codedna.plugins.java_live import LIVE_FEATURES` →
     `from codedna_java.live import LIVE_FEATURES`, and their `CODE`
     fingerprint lists `backend/codedna/plugins/java_live.py` →
     `plugins/codedna-java/codedna_java/live.py`;
   - `scripts/swebench_brake_study.py`:
     `codedna.test_mapping.discovery` → `codedna_java.discovery`;
   - `scripts/run_tuned_gate_check.py` (B13, added later on #18's
     branch): same two fixes as the PTS/CRC scripts;
   - `scripts/sample_graph_edges.py`:
     `codedna.dependency_graph.builder` → `codedna_java.builder`;
   - `docs/REPORT_SYSTEM_DRAFT.md` F10 row: `plugins/java_live.py` →
     `codedna_java/live.py`.
   Consequence: fingerprints of new PTS/CRC runs differ from the saved
   ones (`pts-check-2026-10-25`, `crc-*-2026-10-26`). Say so in the
   protocol addendum.
2. `scripts/build_desktop_core.py` now bundles `codedna_python` (package,
   `--paths`, `--copy-metadata`, version record, install hint), with two
   new tests in `backend/tests/test_desktop_bundle.py`. Without it the
   Windows installer's core would find no Python plugin.

### 3.5 After merging

- Delete merged branches on GitHub (ask the owner first; branch deletion is
  their call).
- Run the full bug check on `main` (§3.2 acceptance), then on the laptop
  (§4).
- Update `MEMORY.md` (repo) "Last updated" and current-state sections, and
  `docs/ROADMAP.md`: M7 plugin manager ✅, Java package ✅, second language ✅
  (Python), confirmatory ✅.

---

## 4. Laptop steps (Windows, `C:\Users\hp\OneDrive\Documents\GitHub\codedna`)

### 4.1 Set GPT's uncommitted edits aside (do this first)

Backups already exist in `C:\Users\hp\codedna-backup-2026-10-26\`
(results, `gpt-uncommitted.diff`, untracked-files zip). In a terminal in
the repo:

```powershell
git status --short          # expect ~91 lines of GPT edits
git stash push -u -m "GPT laptop edits, set aside 2026-10-26" -- . ":(exclude)experiments/results/rolling-evidence-confirmatory-windowsfix-2026-10-26"
git status --short          # expect only the results folder (or nothing)
git stash list              # the stash must be listed
```

Until this is done, **do not commit anything in GitHub Desktop**. Never
run `git stash pop` on main; if anything from the stash is wanted, port it
by hand into a new branch after comparing with PR #17.

### 4.2 Pull after the merges (only after §3 is done)

```powershell
git fetch origin
git log --oneline origin/main..main     # what is local-only (expect 97c3be7)
```

### 4.3 Deal with 97c3be7 (graphify output, email privacy block)

`97c3be7` contains only `graphify-out/` files and is authored with an email
GitHub refuses to publish. Graphify output is regenerated anyway, so keep a
pointer to it and move main to `origin/main`:

```powershell
git branch keep/graphify-97c3be7 97c3be7
git reset --keep origin/main            # refuses if it would lose uncommitted work
& "C:\Users\hp\.codex\tools\graphify\Scripts\graphify.exe" update .
git add graphify-out
git -c user.email=<Amna's GitHub no-reply email> commit -m "Refresh graphify output"
git push origin main                    # or via a PR, if branch protection is on
```

(Find Amna's no-reply email in GitHub → Settings → Emails, it looks like
`12345678+username@users.noreply.github.com`.)

### 4.4 Reinstall and rebuild

```powershell
.venv\Scripts\python -m pip install -e ".[ml,api,dev]" -e plugins\codedna-java -e plugins\codedna-python
.venv\Scripts\python -m pytest --run-maven -q
start.bat                               # installs missing plugins, rebuilds the IDE after a pull
```

For the Maven test on the laptop, load `C:/Users/hp/.codex/tools/java-maven.json`
and set `JAVA_HOME`, `PATH` and `MAVEN_OPTS` as described in the repo
`MEMORY.md` ("Portable Java/Maven runtime").

### 4.5 Clean up after the confirmatory run

- Keep `experiments/datasets/confirmatory-windowsfix-2026-10-26/` (needed for
  §6.1). `confirmatory-live-2026-10-25` is a failed, superseded run: delete
  only after the owner agrees.
- `experiments\datasets\confirmatory\dl4j-pack-part-backup.bin` can be
  deleted once dl4j's pack is verified (it was: 74/74 files, sizes match).
- The worktree `..\codedna-results-wt` can be removed with
  `git worktree remove ..\codedna-results-wt` after #20 is merged.
- Close the keep-awake window when no long job is running.

---

## 5. The novelty claim

### 5.1 Claim wording to use

> CodeDNA is a regression-test brake for AI coding agents and developers.
> It decides how many tests a change needs from a calibrated estimate of
> the risk of skipping the rest, and it only skips anything when the
> project's own recorded history passes an audit; otherwise it runs the
> full suite. The stop threshold can be set by failure-conditional
> conformal risk control (B12f), which bounds the share of failing commits
> whose failure is missed.

What it is **not**: a faster ordering than simple rules (study11 RQ1, and
the confirmatory B10 ≈ B3), a guarantee (the bounds assume
exchangeability, which time-ordered commits only approximate), or the first
conformal test selection (§5.4).

### 5.2 Evidence table

| Evidence | Status | Number (source file) |
|---|---|---|
| study11, 11 projects × 5 seeds | done | ML ordering ≠ better than rules; calibration needed for B10's target (8/9 vs 6/9) — `experiments/results/study11-2026-10-21/FINDINGS.md` |
| Rolling-origin, 4 old projects | exploratory | B10−B3 safety −0.0032 [−0.036, 0.029] — `rolling-evidence-2026-10-24/` |
| **Confirmatory, 9 new projects** | **confirmatory** | B10−B3 safety −0.0072 [−0.0339, 0.0179]; gate accepted 8/44 blocks, miss 2.52 % (UB 3.35 %) — `rolling-evidence-confirmatory-windowsfix-2026-10-26/summary.json`, `docs/CONFIRMATORY_RESULTS_2026-10-26.md` |
| PTS baseline B11 | exploratory | B10−B11 safety +0.007 [−0.063, 0.091] — `pts-check-2026-10-25/` |
| B13 tuned gate (fixed-sequence thresholds) | exploratory, designed after #20 | time −13.0 pp vs gated product [−13.9, −12.2], safety −2.6 pp [−4.2, −1.1], miss ≤ 5 % on 4/4, HikariCP safety 0.914 — `tuned-gate-2026-10-26/`, protocol `docs/TUNED_GATE_PROTOCOL.md` |
| CRC B12 / B12f | exploratory | B12f safety ≥ 0.95 on 4/4 vs B10 2/4; time −4.7 % [−5.4, −4.0] vs gated product — `crc-conditional-2026-10-26/` |
| Agent brake on SWE-bench patches | primary + post hoc | 47/143 = full suite; follow-up 108/149, 108/108 without lombok; 33/33 PASS_TO_PASS regressions — `agent-brake-swebench-2026-10-25/FINDINGS.md` |
| Graph precision | done, AI-labelled | 160/160, Wilson [0.954, 1.00] per label — `graph-precision-2026-10-25/` |

Note the pattern that links them: B10's 5 % target is over **all** commits,
so a project where few commits fail can miss many of its failing commits
and still "meet" 5 %. That is why cloudify (46.6 %) and dspace (9.4 %) have
low B10 safety in the confirmatory study, and why B12f conditions on
failing commits. This is a real finding; write it up as the motivation for
B12f.

### 5.3 Comparison with Facebook Predictive Test Selection (Machalica et al., ICSE-SEIP 2019)

PTS learns a model of test failure per change and picks a **global** score
cutoff tuned so that a target share (e.g. 95 %) of failing tests or changes
is caught on validation data. CodeDNA differs in three ways, and B11
measures the difference instead of arguing it:

1. per-commit stop from a calibrated skip-risk estimate (B10) or a
   conformal threshold (B12f), not one global cutoff;
2. a per-project audit gate with a full-suite fallback, so no project gets
   partial selection without its own evidence;
3. it is packaged as an agent-facing brake with must-run tests.

B11 result (4 old projects): inconclusive on safety; B11 held its
test-recall target on 2/4 and change-recall on 0/4, B10 its miss target on
3/4. Rerun on the confirmatory data (§6.1) before the report quotes it as
more than exploratory.

### 5.4 Prior work that must be cited (never claim "first")

- Machalica et al., *Predictive Test Selection*, ICSE-SEIP 2019 (arXiv 1810.05286).
- Angelopoulos et al., *Conformal Risk Control*, ICLR 2024.
- github.com/l-k-1-2/Predictive-test-selection — CRC on missed failing
  tests, Westermo industrial data (test-level loss; ours is commit-level,
  failure-conditional, open Java CI data, used as the brake rule).
- DANTE (ICST 2026), MOX (Electronics 2026), Context-Aware Sequential
  Ranking (Mathematics 2026, same RTPTorrent data, class-conditional
  conformal candidate sets), AutoTCP (EMSE 2026), TDAD (arXiv 2603.17973),
  TestPrune (arXiv 2510.18270), Launchable/Develocity, Mozilla risk-aware
  batching (arXiv 2604.00222), Pan & Pradel ISSTA 2021, Shahini MSR 2025.
  The full list with the 5-property table is in
  `docs/RELATED_WORK_COMPARISON.md` and `REPORT_SYSTEM_DRAFT.md` §2.
- Open item: DANTE's full text was not read (paywall). Check it has no
  stopping rule before the report says so.

---

## 6. Making the novelty claim true end to end (highest priority)

Do these in order. Each step has an acceptance check.

### 6.1 Rerun PTS and B12f on the confirmatory data

1. **Verdict rule (done on this branch).** `scripts/run_crc_check.py`
   required "≥ 3 projects keep the target" whatever the project count. It
   now requires `ceil(0.75 × projects)` (`required_keeps`, `KEEP_SHARE` in
   `config.json`; 3 of 4 as before, 7 of 9), with a test, and takes
   `--protocol PATH` so the addendum is recorded and fingerprinted.
   `run_pts_check.py` uses `rolling.verdict`, whose rule is already
   relative ("more than half"), so it needs no change. The addendum must
   restate the 7-of-9 rule in words.
2. **Write the protocol addendum before running**:
   `docs/CRC_PTS_CONFIRMATORY_PROTOCOL.md`. Fix, in writing:
   - data: the 9 confirmatory datasets, by SHA-256 (the `input_sha256` list
     in the confirmatory `config.json`);
   - B12f success rule for 9 projects (suggestion: safety ≥ 0.95 on at least
     7 of 9 **and** pooled safety interval lower end ≥ 0.90; time
     compared with the gated product);
   - PTS rule: as `docs/PTS_BASELINE_PROTOCOL.md`, with the project count
     rule restated for 9;
   - that the code fingerprints differ from the 4-project runs only by the
     moved-file paths of §3.4;
   - that these 9 projects have been looked at once (for B10), but B12f and
     B11 were fixed before that, so this is a confirmatory test of B12f.
   Commit it, note the commit SHA.
3. Run (laptop, the datasets live there; check the exact folder with
   `dir /s /b experiments\datasets\confirmatory-windowsfix-2026-10-26\dataset.csv`):

   ```powershell
   $env:OMP_NUM_THREADS=1
   $D="experiments\datasets\confirmatory-windowsfix-2026-10-26\datasets"
   $P="docs\CRC_PTS_CONFIRMATORY_PROTOCOL.md"
   .venv\Scripts\python scripts\run_crc_check.py $D --conditional --protocol $P --out experiments\results\crc-conditional-confirmatory-2026-10-27
   .venv\Scripts\python scripts\run_crc_check.py $D --protocol $P --out experiments\results\crc-check-confirmatory-2026-10-27
   .venv\Scripts\python scripts\run_pts_check.py $D --out experiments\results\pts-check-confirmatory-2026-10-27
   ```
   Each run is resumable per project (it reuses `<project>.json`).
4. Write `FINDINGS.md` in each folder by hand from `summary.json`. Add
   report §4.11 (confirmatory B10 + gate) and §4.12 (B12f/B11 confirmatory).
5. **Acceptance:** three new folders, each with `config.json` naming the
   protocol and code SHAs, nine project reports, `summary.md`; the verdicts
   follow the addendum, whatever they are.

### 6.2 Decide whether the product switches to B12f (D-067)

Pre-register the decision in the addendum: *if B12f meets its rule on the
confirmatory data, the live product uses B12f; otherwise it keeps B10 + gate
and the report says B12f did not confirm.* Do not change the rule after
seeing the numbers.

### 6.3 Implement B12f in the live brake — DONE as opt-in (D-068, 2026-10-26)

**Status:** implemented as `method="crc"` (default still `b10`). Code:
`selection/conformal.py` (`stopper`, `failing_commit_threshold`, `MIN_FAILING`),
`codedna_java/live.py` (`METHODS`), `agent/brake.py`, `agent/mcp_server.py`,
`cli.py risk-select --method`, `api/app.py RiskRequest.method`. The method is
reported as `"crc"`, not `"crc_conditional"`. Tests in `test_live_risk.py`,
`test_agent_brake.py`, `test_demo_agent_brake.py` cover every item listed
below. **What is left:** only flipping the default, if D-067 says so (change
the `method` defaults to `"crc"` and update README/AGENT_BRAKE). The original
design is kept for reference:

Files: `backend/codedna/selection/live.py` (shared), `plugins/codedna-java/codedna_java/live.py`
(Java `risk_select`), `backend/codedna/agent/brake.py`, the IDE's Tests view.

Design:

1. In `selection/live.fit_audited` (or a new `fit_conformal`), after the
   50/25/25 split, take the **failing** audit commits, compute per-threshold
   losses `float(missed > 0)` with the same `stopper` as
   `run_crc_check.py` (move `stopper` into `selection/conformal.py` so the
   script and the product share one function), and call
   `conformal.threshold(losses, alpha=risk_target)`.
2. If the result is `FULL` (fewer than 19 failing audit commits, or the
   bound fails at every grid value) → full-suite fallback with that reason.
3. Otherwise select with `RiskPolicy(budget=None, risk_target=threshold)`
   in `recent_failures` order, pinned tests always in.
4. Keep computing the D-041 Wilson evidence and report it, but the
   decision comes from CRC. Report in `risk`: `method: "crc_conditional"`,
   `alpha`, `threshold`, `failing_audit_commits`, the corrected bound at
   the chosen threshold, and the note "bound assumes exchangeable failing
   commits; not a guarantee".
5. Keep B10 available as `method="b10"` (option `--method b10|crc`) so the
   study can still reproduce the old behaviour. Default per §6.2.
6. Record D-067 in `docs/DECISIONS.md`; update `docs/ARCHITECTURE.md`,
   `docs/AGENT_BRAKE.md`, README "Target-validated risk".

Tests to add (`backend/tests/test_live_risk.py`, `test_agent_brake.py`):
- synthetic history with ≥ 19 failing audit commits → `validated_history`,
  `method == "crc_conditional"`, partial selection, pinned tests kept;
- fewer than 19 failing audit commits → full suite with the reason;
- threshold equals what `run_crc_check.evaluate` picks on the same data
  (shared function, same answer);
- brake `plan()` and `check()` on a validated history return a partial plan
  and a verdict (no such test exists today);
- MCP `codedna_plan_tests` response contains `method`, `alpha`, `threshold`.

### 6.4 Make the brake return the plan the study measured

Today `brake.plan()` → `selection.live.recommend()` → `select_tests(..., "all")`
then risk. The dependency plan (what the SWE-bench study scored) is never
in `must_run`. Change `plan()` to return:

- `must_run`: the union of (a) the dependency plan
  `select_tests(repo, base, head, "dependency")`, (b) must-run policy tests,
  (c) on validated history, the CRC/B10 selection; without validated history,
  the full suite as now (D-041 stays: never skip without evidence);
- `structural_plan`: the dependency plan on its own, labelled
  "structural only, no probability", so an agent can run it first for fast
  feedback and the full suite before finishing.

Add a test that `structural_plan` equals `select_tests(..., "dependency")`.
Then the report can say the brake's structural plan is the one the study
measured. Rerunning the SWE-bench study is not needed for that sentence,
but a smoke run on 2–3 instances with `scripts/swebench_brake_study.py run
--instance …` is a good check.

### 6.5 End-to-end proof — DONE (2026-10-26)

**Status:** `python scripts/demo_brake_end_to_end.py DEST --check` prints
`validated_history`, a 1-of-2 plan, `blocked` on the wrong formula, `passed`
on a harmless comment and `end-to-end result: as expected` (real Maven run
in the container). Tested by `test_demo_agent_brake.py` (the Maven one runs
under `--run-maven`). The history is **synthetic**; it proves the mechanism,
not savings. A HikariCP version with real recorded history is optional. The
original plan:

Write `scripts/demo_brake_end_to_end.py` (or extend `demo_agent_brake.py`):

1. copy `examples/sample-java-project` (or HikariCP via
   `scripts/make_hikaricp_demo.py`) into a temp repo;
2. build a recorded history with enough failing commits for the gate
   (D-053 showed ~240 synthetic commits reach `validated_history`; reuse
   the generator in `backend/tests/test_live_risk.py`);
3. make an agent-style edit; call `codedna mcp` over stdio:
   `codedna_plan_tests` must show a **partial** plan with `method`,
   `threshold` and a skip risk; `codedna_check` (with `--allow-build`) must
   give `blocked` for a breaking edit and `passed` for a harmless one;
4. print the plan size vs the full suite.

**Acceptance:** the demo prints `validated_history`, a plan smaller than the
suite, `blocked` on the breaking edit, `passed` on the harmless edit, and
runs offline after the first Maven dependency download. Today
`demo_agent_brake.py --check` only shows the no-history path (verified
2026-10-26: plan = all 2 classes, check = `blocked`).

### 6.6 Optional, if time allows

- Live agent session: Claude Code (existing subscription) with
  `claude mcp add codedna -- codedna mcp --repo <project> --allow-build`
  on 3–5 seeded bugs; record a short video for the defence. Report as a
  demonstration, not a study.
- Brake for Python: give `codedna_python` a `risk_select` (the live
  features in `codedna_java/live.py` are language-neutral except
  `is_java` counts; move them to core with a per-plugin "analysed file"
  test). Until then the brake for Python repos must say "full suite"
  instead of raising (§7, bug 2).

---

## 6b. Improving time savings (all exploratory until confirmed)

**Why savings are small (first read of the saved confirmatory reports,
2026-10-26, descriptive only).** The gate accepted 8 of 44 blocks. It
rejects a block when the audit's miss-rate Wilson upper bound is above 5 %,
when historical failure recall is below 90 %, or when there are fewer than
10 failing audit commits (`selection/validation.py`). Counting the saved
`blocks[*].evidence.reasons` in the nine `<project>.json` files:

| Project | Accepted | Bound > 5 % | Recall < 90 % | < 10 failing | Failing audit commits per block |
|---|---:|---:|---:|---:|---|
| buck | 0/5 | 5 | 1 | 0 | 52, 71, 90, 89, 65 |
| cloudify | 0/5 | 1 | 5 | 0 | 227, 185, 100, 31, 33 |
| deeplearning4j | 1/5 | 4 | 2 | 0 | 105, 93, 65, 62, 47 |
| dspace | 1/5 | 2 | 2 | 1 (+1 fit error) | 28, 50, 30, 6 |
| jetty.project | 0/5 | 5 | 0 | 0 | 24, 29, 32, 30, 34 |
| okhttp | 3/5 | 2 | 1 | 0 | 65, 137, 138, 73, 51 |
| sling | 2/5 | 3 | 1 | 0 | 138, 113, 96, 93, 116 |
| sonarqube | 0/5 | 4 | 5 | 0 | 29, 41, 74, 77, 41 |
| titan | 1/5 | 4 | 1 | 0 | 35, 30, 19, 18, 24 |

So, contrary to the first guess, **sparse failure history is not the main
reason**: only one block had too few failing audit commits. Blocks are
rejected because **B10 itself misses too many failing commits in the
audit** (bound above 5 %, or recall below 90 %). That is the same flaw B12f
was built to fix: B10's 5 % is over all commits, so it stops too early
when failures are common. The most promising lever is therefore T2 (B12f),
which picks the threshold from the failing audit commits directly. More
history (T3) mainly helps projects with few failures. T1 below turns this
quick count into a proper, committed diagnosis. **Never loosen the gate to
get a nicer number.**

Each idea below needs: a protocol file committed first, its own output
folder, the label "exploratory" (old 4 projects) or "confirmatory" (only if
fixed before the data is seen), and the acceptance check listed. The novelty
thread is testing some of these and may send results; check
`experiments/results/` for newer folders before starting one.

| # | Idea | Protocol to write | Commands | Acceptance |
|---|---|---|---|---|
| T1 | **Per-project diagnosis**: for each of the 9 projects, why each block was rejected (too few failing audit commits / bound / recall) | `docs/GATE_DIAGNOSIS_PROTOCOL.md` (descriptive only, no tuning) | new `scripts/diagnose_gate.py <results-folder>` reading the saved per-project JSONs (`blocks[*].evidence.reasons`, `failing_commits`, `miss_upper_bound`) | a table per project: blocks, reason counts, failing audit commits per block; no refit, numbers match the saved reports |
| T2 | **B12f in place of B10 + gate** (failure-conditional CRC threshold; full suite when < 19 failing audit commits) | §6.1 addendum | §6.1 commands | B12f safety ≥ 0.95 on the pre-set share of projects, time vs product reported with interval |
| T3 | **Record as you go** (D-053): how many recorded full-suite runs a project needs before the gate accepts | `docs/HISTORY_GROWTH_PROTOCOL.md`: truncate each project's history at N = 100, 200, 400, 800 commits, run the same gate, report first N that accepts | `scripts/history_growth.py DATASETS --sizes 100 200 400 800 --out experiments/results/history-growth-DATE` | curve of acceptance vs N per project; the report can then tell a user "expect partial selection after about N runs" |
| T4 | **Better test discovery** (Ant, data-driven tests, TestNG) so more of the suite is visible and selectable | `docs/DISCOVERY_ANT_PROTOCOL.md` (pre-register lombok as the target; other repos unchanged) | after implementing, rerun `scripts/swebench_brake_study.py run --data D --work W --out experiments/results/agent-brake-swebench-ant-DATE` | lombok discovered classes > 0; no change in the other repos' counts (regression check); labelled post hoc |
| T5 | **Pool failure evidence across a project's modules or similar projects** for the *audit only* (never for skipping without own evidence) | must be a new pre-registered study; the D-039 transfer study already showed source-only transfer fails | — | only if T1 shows "too few failing audit commits" dominates |
| T6 | **Commit-level grouping**: treat test classes that always fail together as one unit, so the risk estimate is less noisy | protocol first | `history experiment` variant | calibration error (ECE) and gate acceptance on old 4 projects, then confirmatory |

**Already running:** B13 (tuned gate: try thresholds strict to loose with
the same Wilson check, keep the loosest that passes; fixed-sequence
testing) by the novelty thread; see §0.5. Exploratory result on the old 4:
−13.0 pp time vs the gated product, safety −2.6 pp, HikariCP safety 0.914.
`scripts/run_tuned_gate_check.py`, `backend/codedna/selection/tuned.py`.

Order: T1 first (cheap, explains everything else), then T2 (already
built), then T3 (supports the "history builds up" product story), then T4.
T5/T6 only if T1 points there.

---

## 7. Known bugs and weaknesses (verified)

| # | Problem | Where | Fix |
|---|---|---|---|
| 1 | CRC verdict hard-coded "≥ 3 projects keep the target" | `scripts/run_crc_check.py` | **fixed on this branch** (75 % of projects) |
| 2 | `brake.plan(language="python")` raises `SelectionError: Language plugin 'python' does not provide risk selection`; with the default `language="java"` a Python-only repo gets a full-suite plan (correct but by accident) | `selection/live.py:recommend`, `agent/brake.py` | detect the repo's languages; fall back to full suite with a clear reason when a plugin has no `risk_select` |
| 3 | Live risk path refuses any change with a non-Java file ("unsupported non-Java files"), so mixed repos and changes touching `pom.xml`/resources always run the full suite | `codedna_java/live.py` | count build files as "run everything" but let docs/markdown-only changes through; test both |
| 4 | Brake plan ≠ the plan the study measured | `agent/brake.py` | §6.4 |
| 5 | B12f exists only offline | `selection/conformal.py` | §6.3 |
| 6 | `commit_tests` drops the parse cache for every plugin but Java (fixed on this branch for Java only) | `plugins/languages.py` | add an optional `cache` to the Python plugin's `discover_tests` |
| 7 | Ant builds (lombok) are invisible: no tests discovered | `codedna_java/discovery.py` / `build.py` | read `build.xml` `<junit>`/`<batchtest>` include patterns, label results heuristic; or state the limit |
| 8 | Graph precision labels were made by an AI | `experiments/results/graph-precision-2026-10-25/` | a student labels a random 40 of the 160 by hand; report agreement (Cohen's κ) |
| 9 | IDE says "classes" for Python modules | IDE Tests view | wording per plugin `type_kinds` |
| 10 | Desktop installer unsigned and never tried on a clean PC without Python | `ide/electron-app` | §9 |
| 11 | Windows IDE click-through (Java editor, workspace trust prompt, progress popups) not verified | IDE | manual test script in §9 |
| 12 | Catalogue cannot be hosted while the repo is private (D-048) | `website/catalogue/index.json` | a small public repo or GitHub Pages from a public mirror for the catalogue + wheels only |
| 13 | `history-check` features: the live model drops `co_failures` and structural features, so the shipped model is not the study's 19-feature model | `codedna_java/live.py` | documented (D-041); keep saying so in the report |
| 14 | Bootstrap intervals ignore serial dependence; no multiplicity correction | studies | stated in threats; keep it |
| 15 | RTPTorrent CI records are incomplete (graylog2, jOOQ have no failing commits; HikariCP/wicket gate never accepts live) | data | stated; don't loosen the gate |
| 16 | Starlette/httpx deprecation warning in tests | test client | pin or switch to `httpx2` later; harmless |
| 17 | `REPORT_*` drafts still use some pre-split paths; and repo `MEMORY.md` is dated 2026-10-24 and says "Java only", "245 tests" | docs | refresh after merging |

---

## 8. Tests to add (beyond §6)

- **Gate honesty:** history whose failing commits are rare (e.g. 2 % of
  commits fail) must not reach `validated_history` with B12f when the audit
  has < 19 failing commits.
- **Brake on WORKTREE with untracked files** (agents create new files):
  plan includes tests for a new class; `check` runs on the snapshot.
- **MCP protocol:** malformed JSON-RPC, unknown tool, `codedna_check` without
  `--allow-build` → error, repo path outside the served repo → refused.
- **Must-run policy** with a broken `policy.toml` at BASE → fail-safe (full
  suite) and a warning (D-050 says fail-safe; check there is a test).
- **Python plugin:** `src/` layout, namespace packages, relative imports,
  `conftest.py` changes → run everything; pytest parametrised IDs.
- **Mixed Java+Python repo** through `select`, `impact`, `run-tests` and the
  IDE API (one test per path).
- **Plugin manager:** checksum mismatch → refused and rolled back; version
  not pinned → refused; catalogue URL not official → refused (D-020).
- **Windows paths:** long command lines (D-065 covers rev-list; add one for
  `git archive` of a large tree), paths with spaces, CRLF in patches.
- **IDE (Node):** Project history view states (empty, refused run,
  recorded), Language plugins view install confirm/cancel.
- **Reproducibility check:** rerun `scripts/make_study_figures.py` and
  compare SHA-256 manifests (already reproduces byte-for-byte; keep a test).

---

## 9. Improvements (engineering)

1. **One risk interface for all plugins.** Move `LIVE_FEATURES`,
   `prediction_rows` and `recommend` from `codedna_java/live.py` into core;
   plugins provide only "which files I analyse" and "which test a file
   belongs to". Then Python (and later JS) get the brake for free.
2. **Installer check on a clean Windows VM** (or a friend's PC with no
   Python): install `CodeDNA IDE Setup 0.1.0.exe`, open the HikariCP demo,
   run Changes → Tests to run → Impact graph → Run selected tests.
   Write the result in `docs/IMPLEMENTATION_HANDOFF.md`.
3. **Manual IDE test script** (`docs/IDE_MANUAL_TEST.md`): 15 steps covering
   every view and shortcut (`Ctrl+Shift+Alt+D/T/G/H/R`), the trust prompt,
   build consent, cancel, a failing run, a Python project.
4. **Performance:** `select_tests` parses BASE and HEAD fully; the cache
   helps repeated calls. Measure analysis time on HikariCP and lucene and
   report it (the brake study logged per-pair seconds).
5. **Error messages for agents:** every fallback reason should say what to
   do next ("record 200 more full-suite runs", "install codedna-python").
6. **CI:** add a job that runs `scripts/run_crc_check.py` on a tiny
   synthetic dataset end to end (catches import breakage like §3.4).
7. **Gradle per-test coverage** (currently Maven only).
8. **Method-level call edges** (D-010) if a cheap type resolver appears;
   otherwise keep the limit.

---

## 10. The report

### 10.1 What exists

- `docs/REPORT_SYSTEM_DRAFT.md`: introduction, related work (25 refs),
  requirements, design, implementation, testing, limitations/future work.
- `docs/REPORT_DRAFT.md`: evaluation RQ1–RQ5, §4.6–4.10, threats, conclusion.
- `docs/REPORT_AGENT_BRAKE.md`: the brake chapter.
- `docs/CONFIRMATORY_RESULTS_2026-10-26.md`: confirmatory write-up + figures.

### 10.2 What is left

1. **Abstract** (≤ 300 words) with the honest headline of §0.
2. **Evaluation §4.11 confirmatory** (from PR #20) and **§4.12 B12f/B11
   confirmatory** (§6.1). Rewrite §6 Conclusion: safe and honest, B10 ≈ B3
   confirmed, the gate holds, small savings, B12f result.
3. **Agent brake chapter**: add the end-to-end demo (§6.5) and, if built,
   the B12f product change (D-067).
4. **Python plugin section** in Design/Implementation (D-060) as evidence
   that the plugin interface generalises.
5. **User guide appendix** from README + `docs/AGENT_BRAKE.md`.
6. **Testing chapter numbers**: replace old counts with the real
   `pytest --run-maven` output on `main` after merging.
7. **Figures**: study11 figures (`scripts/make_study_figures.py`),
   confirmatory figures (`docs/figures/confirmatory-2026-10-26/`), an
   architecture diagram, IDE screenshots (`docs/ide-screenshot.png` is old:
   retake), brake sequence diagram.
8. **Threats**: serial dependence, flaky CI failures, AI-made graph labels
   (until §7 bug 8 is done), post-hoc D-064, exchangeability for CRC,
   recorded test time ≠ CI wall time.
9. **Citations**: §5.4 list; check every reference resolves.
10. Export: Markdown → HTML (`markdown` package) → PDF with Chrome headless
    (`chrome.exe --headless=new --no-pdf-header-footer --print-to-pdf=...`),
    or into the university template.

Rules for the report: every number traceable to a file; primary vs post-hoc
labelled; never "first"; never "guarantee".

---

## 11. Defence preparation (target ~May 2027; finish coding much earlier)

### 11.1 Demo script (10 minutes)

1. IDE opens on the HikariCP demo repo (`scripts/make_hikaricp_demo.py`).
2. *Changes* → *Impact graph*: changed class, confirmed vs heuristic edges.
3. *Tests to run*: full suite with "risk unvalidated" — explain why.
4. *History replay*: CodeDNA vs run-everything vs simple rules on saved
   study commits; show estimated vs observed risk.
5. Agent brake: Claude Code or the demo script calls `codedna_plan_tests`,
   then `codedna_check` → `blocked` on a seeded bug.
6. End-to-end validated-history demo (§6.5): partial plan with threshold.
7. One slide: confirmatory result (B10 ≈ B3, gate safe, savings small) and
   the B12f result.

Have a **recorded video** of the whole demo and an **offline** copy (Maven
dependencies cached in the local repository folder; demo repos
pre-built), in case the venue network or the laptop fails.

### 11.2 Questions to rehearse

- "Your method doesn't beat a simple rule. What is the contribution?" →
  the gate and the brake: deciding *whether* skipping is safe, measured on
  9 new projects; B12f bounds misses among failing commits.
- "How is this different from Facebook PTS?" → §5.3, and B11 numbers.
- "Is the 5 % a guarantee?" → no; exchangeability, audited not assumed.
- "Why should an agent trust `passed`?" → it covers the listed tests only;
  the full suite runs when evidence is missing.
- "Why Java, and does it generalise?" → plugin interface; Python plugin.
- "Did AI write this?" → be open about AI assistance; show tests, protocols
  committed before runs, and the student-checked graph labels.

---

## 12. Future features (after the core work)

1. **More language plugins**: JavaScript/TypeScript next (tree-sitter,
   Jest/Vitest), then Kotlin (shares the JVM/Gradle runner). Each must emit
   the shared graph schema and get its own catalogue entry.
2. **Security features after the defence**: plug into the must-run policy
   hook (D-050) — e.g. always run tests that touch auth/crypto paths;
   "security" stays future work in the report.
3. **GitHub Action / PR bot**: comment on a PR with the plan, the skip risk
   and the verdict; the roadmap's missing M6 "PR demonstration".
4. **Online calibration** that adapts as new runs are recorded, with drift
   detection that drops back to full suite.
5. **UI polish** (owner's job later): theme, layout, icons; consistent
   wording across views.
6. **Website** (Amna): hosting, docs pages, catalogue page reading
   `website/catalogue/index.json`.
7. **Catalogue hosting** for plugin wheels (public repo or Pages), then
   in-app install end to end.
8. **File-level co-change fallback** for languages without a plugin,
   always labelled heuristic.

---

## 13. Command cheat sheet

```powershell
# Windows laptop, repo root
.venv\Scripts\python -m pip install -e ".[ml,api,dev]" -e plugins\codedna-java -e plugins\codedna-python
.venv\Scripts\python -m pytest --run-maven -q
& "C:\Users\hp\.codex\tools\graphify\Scripts\graphify.exe" query "how does the live gate decide"
& "C:\Users\hp\.codex\tools\graphify\Scripts\graphify.exe" update .
start.bat
$env:PYTHONIOENCODING="utf-8"      # for scripts that print − or Δ
```

```bash
# Linux/macOS or cloud container
pip install -e ".[ml,api,dev]" -e plugins/codedna-java -e plugins/codedna-python
python -m pytest --run-maven
codedna analyze --repo R --base B --head H
codedna impact  --repo R --base B --head H
codedna select  --repo R --base B --head H --strategy dependency
codedna risk-select --repo R --base B --head H
codedna mcp --repo R [--allow-build]
codedna history record ...          # add a full-suite run to .codedna/history.csv
python scripts/demo_agent_brake.py /tmp/brake-demo --check
python scripts/make_study_figures.py --study experiments/results/study11-2026-10-21
```

Graphify off the laptop: `pip install graphifyy` (two y's), then
`graphify update .`, `graphify query "<question>"`. No API key needed for
code-only graphs.

---

## 14. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| B12f does not confirm on the 9 projects | medium | pre-registered; report it honestly; the gate + brake story still stands |
| GPT edits leak into main | medium | §1.1, §4.1; review every laptop diff against PR #17 |
| Laptop dies / OneDrive sync corrupts data | medium | results are in Git; datasets are rebuildable (hours); keep the backup folder |
| Scope sprawl (website, plugins, UI) delays the report | high | §6 and §10 first; product work only after |
| Defence demo fails live | medium | video + offline repos (§11.1) |
| Supervisor questions novelty | medium | §5, §11.2; cite PTS and CRC prior art openly |
| AI budget runs out | high (stated) | this document; every task has commands and acceptance checks |
| Installer fails on examiner's PC | medium | demo from the developer setup; installer is a bonus |

---

## 15. "Done" checklist

- [ ] §3: all PRs merged in order, #8 closed, `main` green, laptop pulled.
- [ ] §4: GPT edits stashed, 97c3be7 handled, plugins reinstalled, IDE rebuilt.
- [ ] §6.1: CRC/PTS confirmatory reruns with the addendum and fixed verdict rule.
- [x] §6.3: B12f live as opt-in `method="crc"` with tests (D-068).
- [ ] §6.2: D-067 decided; if positive, flip the default to `crc`.
- [ ] §6.4: brake returns the measured structural plan.
- [x] §6.5: end-to-end demo prints `validated_history`, partial plan, `blocked`, `passed`.
- [ ] §7: bugs 1–4 fixed; others fixed or stated as limits.
- [ ] Graph labels spot-checked by a student.
- [ ] Clean-PC installer test and IDE manual test written up.
- [ ] Report complete (§10), numbers re-checked against files.
- [ ] Defence video recorded; offline demo works.

---

## 16. Where things live

| Path | What |
|---|---|
| `backend/codedna/` | core: `git_analysis`, `impact_analysis`, `selection` (`baselines`, `risk`, `validation`, `live`, `conformal`, `pts`, `policy`), `test_history`, `models`, `calibration`, `plugins` (`registry`, `languages`, `manager`, `catalogue`), `agent` (`brake`, `mcp_server`), `api`, `cli.py` |
| `plugins/codedna-java/codedna_java/` | parser, mapping, builder, references, discovery, build, maven, reports, live, plugin |
| `plugins/codedna-python/codedna_python/` | Python plugin |
| `backend/tests/` | pytest suite (`conftest.py` adds `--run-maven`) |
| `ide/` | Theia extension + Electron app |
| `website/` | static site + catalogue JSON (Amna's) |
| `scripts/` | studies, demos, desktop bundle builder |
| `experiments/results/` | every saved result (source of every number) |
| `docs/` | spec, architecture, decisions, roadmap, protocols, report drafts, this file |
| `MEMORY.md` | repo handoff notes (refresh after merging) |

---

## 17. Ready-to-paste prompt for Codex (or any coding agent)

Paste this as the first message of every new Codex session on the laptop.
Replace `<TASK>` with one item from §15 or §6/§6b/§7.

```text
You are working on CodeDNA, a university final-year project, in
C:\Users\hp\OneDrive\Documents\GitHub\codedna. You cannot see GitHub, so the
local tree may be stale. Follow these rules exactly.

Before anything else:
1. Run `git status --short`. If it shows any modified or untracked files
   that you did not create in this session, STOP and report them. Do not
   edit, commit or stash them.
2. Run `git fetch origin` and `git switch main` and `git pull --ff-only origin main`.
   If the pull fails, STOP and report the error.
3. Read, in order: AGENTS.md, MEMORY.md, docs/HANDOFF.md (the full plan),
   docs/ROADMAP.md, and the end of docs/DECISIONS.md.
4. Find the highest decision number in docs/DECISIONS.md (`D-0NN`). Your new
   decision, if any, is the next number. Never reuse a number.

Work rules:
- One task, one branch, one pull request. Create the branch from the
  updated main: `git switch -c codex/<short-task-name>`.
- Never commit to main directly. Never force-push. Never rewrite history.
- Never reintroduce these bugs: (a) dropping test runs whose build exit
  code is non-zero (Maven/Gradle exit 1 when a test fails; those runs ARE
  the failure evidence); (b) writing a second history file or overwriting
  .codedna/history.csv outside test_history/recording.py; (c) editing
  .git/info/exclude. backend/tests/test_project_history.py guards these;
  it must keep passing.
- Java code lives in plugins/codedna-java/codedna_java/, Python plugin code
  in plugins/codedna-python/codedna_python/. The core (backend/codedna/)
  must not import Java-specific modules.
- For any experiment: write the protocol file in docs/ and commit it BEFORE
  running; use a new output folder under experiments/results/; never
  overwrite results; label post-hoc work as post hoc. Never invent numbers.
- Never pass --allow-build on the user's behalf except for the project's
  own test suite and demo repos.
- Write tests for every change (temporary Git repos, no internet).

Before you say you are done:
- Run `.venv\Scripts\python -m pytest --run-maven -q` (set up Java/Maven
  from C:/Users/hp/.codex/tools/java-maven.json as described in MEMORY.md).
  Report the exact passed/failed/skipped counts. If Maven cannot run, say
  "Maven tests unverified" instead of skipping silently.
- If you changed ide/: `cd ide; npm run build:extension; npm test --workspace codedna-extension`.
- Update docs/DECISIONS.md (new D-number), docs/ARCHITECTURE.md and README
  if behaviour changed.
- Run `& "C:\Users\hp\.codex\tools\graphify\Scripts\graphify.exe" update .`
- Commit on your branch with a clear message, then tell the user the branch
  name so they can push it and open a PR. Do not merge anything.

Your task: <TASK>
```

Suggested first tasks for Codex, in order (each is self-contained):

1. (§7 bug 1 is already fixed on the integration branch.)
2. §6b T1: `scripts/diagnose_gate.py` (read-only analysis of saved results).
3. §6.1 step 2: draft `docs/CRC_PTS_CONFIRMATORY_PROTOCOL.md` for the user
   to approve, then (separate task) run the three reruns.
4. §6.4: brake `structural_plan` + tests.
5. §6.3: B12f in the live product: DONE as opt-in (D-068). Only flip the default if §6.2 says so.
6. §6.5: end-to-end demo script: DONE (`scripts/demo_brake_end_to_end.py`).
7. §7 bug 2 and 3: Python/mixed-repo brake fallbacks.

### 17.1 Ready-to-paste prompt for GPT/Codex: do the merges

Paste this to Codex on the laptop. It merges everything through the one
integration branch with plain Git (Codex cannot use the GitHub website;
pushing the merge to `main` makes GitHub mark PR #21 and #15–#20 as merged).

```text
Task: merge CodeDNA's open work into main. Repo:
C:\Users\hp\OneDrive\Documents\GitHub\codedna. Stop and report at the first
step that does not look as described. Never use reset --hard, clean,
checkout -- ., stash pop, rebase or force push. Never commit any file you
did not create in this task.

1. Wait until no CodeDNA analysis job is running (check the PowerShell
   windows; the B13/B12f/B11 run in C:\Users\hp\codedna-b13 must be finished
   and pushed). Do not touch C:\Users\hp\codedna-b13.
2. In the repo: `git status --short`. If it lists modified/untracked files
   (the old GPT edits), set them aside, keeping the confirmatory results:
   git stash push -u -m "GPT laptop edits, set aside 2026-10-26" -- . ":(exclude)experiments/results/rolling-evidence-confirmatory-windowsfix-2026-10-26"
   Then `git status --short` must be empty or show only that results folder.
   Never pop or apply this stash.
3. `git fetch origin`
4. `git log --oneline origin/main..main` — if it lists 97c3be7 (graphify
   output, email blocked by GitHub), run
   `git branch keep/graphify-97c3be7 97c3be7` then `git reset --keep origin/main`.
   If it lists anything else, STOP and report.
5. `git switch main` then `git merge --ff-only origin/main`.
6. Check the integration branch is up to date with every PR branch. For each
   of: claude/project-thread-dfhix3, claude/project-thread-71arlo,
   claude/java-plugin-split, claude/project-thread-info38,
   claude/python-plugin, claude/confirmatory-results-2026-10-26 run
   `git merge-base --is-ancestor origin/<branch> origin/claude/project-thread-lo3rpw; echo $LASTEXITCODE`
   0 = included. If any prints 1, that branch got new commits: make a local
   branch `git switch -c integrate-update origin/claude/project-thread-lo3rpw`,
   `git merge --no-ff origin/<branch>`, resolve conflicts following
   docs/HANDOFF.md §3.3/§3.4 (on 71arlo results: keep the integration
   branch's run_crc_check.py and the `codedna_java.live` imports), run the
   tests (step 8), and use `integrate-update` instead of
   origin/claude/project-thread-lo3rpw in step 7.
7. `git merge --no-ff origin/claude/project-thread-lo3rpw -m "Merge PR #21: integrate PRs #15-#20, fixes, handoff blueprint"`
   (no conflicts are expected; if there are, STOP and report).
8. Reinstall and test:
   .venv\Scripts\python -m pip install -e ".[ml,api,dev]" -e plugins\codedna-java -e plugins\codedna-python
   .venv\Scripts\python -m pytest --run-maven -q
   (set up Java/Maven from C:/Users/hp/.codex/tools/java-maven.json as in
   MEMORY.md). Expect about 475+ passed, 0 failed. If anything fails, STOP,
   do not push, report the failures.
9. `git push origin main` (normal push, no force). If GitHub refuses it
   (branch protection), push the merge to a branch instead and report:
   `git push origin main:claude/merge-21-local`.
10. Close PR #8 on GitHub (the owner can do this by hand: "Included in #16").
11. Rebuild: `start.bat` (installs plugins, rebuilds the IDE), then
    `& "C:\Users\hp\.codex\tools\graphify\Scripts\graphify.exe" update .`
    and commit graphify-out with the owner's GitHub no-reply email.
12. Report: the pushed SHA of main, `git log --oneline -8`, the pytest
    summary line, and `git stash list`.
```
