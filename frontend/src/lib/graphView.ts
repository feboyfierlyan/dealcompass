import type { DealContext, GraphEdge, GraphNode } from './contracts';

export const INITIAL_NODE_LIMIT = 12;
export const MAX_VISIBLE_NODES = 24;
export const EXPAND_BATCH = 6;
export type GraphScope = 'focus' | 'precedents';

// Build once per context. Traversals use adjacency, not a scan of every edge per node.
export function indexGraph(context: DealContext) {
  const nodes = new Map(context.graph.nodes.map(node => [node.id, node]));
  const edges = new Map(context.graph.edges.map(edge => [edge.id, edge]));
  const adjacent = new Map<string, GraphEdge[]>();
  const invalidEdges: GraphEdge[] = [];
  for (const node of nodes.values()) adjacent.set(node.id, []);
  for (const edge of edges.values()) {
    if (!nodes.has(edge.source) || !nodes.has(edge.target)) { invalidEdges.push(edge); continue; }
    adjacent.get(edge.source)!.push(edge);
    if (edge.target !== edge.source) adjacent.get(edge.target)!.push(edge);
  }
  const root = nodes.has(context.deal.deal_id) ? context.deal.deal_id : null;
  const parent = new Map<string, string | null>();
  if (root) {
    parent.set(root, null);
    const queue = [root];
    for (let i = 0; i < queue.length; i++) {
      for (const edge of adjacent.get(queue[i]) ?? []) {
        const next = edge.source === queue[i] ? edge.target : edge.source;
        if (!parent.has(next)) { parent.set(next, queue[i]); queue.push(next); }
      }
    }
  }
  return { nodes, edges, adjacent, invalidEdges, root, parent };
}
export type GraphIndex = ReturnType<typeof indexGraph>;

export function pathToDeal(index: GraphIndex, id: string): string[] {
  if (!index.nodes.has(id)) return [];
  if (!index.parent.has(id)) return [id]; // Keep isolated nodes reachable; never invent an edge.
  const path = [id];
  let parent = index.parent.get(id);
  while (parent) { path.push(parent); parent = index.parent.get(parent); }
  return path.reverse();
}
export function scopeNodes(context: DealContext, index: GraphIndex, scope: GraphScope): string[] {
  const ids = [context.deal.deal_id, context.deal.account_id].filter(id => index.nodes.has(id));
  if (scope === 'focus') {
    const interactions = (index.adjacent.get(context.deal.account_id) ?? [])
      .filter(edge => edge.relation === 'interaction_for' && edge.target === context.deal.account_id)
      .map(edge => edge.source);
    // Newest source event first for presentation, not sales priority or a recommendation.
    const dates = new Map<string, string>();
    for (const e of context.evidence) if (e.date) dates.set(e.source_id, e.date);
    interactions.sort((a, b) => (dates.get(b) ?? '').localeCompare(dates.get(a) ?? '') || a.localeCompare(b));
    ids.push(...interactions);
    for (const edge of index.adjacent.get(context.deal.deal_id) ?? []) {
      if (edge.source === context.deal.deal_id && edge.relation === 'owned_by') ids.push(edge.target);
    }
  } else {
    for (const edge of index.adjacent.get(context.deal.deal_id) ?? []) {
      if (edge.source === context.deal.deal_id && edge.relation.startsWith('candidate_precedent_')) ids.push(edge.target);
    }
  }
  return [...new Set(ids)].filter(id => index.nodes.has(id));
}
export function visibleGraph(index: GraphIndex, ids: string[], kind: 'all' | 'direct' | 'inferred' = 'all') {
  const selected = new Set(ids);
  const nodes = ids.flatMap(id => index.nodes.has(id) ? [index.nodes.get(id)!] : []);
  const edgeIds = new Set<string>();
  const edges: GraphEdge[] = [];
  for (const id of ids) for (const edge of index.adjacent.get(id) ?? []) {
    if (!edgeIds.has(edge.id) && selected.has(edge.source) && selected.has(edge.target) && (kind === 'all' || edge.evidence_type === kind)) {
      edgeIds.add(edge.id); edges.push(edge);
    }
  }
  return { nodes, edges };
}
export function neighbors(index: GraphIndex, id: string): string[] {
  return [...new Set((index.adjacent.get(id) ?? []).map(edge => edge.source === id ? edge.target : edge.source))];
}
export function expandNodes(index: GraphIndex, current: string[], id: string) {
  const unseen = neighbors(index, id).filter(next => !current.includes(next));
  const added = unseen.slice(0, Math.min(EXPAND_BATCH, Math.max(0, MAX_VISIBLE_NODES - current.length)));
  return { ids: [...current, ...added], remaining: unseen.length - added.length };
}
export function searchNodes(index: GraphIndex, query: string, type = 'all') {
  const needle = query.trim().toLocaleLowerCase('id');
  return [...index.nodes.values()].filter(node => (type === 'all' || node.type === type)
    && `${node.id} ${node.label} ${node.type}`.toLocaleLowerCase('id').includes(needle));
}

// Pixel dimensions stay legible as the graph grows: scroll, never fit thousands of rows.
export function layoutGraph(nodes: GraphNode[], containerWidth: number) {
  const width = Math.max(260, Math.floor(containerWidth));
  const columns = width >= 580 ? 2 : 1;
  const cardWidth = Math.min(236, width / columns - 58);
  const positions = new Map(nodes.map((node, i) => [node.id, {
    x: (i % columns + .5) * width / columns,
    y: 65 + Math.floor(i / columns) * 138,
  }]));
  return { width, height: Math.max(260, Math.ceil(nodes.length / columns) * 138), cardWidth, positions };
}

export function evidenceExcerpt(excerpt: string): { text: string; structured: boolean } {
  try {
    const row: unknown = JSON.parse(excerpt);
    if (typeof row === 'object' && row !== null && !Array.isArray(row)) {
      const record = row as Record<string, unknown>;
      // Display the original message if provided. Do not treat every row/aggregate as speech.
      if (typeof record.isi === 'string') return { text: record.isi, structured: true };
      return { text: JSON.stringify(record, null, 2), structured: true };
    }
  } catch { /* Legacy text fixtures remain readable, without interpreting their contents. */ }
  return { text: excerpt, structured: false };
}
