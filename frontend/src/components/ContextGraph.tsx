import { useId, useMemo, useRef, useState } from 'react';
import type { DealContext, GraphEdge } from '../lib/contracts';
import { kindLabel } from '../lib/format';
import { Icon } from './Icon';

export type Selection = { kind: 'node' | 'edge' | 'evidence'; id: string } | null;
export function ContextGraph({ context, selection, onSelect }: { context: DealContext; selection: Selection; onSelect: (value: Selection) => void }) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const drag = useRef<{ x: number; y: number; px: number; py: number } | null>(null);
  const marker = `arrow-${useId().replace(/:/g, '')}`;
  const { nodes, edges } = context.graph;
  const layout = useMemo(() => {
    const ids = new Set(nodes.map(n => n.id));
    const validEdges = edges.filter(e => ids.has(e.source) && ids.has(e.target));
    const levels = new Map<string, number>();
    const root = nodes.find(n => n.id === context.deal.deal_id) ?? nodes[0];
    if (root) {
      levels.set(root.id, 0);
      const queue = [root.id];
      for (let i = 0; i < queue.length; i++) {
        for (const edge of validEdges) {
          const next = edge.source === queue[i] ? edge.target : edge.target === queue[i] ? edge.source : null;
          if (next && !levels.has(next)) { levels.set(next, Math.min(3, levels.get(queue[i])! + 1)); queue.push(next); }
        }
      }
    }
    const columns: string[][] = [[], [], [], [], []];
    nodes.forEach(node => columns[levels.get(node.id) ?? 4].push(node.id));
    const active = columns.filter(c => c.length);
    const height = Math.max(380, ...active.map(c => c.length * 114 + 80));
    const width = Math.max(700, active.length * 220 + 100);
    const positions = new Map<string, { x: number; y: number }>();
    active.forEach((column, x) => column.forEach((id, y) => positions.set(id, { x: 90 + x * ((width - 180) / Math.max(1, active.length - 1)), y: (y + 1) * height / (column.length + 1) })));
    return { positions, width, height, validEdges, invalidCount: edges.length - validEdges.length };
  }, [nodes, edges, context.deal.deal_id]);
  function edgePath(edge: GraphEdge, index: number) {
    const a = layout.positions.get(edge.source)!, b = layout.positions.get(edge.target)!;
    if (edge.source === edge.target) return `M ${a.x - 20} ${a.y - 20} C ${a.x - 85} ${a.y - 100}, ${a.x + 85} ${a.y - 100}, ${a.x + 20} ${a.y - 20}`;
    const offset = a.x === b.x ? 65 : (index % 3 - 1) * 18;
    const middle = (a.x + b.x) / 2 + offset;
    return `M ${a.x} ${a.y} C ${middle} ${a.y}, ${middle} ${b.y}, ${b.x} ${b.y}`;
  }
  if (!nodes.length) return <div className="empty-state"><Icon name="graph" size={32}/><h3>Relasi belum tersedia</h3><p>Konteks ini belum memuat node graph. Bukti yang tersedia tetap dapat diperiksa melalui tab Bukti.</p></div>;
  return <>
    <div className="graph-toolbar"><span><i className="legend-line"/> Langsung <i className="legend-line dashed"/> Inferensi</span><div className="zoom-controls"><button aria-label="Perkecil graph" onClick={() => setZoom(z => Math.max(.6, z - .2))}>−</button><span>{Math.round(zoom * 100)}%</span><button aria-label="Perbesar graph" onClick={() => setZoom(z => Math.min(2.5, z + .2))}>+</button><button onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }} aria-label="Reset tampilan graph"><Icon name="target" size={16}/></button></div></div>
    {layout.invalidCount > 0 && <p className="inline-warning" role="status">{layout.invalidCount} relasi memiliki node yang tidak ditemukan dan tidak dapat digambar.</p>}
    <div className="graph-canvas">
      <svg viewBox={`${pan.x} ${pan.y} ${layout.width / zoom} ${layout.height / zoom}`} aria-label="Peta hubungan deal. Pilih node atau relasi untuk membaca bukti." role="group"
        onPointerDown={e => { if (e.button !== 0) return; drag.current = { x: e.clientX, y: e.clientY, px: pan.x, py: pan.y }; e.currentTarget.setPointerCapture(e.pointerId); }}
        onPointerMove={e => { if (!drag.current) return; const rect = e.currentTarget.getBoundingClientRect(); const scale = Math.max(layout.width / rect.width, layout.height / rect.height) / zoom; setPan({ x: drag.current.px - (e.clientX - drag.current.x) * scale, y: drag.current.py - (e.clientY - drag.current.y) * scale }); }}
        onPointerUp={() => { drag.current = null; }} onPointerCancel={() => { drag.current = null; }}>
        <defs><marker id={marker} markerWidth="8" markerHeight="8" refX="30" refY="3" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0L6 3L0 6" fill="none" stroke="currentColor"/></marker></defs>
        {layout.validEdges.map((edge, index) => <g key={edge.id} role="button" tabIndex={0} aria-label={`Relasi ${edge.relation}: ${edge.source} ke ${edge.target}. ${kindLabel[edge.evidence_type]}`} aria-pressed={selection?.kind === 'edge' && selection.id === edge.id}
          className={`graph-edge ${edge.evidence_type} ${selection?.kind === 'edge' && selection.id === edge.id ? 'selected' : ''}`}
          onPointerDown={e => e.stopPropagation()} onClick={() => onSelect({ kind: 'edge', id: edge.id })} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect({ kind: 'edge', id: edge.id }); } }}>
          <path className="edge-hit" d={edgePath(edge, index)}/><path className="edge-visible" d={edgePath(edge, index)} markerEnd={`url(#${marker})`}/>
        </g>)}
        {nodes.map(node => {
          const position = layout.positions.get(node.id)!;
          const isRoot = node.id === context.deal.deal_id;
          return <g key={node.id} transform={`translate(${position.x},${position.y})`} role="button" tabIndex={0} aria-label={`Node ${node.label}, ${node.type}`} aria-pressed={selection?.kind === 'node' && selection.id === node.id}
            className={`graph-node ${isRoot ? 'root' : ''} ${selection?.kind === 'node' && selection.id === node.id ? 'selected' : ''}`} onPointerDown={e => e.stopPropagation()}
            onClick={() => onSelect({ kind: 'node', id: node.id })} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect({ kind: 'node', id: node.id }); } }}>
            <title>{node.label} · {node.id} · {node.type}</title><circle r="29"/><text className="node-monogram" y="5">{isRoot ? context.deal.account_id : node.type.slice(0, 2).toUpperCase()}</text>
            <text className="node-label" y="48">{node.label.length > 25 ? `${node.label.slice(0, 24)}…` : node.label}</text><text className="node-type" y="64">{node.type}</text>
          </g>;
        })}
      </svg>
      <span className="graph-hint">Geser untuk menjelajah · klik untuk menelusuri bukti</span>
    </div>
    <details className="relation-list"><summary>Daftar relasi · {edges.length}</summary><div>{edges.map(edge => <button className="relation-row" key={edge.id} onClick={() => onSelect({ kind: 'edge', id: edge.id })}><span>{edge.source} <Icon name="arrow" size={12}/> {edge.target}<small>{edge.relation}</small></span><span className={`badge ${edge.evidence_type}`}>{kindLabel[edge.evidence_type]}</span></button>)}</div></details>
  </>;
}
