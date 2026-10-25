import * as React from '@theia/core/shared/react';
import { inject, injectable, postConstruct } from '@theia/core/shared/inversify';
import { ProgressService } from '@theia/core/lib/common/progress-service';
import { ReactWidget } from '@theia/core/lib/browser/widgets/react-widget';
import { CodeDnaService, ProjectHistory, RecordedHistory, SavedRun } from '../common/codedna-protocol';
import { CodeDnaWorkspace } from './codedna-workspace';
import { withProgress } from './progress';
import { Chip, ErrorNotice, Spinner } from './ui';

/** Saved test runs of the project and adding them to its recorded history (D-057; view first drafted by Codex). */
@injectable()
export class HistoryViewWidget extends ReactWidget {
    static readonly ID = 'codedna.history';
    static readonly LABEL = 'Project history';
    @inject(CodeDnaService) protected readonly codedna: CodeDnaService;
    @inject(CodeDnaWorkspace) protected readonly workspace: CodeDnaWorkspace;
    @inject(ProgressService) protected readonly progress: ProgressService;
    protected loading = false;
    protected error: string | undefined;
    protected history: ProjectHistory | undefined;
    protected recorded: RecordedHistory | undefined;
    protected selected: SavedRun | undefined;
    protected source = '';
    protected message: string | undefined;
    protected generation = 0;

    @postConstruct()
    protected init(): void {
        this.id = HistoryViewWidget.ID;
        this.title.label = HistoryViewWidget.LABEL;
        this.title.caption = 'CodeDNA: saved executions and project training history';
        this.title.iconClass = 'codicon codicon-history';
        this.title.closable = true;
        this.addClass('codedna-view');
        this.update();
    }

    protected async task(label: string, action: (repo: string, current: () => boolean) => Promise<void>): Promise<void> {
        if (this.loading) { return; }
        const repo = await this.workspace.repositoryPath();
        if (!repo) { this.error = 'Open a Git project first.'; this.update(); return; }
        const generation = this.generation;
        const current = () => generation === this.generation;
        this.loading = true;
        this.error = undefined;
        this.update();
        try {
            await withProgress(this.progress, label, () => action(repo, current));
        } catch (error) {
            if (current()) { this.error = error instanceof Error ? error.message : String(error); }
        } finally {
            this.loading = false;
            this.update();
        }
    }

    protected async refresh(): Promise<void> {
        await this.task('CodeDNA: loading saved test runs', async (repo, current) => {
            const history = await this.codedna.projectHistory(repo);
            if (current()) { this.history = history; this.selected = undefined; }
        });
    }

    protected async record(): Promise<void> {
        await this.task('CodeDNA: adding saved runs to the project history', async (repo, current) => {
            const recorded = await this.codedna.recordSavedRuns(repo);
            const history = await this.codedna.projectHistory(repo);
            if (current()) {
                this.recorded = recorded;
                this.history = history;
                this.message = recorded.recorded_runs
                    ? 'History updated. Tests to run uses it when the history-file field is empty; the risk gate still decides whether it is enough.'
                    : 'No saved run could be added; the reasons are listed below.';
            }
        });
    }

    protected async import(): Promise<void> {
        const source = this.source.trim();
        if (!source) { return; }
        await this.task('CodeDNA: importing recorded outcomes', async (repo, current) => {
            const imported = await this.codedna.importRun(repo, source);
            const history = await this.codedna.projectHistory(repo);
            if (current()) {
                this.history = history;
                this.recorded = undefined;
                this.message = `Imported ${imported.tests} test classes (${imported.failures} failing). No tests were executed. Add saved runs to history to use it.`;
            }
        });
    }

    protected async inspect(id: string): Promise<void> {
        await this.task('CodeDNA: opening saved test outcomes', async (repo, current) => {
            const selected = await this.codedna.savedRun(repo, id);
            if (current()) { this.selected = selected; }
        });
    }

    protected async open(path: string): Promise<void> {
        try {
            if (this.history) { await this.workspace.openRepositoryFile(this.history.repository, path); }
        }
        catch (error) { this.error = String(error); this.update(); }
    }

    protected render(): React.ReactNode {
        const history = this.history;
        return <div>
            <header className='cd-header'>
                <h2>Project history</h2>
                <p className='cd-subtitle'>Saved test runs of this project. Complete ones become the history CodeDNA needs before it trusts its risk estimates.</p>
            </header>
            <form className='cd-controls' onSubmit={e => { e.preventDefault(); this.refresh(); }}>
                <button className='cd-button' disabled={this.loading} aria-busy={this.loading}>
                    {this.loading ? <><Spinner /> Working…</> : 'Refresh saved runs'}
                </button>
            </form>
            <form className='cd-controls' onSubmit={e => { e.preventDefault(); this.import(); }}>
                <label className='cd-field'>
                    <span className='cd-field-label'>Import recorded results</span>
                    <input value={this.source} disabled={this.loading} placeholder='Full path to results.json'
                        onChange={e => { this.source = e.currentTarget.value; this.update(); }} />
                </label>
                <button className='cd-button' disabled={this.loading || !this.source.trim()}>Import results</button>
                <p className='cd-help'>Reads a saved CodeDNA results.json. Importing and adding history never execute project code.</p>
            </form>
            {this.error && <ErrorNotice message={this.error} />}
            {this.message && <p className='cd-notice' role='status'>{this.message}</p>}
            {history && <>
                <section className='cd-notice'>
                    <h3>Recorded history</h3>
                    <p>{history.candidate_runs} saved runs ({history.candidate_commits} commits) can be history.
                        {' '}{history.history_csv ? 'A history file exists for this project.' : 'No history file yet.'}</p>
                    <button className='cd-button' disabled={this.loading || !history.candidate_runs}
                        onClick={() => this.record()}>Add saved runs to history</button>
                    <p className='cd-help'>Only complete runs on the current branch count. Runs with failing tests count; partial runs never do.
                        Whole-suite runs from Tests to run are added automatically.</p>
                </section>
                {this.recorded && <section className='cd-card' aria-label='Recorded project history'>
                    <h3>History updated</h3>
                    <p>{this.recorded.recorded_runs} runs added; {this.recorded.commits_with_results ?? 0} commits now have results.</p>
                    <p className='cd-code'>{this.recorded.history_csv}</p>
                    {this.recorded.warnings.map(w => <p key={w} className='cd-help'>{w}</p>)}
                    {this.recorded.skipped.length > 0 && <details><summary>Runs not added ({this.recorded.skipped.length})</summary><ul>{this.recorded.skipped.map(r =>
                        <li key={r.id}><code>{r.id.slice(0, 12)}</code>: {r.reason}</li>)}</ul></details>}
                </section>}
                <h3>Saved executions</h3>
                {history.runs.length === 0 ? <p>No saved runs yet. Run recommended tests from Tests to run, or import recorded results above.</p>
                    : <div className='cd-card'>{history.runs.map(run => <button
                        key={run.id} className='cd-row' disabled={this.loading} onClick={() => this.inspect(run.id)}>
                        <span><code>{run.commit?.slice(0, 12) ?? 'Unreadable run'}</code><br />
                            <span className='cd-meta'>{new Date(run.recorded_at).toLocaleString()} · {run.tests} classes · {run.duration_seconds.toFixed(1)} s</span>
                            {run.reason && <span className='cd-help'>{run.reason}</span>}</span>
                        <Chip tone={run.failures ? 'deleted' : 'muted'}>{run.failures ? `${run.failures} failing` : 'No recorded failures'}</Chip>
                        {run.candidate && <Chip tone='added'>can be history</Chip>}
                    </button>)}</div>}
                {history.warnings.map(w => <p className='cd-notice' key={w}>{w}</p>)}
                <p className='cd-footnote'>{history.note}</p>
            </>}
            {this.selected && <section aria-label='Saved execution details'>
                <h3>Recorded test outcomes</h3>
                <div className='cd-card'>{this.selected.results.tests.map(t => <div className='cd-row cd-static' key={t.id}>
                    <span className='cd-code'>{t.id}</span>
                    <Chip tone={t.status === 'failed' || t.status === 'error' ? 'deleted' : t.status === 'passed' ? 'added' : 'muted'}>{t.status}</Chip>
                    <span className='cd-meta'>{t.time.toFixed(2)} s</span>
                </div>)}</div>
                <button className='cd-button' onClick={() => this.open(this.selected!.result_path)}>Open saved results</button>
                {this.selected.logs.map(log => <button className='cd-button' key={log} onClick={() => this.open(log)}>Open {log.split('/').pop()}</button>)}
                {this.selected.results.warnings.map(w => <p className='cd-help' key={w}>{w}</p>)}
            </section>}
        </div>;
    }
}
