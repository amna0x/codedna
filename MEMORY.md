# MEMORY.md: handoff notes for the next agent

Read this first, then AGENTS.md (rules), docs/ROADMAP.md (status) and
docs/DECISIONS.md (D-001 to D-041, why things are the way they are).
Last updated: 2026-10-24 (DANTE-history extension, target audit gate and live IDE execution).

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
  Run `python -m pytest --run-maven`: 245 passed, zero skipped locally on
  2026-10-24. The real Maven/JUnit/JaCoCo integration test passed.
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
