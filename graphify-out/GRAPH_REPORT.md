# Graph Report - codedna  (2026-10-24)

## Corpus Check
- Large corpus: 290 files · ~970,447 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder.

## Summary
- 1307 nodes · 3090 edges · 59 communities (52 shown, 7 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 148 edges (avg confidence: 0.91)
- Token cost: 199,342 input · 0 output

## Community Hubs (Navigation)
- Java Reference Extraction
- Dependency Graph Builder
- Local HTTP API
- Study Runner Scripts
- Language Plugin Interface
- Graph CLI Commands
- Git Blob Reading
- Git Change Extraction Tests
- Chronological Evaluation
- Probability Calibration
- IDE Extension Dependencies
- Change Analysis Mapping
- Experiment Cost Matching
- Surefire JaCoCo Parsing
- JUnit Test Discovery
- Feature Dataset Building
- History Store
- IDE Protocol Types
- Selection Policies Ablations
- Sample Java Project
- Test Selection Baselines
- IDE Change View Rendering
- TypeScript Config
- RTPTorrent Importer
- Architecture Modules Docs
- Research Findings Decisions
- Electron App Dependencies
- Maven Code Index
- Strategy Comparison
- Maven Test Runner
- History Mining Collection
- IDE Comparison Presets
- IDE Contributions Wiring
- IDE Workspace Package
- Commit Mining Store
- IDE Screenshot UI
- CI And Platform Docs
- CLI Argument Parser
- Extension Package Deps
- Agent Rules Tracks
- Tests View Widget
- CodeDNA Theme
- Test Result Models
- Prior Art Datasets
- Select Compare Endpoints
- Study Protocol Findings
- Theia App Config
- Esbuild Bundle
- Change View Widget
- Editor Preferences
- Package Scripts
- Electron Dev Deps
- API Package
- Calibration Package
- Models Package
- Test History Package
- Test Mapping Package
- Python Project Config
- Sample Maven POM

## God Nodes (most connected - your core abstractions)
1. `main()` - 47 edges
2. `HistoryStore` - 43 edges
3. `extract_changes()` - 36 edges
4. `create_app()` - 35 edges
5. `select_tests()` - 33 edges
6. `Row` - 33 edges
7. `run_maven_tests()` - 31 edges
8. `compute_impact()` - 30 edges
9. `run_experiment()` - 28 edges
10. `Node` - 27 edges

## Surprising Connections (you probably didn't know these)
- `Evaluation chapter draft` --semantically_similar_to--> `Thesis claim: honest checked risk estimates as stopping rule at equal test time`  [INFERRED] [semantically similar]
  docs/REPORT_DRAFT.md → MEMORY.md
- `Tests to run view` --references--> `B10 hybrid policy (rules order + calibrated stopping at 5% risk)`  [INFERRED]
  ide/README.md → docs/DECISIONS.md
- `_reachability()` --calls--> `chronological_split()`  [INFERRED]
  scripts/run_study.py → backend/codedna/models/evaluate.py
- `run_project()` --calls--> `evaluate()`  [INFERRED]
  scripts/run_study.py → backend/codedna/models/evaluate.py
- `run_project()` --calls--> `run_experiment()`  [INFERRED]
  scripts/run_study.py → backend/codedna/models/experiment.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **CodeDNA analysis pipeline stages** — docs_architecture_git_analysis, docs_architecture_java_analysis, docs_architecture_dependency_graph, docs_architecture_impact_analysis, docs_architecture_test_mapping, docs_architecture_test_history, docs_architecture_models, docs_architecture_calibration, docs_architecture_selection [EXTRACTED 1.00]
- **Study protocol evolution D-034 to D-037** — docs_decisions_d_034, docs_decisions_d_035, docs_decisions_d_036, docs_decisions_d_037 [INFERRED 0.85]
- **Research questions RQ1-RQ5** — docs_research_plan_rq1, docs_research_plan_rq2, docs_research_plan_rq3, docs_research_plan_rq4, docs_research_plan_rq5 [EXTRACTED 1.00]
- **Change impact to test selection flow in the IDE** — docs_ide_screenshot_compare_baseline_selector, docs_ide_screenshot_changes_panel, docs_ide_screenshot_impact_summary, docs_ide_screenshot_tests_to_run_panel, docs_ide_screenshot_per_test_reasons [INFERRED 0.85]

## Communities (59 total, 7 thin omitted)

### Community 0 - "Java Reference Extraction"
Cohesion: 0.06
Nodes (68): Node, _compact(), extract_references(), _first_named(), Import, _is_named_member_type(), _line(), Collect the raw facts needed for dependency edges from one Java file. Purely… (+60 more)

### Community 1 - "Dependency Graph Builder"
Cohesion: 0.07
Nodes (50): _add_structure(), build_graph_for_commit(), file_role(), _FileContext, _parse_missing(), Path, Build the code graph of one commit. All ``.java`` files of the commit are read…, Classify a file as test or main code by Maven/JUnit path conventions. (+42 more)

### Community 2 - "Local HTTP API"
Cohesion: 0.05
Nodes (48): AnalyzeRequest, ChangeRequest, CompareRequest, create_app(), impact(), loopback_host_only(), plugins(), run_tests() (+40 more)

### Community 3 - "Study Runner Scripts"
Cohesion: 0.08
Nodes (48): argparse, concurrent_futures, _b10_pooled(), _ci(), _fmt(), _load_run_study(), main(), _mean() (+40 more)

### Community 4 - "Language Plugin Interface"
Cohesion: 0.06
Nodes (23): LanguagePlugin, Any, Path, The language-plugin interface (docs/DECISIONS.md D-018). A plugin supplies…, True if this plugin analyses the file at ``path``., Declarations with line ranges for one source file., ``CodeGraph`` (shared schema) for all files of ``commit`` this plugin handles., Statically discovered test classes of ``commit`` (``DiscoveryReport``). (+15 more)

### Community 5 - "Graph CLI Commands"
Cohesion: 0.09
Nodes (45): graph(), _json_file(), main(), Path, Accept either a JSON file or the run directory that contains it., build_graph(), Build the code graph for ``revision`` of the repository at ``repo_path``., End-to-end tests for ``codedna analyze``. (+37 more)

### Community 6 - "Git Blob Reading"
Cohesion: 0.09
Nodes (39): Read files of a commit straight from Git's object store. Nothing is checked…, Read many blobs with a single ``git cat-file --batch`` call., read_blobs(), _attach_line_ranges(), _list_changed_paths(), LineRange, Path, File-level change extraction between two commits. This is the first stage of… (+31 more)

### Community 7 - "Git Change Extraction Tests"
Cohesion: 0.08
Nodes (33): extract_changes(), Compare ``base`` and ``head`` in ``repo_path`` and describe every changed file., GitRepo, isolated_git_config(), numbered_lines(), fixture, Path, Shared pytest fixtures: throwaway Git repositories built inside tmp_path. (+25 more)

### Community 8 - "Chronological Evaluation"
Cohesion: 0.13
Nodes (29): chronological_split(), evaluate(), _ordering_metrics(), _probability_metrics(), Chronological evaluation of test-ordering strategies (D-023). Commits with…, _fit(), apfd(), apfdc() (+21 more)

### Community 9 - "Probability Calibration"
Cohesion: 0.11
Nodes (30): Calibrator, _logit(), Probability calibration (Milestone 5, D-025). A model's raw scores are often…, brier_score(), expected_calibration_error(), Calibration metrics: Brier score, Expected Calibration Error, reliability bins., Equal-width bins over [0, 1]: mean predicted probability vs observed failure…, ECE = sum over bins of (bin share) × |observed rate − mean predicted|. (+22 more)

### Community 10 - "IDE Extension Dependencies"
Cohesion: 0.06
Nodes (34): dependencies, @fontsource-variable/geist, @fontsource-variable/geist-mono, @theia/core, @theia/editor, @theia/filesystem, @theia/monaco, @theia/workspace (+26 more)

### Community 11 - "Change Analysis Mapping"
Cohesion: 0.13
Nodes (32): analyze(), analyze_changes(), File-level changes plus declaration mapping for every Java file., analyze_edit(), by_id(), edit(), java_of(), Tests for mapping changed line ranges to Java declarations. (+24 more)

### Community 12 - "Experiment Cost Matching"
Cohesion: 0.13
Nodes (26): _avg(), _cost_matched_and_bootstrap(), _hybrid_vs_rules(), _outcomes(), Milestone 5 experiment: calibration, risk-aware selection and fallback (D-027).…, Per-commit (time ratio, failing tests, missed failing tests)., _reproducibility(), _rounded() (+18 more)

### Community 13 - "Surefire JaCoCo Parsing"
Cohesion: 0.12
Nodes (27): _covered(), _float(), jvm_class_to_type_id(), parse_jacoco_report(), _parse_surefire_file(), parse_surefire_reports(), _parse_xml(), Exception (+19 more)

### Community 14 - "JUnit Test Discovery"
Cohesion: 0.13
Nodes (25): tests(), _ancestors(), discover_tests(), discover_tests_for_commit(), DiscoveredTest, DiscoveryReport, _modifiers(), Path (+17 more)

### Community 15 - "Feature Dataset Building"
Cohesion: 0.11
Nodes (22): BoundedParseCache, Least-recently-used parse cache shared across many commits. Consecutive commits…, build_dataset(), Dataset, _history_features(), _is_file_of(), _is_test_path(), Path (+14 more)

### Community 16 - "History Store"
Cohesion: 0.11
Nodes (18): HistoryStore, Path, Insert many (sha, test_id, status, time, source) rows in one transaction., fixture, store(), test_history_experiment_command(), dataset(), fixture (+10 more)

### Community 17 - "IDE Protocol Types"
Cohesion: 0.13
Nodes (16): AnalyzeReport, CODEDNA_SERVICE_PATH, CodeDnaStatus, ImpactReport, JavaFileAnalysis, PathStep, SelectionReport, SelectionStrategy (+8 more)

### Community 18 - "Selection Policies Ablations"
Cohesion: 0.16
Nodes (26): _ablations(), class_weight_check(), _measure(), _ml_policy(), choose(), Fallback driven only by the estimated skip risk (unfamiliar-change rule off)., Recent failures first (then shortest); probabilities only decide where to stop., Is the calibration gain only undoing balanced class weights? Trains the full… (+18 more)

### Community 19 - "Sample Java Project"
Cohesion: 0.11
Nodes (9): arraylist, assertequals, assertthrows, OrderService, PriceCalculator, OrderServiceTest, PriceCalculatorTest, list (+1 more)

### Community 20 - "Test Selection Baselines"
Cohesion: 0.19
Nodes (23): select_tests(), save_json(), commit(), coverage_map(), history(), fixture, Tests for the selection baselines (all / dependency / coverage) and compare., results() (+15 more)

### Community 21 - "IDE Change View Rendering"
Cohesion: 0.19
Nodes (17): unique(), breakable(), changeLabel(), confidenceLabel(), fileStatusLabel(), friendlyReason(), friendlyWarning(), kindLabel() (+9 more)

### Community 22 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, declarationMap, downlevelIteration, emitDecoratorMetadata, esModuleInterop, experimentalDecorators, jsx (+15 more)

### Community 23 - "RTPTorrent Importer"
Cohesion: 0.19
Nodes (20): _changed_files(), _commit_meta(), _existing_commits(), import_rtptorrent(), ImportReport, list_projects(), _push_base(), Path (+12 more)

### Community 24 - "Architecture Modules Docs"
Cohesion: 0.14
Nodes (21): Git via run_git argument lists, no shell=True, Tree-sitter Java, CodeDNA Architecture, calibration module (none/Platt/isotonic, Brier/ECE), dependency_graph module, git_analysis module, impact_analysis module (reverse BFS), java_analysis module (Tree-sitter parser + mapping) (+13 more)

### Community 25 - "Research Findings Decisions"
Cohesion: 0.15
Nodes (21): B10 hybrid policy (rules order + calibrated stopping at 5% risk), D-023 Leakage-free feature and evaluation protocol, D-036 Hybrid policy B10: rules order, calibrated stopping, D-037 Class-weight check as stricter RQ3 baseline, Evaluation chapter draft, Research Plan, APFD / APFDc prioritisation metrics, B3 recent failures + short duration ordering (+13 more)

### Community 26 - "Electron App Dependencies"
Cohesion: 0.10
Nodes (20): @theia/cli, @theia/core, @theia/editor, @theia/filesystem, @theia/monaco, @theia/workspace, main, name (+12 more)

### Community 27 - "Maven Code Index"
Cohesion: 0.17
Nodes (15): list_files(), Path, Return sorted ``(path, blob_sha)`` for regular files in ``commit`` ending in…, _CodeIndex, _collect_results(), Path, Run a project's JUnit tests with Maven, optionally with per-test JaCoCo…, Declarations of every Java file of a commit, for mapping covered lines. (+7 more)

### Community 28 - "Strategy Comparison"
Cohesion: 0.14
Nodes (15): compare_strategies(), _estimate_time(), Path, ValueError, Regression test selection baselines and their comparison. Strategies (names…, Compare strategies against a full-suite run of HEAD (the ground truth)., The requested selection cannot be computed (e.g. missing coverage map)., _select_by_coverage() (+7 more)

### Community 29 - "Maven Test Runner"
Cohesion: 0.19
Nodes (18): export_commit(), Write the files of ``commit`` into ``destination`` (which must be empty or…, BuildError, find_maven(), The build could not be started or its output could not be read., Run the tests of ``revision`` and write ``results.json`` (+ ``coverage-…, run_maven_tests(), project() (+10 more)

### Community 30 - "History Mining Collection"
Cohesion: 0.16
Nodes (16): collect_results(), import_results(), Path, Run the suite for mined commits without results, oldest first., mine_history(), Path, Store the first-parent history ending at ``revision`` (oldest first). First-…, Tests for history mining, the result store, import and collection (Milestone 4). (+8 more)

### Community 31 - "IDE Comparison Presets"
Cohesion: 0.20
Nodes (12): CodeDnaComparison, ComparisonPreset, PRESETS, injectable, friendlyError, STRATEGIES, Chip(), ComparePicker() (+4 more)

### Community 32 - "IDE Contributions Wiring"
Cohesion: 0.15
Nodes (10): ChangeViewContribution, TestsViewContribution, injectable, CodeDnaWorkspace, inject, injectable, ide_codedna_extension_src_browser_style_codedna, ide_codedna_extension_src_browser_style_codedna_shell (+2 more)

### Community 33 - "IDE Workspace Package"
Cohesion: 0.12
Nodes (16): description, devDependencies, @theia/cli, engines, node, npm, @theia/cli, name (+8 more)

### Community 34 - "Commit Mining Store"
Cohesion: 0.15
Nodes (9): _count(), Mine the first-parent commit history of a repository into the history store., CommitRecord, FileChange, SQLite store for commit history and test results (docs/DECISIONS.md D-021). One…, Store mined history; ``seq`` must already be chronological from 0., Results of one commit; with several sources, a failure in any source wins., ResultRecord (+1 more)

### Community 35 - "IDE Screenshot UI"
Cohesion: 0.16
Nodes (16): Affected Tests Only Selection Mode, Changes Panel (left sidebar), CodeDNA IDE (screenshot), Compare Baseline Selector (My last commit), Editor Area (pom.xml open), Failure Risk Pending Test History, Change Impact Summary (files changed, parts touched, classes affected), Non-Java File Notice (unanalysed changes) (+8 more)

### Community 36 - "CI And Platform Docs"
Cohesion: 0.15
Nodes (15): CI workflow (GitHub Actions), CI job: ide-extension (TypeScript build), CI job: maven-integration (real Maven/JaCoCo), CI job: sample-java-project (Maven + JUnit 5), JaCoCo, Local API (FastAPI, codedna serve), D-019 IDE built on Eclipse Theia talking to a local API, D-028 Local API: FastAPI on loopback with session token (+7 more)

### Community 37 - "CLI Argument Parser"
Cohesion: 0.31
Nodes (13): ArgumentParser, _add_change_args(), _add_non_java_arg(), build_parser(), _fraction(), _import_rtptorrent(), _non_negative_int(), Command-line interface for CodeDNA. Usage: codedna analyze --repo PATH --base… (+5 more)

### Community 38 - "Extension Package Deps"
Cohesion: 0.14
Nodes (14): dependencies, codedna-extension, @theia/core, @theia/editor, @theia/electron, @theia/filesystem, @theia/markers, @theia/messages (+6 more)

### Community 39 - "Agent Rules Tracks"
Cohesion: 0.19
Nodes (13): CI job: python-tests (Ubuntu/Windows, py3.11/3.12), AGENTS.md (rules for AI agents and contributors), Confirmed / heuristic / unresolved edge labels, Never fabricate test or research numbers, Product track (IDE, plugins, website), Research track (Milestones 0-5, priority), CLAUDE.md (includes AGENTS.md), CodeDNA (change-impact + regression test selection platform) (+5 more)

### Community 40 - "Tests View Widget"
Cohesion: 0.18
Nodes (5): TestsViewWidget, inject, injectable, postConstruct, CodeDnaService

### Community 41 - "CodeDNA Theme"
Cohesion: 0.20
Nodes (8): C, CODEDNA_THEME_ID, CodeDnaThemeContribution, COLORS, TOKEN_COLORS, inject, injectable, ref_theia_monaco

### Community 42 - "Test Result Models"
Cohesion: 0.22
Nodes (5): Store every test-class result of ``run``; returns the number of rows., TestClassResult, TestRunResult, run_result(), test_history_cli_mine_import_status()

### Community 43 - "Prior Art Datasets"
Cohesion: 0.22
Nodes (11): CodeDNA FYP Starter brief, Cytoscape.js, Ekstazi, Fine-Ekstazi, Predictive RTS, RTSTester, Dataset Plan, Apache Commons CSV (self-collected) (+3 more)

### Community 44 - "Select Compare Endpoints"
Cohesion: 0.29
Nodes (8): compare(), select(), _json_file(), Path, CoverageMap, load_coverage_map(), load_results(), Path

### Community 45 - "Study Protocol Findings"
Cohesion: 0.31
Nodes (10): D-034 Study protocol: six projects, five seeds, B9r/B9n, D-035 Cost-matched comparisons and hierarchical bootstrap, B9 calibrated ML + fallback (B9r, B9n variants), Roadmap, HikariCP first real evaluation, Eleven-project study findings, Data gap: graylog2-server and jOOQ have no failing test commits, Eleven-project study summary (+2 more)

### Community 46 - "Theia App Config"
Cohesion: 0.20
Nodes (10): applicationName, defaultTheme, electron, reloadOnReconnect, windowOptions, config, theia, frontend (+2 more)

### Community 47 - "Esbuild Bundle"
Cohesion: 0.22
Nodes (8): ide_electron_app_gen_esbuild_browser, ide_electron_app_gen_esbuild_browser_browseroptions, ide_electron_app_gen_esbuild_browser_watch, ide_electron_app_gen_esbuild_electron, ide_electron_app_gen_esbuild_electron_electronoptions, ide_electron_app_gen_esbuild_node, ide_electron_app_gen_esbuild_node_nodeoptions, ref_esbuild

### Community 48 - "Change View Widget"
Cohesion: 0.33
Nodes (4): ChangeViewWidget, inject, injectable, postConstruct

### Community 49 - "Editor Preferences"
Cohesion: 0.33
Nodes (6): preferences, editor.fontFamily, editor.fontSize, editor.lineHeight, workbench.colorTheme, workbench.iconTheme

### Community 50 - "Package Scripts"
Cohesion: 0.40
Nodes (5): scripts, bundle, rebuild, start, watch

### Community 51 - "Electron Dev Deps"
Cohesion: 0.67
Nodes (3): devDependencies, electron, @theia/cli

## Knowledge Gaps
- **137 isolated node(s):** `example:sample-java-project`, `name`, `version`, `private`, `description` (+132 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 433 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Graph CLI Commands` to `Dependency Graph Builder`, `Local HTTP API`, `Language Plugin Interface`, `CLI Argument Parser`, `Git Change Extraction Tests`, `Chronological Evaluation`, `Probability Calibration`, `Test Result Models`, `Change Analysis Mapping`, `Select Compare Endpoints`, `Surefire JaCoCo Parsing`, `JUnit Test Discovery`, `History Store`, `Test Selection Baselines`, `Strategy Comparison`, `Maven Test Runner`, `History Mining Collection`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `HistoryStore` connect `History Store` to `Commit Mining Store`, `Study Runner Scripts`, `CLI Argument Parser`, `Git Blob Reading`, `Chronological Evaluation`, `Probability Calibration`, `Test Result Models`, `Feature Dataset Building`, `RTPTorrent Importer`, `History Mining Collection`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `extract_changes()` connect `Git Change Extraction Tests` to `Java Reference Extraction`, `Local HTTP API`, `Graph CLI Commands`, `CLI Argument Parser`, `Git Blob Reading`, `Change Analysis Mapping`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `HistoryStore` (e.g. with `collect_results()` and `import_results()`) actually correct?**
  _`HistoryStore` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `create_app()` (e.g. with `require_token()` and `ReportError`) actually correct?**
  _`create_app()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `select_tests()` (e.g. with `CoverageMap` and `TestRunResult`) actually correct?**
  _`select_tests()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `example:sample-java-project`, `name`, `version` to the rest of the system?**
  _137 weakly-connected nodes found - possible documentation gaps or missing edges._