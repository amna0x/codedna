# Graph Report - codedna  (2026-10-24)

## Corpus Check
- 21 files · ~77,145 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1716 nodes · 4196 edges · 102 communities (76 shown, 26 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 377 edges (avg confidence: 0.88)
- Token cost: 253,827 input · 0 output

## Community Hubs (Navigation)
- Java Reference Extraction
- Dependency Graph Builder
- Local API Endpoints
- Language Plugin Interface
- CI Workflow Config
- API Request Models
- Milestone 5 Experiment
- Maven Runner & Coverage
- Git Blob Access
- Probability Calibrators
- IDE Extension Package
- History Dataset Builder
- Test Result Collection
- Java Change Analysis
- IDE Protocol Types
- IDE Change View Rendering
- JaCoCo/Surefire Reports
- Test Git Repo Helper
- Study Runner
- Sample Java Project
- RTPTorrent Import
- Baseline Rankers
- Cross-Project Transfer Model
- Live Risk Decision
- Dependency Graph Tests
- IDE Contributions Wiring
- TypeScript Config
- CLI Argument Parser
- Git Change Extraction Tests
- DANTE-H History Scores
- Chronological Evaluation Metrics
- Research Plan Questions
- Project Rules & Plans
- Evaluation & Ablations
- CLI Entry & Tests
- Early Core Decisions
- Architecture Pipeline Docs
- IDE Workspace Service
- Dataset & Leakage Guard
- CI Jobs & Starter Brief
- Runner Reproducibility Tests
- Transfer & B10 Protocols
- IDE Root Package
- Transfer Runner Tests
- IDE Screenshot UI
- Subset Download Tests
- Transfer Protocol Docs
- Theia Dependencies
- Safe Git Wrapper
- RTPTorrent Subset Fetch
- Study Figure Script
- Class-Weight Check
- Graph & Mapping Milestones
- Experiment Protocol Decisions
- Scope & Platform Decisions
- Platform Components
- Selection Policies
- Cost-Matched & B10 Decisions
- IDE Comparison Presets
- Electron App Package
- History Mining
- IDE & API Decisions
- Baseline Policy Decisions
- Change View Widget
- Electron App Config
- Remote Zip Reader
- Git Error Types
- Select & Compare Commands
- Pytest Fixtures
- RTPTorrent Import Tests
- Transfer Feature Prep
- Plugin Catalogue Decisions
- IDE & Local API Milestone
- CLI Run Commands
- Parse Cache
- RTPTorrent & SQLite Decisions
- IDE Editor Preferences
- Validation & Demo Setup
- Package Scripts
- Platform Website Milestone
- Git CLI Decision
- Milestone 1 Analyze
- Local Graphify Tooling
- Study Figure Provenance
- RQ5 Graph Features
- Extension Package Id
- Theia Core
- Theia Electron
- Theia Messages
- Theia Preferences
- Theia Terminal
- CLAUDE.md
- RQ2 Test Time Saved
- Progress Report Rule
- CodeDNA Root
- Sample Project Example

## God Nodes (most connected - your core abstractions)
1. `main()` - 50 edges
2. `create_app()` - 44 edges
3. `HistoryStore` - 43 edges
4. `extract_changes()` - 40 edges
5. `run_maven_tests()` - 39 edges
6. `CodeDNA Decision Log` - 39 edges
7. `Row` - 38 edges
8. `select_tests()` - 36 edges
9. `Dataset` - 31 edges
10. `resolve_repository()` - 31 edges

## Surprising Connections (you probably didn't know these)
- `D-029 IDE skeleton: Theia 1.76.0, Electron, backend proxy` --references--> `electron`  [EXTRACTED]
  docs/DECISIONS.md → ide/electron-app/package.json
- `CI job: ide-extension (TypeScript build)` --references--> `CodeDNA IDE (Theia 1.76 + Electron 42)`  [INFERRED]
  .github/workflows/ci.yml → ide/README.md
- `Reproducible Experiments (Seeds, Chronological Splits)` --semantically_similar_to--> `Chronological 60/20/20 Split Protocol`  [INFERRED] [semantically similar]
  AGENTS.md → docs/RESEARCH_PLAN.md
- `run_project()` --uses--> `Dataset`  [INFERRED]
  scripts/class_weight_check.py → backend/codedna/test_history/features.py
- `run()` --uses--> `Dataset`  [INFERRED]
  scripts/run_dante_check.py → backend/codedna/test_history/features.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Change impact to test selection flow in the IDE** — docs_ide_screenshot_compare_baseline_selector, docs_ide_screenshot_changes_panel, docs_ide_screenshot_impact_summary, docs_ide_screenshot_tests_to_run_panel, docs_ide_screenshot_per_test_reasons [INFERRED 0.85]
- **Research Questions and Their Study Results** — docs_research_plan_rq1, docs_research_plan_rq3, docs_research_plan_rq4, docs_research_plan_rq5, memory_rq1_result, memory_rq3_result, memory_rq4_result, memory_rq5_result [INFERRED 0.85]
- **Core CLI Analysis Pipeline (analyze, graph, impact, select)** — readme_cli_analyze, readme_cli_graph, readme_cli_impact, readme_cli_select_compare, readme_cli_run_tests [INFERRED 0.85]
- **Platform Product Components (D-017)** — agents_platform_d017, readme_codedna_ide, docs_roadmap_local_api, docs_roadmap_language_plugin_interface, docs_roadmap_plugin_catalogue [INFERRED 0.85]
- **Calibrated risk-based stopping flow (model -> calibration -> skip risk -> B10)** — docs_architecture_failure_probability_model, docs_architecture_probability_calibration, docs_architecture_skip_risk_formula, docs_report_draft_b10_hybrid_policy [INFERRED 0.85]
- **Temporal leakage prevention across features, splits and transfer** — docs_architecture_leakage_guard, docs_report_draft_chronological_split, docs_cross_project_protocol_source_prefix_restriction [INFERRED 0.85]
- **Transfer validation data recovery and evaluation pipeline** — docs_cross_project_protocol_byte_range_recovery, docs_cross_project_protocol_feature_rebuild, docs_architecture_transfer_validation, docs_dataset_plan_transfer_subset_recovery [EXTRACTED 1.00]
- **Baseline selection policies compared in the study** — docs_decisions_policy_b0, docs_decisions_policy_b3, docs_decisions_policy_b4, docs_decisions_policy_b8, docs_decisions_policy_b9, docs_decisions_policy_b9r, docs_decisions_policy_b9n, docs_decisions_policy_b10 [EXTRACTED 1.00]
- **Calibration fitted on validation and evaluated by ECE/Brier** — docs_decisions_d_025, docs_decisions_platt_scaling, docs_decisions_isotonic_regression, docs_decisions_expected_calibration_error, docs_decisions_chronological_split [INFERRED 0.85]
- **IDE platform stack: Theia, local FastAPI, session token** — docs_decisions_d_019, docs_decisions_d_028, docs_decisions_d_029, docs_decisions_eclipse_theia, docs_decisions_fastapi, docs_decisions_session_token [INFERRED 0.85]

## Communities (102 total, 26 thin omitted)

### Community 0 - "Java Reference Extraction"
Cohesion: 0.05
Nodes (48): Node, _compact(), extract_references(), _first_named(), Import, _is_named_member_type(), _line(), _text() (+40 more)

### Community 1 - "Dependency Graph Builder"
Cohesion: 0.07
Nodes (37): _add_structure(), build_graph(), build_graph_for_commit(), file_role(), _FileContext, _parse_missing(), _Resolution, _Resolver (+29 more)

### Community 2 - "Local API Endpoints"
Cohesion: 0.07
Nodes (33): create_app(), graph(), impact(), plugins(), risk_select(), run_selection(), compare_strategies(), _estimate_time() (+25 more)

### Community 3 - "Language Plugin Interface"
Cohesion: 0.06
Nodes (7): LanguagePlugin, JavaPlugin, load_plugins(), _major(), PluginRegistry, test_builtin_java_plugin_is_registered(), test_incompatible_and_broken_plugins_are_rejected()

### Community 4 - "CI Workflow Config"
Cohesion: 0.06
Nodes (43): run, defaults, name, runs-on, steps, jobs, ide-extension, maven-integration (+35 more)

### Community 5 - "API Request Models"
Cohesion: 0.08
Nodes (25): AnalyzeRequest, ChangeRequest, CompareRequest, loopback_host_only(), GraphRequest, _hostname(), ImpactRequest, new_token() (+17 more)

### Community 6 - "Milestone 5 Experiment"
Cohesion: 0.10
Nodes (24): _avg(), _cost_matched_and_bootstrap(), _hybrid_vs_rules(), _outcomes(), _reproducibility(), _risk_only(), _rounded(), probabilities() (+16 more)

### Community 7 - "Maven Runner & Coverage"
Cohesion: 0.11
Nodes (23): run_tests(), BuildError, _CodeIndex, _collect_results(), find_maven(), _run_maven(), run_maven_tests(), _run_per_test() (+15 more)

### Community 8 - "Git Blob Access"
Cohesion: 0.09
Nodes (22): tests(), export_commit(), list_files(), read_blobs(), _ancestors(), discover_tests(), discover_tests_for_commit(), DiscoveredTest (+14 more)

### Community 9 - "Probability Calibrators"
Cohesion: 0.11
Nodes (23): Calibrator, _logit(), brier_score(), expected_calibration_error(), reliability_bins(), _calibration_section(), run_experiment(), miscalibrated() (+15 more)

### Community 10 - "IDE Extension Package"
Cohesion: 0.07
Nodes (34): dependencies, @fontsource-variable/geist@^5.3.0, @fontsource-variable/geist-mono@^5.3.0, @theia/core@1.76.0, @theia/editor@1.76.0, @theia/filesystem@1.76.0, @theia/monaco@1.76.0, @theia/workspace@1.76.0 (+26 more)

### Community 11 - "History Dataset Builder"
Cohesion: 0.12
Nodes (14): build_dataset(), HistoryStore, ResultRecord, store(), test_failure_from_any_source_wins(), test_mine_first_parent_history_in_order(), history(), test_too_few_failures_are_warned_about() (+6 more)

### Community 12 - "Test Result Collection"
Cohesion: 0.14
Nodes (12): collect_results(), import_results(), TestCaseResult, TestClassResult, save_json(), TestRunResult, run_result(), test_collect_requires_allow_build() (+4 more)

### Community 13 - "Java Change Analysis"
Cohesion: 0.15
Nodes (26): analyze(), analyze_changes(), analyze_edit(), by_id(), edit(), java_of(), test_added_java_file_lists_all_declarations_as_added(), test_added_method_does_not_flag_the_class() (+18 more)

### Community 14 - "IDE Protocol Types"
Cohesion: 0.13
Nodes (12): AnalyzeReport, CODEDNA_SERVICE_PATH, CodeDnaStatus, ImpactReport, JavaFileAnalysis, PathStep, SelectionRun, SelectionStrategy (+4 more)

### Community 15 - "IDE Change View Rendering"
Cohesion: 0.19
Nodes (20): unique(), breakable(), changeLabel(), confidenceLabel(), fileStatusLabel(), friendlyReason(), friendlyWarning(), kindLabel() (+12 more)

### Community 16 - "JaCoCo/Surefire Reports"
Cohesion: 0.14
Nodes (14): _covered(), _float(), jvm_class_to_type_id(), parse_jacoco_report(), _parse_surefire_file(), parse_surefire_reports(), _parse_xml(), ReportError (+6 more)

### Community 17 - "Test Git Repo Helper"
Cohesion: 0.14
Nodes (16): GitRepo, project(), test_invalid_revision_is_rejected(), test_binary_file_is_flagged_with_warning(), test_filenames_with_spaces(), test_renamed_java_file_without_content_change(), test_collect_runs_each_commit_once(), test_mine_limits_and_binary_files() (+8 more)

### Community 18 - "Study Runner"
Cohesion: 0.16
Nodes (19): _agg(), _ci(), _contributing(), _cost_matched(), _fmt(), _fmt_stats(), _graph_signal(), _hierarchical_draws() (+11 more)

### Community 19 - "Sample Java Project"
Cohesion: 0.13
Nodes (4): OrderService, PriceCalculator, OrderServiceTest, PriceCalculatorTest

### Community 20 - "RTPTorrent Import"
Cohesion: 0.17
Nodes (16): run_git(), _changed_files(), _commit_meta(), _existing_commits(), import_rtptorrent(), ImportReport, list_projects(), _push_base() (+8 more)

### Community 21 - "Baseline Rankers"
Cohesion: 0.12
Nodes (12): _rules_policy(), choose(), order_by_baseline(), fit_audited(), prediction_rows(), recommend(), _history_features(), _is_file_of() (+4 more)

### Community 22 - "Cross-Project Transfer Model"
Cohesion: 0.14
Nodes (12): evaluate_target(), fit_project(), FittedProject, source_prefix_before(), dataset(), SpyRanker, test_calendar_filter_stops_at_first_excluded_commit(), test_identical_data_cannot_be_passed_as_two_projects() (+4 more)

### Community 23 - "Live Risk Decision"
Cohesion: 0.17
Nodes (17): fit_audited(), choose(), decide(), _decision(), RiskPolicy, SelectionDecision, _skip_risk(), _unfamiliar() (+9 more)

### Community 24 - "Dependency Graph Tests"
Cohesion: 0.19
Nodes (22): build(), dependency_edges(), test_duplicate_type_names_make_edges_heuristic(), test_extends_and_implements_edges(), test_file_role_uses_path_conventions(), test_generic_arguments_in_extends_are_uses(), test_graph_of_older_revision_uses_same_ids(), test_import_resolution_wins_over_same_package() (+14 more)

### Community 25 - "IDE Contributions Wiring"
Cohesion: 0.11
Nodes (7): ChangeViewContribution, TestsViewContribution, C, CODEDNA_THEME_ID, CodeDnaThemeContribution, COLORS, TOKEN_COLORS

### Community 26 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, declarationMap, downlevelIteration, emitDecoratorMetadata, esModuleInterop, experimentalDecorators, jsx (+15 more)

### Community 27 - "CLI Argument Parser"
Cohesion: 0.16
Nodes (8): _add_change_args(), _add_non_java_arg(), build_parser(), _fraction(), _non_negative_int(), git(), main(), write()

### Community 28 - "Git Change Extraction Tests"
Cohesion: 0.19
Nodes (18): extract_changes(), numbered_lines(), by_path(), test_added_java_file(), test_comparison_across_several_commits(), test_deleted_java_file(), test_directory_that_is_not_a_repository_fails_clearly(), test_empty_diff_between_identical_commits() (+10 more)

### Community 29 - "DANTE-H History Scores"
Cohesion: 0.18
Nodes (15): historical_scores(), order_history(), recommend(), _estimated_costs(), Dataset, dataset(), test_audit_needs_failures_recall_and_an_upper_bound(), test_dante_history_adapter_isolates_test_windows_and_matches_fixed_score() (+7 more)

### Community 30 - "Chronological Evaluation Metrics"
Cohesion: 0.19
Nodes (16): chronological_split(), _ordering_metrics(), apfd(), apfdc(), recall_at_budget(), time_to_first_failure(), features_of(), row() (+8 more)

### Community 31 - "Research Plan Questions"
Cohesion: 0.11
Nodes (19): Baselines B0-B9, Metrics (APFD/APFDc, PR-AUC, Brier, ECE), Prior Art to Study, RQ1: Feature Prediction of Test Failures, RQ3: Calibration Reliability, RQ4: Uncertainty-Aware Fallback, Calibration None/Platt/Isotonic (D-025), Milestone 5: Research Contribution (+11 more)

### Community 32 - "Project Rules & Plans"
Cohesion: 0.11
Nodes (17): CodeDNA Platform (D-017), AGENTS.md Contributor Rules, CodeDNA Research Plan, Evaluation Chapter Draft (REPORT_DRAFT.md), Language-Plugin Interface and Registry (D-018, D-024), Leakage-Free (commit, test) Features (D-023), Milestone 4: History and Predictive Ranking, Product Track (IDE, Plugins, Website) (+9 more)

### Community 33 - "Evaluation & Ablations"
Cohesion: 0.23
Nodes (12): evaluate(), _probability_metrics(), _ablations(), class_weight_check(), _fit(), _measure(), _ml_policy(), choose() (+4 more)

### Community 34 - "CLI Entry & Tests"
Cohesion: 0.13
Nodes (16): _json_file(), main(), test_analyze_defaults_to_method_level(), test_analyze_file_level_prints_json_report(), test_analyze_invalid_commit_exits_with_error(), test_analyze_invalid_repository_exits_with_error(), test_analyze_writes_output_file(), test_missing_required_argument_is_usage_error() (+8 more)

### Community 35 - "Early Core Decisions"
Cohesion: 0.14
Nodes (5): CodeDNA Decision Log, Geist / Geist Mono fonts, JaCoCo, JavaParser symbol solver, scikit-learn

### Community 36 - "Architecture Pipeline Docs"
Cohesion: 0.16
Nodes (15): Change-Impact Analyzer (compute_impact, D-012), CodeDNA Analysis Pipeline, Dependency Graph Builder (dependency_graph), Failure-Probability Model (models), Git Change Extractor (git_analysis.changes), Java Declaration Mapper (java_analysis), Known Limitations (class-level impact, no reflection/DI edges), Probability Calibration (Platt / isotonic) (+7 more)

### Community 37 - "IDE Workspace Service"
Cohesion: 0.13
Nodes (3): CodeDnaWorkspace, TestsViewWidget, CodeDnaService

### Community 38 - "Dataset & Leakage Guard"
Cohesion: 0.14
Nodes (12): Test History Store and Mining (test_history), RTPTorrent v1.1 (Mattis et al., MSR 2020, doi:10.1145/3379597.3387458), Eleven Imported RTPTorrent Projects, CI Recording Gaps (graylog2-server, jOOQ), RTPTorrent Primary Dataset, RTPTorrent to CodeDNA History Store Mapping, Histogram Gradient Boosting (balanced weights), Logistic Regression Ranker (+4 more)

### Community 39 - "CI Jobs & Starter Brief"
Cohesion: 0.12
Nodes (17): CI workflow (GitHub Actions), CI job: ide-extension (TypeScript build), CI job: maven-integration (real Maven/JaCoCo), CI job: python-tests (Ubuntu/Windows, py3.11/3.12), CI job: sample-java-project (Maven + JUnit 5), CodeDNA FYP Starter brief, Cytoscape.js, Ekstazi (+9 more)

### Community 40 - "Runner Reproducibility Tests"
Cohesion: 0.18
Nodes (9): test_runner_reproducibility_and_resume_fingerprints(), saved_study(), test_budget_averages_seeds_then_projects_without_zero_filling(), test_calibration_and_stopping_use_common_cohorts(), test_different_risk_targets_cannot_share_a_target_line(), test_inconsistent_budget_grid_is_rejected(), test_missing_seed_does_not_silently_shrink_the_study(), test_nonfinite_numbers_are_rejected() (+1 more)

### Community 41 - "Transfer & B10 Protocols"
Cohesion: 0.12
Nodes (13): Fixed DANTE-H / B10 extension protocol — 2026-10-24, Fixed experiment, Independent baseline and attribution, Operational gate (separate from this retrospective experiment), Revised adapter, frozen before its own results, Complete Java recommendation/execution workflow, Direct selected execution, First use: no history (+5 more)

### Community 42 - "IDE Root Package"
Cohesion: 0.12
Nodes (16): description, devDependencies, @theia/cli@1.76.0, engines, node, npm, @theia/cli, name (+8 more)

### Community 43 - "Transfer Runner Tests"
Cohesion: 0.20
Nodes (7): test_runner_keeps_unavailable_calendar_direction_and_can_resume(), main(), markdown(), _mean(), run(), _study_helpers(), summarise()

### Community 44 - "IDE Screenshot UI"
Cohesion: 0.16
Nodes (13): Affected Tests Only Selection Mode, Changes Panel (left sidebar), CodeDNA IDE (screenshot), Compare Baseline Selector (My last commit), Editor Area (pom.xml open), Change Impact Summary (files changed, parts touched, classes affected), OrderTotalsTest, Per-Test Selection Reasons (+5 more)

### Community 45 - "Subset Download Tests"
Cohesion: 0.13
Nodes (4): test_archive_paths_cannot_escape_output(), test_subset_download_filters_shared_map_and_verifies_restart(), __init__(), test_preparation_recovers_database_when_feature_csv_is_cached()

### Community 46 - "Transfer Protocol Docs"
Cohesion: 0.18
Nodes (14): Project-Disjoint Transfer Validation (models.transfer, D-039), HTTP Byte-Range Subset Recovery (fetch_rtptorrent_subset.py), Commands, Cross-project transfer protocol, Data recovery, Transfer Feature Rebuild (prepare_transfer_features.py), Four-Project Cohort (HikariCP, LittleProxy, jade4j, wicket-bootstrap), Measures and decision rules (+6 more)

### Community 47 - "Theia Dependencies"
Cohesion: 0.13
Nodes (15): dependencies, @theia/editor@1.76.0, @theia/filesystem@1.76.0, @theia/markers@1.76.0, @theia/monaco@1.76.0, @theia/navigator@1.76.0, @theia/process@1.76.0, @theia/workspace@1.76.0 (+7 more)

### Community 48 - "Safe Git Wrapper"
Cohesion: 0.21
Nodes (7): GitCommandError, resolve_commit(), resolve_repository(), _run(), run_git_bytes(), test_bare_repositories_are_accepted(), test_bounded_cache_gives_identical_graphs()

### Community 49 - "RTPTorrent Subset Fetch"
Cohesion: 0.20
Nodes (4): fetch(), main(), safe_target(), selected_entry()

### Community 50 - "Study Figure Script"
Cohesion: 0.24
Nodes (8): collect_data(), load(), export(), main(), _number(), _reject_constant(), render_figures(), _stats()

### Community 51 - "Class-Weight Check"
Cohesion: 0.33
Nodes (9): _b10_pooled(), _ci(), _fmt(), _load_run_study(), main(), _mean(), run_project(), summarise() (+1 more)

### Community 52 - "Graph & Mapping Milestones"
Cohesion: 0.20
Nodes (9): Method-Level Call Edges (Deferred, D-010), Milestone 2: Dependency Graph, Milestone 3: Test Mapping, codedna graph, codedna impact, codedna run-tests (--allow-build), codedna select / compare, codedna tests (+1 more)

### Community 53 - "Experiment Protocol Decisions"
Cohesion: 0.23
Nodes (7): APFD / APFDc metrics, class_weight_check() and MLRanker class_weight option, cross-project-2026-10-24 FINDINGS.md, Expected Calibration Error (ECE) and Brier score, Isotonic regression calibration, Platt scaling, RQ3 / RQ4 / RQ5 research questions

### Community 54 - "Scope & Platform Decisions"
Cohesion: 0.20
Nodes (6): CodeDNA (change-impact + regression test selection platform), JavaPlugin, LanguagePlugin protocol and registry, Maven, unanalysed_changes reporting, Project Specification

### Community 55 - "Platform Components"
Cohesion: 0.20
Nodes (9): CodeDNA IDE (Eclipse Theia 1.76, Electron), Built-in Java Plugin, Local API (codedna serve, FastAPI, D-028), Per-test JaCoCo Coverage Mapping (D-015), Platform Website and Plugin Catalogue, Language Plugin Registry (codedna.languages, D-024), Target Product Architecture (D-017 - D-020), Apache Commons CSV Self-Collected Dataset (+1 more)

### Community 56 - "Selection Policies"
Cohesion: 0.25
Nodes (8): Transfer Measures and Decision Rules, B3 Recent-Failures-then-Shortest Rule, B9 / B9r / B9n Fallback Policies, Hierarchical Percentile Bootstrap Intervals, RQ2: Time Saved at Detection Target, RQ4: Fallback and Risk-Based Stopping, Selection Policies B0-B10, wicket-bootstrap Drives Selection Differences

### Community 57 - "Cost-Matched & B10 Decisions"
Cohesion: 0.22
Nodes (6): Matplotlib (plots extra), Shared bounded LRU parse cache (4,000 blobs), B10 hybrid: rules order, calibrated stopping, B3 rules order (recent failures, then shortest), B8 calibrated selector with time budget, study11 FINDINGS.md

### Community 58 - "IDE Comparison Presets"
Cohesion: 0.35
Nodes (7): ComparisonPreset, PRESETS, friendlyError, ComparePicker(), ErrorNotice(), FirstRun(), Spinner()

### Community 59 - "Electron App Package"
Cohesion: 0.22
Nodes (10): devDependencies, electron@42.8.1, @theia/cli@1.76.0, @theia/cli, main, name, private, productName (+2 more)

### Community 60 - "History Mining"
Cohesion: 0.27
Nodes (3): _count(), mine_history(), CommitRecord

### Community 61 - "IDE & API Decisions"
Cohesion: 0.27
Nodes (4): Eclipse Theia, FastAPI, NetworkX, X-CodeDNA-Token per-session token

### Community 62 - "Baseline Policy Decisions"
Cohesion: 0.22
Nodes (8): B0 retest-all, B4 static dependency selection proxy, B6 change-features-only model, B7 trained ML model, B9 calibrated risk-aware fallback, B9n unfamiliar-change rule only, B9r risk-only fallback, wicket-bootstrap project

### Community 64 - "Electron App Config"
Cohesion: 0.20
Nodes (10): applicationName, defaultTheme, electron, reloadOnReconnect, windowOptions, config, theia, frontend (+2 more)

### Community 66 - "Git Error Types"
Cohesion: 0.28
Nodes (3): CodeDNAGitError, InvalidCommitError, InvalidRepositoryError

### Community 68 - "Select & Compare Commands"
Cohesion: 0.36
Nodes (5): compare(), select(), _json_file(), load_coverage_map(), load_results()

### Community 70 - "RTPTorrent Import Tests"
Cohesion: 0.36
Nodes (3): dataset(), test_repeated_runs_in_one_job_are_merged_and_failure_wins(), write_csv()

### Community 71 - "Transfer Feature Prep"
Cohesion: 0.36
Nodes (3): test_export_fingerprints_inputs_and_is_repeatable(), main(), prepare()

### Community 72 - "Plugin Catalogue Decisions"
Cohesion: 0.33
Nodes (3): HikariCP project, Plugin catalogue (versioned JSON index), tree-sitter / tree-sitter-java

### Community 73 - "IDE & Local API Milestone"
Cohesion: 0.40
Nodes (5): CodeDNA Dark Theme (D-030, D-031), Local API FastAPI (D-019, D-028), Milestone 6: CodeDNA IDE and FYP Demo, codedna serve (Local API), CodeDNA IDE (Theia 1.76 + Electron)

### Community 74 - "CLI Run Commands"
Cohesion: 0.67
Nodes (5): _import_rtptorrent(), _run_history(), _run_on_dataset(), _run_tests(), _write_json()

### Community 76 - "RTPTorrent & SQLite Decisions"
Cohesion: 0.33
Nodes (4): Bare repository support (resolve_repository), Mattis et al., MSR 2020 (doi:10.1145/3379597.3387458), RTPTorrent v1.1 dataset, SQLite (sqlite3)

### Community 77 - "IDE Editor Preferences"
Cohesion: 0.33
Nodes (6): preferences, editor.fontFamily, editor.fontSize, editor.lineHeight, workbench.colorTheme, workbench.iconTheme

### Community 78 - "Validation & Demo Setup"
Cohesion: 0.40
Nodes (4): Portable JDK 17 + Maven 3.10 Runtime, Demo Repository (make_demo_repo.py), Real Maven/JUnit/JaCoCo Integration Test, Sample Java Project (OrderService, PriceCalculator)

### Community 79 - "Package Scripts"
Cohesion: 0.40
Nodes (5): scripts, bundle, rebuild, start, watch

### Community 82 - "Milestone 1 Analyze"
Cohesion: 0.67
Nodes (3): Milestone 1: Git and Java Change Analysis, tree-sitter Pinned <0.26 (D-033), codedna analyze

## Ambiguous Edges - Review These
- `Thesis Claim: Calibrated Stopping Rule on Simple Ordering` → `Candidate Contribution: Hybrid Calibrated Selector with Fallback`  [AMBIGUOUS]
  docs/RESEARCH_PLAN.md · relation: conceptually_related_to
- `D-008 Tree-sitter Java for syntax-level declaration extraction` → `D-020 Platform website and plugin distribution`  [AMBIGUOUS]
  docs/DECISIONS.md · relation: conceptually_related_to
- `D-011 Plain dictionaries, not NetworkX, for the graph` → `Shared bounded LRU parse cache (4,000 blobs)`  [AMBIGUOUS]
  docs/DECISIONS.md · relation: conceptually_related_to

## Knowledge Gaps
- **70 isolated node(s):** `example:sample-java-project`, `Tree-sitter Java`, `Cytoscape.js`, `Tests to run view`, `Ekstazi` (+65 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 516 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CodeDNA Decision Log` connect `Early Core Decisions` to `Plugin Catalogue Decisions`, `RTPTorrent & SQLite Decisions`, `Git CLI Decision`, `Experiment Protocol Decisions`, `Scope & Platform Decisions`, `Cost-Matched & B10 Decisions`, `IDE & API Decisions`, `Baseline Policy Decisions`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `create_app()` (e.g. with `require_token()` and `ReportError`) actually correct?**
  _`create_app()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `example:sample-java-project`, `Tree-sitter Java`, `Cytoscape.js` to the rest of the system?**
  _70 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Java Reference Extraction` be split into smaller, more focused modules?**
  _Cohesion score 0.05337078651685393 - nodes in this community are weakly interconnected._
- **Why does `D-014 Running builds is opt-in and isolated` connect `Scope & Platform Decisions` to `Early Core Decisions`, `RTPTorrent & SQLite Decisions`, `Maven Runner & Coverage`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Thesis Claim: Calibrated Stopping Rule on Simple Ordering` and `Candidate Contribution: Hybrid Calibrated Selector with Fallback`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `D-008 Tree-sitter Java for syntax-level declaration extraction` and `D-020 Platform website and plugin distribution`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._