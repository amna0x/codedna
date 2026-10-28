import * as React from '@theia/core/shared/react';
import { AnalysisTimingRecord } from '../common/codedna-protocol';
import { COUNTER_LABELS, safeAnalysisTimings, STAGE_LABELS } from './analysis-metrics';

/** Core measurements, displayed separately from execution results or risk. */
export function AnalysisTimingDetails({ reports, title = 'Analysis timing' }: {
    reports: AnalysisTimingRecord[]; title?: string
}): React.ReactNode {
    const records = safeAnalysisTimings(reports);
    if (!records.length) { return null; }
    return <details className='cd-notice'>
        <summary>{title}</summary>
        <p>Stage times overlap and should not be added together. These are analysis timings, separate from project test execution.</p>
        {records.map(({ id, operation, metrics }) => <section key={id}>
            <h4>{operation === 'impact' ? 'Impact analysis' : operation === 'analyze' ? 'Change analysis' : 'Test recommendation'}</h4>
            <p>Core analysis: {metrics.total_seconds.toFixed(3)} s
                {metrics.worker_startup_seconds !== undefined && <> · Worker startup: {metrics.worker_startup_seconds.toFixed(3)} s</>}</p>
            <ul>{Object.entries(metrics.stages).map(([name, value]) =>
                <li key={name}>{STAGE_LABELS[name]}: {value.seconds.toFixed(3)} s ({value.calls} calls)</li>)}</ul>
            {!!Object.keys(metrics.counters).length && <ul>{Object.entries(metrics.counters).map(([name, value]) =>
                <li key={name}>{COUNTER_LABELS[name]}: {value}</li>)}</ul>}
        </section>)}
    </details>;
}
