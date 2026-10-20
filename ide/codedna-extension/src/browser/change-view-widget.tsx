import * as React from '@theia/core/shared/react';
import { inject, injectable, postConstruct } from '@theia/core/shared/inversify';
import { ReactWidget } from '@theia/core/lib/browser/widgets/react-widget';
import {
    AnalyzeReport, ChangedFile, CodeDnaService, DeclarationChange, ImpactReport, ImpactedNode
} from '../common/codedna-protocol';
import { CodeDnaWorkspace } from './codedna-workspace';

/**
 * "Changed code": which classes and methods changed between two commits, and
 * which classes may be affected — each with the dependency path that explains
 * why. Heuristic links are always marked as heuristic.
 */
@injectable()
export class ChangeViewWidget extends ReactWidget {

    static readonly ID = 'codedna.changes';
    static readonly LABEL = 'Changed code';

    @inject(CodeDnaService) protected readonly codedna: CodeDnaService;
    @inject(CodeDnaWorkspace) protected readonly workspace: CodeDnaWorkspace;

    protected base = 'HEAD~1';
    protected head = 'HEAD';
    protected loading = false;
    protected error: string | undefined;
    protected changes: AnalyzeReport | undefined;
    protected impact: ImpactReport | undefined;

    @postConstruct()
    protected init(): void {
        this.id = ChangeViewWidget.ID;
        this.title.label = ChangeViewWidget.LABEL;
        this.title.caption = 'CodeDNA: changed classes and methods, and what they may affect';
        this.title.iconClass = 'codicon codicon-git-compare';
        this.title.closable = true;
        this.addClass('codedna-view');
        this.update();
    }

    protected async analyze(): Promise<void> {
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
            const [changes, impact] = await Promise.all([
                this.codedna.analyze(repo, this.base, this.head),
                this.codedna.impact(repo, this.base, this.head)
            ]);
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
            <h2>Changed code</h2>
            <p className='cd-subtitle'>Compare two commits to see what changed and what it may affect.</p>
            <form className='cd-controls' onSubmit={e => { e.preventDefault(); this.analyze(); }}>
                <label className='cd-field'>Base
                    <input value={this.base} spellCheck={false} aria-label='Base commit'
                        onChange={e => { this.base = e.target.value; this.update(); }} />
                </label>
                <label className='cd-field'>Head
                    <input value={this.head} spellCheck={false} aria-label='Head commit'
                        onChange={e => { this.head = e.target.value; this.update(); }} />
                </label>
                <button className='cd-button' type='submit' disabled={this.loading}>
                    {this.loading ? 'Analysing…' : 'Analyse'}
                </button>
            </form>
            {this.loading && <div className='cd-progress' role='progressbar' aria-label='Analysing' />}
            {this.error && <div className='cd-notice cd-error' role='alert'>{this.error}</div>}
            {this.changes ? this.renderResults(this.changes) :
                !this.loading && !this.error && <p className='cd-empty'>Commits only for now — uncommitted edits are not analysed yet.</p>}
        </div>;
    }

    protected renderResults(changes: AnalyzeReport): React.ReactNode {
        const java = changes.changed_files.filter(f => f.is_java);
        const declarations = java.flatMap(f => f.java?.declarations ?? []);
        const codeChanges = declarations.filter(d => d.code_changed !== false);
        const impacted = this.impact?.impacted ?? [];
        const warnings = [...changes.warnings, ...(this.impact?.warnings ?? [])];
        return <>
            <div className='cd-summary'>
                {stat(changes.changed_files.length, 'files changed')}
                {stat(codeChanges.length, 'declarations changed')}
                {stat(impacted.length, 'classes may be affected')}
            </div>
            {warnings.length > 0 && <div className='cd-notice cd-warning'>
                <strong>Check these</strong>
                <ul>{unique(warnings).map(w => <li key={w}>{w}</li>)}</ul>
            </div>}
            <section aria-label='Changed files'>
                <h3>Changed files</h3>
                {changes.changed_files.length === 0 && <p className='cd-empty'>No differences between these commits.</p>}
                {changes.changed_files.map(file => this.renderFile(file))}
            </section>
            <section aria-label='May be affected'>
                <h3>May be affected</h3>
                {impacted.length === 0
                    ? <p className='cd-empty'>Nothing else depends on the changed classes.</p>
                    : impacted.map(node => this.renderImpacted(node))}
            </section>
        </>;
    }

    protected renderFile(file: ChangedFile): React.ReactNode {
        const declarations = file.java?.declarations ?? [];
        return <div className='cd-file' key={file.path}>
            <div className='cd-file-header'>
                <span className={`cd-badge cd-${file.status}`}>{file.status}</span>
                <span className='cd-file-name'>{baseName(file.path)}</span>
                {(folder(file.path) || file.old_path) && <span className='cd-meta'>
                    {[folder(file.path), file.old_path && `from ${file.old_path}`].filter(Boolean).join(' · ')}
                </span>}
            </div>
            {!file.is_java && <div className='cd-row cd-static'>
                <span className='cd-badge cd-muted'>skipped</span>
                <span className='cd-muted'>Not Java — not analysed</span>
            </div>}
            {declarations.map(d => this.renderDeclaration(file, d))}
            {file.java?.outside_declarations.filter(o => o.code_changed !== false).map((o, i) =>
                <div className='cd-row cd-static' key={`outside-${i}`}>
                    <span className='cd-badge cd-modified'>file</span>
                    <span className='cd-id'>{o.parts.join(', ')}</span>
                    <span className='cd-meta'>outside classes</span>
                </div>)}
            {file.java?.unresolved.map((u, i) =>
                <div className='cd-row cd-static' key={`unresolved-${i}`}>
                    <span className='cd-badge cd-heuristic'>unresolved</span>
                    <span>{u.reason}</span>
                </div>)}
        </div>;
    }

    protected renderDeclaration(file: ChangedFile, d: DeclarationChange): React.ReactNode {
        const line = d.head_lines?.[0] ?? d.base_lines?.[0];
        const commentOnly = d.code_changed === false;
        return <button className='cd-row' key={d.id} title={`Open ${file.path}`}
            disabled={d.change === 'deleted'}
            onClick={() => this.workspace.openFile(file.path, line)}>
            <span className={`cd-badge cd-${commentOnly ? 'muted' : d.change}`}>{commentOnly ? 'comment' : d.change}</span>
            <span className='cd-id'>{shortId(d.id)}</span>
            <span className='cd-meta'>{d.kind}{line ? ` · line ${line}` : ''}</span>
        </button>;
    }

    protected renderImpacted(node: ImpactedNode): React.ReactNode {
        const why = node.path.map(step =>
            `${shortId(step.dependent.replace('type:', ''))} ${step.kind} ${shortId(step.depends_on.replace('type:', ''))}` +
            `${step.confidence === 'heuristic' ? ' (heuristic)' : ''}`).join(' → ');
        return <div key={node.node}>
            <button className='cd-row' title={why} onClick={() => node.file && this.workspace.openFile(node.file)}>
                <span className={`cd-badge cd-${node.confidence}`}>{node.confidence}</span>
                <span className='cd-id'>{node.node.replace('type:', '')}</span>
                <span className='cd-meta'>{node.role === 'test' ? 'test · ' : ''}{node.distance} hop{node.distance === 1 ? '' : 's'}</span>
            </button>
            <ul className='cd-reasons'><li>{why}</li></ul>
        </div>;
    }
}

function stat(value: number, label: string): React.ReactNode {
    return <div className='cd-stat' key={label}>
        <span className='cd-stat-value'>{value}</span>
        <span className='cd-stat-label'>{label}</span>
    </div>;
}

function shortId(id: string): string {
    const [type, member] = id.split('#');
    const simple = type.split('.').slice(-1)[0];
    return member ? `${simple}#${member}` : simple;
}

function baseName(path: string): string {
    return path.split('/').slice(-1)[0];
}

function folder(path: string): string {
    return path.includes('/') ? path.slice(0, path.lastIndexOf('/')) : '';
}

function unique(values: string[]): string[] {
    return [...new Set(values)];
}
