import { useState } from 'react';
import type { DealContext, Evidence } from '../lib/contracts';
import { evidenceExcerpt } from '../lib/graphView';
import { resolveEvidence } from '../lib/contracts';
import { dateLabel, kindLabel } from '../lib/format';
import type { Selection } from './ContextGraph';
import { Icon } from './Icon';

function sourceUrl(file: string) {
  if (!/^dataset_kasirnusa\/[\w.-]+\.(csv|jsonl)$/.test(file)) return null;
  return `https://github.com/feboyfierlyan/dealcompass/blob/main/${file.split('/').map(encodeURIComponent).join('/')}`;
}
export function EvidenceCard({ evidence }: { evidence: Evidence }) {
  const url = sourceUrl(evidence.source_file);
  const excerpt = evidenceExcerpt(evidence.excerpt);
  return <article className="evidence-card"><div className="row-between"><span className={`badge ${evidence.evidence_type}`}>{kindLabel[evidence.evidence_type]}</span><span className="mono">{evidence.id}</span></div>
    <p className="evidence-date"><Icon name="clock" size={13}/>{dateLabel(evidence.date)}</p>
    <blockquote>{excerpt.text || 'Kutipan belum tersedia.'}</blockquote>
    {excerpt.structured && <details className="raw-source"><summary>Record asli (JSON)</summary><pre>{evidence.excerpt}</pre></details>}
    <dl className="source-details"><div><dt>Sumber</dt><dd>{url ? <a href={url} target="_blank" rel="noreferrer">{evidence.source_file} ↗</a> : evidence.source_file}</dd></div><div><dt>Record sumber</dt><dd className="mono">{evidence.source_id}</dd></div></dl>
  </article>;
}
function EvidenceStack({ records }: { records: Evidence[] }) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);
  const filtered = records.filter(e => `${e.id} ${e.source_id} ${e.excerpt}`.toLowerCase().includes(query.trim().toLowerCase()));
  return <><label className="evidence-search">Cari bukti terkait<input value={query} onChange={e => { setQuery(e.target.value); setPage(0); }} placeholder="ID atau isi sumber"/></label><p className="small muted">{filtered.length} cocok dari {records.length} bukti terkait · menampilkan {Math.min(page * 6 + 1, filtered.length)}–{Math.min((page + 1) * 6, filtered.length)}</p><div className="evidence-stack">{filtered.slice(page * 6, (page + 1) * 6).map(e => <EvidenceCard key={e.id} evidence={e}/>)}</div><div className="pagination"><button disabled={!page} onClick={() => setPage(p => p - 1)}>Bukti sebelumnya</button><button disabled={(page + 1) * 6 >= filtered.length} onClick={() => setPage(p => p + 1)}>Bukti berikutnya</button></div></>;
}
export function EvidencePanel({ context, selection, onClear }: { context: DealContext | null; selection: Selection; onClear: () => void }) {
  let title = 'Telusuri alasannya';
  let subtitle = 'Pilih bukti, node, atau relasi untuk melihat sumbernya.';
  let ids: string[] = [];
  let edge = null;
  let connected = 0;
  if (context && selection?.kind === 'evidence') { ids = [selection.id]; title = 'Bukti terpilih'; }
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
  return <aside className="inspector panel" aria-label="Panel sumber bukti"><div className="panel-heading"><span className="eyebrow">JEJAK BUKTI</span><Icon name="file" size={18}/></div>
    <h3>{title}</h3><p className="muted small">{subtitle}</p>
    {selection && <button className="text-button" onClick={onClear}>Hapus pilihan</button>}
    {edge && <div className="edge-meta"><span className={`badge ${edge.evidence_type}`}>{kindLabel[edge.evidence_type]}</span><dl><dt>Berlaku sejak</dt><dd>{dateLabel(edge.valid_from)}</dd><dt>Berlaku sampai</dt><dd>{edge.valid_to ? dateLabel(edge.valid_to) : 'Tidak dicantumkan'}</dd></dl></div>}
    {!selection && <div className="inspector-empty"><div className="paper-stack"><Icon name="file" size={32}/></div><p>Setiap keputusan dimulai<br/>dari bukti yang bisa diperiksa.</p><small>{context ? `${context.evidence.length} bukti tersedia pada deal ini.` : 'Bukti tampil setelah konteks deal tersedia.'}</small></div>}
    {selection && !ids.length && <p className="inline-warning">Belum ada ID bukti yang ditautkan{selection.kind === 'node' ? ' pada relasi node ini' : ''}.</p>}
    {!!resolved.missing.length && <p role="status" className="inline-warning">Sumber belum dapat diverifikasi untuk ID: {resolved.missing.join(', ')}.</p>}
    {!!resolved.records.length && <EvidenceStack key={`${selection?.kind}:${selection?.id}`} records={resolved.records}/>}
    <div className="inspector-footnote"><Icon name="info" size={14}/><span>Inferensi adalah hasil penalaran. Periksa sumber sebelum mengambil tindakan.</span></div>
  </aside>;
}
