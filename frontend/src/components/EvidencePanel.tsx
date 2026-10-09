import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import type { DealContext, Evidence } from '../lib/contracts';
import { evidenceExcerpt } from '../lib/graphView';
import { evidenceGraphLinks } from '../lib/analysisView';
import type { GraphTarget } from '../lib/analysisView';
import { resolveEvidence } from '../lib/contracts';
import { dateLabel, kindLabel } from '../lib/format';
import { evidenceTitle, interactionMeta, nodeName, nodeTypeLabel, relationPhrase } from '../lib/present';
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
    {links.node ? <button className="button secondary small" onClick={() => onGraph({ kind: 'node', id: links.node!.id })}><Icon name="graph" size={16}/>Tampilkan di peta hubungan: {links.node.id}</button> : <p className="small muted">Record ini tidak punya titik unik di peta hubungan.</p>}
    {links.edges.length ? <details className="disclosure compact"><summary>Relasi yang memakai record ini <span className="count">{links.edges.length}</span></summary><p className="small muted">Pilih relasi untuk melihat kedua ujung dan buktinya di peta. {page * 6 + 1}–{Math.min((page + 1) * 6, links.edges.length)} dari {links.edges.length}</p>{links.edges.slice(page * 6, (page + 1) * 6).map(edge => <button className="edge-row" key={edge.id} onClick={() => onGraph({ kind: 'edge', id: edge.id })}><span><strong>{relationPhrase(edge.relation)}</strong><span className="mono">{edge.source} → {edge.target} · {edge.relation}</span></span><span className={`tag ${edge.evidence_type}`}>{kindLabel[edge.evidence_type]}</span><span className="muted small">{dateLabel(edge.valid_from)}</span></button>)}{links.edges.length > 6 && <div className="pagination"><button disabled={!page} onClick={() => setPage(p => p - 1)}>Relasi sebelumnya</button><button disabled={(page + 1) * 6 >= links.edges.length} onClick={() => setPage(p => p + 1)}>Relasi berikutnya</button></div>}</details> : <p className="inline-warning">Tidak ada relasi di peta yang merujuk record ini. Record tetap bisa diperiksa; hubungan tidak dibuat-buat.</p>}
  </div>;
}
export function EvidenceCard({ evidence, context, onGraph, hideTitle = false }: { evidence: Evidence; context: DealContext; onGraph: (target: GraphTarget) => void; hideTitle?: boolean }) {
  const url = sourceUrl(evidence.source_file);
  const excerpt = evidenceExcerpt(evidence.excerpt);
  const { kind, title } = evidenceTitle(evidence), meta = interactionMeta(evidence);
  return <article className="evidence-card">
    <div className="evidence-card-head"><span className="tag">{kind}</span><span className={`tag ${evidence.evidence_type}`}>{kindLabel[evidence.evidence_type]}</span></div>
    {!hideTitle && <h4>{title}</h4>}
    <p className="evidence-date"><Icon name="clock" size={14}/>{dateLabel(evidence.date)}{meta?.from && <span> · dari {meta.from}</span>}{meta?.to && <span> · ke {meta.to}</span>}</p>
    <blockquote>{excerpt.text || 'Kutipan belum tersedia.'}</blockquote>
    <details className="raw-source"><summary>Detail sumber · {evidence.source_id}</summary>
      <dl className="source-details"><div><dt>File sumber</dt><dd>{url ? <a href={url} target="_blank" rel="noreferrer">{evidence.source_file}<span className="visually-hidden"> (membuka tab baru)</span></a> : evidence.source_file}</dd></div><div><dt>ID record</dt><dd className="mono">{evidence.source_id}</dd></div><div><dt>ID bukti</dt><dd className="mono">{evidence.id}</dd></div></dl>
      {excerpt.structured && <><p className="small muted">Record asli (JSON)</p><pre>{evidence.excerpt}</pre></>}
    </details>
    <SourceGraphLinks evidence={evidence} context={context} onGraph={onGraph}/>
  </article>;
}
function EvidenceStack({ records, context, onGraph, hideTitle = false }: { records: Evidence[]; context: DealContext; onGraph: (target: GraphTarget) => void; hideTitle?: boolean }) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);
  const filtered = records.filter(e => `${e.id} ${e.source_id} ${e.excerpt}`.toLowerCase().includes(query.trim().toLowerCase()));
  return <>{records.length > 1 && <><label className="field">Cari di bukti ini<input value={query} onChange={e => { setQuery(e.target.value); setPage(0); }} placeholder="ID atau isi sumber"/></label><p className="small muted">{filtered.length} cocok dari {records.length} bukti · menampilkan {Math.min(page * 6 + 1, filtered.length)}–{Math.min((page + 1) * 6, filtered.length)}</p></>}<div className="evidence-stack">{filtered.slice(page * 6, (page + 1) * 6).map(e => <EvidenceCard key={e.id} evidence={e} context={context} onGraph={onGraph} hideTitle={hideTitle}/>)}</div>{records.length > 6 && <div className="pagination"><button disabled={!page} onClick={() => setPage(p => p - 1)}>Bukti sebelumnya</button><button disabled={(page + 1) * 6 >= filtered.length} onClick={() => setPage(p => p + 1)}>Bukti berikutnya</button></div>}</>;
}

/** Evidence, node or relation details. Titles are built from record fields; IDs stay visible. */
export function EvidenceInspector({ context, selection, titleId, onGraph }: { context: DealContext; selection: NonNullable<Selection>; titleId: string; onGraph: (target: GraphTarget) => void }) {
  let title = selection.id, subtitle = '', ids: string[] = [];
  const edge = selection.kind === 'edge' ? context.graph.edges.find(e => e.id === selection.id) ?? null : null;
  const related = selection.kind === 'node' ? context.graph.edges.filter(e => e.source === selection.id || e.target === selection.id) : edge ? [edge] : [];
  const nodeLabel = (id: string) => { const node = context.graph.nodes.find(n => n.id === id); return node ? nodeName(node, context) : id; };
  if (selection.kind === 'evidence') {
    const record = context.evidence.find(e => e.id === selection.id);
    ids = [selection.id];
    // The card below repeats kind, date and sender, so the heading carries the title only.
    if (record) title = evidenceTitle(record).title; else subtitle = 'Record belum ditemukan dalam data deal ini';
  }
  if (selection.kind === 'edge') {
    if (edge) { title = relationPhrase(edge.relation); subtitle = `${nodeLabel(edge.source)} → ${nodeLabel(edge.target)}`; ids = edge.evidence_ids; } else subtitle = 'Relasi belum ditemukan dalam data deal ini';
  }
  if (selection.kind === 'node') {
    const node = context.graph.nodes.find(n => n.id === selection.id);
    title = node ? nodeName(node, context) : selection.id;
    subtitle = `${node ? nodeTypeLabel(node.type) : 'Titik'} · ${related.length} relasi terkait · ${selection.id}`;
    ids = related.flatMap(e => e.evidence_ids);
  }
  const resolved = resolveEvidence(ids, context.evidence);
  return <>
    <h3 id={titleId} tabIndex={-1} className="drawer-title">{title}</h3>
    {subtitle && <p className="muted small">{subtitle}</p>}
    {edge && <div className="edge-meta"><span className={`tag ${edge.evidence_type}`}>{kindLabel[edge.evidence_type]}</span><dl><div><dt>Kode relasi</dt><dd className="mono">{edge.relation}</dd></div><div><dt>Arah asli</dt><dd className="mono">{edge.source} → {edge.target}</dd></div><div><dt>Berlaku sejak</dt><dd>{dateLabel(edge.valid_from)}</dd></div><div><dt>Berlaku sampai</dt><dd>{edge.valid_to ? dateLabel(edge.valid_to) : 'Tidak dicantumkan'}</dd></div></dl></div>}
    {!ids.length && <p className="inline-warning">Belum ada bukti yang ditautkan{selection.kind === 'node' ? ' pada relasi titik ini' : ''}.</p>}
    {!!resolved.missing.length && <p role="status" className="inline-warning">Sumber belum dapat diverifikasi untuk ID: {resolved.missing.join(', ')}.</p>}
    {!!resolved.records.length && <EvidenceStack key={`${selection.kind}:${selection.id}`} records={resolved.records} context={context} onGraph={onGraph} hideTitle={selection.kind === 'evidence'}/>}
    {(resolved.records.some(e => e.evidence_type === 'inferred') || related.some(e => e.evidence_type === 'inferred')) && <p className="drawer-footnote"><Icon name="info" size={15}/><span>“Dugaan dari hubungan data” adalah hasil penalaran, bukan fakta langsung. Periksa sumbernya sebelum bertindak.</span></p>}
  </>;
}

/** Side panel on wide screens (non-modal, Escape closes); modal sheet on narrow screens. */
export function EvidenceDrawer({ mode, titleId, onClose, children }: { mode: 'side' | 'sheet'; titleId: string; onClose: () => void; children: ReactNode }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const close = useRef(onClose); close.current = onClose;
  useEffect(() => {
    if (mode !== 'sheet') return;
    const element = dialog.current;
    if (element && !element.open) element.showModal();
    return () => { if (element?.open) element.close(); };
  }, [mode]);
  useEffect(() => {
    if (mode !== 'side') return;
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape' && !event.defaultPrevented) close.current(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [mode]);
  const body = <div className="drawer-body">
    <div className="drawer-bar"><span>Bukti & sumber</span><button className="icon-button" aria-label="Tutup panel bukti" onClick={() => close.current()}><Icon name="close" size={20}/></button></div>
    {children}
  </div>;
  if (mode === 'sheet') return <dialog ref={dialog} className="drawer sheet" aria-labelledby={titleId} onCancel={event => { event.preventDefault(); close.current(); }} onClick={event => { if (event.target === event.currentTarget) close.current(); }}>{body}</dialog>;
  return <aside className="drawer side" aria-labelledby={titleId}>{body}</aside>;
}
