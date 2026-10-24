import * as React from '@theia/core/shared/react';
import { inject, injectable, postConstruct } from '@theia/core/shared/inversify';
import { ReactWidget } from '@theia/core/lib/browser/widgets/react-widget';
import cytoscape from 'cytoscape';
import { CodeDnaService, ExplanationGraph } from '../common/codedna-protocol';
import { CodeDnaComparison } from './comparison';
import { CodeDnaWorkspace } from './codedna-workspace';
import { confidenceLabel, friendlyWarning, readableName } from './plain-language';
import { Chip, ComparePicker, ErrorNotice, FirstRun, Spinner } from './ui';

type GraphNode = ExplanationGraph['nodes'][number];

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

    protected loading = false;
    protected error: string | undefined;
    protected graph: ExplanationGraph | undefined;
    protected warnings: string[] = [];
    protected selected: GraphNode | undefined;
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
            const impact = await this.codedna.impact(repo, base, head);
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
    }

    protected draw(): void {
        if (!this.graph || !this.canvas || this.cy) {
            return;
        }
        const style = getComputedStyle(this.node);
        const color = (name: string) => style.getPropertyValue(name).trim() || '#888';
        this.cy = cytoscape({
            container: this.canvas,
            elements: [
                ...this.graph.nodes.map(n => ({ data: {
                    id: n.id, label: nodeLabel(n.id),
                    color: color(CATEGORY[n.category].color), category: n.category } })),
                // Core edges read "dependent depends on target"; draw them the way the change travels.
                ...this.graph.edges.map(e => ({ data: {
                    id: e.id, source: e.target, target: e.source, confidence: e.confidence } }))
            ],
            layout: { name: 'breadthfirst', directed: true, spacingFactor: 1.1,
                roots: this.graph.nodes.filter(n => n.changed).map(n => n.id) },
            wheelSensitivity: 0.3,
            style: [
                { selector: 'node', style: {
                    'background-color': 'data(color)', label: 'data(label)', color: color('--cd-text'),
                    'font-size': 11, 'text-valign': 'bottom', 'text-margin-y': 4, width: 18, height: 18 } },
                { selector: 'node[category = "unanalysed"]', style: {
                    'border-width': 2, 'border-style': 'dashed', 'border-color': color('--cd-deleted'),
                    'background-opacity': 0.2 } },
                { selector: 'edge', style: {
                    width: 1.5, 'line-color': color('--cd-muted'), 'target-arrow-color': color('--cd-muted'),
                    'target-arrow-shape': 'triangle', 'curve-style': 'bezier' } },
                { selector: 'edge[confidence = "heuristic"]', style: { 'line-style': 'dashed' } },
                { selector: '.cd-faded', style: { opacity: 0.25 } },
                { selector: '.cd-path', style: { 'line-color': color('--cd-modified'),
                    'target-arrow-color': color('--cd-modified'), width: 3 } }
            ]
        });
        this.cy.on('tap', 'node', event => this.select(event.target.id()));
        this.cy.on('tap', event => { if (event.target === this.cy) { this.select(undefined); } });
    }

    protected select(id: string | undefined): void {
        const cy = this.cy;
        this.selected = this.graph?.nodes.find(n => n.id === id);
        if (cy) {
            cy.elements().removeClass('cd-faded cd-path');
            if (this.selected) {
                const path = cy.collection();
                for (const edgeId of this.selected.path_edges) {
                    const edge = cy.getElementById(edgeId);
                    path.merge(edge).merge(edge.connectedNodes());
                }
                path.merge(cy.getElementById(this.selected.id));
                cy.elements().not(path).addClass('cd-faded');
                path.edges().addClass('cd-path');
            }
        }
        this.update();
    }

    protected render(): React.ReactNode {
        const graph = this.graph;
        return <div className='cd-graph-layout'>
            <header className='cd-header'>
                <h2>Impact graph</h2>
                <p className='cd-subtitle'>Follow your change to the code and tests it may affect. Click a dot to see why.</p>
            </header>
            <form className='cd-controls' onSubmit={e => { e.preventDefault(); this.load(); }}>
                <ComparePicker comparison={this.comparison} disabled={this.loading} />
                <button className='cd-button' type='submit' disabled={this.loading} aria-busy={this.loading}>
                    {this.loading ? <><Spinner /> Building graph…</> : 'Show graph'}
                </button>
            </form>
            {this.error && <ErrorNotice message={this.error} />}
            {!graph && !this.loading && !this.error && <FirstRun action='Show graph' />}
            {graph && graph.nodes.length === 0 && <p className='cd-lede'>No code changes to show between these commits.</p>}
            {graph && graph.nodes.length > 0 && <>
                <ul className='cd-legend' aria-label='Legend'>
                    {Object.entries(CATEGORY).map(([key, c]) =>
                        <li key={key}><span className={`cd-dot cd-dot-${key}`} />{c.label}</li>)}
                    <li><span className='cd-line-solid' />Direct link</li>
                    <li><span className='cd-line-dashed' />Likely link</li>
                </ul>
                <div className='cd-graph-canvas' ref={el => { this.canvas = el; }}
                    role='img' aria-label={`Impact graph with ${graph.nodes.length} parts`} />
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
                    <span className='cd-code'>{readableName(step.source)}</span> uses <span className='cd-code'>{readableName(step.target)}</span>
                    {' '}({step.kind}, {confidenceLabel(step.confidence).text.toLowerCase()}, <span className='cd-meta'>{step.evidence}</span>)
                </li>)}
            </ol>}
            {node.file && <button className='cd-button' onClick={() => this.workspace.openFile(node.file!)}>Open file</button>}
        </section>;
    }
}

/** Type ids read as class names; unanalysed files keep their path (`file:pom.xml` → `pom.xml`). */
function nodeLabel(id: string): string {
    return id.startsWith('file:') ? id.slice('file:'.length) : readableName(id);
}
