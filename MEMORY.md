# MEMORY.md: handoff notes for the next agent

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
