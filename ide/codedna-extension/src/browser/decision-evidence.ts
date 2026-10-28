import { AnalysisTimingRecord, SelectionReport, SelectionRun } from '../common/codedna-protocol';
import { safeAnalysisTimings } from './analysis-metrics';

/** Presentation guidance only. The core remains the sole authority on risk. */
export function recoverySteps(report: SelectionReport): string[] {
    if (!report.risk) {
        return ['This selection uses structural rules and has no validated skip-risk estimate. Choose Validated risk stopping to request a prior-audited estimate; it may still require the full suite.'];
    }
    const reasons = report.risk.reasons.join(' ');
    if (/All discovered tests are required by the must-run policy/.test(reasons)) {
        return ['All tests are already mandatory. Run the full suite; this recommendation does not need a fitted risk model.'];
    }
    const unsupported = /unsupported|non-Java|mixed|language/i.test(reasons);
    const steps: string[] = [];
    if (/another repository|branch|future|chronological|target outcome/i.test(reasons)) {
        steps.push('Use history from this repository and branch ending at the comparison base. Keep target-change outcomes out of its prediction.');
    }
    if (/stale|next first-parent/i.test(reasons)) {
        steps.push('Compare the next first-parent change and use complete history through its base commit.');
    }
    if (unsupported) {
        steps.push('Risk stopping is supported only in its validated language domain. Use the full suite for this change.');
    }
    if (/invalid|duplicate|empty/i.test(reasons)) {
        steps.push('Inspect the history import and its warnings. Do not edit outcomes merely to make validation pass.');
    }
    if (report.risk.status !== 'validated_history' && unsupported) {
        steps.push('More history alone cannot make an unsupported change eligible for risk stopping.');
    } else if (report.risk.status !== 'validated_history') {
        steps.push('Record complete full-suite runs over subsequent changes. Passing runs alone do not establish failure-detection safety; the prior audit must pass.');
    } else {
        steps.push('Continue recording full-suite audits. This decision describes this comparison; it does not validate later changes automatically.');
    }
    return steps;
}

/** Allowlisted evidence: no source text, environment variables, credentials or raw logs. */
export function decisionRecord(report: SelectionReport, execution?: SelectionRun, createdAt = new Date().toISOString(), timings: AnalysisTimingRecord[] = []): object {
    return {
        schema_version: 1, kind: 'codedna-decision-evidence', created_at: createdAt,
        ...(timings.length ? { analysis_timings: safeAnalysisTimings(timings) } : {}),
        disclosure: 'Contains local repository paths, test names and core diagnostic messages. Review before sharing.',
        comparison: { repository: report.repository, base: report.base_commit, head: report.head_commit },
        selection: { strategy: report.strategy, total_tests: report.total_tests,
            selected: report.selected.map(item => ({ test: item.test, file: item.file ?? null, reasons: item.reasons })),
            skipped: report.skipped, estimated_time: report.estimated_time },
        risk: report.risk ?? null, warnings: report.warnings,
        execution: execution ? { tests: execution.results.tests.map(test => ({
            id: test.id, status: test.status, time: test.time,
            cases: test.cases?.map(item => ({ name: item.name, status: item.status, time: item.time }))
        })), failing_tests: execution.results.failing_tests, exit_codes: execution.results.exit_codes,
        duration_seconds: execution.results.duration_seconds, recording: execution.recording ?? null } : null
    };
}
