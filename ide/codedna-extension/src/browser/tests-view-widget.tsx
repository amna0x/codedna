import * as React from '@theia/core/shared/react';
import { inject, injectable, postConstruct } from '@theia/core/shared/inversify';
import { ReactWidget } from '@theia/core/lib/browser/widgets/react-widget';
import { CodeDnaService, RiskReport, SelectionReport, SelectionStrategy } from '../common/codedna-protocol';
import { CodeDnaComparison } from './comparison';
import { CodeDnaWorkspace } from './codedna-workspace';
import { breakable, friendlyReason, friendlyWarning, packageName, plural, simpleName } from './plain-language';
import { Chip, ComparePicker, ErrorNotice, FirstRun, Spinner } from './ui';

type Mode = SelectionStrategy | 'risk';

const STRATEGIES: { value: Mode; label: string }[] = [
    { value: 'dependency', label: 'Affected tests only' },
    { value: 'risk', label: 'Learned from test history (risk check)' },
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

    protected strategy: Mode = 'dependency';
    protected loading = false;
    protected error: string | undefined;
    protected report: SelectionReport | undefined;
    protected riskReport: RiskReport | undefined;

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
            if (this.strategy === 'risk') {
                this.report = undefined;
                this.riskReport = await this.codedna.risk(repo, this.comparison.base, this.comparison.head);
            } else {
                this.riskReport = undefined;
                this.report = await this.codedna.select(repo, this.comparison.base, this.comparison.head, this.strategy);
            }
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
                        onChange={e => { this.strategy = e.target.value as Mode; this.update(); }}>
                        {STRATEGIES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                    </select>
                </label>
                <button className='cd-button' type='submit' disabled={this.loading} aria-busy={this.loading}>
                    {this.loading ? <><Spinner /> Finding tests…</> : 'Suggest tests'}
                </button>
            </form>
            {this.error && <ErrorNotice message={this.error} />}
            {this.riskReport ? this.renderRisk(this.riskReport)
                : this.report ? this.renderReport(this.report)
                    : !this.loading && !this.error && <FirstRun action='Suggest tests' />}
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
                For failure risk per test, pick “Learned from test history”.
            </p>
        </div>;
    }

    protected renderRisk(report: RiskReport): React.ReactNode {
        const { gate, decision } = report;
        const validated = gate.status === 'validated';
        const full = decision.mode === 'full_suite';
        const target = gate.config.risk_target;
        const evidence = gate.evidence.validation;
        const probability = new Map(report.tests.map(t => [t.test, t.probability]));
        return <div className='cd-results'>
            <p className='cd-lede'>
                {full
                    ? <>Run all {plural(decision.selected.length, 'test class', 'test classes')}.</>
                    : <>Run {decision.selected.length} of {plural(report.tests.length, 'test class', 'test classes')}.
                        {` Estimated chance that a skipped test fails: ${percent(decision.estimated_skip_risk ?? 0)}.`}</>}
            </p>
            <p className='cd-help'>
                {full
                    ? 'CodeDNA isn’t confident enough to skip anything for this change.'
                    : `About ${Math.round(decision.estimated_time_fraction * 100)}% of the usual test time. ` +
                      `CodeDNA stops adding tests once the estimated risk is at most ${percent(target)}.`}
            </p>
            <div className={validated ? 'cd-notice' : 'cd-notice cd-error'} role='status'>
                <strong>{validated ? 'Risk check passed on this project’s history' : 'Risk not validated for this project'}</strong>
                <ul>{gate.reasons.map(r => <li key={r}>{r}</li>)}</ul>
                {evidence && <p className='cd-help'>
                    {`On the newest earlier commits a failure was missed on ${percent(evidence.observed_miss_rate)} of commits ` +
                     `(95% range ${percent(evidence.observed_miss_rate_95ci[0])}–${percent(evidence.observed_miss_rate_95ci[1])}), ` +
                     `estimated ${percent(evidence.mean_estimated_skip_risk)}.`}
                </p>}
                {report.commits_since_full_run !== null && <p className='cd-help'>
                    {`${plural(report.commits_since_full_run, 'commit', 'commits')} since the last full test run ` +
                     `(a full run is needed at least every ${gate.config.max_commits_since_full_run}).`}
                </p>}
            </div>
            {decision.reasons.length > 0 && <div className='cd-notice'>
                <strong>Why</strong>
                <ul>{decision.reasons.map(r => <li key={r}>{r}</li>)}</ul>
            </div>}
            {decision.selected.length > 0 && <section aria-label='Run these'>
                <h3>Run these</h3>
                <div className='cd-card'>
                    {decision.selected.map(test => <button className='cd-row' key={test} title={`Open ${test}`}
                        onClick={() => this.workspace.openFile(testPath(test))}>
                        <span className='cd-code'>{simpleName(test)}</span>
                        <span className='cd-row-meta'>
                            <Chip tone='added'>Run</Chip>
                            {riskChip(probability.get(test))}
                            <span className='cd-meta'>{breakable(packageName(test))}</span>
                        </span>
                    </button>)}
                </div>
            </section>}
            {decision.skipped.length > 0 && <section aria-label='Skipped'>
                <h3>Skipped</h3>
                <div className='cd-card'>
                    {decision.skipped.map(test => <div className='cd-row cd-static' key={test}>
                        <span className='cd-code'>{simpleName(test)}</span>
                        <span className='cd-row-meta'>
                            <Chip tone='muted'>Skip</Chip>
                            {riskChip(probability.get(test))}
                        </span>
                    </div>)}
                </div>
            </section>}
            <p className='cd-footnote'>{report.note}.</p>
        </div>;
    }
}

function percent(value: number): string {
    return value < 0.01 && value > 0 ? '<1%' : `${Math.round(value * 100)}%`;
}

function riskChip(probability: number | null | undefined): React.ReactNode {
    return probability === null || probability === undefined
        ? undefined
        : <Chip tone='muted' title='Estimated chance this test fails for this change'>{`fail ${percent(probability)}`}</Chip>;
}

function testPath(testId: string): string {
    return `src/test/java/${testId.replace(/\./g, '/')}.java`;
}

function unique(values: string[]): string[] {
    return [...new Set(values)];
}
