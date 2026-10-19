# CodeDNA — Roadmap

Status legend: ✅ done · 🔄 in progress · ⏳ not started

CodeDNA has two tracks (D-017):

- **Research track (priority):** Java change-impact analysis, test
  selection and calibrated risk — Milestones 0–5. This is what the FYP is
  evaluated on.
- **Product track:** the CodeDNA IDE (built on Eclipse Theia), language
  plugins, and a platform website with a plugin catalogue — Milestones 6–7
  and the plugin refactor in Milestone 4. It must not delay Milestones 4–5.

Java stays the only supported language until Milestone 5 is complete.

## Milestone 0 — Repository bootstrap ✅

- ✅ Python package + `pyproject.toml`, editable install
- ✅ AGENTS.md, README.md, docs/
- ✅ pytest suite
- ✅ GitHub Actions workflow (Python tests on Ubuntu + Windows; Maven build of
  the sample project)
- ✅ Example Java/Maven/JUnit 5 project (`examples/sample-java-project`)
- ⚠️ Maven is not installed on the original development laptop; the sample
  project's Maven build is verified in CI only. Main sources compile with
  `javac` locally.

## Milestone 1 — Git and Java change analysis ✅

- ✅ `codedna analyze --repo --base --head` with file-level JSON
- ✅ Added / deleted / modified / renamed / non-Java / empty diff / spaces in
  names / binary files, with tests
- ✅ Java parser chosen: Tree-sitter Java (D-008)
- ✅ Map changed line ranges to classes, methods, constructors, fields
  (`analysis_level: "method"`, default)
- ✅ Report changes outside methods (imports, package, type annotations /
  header, comments) explicitly
- ✅ `unresolved` entries + warnings for syntax errors / unsupported constructs
- ✅ Tests: overloads, constructors, nested classes, multiple methods, comment-
  and formatting-only changes, multi-method spans, method deletion, added /
  deleted / renamed files, syntax errors, CRLF files, demo repository

## Milestone 2 — Dependency graph ✅

- ✅ Stable node IDs: `package:`, `file:`, `type:`, `member:` (member IDs match
  Milestone 1 declaration IDs)
- ✅ Typed edges: `contains`, `extends`, `implements`, `uses`, `imports`,
  `static_access`; each `confirmed` or `heuristic` with file:line evidence
- ✅ Unresolved references listed (never turned into edges), unresolved rate
  in `stats`
- ✅ `codedna graph` JSON export
- ✅ `codedna impact`: reverse-dependency traversal over merged BASE+HEAD
  graphs, confirmed-first BFS, explanation paths, `--max-depth`,
  `--confirmed-only`
- ✅ Class-level dependency-only candidate tests (preview of baseline B4)
- ⏳ Method-level call edges (deferred: needs type resolution; see D-010)
- ⏳ Manual precision check of extracted edges on a real project (needed for
  the "graph correctness" metric)

## Milestone 3 — Test mapping ✅

- ✅ Static JUnit 4/5 discovery (`codedna tests`): direct, `@Nested` and
  inherited test methods, Surefire default-include check, TestNG flagged
- ✅ Maven execution only with `--allow-build`, on a `git archive` export;
  JaCoCo attached from the command line (D-014)
- ✅ Surefire + JaCoCo XML parsers; per-test-class coverage map onto graph IDs
  (D-015)
- ✅ Baselines: retest-all (B0), dependency-only (B4), coverage-based
  (Ekstazi-style, method level); non-Java fallback (D-016)
- ✅ `codedna compare`: selection ratio, estimated time, failures caught/missed
  against a full HEAD run
- ✅ Offline tests with a fake `mvn`; real Maven/JaCoCo end-to-end test in CI
- ⚠️ Real Maven flow not yet run on the development laptop (Maven missing)
- ⏳ Multi-module Maven, Gradle, custom Surefire includes
- ⏳ Evaluate B0/B4/coverage over many commits of a real project (needs
  Milestone 4 history tooling)

## Milestone 4 — History and predictive ranking 🔄 (tooling done)

- ✅ SQLite history store (D-021); `history mine` (first-parent, numstat),
  `history import` (results.json), `history collect --allow-build` (full
  suite per commit), `history status`
- ✅ Leakage-free (commit, test) features: change size, test changed,
  structural (impact distance / confirmed path), history (failures, recency,
  durations, co-failures) (D-023)
- ✅ Baselines B1 random, B2 shortest-first, B3 recent failures, B5 failure
  history; logistic regression and gradient boosting (D-022)
- ✅ `history evaluate`: chronological 60/20/20 split; APFD, APFDc,
  recall at 25 %/50 % time, time to first failure, PR-AUC, Brier;
  `--dataset-csv` export
- ✅ Tests on synthetic histories only — **no research numbers exist yet**
- ⏳ **Choose the study project / datasets** (DATASET_PLAN.md) and collect or
  import real results — blocks every real evaluation
- ⏳ Run `history evaluate` on real data and record results under
  `experiments/results/` with dataset versions and commands

Product track, alongside:

- ✅ Language-plugin interface, registry (`codedna.languages` entry points)
  and built-in Java plugin; core impact/selection/collection go through it;
  `codedna plugins` (D-018, D-024)
- ⏳ Physically move Java code into a separate `codedna-java` package
  (Milestone 7)

## Milestone 5 — Research contribution 🔄 (tooling done)

- ✅ Calibration: none / Platt / isotonic fitted on the validation split;
  Brier, ECE, reliability bins (D-025)
- ✅ Risk-aware selection: risk-per-second greedy under a time budget,
  estimated skip risk, risk target, uncertainty fallback with reasons (D-026)
- ✅ `history experiment`: B0, B4, B6, B7, B8, B9 on the test split;
  budget and risk-target sweeps (risk–coverage); feature-group ablations;
  reproducibility block (dataset SHA-256, seed, versions) (D-027)
- ✅ Tests on synthetic data only — **no research numbers exist yet**
- ⏳ Run on real study data (blocked on the study project, see Milestone 4),
  store reports in `experiments/results/`, write up RQ1–RQ5 honestly,
  including null or negative results
- ⏳ Cross-project / multiple-seed runs for robustness

## Milestone 6 — CodeDNA IDE and FYP demo ⏳

Replaces the standalone React dashboard: the same views live inside the IDE.
May start in parallel (Student C) once the analysis JSON formats are stable.

- ✅ Local API (FastAPI): `codedna serve`; analyze / graph / impact / tests /
  select / compare / run-tests / plugins / capabilities; loopback only,
  session token, Host check, build opt-in (D-019, D-028)
- ⏳ API: per-commit risk scores for the Tests view (needs a trained model
  stored per repository), progress for long runs, run only selected tests
- ⏳ CodeDNA IDE built on Eclipse Theia, branded, desktop (Electron) build
  (D-019); Java editing through existing open-source Java extensions
- ⏳ CodeDNA panels: changed methods, impacted classes with explanation paths,
  recommended tests with risk, "run selected tests", Cytoscape.js graph view
  (confirmed / heuristic / unresolved styling)
- ⏳ GitHub PR demonstration and final experimental report

## Milestone 7 — Platform website and plugin distribution ⏳

- ⏳ Static platform website: project info, IDE downloads, documentation,
  plugin catalogue (D-020)
- ⏳ Plugin catalogue index (versioned JSON) shared by the website and the IDE
- ⏳ In-app plugin manager: browse, install, update, remove — official
  catalogue only, checksums verified, versions pinned (D-020)
- ⏳ Package the Java plugin through the catalogue

## Later (only if Milestones 4–7 are on track)

- ⏳ Second language plugin (e.g. Python or JavaScript) to show the plugin
  interface generalises
- ⏳ File-level history fallback (co-change) for languages without a plugin,
  always labelled heuristic
