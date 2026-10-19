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

## Milestone 3 — Test mapping ⏳ (next)

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
