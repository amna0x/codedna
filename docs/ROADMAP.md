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
- ✅ Portable JDK 17 and Maven 3.10 are installed on the current Windows
  laptop; the real sample-project Maven/JaCoCo integration test passed locally.

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
- ✅ Real Maven/JaCoCo flow verified locally on Windows (JDK 17, Maven 3.10);
  the full suite includes the integration test with `--run-maven`.
- ✅ Multi-module Maven, Gradle, custom Surefire includes (D-045; static
  layout, per-test coverage still single-module Maven only)
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
- ✅ Offline tests on synthetic histories; real study results are recorded below
- ✅ Study dataset chosen: RTPTorrent v1.1 (D-032), downloaded and verified;
  Defects4J and Commons CSV remain secondary options (DATASET_PLAN.md)
- ✅ `history import-rtptorrent`: imports one project's tested commits,
  changed files and per-job test-class results; bare-repository support;
  HikariCP imported (1,427 tested commits, 123 with failures)
- ✅ First real run on HikariCP (`experiments/results/hikaricp-2026-10-21`)
- ✅ Study over six RTPTorrent projects × five seeds with separated fallback
  triggers B9r / B9n (D-034) — `experiments/results/study-2026-10-21`
- ✅ Study over eleven projects × five seeds with cost-matched comparisons
  and hierarchical bootstrap intervals (D-035) —
  `experiments/results/study11-2026-10-21/FINDINGS.md`: calibration robustly
  improves reliability; fallback gives no reliable gain over the same test
  time (one project excepted); ML ordering does not beat simple rules
- ✅ Hybrid B10 (rules order, calibrated stopping; D-036): never worse than
  rules or calibrated ML at the same time, meets its 5 % miss target on 10 of
  11 projects; pooled gain not statistically clear
- ✅ Class-weight check for RQ3 (D-037): an unweighted model is nearly as
  well calibrated as the calibrated class-weighted one; calibration mainly
  undoes class weighting in ECE, but B10 needs it to keep its risk target
- 🔄 Evaluation chapter draft (RQ1–RQ5): `docs/REPORT_DRAFT.md`

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
- ✅ Offline tests on synthetic histories and saved-report figure exports
- ✅ Real study over eleven projects × five seeds, with reports under
  `experiments/results/study11-2026-10-21/`
- ✅ Reproducible RQ1–RQ5 figures and SHA-256 input/output manifest
  (`scripts/make_study_figures.py`, D-038); no experiment rerun required
- 🔄 Finish the evaluation chapter and remaining report, including null and
  negative results; supervisor review of the thesis claim remains outstanding
- ✅ Multi-project / multiple-seed robustness: eleven projects, each trained
  and evaluated separately with five seeds on a fixed chronological split.
  Cross-project transfer check completed separately (D-039): four projects,
  twelve directions, five seeds, plus fresh within-project controls. Seven of
  nine calibrated directions meet the observed 5% miss target; three other
  directions lack source calibration. General transfer is not established.
  See `experiments/results/cross-project-2026-10-24/FINDINGS.md`.

- ✅ Exploratory DANTE-history-score adaptation/B10 extension: four projects ×
  five seeds; all calibrated observed targets hold, but matched-time safety
  difference +0.0460 [-0.0500, 0.2806] is not significant. Full-DANTE reproduction
  and general superiority are not claimed (D-040).
- 🔄 Rolling-origin evidence study with pre-fixed rules (D-042): on the four
  inspected projects B10 shows no meaningful safety difference from matched B3;
  the gate accepts few blocks but those miss rarely. New-project confirmation
  pending data access: `scripts/prepare_confirmatory.py` fetches, imports and
  builds the projects outside study11 on a machine that reaches Zenodo.

## Milestone 6 — CodeDNA IDE and FYP demo ⏳

Replaces the standalone React dashboard: the same views live inside the IDE.
May start in parallel (Student C) once the analysis JSON formats are stable.

- ✅ Local API (FastAPI): `codedna serve`; analyze / graph / impact / tests /
  select / compare / run-tests / plugins / capabilities; loopback only,
  session token, Host check, build opt-in (D-019, D-028)
- ✅ API/CLI: target-bound risk selection, 50/25/25 fit/calibrate/audit gate,
  explicit full-suite fallback, recomputed selected-test execution (D-041).
  No serialized model is loaded; long runs show elapsed-time progress (D-044).
- ✅ CodeDNA IDE skeleton: Theia 1.76.0 + Electron 42 desktop app in `ide/`
  (D-029); builds and runs on Windows; extension compiled in CI
- ✅ "Changed code" and "Recommended tests" views talking to the core through
  a Theia backend service that starts `codedna serve` (token stays in the
  backend); verified end to end on the demo repository
- ✅ CodeDNA Dark theme as the default (D-030), revised for newcomers:
  calm neutral look, plain-language "Changes" / "Tests to run" views,
  shared "Compare" picker, friendly errors, first-run guide (D-031)
- ✅ Impact graph view (Cytoscape.js, D-043): changed code → affected parts →
  tests, confidence-labelled edges, click-to-explain paths
- 🔄 Java editor support, progress notifications, Windows installer (D-044);
  needs a Windows build check
- ✅ Uncommitted-change analysis: `WORKTREE` revision + "My uncommitted
  changes" in the IDE (D-046)
- ⏳ GitHub PR demonstration and final experimental report

- ✅ IDE: risk status/audit evidence, explicit execution confirmation, actual
  selected-test statuses and logs; structural selection carries no probability
  guarantee. Native build validation is recorded in the implementation handoff.

## Milestone 7 — Platform website and plugin distribution ⏳

- ✅ Static platform website in `website/`: home, docs, catalogue page (D-047);
  hosting (e.g. GitHub Pages) still to switch on
- ✅ Plugin catalogue index `website/catalogue/index.json` with a core
  validator (`codedna.plugins.catalogue`: pinned, SHA-256, official URLs)
- ⏳ In-app plugin manager: browse, install, update, remove — official
  catalogue only, checksums verified, versions pinned (D-020)
- ⏳ Package the Java plugin through the catalogue

## Later (only if Milestones 4–7 are on track)

- ⏳ Second language plugin (e.g. Python or JavaScript) to show the plugin
  interface generalises
- ⏳ File-level history fallback (co-change) for languages without a plugin,
  always labelled heuristic
