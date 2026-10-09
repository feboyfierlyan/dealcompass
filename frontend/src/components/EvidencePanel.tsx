import { useState } from 'react';
import type { DealContext, Evidence } from '../lib/contracts';
import { evidenceExcerpt } from '../lib/graphView';
import { evidenceGraphLinks } from '../lib/analysisView';
import type { GraphTarget } from '../lib/analysisView';
import { resolveEvidence } from '../lib/contracts';
import { dateLabel, kindLabel } from '../lib/format';
import type { Selection } from './ContextGraph';
import { Icon } from './Icon';

function sourceUrl(file: string) {
  if (!/^dataset_kasirnusa\/[\w.-]+\.(csv|jsonl)$/.test(file)) return null;
  return `https://github.com/feboyfierlyan/dealcompass/blob/main/${file.split('/').map(encodeURIComponent).join('/')}`;
}
function SourceGraphLinks({ evidence, context, onGraph }: { evidence: Evidence; context: DealContext; onGraph: (target: GraphTarget) => void }) {
  const [page, setPage] = useState(0);
  const links = evidenceGraphLinks(context, evidence.id);
  return <div className="source-graph-links">
    {links.node ? <button className="button secondary" onClick={() => onGraph({ kind: 'node', id: links.node!.id })}>Fokus graph: {links.node.id}</button> : <p className="small muted">Sumber ini tidak memiliki pemetaan node unik dari ID dan relasi yang tersedia.</p>}
    {links.edges.length ? <details><summary>Relasi yang memakai sumber ini ({links.edges.length})</summary><p className="small muted">Pilih relasi untuk membuka endpoint asli dan buktinya. {page * 6 + 1}–{Math.min((page + 1) * 6, links.edges.length)} / {links.edges.length}</p>{links.edges.slice(page * 6, (page + 1) * 6).map(edge => <button className="source-edge" key={edge.id} onClick={() => onGraph({ kind: 'edge', id: edge.id })}><strong>{edge.source} → {edge.target}</strong><small>{edge.relation} · {kindLabel[edge.evidence_type]}</small><small>{dateLabel(edge.valid_from)}</small></button>)}{links.edges.length > 6 && <div className="pagination"><button disabled={!page} onClick={() => setPage(p => p - 1)}>Relasi sumber sebelumnya</button><button disabled={(page + 1) * 6 >= links.edges.length} onClick={() => setPage(p => p + 1)}>Relasi sumber berikutnya</button></div>}</details> : <p className="inline-warning">Tidak ada relasi tersedia yang merujuk bukti ini. Record tetap dapat diperiksa; hubungan tidak dibuat.</p>}
  </div>;
}
export function EvidenceCard({ evidence, context, onGraph }: { evidence: Evidence; context: DealContext; onGraph: (target: GraphTarget) => void }) {
  const url = sourceUrl(evidence.source_file);
  const excerpt = evidenceExcerpt(evidence.excerpt);
  return <article className="evidence-card"><div className="row-between"><span className={`badge ${evidence.evidence_type}`}>{kindLabel[evidence.evidence_type]}</span><span className="mono">{evidence.id}</span></div>
    <p className="evidence-date"><Icon name="clock" size={13}/>{dateLabel(evidence.date)}</p>
    <blockquote>{excerpt.text || 'Kutipan belum tersedia.'}</blockquote>
    {excerpt.structured && <details className="raw-source"><summary>Record asli (JSON)</summary><pre>{evidence.excerpt}</pre></details>}
    <dl className="source-details"><div><dt>Sumber</dt><dd>{url ? <a href={url} target="_blank" rel="noreferrer">{evidence.source_file} ↗</a> : evidence.source_file}</dd></div><div><dt>Record sumber</dt><dd className="mono">{evidence.source_id}</dd></div></dl>
    <SourceGraphLinks evidence={evidence} context={context} onGraph={onGraph}/>
  </article>;
}
function EvidenceStack({ records, context, onGraph }: { records: Evidence[]; context: DealContext; onGraph: (target: GraphTarget) => void }) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);
  const filtered = records.filter(e => `${e.id} ${e.source_id} ${e.excerpt}`.toLowerCase().includes(query.trim().toLowerCase()));
  return <><label className="evidence-search">Cari bukti terkait<input value={query} onChange={e => { setQuery(e.target.value); setPage(0); }} placeholder="ID atau isi sumber"/></label><p className="small muted">{filtered.length} cocok dari {records.length} bukti terkait · menampilkan {Math.min(page * 6 + 1, filtered.length)}–{Math.min((page + 1) * 6, filtered.length)}</p><div className="evidence-stack">{filtered.slice(page * 6, (page + 1) * 6).map(e => <EvidenceCard key={e.id} evidence={e} context={context} onGraph={onGraph}/>)}</div><div className="pagination"><button disabled={!page} onClick={() => setPage(p => p - 1)}>Bukti sebelumnya</button><button disabled={(page + 1) * 6 >= filtered.length} onClick={() => setPage(p => p + 1)}>Bukti berikutnya</button></div></>;
}
export function EvidencePanel({ context, selection, onClear, onGraph }: { context: DealContext | null; selection: Selection; onClear: () => void; onGraph: (target: GraphTarget) => void }) {
  let title = 'Telusuri alasannya';
  let subtitle = 'Pilih bukti, node, atau relasi untuk melihat sumbernya.';
  let ids: string[] = [];
  let edge = null;
  let connected = 0;
  if (context && selection?.kind === 'evidence') { ids = [selection.id]; title = 'Bukti terpilih'; subtitle = selection.id; }
  if (context && selection?.kind === 'edge') {
    edge = context.graph.edges.find(e => e.id === selection.id) ?? null;
    if (edge) { title = edge.relation; subtitle = `${edge.source} → ${edge.target}`; ids = edge.evidence_ids; }
  }
  if (context && selection?.kind === 'node') {
    const node = context.graph.nodes.find(n => n.id === selection.id);
    const edges = context.graph.edges.filter(e => e.source === selection.id || e.target === selection.id);
    connected = edges.length;
    title = node?.label ?? selection.id;
    subtitle = `${node?.type ?? 'Node'} · ${connected} relasi terkait`;
    ids = edges.flatMap(e => e.evidence_ids);
  }
  const resolved = resolveEvidence(ids, context?.evidence ?? []);
  return <aside id="evidence-inspector" tabIndex={-1} className="inspector panel" aria-label="Panel sumber bukti"><div className="panel-heading"><span className="eyebrow">JEJAK BUKTI</span><Icon name="file" size={18}/></div>
    <h3>{title}</h3><p className="muted small">{subtitle}</p>
    {selection && <button className="text-button" onClick={onClear}>Hapus pilihan</button>}
    {edge && <div className="edge-meta"><span className={`badge ${edge.evidence_type}`}>{kindLabel[edge.evidence_type]}</span><dl><dt>Berlaku sejak</dt><dd>{dateLabel(edge.valid_from)}</dd><dt>Berlaku sampai</dt><dd>{edge.valid_to ? dateLabel(edge.valid_to) : 'Tidak dicantumkan'}</dd></dl></div>}
    {!selection && <div className="inspector-empty"><div className="paper-stack"><Icon name="file" size={32}/></div><p>Setiap keputusan dimulai<br/>dari bukti yang bisa diperiksa.</p><small>{context ? `${context.evidence.length} bukti tersedia pada deal ini.` : 'Bukti tampil setelah konteks deal tersedia.'}</small></div>}
    {selection && !ids.length && <p className="inline-warning">Belum ada ID bukti yang ditautkan{selection.kind === 'node' ? ' pada relasi node ini' : ''}.</p>}
    {!!resolved.missing.length && <p role="status" className="inline-warning">Sumber belum dapat diverifikasi untuk ID: {resolved.missing.join(', ')}.</p>}
    {context && !!resolved.records.length && <EvidenceStack key={`${selection?.kind}:${selection?.id}`} records={resolved.records} context={context} onGraph={onGraph}/>}
    <div className="inspector-footnote"><Icon name="info" size={14}/><span>Inferensi adalah hasil penalaran. Periksa sumber sebelum mengambil tindakan.</span></div>
  </aside>;
}
