import { useEffect, useId, useMemo, useRef, useState } from 'react';
import type { DealContext, GraphEdge } from '../lib/contracts';
import { kindLabel } from '../lib/format';
import { expandNodes, indexGraph, INITIAL_NODE_LIMIT, layoutGraph, MAX_VISIBLE_NODES, neighbors, pathToDeal, scopeNodes, searchNodes, visibleGraph } from '../lib/graphView';
import type { GraphScope } from '../lib/graphView';
import { Icon } from './Icon';

export type Selection = { kind: 'node' | 'edge' | 'evidence'; id: string } | null;
const number = (n: number) => n.toLocaleString('id-ID');

export function ContextGraph({ context, selection, onSelect }: { context: DealContext; selection: Selection; onSelect: (value: Selection) => void }) {
  const index = useMemo(() => indexGraph(context), [context]);
  const [scope, setScope] = useState<GraphScope>('focus');
  const [ids, setIds] = useState(() => scopeNodes(context, index, 'focus').slice(0, INITIAL_NODE_LIMIT));
  const [query, setQuery] = useState('');
  const [type, setType] = useState('all');
  const [searchPage, setSearchPage] = useState(0);
  const [edgePage, setEdgePage] = useState(0);
  const [edgeKind, setEdgeKind] = useState<'all' | 'direct' | 'inferred'>('all');
  const [zoom, setZoom] = useState(1);
  const [width, setWidth] = useState(620);
  const [notice, setNotice] = useState('');
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
    setScope(next); setIds(scopeNodes(context, index, next).slice(0, INITIAL_NODE_LIMIT));
    setEdgeKind('all'); setZoom(1); setNotice(''); setEdgePage(0); onSelect(null);
    canvas.current?.scrollTo({ top: 0, left: 0 });
  }
  function focusNode(id: string) {
    const path = pathToDeal(index, id);
    // All real paths remain accessible. If unusually long, disclose the cut explicitly.
    const limited = path.length > MAX_VISIBLE_NODES ? path.slice(-MAX_VISIBLE_NODES) : path;
    const connected = index.parent.has(id);
    setIds(limited); setEdgeKind('all'); setEdgePage(0); setZoom(1);
    setNotice(!connected ? 'Node ini tidak memiliki jalur ke deal pada payload. Tidak ada hubungan yang dibuat.' : path.length > MAX_VISIBLE_NODES ? `Jalur berisi ${path.length} node; menampilkan ${MAX_VISIBLE_NODES} node terakhir. Cari node lain untuk menelusuri bagian sebelumnya.` : 'Menampilkan jalur hubungan yang tersedia ke deal. Jalur bukan rekomendasi bisnis.');
    onSelect({ kind: 'node', id });
    requestAnimationFrame(() => canvas.current?.scrollTo({ top: 0, left: 0 }));
  }
  function expand() {
    if (!activeNode) return;
    const next = expandNodes(index, ids, activeNode);
    setIds(next.ids); setEdgePage(0);
    setNotice(next.remaining ? `${number(next.remaining)} tetangga belum ditampilkan. Maksimal ${MAX_VISIBLE_NODES} node per tampilan; gunakan Fokuskan node atau cari node lain.` : 'Semua tetangga langsung node terpilih sudah dimuat dalam tampilan.');
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
  if (!context.graph.nodes.length) return <div className="empty-state"><h3>Relasi belum tersedia</h3><p>Bukti yang tersedia tetap dapat dibuka melalui tab Bukti.</p></div>;
  return <div className="focused-graph">
    <div className="scope-buttons" aria-label="Lingkup graph"><button aria-pressed={scope === 'focus'} onClick={() => resetView('focus')}>Deal & percakapan</button><button aria-pressed={scope === 'precedents'} onClick={() => resetView('precedents')}>Kandidat preseden</button></div>
    <p className="graph-counts" role="status"><strong>{number(graph.nodes.length)} / {number(context.graph.nodes.length)} node</strong><span>{number(graph.edges.length)} / {number(context.graph.edges.length)} relasi</span></p>
    <p className="graph-disclosure">Tampilan fokus, bukan seluruh graph. {number(context.graph.nodes.length - graph.nodes.length)} node belum ditampilkan. Semua {number(context.evidence.length)} bukti tetap tersedia di tab Bukti. Kandidat preseden belum merupakan rekomendasi.</p>
    <div className="graph-search"><label><span>Cari di seluruh graph</span><input value={query} placeholder="ID atau nama, mis. ID interaksi" onChange={e => { setQuery(e.target.value); setSearchPage(0); }} /></label><label><span>Jenis node</span><select value={type} onChange={e => { setType(e.target.value); setSearchPage(0); }}><option value="all">Semua jenis</option>{types.map(t => <option key={t}>{t}</option>)}</select></label></div>
    {(query.trim() || type !== 'all') && <div className="graph-results"><p>{number(results.length)} hasil di seluruh graph · {results.length ? `${searchPage * 6 + 1}–${Math.min(results.length, (searchPage + 1) * 6)}` : '0'}</p>{results.slice(searchPage * 6, (searchPage + 1) * 6).map(node => <button key={node.id} onClick={() => focusNode(node.id)}><strong>{node.id}</strong><span>{node.label} <small>· {node.type}</small></span><Icon name="arrow" size={14}/></button>)}<div className="pagination"><button disabled={!searchPage} onClick={() => setSearchPage(p => p - 1)}>Sebelumnya</button><button disabled={(searchPage + 1) * 6 >= results.length} onClick={() => setSearchPage(p => p + 1)}>Berikutnya</button><button onClick={() => { setQuery(''); setType('all'); setSearchPage(0); }}>Tutup pencarian</button></div></div>}
    <div className="graph-actions"><button disabled={!activeNode || !moreNeighbors || ids.length >= MAX_VISIBLE_NODES} onClick={expand}>Perluas node (+{Math.min(6, moreNeighbors, MAX_VISIBLE_NODES - ids.length)})</button><button disabled={!activeNode} onClick={() => activeNode && focusNode(activeNode)}>Fokuskan node</button><button disabled={!moreScope.length || ids.length >= MAX_VISIBLE_NODES} onClick={() => { setIds(current => [...current, ...moreScope.slice(0, Math.min(6, MAX_VISIBLE_NODES - current.length))]); setEdgePage(0); }}>Tambah dari lingkup ({number(moreScope.length)})</button></div>
    <p className="graph-selection">Node untuk diperluas: <strong>{activeNode ?? 'belum dipilih'}</strong>{activeNode && ` · ${number(moreNeighbors)} tetangga belum ditampilkan`}</p>
    {notice && <p className="graph-notice" role="status">{notice}</p>}
    {!!index.invalidEdges.length && <p className="inline-warning">{index.invalidEdges.length} relasi tidak dapat digambar karena node ujung tidak ada pada payload.</p>}
    <div className="graph-toolbar"><label>Relasi <select aria-label="Filter jenis relasi" value={edgeKind} onChange={e => { setEdgeKind(e.target.value as typeof edgeKind); setEdgePage(0); }}><option value="all">Semua</option><option value="direct">Langsung</option><option value="inferred">Inferensi</option></select></label><div className="zoom-controls"><button aria-label="Perkecil graph" disabled={zoom <= .85} onClick={() => setZoom(z => Math.max(.85, z - .15))}>−</button><span>{Math.round(zoom * 100)}%</span><button aria-label="Perbesar graph" disabled={zoom >= 2} onClick={() => setZoom(z => Math.min(2, z + .15))}>+</button><button aria-label="Reset tampilan graph" onClick={() => resetView()}><Icon name="target" size={16}/></button></div></div>
    <p className="graph-scroll-help">Scroll dalam kanvas untuk melihat node lainnya. Garis putus-putus = inferensi. Label dipertahankan pada ukuran baca.</p>
    <div className="graph-canvas focus-canvas" ref={canvas} tabIndex={0} role="region" aria-label="Kanvas graph fokus, dapat digulir">
      <svg style={{ width: layout.width * zoom, height: layout.height * zoom }} viewBox={`0 0 ${layout.width} ${layout.height}`} role="group" aria-label="Peta hubungan deal. Pilih node atau relasi untuk membaca bukti.">
        <defs><marker id={marker} markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0L6 3L0 6" fill="none" stroke="currentColor"/></marker></defs>
        {graph.edges.map((edge, i) => <g key={edge.id} role="button" tabIndex={0} aria-label={`Relasi ${edge.relation}: ${edge.source} ke ${edge.target}. ${kindLabel[edge.evidence_type]}. ${edge.id}`} aria-pressed={selection?.kind === 'edge' && selection.id === edge.id} className={`graph-edge ${edge.evidence_type} ${selection?.kind === 'edge' && selection.id === edge.id ? 'selected' : ''}`} onClick={() => onSelect({ kind: 'edge', id: edge.id })} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect({ kind: 'edge', id: edge.id }); } }}><path className="edge-hit" d={edgePath(edge, i)}/><path className="edge-visible" d={edgePath(edge, i)} markerEnd={`url(#${marker})`}/></g>)}
        {graph.nodes.map(node => { const p = layout.positions.get(node.id)!; return <g key={node.id} transform={`translate(${p.x},${p.y})`} role="button" tabIndex={0} aria-label={`Node ${node.id}: ${node.label}, ${node.type}`} aria-pressed={selection?.kind === 'node' && selection.id === node.id} className={`focus-node ${node.id === index.root ? 'root' : ''} ${selection?.kind === 'node' && selection.id === node.id ? 'selected' : ''}`} onClick={() => onSelect({ kind: 'node', id: node.id })} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect({ kind: 'node', id: node.id }); } }}><title>{node.id} · {node.label} · {node.type}</title><rect x={-layout.cardWidth / 2} y="-40" width={layout.cardWidth} height="88" rx="9"/><text className="focus-id" x={-layout.cardWidth / 2 + 12} y="-20">{node.id.length > 29 ? `${node.id.slice(0, 28)}…` : node.id}</text>{wrapLabel(node.label).map((line, i) => <text key={i} className="focus-label" x={-layout.cardWidth / 2 + 12} y={i * 17 + 1}>{line}</text>)}<text className="focus-type" x={-layout.cardWidth / 2 + 12} y="35">{node.type}</text></g>; })}
      </svg>
    </div>
    <details className="relation-list"><summary>Relasi dalam tampilan · {number(graph.edges.length)} / {number(context.graph.edges.length)}</summary><p className="small muted">Hanya relasi antar-node yang sedang dimuat dan lolos filter. Klik untuk memeriksa bukti asli.</p>{graph.edges.slice(edgePage * 12, (edgePage + 1) * 12).map(edge => <button className="relation-row" key={edge.id} onClick={() => onSelect({ kind: 'edge', id: edge.id })}><span>{edge.source} → {edge.target}<small>{edge.relation}</small><small>{edge.evidence_ids.join(" · ")}</small></span><span className={`badge ${edge.evidence_type}`}>{kindLabel[edge.evidence_type]}</span></button>)}<div className="pagination"><span>{Math.min(edgePage * 12 + 1, graph.edges.length)}–{Math.min((edgePage + 1) * 12, graph.edges.length)} / {graph.edges.length}</span><button disabled={!edgePage} onClick={() => setEdgePage(p => p - 1)}>Relasi sebelumnya</button><button disabled={(edgePage + 1) * 12 >= graph.edges.length} onClick={() => setEdgePage(p => p + 1)}>Relasi berikutnya</button></div></details>
  </div>;
}
