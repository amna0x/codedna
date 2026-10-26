# Graph Report - codedna  (2026-10-26)

## Corpus Check
- 224 files · ~198,759 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 3, .css 3, .example 1)

## Summary
- 3196 nodes · 8109 edges · 190 communities (154 shown, 36 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 714 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8183d2d1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- find_replay_sources
- impact.py
- select_tests
- languages.py
- CI Workflow Config
- API Request Models
- experiment.py
- maven.py
- test_test_discovery.py
- Probability Calibrators
- IDE Extension Package
- HistoryStore
- TestRunResult
- Java Change Analysis
- codedna-protocol.ts
- change-view-widget.tsx
- reports.py
- .commit
- Study Runner
- org.junit.jupiter.api.Test
- RTPTorrent Import
- test_history.py
- Cross-Project Transfer Model
- compute_impact
- Dependency Graph Tests
- codedna-frontend-module.ts
- TypeScript Config
- mcp_server.py
- Git Change Extraction Tests
- codedna_java/live.py
- Row
- Research Plan Questions
- Project Rules & Plans
- replay.py
- main
- Early Core Decisions
- Architecture Pipeline Docs
- TestsViewWidget
- Dataset & Leakage Guard
- CI Jobs & Starter Brief
- pytest
- Complete Java recommendation/execution workflow
- IDE Root Package
- prepare_confirmatory.py
- IDE Screenshot UI
- .handle
- Transfer Protocol Docs
- Theia Dependencies
- git.py
- fetch_rtptorrent_subset.py
- baselines.py
- json
- Graph & Mapping Milestones
- Experiment Protocol Decisions
- Scope & Platform Decisions
- Platform Components
- Selection Policies
- Cost-Matched & B10 Decisions
- HistoryViewWidget
- Electron App Package
- check
- IDE & API Decisions
- Baseline Policy Decisions
- CodeDNA — full handoff blueprint (2026-10-26)
- Electron App Config
- swebench_brake_study.py
- TestRunResult
- Electron Bundle Gen
- ReplayViewWidget
- conftest.py
- codedna_java/mapping.py
- hashlib
- Plugin Catalogue Decisions
- IDE & Local API Milestone
- cli.py
- BoundedParseCache
- RTPTorrent & SQLite Decisions
- CodeGraph
- Validation & Demo Setup
- Package Scripts
- Platform Website Milestone
- test_python_plugin.py
- Milestone 1 Analyze
- Local Graphify Tooling
- graph-view-widget.tsx
- Study Figure Provenance
- RQ5 Graph Features
- run_rolling_evidence.py
- Node
- Theia Electron
- Theia Messages
- CodeDnaService
- codedna_python/parser.py
- CLAUDE.md
- RQ2 Test Time Saved
- Progress Report Rule
- codedna
- Sample Project Example
- codedna_python/mapping.py
- app.py
- build.py
- test_policy.py
- codedna_java/discovery.py
- create_app
- policy.py
- .from_csv
- JavaPlugin
- electron-builder.yml
- codedna_python/discovery.py
- CodeDNA: system chapters (draft)
- test_live_risk.py
- test_pts_check.py
- RiskPolicy
- importlib_util
- _CodeIndex
- resolve_commit
- dataclasses
- test_desktop_bundle.py
- continue_confirmatory.py
- make_hikaricp_demo.py
- sys
- _Resolver
- workflow.test.cjs
- build-core.cjs
- runner.py
- test_replay.py
- Java workflow handoff
- CodeDNA as a test brake for AI coding agents (report chapter draft)
- codedna-theme.ts
- PythonPlugin
- test_brake_planning.py
- dataset
- codedna_python/builder.py
- CodeDNA README
- run_crc_check.py
- test_confirmatory_continuation.py
- .handle
- type_kinds
- CodeDNA FYP Starter brief
- Agent brake study on public SWE-bench Java patches — protocol
- Nine-project confirmatory results — 2026-10-26
- devDependencies
- CombinedDiscovery
- run_tests
- test_rolling_evidence.py
- _Resolver
- 4. Design
- test_agent_brake.py
- test_demo_agent_brake.py
- Conformal risk control stopping protocol — 2026-10-26
- Predictive Test Selection baseline protocol — 2026-10-25
- CodeDNA compared with closely related work (updated 2026-10-25)
- Cross-Project Transfer Test (D-039)
- Tuned-threshold gate protocol — 2026-10-26
- CodeDNA Roadmap
- test_worktree_snapshot.py
- test_language_plugins.py
- Confirmatory data preparation — 2026-10-25
- Failure-conditional conformal stopping protocol — 2026-10-26
- OrderService
- Failure-conditional tuned gate protocol (B13f) — 2026-10-26
- scripts
- Recovered Claude work and next priorities — 2026-10-24
- Fixed DANTE-H / B10 extension protocol — 2026-10-24
- project
- 5. Implementation
- prediction_rows
- theiaPlugins
- @theia/monaco@1.76.0
- @theia/navigator@1.76.0
- @theia/plugin-ext@1.76.0
- @theia/plugin-ext-vscode@1.76.0
- @theia/process@1.76.0
- codedna-java/README.md
- codedna-python/README.md
- RemoteZip
- Test brake for AI coding agents — setup guide
- 2. Background and related work
- test_swebench_brake_study.py
- PolicyRule
- _structural
- SpyRanker
- summarise

## God Nodes (most connected - your core abstractions)
1. `create_app()` - 85 edges
2. `main()` - 71 edges
3. `Dataset` - 71 edges
4. `select_tests()` - 64 edges
5. `Row` - 60 edges
6. `resolve_repository()` - 52 edges
7. `HistoryStore` - 51 edges
8. `compute_impact()` - 47 edges
9. `TestRunResult` - 44 edges
10. `extract_changes()` - 43 edges

## Surprising Connections (you probably didn't know these)
- `1. Ground rules (read before touching anything)` --references--> `run_git()`  [INFERRED]
  docs/HANDOFF.md → backend/codedna/git_analysis/git.py
- `Policies per block` --references--> `match_budget()`  [INFERRED]
  docs/EVIDENCE_STUDY_PROTOCOL.md → backend/codedna/models/uncertainty.py
- `Analyses` --references--> `match_budget()`  [INFERRED]
  docs/PTS_BASELINE_PROTOCOL.md → backend/codedna/models/uncertainty.py
- `4.2 Platform structure (D-017, D-018)` --references--> `LanguagePlugin`  [INFERRED]
  docs/REPORT_SYSTEM_DRAFT.md → backend/codedna/plugins/base.py
- `6.5 End-to-end proof — DONE (2026-10-26)` --references--> `threshold()`  [INFERRED]
  docs/HANDOFF.md → backend/codedna/selection/conformal.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Baseline selection policies compared in the study** — docs_decisions_policy_b0, docs_decisions_policy_b3, docs_decisions_policy_b4, docs_decisions_policy_b8, docs_decisions_policy_b9, docs_decisions_policy_b9r, docs_decisions_policy_b9n, docs_decisions_policy_b10 [EXTRACTED 1.00]
- **Transfer validation data recovery and evaluation pipeline** — docs_cross_project_protocol_byte_range_recovery, docs_cross_project_protocol_feature_rebuild, docs_architecture_transfer_validation, docs_dataset_plan_transfer_subset_recovery [EXTRACTED 1.00]
- **Core CLI Analysis Pipeline (analyze, graph, impact, select)** — readme_cli_analyze, readme_cli_graph, readme_cli_impact, readme_cli_select_compare, readme_cli_run_tests [INFERRED 0.85]
- **Calibration fitted on validation and evaluated by ECE/Brier** — docs_decisions_d_025, docs_decisions_platt_scaling, docs_decisions_isotonic_regression, docs_decisions_expected_calibration_error, docs_decisions_chronological_split [INFERRED 0.85]
- **IDE platform stack: Theia, local FastAPI, session token** — docs_decisions_d_019, docs_decisions_d_028, docs_decisions_d_029, docs_decisions_eclipse_theia, docs_decisions_fastapi, docs_decisions_session_token [INFERRED 0.85]
- **Change impact to test selection flow in the IDE** — docs_ide_screenshot_compare_baseline_selector, docs_ide_screenshot_changes_panel, docs_ide_screenshot_impact_summary, docs_ide_screenshot_tests_to_run_panel, docs_ide_screenshot_per_test_reasons [INFERRED 0.85]
- **Platform Product Components (D-017)** — agents_platform_d017, readme_codedna_ide, docs_roadmap_local_api, docs_roadmap_language_plugin_interface, docs_roadmap_plugin_catalogue [INFERRED 0.85]
- **Research Questions and Their Study Results** — docs_research_plan_rq1, docs_research_plan_rq3, docs_research_plan_rq4, docs_research_plan_rq5, memory_rq1_result, memory_rq3_result, memory_rq4_result, memory_rq5_result [INFERRED 0.85]
- **Calibrated risk-based stopping flow (model -> calibration -> skip risk -> B10)** — docs_architecture_failure_probability_model, docs_architecture_probability_calibration, docs_architecture_skip_risk_formula, docs_report_draft_b10_hybrid_policy [INFERRED 0.85]
- **Temporal leakage prevention across features, splits and transfer** — docs_architecture_leakage_guard, docs_report_draft_chronological_split, docs_cross_project_protocol_source_prefix_restriction [INFERRED 0.85]

## Communities (190 total, 36 thin omitted)

### Community 0 - "find_replay_sources"
Cohesion: 0.15
Nodes (15): replay(), replay_overview_(), replay_sources(), _candidates(), find_replay_sources(), load_report(), _mean(), _project_name() (+7 more)

### Community 1 - "impact.py"
Cohesion: 0.15
Nodes (13): _candidate_tests(), _collect_seeds(), add(), explanation_graph(), _impacted(), _impacted_files(), ImpactedNode, ImpactReport (+5 more)

### Community 2 - "select_tests"
Cohesion: 0.18
Nodes (21): select_tests(), commit(), coverage_map(), history(), results(), selected(), test_added_member_selects_tests_covering_its_class(), test_changed_test_class_is_always_selected() (+13 more)

### Community 3 - "languages.py"
Cohesion: 0.12
Nodes (14): plugin_catalogue(), api_compatible(), LanguagePlugin, build_graph(), commit_graph(), file_language(), _has_files(), installed() (+6 more)

### Community 4 - "CI Workflow Config"
Cohesion: 0.06
Nodes (43): run, defaults, name, runs-on, steps, jobs, ide-extension, maven-integration (+35 more)

### Community 5 - "API Request Models"
Cohesion: 0.14
Nodes (15): loopback_host_only(), _hostname(), new_token(), is_loopback(), serve(), client(), test_analysis_endpoints_return_cli_json(), test_catalogue_versions_carry_the_core_compatibility_answer() (+7 more)

### Community 6 - "experiment.py"
Cohesion: 0.09
Nodes (22): Calibrator, _logit(), brier_score(), expected_calibration_error(), reliability_bins(), _ablations(), _avg(), _calibration_section() (+14 more)

### Community 7 - "maven.py"
Cohesion: 0.09
Nodes (25): export_commit(), test_coverage_mapping_and_strategy_comparison_with_real_maven(), test_build_failure_is_reported_as_warning(), test_build_requires_explicit_permission(), test_cli_refuses_without_allow_build(), test_full_suite_run_writes_results_and_keeps_worktree_clean(), test_missing_maven_is_reported(), test_output_directory_must_be_empty() (+17 more)

### Community 8 - "test_test_discovery.py"
Cohesion: 0.33
Nodes (9): discover(), test_abstract_base_tests_are_inherited(), test_junit3_methods_through_repository_base_classes(), test_junit3_test_case_methods_are_discovered(), test_junit4_framework_detected(), test_junit5_test_class_with_methods(), test_nested_test_classes_belong_to_top_level_class(), test_testng_is_reported_as_unsupported() (+1 more)

### Community 9 - "Probability Calibrators"
Cohesion: 0.13
Nodes (22): run_experiment(), probabilities(), _summary(), test_cli_experiment_replay_flag_records_the_trace(), traced(), miscalibrated(), synthetic_dataset(), test_calibrator_errors() (+14 more)

### Community 10 - "IDE Extension Package"
Cohesion: 0.11
Nodes (24): dependencies, cytoscape@3.30.4, @fontsource-variable/geist@^5.3.0, @fontsource-variable/geist-mono@^5.3.0, @theia/core@1.76.0, @theia/editor@1.76.0, @theia/filesystem@1.76.0, @theia/monaco@1.76.0 (+16 more)

### Community 11 - "HistoryStore"
Cohesion: 0.10
Nodes (15): build_dataset(), HistoryStore, ResultRecord, store(), test_failure_from_any_source_wins(), test_mine_first_parent_history_in_order(), test_import_large_push_keeps_the_correct_tip_with_bounded_git_arguments(), history() (+7 more)

### Community 12 - "TestRunResult"
Cohesion: 0.11
Nodes (20): _check(), _digest(), first_parent_line(), ignore_outputs(), record_run(), record_runs(), refusal(), _refuse_all() (+12 more)

### Community 13 - "Java Change Analysis"
Cohesion: 0.14
Nodes (27): analyze_changes(), analyze_edit(), by_id(), edit(), java_of(), test_added_java_file_lists_all_declarations_as_added(), test_added_method_does_not_flag_the_class(), test_change_spanning_two_methods() (+19 more)

### Community 14 - "codedna-protocol.ts"
Cohesion: 0.07
Nodes (21): CODEDNA_SERVICE_PATH, CodeDnaStatus, InstalledPlugin, JavaFileAnalysis, PathStep, PluginCatalogueView, PluginChange, ProjectRun (+13 more)

### Community 15 - "change-view-widget.tsx"
Cohesion: 0.10
Nodes (30): ChangeViewWidget, mappingOf(), unique(), CodeDnaComparison, ComparisonPreset, PRESETS, bareId(), breakable() (+22 more)

### Community 16 - "reports.py"
Cohesion: 0.14
Nodes (14): test_all_skipped_class_is_skipped_not_failed(), test_jacoco_report_gives_covered_types_and_lines(), test_jvm_class_names_map_to_type_ids(), test_malformed_report_raises_report_error(), test_surefire_results_are_aggregated_per_top_level_class(), _covered(), _float(), JacocoCoverage (+6 more)

### Community 17 - ".commit"
Cohesion: 0.10
Nodes (29): test_project_without_tests_checks_nothing(), project(), java_project(), python_project(), test_invalid_revision_is_rejected(), by_path(), test_added_java_file(), test_comparison_across_several_commits() (+21 more)

### Community 18 - "Study Runner"
Cohesion: 0.10
Nodes (27): Data and project sets, Gate analysis, Policies per block, Primary analysis, Question, Reporting and reproducibility, Rolling-origin design, Rolling-origin evidence study protocol — 2026-10-24 (+19 more)

### Community 19 - "org.junit.jupiter.api.Test"
Cohesion: 0.23
Nodes (3): Demo, OrderServiceTest, PriceCalculatorTest

### Community 20 - "RTPTorrent Import"
Cohesion: 0.15
Nodes (17): _changed_files(), _commit_meta(), _existing_commits(), import_rtptorrent(), ImportReport, list_projects(), _push_base(), _read_built_commits() (+9 more)

### Community 21 - "test_history.py"
Cohesion: 0.13
Nodes (8): CodeDNAGitError, collect_results(), import_results(), _count(), mine_history(), test_collect_requires_allow_build(), test_collect_runs_each_commit_once(), test_import_results_and_warn_about_unknown_commits()

### Community 22 - "Cross-Project Transfer Model"
Cohesion: 0.17
Nodes (17): chronological_split(), _reproducibility(), evaluate_target(), fit_project(), FittedProject, source_prefix_before(), Dataset, _warn_if_few_failures() (+9 more)

### Community 23 - "compute_impact"
Cohesion: 0.25
Nodes (16): compute_impact(), commit_files(), impacted_by_id(), test_comment_only_change_has_no_impact(), test_confirmed_path_is_preferred_over_shorter_heuristic_path(), test_deleted_class_impacts_its_former_dependents(), test_deleted_test_is_not_a_candidate(), test_explanation_graph_groups_nodes_by_package_and_counts_them() (+8 more)

### Community 24 - "Dependency Graph Tests"
Cohesion: 0.16
Nodes (28): build(), dependency_edges(), test_duplicate_type_names_make_edges_heuristic(), test_extends_and_implements_edges(), test_file_role_uses_path_conventions(), test_generic_arguments_in_extends_are_uses(), test_graph_of_older_revision_uses_same_ids(), test_import_resolution_wins_over_same_package() (+20 more)

### Community 25 - "codedna-frontend-module.ts"
Cohesion: 0.14
Nodes (7): ChangeViewContribution, GraphViewContribution, HistoryViewContribution, PluginsViewContribution, ReplayViewContribution, TestsViewContribution, withProgress()

### Community 26 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, declarationMap, downlevelIteration, emitDecoratorMetadata, esModuleInterop, experimentalDecorators, jsx (+15 more)

### Community 27 - "mcp_server.py"
Cohesion: 0.17
Nodes (7): _content(), _error(), _impact(), _patterns(), _result(), _risk_target(), ToolError

### Community 28 - "Git Change Extraction Tests"
Cohesion: 0.17
Nodes (14): extract_changes(), _list_changed_paths(), numbered_lines(), test_binary_file_is_flagged_with_warning(), test_directory_that_is_not_a_repository_fails_clearly(), test_empty_diff_between_identical_commits(), test_file_instead_of_directory_fails_clearly(), test_invalid_commit_fails_clearly() (+6 more)

### Community 29 - "codedna_java/live.py"
Cohesion: 0.22
Nodes (4): order_history(), _estimated_costs(), fit_audited(), recommend()

### Community 30 - "Row"
Cohesion: 0.14
Nodes (22): evaluate(), _ordering_metrics(), _probability_metrics(), _fit(), apfd(), apfdc(), recall_at_budget(), time_to_first_failure() (+14 more)

### Community 31 - "Research Plan Questions"
Cohesion: 0.17
Nodes (13): Baselines B0-B9, Metrics (APFD/APFDc, PR-AUC, Brier, ECE), RQ1: Feature Prediction of Test Failures, RQ3: Calibration Reliability, RQ4: Uncertainty-Aware Fallback, Calibration None/Platt/Isotonic (D-025), Milestone 5: Research Contribution, Risk-Aware Selection (D-026) (+5 more)

### Community 32 - "Project Rules & Plans"
Cohesion: 0.16
Nodes (10): CodeDNA Research Plan, Evaluation Chapter Draft (REPORT_DRAFT.md), Language-Plugin Interface and Registry (D-018, D-024), Leakage-Free (commit, test) Features (D-023), Milestone 4: History and Predictive Ranking, Second Language Plugin (Later), SQLite History Store (D-021), scripts/make_study_figures.py (D-038) (+2 more)

### Community 33 - "replay.py"
Cohesion: 0.13
Nodes (16): _check(), _commits_from_per_commit(), _commits_from_trace(), _cumulative(), _events(), _fill_from_report(), _number(), replay_timeline() (+8 more)

### Community 34 - "main"
Cohesion: 0.12
Nodes (17): _json_file(), main(), test_analyze_defaults_to_method_level(), test_analyze_file_level_prints_json_report(), test_analyze_invalid_commit_exits_with_error(), test_analyze_invalid_repository_exits_with_error(), test_analyze_writes_output_file(), test_missing_required_argument_is_usage_error() (+9 more)

### Community 35 - "Early Core Decisions"
Cohesion: 0.12
Nodes (5): CodeDNA Decision Log, Geist / Geist Mono fonts, codedna.git_analysis.git.run_git, PyDriller, scikit-learn

### Community 36 - "Architecture Pipeline Docs"
Cohesion: 0.16
Nodes (15): Change-Impact Analyzer (compute_impact, D-012), CodeDNA Analysis Pipeline, Dependency Graph Builder (dependency_graph), Failure-Probability Model (models), Git Change Extractor (git_analysis.changes), Java Declaration Mapper (java_analysis), Known Limitations (class-level impact, no reflection/DI edges), Probability Calibration (Platt / isotonic) (+7 more)

### Community 38 - "Dataset & Leakage Guard"
Cohesion: 0.14
Nodes (12): Test History Store and Mining (test_history), RTPTorrent v1.1 (Mattis et al., MSR 2020, doi:10.1145/3379597.3387458), Eleven Imported RTPTorrent Projects, CI Recording Gaps (graylog2-server, jOOQ), RTPTorrent Primary Dataset, RTPTorrent to CodeDNA History Store Mapping, Histogram Gradient Boosting (balanced weights), Logistic Regression Ranker (+4 more)

### Community 39 - "CI Jobs & Starter Brief"
Cohesion: 0.22
Nodes (9): CI workflow (GitHub Actions), CI job: ide-extension (TypeScript build), CI job: maven-integration (real Maven/JaCoCo), CI job: python-tests (Ubuntu/Windows, py3.11/3.12), CI job: sample-java-project (Maven + JUnit 5), JaCoCo, Changes view, Tests to run view (+1 more)

### Community 40 - "pytest"
Cohesion: 0.16
Nodes (12): load(), test_sample_is_seeded_stratified_and_never_overwrites(), test_score_counts_labels_and_rejects_unlabelled_rows(), saved_study(), test_budget_averages_seeds_then_projects_without_zero_filling(), test_calibration_and_stopping_use_common_cohorts(), test_different_risk_targets_cannot_share_a_target_line(), test_export_fingerprints_inputs_and_is_repeatable() (+4 more)

### Community 41 - "Complete Java recommendation/execution workflow"
Cohesion: 0.33
Nodes (6): Complete Java recommendation/execution workflow, Direct selected execution, First use: no history, Prepare trustworthy target history, Remaining original scope, What risk validation means

### Community 42 - "IDE Root Package"
Cohesion: 0.12
Nodes (16): description, devDependencies, @theia/cli@1.76.0, engines, node, npm, @theia/cli, name (+8 more)

### Community 43 - "prepare_confirmatory.py"
Cohesion: 0.39
Nodes (4): main(), new_projects(), _script(), short_name()

### Community 44 - "IDE Screenshot UI"
Cohesion: 0.16
Nodes (13): Affected Tests Only Selection Mode, Changes Panel (left sidebar), CodeDNA IDE (screenshot), Compare Baseline Selector (My last commit), Editor Area (pom.xml open), Change Impact Summary (files changed, parts touched, classes affected), OrderTotalsTest, Per-Test Selection Reasons (+5 more)

### Community 45 - ".handle"
Cohesion: 0.33
Nodes (3): test_mcp_python_plan_is_not_an_error(), test_subset_download_filters_shared_map_and_verifies_restart(), __init__()

### Community 46 - "Transfer Protocol Docs"
Cohesion: 0.20
Nodes (13): Project-Disjoint Transfer Validation (models.transfer, D-039), HTTP Byte-Range Subset Recovery (fetch_rtptorrent_subset.py), Commands, Cross-project transfer protocol, Data recovery, Transfer Feature Rebuild (prepare_transfer_features.py), Four-Project Cohort (HikariCP, LittleProxy, jade4j, wicket-bootstrap), Measures and decision rules (+5 more)

### Community 47 - "Theia Dependencies"
Cohesion: 0.12
Nodes (17): dependencies, codedna-extension@0.1.0, @theia/core@1.76.0, @theia/editor@1.76.0, @theia/filesystem@1.76.0, @theia/markers@1.76.0, @theia/preferences@1.76.0, @theia/terminal@1.76.0 (+9 more)

### Community 48 - "git.py"
Cohesion: 0.09
Nodes (16): _dirty_submodules(), _output_excludes(), _run(), run_git(), run_git_bytes(), snapshot_worktree(), _tips(), large_push() (+8 more)

### Community 49 - "fetch_rtptorrent_subset.py"
Cohesion: 0.18
Nodes (5): fetch(), main(), remote_projects(), safe_target(), selected_entry()

### Community 50 - "baselines.py"
Cohesion: 0.15
Nodes (8): compare_strategies(), _estimate_time(), _select_by_coverage(), pick(), SelectedTest, SelectionError, SelectionReport, CoverageMap

### Community 51 - "json"
Cohesion: 0.06
Nodes (37): build_command(), main(), write_manifest(), _b10_pooled(), _ci(), _fmt(), _load_run_study(), main() (+29 more)

### Community 52 - "Graph & Mapping Milestones"
Cohesion: 0.20
Nodes (9): Method-Level Call Edges (Deferred, D-010), Milestone 2: Dependency Graph, Milestone 3: Test Mapping, codedna graph, codedna impact, codedna run-tests (--allow-build), codedna select / compare, codedna tests (+1 more)

### Community 53 - "Experiment Protocol Decisions"
Cohesion: 0.21
Nodes (8): APFD / APFDc metrics, class_weight_check() and MLRanker class_weight option, cross-project-2026-10-24 FINDINGS.md, Expected Calibration Error (ECE) and Brier score, Isotonic regression calibration, Platt scaling, RQ3 / RQ4 / RQ5 research questions, RTPTorrent v1.1 dataset

### Community 54 - "Scope & Platform Decisions"
Cohesion: 0.25
Nodes (5): JaCoCo, JavaPlugin, LanguagePlugin protocol and registry, Maven, unanalysed_changes reporting

### Community 55 - "Platform Components"
Cohesion: 0.20
Nodes (9): CodeDNA IDE (Eclipse Theia 1.76, Electron), Built-in Java Plugin, Local API (codedna serve, FastAPI, D-028), Per-test JaCoCo Coverage Mapping (D-015), Platform Website and Plugin Catalogue, Language Plugin Registry (codedna.languages, D-024), Target Product Architecture (D-017 - D-020), Apache Commons CSV Self-Collected Dataset (+1 more)

### Community 56 - "Selection Policies"
Cohesion: 0.23
Nodes (9): Transfer Measures and Decision Rules, B3 Recent-Failures-then-Shortest Rule, B9 / B9r / B9n Fallback Policies, Evaluation Conclusion, Hierarchical Percentile Bootstrap Intervals, RQ2: Time Saved at Detection Target, RQ4: Fallback and Risk-Based Stopping, Selection Policies B0-B10 (+1 more)

### Community 57 - "Cost-Matched & B10 Decisions"
Cohesion: 0.22
Nodes (5): Matplotlib (plots extra), Shared bounded LRU parse cache (4,000 blobs), B10 hybrid: rules order, calibrated stopping, B3 rules order (recent failures, then shortest), study11 FINDINGS.md

### Community 58 - "HistoryViewWidget"
Cohesion: 0.14
Nodes (5): HistoryViewWidget, Spinner(), ProjectHistory, RecordedHistory, SavedRun

### Community 59 - "Electron App Package"
Cohesion: 0.16
Nodes (14): description, devDependencies, electron@42.8.1, electron-builder@26.0.12, @theia/cli@1.76.0, @theia/cli, main, name (+6 more)

### Community 60 - "check"
Cohesion: 0.13
Nodes (14): check(), plan(), _plan_summary(), _run_verdict(), _verdict(), test_brake_plans_part_of_the_suite_on_validated_history(), test_check_needs_explicit_build_consent(), test_check_of_a_commit_is_recorded_as_history() (+6 more)

### Community 61 - "IDE & API Decisions"
Cohesion: 0.31
Nodes (4): Eclipse Theia, FastAPI, NetworkX, X-CodeDNA-Token per-session token

### Community 62 - "Baseline Policy Decisions"
Cohesion: 0.22
Nodes (9): B0 retest-all, B4 static dependency selection proxy, B6 change-features-only model, B7 trained ML model, B8 calibrated selector with time budget, B9 calibrated risk-aware fallback, B9n unfamiliar-change rule only, B9r risk-only fallback (+1 more)

### Community 63 - "CodeDNA — full handoff blueprint (2026-10-26)"
Cohesion: 0.04
Nodes (48): plugins(), 0.5 Where Claude stopped — resume here (kept current; last update 2026-10-26 09:40Z), 0. One-page summary, 10.1 What exists, 10.2 What is left, 10. The report, 11.1 Demo script (10 minutes), 11.2 Questions to rehearse (+40 more)

### Community 64 - "Electron App Config"
Cohesion: 0.12
Nodes (16): applicationName, defaultTheme, electron, preferences, reloadOnReconnect, windowOptions, config, editor.fontFamily (+8 more)

### Community 65 - "swebench_brake_study.py"
Cohesion: 0.14
Nodes (18): base_commit(), _download(), fetch(), _git(), log_base_url(), main(), _pair(), patch_paths() (+10 more)

### Community 66 - "TestRunResult"
Cohesion: 0.15
Nodes (22): resolve_repository(), import_run(), list_runs(), load_saved_run(), ProjectHistoryError, record_saved_runs(), run_detail(), _same_repository() (+14 more)

### Community 68 - "ReplayViewWidget"
Cohesion: 0.13
Nodes (13): plural(), COLOUR, CommitStrip(), duration(), LineChart(), pct(), ReplayViewWidget, Series (+5 more)

### Community 69 - "conftest.py"
Cohesion: 0.16
Nodes (4): GitRepo, isolated_git_config(), repo(), test_mine_limits_and_binary_files()

### Community 70 - "codedna_java/mapping.py"
Cohesion: 0.07
Nodes (24): _attach_line_ranges(), ChangedFile, ChangeReport, _to_range(), _add_declarations(), _add_outside(), _all_unresolved(), analyze_changes() (+16 more)

### Community 71 - "hashlib"
Cohesion: 0.08
Nodes (46): plugin_install(), plugin_remove(), _plugins(), CatalogueError, load_catalogue(), PluginVersion, validate_catalogue(), _version() (+38 more)

### Community 72 - "Plugin Catalogue Decisions"
Cohesion: 0.25
Nodes (4): HikariCP project, JavaParser symbol solver, Plugin catalogue (versioned JSON index), tree-sitter / tree-sitter-java

### Community 73 - "IDE & Local API Milestone"
Cohesion: 0.40
Nodes (5): CodeDNA Dark Theme (D-030, D-031), Local API FastAPI (D-019, D-028), Milestone 6: CodeDNA IDE and FYP Demo, codedna serve (Local API), CodeDNA IDE (Theia 1.76 + Electron)

### Community 74 - "cli.py"
Cohesion: 0.22
Nodes (12): _add_change_args(), _add_must_run_arg(), _add_non_java_arg(), build_parser(), _fraction(), _import_rtptorrent(), _non_negative_int(), _record_run() (+4 more)

### Community 76 - "RTPTorrent & SQLite Decisions"
Cohesion: 0.40
Nodes (3): Bare repository support (resolve_repository), Mattis et al., MSR 2020 (doi:10.1145/3379597.3387458), SQLite (sqlite3)

### Community 77 - "CodeGraph"
Cohesion: 0.17
Nodes (8): CodeGraph, Edge, Evidence, merge_graphs(), union_graphs(), UnresolvedReference, _add_structure(), file_role()

### Community 78 - "Validation & Demo Setup"
Cohesion: 0.40
Nodes (4): Portable JDK 17 + Maven 3.10 Runtime, Demo Repository (make_demo_repo.py), Real Maven/JUnit/JaCoCo Integration Test, Sample Java Project (OrderService, PriceCalculator)

### Community 79 - "Package Scripts"
Cohesion: 0.22
Nodes (9): scripts, build:core, bundle, download:plugins, package, rebuild, start, test:runtime (+1 more)

### Community 81 - "test_python_plugin.py"
Cohesion: 0.15
Nodes (19): discover_tests(), commit(), edges(), java_only_plugins(), mixed(), test_a_dot_pytest_ini_is_read_like_pytest_ini(), test_a_java_change_selects_only_java_tests(), test_a_python_change_selects_only_the_python_tests_that_depend_on_it() (+11 more)

### Community 82 - "Milestone 1 Analyze"
Cohesion: 0.67
Nodes (3): Milestone 1: Git and Java Change Analysis, tree-sitter Pinned <0.26 (D-033), codedna analyze

### Community 86 - "graph-view-widget.tsx"
Cohesion: 0.10
Nodes (15): CodeDnaWorkspace, GraphNode, LANE_COLUMN, LANE_ROW, lanePositions(), ORDER, CATEGORY, DEPTHS (+7 more)

### Community 90 - "run_rolling_evidence.py"
Cohesion: 0.09
Nodes (25): bootstrap(), _difference(), _interval(), match_budget(), metrics(), test_match_budget_finds_the_same_time(), evaluate(), choose() (+17 more)

### Community 91 - "Node"
Cohesion: 0.20
Nodes (15): Node, _compact(), Declaration, _end(), _error_lines(), _Extractor, _package_name(), _parameter_list() (+7 more)

### Community 94 - "CodeDnaService"
Cohesion: 0.11
Nodes (7): compareVersions(), errorText(), PluginsViewWidget, CataloguePlugin, CatalogueVersion, CodeDnaService, InstalledPlugins

### Community 95 - "codedna_python/parser.py"
Cohesion: 0.12
Nodes (17): test_declarations_have_prefixed_ids_and_decorators_belong_to_them(), test_module_names_come_from_paths(), test_relative_imports_resolve_against_the_package(), test_syntax_errors_are_reported_not_guessed(), _absolute(), _blocks(), ClassBase, _collect() (+9 more)

### Community 100 - "codedna"
Cohesion: 0.67
Nodes (3): codedna, codedna-java, codedna-python

### Community 102 - "codedna_python/mapping.py"
Cohesion: 0.15
Nodes (19): _add_declarations(), _add_outside(), _all_unresolved(), analyze_python_file(), attach_python_declarations(), _attribute(), DeclarationChange, _extent() (+11 more)

### Community 103 - "app.py"
Cohesion: 0.12
Nodes (19): AnalyzeRequest, ChangeRequest, CompareRequest, GraphRequest, ImpactRequest, ImportProjectRunRequest, PluginInstallRequest, PluginRemoveRequest (+11 more)

### Community 104 - "build.py"
Cohesion: 0.11
Nodes (11): list_files(), read_blobs(), _all(), BuildLayout, _child_text(), _gradle(), _gradle_test_roots(), _local() (+3 more)

### Community 105 - "test_policy.py"
Cohesion: 0.20
Nodes (12): change(), reasons(), test_a_change_cannot_loosen_or_tighten_its_own_policy(), test_api_select_accepts_must_run_patterns(), test_base_policy_pins_tests_the_strategy_would_skip(), test_compare_measures_baselines_without_the_policy(), test_installed_rules_add_pins_and_fail_safe(), test_patterns_match_and_unmatched_patterns_warn() (+4 more)

### Community 106 - "codedna_java/discovery.py"
Cohesion: 0.14
Nodes (14): _ancestors(), discover_tests_for_commit(), DiscoveredTest, DiscoveryReport, _extends_junit3(), _framework(), _junit3_candidate(), _junit3_provider() (+6 more)

### Community 107 - "create_app"
Cohesion: 0.09
Nodes (17): create_app(), analyze(), compare(), graph(), impact(), import_project_run_(), project_history_(), project_run_() (+9 more)

### Community 108 - "policy.py"
Cohesion: 0.17
Nodes (7): GitCommandError, apply_policy(), installed_rules(), PatternRule, PolicyContext, PolicyResult, read_policy()

### Community 109 - ".from_csv"
Cohesion: 0.08
Nodes (17): _history_features(), _TestState, bare(), load_script(), test_demo_refuses_untested_commits_and_existing_folders(), test_demo_workspace_holds_only_prior_history_and_the_real_outcome(), load(), test_explicit_project_selection_cannot_relabel_inspected_or_colliding_data() (+9 more)

### Community 111 - "electron-builder.yml"
Cohesion: 0.09
Nodes (21): appId, asar, directories, buildResources, output, electronDist, extraResources, from (+13 more)

### Community 112 - "codedna_python/discovery.py"
Cohesion: 0.18
Nodes (12): discover_tests(), discover_tests_for_commit(), DiscoveredTest, DiscoveryReport, _in_testpaths(), _ini(), _is_test_file(), _matches() (+4 more)

### Community 113 - "CodeDNA: system chapters (draft)"
Cohesion: 0.11
Nodes (19): 1.1 Problem, 1.2 Aim, 1.3 Objectives, 1.4 Contribution and its limits, 1.5 Report structure, 1. Introduction, 3.1 Functional requirements, 3.2 Non-functional requirements (+11 more)

### Community 114 - "test_live_risk.py"
Cohesion: 0.14
Nodes (18): risk_select(), recommend(), _unvalidated_all(), test_api_gate_and_execution_permission(), test_api_risk_select_passes_the_method(), test_audit_needs_failures_recall_and_an_upper_bound(), test_cli_risk_select(), test_conformal_stop_keeps_must_run_tests() (+10 more)

### Community 115 - "test_pts_check.py"
Cohesion: 0.20
Nodes (13): _count_cutoff(), Cutoffs, _score_cutoff(), select(), tune(), load(), row(), test_auc_counts_ties_as_half_and_needs_both_classes() (+5 more)

### Community 116 - "RiskPolicy"
Cohesion: 0.09
Nodes (30): choose(), choose(), fit_audited(), choose(), decide(), _decision(), _extend_to_risk_target(), RiskPolicy (+22 more)

### Community 117 - "importlib_util"
Cohesion: 0.26
Nodes (8): search(), load(), outcomes(), test_check_tunes_on_history_and_pairs_every_commit(), test_conditional_mode_checks_failing_audit_commits_only(), test_runner_refuses_changed_protocol(), test_search_falls_back_to_full_when_the_strictest_fails(), test_search_takes_the_largest_threshold_before_the_first_failure()

### Community 118 - "_CodeIndex"
Cohesion: 0.36
Nodes (3): TestCoverage, _CodeIndex, _to_ranges()

### Community 119 - "resolve_commit"
Cohesion: 0.38
Nodes (13): resolve_commit(), commit(), junit_class(), test_class_patterns_in_surefire_includes_select_test_classes(), test_gradle_multi_line_include_and_comments(), test_gradle_settings_modules_run_every_junit_class(), test_gradle_test_source_sets_moved_by_scripts(), test_maven_modules_are_followed_and_custom_includes_read() (+5 more)

### Community 120 - "dataclasses"
Cohesion: 0.16
Nodes (16): test_bounded_cache_gives_identical_graphs(), _add_structure(), build_graph(), build_graph_for_commit(), file_role(), _parse_missing(), _compact(), extract_references() (+8 more)

### Community 121 - "test_desktop_bundle.py"
Cohesion: 0.22
Nodes (10): load_builder(), test_bundle_includes_the_java_plugin_and_its_entry_point(), test_bundle_includes_the_python_plugin_and_its_entry_point(), test_failed_freezer_does_not_publish_a_manifest(), test_manifest_tracks_nested_files_and_changes(), test_missing_freezer_gives_install_command(), test_missing_java_plugin_gives_install_command(), test_missing_python_plugin_gives_install_command() (+2 more)

### Community 122 - "continue_confirmatory.py"
Cohesion: 0.33
Nodes (11): continue_once(), digest(), freeze(), freeze_sources(), main(), output_lock(), read_cache(), ready() (+3 more)

### Community 123 - "make_hikaricp_demo.py"
Cohesion: 0.30
Nodes (9): bare_repository(), candidates(), evaluate(), first_parents(), list_candidates(), main(), prior_history(), real_outcome() (+1 more)

### Community 124 - "sys"
Cohesion: 0.07
Nodes (25): _pip(), checkout(), run(), test_default_run_creates_the_demo_and_opens_it(), test_given_folder_is_opened_and_first_run_installs_and_builds(), test_installs_both_language_plugins_once_into_a_venv_without_them(), test_installs_the_java_plugin_once_into_an_older_venv(), test_launcher_reuses_portable_gradle_and_preserves_custom_cache() (+17 more)

### Community 126 - "workflow.test.cjs"
Cohesion: 0.15
Nodes (3): head, root, source

### Community 127 - "build-core.cjs"
Cohesion: 0.22
Nodes (4): localPython, result, root, resolveCoreExecutable()

### Community 128 - "runner.py"
Cohesion: 0.23
Nodes (8): _collect(), find_python(), _float(), _message(), PytestRunError, _run(), run_pytest(), _status()

### Community 129 - "test_replay.py"
Cohesion: 0.22
Nodes (12): compact(), load_script(), test_api_replay_endpoints(), test_api_returns_bad_request_for_invalid_outcomes(), test_cli_lists_and_replays(), test_compact_report_replays_the_same_totals_without_detail(), test_compact_summary_takes_unrecordable_means_from_the_report(), test_missing_policies_are_noted_not_invented() (+4 more)

### Community 130 - "Java workflow handoff"
Cohesion: 0.17
Nodes (11): Completed, Current review — 2026-10-25, Decision against original scope, Environment repaired, Java workflow handoff, Latest status — 2026-10-25, Original implementation batch — 2026-10-24, Remaining original scope (+3 more)

### Community 131 - "CodeDNA as a test brake for AI coding agents (report chapter draft)"
Cohesion: 0.17
Nodes (12): 1. Motivation, 2. Design, 3. Evaluation question, 4. Method, 5.1 Primary run (pre-registered), 5.2 Follow-up run with fixed discovery (post hoc), 5.3 Size of the plan (RQ-B2, follow-up run), 5. Results (+4 more)

### Community 132 - "codedna-theme.ts"
Cohesion: 0.20
Nodes (5): C, CODEDNA_THEME_ID, CodeDnaThemeContribution, COLORS, TOKEN_COLORS

### Community 134 - "test_brake_planning.py"
Cohesion: 0.15
Nodes (9): test_partial_broadening_labels_original_estimate_conservatively(), test_python_check_executes_pytest_and_reports_actual_verdict(), test_python_check_still_requires_consent(), test_python_fallback_keeps_policy_pins(), test_python_plan_has_explicit_full_suite_fallback(), test_structural_plan_uses_same_immutable_snapshot(), test_unsupported_language_does_not_accept_unknown_method(), test_unsupported_language_does_not_bypass_target_validation() (+1 more)

### Community 135 - "dataset"
Cohesion: 0.17
Nodes (13): historical_scores(), load(), test_check_tunes_on_history_and_pairs_every_commit(), test_conditional_mode_tunes_on_failing_audit_commits_only(), test_runner_refuses_changed_protocol(), test_saves_time_needs_the_target_on_three_quarters_of_projects(), test_threshold_needs_enough_commits_and_stops_at_first_violation(), test_threshold_uses_the_corrected_bound() (+5 more)

### Community 136 - "codedna_python/builder.py"
Cohesion: 0.28
Nodes (3): _Bindings, build_graph_for_commit(), parse_commit()

### Community 137 - "CodeDNA README"
Cohesion: 0.46
Nodes (3): Project Specification, CodeDNA IDE README, CodeDNA README

### Community 138 - "run_crc_check.py"
Cohesion: 0.12
Nodes (14): _outcomes(), failing_commit_threshold(), stopper(), threshold(), test_conformal_threshold_matches_the_offline_check(), 6.3 Implement B12f in the live brake — DONE as opt-in (D-068, 2026-10-26), digest(), evaluate() (+6 more)

### Community 140 - "test_confirmatory_continuation.py"
Cohesion: 0.40
Nodes (8): cache_for_fixture(), load(), test_corrupt_source_file_is_rejected_before_preparation(), test_end_to_end_reuses_cache_and_freezes_model_code(), test_freezing_provenance_preserves_an_existing_conflicting_record(), test_incomplete_cli_records_status_without_waiting_or_downloading(), test_output_lock_prevents_duplicate_workers_and_allows_restart(), test_partial_and_wrong_project_caches_are_not_ready()

### Community 142 - "type_kinds"
Cohesion: 0.10
Nodes (5): type_kinds(), _Api10Java, test_commands_that_need_java_name_the_plugin_to_install(), test_incompatible_and_broken_plugins_are_rejected(), 7. Known bugs and weaknesses (verified)

### Community 143 - "CodeDNA FYP Starter brief"
Cohesion: 0.22
Nodes (9): CodeDNA FYP Starter brief, CodeDNA (change-impact + regression test selection platform), Cytoscape.js, Ekstazi, Fine-Ekstazi, Predictive RTS, RTSTester, Tree-sitter Java (+1 more)

### Community 144 - "Agent brake study on public SWE-bench Java patches — protocol"
Cohesion: 0.22
Nodes (9): Agent brake study on public SWE-bench Java patches — protocol, Arms, Changes after fixing the protocol, Data, Exclusions, Known limits (stated in advance), Outcomes, Question (+1 more)

### Community 145 - "Nine-project confirmatory results — 2026-10-26"
Cohesion: 0.18
Nodes (9): Design and scope, Gate evidence, Limitations and claim boundaries, Nine-project confirmatory results — 2026-10-26, Per-project observations, Pooled result, Provenance check (2026-10-26), Reproducibility (+1 more)

### Community 146 - "devDependencies"
Cohesion: 0.22
Nodes (9): devDependencies, rimraf@^5.0.0, @types/cytoscape@3.21.9, @types/react@^19.3.0, typescript@~5.4.5, rimraf, @types/cytoscape, @types/react (+1 more)

### Community 147 - "CombinedDiscovery"
Cohesion: 0.22
Nodes (3): CombinedDiscovery, commit_tests(), discover()

### Community 148 - "run_tests"
Cohesion: 0.19
Nodes (6): run_tests(), TestRunError, FakeJava, test_a_failing_python_test_is_reported(), test_a_mixed_run_splits_tests_by_language_and_joins_results(), test_running_needs_allow_build()

### Community 149 - "test_rolling_evidence.py"
Cohesion: 0.39
Nodes (5): load(), test_block_labels_never_reach_fitting(), test_blocks_cover_only_the_later_half_in_order(), test_runner_sets_eligibility_and_resume_fingerprints(), test_verdict_rules_are_the_fixed_ones()

### Community 150 - "_Resolver"
Cohesion: 0.33
Nodes (3): _FileContext, _Resolution, _Resolver

### Community 151 - "4. Design"
Cohesion: 0.25
Nodes (8): 4.1 Pipeline, 4.2 Platform structure (D-017, D-018), 4.3 Graph model and confidence labels (D-010), 4.4 Learning and risk design, 4.5 Must-run policy (D-050), 4.6 Building history while in use (D-053), 4.7 Security of the local tool, 4. Design

### Community 152 - "test_agent_brake.py"
Cohesion: 0.32
Nodes (9): BrakeServer, main(), rpc(), test_check_is_offered_only_with_build_consent_for_one_repository(), test_initialize_negotiates_the_protocol_version(), test_mcp_plan_accepts_the_conformal_method(), test_stdio_loop_answers_requests_and_parse_errors(), test_tool_calls_validate_arguments_and_repository() (+1 more)

### Community 153 - "test_demo_agent_brake.py"
Cohesion: 0.33
Nodes (3): load(), test_demo_plans_tests_for_the_agents_edit_without_building(), test_end_to_end_demo_blocks_the_breaking_edit_and_passes_the_harmless_one()

### Community 154 - "Conformal risk control stopping protocol — 2026-10-26"
Cohesion: 0.29
Nodes (6): Analyses, B12, Conformal risk control stopping protocol — 2026-10-26, Data and design, Outputs, Question

### Community 155 - "Predictive Test Selection baseline protocol — 2026-10-25"
Cohesion: 0.29
Nodes (6): Analyses, B11: PTS-style selection, Data and design, Outputs, Predictive Test Selection baseline protocol — 2026-10-25, Question

### Community 156 - "CodeDNA compared with closely related work (updated 2026-10-25)"
Cohesion: 0.29
Nodes (7): Agents, CodeDNA compared with closely related work (updated 2026-10-25), Comparison on the five properties that matter, Conformal risk control (D-063), Sources, The claim being checked, Where the claim is weakest

### Community 157 - "Cross-Project Transfer Test (D-039)"
Cohesion: 0.29
Nodes (6): Prior Art to Study, Cross-Project Transfer Test (D-039), RTPTorrent v1.1 Four-Project Subset, codedna history import-rtptorrent, Reproduce Cross-Project Transfer Check, RTPTorrent Dataset (Mattis et al., MSR 2020)

### Community 158 - "Tuned-threshold gate protocol — 2026-10-26"
Cohesion: 0.29
Nodes (6): Analyses, B13: tuned-threshold gate, Outputs, Pre-registered reruns on the confirmatory nine, Tuned-threshold gate protocol — 2026-10-26, Why the gate rejects (diagnosis from the saved confirmatory numbers)

### Community 159 - "CodeDNA Roadmap"
Cohesion: 0.40
Nodes (6): CodeDNA Platform (D-017), AGENTS.md Contributor Rules, Product Track (IDE, Plugins, Website), Research Track (Milestones 0-5), CodeDNA Roadmap, MEMORY.md Handoff Notes

### Community 160 - "test_worktree_snapshot.py"
Cohesion: 0.27
Nodes (4): InvalidCommitError, InvalidRepositoryError, test_edits_inside_a_submodule_are_refused_not_lost(), test_filter_drivers_are_refused_rather_than_run()

### Community 161 - "test_language_plugins.py"
Cohesion: 0.13
Nodes (8): PluginMissingError, api10_java(), no_plugins(), test_an_api_1_0_plugin_is_loaded_and_says_changes_stay_at_file_level(), test_changes_are_listed_and_java_files_reported_as_not_analysed(), test_load_problems_are_part_of_the_message(), test_the_core_never_imports_the_java_plugin(), test_the_installed_java_plugin_maps_the_same_change()

### Community 162 - "Confirmatory data preparation — 2026-10-25"
Cohesion: 0.33
Nodes (5): Confirmatory data preparation — 2026-10-25, Equivalent runtime inputs, cheaper extraction, Fixed project set, Reproduce, Reuse the existing producer

### Community 163 - "Failure-conditional conformal stopping protocol — 2026-10-26"
Cohesion: 0.33
Nodes (5): Analyses, Failure-conditional conformal stopping protocol — 2026-10-26, Method (B12f), Outputs, Question

### Community 165 - "Failure-conditional tuned gate protocol (B13f) — 2026-10-26"
Cohesion: 0.33
Nodes (5): Analyses, Failure-conditional tuned gate protocol (B13f) — 2026-10-26, Method (B13f), Outputs, Question

### Community 166 - "scripts"
Cohesion: 0.33
Nodes (6): scripts, build, clean, prepare, test, watch

### Community 167 - "Recovered Claude work and next priorities — 2026-10-24"
Cohesion: 0.40
Nodes (4): Next order of work, Reconciliation needed, Recovered Claude work and next priorities — 2026-10-24, What uncertainty means

### Community 168 - "Fixed DANTE-H / B10 extension protocol — 2026-10-24"
Cohesion: 0.40
Nodes (5): Fixed DANTE-H / B10 extension protocol — 2026-10-24, Fixed experiment, Independent baseline and attribution, Operational gate (separate from this retrospective experiment), Revised adapter, frozen before its own results

### Community 169 - "project"
Cohesion: 0.22
Nodes (7): junit_class(), project(), outcomes(), test_brake_check_on_validated_history_gives_a_verdict(), test_build_errors_and_all_skipped_runs_are_incomplete(), test_check_verdicts(), validated()

### Community 170 - "5. Implementation"
Cohesion: 0.40
Nodes (5): 5.1 Technology choices, 5.2 Core modules, 5.3 CodeDNA IDE, 5.4 Real-project demonstration (D-052), 5. Implementation

### Community 171 - "prediction_rows"
Cohesion: 0.33
Nodes (5): _is_file_of(), _is_test_path(), test_prediction_uses_prior_outcomes_and_costs_only(), 9. Improvements (engineering), prediction_rows()

### Community 172 - "theiaPlugins"
Cohesion: 0.67
Nodes (3): theiaPlugins, redhat.java, vscode.java

### Community 182 - "Test brake for AI coding agents — setup guide"
Cohesion: 0.25
Nodes (6): Connect an agent, Limits, Structural feedback and language support, Tell the agent to use it, Test brake for AI coding agents — setup guide, Tools

### Community 183 - "2. Background and related work"
Cohesion: 0.25
Nodes (8): 2.1 Regression test selection and prioritisation, 2.2 History-based and learned approaches in CI, 2.3 Predictive test selection with a target, 2.4 Recent research closest to CodeDNA, 2.5 Calibration and uncertainty, 2.6 Test selection for AI coding agents, 2.7 Position, 2. Background and related work

### Community 184 - "test_swebench_brake_study.py"
Cohesion: 0.48
Nodes (5): junit(), load(), test_benchmark_test_names_map_to_classes_or_stay_unmapped(), test_parsers_read_harness_files(), test_run_builds_harness_states_and_scores_the_plan()

### Community 189 - "summarise"
Cohesion: 0.67
Nodes (3): summarise(), block(), wilson()

## Ambiguous Edges - Review These
- `Candidate Contribution: Hybrid Calibrated Selector with Fallback` → `Thesis Claim: Calibrated Stopping Rule on Simple Ordering`  [AMBIGUOUS]
  docs/RESEARCH_PLAN.md · relation: conceptually_related_to
- `Shared bounded LRU parse cache (4,000 blobs)` → `D-011 Plain dictionaries, not NetworkX, for the graph`  [AMBIGUOUS]
  docs/DECISIONS.md · relation: conceptually_related_to
- `D-008 Tree-sitter Java for syntax-level declaration extraction` → `D-020 Platform website and plugin distribution`  [AMBIGUOUS]
  docs/DECISIONS.md · relation: conceptually_related_to

## Knowledge Gaps
- **71 isolated node(s):** `example:sample-java-project`, `codedna-java`, `codedna-python`, `Cytoscape.js`, `Tree-sitter Java` (+66 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1034 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **36 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Study11 (11 projects x 5 seeds)` connect `Project Rules & Plans` to `Study Runner`, `json`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `create_app()` (e.g. with `require_token()` and `ReplayError`) actually correct?**
  _`create_app()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `example:sample-java-project`, `codedna-java`, `codedna-python` to the rest of the system?**
  _71 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `languages.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._
- **Why does `CodeDNA README` connect `CodeDNA README` to `Project Rules & Plans`, `Test brake for AI coding agents — setup guide`, `CodeDNA Roadmap`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Candidate Contribution: Hybrid Calibrated Selector with Fallback` and `Thesis Claim: Calibrated Stopping Rule on Simple Ordering`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Shared bounded LRU parse cache (4,000 blobs)` and `D-011 Plain dictionaries, not NetworkX, for the graph`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._