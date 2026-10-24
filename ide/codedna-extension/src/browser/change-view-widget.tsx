import * as React from '@theia/core/shared/react';
import { inject, injectable, postConstruct } from '@theia/core/shared/inversify';
import { ProgressService } from '@theia/core/lib/common/progress-service';
import { ReactWidget } from '@theia/core/lib/browser/widgets/react-widget';
import {
    AnalyzeReport, ChangedFile, CodeDnaService, DeclarationChange, ImpactReport, ImpactedNode
} from '../common/codedna-protocol';
import { CodeDnaComparison } from './comparison';
import { CodeDnaWorkspace } from './codedna-workspace';
import { withProgress } from './progress';
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
        this.toDispose.push(this.comparison.onDidChange(() => this.update()));
        this.update();
    }

    protected async analyze(): Promise<void> {
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
            const { base, head } = this.comparison;
            const [changes, impact] = await withProgress(this.progress, 'CodeDNA: analysing the change', () => Promise.all([
                this.codedna.analyze(repo, base, head),
                this.codedna.impact(repo, base, head)
            ]));
            this.changes = changes;
            this.impact = impact;
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
                <h2>Changes</h2>
                <p className='cd-subtitle'>See what changed in your code and what else it might affect.</p>
            </header>
            <form className='cd-controls' onSubmit={e => { e.preventDefault(); this.analyze(); }}>
                <ComparePicker comparison={this.comparison} disabled={this.loading} />
                <button className='cd-button' type='submit' disabled={this.loading} aria-busy={this.loading}>
                    {this.loading ? <><Spinner /> Looking at your changes…</> : 'Show changes'}
                </button>
            </form>
            {this.error && <ErrorNotice message={this.error} />}
            {this.changes ? this.renderResults(this.changes) : !this.loading && !this.error && <FirstRun action='Show changes' />}
        </div>;
    }

    protected renderResults(changes: AnalyzeReport): React.ReactNode {
        const declarations = changes.changed_files.flatMap(f => f.java?.declarations ?? []);
        const codeChanges = declarations.filter(d => d.code_changed !== false);
        const impacted = this.impact?.impacted ?? [];
        const notes = unique([...changes.warnings, ...(this.impact?.warnings ?? [])]
            .map(friendlyWarning).filter((w): w is string => !!w));
        return <div className='cd-results'>
            <p className='cd-lede'>
                {changes.changed_files.length === 0
                    ? 'No differences between these commits.'
                    : <>{plural(changes.changed_files.length, 'file', 'files')} changed, touching {plural(codeChanges.length, 'part', 'parts')} of
                        your code. {impacted.length === 0
                            ? 'Nothing else depends on it.'
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
        const declarations = file.java?.declarations ?? [];
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
            {!file.is_java && <p className='cd-row-note'>Not Java code, so CodeDNA doesn’t look inside it.</p>}
            {declarations.map(d => this.renderDeclaration(file, d))}
            {file.java?.outside_declarations.some(o => o.code_changed !== false) &&
                <p className='cd-row-note'>Imports or the package line changed too.</p>}
            {file.java?.unresolved.length ? <p className='cd-row-note cd-modified'>
                Some lines couldn’t be matched to methods ({file.java.unresolved[0].reason}).</p> : undefined}
        </div>;
    }

    protected renderDeclaration(file: ChangedFile, d: DeclarationChange): React.ReactNode {
        const line = d.head_lines?.[0] ?? d.base_lines?.[0];
        const label = changeLabel(d.change, d.code_changed === false);
        const removed = d.change === 'deleted';
        return <button className='cd-row' key={d.id} disabled={removed}
            title={removed ? `${d.id} (removed)` : `Open at line ${line} · ${d.id}`}
            onClick={() => this.workspace.openFile(file.path, line)}>
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
            onClick={() => node.file && this.workspace.openFile(node.file)}>
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
