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
    status(): Promise<CodeDnaStatus>;
    analyze(repo: string, base: string, head: string): Promise<AnalyzeReport>;
    impact(repo: string, base: string, head: string): Promise<ImpactReport>;
    select(repo: string, base: string, head: string, strategy: SelectionStrategy, historyCsv?: string): Promise<SelectionReport>;
    runSelection(repo: string, base: string, head: string, strategy: SelectionStrategy, historyCsv?: string): Promise<SelectionRun>;
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
    }[];
    edges: { id: string; source: string; target: string; kind: string;
        confidence: 'confirmed' | 'heuristic'; evidence: string }[];
}

// --- select --------------------------------------------------------------------

export interface SelectionRun {
    selection: SelectionReport;
    results: { tests: { id: string; status: string; time: number }[];
        failing_tests: string[]; warnings: string[]; duration_seconds: number; exit_codes: number[] };
    output_dir: string;
}

export interface SelectionReport {
    repository: string;
    base_commit: string;
    head_commit: string;
    risk?: {
        status: 'unvalidated' | 'validated_history'; target: number;
        estimated_skip_risk: number | null; proposed_skip_risk: number | null;
        reasons: string[]; note: string;
        validation: { commits: number; failing_commits: number; miss_upper_bound: number;
            failure_recall: number | null; accepted: boolean } | null;
    };
    strategy: string;
    total_tests: number;
    selected: { test: string; reasons: string[] }[];
    skipped: string[];
    selection_ratio: number;
    estimated_time: { selected_seconds: number; all_seconds: number; saved_ratio: number } | null;
    warnings: string[];
}
