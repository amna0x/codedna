import * as React from '@theia/core/shared/react';
import { inject, injectable, postConstruct } from '@theia/core/shared/inversify';
import { ReactWidget } from '@theia/core/lib/browser/widgets/react-widget';
import { CodeDnaService, SelectionReport, SelectionStrategy } from '../common/codedna-protocol';
import { CodeDnaWorkspace } from './codedna-workspace';

const STRATEGIES: { value: SelectionStrategy; label: string; hint: string }[] = [
    { value: 'dependency', label: 'Affected by the change', hint: 'Tests that depend on changed classes (static graph).' },
    { value: 'all', label: 'All tests', hint: 'Run everything (the safe baseline).' }
];

/**
 * "Recommended tests": which test classes to run for a change, and why.
 * Failure-risk scores need a model trained on this repository's history; until
 * one exists the view says so instead of inventing numbers.
 */
@injectable()
export class TestsViewWidget extends ReactWidget {

    static readonly ID = 'codedna.tests';
    static readonly LABEL = 'Recommended tests';

    @inject(CodeDnaService) protected readonly codedna: CodeDnaService;
    @inject(CodeDnaWorkspace) protected readonly workspace: CodeDnaWorkspace;

    protected base = 'HEAD~1';
    protected head = 'HEAD';
    protected strategy: SelectionStrategy = 'dependency';
    protected loading = false;
    protected error: string | undefined;
    protected report: SelectionReport | undefined;

    @postConstruct()
    protected init(): void {
        this.id = TestsViewWidget.ID;
        this.title.label = TestsViewWidget.LABEL;
        this.title.caption = 'CodeDNA: tests to run for a change, with reasons';
        this.title.iconClass = 'codicon codicon-beaker';
        this.title.closable = true;
        this.addClass('codedna-view');
        this.update();
    }

    protected async recommend(): Promise<void> {
        const repo = await this.workspace.repositoryPath();
        if (!repo) {
            this.error = 'Open a folder that is a Git repository first.';
            this.update();
            return;
        }
        this.loading = true;
        this.error = undefined;
        this.update();
        try {
            this.report = await this.codedna.select(repo, this.base, this.head, this.strategy);
        } catch (error) {
            this.error = error instanceof Error ? error.message : String(error);
        } finally {
            this.loading = false;
            this.update();
        }
    }

    protected render(): React.ReactNode {
        const hint = STRATEGIES.find(s => s.value === this.strategy)?.hint;
        return <div>
            <h2>Recommended tests</h2>
            <p className='cd-subtitle'>Which test classes to run for a change — and why.</p>
            <form className='cd-controls' onSubmit={e => { e.preventDefault(); this.recommend(); }}>
                <label className='cd-field'>Base
                    <input value={this.base} spellCheck={false} aria-label='Base commit'
                        onChange={e => { this.base = e.target.value; this.update(); }} />
                </label>
                <label className='cd-field'>Head
                    <input value={this.head} spellCheck={false} aria-label='Head commit'
                        onChange={e => { this.head = e.target.value; this.update(); }} />
                </label>
                <label className='cd-field'>Select
                    <select value={this.strategy} aria-label='Selection strategy'
                        onChange={e => { this.strategy = e.target.value as SelectionStrategy; this.update(); }}>
                        {STRATEGIES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                    </select>
                </label>
                <button className='cd-button' type='submit' disabled={this.loading}>
                    {this.loading ? 'Selecting…' : 'Recommend'}
                </button>
            </form>
            <p className='cd-hint'>{hint}</p>
            {this.loading && <div className='cd-progress' role='progressbar' aria-label='Selecting tests' />}
            {this.error && <div className='cd-notice cd-error' role='alert'>{this.error}</div>}
            {this.report ? this.renderReport(this.report) :
                !this.loading && !this.error && <p className='cd-empty'>Choose two commits and press Recommend.</p>}
        </div>;
    }

    protected renderReport(report: SelectionReport): React.ReactNode {
        const time = report.estimated_time;
        return <>
            <div className='cd-summary'>
                <div className='cd-stat'>
                    <span className='cd-stat-value'>{report.selected.length}<span className='cd-meta'> / {report.total_tests}</span></span>
                    <span className='cd-stat-label'>test classes to run</span>
                </div>
                <div className='cd-stat'>
                    <span className='cd-stat-value'>{Math.round(report.selection_ratio * 100)}%</span>
                    <span className='cd-stat-label'>of the suite</span>
                </div>
                <div className='cd-stat'>
                    <span className='cd-stat-value'>{time ? `${Math.round(time.saved_ratio * 100)}%` : '—'}</span>
                    <span className='cd-stat-label'>{time ? 'test time saved (est.)' : 'time saved · no timings yet'}</span>
                </div>
            </div>
            <div className='cd-notice'>
                Failure risk per test appears here once a model has been trained on this
                repository's history (<code>codedna history</code>). No risk is shown until then.
            </div>
            {report.warnings.length > 0 && <div className='cd-notice cd-warning'>
                <strong>Check these</strong>
                <ul>{report.warnings.map(w => <li key={w}>{w}</li>)}</ul>
            </div>}
            <section aria-label='Run these'>
                <h3>Run these ({report.selected.length})</h3>
                {report.selected.length === 0 && <p className='cd-empty'>No tests are affected by this change.</p>}
                {report.selected.map(item => <div key={item.test}>
                    <button className='cd-row' onClick={() => this.workspace.openFile(testPath(item.test))}
                        title='Open test class (assumes src/test/java layout)'>
                        <span className='cd-badge cd-added'>run</span>
                        <span className='cd-id'>{item.test}</span>
                    </button>
                    <ul className='cd-reasons'>{item.reasons.map(r => <li key={r}>{r}</li>)}</ul>
                </div>)}
            </section>
            {report.skipped.length > 0 && <section aria-label='Skipped'>
                <h3>Can be skipped ({report.skipped.length})</h3>
                {report.skipped.map(test => <div className='cd-row cd-static' key={test}>
                    <span className='cd-badge cd-muted'>skip</span>
                    <span className='cd-id'>{test}</span>
                </div>)}
            </section>}
        </>;
    }
}

function testPath(testId: string): string {
    return `src/test/java/${testId.replace(/\./g, '/')}.java`;
}
