import { CommandService } from '@theia/core/lib/common/command';
import * as React from '@theia/core/shared/react';
import { inject, injectable, postConstruct } from '@theia/core/shared/inversify';
import { ConfirmDialog } from '@theia/core/lib/browser/dialogs';
import { ProgressService } from '@theia/core/lib/common/progress-service';
import { ReactWidget } from '@theia/core/lib/browser/widgets/react-widget';
import { CodeDnaService, SelectionReport, SelectionStrategy, SelectionRun, TestDiscovery } from '../common/codedna-protocol';
import { CodeDnaComparison } from './comparison';
import { CodeDnaWorkspace } from './codedna-workspace';
import { withProgress } from './progress';
import { decisionRecord, recoverySteps } from './decision-evidence';
import { TestOutcomes } from './test-outcomes';
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
    @inject(CommandService) protected readonly commands: CommandService;

    protected strategy: SelectionStrategy = 'risk';
    protected loading = false;
    protected error: string | undefined;
    protected report: SelectionReport | undefined;
    protected execution: SelectionRun | undefined;
    protected historyCsv = '';
    protected reportHistory = '';
    protected reportStrategy: SelectionStrategy = 'risk';
    protected generation = 0;
    protected notice: string | undefined;
    protected inspected: TestDiscovery['tests'][number] | undefined;
    protected inspecting = false;
    protected readonly revealTestDetails = (element: HTMLElement | null): void => {
        element?.scrollIntoView({ block: 'nearest' });
    };
    protected discovery: { report: SelectionReport; result: Promise<TestDiscovery> } | undefined;

    @postConstruct()
    protected init(): void {
        this.id = TestsViewWidget.ID;
        this.title.label = TestsViewWidget.LABEL;
        this.title.caption = 'CodeDNA: which tests to run for your change, and why';
        this.title.iconClass = 'codicon codicon-beaker';
        this.title.closable = true;
        this.addClass('codedna-view');
        this.toDispose.push(this.comparison.onDidChange(() => this.invalidate()));
        this.update();
    }

    protected invalidate(): void {
        this.generation++;
        this.report = undefined;
        this.execution = undefined;
        this.discovery = undefined;
        this.inspected = undefined;
        this.error = undefined;
        this.notice = undefined;
        this.update();
    }

    protected async suggest(): Promise<void> {
        if (this.loading) { return; }
        this.invalidate();
        const generation = this.generation;
        const base = this.comparison.base, head = this.comparison.head;
        const strategy = this.strategy, history = this.historyCsv;
        this.loading = true;
        this.update();
        try {
            const repo = await this.workspace.repositoryPath();
            if (!repo) { throw new Error('Open a folder first.'); }
            const result = await withProgress(this.progress, strategy === 'risk' ? 'CodeDNA: checking history and choosing tests' : 'CodeDNA: choosing tests',
                () => this.codedna.select(repo, base, head, strategy, history));
            if (generation !== this.generation) { return; }
            this.report = result;
            this.reportHistory = history;
            this.reportStrategy = strategy;
        } catch (error) {
            if (generation === this.generation) {
                this.error = error instanceof Error ? error.message : String(error);
            }
        } finally {
            this.loading = false;
            this.update();
        }
    }

    protected async runSelected(): Promise<void> {
        const report = this.report, generation = this.generation;
        if (!report || this.loading) { return; }
        const confirmed = await new ConfirmDialog({
            title: 'Run project tests?',
            msg: 'This executes this project’s code and build plugins (Maven, Gradle or pytest). Maven may download dependencies. Run only projects you trust.',
            ok: 'Run tests', cancel: 'Cancel'
        }).open();
        if (!confirmed || this.report !== report || generation !== this.generation) { return; }
        this.loading = true;
        this.error = undefined;
        this.notice = undefined;
        this.execution = undefined;
        this.update();
        try {
            const execution = await withProgress(this.progress, 'CodeDNA: running selected tests',
                () => this.codedna.runSelection(report.repository,
                    report.base_commit, report.head_commit, this.reportStrategy, this.reportHistory));
            if (generation !== this.generation || this.report !== report) {
                this.notice = 'Tests finished for the previous comparison. Open Project history to inspect the saved results.';
                return;
            }
            this.execution = execution;
            this.report = execution.selection;
        } catch (error) {
            if (generation === this.generation) {
                this.error = error instanceof Error ? error.message : String(error);
            }
        } finally {
            this.loading = false;
            this.update();
        }
    }

    protected async discoverTest(report: SelectionReport, test: string): Promise<TestDiscovery['tests'][number] | undefined> {
        if (this.report !== report) { return undefined; }
        if (this.discovery?.report !== report) {
            this.discovery = { report, result: this.codedna.tests(report.repository, report.head_commit) };
        }
        const discovery = await this.discovery.result;
        if (this.report !== report) { return undefined; }
        if (discovery.commit !== report.head_commit) {
            throw new Error('Test details belong to another commit. Suggest tests again.');
        }
        const item = discovery.tests.find(entry => entry.id === test);
        if (!item?.file) { throw new Error(`No source file was discovered for ${test} at this commit.`); }
        return item;
    }

    protected async inspectTest(report: SelectionReport, test: string): Promise<void> {
        if (this.inspecting) { return; }
        this.inspecting = true;
        this.update();
        try {
            const item = await this.discoverTest(report, test);
            if (this.report === report) { this.inspected = item; }
        } catch (error) { this.testDetailError(report, error); }
        finally { this.inspecting = false; this.update(); }
    }

    protected testDetailError(report: SelectionReport, error: unknown): void {
        if (this.report === report) {
            this.discovery = undefined;
            this.error = error instanceof Error ? error.message : String(error);
            this.update();
        }
    }

    protected async openTest(report: SelectionReport, test: string): Promise<void> {
        try {
            const item = await this.discoverTest(report, test);
            if (item && this.report === report) { await this.workspace.openRepositoryFile(report.repository, item.file); }
        } catch (error) { this.testDetailError(report, error); }
    }

    protected async exportEvidence(report: SelectionReport): Promise<void> {
        if (this.report !== report) { return; }
        try {
            const content = JSON.stringify(decisionRecord(report, this.execution), null, 2) + '\n';
            const saved = await this.workspace.saveDecisionEvidence(content);
            if (saved && this.report === report) { this.notice = 'Decision evidence saved. Review local paths and test names before sharing.'; }
        } catch (error) {
            if (this.report === report) { this.error = error instanceof Error ? error.message : String(error); }
        } finally { this.update(); }
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
                        onChange={e => { this.strategy = e.target.value as SelectionStrategy; this.invalidate(); }}>
                        {STRATEGIES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                    </select>
                </label>
                {this.strategy === 'risk' && <label className='cd-field'>
                    <span className='cd-field-label'>Test history file (optional)</span>
                    <input value={this.historyCsv} disabled={this.loading}
                        placeholder='Use this project’s saved history'
                        onChange={e => { this.historyCsv = e.target.value; this.invalidate(); }} />
                </label>}
                <button className='cd-button' type='submit'  disabled={this.loading} aria-busy={this.loading}>
                    {this.loading ? <><Spinner /> Finding tests…</> : 'Suggest tests'}
                </button>
                <button className='cd-button' type='button' onClick={() => this.commands.executeCommand('codedna.history.open')}>
                    Open project history
                </button>
            </form>
            {this.error && <ErrorNotice message={this.error} />}
            {this.notice && <p className='cd-notice' role='status'>{this.notice}</p>}
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
                {risk?.status === 'unvalidated' && <p className='cd-help'>Passing tests and validated skip risk are different.
                    A successful run records what happened; it does not prove that future tests can be skipped.
                    Only sufficiently audited earlier history can support that decision.</p>}
                {risk?.reasons.some(reason => /another repository, branch or future commits/i.test(reason)) &&
                    <p className='cd-help'>This can also happen when history already contains results for the change being compared.
                        For a previous-commit comparison, those outcomes are later than its base commit.
                        CodeDNA refuses to use them to predict that same change. Keep your saved history;
                        use HEAD to WORKTREE for a new uncommitted change, or supply history from before the comparison base.
                        The earlier history must still pass its audit.</p>}
                {!!risk?.reasons.length && <ul>{risk.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul>}
                <details><summary>Evidence health and next steps</summary>
                    <p>Project: <code>{report.repository}</code></p>
                    <p>Evidence must precede base <code>{report.base_commit}</code>. Target: <code>{report.head_commit}</code>.</p>
                    {risk?.provenance?.history_sha256 && <p>History fingerprint: <code>{risk.provenance.history_sha256}</code></p>}
                    <ul>{recoverySteps(report).map(step => <li key={step}>{step}</li>)}</ul>
                    {risk?.note && <p>{risk.note}</p>}
                    {risk?.conformal?.note && <p>{risk.conformal.note}</p>}
                </details>
            </section>
            <button className='cd-button' onClick={() => this.exportEvidence(report)}>Export decision evidence</button>
            <p className='cd-help'>The export includes local paths, test names and risk evidence. It excludes source code and raw build logs.</p>
            <button className='cd-button' disabled={this.loading || !report.total_tests}
                onClick={() => this.runSelected()}>
                {this.loading ? 'Running…' : `Run ${report.selected.length} recommended tests`}
            </button>
            {this.execution && <section aria-label='Test execution results'>
                <h3>{this.execution.results.exit_codes.some(code => code !== 0)
                    ? 'Build did not complete successfully'
                    : this.execution.results.tests.length === 0 ? 'No test results recorded'
                    : `${this.execution.results.failing_tests.length} failing tests`}</h3>
                <p>Finished in {this.execution.results.duration_seconds.toFixed(1)} seconds.</p>
                <TestOutcomes tests={this.execution.results.tests} />
                <p className='cd-help'>These are tests written in your project. CodeDNA selects and runs them.
                    The checks below each class or module show what the runner actually executed.</p>
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
                        : <>Run {report.selected.length} of {plural(report.total_tests, 'test', 'tests')}.
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
            {this.inspected && <section key={`${report.head_commit}:${this.inspected.id}`} ref={this.revealTestDetails}
                className='cd-notice' aria-label='Discovered test details' aria-live='polite'>
                <h3>Checks declared in {simpleName(this.inspected.id)}</h3>
                <p><code>{this.inspected.file}</code> at <code>{report.head_commit.slice(0, 12)}</code></p>
                <p>{this.inspected.framework ?? 'Framework not reported'}{this.inspected.language ? ` · ${this.inspected.language}` : ''}</p>
                {this.inspected.methods?.length ? <ul>{this.inspected.methods.map(method => <li key={method}>
                    <span>{method.replace(/([a-z0-9])([A-Z])/g, '$1 $2').replace(/_/g, ' ')}</span> <code>{method}</code>
                </li>)}</ul> : <p>No individual check names were reported by static discovery.</p>}
                <p className='cd-help'>These names come from project source. Read the assertions for exact behavior; discovery does not execute or verify these checks. Source navigation opens your current working copy, which may differ from this commit.</p>
                <button className='cd-button' onClick={() => this.openTest(report, this.inspected!.id)}>Read source (working copy)</button>
            </section>}
            {report.selected.length > 0 && <section aria-label='Run these'>
                <h3>Run these</h3>
                <p className='cd-help'>Each item is a test class or module and may contain several checks.
                    Select an item to read its source; after running, inspect its individual outcomes above.</p>
                <div className='cd-card'>
                    {report.selected.map(item => <div key={item.test}><button className='cd-row'
                        title={`Open ${item.test}`}
                        onClick={() => this.openTest(report, item.test)}>
                        <span className='cd-code'>{simpleName(item.test)}</span>
                        <span className='cd-row-meta'>
                            <Chip tone='added'>Run</Chip>
                            <span className='cd-meta'>{breakable(packageName(item.test))}</span>
                        </span>
                        <ul className='cd-reasons'>
                            {unique(item.reasons.map(friendlyReason)).map(r => <li key={r}>{r}</li>)}
                        </ul>
                    </button>
                    {item.file && <p className='cd-meta'><code>{item.file}</code></p>}
                    <button className='cd-button' disabled={this.inspecting} onClick={() => this.inspectTest(report, item.test)}>
                        {this.inspecting ? 'Loading checks…' : 'Explain this test'}
                    </button></div>)}
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

function unique(values: string[]): string[] {
    return [...new Set(values)];
}
