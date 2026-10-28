import { AnalysisTimingRecord, AnalysisTimings } from '../common/codedna-protocol';

export const STAGE_LABELS: Record<string, string> = {
    git: 'Reading Git', 'parse.java': 'Parsing Java', 'parse.python': 'Parsing Python',
    graph: 'Building dependency graphs', test_discovery: 'Discovering tests',
    test_selection: 'Selecting tests', 'risk.recommendation': 'Risk recommendation',
    'risk.history_load': 'Reading history', 'risk.fit_and_audit': 'Model and audit work',
    'risk.model_setup': 'Preparing the model', 'risk.training': 'Training the model',
    'risk.calibration': 'Calibrating probabilities', 'risk.audit_prediction': 'Predicting audit outcomes',
    'risk.audit': 'Checking the historical audit', 'fit_cache.fingerprint': 'Checking model inputs',
    'fit_cache.copy': 'Copying reusable fitted models'
};
export const COUNTER_LABELS: Record<string, string> = {
    'fit_cache.hit': 'Reused fitted models', 'fit_cache.miss': 'Fresh model fits',
    'fit_cache.disabled': 'Fits outside a reuse scope', 'fit_cache.copy_failed': 'Reuse unavailable',
    'fit_cache.evicted': 'Old model entries removed', 'parse_cache.get': 'Cached parse reads',
    'parse_cache.store': 'Parsed entries stored', 'parse_cache.evicted': 'Old parses removed',
    'fallback.all_tests_required': 'Full suite: every test is mandatory',
    'fallback.history_missing': 'Full suite: no project history',
    'fallback.prior_audit_failed': 'Full suite: earlier audit failed',
    'fallback.conformal_full_suite': 'Full suite: conformal evidence insufficient',
    'fallback.unsupported_change': 'Full suite: unsupported change',
    'fallback.evidence_unusable': 'Full suite: evidence could not be used'
};
const number = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value) && value >= 0;

/** Optional diagnostic data only: no paths, source, environment or unknown fields. */
export function safeAnalysisTimings(records: AnalysisTimingRecord[]): AnalysisTimingRecord[] {
    const result: AnalysisTimingRecord[] = [];
    for (const record of records.slice(0, 4)) {
        if (!record || !/^[a-zA-Z0-9_-]{1,64}$/.test(record.id)
            || !['tests', 'analyze', 'impact', 'select', 'risk-select'].includes(record.operation)) { continue; }
        const input = record.metrics;
        if (!input || input.schema_version !== 1 || !number(input.total_seconds)) { continue; }
        const metrics: AnalysisTimings = { schema_version: 1, total_seconds: input.total_seconds, stages: {}, counters: {} };
        if (number(input.worker_startup_seconds)) { metrics.worker_startup_seconds = input.worker_startup_seconds; }
        for (const [name, value] of Object.entries(input.stages ?? {})) {
            if (Object.hasOwn(STAGE_LABELS, name) && value && number(value.calls) && Number.isInteger(value.calls)
                && number(value.seconds) && number(value.self_seconds)) {
                metrics.stages[name] = { calls: value.calls, seconds: value.seconds, self_seconds: value.self_seconds };
            }
        }
        for (const [name, value] of Object.entries(input.counters ?? {})) {
            if (Object.hasOwn(COUNTER_LABELS, name) && number(value) && Number.isInteger(value)) { metrics.counters[name] = value; }
        }
        result.push({ id: record.id, operation: record.operation, metrics });
    }
    return result;
}
