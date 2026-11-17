import { WorkflowNav } from './ui';
import * as React from '@theia/core/shared/react';
import { inject, injectable, postConstruct } from '@theia/core/shared/inversify';
import { ProgressService } from '@theia/core/lib/common/progress-service';
import { ReactWidget } from '@theia/core/lib/browser/widgets/react-widget';
import cytoscape from 'cytoscape';
import { CodeDnaService, ExplanationGraph, ImpactOptions } from '../common/codedna-protocol';
import { CodeDnaComparison } from './comparison';
import { CodeDnaWorkspace } from './codedna-workspace';
import { lanePositions } from './graph-layout';
import { withProgress } from './progress';
import { confidenceLabel, friendlyWarning, readableName } from './plain-language';
import { Chip, ComparePicker, ErrorNotice, FirstRun, Spinner } from './ui';

type GraphNode = ExplanationGraph['nodes'][number];

/** Depth choices offered for the traversal; undefined = follow every link. */
const DEPTHS: { label: string; value: number | undefined }[] = [
    { label: 'All links', value: undefined },
    { label: '1 link away', value: 1 },
    { label: '2 links away', value: 2 },
    { label: '3 links away', value: 3 }
];

const CATEGORY: Record<GraphNode['category'], { label: string; color: string }> = {
    changed: { label: 'Changed', color: '--cd-modified' },
    impacted: { label: 'May be affected', color: '--cd-muted' },
    test: { label: 'Related test', color: '--cd-added' },
    unanalysed: { label: 'Not analysed', color: '--cd-deleted' }
};

/**
 * "Impact graph": changed code → parts that may be affected → related tests.
 * The core builds the graph (explanation paths, edge confidence); this view
 * only draws it. Arrows point from a changed part to what may feel the change.
 */
@injectable()
export class GraphViewWidget extends ReactWidget {

    static readonly ID = 'codedna.graph';
    static readonly LABEL = 'Impact graph';

    @inject(CodeDnaService) protected readonly codedna: CodeDnaService;
    @inject(CodeDnaWorkspace) protected readonly workspace: CodeDnaWorkspace;
    @inject(CodeDnaComparison) protected readonly comparison: CodeDnaComparison;
    @inject(ProgressService) protected readonly progress: ProgressService;

    protected loading = false;
    protected error: string | undefined;
    protected graph: ExplanationGraph | undefined;
    protected warnings: string[] = [];
    protected selected: GraphNode | undefined;
    protected options: ImpactOptions = {};
    protected cy: cytoscape.Core | undefined;
    protected canvas: HTMLDivElement | null = null;

    @postConstruct()
    protected init(): void {
        this.id = GraphViewWidget.ID;
        this.title.label = GraphViewWidget.LABEL;
        this.title.caption = 'CodeDNA: how your change reaches other code and tests';
        this.title.iconClass = 'codicon codicon-type-hierarchy';
        this.title.closable = true;
        this.addClass('codedna-view');
        this.addClass('cd-graph-view');
        this.toDispose.push(this.comparison.onDidChange(() => { this.clear(); this.update(); }));
        this.toDispose.push({ dispose: () => this.cy?.destroy() });
        this.update();
    }

    protected clear(): void {
        this.cy?.destroy();
        this.cy = undefined;
        this.graph = undefined;
        this.selected = undefined;
    }

    protected async load(): Promise<void> {
        const repo = await this.workspace.repositoryPath();
        if (!repo) {
            this.error = 'Open a folder first.';
            this.update();
            return;
        }
        this.loading = true;
        this.error = undefined;
        this.clear();
        this.update();
        try {
            const { base, head } = this.comparison;
            const options = { ...this.options };
            const impact = await withProgress(this.progress, 'CodeDNA: building the impact graph',
                () => this.codedna.impact(repo, base, head, options));
            if (base !== this.comparison.base || head !== this.comparison.head) {
                this.error = 'The comparison changed. Show the graph again.';
                return;
            }
            this.graph = impact.explanation_graph;
            this.warnings = impact.warnings.map(friendlyWarning).filter((w): w is string => !!w);
        } catch (error) {
            this.error = error instanceof Error ? error.message : String(error);
        } finally {
            this.loading = false;
            this.update();
        }
    }

    protected override onUpdateRequest(msg: Parameters<ReactWidget['onUpdateRequest']>[0]): void {
        super.onUpdateRequest(msg);
        // React renders asynchronously; draw once the canvas element exists.
        requestAnimationFrame(() => this.draw());
    }

    protected override onResize(msg: Parameters<ReactWidget['onResize']>[0]): void {
        super.onResize(msg);
        this.cy?.resize();
        this.update();  // draws a graph that arrived while the view was hidden
    }

    protected override onAfterShow(msg: Parameters<ReactWidget['onAfterShow']>[0]): void {
        super.onAfterShow(msg);
        this.update();
    }

    protected draw(): void {
        // A hidden view has no size; a layout computed then would stack every node.
        if (!this.graph || !this.canvas || this.cy || !this.canvas.clientWidth) {
            return;
        }
        const style = getComputedStyle(this.node);
        const color = (name: string) => style.getPropertyValue(name).trim() || '#888';
        // One box per package once the change spans several; a single box adds nothing.
        const grouped = this.graph.packages.length > 1;
        const layout = lanePositions(this.graph);
        // Grow the canvas with the graph (within limits) so labels stay readable; scroll/zoom for more.
        this.canvas.style.height = `${Math.min(760, Math.max(360, layout.height * 0.75 + 80))}px`;
        this.cy = cytoscape({
            container: this.canvas,
            elements: [
                ...(grouped ? this.graph.packages.map(g => ({ data: {
                    id: g.id, label: g.label, kind: 'package', changed: g.changed } })) : []),
                ...this.graph.nodes.map(n => ({ data: {
                    id: n.id, label: nodeLabel(n.id),
                    color: color(CATEGORY[n.category].color), category: n.category, changed: n.changed,
                    ...(grouped && n.package !== null ? { parent: `package:${n.package}` } : {}) } })),
                // Core edges read "dependent depends on target"; draw them the way the change travels.
                ...this.graph.edges.map(e => ({ data: {
                    id: e.id, source: e.target, target: e.source, confidence: e.confidence } }))
            ],
            // Lanes: one band per package, columns by links from the change (graph-layout.ts).
            layout: { name: 'preset', positions: layout.positions, fit: true, padding: 24 },
            style: [
                { selector: 'node', style: {
                    'background-color': 'data(color)', label: 'data(label)', color: color('--cd-text'),
                    'font-size': 11, 'text-valign': 'center', 'text-halign': 'right', 'text-margin-x': 6,
                    // Labels sit on the canvas colour so edges passing behind them stay readable.
                    'text-background-color': color('--cd-bg'), 'text-background-opacity': 0.85,
                    'text-background-padding': '2px', width: 14, height: 14 } },
                // The change itself stands out: larger, outlined, bold label.
                { selector: 'node[?changed][category != "unanalysed"]', style: {
                    width: 22, height: 22, 'border-width': 3, 'border-color': color('--cd-text'),
                    'font-weight': 'bold', 'font-size': 12 } },
                { selector: 'node[kind = "package"]', style: {
                    'background-color': color('--cd-muted'), 'background-opacity': 0.06,
                    'border-width': 1, 'border-color': color('--cd-line'), shape: 'round-rectangle',
                    label: 'data(label)', 'text-valign': 'top', 'text-halign': 'center',
                    'text-background-opacity': 0, 'font-size': 11, color: color('--cd-muted'),
                    // Compound padding is valid Cytoscape style but missing from @types/cytoscape 3.21.
                    padding: '14px' } as cytoscape.Css.Node },
                { selector: 'node[kind = "package"][?changed]', style: {
                    'border-color': color('--cd-modified'), 'border-width': 2 } },
                { selector: 'node[category = "unanalysed"]', style: {
                    'border-width': 2, 'border-style': 'dashed', 'border-color': color('--cd-deleted'),
                    'background-opacity': 0.2 } },
                { selector: 'edge', style: {
                    width: 1.5, 'line-color': color('--cd-muted'), 'target-arrow-color': color('--cd-muted'),
                    'target-arrow-shape': 'triangle', 'curve-style': 'bezier' } },
                { selector: 'edge[confidence = "heuristic"]', style: { 'line-style': 'dashed' } },
                { selector: '.cd-faded', style: { opacity: 0.25 } },
                { selector: '.cd-path', style: { 'line-color': color('--cd-modified'),
                    'target-arrow-color': color('--cd-modified'), width: 3 } },
                { selector: 'node.cd-selected', style: {
                    'border-width': 3, 'border-style': 'solid', 'border-color': color('--cd-text') } }
            ]
        });
        this.cy.on('tap', 'node', event => this.select(event.target.id()));
        this.cy.on('tap', event => { if (event.target === this.cy) { this.select(undefined); } });
    }

    protected select(id: string | undefined): void {
        const cy = this.cy;
        this.selected = this.graph?.nodes.find(n => n.id === id);
        if (cy) {
            cy.elements().removeClass('cd-faded cd-path cd-selected');
            if (this.selected) {
                const path = cy.collection();
                for (const edgeId of this.selected.path_edges) {
                    const edge = cy.getElementById(edgeId);
                    path.merge(edge).merge(edge.connectedNodes());
                }
                path.merge(cy.getElementById(this.selected.id));
                // Package boxes stay visible: fading a box would fade everything inside it.
                cy.elements().not(path).not('node[kind = "package"]').addClass('cd-faded');
                path.edges().addClass('cd-path');
                cy.getElementById(this.selected.id).addClass('cd-selected');
            }
        }
        this.update();
    }

    protected async open(file: string): Promise<void> {
        try {
            await this.workspace.openFile(file);
        } catch {
            this.error = `Could not open ${file}. It may have been deleted or moved by this change.`;
            this.update();
        }
    }

    protected render(): React.ReactNode {
        const graph = this.graph;
        return <div className='cd-graph-layout'>
            <WorkflowNav workspace={this.workspace} current='graph' />
            <header className='cd-header'>
                <h2>Impact graph</h2>
                <p className='cd-subtitle'>Follow your change to the code and tests it may affect. Click a dot to see why.</p>
            </header>
            <form className='cd-controls' onSubmit={e => { e.preventDefault(); this.load(); }}>
                <ComparePicker comparison={this.comparison} disabled={this.loading} />
                <label className='cd-field'>
                    <span className='cd-field-label'>Follow</span>
                    <select value={String(this.options.maxDepth ?? '')} disabled={this.loading}
                        onChange={e => { this.options = { ...this.options, maxDepth: e.currentTarget.value ? Number(e.currentTarget.value) : undefined }; this.update(); }}>
                        {DEPTHS.map(d => <option key={d.label} value={d.value ?? ''}>{d.label}</option>)}
                    </select>
                </label>
                <label className='cd-check'>
                    <input type='checkbox' checked={!!this.options.confirmedOnly} disabled={this.loading}
                        onChange={e => { this.options = { ...this.options, confirmedOnly: e.currentTarget.checked }; this.update(); }} />
                    Confirmed links only
                </label>
                <button className='cd-button' type='submit' disabled={this.loading} aria-busy={this.loading}>
                    {this.loading ? <><Spinner /> Building graph…</> : 'Show graph'}
                </button>
            </form>
            {this.error && <ErrorNotice message={this.error} />}
            {!graph && !this.loading && !this.error && <FirstRun action='Show graph' />}
            {graph && graph.nodes.length === 0 && <p className='cd-lede'>No code changes to show between these commits.</p>}
            {graph && graph.nodes.length > 0 && <>
                <p className='cd-help' aria-live='polite'>{summaryText(graph)}</p>
                <ul className='cd-legend' aria-label='Legend'>
                    {Object.entries(CATEGORY).map(([key, c]) =>
                        <li key={key}><span className={`cd-dot cd-dot-${key}`} />{c.label}</li>)}
                    <li><span className='cd-line-solid' />Direct link</li>
                    <li><span className='cd-line-dashed' />Likely link</li>
                    {graph.packages.length > 1 && <li><span className='cd-box' />Package</li>}
                </ul>
                <div className='cd-graph-canvas' ref={el => { this.canvas = el; }}
                    role='img' aria-label={`Impact graph with ${graph.nodes.length} parts. Use the list below to explain a part.`} />
                <label className='cd-field cd-graph-pick'>
                    <span className='cd-field-label'>Explain a part</span>
                    <select value={this.selected?.id ?? ''} onChange={e => this.select(e.currentTarget.value || undefined)}>
                        <option value=''>Choose…</option>
                        {graph.nodes.map(n => <option key={n.id} value={n.id}>
                            {nodeLabel(n.id)} ({CATEGORY[n.category].label.toLowerCase()})
                        </option>)}
                    </select>
                </label>
                {this.selected ? this.renderDetails(this.selected, graph) : <p className='cd-help'>Click a dot to see its explanation path.</p>}
                {this.warnings.length > 0 && <div className='cd-notice'>
                    <strong>Good to know</strong>
                    <ul>{this.warnings.map(w => <li key={w}>{w}</li>)}</ul>
                </div>}
            </>}
        </div>;
    }

    protected renderDetails(node: GraphNode, graph: ExplanationGraph): React.ReactNode {
        const edges = new Map(graph.edges.map(e => [e.id, e]));
        const steps = node.path_edges.map(id => edges.get(id)).filter((e): e is ExplanationGraph['edges'][number] => !!e);
        const confidence = node.confidence === 'unresolved' ? undefined : confidenceLabel(node.confidence);
        return <section className='cd-card cd-graph-details' aria-label='Explanation path'>
            <div className='cd-row cd-static'>
                <span className='cd-code'>{nodeLabel(node.id)}</span>
                <span className='cd-row-meta'>
                    <Chip tone={node.category === 'test' ? 'added' : node.changed ? 'modified' : 'muted'}>{CATEGORY[node.category].label}</Chip>
                    {confidence ? <Chip tone={confidence.tone} title={confidence.hint}>{confidence.text}</Chip>
                        : <Chip tone='deleted' title='CodeDNA cannot analyse this file, so its effect is unknown.'>Unknown</Chip>}
                </span>
            </div>
            {node.reasons.length > 0 && <ul className='cd-reasons'>{node.reasons.map(r => <li key={r}>{r}</li>)}</ul>}
            {steps.length > 0 && <ol className='cd-path-steps'>
                {[...steps].reverse().map(step => <li key={step.id}>
                    <span className='cd-code'>{readableName(step.source)}</span> depends on <span className='cd-code'>{readableName(step.target)}</span>
                    {' '}({step.kind}, {confidenceLabel(step.confidence).text.toLowerCase()}, <span className='cd-meta'>{step.evidence}</span>)
                </li>)}
            </ol>}
            {node.file && <button className='cd-button' onClick={() => this.open(node.file!)}>Open file</button>}
        </section>;
    }
}

/** Type ids read as class names; unanalysed files keep their path (`file:pom.xml` → `pom.xml`). */
function nodeLabel(id: string): string {
    return id.startsWith('file:') ? id.slice('file:'.length) : readableName(id);
}

function summaryText(graph: ExplanationGraph): string {
    const { changed, impacted, test, unanalysed } = graph.summary;
    const parts = [`${changed} changed`, `${impacted} may be affected`, `${test} related test${test === 1 ? '' : 's'}`];
    if (unanalysed) {
        parts.push(`${unanalysed} not analysed`);
    }
    const packages = graph.packages.length;
    return parts.join(' · ') + (packages > 1 ? `, across ${packages} packages` : '');
}
