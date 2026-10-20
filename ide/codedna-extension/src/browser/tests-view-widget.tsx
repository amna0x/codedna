import * as React from '@theia/core/shared/react';
import { inject, injectable, postConstruct } from '@theia/core/shared/inversify';
import { ReactWidget } from '@theia/core/lib/browser/widgets/react-widget';
import { CodeDnaService, SelectionReport, SelectionStrategy } from '../common/codedna-protocol';
import { CodeDnaComparison } from './comparison';
import { CodeDnaWorkspace } from './codedna-workspace';
import { breakable, friendlyReason, friendlyWarning, packageName, plural, simpleName } from './plain-language';
import { Chip, ComparePicker, ErrorNotice, FirstRun, Spinner } from './ui';

const STRATEGIES: { value: SelectionStrategy; label: string }[] = [
    { value: 'dependency', label: 'Affected tests only' },
    { value: 'all', label: 'All tests (safest)' }
];

/**
 * "Tests to run": which test classes a change needs, with the reason for
 * each, in plain language. Same selection as `codedna select`; failure-risk
 * scores appear only once a model exists — nothing is invented.
 */
@injectable()
export class TestsViewWidget extends ReactWidget {

    static readonly ID = 'codedna.tests';
    static readonly LABEL = 'Tests to run';

    @inject(CodeDnaService) protected readonly codedna: CodeDnaService;
    @inject(CodeDnaWorkspace) protected readonly workspace: CodeDnaWorkspace;
    @inject(CodeDnaComparison) protected readonly comparison: CodeDnaComparison;

    protected strategy: SelectionStrategy = 'dependency';
    protected loading = false;
    protected error: string | undefined;
    protected report: SelectionReport | undefined;

    @postConstruct()
    protected init(): void {
        this.id = TestsViewWidget.ID;
        this.title.label = TestsViewWidget.LABEL;
        this.title.caption = 'CodeDNA: which tests to run for your change, and why';
        this.title.iconClass = 'codicon codicon-beaker';
        this.title.closable = true;
        this.addClass('codedna-view');
        this.toDispose.push(this.comparison.onDidChange(() => this.update()));
        this.update();
    }

    protected async suggest(): Promise<void> {
        const repo = await this.workspace.repositoryPath();
        if (!repo) {
            this.error = 'Open a folder first.';
            this.update();
            return;
        }
        this.loading = true;
        this.error = undefined;
        this.update();
        try {
            this.report = await this.codedna.select(repo, this.comparison.base, this.comparison.head, this.strategy);
        } catch (error) {
            this.error = error instanceof Error ? error.message : String(error);
        } finally {
            this.loading = false;
            this.update();
        }
    }

    protected render(): React.ReactNode {
        return <div>
            <header className='cd-header'>
                <h2>Tests to run</h2>
                <p className='cd-subtitle'>Run the tests your change can break — and see why each one is needed.</p>
            </header>
            <form className='cd-controls' onSubmit={e => { e.preventDefault(); this.suggest(); }}>
                <ComparePicker comparison={this.comparison} disabled={this.loading} />
                <label className='cd-field'>
                    <span className='cd-field-label'>Which tests</span>
                    <select value={this.strategy} disabled={this.loading}
                        onChange={e => { this.strategy = e.target.value as SelectionStrategy; this.update(); }}>
                        {STRATEGIES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                    </select>
                </label>
                <button className='cd-button' type='submit' disabled={this.loading} aria-busy={this.loading}>
                    {this.loading ? <><Spinner /> Finding tests…</> : 'Suggest tests'}
                </button>
            </form>
            {this.error && <ErrorNotice message={this.error} />}
            {this.report ? this.renderReport(this.report) : !this.loading && !this.error && <FirstRun action='Suggest tests' />}
        </div>;
    }

    protected renderReport(report: SelectionReport): React.ReactNode {
        const time = report.estimated_time;
        const notes = report.warnings.map(friendlyWarning).filter((w): w is string => !!w);
        const everything = report.selected.length === report.total_tests && report.total_tests > 0;
        return <div className='cd-results'>
            <p className='cd-lede'>
                {report.total_tests === 0
                    ? 'No JUnit tests were found in this project.'
                    : report.selected.length === 0
                        ? 'No tests are affected by this change.'
                        : <>Run {report.selected.length} of {plural(report.total_tests, 'test class', 'test classes')}.
                            {everything ? ' That’s all of them.' : ` You can skip ${report.skipped.length}.`}</>}
            </p>
            <p className='cd-help'>
                {time
                    ? `That saves about ${Math.round(time.saved_ratio * 100)}% of test time.`
                    : 'Time savings show up after your tests have been run once with CodeDNA.'}
            </p>
            {notes.length > 0 && <div className='cd-notice'>
                <strong>Good to know</strong>
                <ul>{notes.map(note => <li key={note}>{note}</li>)}</ul>
            </div>}
            {report.selected.length > 0 && <section aria-label='Run these'>
                <h3>Run these</h3>
                <div className='cd-card'>
                    {report.selected.map(item => <button className='cd-row' key={item.test}
                        title={`Open ${item.test}`}
                        onClick={() => this.workspace.openFile(testPath(item.test))}>
                        <span className='cd-code'>{simpleName(item.test)}</span>
                        <span className='cd-row-meta'>
                            <Chip tone='added'>Run</Chip>
                            <span className='cd-meta'>{breakable(packageName(item.test))}</span>
                        </span>
                        <ul className='cd-reasons'>
                            {unique(item.reasons.map(friendlyReason)).map(r => <li key={r}>{r}</li>)}
                        </ul>
                    </button>)}
                </div>
            </section>}
            {report.skipped.length > 0 && <section aria-label='Safe to skip'>
                <h3>Safe to skip</h3>
                <div className='cd-card'>
                    {report.skipped.map(test => <div className='cd-row cd-static' key={test}>
                        <span className='cd-code'>{simpleName(test)}</span>
                        <span className='cd-row-meta'>
                            <Chip tone='muted'>Skip</Chip>
                            <span className='cd-meta'>Doesn’t use anything that changed.</span>
                        </span>
                    </div>)}
                </div>
            </section>}
            <p className='cd-footnote'>
                Failure risk for each test appears once CodeDNA has learned from this project’s test history.
            </p>
        </div>;
    }
}

function testPath(testId: string): string {
    return `src/test/java/${testId.replace(/\./g, '/')}.java`;
}

function unique(values: string[]): string[] {
    return [...new Set(values)];
}
