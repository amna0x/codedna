import { ExplanationGraph } from '../common/codedna-protocol';

type GraphNode = ExplanationGraph['nodes'][number];

/** Column width and row height of the lane layout, in graph units. */
export const LANE_COLUMN = 260;
export const LANE_ROW = 44;
const LANE_GAP = 40;
const ORDER: Record<GraphNode['category'], number> = { changed: 0, impacted: 1, test: 2, unanalysed: 3 };

/**
 * Positions for a "swimlane" drawing: one horizontal band per package, and
 * columns by the core's `distance` (links from the change), so the change sits
 * on the left and its effects spread to the right. Bands with changed code come
 * first. Pure placement of the core's data; nothing is analysed here.
 */
export function lanePositions(graph: ExplanationGraph): { positions: Record<string, { x: number; y: number }>; height: number } {
    const bands = new Map<string, GraphNode[]>();
    for (const node of graph.nodes) {
        // Files outside the graph (non-Java changes) share one band at the end.
        const key = node.package === null ? '\u0000' : node.package;
        bands.set(key, [...(bands.get(key) ?? []), node]);
    }
    const changed = (key: string) => bands.get(key)!.some(n => n.changed);
    const keys = [...bands.keys()].sort((a, b) =>
        (a === '\u0000' ? 1 : 0) - (b === '\u0000' ? 1 : 0)
        || Number(changed(b)) - Number(changed(a))
        || a.localeCompare(b));
    const positions: Record<string, { x: number; y: number }> = {};
    let top = 0;
    for (const key of keys) {
        const columns = new Map<number, GraphNode[]>();
        for (const node of bands.get(key)!) {
            const column = node.distance ?? 0;
            columns.set(column, [...(columns.get(column) ?? []), node]);
        }
        let rows = 0;
        for (const [column, nodes] of columns) {
            nodes.sort((a, b) => ORDER[a.category] - ORDER[b.category] || a.id.localeCompare(b.id));
            nodes.forEach((node, row) => { positions[node.id] = { x: column * LANE_COLUMN, y: top + row * LANE_ROW }; });
            rows = Math.max(rows, nodes.length);
        }
        top += rows * LANE_ROW + LANE_GAP;
    }
    return { positions, height: Math.max(0, top - LANE_GAP) };
}
