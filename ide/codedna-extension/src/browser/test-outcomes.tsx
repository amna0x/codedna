import * as React from '@theia/core/shared/react';
import { SelectionRun } from '../common/codedna-protocol';
import { Chip } from './ui';

/** Display recorded outcomes, including individual checks when the runner supplies them. */
export function TestOutcomes({ tests }: { tests: SelectionRun['results']['tests'] }): React.ReactElement {
    return <div className='cd-card'>{tests.map(test => <section key={test.id}>
        <div className='cd-row cd-static'>
            <code>{test.id}</code><Chip tone={tone(test.status)}>{test.status}</Chip>
            <span>{test.time.toFixed(2)} s</span>
        </div>
        {test.cases?.length ? <ul aria-label={`Checks in ${test.id}`}>{test.cases.map((item, index) =>
            <li key={`${item.name}-${index}`}>
                <span>{item.name.replace(/([a-z0-9])([A-Z])/g, '$1 $2').replace(/_/g, ' ')}</span>
                {' — '}<strong>{item.status}</strong>{' '}({item.time.toFixed(2)} s)
                <details><summary>Recorded check name and details</summary><code>{item.name}</code>
                    {item.message && <pre>{item.message}</pre>}</details>
            </li>)}</ul> : <p className='cd-help'>Individual check details were not recorded for this run.</p>}
    </section>)}</div>;
}

function tone(status: string): 'added' | 'deleted' | 'muted' {
    return status === 'passed' ? 'added' : status === 'failed' || status === 'error' ? 'deleted' : 'muted';
}
