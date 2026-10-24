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
    select(repo: string, base: string, head: string, strategy: SelectionStrategy): Promise<SelectionReport>;
    /** Calibrated stopping behind the target-validation gate (D-041). */
    risk(repo: string, base: string, head: string): Promise<RiskReport>;
}

export type SelectionStrategy = 'dependency' | 'all';

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
}

// --- select --------------------------------------------------------------------

export interface SelectionReport {
    strategy: string;
    total_tests: number;
    selected: { test: string; reasons: string[] }[];
    skipped: string[];
    selection_ratio: number;
    estimated_time: { selected_seconds: number; all_seconds: number; saved_ratio: number } | null;
    warnings: string[];
}

// --- risk (D-041) --------------------------------------------------------------

export interface RiskGateReport {
    status: 'validated' | 'unvalidated';
    reasons: string[];
    evidence: {
        history_commits: number;
        failing_commits: { train: number; calibration: number; validation: number };
        validation?: {
            observed_miss_rate: number;
            observed_miss_rate_95ci: [number, number];
            mean_estimated_skip_risk: number;
            mean_time_ratio: number;
        };
    };
    config: { risk_target: number; max_commits_since_full_run: number };
    validated_through: string | null;
}

export interface RiskReport {
    head: string;
    gate: RiskGateReport;
    commits_since_full_run: number | null;
    decision: {
        mode: 'full_suite' | 'calibrated_stop';
        selected: string[];
        skipped: string[];
        estimated_skip_risk: number | null;
        estimated_time_fraction: number;
        reasons: string[];
    };
    tests: { test: string; probability: number | null; selected: boolean; estimated_seconds: number }[];
    note: string;
}
