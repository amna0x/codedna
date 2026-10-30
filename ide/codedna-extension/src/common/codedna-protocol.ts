/**
 * Contract between the CodeDNA views (frontend) and the CodeDNA backend
 * service. The backend starts `codedna serve` and forwards calls to the local
 * API; the session token never reaches the renderer.
 *
 * Types describe only the fields the views use; the JSON is produced by the
 * Python core (docs/PROJECT_SPEC.md).
 */

export const CODEDNA_SERVICE_PATH = '/services/codedna';
export const CodeDnaService = Symbol('CodeDnaService');

export interface CodeDnaStatus {
    running: boolean;
    version?: string;
    executable: string;
    error?: string;
}

export interface CodeDnaService {
    snapshotFile(repository: string, revision: string, path: string): Promise<string>;
    status(): Promise<CodeDnaStatus>;
    /** Capability-gated: older packaged cores keep the synchronous path. */
    analysisJobs(): Promise<boolean>;
    startAnalysis(operation: AnalysisOperation, payload: object): Promise<AnalysisJob>;
    analysisJob(id: string): Promise<AnalysisJob>;
    cancelAnalysis(id: string): Promise<AnalysisJob>;
    tests(repo: string, revision: string): Promise<TestDiscovery>;
    projectHistory(repo: string): Promise<ProjectHistory>;
    recordSavedRuns(repo: string): Promise<RecordedHistory>;
    importRun(repo: string, source: string): Promise<{ id: string; tests: number; failures: number }>;
    savedRun(repo: string, runId: string): Promise<SavedRun>;
    analyze(repo: string, base: string, head: string): Promise<AnalyzeReport>;
    impact(repo: string, base: string, head: string, options?: ImpactOptions): Promise<ImpactReport>;
    select(repo: string, base: string, head: string, strategy: SelectionStrategy, historyCsv?: string): Promise<SelectionReport>;
    runSelection(repo: string, base: string, head: string, strategy: SelectionStrategy, historyCsv?: string): Promise<SelectionRun>;
    /** Folders to look for experiment reports in (CODEDNA_REPLAY_FOLDERS), may be empty. */
    replayFolders(): Promise<string[]>;
    replaySources(folders: string[]): Promise<ReplaySources>;
    replayOverview(folders: string[], seed?: number): Promise<ReplayOverview>;
    replay(path: string): Promise<ReplayTimeline>;
    /** Language plugins CodeDNA's engine found (D-018, D-054). */
    installedPlugins(): Promise<InstalledPlugins>;
    /** The official catalogue (fixed URL in the core) plus what is installed. */
    pluginCatalogue(): Promise<PluginCatalogueView>;
    /** Only after the view's explicit confirmation: installing runs the plugin's code. */
    installPlugin(plugin: string, version: string): Promise<PluginChange>;
    removePlugin(plugin: string): Promise<PluginChange>;
}

/** File locations returned by the core's existing test-discovery endpoint. */
export interface TestDiscovery {
    repository: string;
    commit: string;
    tests: { id: string; file: string; methods?: string[]; framework?: string; language?: string }[];
}

export type SelectionStrategy = 'dependency' | 'all' | 'risk';

// --- analyze -----------------------------------------------------------------

export interface DeclarationChange {
    id: string;
    kind: string;
    change: 'added' | 'deleted' | 'modified';
    code_changed: boolean | null;
    parent: string | null;
    head_lines: [number, number] | null;
    base_lines: [number, number] | null;
}

export interface JavaFileAnalysis {
    package: string | null;
    declarations: DeclarationChange[];
    outside_declarations: { side: string; lines: number[][]; parts: string[]; code_changed: boolean | null }[];
    unresolved: { side: string; lines: number[][]; reason: string }[];
}

export interface ChangedFile {
    path: string;
    status: string;
    old_path: string | null;
    is_java: boolean;
    is_binary: boolean;
    changed_lines: number[][];
    java: JavaFileAnalysis | null;
    /** Installed plugin that handles the file ("java", "python"), null if none does. */
    language?: string | null;
    /** Declaration mapping from a plugin other than Java; same shape. */
    analysis?: JavaFileAnalysis | null;
}

export interface AnalyzeReport {
    repository: string;
    base_commit: string;
    head_commit: string;
    changed_files: ChangedFile[];
    warnings: string[];
}

// --- impact --------------------------------------------------------------------

export interface PathStep {
    dependent: string;
    depends_on: string;
    kind: string;
    confidence: 'confirmed' | 'heuristic';
    evidence: string;
}

export interface ImpactedNode {
    node: string;
    kind: string;
    file: string | null;
    role: string | null;
    distance: number;
    confidence: 'confirmed' | 'heuristic';
    seed: string;
    path: PathStep[];
}

export interface ImpactReport {
    seeds: { node: string; file: string | null; reasons: string[] }[];
    impacted: ImpactedNode[];
    unanalysed_changes: { path: string; reason: string }[];
    warnings: string[];
    explanation_graph: ExplanationGraph;
}

/** Limits passed to the core's traversal (`max_depth`, `confirmed_only`). */
export interface ImpactOptions {
    /** Links followed from a changed part; undefined = no limit. */
    maxDepth?: number;
    /** Follow only confirmed links. */
    confirmedOnly?: boolean;
}

/** Built by the core (impact_analysis.explanation_graph); the IDE only draws it. */
export interface ExplanationGraph {
    nodes: {
        id: string;
        category: 'changed' | 'impacted' | 'test' | 'unanalysed';
        changed: boolean;
        file: string | null;
        confidence: 'confirmed' | 'heuristic' | 'unresolved';
        distance: number | null;
        seed?: string;
        reasons: string[];
        path_edges: string[];
        /** Java package ('' = default package); null for files outside the graph. */
        package: string | null;
    }[];
    edges: { id: string; source: string; target: string; kind: string;
        confidence: 'confirmed' | 'heuristic'; evidence: string }[];
    packages: { id: string; name: string; label: string; changed: boolean;
        counts: { changed: number; impacted: number; test: number } }[];
    summary: { changed: number; impacted: number; test: number; unanalysed: number };
}

// --- select --------------------------------------------------------------------

export interface SelectionRun {
    selection: SelectionReport;
    results: { tests: { id: string; status: string; time: number;
        cases?: { name: string; status: string; time: number; message: string | null }[] }[];
        failing_tests: string[]; warnings: string[]; duration_seconds: number; exit_codes: number[] };
    output_dir: string;
    /** Whole-suite runs are kept as project history for risk selection (D-053). */
    recording?: { recorded: boolean; reason: string | null; commits_with_results?: number };
}

export interface SelectionReport {
    policy?: { pinned: string[]; source: string | null } | null;
    repository: string;
    base_commit: string;
    head_commit: string;
    risk?: {
        status: 'unvalidated' | 'validated_history'; target: number;
        estimated_skip_risk: number | null; proposed_skip_risk: number | null;
        reasons: string[]; note: string;
        method?: string; analysis_seconds?: number;
        provenance?: { history_sha256?: string; [key: string]: unknown };
        conformal?: { note?: string; corrected_bound?: number | null; failing_audit_commits?: number;
            alpha?: number; threshold?: number | null; [key: string]: unknown };
        validation: { commits: number; failing_commits: number; miss_upper_bound: number;
            failure_recall: number | null; accepted: boolean } | null;
    };
    strategy: string;
    total_tests: number;
    selected: { test: string; reasons: string[]; file?: string | null }[];
    skipped: string[];
    selection_ratio: number;
    estimated_time: { selected_seconds: number; all_seconds: number; saved_ratio: number } | null;
    warnings: string[];
}

// --- history replay (codedna.models.replay, D-049) --------------------------------

export interface ReplayPolicy { key: string; label: string; description: string }

export interface ReplaySource {
    project: string;
    seed: number | null;
    path: string;
    kind: 'trace' | 'per_commit';
    commits: number;
}

export interface ReplaySources { folders: string[]; missing: string[]; sources: ReplaySource[] }

export interface ReplayOutcome {
    time_ratio: number;
    missed: number;
    missed_tests: string[] | null;
    selected: number | null;
    seconds: number | null;
    estimated_risk: number | null;
    fallback: boolean | null;
}

export interface ReplayCommit {
    index: number;
    sha: string | null;
    tests: number | null;
    suite_seconds: number | null;
    failing: number;
    failing_tests: string[] | null;
    outcomes: Record<string, ReplayOutcome>;
}

/** Running values after each commit, index-aligned with `commits`. */
export interface ReplayCumulative {
    mean_time_ratio: number[];
    failures: number[];
    failures_missed: number[];
    failures_caught: number[];
    commits_with_miss: number[];
    observed_miss_rate: number[];
    seconds_run: (number | null)[];
    seconds_saved: (number | null)[];
    mean_estimated_risk: (number | null)[];
}

export interface ReplaySummary {
    commits: number;
    commits_with_failures: number;
    failures: number;
    missed_failures: number;
    failing_test_recall: number | null;
    commit_safety_rate: number | null;
    mean_time_ratio: number | null;
    observed_miss_rate: number | null;
    mean_estimated_skip_risk: number | null;
    fallback_rate: number | null;
    seconds_run: number | null;
    suite_seconds: number | null;
    from_report: string[];
}

export interface ReplayEvent {
    index: number;
    kind: 'caught' | 'missed' | 'fallback';
    sha: string | null;
    failing: number;
    missed: number;
    missed_tests: string[] | null;
    time_ratio: number;
    estimated_risk: number | null;
}

export interface ReplayTimeline {
    project: string | null;
    source: { kind: 'trace' | 'per_commit'; path: string | null; seed: number | null;
        model: string | null; calibration: string | null; dataset_sha256: string | null;
        splits: Record<string, number> | null };
    risk_target: number | null;
    rules_budget_at_same_time: number | null;
    policies: ReplayPolicy[];
    commits: ReplayCommit[];
    cumulative: Record<string, ReplayCumulative>;
    summary: Record<string, ReplaySummary>;
    events: ReplayEvent[];
    checks: { policy: string; metric: string; replay: number; report: number; match: boolean }[];
    notes: string[];
}

export type ReplayMetric = 'mean_time_ratio' | 'observed_miss_rate' | 'mean_estimated_skip_risk'
    | 'failing_test_recall' | 'commit_safety_rate' | 'missed_failures';

export interface ReplayOverview {
    seed: number | null;
    policies: ReplayPolicy[];
    projects: {
        project: string;
        seeds: number[];
        kinds: ('trace' | 'per_commit')[];
        commits: number;
        commits_with_failures: number;
        risk_target: number | null;
        within_risk_target: boolean | null;
        policies: Record<string, Record<ReplayMetric, number | null>>;
        mismatches: number;
    }[];
    overall: Record<string, Record<ReplayMetric, { mean: number | null; projects: number }>>;
    within_risk_target: { projects: number; of: number };
    note: string;
}


// --- project history: recorded executions, not saved research simulations ------
export interface ProjectRun {
    id: string;
    commit: string | null;
    tests: number;
    failures: number;
    duration_seconds: number;
    recorded_at: string;
    result_path: string;
    /** True when the run meets the D-053 recording rules. */
    candidate: boolean;
    reason: string | null;
}
export interface ProjectHistory {
    repository: string;
    runs: ProjectRun[];
    candidate_runs: number;
    candidate_commits: number;
    history_csv: string | null;
    warnings: string[];
    note: string;
}
export interface RecordedHistory {
    repository: string;
    recorded_runs: number;
    commits_with_results: number | null;
    history_csv: string;
    skipped: { id: string; reason: string }[];
    warnings: string[];
    note: string;
}
export interface SavedRun {
    id: string;
    results: SelectionRun['results'];
    logs: string[];
    result_path: string;
}

// --- language plugins and the catalogue (codedna.plugins, D-020, D-048, D-054) -------

export interface InstalledPlugin {
    name: string;
    display_name: string;
    version: string;
    api_version: string;
    file_suffixes: string[];
}

export interface InstalledPlugins { api_version: string; plugins: InstalledPlugin[]; problems: string[] }

export interface CatalogueVersion {
    version: string;
    api_version: string;
    /** Bundled with CodeDNA (installed from the repository), no download. */
    builtin: boolean;
    url: string | null;
    sha256: string | null;
    /** Whether this CodeDNA core can load it (decided by the core). */
    compatible?: boolean;
}

export interface CataloguePlugin {
    id: string;
    package?: string;
    name: string;
    description: string;
    licence: string;
    source: string;
    versions: CatalogueVersion[];
}

export interface PluginCatalogueView {
    catalogue: { schema_version: number; plugins: CataloguePlugin[] };
    installed: InstalledPlugins;
}

export interface PluginChange {
    plugin: string;
    version?: string;
    sha256?: string;
    status: string;
    /** Set after an update or removal: the old plugin code stays loaded until the server restarts. */
    restart_required?: boolean;
    previous_version?: string;
    installed: InstalledPlugins;
}

/** Read-only core jobs. Builds, plugins and history writes are excluded. */
export type AnalysisOperation = 'tests' | 'analyze' | 'impact' | 'select' | 'risk-select';
export interface AnalysisJob {
    id: string;
    operation: AnalysisOperation;
    state: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
    stage: string;
    elapsed_seconds: number;
    metrics?: AnalysisTimings;
    result?: object;
    error?: string;
}

export interface AnalysisTimings {
    schema_version: 1;
    total_seconds: number;
    worker_startup_seconds?: number;
    stages: Record<string, { calls: number; seconds: number; self_seconds: number }>;
    counters: Record<string, number>;
}
export interface AnalysisTimingRecord {
    id: string;
    operation: AnalysisOperation;
    metrics: AnalysisTimings;
}
