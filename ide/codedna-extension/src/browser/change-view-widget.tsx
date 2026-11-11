import * as React from '@theia/core/shared/react';
import { inject, injectable, postConstruct } from '@theia/core/shared/inversify';
import { ProgressService } from '@theia/core/lib/common/progress-service';
import { ReactWidget } from '@theia/core/lib/browser/widgets/react-widget';
import {
    AnalysisJob, AnalysisTimingRecord, AnalyzeReport, ChangedFile, CodeDnaService, DeclarationChange, ImpactReport, ImpactedNode, JavaFileAnalysis
} from '../common/codedna-protocol';
import { CodeDnaComparison } from './comparison';
import { CodeDnaWorkspace } from './codedna-workspace';
import { withProgress } from './progress';
import { waitForAnalysis } from './analysis-jobs-ui';
import { AnalysisTimingDetails } from './analysis-timings';
import {
    breakable, changeLabel, confidenceLabel, fileStatusLabel, friendlyWarning, kindLabel, plural, readableName, simpleName
} from './plain-language';
import { Chip, ComparePicker, ErrorNotice, FirstRun, Spinner } from './ui';

/**
 * "Changes": what changed between two commits and what else it may affect,
 * in plain language. The data is exactly what the core reports (analyze +
 * impact); only the wording is friendlier.
 */
@injectable()
export class ChangeViewWidget extends ReactWidget {

    static readonly ID = 'codedna.changes';
    static readonly LABEL = 'Changes';

    @inject(CodeDnaService) protected readonly codedna: CodeDnaService;
    @inject(CodeDnaWorkspace) protected readonly workspace: CodeDnaWorkspace;
    @inject(CodeDnaComparison) protected readonly comparison: CodeDnaComparison;
    @inject(ProgressService) protected readonly progress: ProgressService;

    protected loading = false;
    protected generation = 0;
    protected analysisJob: AnalysisJob | undefined;
    protected timings: AnalysisTimingRecord[] = [];
    protected analysisCancelled = false;
    protected cancelling = false;
    protected notice: string | undefined;
    protected error: string | undefined;
    protected changes: AnalyzeReport | undefined;
    protected impact: ImpactReport | undefined;

    @postConstruct()
    protected init(): void {
        this.id = ChangeViewWidget.ID;
        this.title.label = ChangeViewWidget.LABEL;
        this.title.caption = 'CodeDNA: what changed, and what it might affect';
        this.title.iconClass = 'codicon codicon-git-compare';
        this.title.closable = true;
        this.addClass('codedna-view');
        this.toDispose.push(this.comparison.onDidChange(() => this.invalidate()));
        this.update();
    }

    protected invalidate(): void {
        this.timings = [];
        this.generation++;
        this.analysisCancelled = true;
        this.changes = undefined;
        this.impact = undefined;
        this.error = undefined;
        this.notice = undefined;
        this.update();
    }

    protected async analyze(): Promise<void> {
        if (this.loading) { return; }
        this.invalidate();
        const generation = this.generation, { base, head } = this.comparison;
        this.loading = true;
        this.analysisCancelled = false;
        this.cancelling = false;
        this.analysisJob = undefined;
        this.update();
        const current = (): boolean => generation === this.generation && !this.analysisCancelled && !this.isDisposed;
        const progress = (job: AnalysisJob): void => {
            this.analysisJob = job;
            if (job.metrics) {
                this.timings = [...this.timings.filter(item => item.id !== job.id),
                    { id: job.id, operation: job.operation, metrics: job.metrics }];
            }
            this.update();
        };
        try {
            const repo = await this.workspace.repositoryPath();
            if (!repo) { throw new Error('Open a folder first.'); }
            if (!current()) { return; }
            const supportsJobs = this.codedna.analysisJobs && await this.codedna.analysisJobs();
            if (!current()) { return; }
            const changes = supportsJobs
                ? await waitForAnalysis<AnalyzeReport>(this.codedna, 'analyze', { repo, base, head, level: 'method' }, current, progress)
                : await withProgress(this.progress, 'CodeDNA: analysing the change', () => this.codedna.analyze(repo, base, head));
            if (!current() || !changes) {
                if (generation === this.generation) { this.notice = 'Analysis cancelled. No tests were executed.'; }
                return;
            }
            // Reuse the actual immutable analysis comparison, including a
            // WORKTREE snapshot, rather than capturing later working edits.
            const impact = supportsJobs
                ? await waitForAnalysis<ImpactReport>(this.codedna, 'impact', {
                    repo, base: changes.base_commit, head: changes.head_commit
                }, current, progress)
                : await withProgress(this.progress, 'CodeDNA: checking impact',
                    () => this.codedna.impact(repo, changes.base_commit, changes.head_commit));
            if (!current() || !impact) {
                if (generation === this.generation) { this.notice = 'Analysis cancelled. No tests were executed.'; }
                return;
            }
            this.changes = changes;
            this.impact = impact;
        } catch (error) {
            if (generation === this.generation) {
                this.error = error instanceof Error ? error.message : String(error);
            }
        } finally {
            this.loading = false;
            this.analysisJob = undefined;
            this.cancelling = false;
            this.update();
        }
    }

    protected async cancelAnalysis(): Promise<void> {
        const job = this.analysisJob, generation = this.generation;
        if (!job || this.cancelling || !['queued', 'running'].includes(job.state)) { return; }
        this.cancelling = true;
        this.analysisCancelled = true;
        this.update();
        try {
            const result = await this.codedna.cancelAnalysis(job.id);
            if (generation === this.generation && this.analysisJob?.id === job.id) { this.analysisJob = result; }
        } catch (error) {
            if (generation === this.generation) {
                this.error = `Could not confirm cancellation: ${error instanceof Error ? error.message : String(error)}`;
            }
        } finally {
            if (generation === this.generation) { this.cancelling = false; }
            this.update();
        }
    }

    protected render(): React.ReactNode {
        return <div>
            <header className='cd-header'>
                <h2>Changes</h2>
                <p className='cd-subtitle'>See what changed in your code and what else it might affect.</p>
            </header>
            <form className='cd-controls' data-codedna-tour='changes' onSubmit={e => { e.preventDefault(); this.analyze(); }}>
                <ComparePicker comparison={this.comparison} disabled={this.loading} />
                <button className='cd-button' type='submit' disabled={this.loading} aria-busy={this.loading}>
                    {this.loading ? <><Spinner /> Looking at your changes…</> : 'Show changes'}
                </button>
            </form>
            {this.loading && this.analysisJob && <div className='cd-notice' role='status' aria-live='polite'>
                <span>{this.analysisJob.stage} · {Math.floor(this.analysisJob.elapsed_seconds)} seconds</span>
                {['queued', 'running'].includes(this.analysisJob.state) && <button className='cd-button' type='button'
                    disabled={this.cancelling} onClick={() => this.cancelAnalysis()}>
                    {this.cancelling ? 'Stopping analysis…' : 'Cancel analysis'}
                </button>}
            </div>}
            {this.notice && <p className='cd-notice' role='status'>{this.notice}</p>}
            <AnalysisTimingDetails reports={this.timings} title='Change and impact analysis timing' />
            {this.error && <ErrorNotice message={this.error} />}
            {this.changes ? this.renderResults(this.changes) : !this.loading && !this.error && <FirstRun action='Show changes' />}
        </div>;
    }

    protected async openResultFile(path: string, line?: number): Promise<void> {
        const report = this.changes;
        if (!report) { return; }
        try {
            await this.workspace.openRepositoryFile(report.repository, path, line);
        } catch (error) {
            if (this.changes === report) {
                this.error = `Could not open the working file: ${error instanceof Error ? error.message : String(error)}`;
                this.update();
            }
        }
    }

    protected renderResults(changes: AnalyzeReport): React.ReactNode {
        const declarations = changes.changed_files.flatMap(f => mappingOf(f)?.declarations ?? []);
        const codeChanges = declarations.filter(d => d.code_changed !== false);
        const impacted = this.impact?.impacted ?? [];
        const notes = unique([...changes.warnings, ...(this.impact?.warnings ?? [])]
            .map(friendlyWarning).filter((w): w is string => !!w));
        return <div className='cd-results'>
            <p className='cd-meta'>Compared snapshots {changes.base_commit.slice(0, 12)} and {changes.head_commit.slice(0, 12)}.
                File links open current working files; line numbers may differ.</p>
            <p className='cd-lede'>
                {changes.changed_files.length === 0
                    ? 'No differences between these commits.'
                    : <>{plural(changes.changed_files.length, 'file', 'files')} changed, touching {plural(codeChanges.length, 'part', 'parts')} of
                        your code. {impacted.length === 0
                            ? 'No further impacts were identified.'
                            : <>{plural(impacted.length, 'other class', 'other classes')} might be affected.</>}</>}
            </p>
            {notes.length > 0 && <div className='cd-notice'>
                <strong>Good to know</strong>
                <ul>{notes.map(note => <li key={note}>{note}</li>)}</ul>
            </div>}
            {changes.changed_files.length > 0 && <section aria-label='What changed'>
                <h3>What changed</h3>
                {changes.changed_files.map(file => this.renderFile(file))}
            </section>}
            {impacted.length > 0 && <section aria-label='Might be affected'>
                <h3>Might be affected</h3>
                <div className='cd-card'>{impacted.map(node => this.renderImpacted(node))}</div>
            </section>}
        </div>;
    }

    protected renderFile(file: ChangedFile): React.ReactNode {
        const status = fileStatusLabel(file.status);
        const mapping = mappingOf(file);
        const declarations = mapping?.declarations ?? [];
        const folder = file.path.includes('/') ? file.path.slice(0, file.path.lastIndexOf('/')) : '';
        return <div className='cd-card' key={file.path}>
            <div className='cd-card-header'>
                <span className='cd-file-name'>{breakable(file.path.split('/').slice(-1)[0])}</span>
                <span className='cd-row-meta'>
                    <Chip tone={status.tone}>{status.text}</Chip>
                    {(folder || file.old_path) && <span className='cd-meta'>
                        {breakable([folder, file.old_path && `was ${file.old_path}`].filter(Boolean).join(' · '))}
                    </span>}
                </span>
            </div>
            {!file.language && <p className='cd-row-note'>No installed language plugin reads this file, so CodeDNA doesn’t look inside it.</p>}
            {declarations.map(d => this.renderDeclaration(file, d))}
            {mapping?.outside_declarations.some(o => o.code_changed !== false) &&
                <p className='cd-row-note'>{file.language === 'python'
                    ? 'Imports or other module-level code changed too.'
                    : 'Imports or the package line changed too.'}</p>}
            {mapping?.unresolved.length ? <p className='cd-row-note cd-modified'>
                Some lines couldn’t be matched to {file.language === 'python' ? 'functions' : 'methods'} ({mapping.unresolved[0].reason}).</p> : undefined}
        </div>;
    }

    protected renderDeclaration(file: ChangedFile, d: DeclarationChange): React.ReactNode {
        const line = d.head_lines?.[0] ?? d.base_lines?.[0];
        const label = changeLabel(d.change, d.code_changed === false);
        const removed = d.change === 'deleted';
        return <button className='cd-row' key={d.id} disabled={removed}
            title={removed ? `${d.id} (removed)` : `Open working file at line ${line} · ${d.id}`}
            onClick={() => this.openResultFile(file.path, line)}>
            <span className='cd-code'>{breakable(readableName(d.id))}</span>
            <span className='cd-row-meta'>
                <Chip tone={label.tone}>{label.text}</Chip>
                <span className='cd-meta'>{kindLabel(d.kind)}{line && !removed ? ` · line ${line}` : ''}</span>
            </span>
        </button>;
    }

    protected renderImpacted(node: ImpactedNode): React.ReactNode {
        const confidence = confidenceLabel(node.confidence);
        const first = node.path[0];
        const why = !first
            ? 'Connected to the change.'
            : node.path.length === 1
                ? `Uses ${simpleName(first.depends_on)}, which changed.`
                : `Uses ${simpleName(first.depends_on)}, which depends on ${simpleName(node.seed)}, which changed.`;
        return <button className='cd-row' key={node.node} title={`${node.node.replace('type:', '')} · ${confidence.hint}`}
            onClick={() => node.file && this.openResultFile(node.file)}>
            <span className='cd-code'>{simpleName(node.node)}{node.role === 'test' ? <span className='cd-meta'> · test</span> : ''}</span>
            <span className='cd-row-meta'>
                <Chip tone={confidence.tone} title={confidence.hint}>{confidence.text}</Chip>
                <span className='cd-meta'>{why}</span>
            </span>
        </button>;
    }
}

function unique(values: string[]): string[] {
    return [...new Set(values)];
}

/** The declaration mapping of a changed file, whichever language plugin made it. */
export function mappingOf(file: ChangedFile): JavaFileAnalysis | null {
    return file.java ?? file.analysis ?? null;
}
