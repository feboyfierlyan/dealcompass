import { useEffect, useId, useMemo, useRef, useState } from 'react';
import type { DealContext, GraphEdge } from '../lib/contracts';
import { kindLabel } from '../lib/format';
import { nodeName, nodeTypeLabel, relationPhrase } from '../lib/present';
import { expandNodes, focusTarget, indexGraph, INITIAL_NODE_LIMIT, layoutGraph, MAX_VISIBLE_NODES, neighbors, pathToDeal, scopeNodes, searchNodes, visibleGraph } from '../lib/graphView';
import type { GraphTarget } from '../lib/analysisView';
import type { GraphScope } from '../lib/graphView';
import { Icon } from './Icon';

export type Selection = { kind: 'node' | 'edge' | 'evidence'; id: string } | null;
const number = (n: number) => n.toLocaleString('en-GB');

export type GraphPath = { node_ids: string[]; edge_ids: string[] };
/** Union of API evidence paths, limited to nodes present in the payload. Edges are never created. */
function pathNodes(index: ReturnType<typeof indexGraph>, paths: GraphPath[]) {
  const ids = [...new Set(paths.flatMap(p => p.node_ids))].filter(id => index.nodes.has(id));
  return { ids: ids.slice(0, MAX_VISIBLE_NODES), truncated: ids.length > MAX_VISIBLE_NODES };
}
export function ContextGraph({ context, selection, onSelect, initialFocus, initialPaths }: { context: DealContext; selection: Selection; onSelect: (value: Selection) => void; initialFocus?: GraphTarget; initialPaths?: GraphPath[] }) {
  const index = useMemo(() => indexGraph(context), [context]);
  const [scope, setScope] = useState<GraphScope>('focus');
  const [ids, setIds] = useState(() => initialPaths?.length ? pathNodes(index, initialPaths).ids : initialFocus ? focusTarget(index, initialFocus).ids : scopeNodes(context, index, 'focus').slice(0, INITIAL_NODE_LIMIT));
  const [highlight, setHighlight] = useState(() => new Set(initialPaths?.flatMap(p => p.edge_ids) ?? []));
  const [query, setQuery] = useState('');
  const [type, setType] = useState('all');
  const [searchPage, setSearchPage] = useState(0);
  const [edgePage, setEdgePage] = useState(0);
  const [edgeKind, setEdgeKind] = useState<'all' | 'direct' | 'inferred'>('all');
  const [zoom, setZoom] = useState(1);
  const [width, setWidth] = useState(620);
  const [notice, setNotice] = useState(() => initialPaths?.length ? `Showing ${initialPaths.length} supporting paths (${pathNodes(index, initialPaths).ids.length} nodes). Highlighted lines are the supporting paths.${pathNodes(index, initialPaths).truncated ? ' Paths limited to 24 nodes; search to explore further.' : ''}` : initialFocus ? focusTarget(index, initialFocus).truncated ? 'Long paths are limited to 24 nodes; the source endpoint remains visible. Search for other nodes.' : 'Focused on the selected source. A path does not establish consent or a recommendation.' : '');
  const canvas = useRef<HTMLDivElement>(null);
  const marker = `arrow-${useId().replace(/:/g, '')}`;
  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    const observer = new ResizeObserver(() => setWidth(element.clientWidth));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  const scopeIds = useMemo(() => scopeNodes(context, index, scope), [context, index, scope]);
  const graph = useMemo(() => visibleGraph(index, ids, edgeKind), [index, ids, edgeKind]);
  const lanes = useMemo(() => {
    const groups = new Map<string, string[]>();
    for (const edge of graph.edges) {
      const pair = JSON.stringify([edge.source, edge.target].sort());
      groups.set(pair, [...(groups.get(pair) ?? []), edge.id]);
    }
    const offsets = new Map<string, number>();
    for (const edges of groups.values()) edges.forEach((id, i) => offsets.set(id, (i - (edges.length - 1) / 2) * 32));
    return offsets;
  }, [graph.edges]);
  const layout = useMemo(() => layoutGraph(graph.nodes, width), [graph.nodes, width]);
  const results = useMemo(() => searchNodes(index, query, type), [index, query, type]);
  const types = useMemo(() => [...new Set(context.graph.nodes.map(n => n.type))].sort(), [context]);
  const activeNode = selection?.kind === 'node' ? selection.id : selection?.kind === 'edge' ? index.edges.get(selection.id)?.target : index.root;
  const moreNeighbors = activeNode ? neighbors(index, activeNode).filter(id => !ids.includes(id)).length : 0;
  const moreScope = scopeIds.filter(id => !ids.includes(id));
  function resetView(next: GraphScope = scope) {
    setScope(next); setIds(scopeNodes(context, index, next).slice(0, INITIAL_NODE_LIMIT)); setHighlight(new Set());
    setEdgeKind('all'); setZoom(1); setNotice(''); setEdgePage(0); onSelect(null);
    canvas.current?.scrollTo({ top: 0, left: 0 });
  }
  function focusNode(id: string) {
    const path = pathToDeal(index, id);
    // All real paths remain accessible. If unusually long, disclose the cut explicitly.
    const limited = path.length > MAX_VISIBLE_NODES ? path.slice(-MAX_VISIBLE_NODES) : path;
    const connected = index.parent.has(id);
    setIds(limited); setEdgeKind('all'); setEdgePage(0); setZoom(1);
    setNotice(!connected ? 'This node has no path to the deal in the data. No relationship was invented.' : path.length > MAX_VISIBLE_NODES ? `Path contains ${path.length} nodes; showing the last ${MAX_VISIBLE_NODES}. Search for earlier nodes.` : 'Showing the available path to the deal. A path is not a business recommendation.');
    onSelect({ kind: 'node', id });
    requestAnimationFrame(() => canvas.current?.scrollTo({ top: 0, left: 0 }));
  }
  function expand() {
    if (!activeNode) return;
    const next = expandNodes(index, ids, activeNode);
    setIds(next.ids); setEdgePage(0);
    setNotice(next.remaining ? `${number(next.remaining)} neighbors hidden. Maximum ${MAX_VISIBLE_NODES} nodes per view; focus or search another node.` : 'All direct neighbors of the selected node are visible.');
  }
  function edgePath(edge: GraphEdge, i: number) {
    const a = layout.positions.get(edge.source)!, b = layout.positions.get(edge.target)!;
    const lane = lanes.get(edge.id) ?? 0;
    const gutter = 15 + (i % 4) * 7 + lane / 4;
    if (edge.source === edge.target) return `M ${a.x - 30} ${a.y - 40} C ${a.x - 65} ${a.y - 65}, ${a.x + 65} ${a.y - 65}, ${a.x + 30} ${a.y - 40}`;
    if (a.x === b.x) return `M ${a.x - layout.cardWidth / 2} ${a.y} C ${gutter} ${a.y}, ${gutter} ${b.y}, ${b.x - layout.cardWidth / 2} ${b.y}`;
    const direction = b.x > a.x ? 1 : -1;
    const x1 = a.x + direction * layout.cardWidth / 2, x2 = b.x - direction * layout.cardWidth / 2;
    const middle = (x1 + x2) / 2 + (i % 3 - 1) * 10;
    return `M ${x1} ${a.y} C ${middle} ${a.y + lane}, ${middle} ${b.y + lane}, ${x2} ${b.y}`;
  }
  const wrapLabel = (label: string) => {
    const max = Math.max(18, Math.floor((layout.cardWidth - 24) / 7));
    if (label.length <= max) return [label];
    const cut = label.lastIndexOf(' ', max);
    const first = cut > max / 2 ? cut : max;
    return [label.slice(0, first), label.slice(first).trim().slice(0, max - 1) + (label.slice(first).trim().length >= max ? '…' : '')];
  };
  if (!context.graph.nodes.length) return <div className="empty-state"><h3>No relationships yet</h3><p>Available sources can still be opened under All sources.</p></div>;
  return <div className="focused-graph">
    {notice && <p className="graph-notice" role="status">{notice}</p>}
    <div className="graph-toolbar"><details className="graph-view-options"><summary>Graph options</summary><div className="scope-buttons" role="group" aria-label="Graph scope"><button aria-pressed={scope === 'focus' && !highlight.size} onClick={() => resetView('focus')}>Deal & conversations</button><button aria-pressed={scope === 'precedents' && !highlight.size} onClick={() => resetView('precedents')}>Historical decisions (candidates)</button></div><label>Relationship <select aria-label="Filter relationship type" value={edgeKind} onChange={e => { setEdgeKind(e.target.value as typeof edgeKind); setEdgePage(0); }}><option value="all">All</option><option value="direct">Direct from source</option><option value="inferred">Inferred from relationships</option></select></label></details><div className="zoom-controls"><button aria-label="Zoom out" disabled={zoom <= .85} onClick={() => setZoom(z => Math.max(.85, z - .15))}><Icon name="minus" size={16}/></button><span>{Math.round(zoom * 100)}%</span><button aria-label="Zoom in" disabled={zoom >= 2} onClick={() => setZoom(z => Math.min(2, z + .15))}><Icon name="plus" size={16}/></button><button aria-label="Reset graph view" onClick={() => resetView()}><Icon name="target" size={16}/></button></div></div>
    <p className="graph-counts" role="status"><strong>{number(graph.nodes.length)} / {number(context.graph.nodes.length)} nodes</strong><span>{number(graph.edges.length)} / {number(context.graph.edges.length)} edges</span></p>
    <div className="graph-legend" aria-label="Relationship legend"><span><i aria-hidden="true"/>Direct</span><span><i className="dashed" aria-hidden="true"/>Inferred</span><span><Icon name="arrow" size={14}/>Direction</span></div>
    {!!index.invalidEdges.length && <p className="inline-warning">{index.invalidEdges.length} relationships cannot be drawn because their endpoints are missing.</p>}
    <div className="graph-canvas focus-canvas" ref={canvas} tabIndex={0} role="region" aria-label="Relationship graph canvas, scrollable">
      <svg style={{ width: layout.width * zoom, height: layout.height * zoom }} viewBox={`0 0 ${layout.width} ${layout.height}`} role="group" aria-label="Deal relationships. Select a node or edge to read its evidence.">
        <defs><marker id={marker} markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0L6 3L0 6" fill="none" stroke="currentColor"/></marker></defs>
        {graph.edges.map((edge, i) => <g key={edge.id} role="button" tabIndex={0} aria-label={`Relationship ${relationPhrase(edge.relation)} (${edge.relation}): ${edge.source} to ${edge.target}. ${kindLabel[edge.evidence_type]}.${highlight.has(edge.id) ? ' Part of the supporting path.' : ''}`} aria-pressed={selection?.kind === 'edge' && selection.id === edge.id} className={`graph-edge ${edge.evidence_type} ${highlight.has(edge.id) ? 'on-path' : ''} ${selection?.kind === 'edge' && selection.id === edge.id ? 'selected' : ''}`} onClick={() => onSelect({ kind: 'edge', id: edge.id })} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect({ kind: 'edge', id: edge.id }); } }}><path className="edge-hit" d={edgePath(edge, i)}/><path className="edge-visible" d={edgePath(edge, i)} markerEnd={`url(#${marker})`}/></g>)}
        {graph.nodes.map(node => { const p = layout.positions.get(node.id)!; return <g key={node.id} transform={`translate(${p.x},${p.y})`} role="button" tabIndex={0} aria-label={`Node ${nodeName(node, context)}, ${nodeTypeLabel(node.type)}, ID ${node.id}`} aria-pressed={selection?.kind === 'node' && selection.id === node.id} className={`focus-node ${node.id === index.root ? 'root' : ''} ${selection?.kind === 'node' && selection.id === node.id ? 'selected' : ''}`} onClick={() => onSelect({ kind: 'node', id: node.id })} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect({ kind: 'node', id: node.id }); } }}><title>{`${nodeName(node, context)} · ${nodeTypeLabel(node.type)} · ${node.id}`}</title><rect x={-layout.cardWidth / 2} y="-40" width={layout.cardWidth} height="88" rx="9"/>{wrapLabel(nodeName(node, context)).map((line, i) => <text key={i} className="focus-label" x={-layout.cardWidth / 2 + 12} y={i * 18 - 14}>{line}</text>)}<text className="focus-type" x={-layout.cardWidth / 2 + 12} y="33">{nodeTypeLabel(node.type)} · {node.id.length > 24 ? `${node.id.slice(0, 23)}…` : node.id}</text></g>; })}
      </svg>
    </div>
    <details className="relation-list"><summary>Visible relationships · {number(graph.edges.length)} / {number(context.graph.edges.length)}</summary><p className="small muted">Relationships between visible nodes matching the filter. Select to inspect original evidence; keyboard accessible.</p>{graph.edges.slice(edgePage * 12, (edgePage + 1) * 12).map(edge => <button className={`relation-row ${highlight.has(edge.id) ? 'on-path' : ''}`} key={edge.id} onClick={() => onSelect({ kind: 'edge', id: edge.id })}><span><strong>{relationPhrase(edge.relation)}</strong><small className="mono">{edge.source} → {edge.target} · {edge.relation}</small><small className="mono">{edge.evidence_ids.join(' · ')}</small></span><span className={`tag ${edge.evidence_type}`}>{kindLabel[edge.evidence_type]}</span></button>)}<div className="pagination"><span>{Math.min(edgePage * 12 + 1, graph.edges.length)}–{Math.min((edgePage + 1) * 12, graph.edges.length)} / {graph.edges.length}</span><button disabled={!edgePage} onClick={() => setEdgePage(p => p - 1)}>Previous relationships</button><button disabled={(edgePage + 1) * 12 >= graph.edges.length} onClick={() => setEdgePage(p => p + 1)}>Next relationships</button></div></details>
    <details className="graph-explore"><summary>Search & expand graph</summary>
      <p className="graph-disclosure">Focused view: {number(context.graph.nodes.length - graph.nodes.length)} nodes hidden. All {number(context.evidence.length)} records remain in All sources. Candidate decisions are not recommendations.</p>
      <div className="graph-search"><label><span>Search all nodes</span><input value={query} placeholder="ID or name, e.g. I0348" onChange={e => { setQuery(e.target.value); setSearchPage(0); }} /></label><label><span>Node type</span><select value={type} onChange={e => { setType(e.target.value); setSearchPage(0); }}><option value="all">All types</option>{types.map(t => <option key={t} value={t}>{nodeTypeLabel(t)}</option>)}</select></label></div>
      {(query.trim() || type !== 'all') && <div className="graph-results"><p>{number(results.length)} results across the graph · {results.length ? `${searchPage * 6 + 1}–${Math.min(results.length, (searchPage + 1) * 6)}` : '0'}</p>{results.slice(searchPage * 6, (searchPage + 1) * 6).map(node => <button key={node.id} onClick={() => focusNode(node.id)}><strong>{node.id}</strong><span>{nodeName(node, context)} <small>· {nodeTypeLabel(node.type)}</small></span><Icon name="arrow" size={14}/></button>)}<div className="pagination"><button disabled={!searchPage} onClick={() => setSearchPage(p => p - 1)}>Previous</button><button disabled={(searchPage + 1) * 6 >= results.length} onClick={() => setSearchPage(p => p + 1)}>Next</button><button onClick={() => { setQuery(''); setType('all'); setSearchPage(0); }}>Close search</button></div></div>}
      <div className="graph-actions"><button disabled={!activeNode || !moreNeighbors || ids.length >= MAX_VISIBLE_NODES} onClick={expand}>Expand node (+{Math.min(6, moreNeighbors, MAX_VISIBLE_NODES - ids.length)})</button><button disabled={!activeNode} onClick={() => activeNode && focusNode(activeNode)}>Focus node</button><button disabled={!moreScope.length || ids.length >= MAX_VISIBLE_NODES} onClick={() => { setIds(current => [...current, ...moreScope.slice(0, Math.min(6, MAX_VISIBLE_NODES - current.length))]); setEdgePage(0); }}>Add from scope ({number(moreScope.length)})</button></div>
      <p className="graph-selection">Expand node: <strong>{activeNode ?? 'none selected'}</strong>{activeNode && ` · ${number(moreNeighbors)} neighbors hidden`}</p>
    </details>
  </div>;
}
