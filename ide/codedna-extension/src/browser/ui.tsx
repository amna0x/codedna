import * as React from '@theia/core/shared/react';
import { CodeDnaComparison, ComparisonPreset, PRESETS } from './comparison';
import { friendlyError } from './plain-language';

export function ComparePicker({ comparison, disabled }: { comparison: CodeDnaComparison; disabled: boolean }): React.ReactElement {
    return <div className='cd-compare'>
        <label className='cd-field'>
            <span className='cd-field-label'>Compare</span>
            <select value={comparison.preset} disabled={disabled}
                onChange={e => comparison.update({ preset: e.target.value as ComparisonPreset })}>
                {PRESETS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
        </label>
        <p className='cd-help'>{comparison.preset === 'uncommitted'
            ? 'Save your files first. CodeDNA compares them with your latest commit.'
            : comparison.preset === 'custom'
                ? 'Compare two saved versions using commit IDs or branch names.'
                : 'Compares saved Git commits. Uncommitted edits are excluded.'}</p>
        {comparison.preset === 'custom' && <div className='cd-custom-range'>
            <label className='cd-field'>
                <span className='cd-field-label'>From</span>
                <input value={comparison.customBase} spellCheck={false} disabled={disabled}
                    placeholder='HEAD~1' aria-describedby='cd-range-help'
                    onChange={e => comparison.update({ customBase: e.target.value })} />
            </label>
            <label className='cd-field'>
                <span className='cd-field-label'>To</span>
                <input value={comparison.customHead} spellCheck={false} disabled={disabled}
                    placeholder='HEAD'
                    onChange={e => comparison.update({ customHead: e.target.value })} />
            </label>
            <p className='cd-help' id='cd-range-help'>A commit id, a branch name, or HEAD (your latest commit).</p>
        </div>}
    </div>;
}

export function ErrorNotice({ message }: { message: string }): React.ReactElement {
    const error = friendlyError(message);
    return <div className='cd-notice cd-error' role='alert'>
        <strong>{error.title}</strong>
        <p>{error.help}</p>
        {error.details && <details>
            <summary>Details</summary>
            <code>{error.details}</code>
        </details>}
    </div>;
}

export function FirstRun({ action }: { action: string }): React.ReactElement {
    return <ol className='cd-steps'>
        <li><span>Open your project folder</span> <span className='cd-meta'>File → Open Folder…</span></li>
        <li><span>Pick what to compare</span> <span className='cd-meta'>Choose My uncommitted changes for saved edits, or My last commit for a committed change.</span></li>
        <li><span>Press {action}</span></li>
    </ol>;
}

export function Chip({ tone, children, title }: { tone: string; children: React.ReactNode; title?: string }): React.ReactElement {
    return <span className={`cd-chip cd-${tone}`} title={title}>{children}</span>;
}

export function Spinner(): React.ReactElement {
    return <span className='cd-spinner' aria-hidden='true' />;
}
