import * as React from '@theia/core/shared/react';
import { inject, injectable, postConstruct } from '@theia/core/shared/inversify';
import { ConfirmDialog } from '@theia/core/lib/browser/dialogs';
import { ProgressService } from '@theia/core/lib/common/progress-service';
import { ReactWidget } from '@theia/core/lib/browser/widgets/react-widget';
import { CodeDnaService, SelectionReport, SelectionStrategy, SelectionRun } from '../common/codedna-protocol';
import { CodeDnaComparison } from './comparison';
import { CodeDnaWorkspace } from './codedna-workspace';
import { withProgress } from './progress';
import { breakable, friendlyReason, friendlyWarning, packageName, plural, simpleName } from './plain-language';
import { Chip, ComparePicker, ErrorNotice, FirstRun, Spinner } from './ui';

const STRATEGIES: { value: SelectionStrategy; label: string }[] = [
    { value: 'risk', label: 'Validated risk stopping' },
    { value: 'dependency', label: 'Affected tests only' },
    { value: 'all', label: 'All discovered tests' }
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
    @inject(ProgressService) protected readonly progress: ProgressService;

    protected strategy: SelectionStrategy = 'risk';
    protected loading = false;
    protected error: string | undefined;
    protected report: SelectionReport | undefined;
    protected execution: SelectionRun | undefined;
    protected historyCsv = '';
    protected reportHistory = '';
    protected reportStrategy: SelectionStrategy = 'risk';

    @postConstruct()
    protected init(): void {
        this.id = TestsViewWidget.ID;
        this.title.label = TestsViewWidget.LABEL;
        this.title.caption = 'CodeDNA: which tests to run for your change, and why';
        this.title.iconClass = 'codicon codicon-beaker';
        this.title.closable = true;
        this.addClass('codedna-view');
        this.toDispose.push(this.comparison.onDidChange(() => { this.report = undefined; this.execution = undefined; this.update(); }));
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
        this.report = undefined;
        this.execution = undefined;
        this.error = undefined;
        this.update();
        try {
            const base = this.comparison.base, head = this.comparison.head;
            const result = await withProgress(this.progress, this.strategy === 'risk' ? 'CodeDNA: checking history and choosing tests' : 'CodeDNA: choosing tests',
                () => this.codedna.select(repo, base, head, this.strategy, this.historyCsv));
            if (base !== this.comparison.base || head !== this.comparison.head) {
                this.error = 'The comparison changed. Suggest tests again.';
                return;
            }
            this.report = result;
            this.reportHistory = this.historyCsv;
            this.reportStrategy = this.strategy;
        } catch (error) {
            this.error = error instanceof Error ? error.message : String(error);
        } finally {
            this.loading = false;
            this.update();
        }
    }

    protected async runSelected(): Promise<void> {
        const report = this.report;
        if (!report || this.loading) { return; }
        const confirmed = await new ConfirmDialog({
            title: 'Run project tests?',
            msg: 'This executes this project’s code and build plugins (Maven, Gradle or pytest). Maven may download dependencies. Run only projects you trust.',
            ok: 'Run tests', cancel: 'Cancel'
        }).open();
        if (!confirmed || this.report !== report) { return; }
        this.loading = true;
        this.error = undefined;
        this.execution = undefined;
        this.update();
        try {
            this.execution = await withProgress(this.progress, 'CodeDNA: running selected tests',
                () => this.codedna.runSelection(report.repository,
                    report.base_commit, report.head_commit, this.reportStrategy, this.reportHistory));
            this.report = this.execution.selection;
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
                        onChange={e => { this.strategy = e.target.value as SelectionStrategy; this.report = undefined; this.execution = undefined; this.update(); }}>
                        {STRATEGIES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                    </select>
                </label>
                {this.strategy === 'risk' && <label className='cd-field'>
                    <span className='cd-field-label'>Test history file (optional)</span>
                    <input value={this.historyCsv} disabled={this.loading}
                        placeholder='Use this project’s saved history'
                        onChange={e => { this.historyCsv = e.target.value; this.report = undefined; this.execution = undefined; this.update(); }} />
                </label>}
                <button className='cd-button' type='submit'  disabled={this.loading} aria-busy={this.loading}>
                    {this.loading ? <><Spinner /> Finding tests…</> : 'Suggest tests'}
                </button>
            </form>
            {this.error && <ErrorNotice message={this.error} />}
            {this.report ? this.renderReport(this.report) : !this.loading && !this.error && <FirstRun action='Suggest tests' />}
        </div>;
    }

    protected renderReport(report: SelectionReport): React.ReactNode {
        const time = report.estimated_time;
        const risk = report.risk;
        const notes = report.warnings.map(friendlyWarning).filter((w): w is string => !!w);
        const everything = report.selected.length === report.total_tests && report.total_tests > 0;
        return <div className='cd-results'>
            <section className='cd-notice' aria-label='Risk evidence'>
                <h3>{risk?.status === 'validated_history' ? 'Validated on earlier project history' : 'Risk unvalidated'}</h3>
                {risk?.status === 'validated_history'
                    ? <p>Estimated chance of at least one skipped test failing: {((risk.estimated_skip_risk ?? 0) * 100).toFixed(2)}%.
                        Target: {(risk.target * 100).toFixed(0)}%. This is an estimate, not a guarantee.</p>
                    : <p>{risk ? 'Run the full suite because the evidence does not justify risk-based skipping.'
                        : 'This structural selection has no validated probability of missing failures.'}</p>}
                {risk?.validation && <p>Prior audit: {risk.validation.commits} commits,
                    {' '}{risk.validation.failing_commits} with failures. Historical miss-rate upper bound:
                    {' '}{(risk.validation.miss_upper_bound * 100).toFixed(2)}%.</p>}
                {!!risk?.reasons.length && <ul>{risk.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul>}
            </section>
            <button className='cd-button' disabled={this.loading || !report.total_tests}
                onClick={() => this.runSelected()}>
                {this.loading ? 'Running…' : `Run ${report.selected.length} recommended test classes`}
            </button>
            {this.execution && <section aria-label='Test execution results'>
                <h3>{this.execution.results.exit_codes.some(code => code !== 0)
                    ? 'Build did not complete successfully'
                    : this.execution.results.tests.length === 0 ? 'No test results recorded'
                    : `${this.execution.results.failing_tests.length} failing test classes`}</h3>
                <p>Finished in {this.execution.results.duration_seconds.toFixed(1)} seconds.</p>
                <div className='cd-card'>{this.execution.results.tests.map(test => <div className='cd-row cd-static' key={test.id}>
                    <span className='cd-code'>{simpleName(test.id)}</span><span>{test.status}</span>
                </div>)}</div>
                {this.execution.results.warnings.map(warning => <p key={warning}>{warning}</p>)}
                {this.execution.recording && <p className='cd-footnote'>{this.execution.recording.recorded
                    ? `Saved as project history (${this.execution.recording.commits_with_results} commits with full results). Risk selection turns on once this history passes its audit.`
                    : `Not saved as history: ${this.execution.recording.reason}`}</p>}
                <p className='cd-footnote'>Logs and reports: {this.execution.output_dir}</p>
            </section>}
            <p className='cd-meta'>Compared commits: {report.base_commit.slice(0, 8)} → {report.head_commit.slice(0, 8)}</p>
            <p className='cd-lede'>
                {report.total_tests === 0
                    ? 'No JUnit or pytest tests were found in this project.'
                    : report.selected.length === 0
                        ? 'No tests are recommended by the current selection policy.'
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
                        onClick={() => this.workspace.openFile(item.file ?? testPath(item.test))}>
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
            {report.skipped.length > 0 && <section aria-label='Not selected'>
                <h3>Not selected</h3>
                <div className='cd-card'>
                    {report.skipped.map(test => <div className='cd-row cd-static' key={test}>
                        <span className='cd-code'>{simpleName(test)}</span>
                        <span className='cd-row-meta'>
                            <Chip tone='muted'>Skip</Chip>
                            <span className='cd-meta'>No failure-free guarantee. Review the selection evidence.</span>
                        </span>
                    </div>)}
                </div>
            </section>}
            <p className='cd-footnote'>
                Risk-based skipping requires a separate prior audit. Refresh evidence with full-suite runs; selected-only results cannot reveal missed failures.
            </p>
        </div>;
    }
}

/** Best guess at a test's file from its ID, for reports without `file` (Python: `py:tests.test_x` → `tests/test_x.py`). */
function testPath(testId: string): string {
    if (testId.startsWith('py:')) {
        return `${testId.slice(3).replace(/\./g, '/')}.py`;
    }
    return `src/test/java/${testId.replace(/\./g, '/')}.java`;
}

function unique(values: string[]): string[] {
    return [...new Set(values)];
}
