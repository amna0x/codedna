# Graph Report - codedna  (2026-10-24)

## Corpus Check
- 115 files · ~76,195 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 3, .css 2, .example 1)

## Summary
- 1449 nodes · 3741 edges · 85 communities (64 shown, 21 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 335 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `991484d2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Java Reference Extraction
- Dependency Graph Builder
- create_app
- run_study.py
- load_plugins
- Graph CLI Commands
- mine_history
- Git Change Extraction Tests
- Chronological Evaluation
- compute_impact
- codedna-extension/package.json
- Change Analysis Mapping
- Experiment Cost Matching
- reports.py
- JUnit Test Discovery
- Dataset
- with
- IDE Protocol Types
- test_risk_calibration.py
- Sample Java Project
- test_selection.py
- IDE Change View Rendering
- TypeScript Config
- RTPTorrent Importer
- Architecture Modules Docs
- CodeDNA FYP Starter brief
- experiment.py
- _CodeIndex
- cli.py
- Maven Test Runner
- pathlib
- ui.tsx
- IDE Contributions Wiring
- IDE Workspace Package
- HistoryStore
- IDE Screenshot UI
- CI workflow (GitHub Actions)
- _run_history
- main
- Agent Rules Tracks
- Tests View Widget
- CodeDNA Theme
- app.py
- Dataset Plan
- .commit
- B10 hybrid policy (rules order + calibrated stopping at 5% risk)
- test_api.py
- ChangeViewWidget
- dependencies
- git.py
- electron-app/package.json
- fetch_rtptorrent_subset.py
- run_cross_project.py
- Python Project Config
- Sample Maven POM
- config
- json
- java_analysis module (Tree-sitter parser + mapping)
- analyze_changes
- preferences
- scripts
- load_results
- codedna-extension@0.1.0
- make_study_figures.py
- @theia/electron@1.76.0
- @theia/messages@1.76.0
- @theia/preferences@1.76.0
- @theia/terminal@1.76.0
- pytest
- RemoteZip
- conftest.py
- CodeDNA IDE (Theia 1.76 + Electron 42)
- @theia/core@1.76.0
- server.py
- JavaPlugin
- test_incompatible_and_broken_plugins_are_rejected
- Cross-project transfer protocol
- _structural
- SpyRanker
- saved_study

## God Nodes (most connected - your core abstractions)
1. `main()` - 47 edges
2. `HistoryStore` - 46 edges
3. `Row` - 39 edges
4. `Dataset` - 37 edges
5. `extract_changes()` - 36 edges
6. `create_app()` - 35 edges
7. `run_maven_tests()` - 34 edges
8. `select_tests()` - 33 edges
9. `compute_impact()` - 30 edges
10. `import_rtptorrent()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `Evaluation chapter draft` --semantically_similar_to--> `Thesis claim: honest checked risk estimates as stopping rule at equal test time`  [INFERRED] [semantically similar]
  docs/REPORT_DRAFT.md → MEMORY.md
- `CI job: ide-extension (TypeScript build)` --references--> `CodeDNA IDE (Theia 1.76 + Electron 42)`  [INFERRED]
  .github/workflows/ci.yml → ide/README.md
- `Project Specification` --references--> `CodeDNA (change-impact + regression test selection platform)`  [INFERRED]
  docs/PROJECT_SPEC.md → CODEDNA_STARTER.md
- `CI job: python-tests (Ubuntu/Windows, py3.11/3.12)` --conceptually_related_to--> `Never fabricate test or research numbers`  [INFERRED]
  .github/workflows/ci.yml → AGENTS.md
- `CodeDNA README` --references--> `CodeDNA IDE README`  [INFERRED]
  README.md → ide/README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **CodeDNA analysis pipeline stages** — docs_architecture_git_analysis, docs_architecture_java_analysis, docs_architecture_dependency_graph, docs_architecture_impact_analysis, docs_architecture_test_mapping, docs_architecture_test_history, docs_architecture_models, docs_architecture_calibration, docs_architecture_selection [EXTRACTED 1.00]
- **Research questions RQ1-RQ5** — docs_research_plan_rq1, docs_research_plan_rq2, docs_research_plan_rq3, docs_research_plan_rq4, docs_research_plan_rq5 [EXTRACTED 1.00]
- **Change impact to test selection flow in the IDE** — docs_ide_screenshot_compare_baseline_selector, docs_ide_screenshot_changes_panel, docs_ide_screenshot_impact_summary, docs_ide_screenshot_tests_to_run_panel, docs_ide_screenshot_per_test_reasons [INFERRED 0.85]
- **Study protocol evolution D-034 to D-037** — docs_decisions_d_034, docs_decisions_d_035, docs_decisions_d_036, docs_decisions_d_037 [INFERRED 0.85]

## Communities (85 total, 21 thin omitted)

### Community 0 - "Java Reference Extraction"
Cohesion: 0.08
Nodes (25): _attach_line_ranges(), ChangedFile, ChangeReport, _list_changed_paths(), _to_range(), GitCommandError, _add_declarations(), _add_outside() (+17 more)

### Community 1 - "Dependency Graph Builder"
Cohesion: 0.06
Nodes (40): _add_structure(), BoundedParseCache, build_graph(), build_graph_for_commit(), file_role(), _FileContext, _parse_missing(), _Resolution (+32 more)

### Community 2 - "create_app"
Cohesion: 0.15
Nodes (5): create_app(), graph(), impact(), run_tests(), tests()

### Community 3 - "run_study.py"
Cohesion: 0.16
Nodes (18): _agg(), _ci(), _contributing(), _cost_matched(), _fmt(), _fmt_stats(), _graph_signal(), _hierarchical_draws() (+10 more)

### Community 4 - "load_plugins"
Cohesion: 0.15
Nodes (6): plugins(), LanguagePlugin, load_plugins(), _major(), PluginRegistry, test_builtin_java_plugin_is_registered()

### Community 5 - "Graph CLI Commands"
Cohesion: 0.19
Nodes (22): build(), dependency_edges(), test_duplicate_type_names_make_edges_heuristic(), test_extends_and_implements_edges(), test_file_role_uses_path_conventions(), test_generic_arguments_in_extends_are_uses(), test_graph_of_older_revision_uses_same_ids(), test_import_resolution_wins_over_same_package() (+14 more)

### Community 6 - "mine_history"
Cohesion: 0.26
Nodes (5): resolve_commit(), _count(), mine_history(), CommitRecord, FileChange

### Community 7 - "Git Change Extraction Tests"
Cohesion: 0.21
Nodes (20): extract_changes(), numbered_lines(), by_path(), test_added_java_file(), test_comparison_across_several_commits(), test_deleted_java_file(), test_directory_that_is_not_a_repository_fails_clearly(), test_empty_diff_between_identical_commits() (+12 more)

### Community 8 - "Chronological Evaluation"
Cohesion: 0.14
Nodes (22): evaluate(), _ordering_metrics(), _probability_metrics(), _fit(), apfd(), apfdc(), recall_at_budget(), time_to_first_failure() (+14 more)

### Community 9 - "compute_impact"
Cohesion: 0.15
Nodes (23): _candidate_tests(), _collect_seeds(), add(), compute_impact(), _impacted(), _impacted_files(), ImpactedNode, ImpactReport (+15 more)

### Community 10 - "codedna-extension/package.json"
Cohesion: 0.07
Nodes (34): dependencies, @fontsource-variable/geist@^5.3.0, @fontsource-variable/geist-mono@^5.3.0, @theia/core@1.76.0, @theia/editor@1.76.0, @theia/filesystem@1.76.0, @theia/monaco@1.76.0, @theia/workspace@1.76.0 (+26 more)

### Community 11 - "Change Analysis Mapping"
Cohesion: 0.20
Nodes (19): analyze_edit(), by_id(), edit(), test_added_method_does_not_flag_the_class(), test_change_spanning_two_methods(), test_changes_outside_methods_are_reported_explicitly(), test_class_rename_shows_added_and_deleted_types(), test_comment_only_change_inside_method() (+11 more)

### Community 12 - "Experiment Cost Matching"
Cohesion: 0.22
Nodes (10): _cost_matched_and_bootstrap(), bootstrap(), _difference(), _interval(), match_budget(), metrics(), test_bootstrap_intervals_and_paired_differences(), test_bootstrap_reports_no_interval_without_failures() (+2 more)

### Community 13 - "reports.py"
Cohesion: 0.14
Nodes (14): _covered(), _float(), jvm_class_to_type_id(), parse_jacoco_report(), _parse_surefire_file(), parse_surefire_reports(), _parse_xml(), ReportError (+6 more)

### Community 14 - "JUnit Test Discovery"
Cohesion: 0.14
Nodes (18): _ancestors(), discover_tests(), discover_tests_for_commit(), DiscoveredTest, DiscoveryReport, _modifiers(), _scan_file(), visit() (+10 more)

### Community 15 - "Dataset"
Cohesion: 0.11
Nodes (21): chronological_split(), _reproducibility(), evaluate_target(), fit_project(), FittedProject, source_prefix_before(), Dataset, _history_features() (+13 more)

### Community 16 - "with"
Cohesion: 0.06
Nodes (43): run, defaults, name, runs-on, steps, jobs, ide-extension, maven-integration (+35 more)

### Community 17 - "IDE Protocol Types"
Cohesion: 0.13
Nodes (11): AnalyzeReport, CODEDNA_SERVICE_PATH, CodeDnaStatus, ImpactReport, JavaFileAnalysis, PathStep, SelectionStrategy, CodeDnaServiceImpl (+3 more)

### Community 18 - "test_risk_calibration.py"
Cohesion: 0.11
Nodes (31): Calibrator, _logit(), _risk_only(), run_experiment(), _summary(), decide(), _decision(), _estimated_costs() (+23 more)

### Community 19 - "Sample Java Project"
Cohesion: 0.13
Nodes (4): OrderService, PriceCalculator, OrderServiceTest, PriceCalculatorTest

### Community 20 - "test_selection.py"
Cohesion: 0.11
Nodes (26): compare_strategies(), _estimate_time(), _select_by_coverage(), select_tests(), pick(), SelectedTest, SelectionError, SelectionReport (+18 more)

### Community 21 - "IDE Change View Rendering"
Cohesion: 0.19
Nodes (20): unique(), breakable(), changeLabel(), confidenceLabel(), fileStatusLabel(), friendlyReason(), friendlyWarning(), kindLabel() (+12 more)

### Community 22 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, declarationMap, downlevelIteration, emitDecoratorMetadata, esModuleInterop, experimentalDecorators, jsx (+15 more)

### Community 23 - "RTPTorrent Importer"
Cohesion: 0.18
Nodes (15): run_git(), _changed_files(), _commit_meta(), _existing_commits(), import_rtptorrent(), ImportReport, list_projects(), _push_base() (+7 more)

### Community 24 - "Architecture Modules Docs"
Cohesion: 0.15
Nodes (10): CodeDNA Architecture, calibration module (none/Platt/isotonic, Brier/ECE), git_analysis module, impact_analysis module (reverse BFS), models module (metrics, rankers, evaluate, experiment), Analysis pipeline (change -> graph -> impact -> tests -> model -> calibration -> selection), Language plugin interface and registry, selection module (baselines + risk-aware) (+2 more)

### Community 25 - "CodeDNA FYP Starter brief"
Cohesion: 0.17
Nodes (15): CodeDNA FYP Starter brief, CodeDNA (change-impact + regression test selection platform), Cytoscape.js, Ekstazi, Fine-Ekstazi, Predictive RTS, RTSTester, Evaluation chapter draft (+7 more)

### Community 26 - "experiment.py"
Cohesion: 0.12
Nodes (20): brier_score(), expected_calibration_error(), reliability_bins(), _ablations(), _avg(), _calibration_section(), class_weight_check(), _hybrid_vs_rules() (+12 more)

### Community 27 - "_CodeIndex"
Cohesion: 0.20
Nodes (6): list_files(), read_blobs(), _CodeIndex, _to_ranges(), JacocoCoverage, TestCoverage

### Community 28 - "cli.py"
Cohesion: 0.14
Nodes (9): _add_change_args(), _add_non_java_arg(), build_parser(), _fraction(), _json_file(), _non_negative_int(), git(), main() (+1 more)

### Community 29 - "Maven Test Runner"
Cohesion: 0.15
Nodes (15): export_commit(), BuildError, _collect_results(), find_maven(), _run_maven(), run_maven_tests(), _run_per_test(), test_coverage_mapping_and_strategy_comparison_with_real_maven() (+7 more)

### Community 30 - "pathlib"
Cohesion: 0.15
Nodes (12): collect_results(), import_results(), TestCaseResult, TestClassResult, save_json(), TestRunResult, run_result(), test_collect_requires_allow_build() (+4 more)

### Community 31 - "ui.tsx"
Cohesion: 0.35
Nodes (7): ComparisonPreset, PRESETS, friendlyError, ComparePicker(), ErrorNotice(), FirstRun(), Spinner()

### Community 33 - "IDE Workspace Package"
Cohesion: 0.12
Nodes (16): description, devDependencies, @theia/cli@1.76.0, engines, node, npm, @theia/cli, name (+8 more)

### Community 34 - "HistoryStore"
Cohesion: 0.10
Nodes (16): build_dataset(), _is_file_of(), _is_test_path(), HistoryStore, ResultRecord, store(), test_failure_from_any_source_wins(), test_mine_first_parent_history_in_order() (+8 more)

### Community 35 - "IDE Screenshot UI"
Cohesion: 0.16
Nodes (13): Affected Tests Only Selection Mode, Changes Panel (left sidebar), CodeDNA IDE (screenshot), Compare Baseline Selector (My last commit), Editor Area (pom.xml open), Change Impact Summary (files changed, parts touched, classes affected), OrderTotalsTest, Per-Test Selection Reasons (+5 more)

### Community 36 - "CI workflow (GitHub Actions)"
Cohesion: 0.29
Nodes (7): CI workflow (GitHub Actions), CI job: ide-extension (TypeScript build), CI job: maven-integration (real Maven/JaCoCo), CI job: python-tests (Ubuntu/Windows, py3.11/3.12), CI job: sample-java-project (Maven + JUnit 5), JaCoCo, Sample Java project (Maven + JUnit 5)

### Community 37 - "_run_history"
Cohesion: 0.67
Nodes (5): _import_rtptorrent(), _run_history(), _run_on_dataset(), _run_tests(), _write_json()

### Community 38 - "main"
Cohesion: 0.23
Nodes (11): main(), test_analyze_defaults_to_method_level(), test_analyze_file_level_prints_json_report(), test_analyze_invalid_commit_exits_with_error(), test_analyze_invalid_repository_exits_with_error(), test_analyze_writes_output_file(), test_missing_required_argument_is_usage_error(), test_cli_refuses_without_allow_build() (+3 more)

### Community 39 - "Agent Rules Tracks"
Cohesion: 0.29
Nodes (9): AGENTS.md (rules for AI agents and contributors), Product track (IDE, plugins, website), Research track (Milestones 0-5, priority), CLAUDE.md (includes AGENTS.md), Decision records (D-001 to D-037), Project Specification, Roadmap, MEMORY.md handoff notes (+1 more)

### Community 40 - "Tests View Widget"
Cohesion: 0.15
Nodes (3): CodeDnaWorkspace, TestsViewWidget, CodeDnaService

### Community 41 - "CodeDNA Theme"
Cohesion: 0.20
Nodes (5): C, CODEDNA_THEME_ID, CodeDnaThemeContribution, COLORS, TOKEN_COLORS

### Community 42 - "app.py"
Cohesion: 0.19
Nodes (9): AnalyzeRequest, ChangeRequest, CompareRequest, GraphRequest, ImpactRequest, RepoRequest, RevRequest, RunTestsRequest (+1 more)

### Community 43 - "Dataset Plan"
Cohesion: 0.50
Nodes (4): Dataset Plan, Apache Commons CSV (self-collected), Defects4J, RTPTorrent v1.1 (Mattis et al., MSR 2020)

### Community 44 - ".commit"
Cohesion: 0.15
Nodes (11): project(), test_graph_command_exports_json(), test_graph_command_reports_bad_revision(), test_invalid_revision_is_rejected(), test_binary_file_is_flagged_with_warning(), test_collect_runs_each_commit_once(), test_mine_limits_and_binary_files(), test_crlf_java_file_keeps_git_line_numbers() (+3 more)

### Community 45 - "B10 hybrid policy (rules order + calibrated stopping at 5% risk)"
Cohesion: 0.22
Nodes (6): B10 hybrid policy (rules order + calibrated stopping at 5% risk), B3 recent failures + short duration ordering, B8 hybrid ML, calibrated, B9 calibrated ML + fallback (B9r, B9n variants), RQ4 uncertainty-aware fallback safety/cost, Tests to run view

### Community 46 - "test_api.py"
Cohesion: 0.19
Nodes (10): loopback_host_only(), _hostname(), client(), test_analysis_endpoints_return_cli_json(), test_errors_are_json_with_useful_status(), test_health_is_open_but_everything_else_needs_the_token(), test_hostname_parsing(), test_no_cors_headers_are_sent() (+2 more)

### Community 49 - "dependencies"
Cohesion: 0.13
Nodes (15): dependencies, @theia/editor@1.76.0, @theia/filesystem@1.76.0, @theia/markers@1.76.0, @theia/monaco@1.76.0, @theia/navigator@1.76.0, @theia/process@1.76.0, @theia/workspace@1.76.0 (+7 more)

### Community 50 - "git.py"
Cohesion: 0.14
Nodes (9): CodeDNAGitError, InvalidCommitError, InvalidRepositoryError, resolve_repository(), _run(), run_git_bytes(), test_bare_repositories_are_accepted(), test_repeated_runs_in_one_job_are_merged_and_failure_wins() (+1 more)

### Community 51 - "electron-app/package.json"
Cohesion: 0.22
Nodes (10): devDependencies, electron@42.8.1, @theia/cli@1.76.0, @theia/cli, main, name, private, productName (+2 more)

### Community 54 - "fetch_rtptorrent_subset.py"
Cohesion: 0.12
Nodes (7): test_archive_paths_cannot_escape_output(), test_subset_download_filters_shared_map_and_verifies_restart(), __init__(), fetch(), main(), safe_target(), selected_entry()

### Community 55 - "run_cross_project.py"
Cohesion: 0.16
Nodes (7): test_runner_keeps_unavailable_calendar_direction_and_can_resume(), main(), markdown(), _mean(), run(), _study_helpers(), summarise()

### Community 59 - "config"
Cohesion: 0.20
Nodes (10): applicationName, defaultTheme, electron, reloadOnReconnect, windowOptions, config, theia, frontend (+2 more)

### Community 60 - "json"
Cohesion: 0.22
Nodes (11): _b10_pooled(), _ci(), _fmt(), _load_run_study(), main(), _mean(), run_project(), summarise() (+3 more)

### Community 61 - "java_analysis module (Tree-sitter parser + mapping)"
Cohesion: 0.29
Nodes (4): Tree-sitter Java, dependency_graph module, java_analysis module (Tree-sitter parser + mapping), RQ5 value of graph-derived features

### Community 62 - "analyze_changes"
Cohesion: 0.24
Nodes (9): analyze(), analyze_changes(), java_of(), test_added_java_file_lists_all_declarations_as_added(), test_deleted_java_file_lists_all_declarations_as_deleted(), test_demo_repository_names_modified_method_and_added_class(), test_java_renamed_to_non_java_is_unresolved(), test_non_java_files_have_no_declaration_mapping() (+1 more)

### Community 63 - "preferences"
Cohesion: 0.33
Nodes (6): preferences, editor.fontFamily, editor.fontSize, editor.lineHeight, workbench.colorTheme, workbench.iconTheme

### Community 64 - "scripts"
Cohesion: 0.40
Nodes (5): scripts, bundle, rebuild, start, watch

### Community 65 - "load_results"
Cohesion: 0.36
Nodes (5): compare(), select(), _json_file(), load_coverage_map(), load_results()

### Community 67 - "make_study_figures.py"
Cohesion: 0.27
Nodes (8): collect_data(), load(), export(), main(), _number(), _reject_constant(), render_figures(), _stats()

### Community 73 - "pytest"
Cohesion: 0.27
Nodes (8): test_budget_averages_seeds_then_projects_without_zero_filling(), test_calibration_and_stopping_use_common_cohorts(), test_different_risk_targets_cannot_share_a_target_line(), test_export_fingerprints_inputs_and_is_repeatable(), test_inconsistent_budget_grid_is_rejected(), test_missing_seed_does_not_silently_shrink_the_study(), test_nonfinite_numbers_are_rejected(), test_render_all_figures_from_saved_reports()

### Community 75 - "conftest.py"
Cohesion: 0.15
Nodes (4): GitRepo, isolated_git_config(), repo(), dataset()

### Community 76 - "CodeDNA IDE (Theia 1.76 + Electron 42)"
Cohesion: 0.29
Nodes (4): Local API (FastAPI, codedna serve), CodeDNA IDE README, Changes view, CodeDNA IDE (Theia 1.76 + Electron 42)

### Community 78 - "server.py"
Cohesion: 0.39
Nodes (4): new_token(), is_loopback(), serve(), test_token_and_host_policies()

### Community 81 - "Cross-project transfer protocol"
Cohesion: 0.29
Nodes (6): Commands, Cross-project transfer protocol, Data recovery, Measures and decision rules, Question and scope, Training and evaluation

## Knowledge Gaps
- **16 isolated node(s):** `example:sample-java-project`, `codedna`, `Analysis pipeline (change -> graph -> impact -> tests -> model -> calibration -> selection)`, `Cytoscape.js`, `APFD / APFDc prioritisation metrics` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 428 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `main` to `Dependency Graph Builder`, `load_plugins`, `Graph CLI Commands`, `Git Change Extraction Tests`, `Chronological Evaluation`, `compute_impact`, `reports.py`, `JUnit Test Discovery`, `test_risk_calibration.py`, `test_selection.py`, `cli.py`, `Maven Test Runner`, `pathlib`, `HistoryStore`, `_run_history`, `.commit`, `git.py`, `analyze_changes`, `load_results`, `server.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `HistoryStore` (e.g. with `collect_results()` and `import_results()`) actually correct?**
  _`HistoryStore` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `example:sample-java-project`, `codedna`, `Analysis pipeline (change -> graph -> impact -> tests -> model -> calibration -> selection)` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Java Reference Extraction` be split into smaller, more focused modules?**
  _Cohesion score 0.07692307692307693 - nodes in this community are weakly interconnected._
- **Why does `run_maven_tests()` connect `Maven Test Runner` to `create_app`, `load_plugins`, `_run_history`, `mine_history`, `app.py`, `json`, `JavaPlugin`, `git.py`, `test_selection.py`, `cli.py`, `pathlib`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Should `Dependency Graph Builder` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._
- **Why does `analyze_changes()` connect `analyze_changes` to `Java Reference Extraction`, `create_app`, `main`, `Git Change Extraction Tests`, `compute_impact`, `app.py`, `Change Analysis Mapping`, `.commit`, `test_selection.py`, `cli.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._