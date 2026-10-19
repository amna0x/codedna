# CodeDNA — Roadmap

Status legend: ✅ done · 🔄 in progress · ⏳ not started

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

## Milestone 1 — Git and Java change analysis 🔄

- ✅ `codedna analyze --repo --base --head` with file-level JSON
- ✅ Added / deleted / modified / renamed / non-Java / empty diff / spaces in
  names / binary files, with tests
- ⏳ Choose Java parser (Tree-sitter Java first; record in DECISIONS.md)
- ⏳ Map changed line ranges to classes, methods, constructors, fields
- ⏳ Report changes outside methods (imports, fields, annotations) explicitly
- ⏳ `unresolved` entries for syntax errors / unsupported constructs
- ⏳ Tests: overloads, constructors, nested classes, multiple methods, comment-
  and formatting-only changes, multi-method spans, method deletion, syntax
  errors

## Milestone 2 — Dependency graph ⏳

Package/file/class-level relationships first; method-level only where
resolution is reliable. Stable node IDs, typed + labelled edges
(confirmed/heuristic/unresolved), impact traversal, explanation paths, JSON
export.

## Milestone 3 — Test mapping ⏳

JUnit test discovery, Maven test execution (in a sandboxed, user-approved
way), JaCoCo coverage import, test↔code mapping, dependency-only baseline (B4)
vs retest-all (B0).

## Milestone 4 — History and predictive ranking ⏳

History mining, historical test results and durations, features, simple
historical baselines (B2, B3, B5), logistic regression, gradient boosting.

## Milestone 5 — Research contribution ⏳

Calibration, risk policies, fallback to broader/full suite, risk–cost
experiments, ablations, reproducible results (B6–B9).

## Milestone 6 — Visualization and FYP demo ⏳

React + TypeScript + Vite + Cytoscape.js dashboard over the analysis JSON.
May start in parallel once the graph JSON format is stable.
