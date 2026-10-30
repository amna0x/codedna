import * as React from '@theia/core/shared/react';
import { CodeDnaComparison, ComparisonPreset, PRESETS } from './comparison';
import { CodeDnaWorkspace } from './codedna-workspace';
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
    return <div className='cd-getting-started'><strong>Start here — no tests run until you confirm.</strong><ol className='cd-steps'>
        <li><span>Open your project folder</span> <span className='cd-meta'>File → Open Folder…</span></li>
        <li><span>Pick what to compare</span> <span className='cd-meta'>your last commit is a good start</span></li>
        <li><span>Press {action}</span> <span className='cd-meta'>Results appear below. Click a code item to open its highlighted line.</span></li>
    </ol><p className='cd-help'>A test is an automatic check of your code’s answer. Start with reviewing a change, then choose Check tests above.</p></div>;
}

export function Chip({ tone, children, title }: { tone: string; children: React.ReactNode; title?: string }): React.ReactElement {
    return <span className={`cd-chip cd-${tone}`} title={title}>{children}</span>;
}

export function Spinner(): React.ReactElement {
    return <span className='cd-spinner' aria-hidden='true' />;
}

/** Persistent, labelled navigation instead of requiring keyboard shortcuts. */
export function WorkflowNav({ workspace, current }: { workspace: CodeDnaWorkspace; current: string }): React.ReactElement {
    const [theme, setTheme] = React.useState(workspace.theme);
    const [error, setError] = React.useState('');
    const destinations = [ ['changes', '1 · Review changes'], ['tests', '2 · Check tests'],
        ['graph', 'Impact map'], ['history', 'Past runs'], ['plugins', 'Languages'] ];
    return <div className='cd-workflow'>
        <nav aria-label='CodeDNA workflow' className='cd-workflow-links'>
            {destinations.map(([id, label]) => <button key={id} type='button' aria-current={id === current ? 'page' : undefined}
                disabled={id === current} onClick={() => { setError(''); workspace.navigate(id).catch(e => setError(String(e))); }}>{label}</button>)}
        </nav>
        <label className='cd-theme-choice'>Appearance <select aria-label='CodeDNA colour theme' value={theme}
            onChange={e => { workspace.setTheme(e.target.value); setTheme(e.target.value); }}>
            <option value='codedna-dark'>Graphite dark</option><option value='codedna-ocean'>Ocean dark</option>
            <option value='codedna-light'>Clear light</option><option value='codedna-contrast'>High contrast</option>
            {!['codedna-dark', 'codedna-ocean', 'codedna-light', 'codedna-contrast'].includes(theme) && <option value={theme}>Current editor theme</option>}
        </select></label>
        {error && <p role='alert'>{error}</p>}
    </div>;
}
