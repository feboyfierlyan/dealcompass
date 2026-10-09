import { useState } from 'react';
import type { DealContext, Recommendation } from '../lib/contracts';
import { explanationGroups } from '../lib/analysisView';
import { dateLabel } from '../lib/format';

export function TextList({ items, empty }: { items: string[]; empty: string }) {
  return items.length ? <ul className="report-list">{items.map((item, i) => <li key={i}>{item}</li>)}</ul> : <p className="muted">{empty}</p>;
}
export function ContextNotes({ context }: { context: DealContext }) {
  return <details className="report-disclosure context-notes"><summary>Informasi belum diketahui dari konteks ({context.unknowns.length})</summary><TextList items={context.unknowns} empty="Tidak dicantumkan oleh layanan. Ini bukan bukti tidak ada risiko."/></details>;
}
function SourceReferences({ ids, context, onEvidence }: { ids: string[]; context: DealContext; onEvidence: (id: string) => void }) {
  const [page, setPage] = useState(0);
  const unique = [...new Set(ids)];
  return <><p className="muted">{unique.length} sumber dirujuk · pilih untuk membuka record asli, lalu telusuri graph.</p><div className="report-sources">{unique.slice(page * 8, (page + 1) * 8).map(id => {
    const evidence = context.evidence.find(e => e.id === id);
    return <button key={id} onClick={() => onEvidence(id)} aria-label={`Buka sumber ${id}`}><strong>{evidence?.source_id ?? id}</strong><small>{evidence ? `${dateLabel(evidence.date)} · ${evidence.source_file}` : 'Record belum ditemukan dalam konteks'}</small><span>Buka bukti →</span></button>;
  })}</div>{!unique.length && <p className="inline-warning">Belum ada sumber yang ditautkan oleh analisis.</p>}{unique.length > 8 && <div className="pagination"><button disabled={!page} onClick={() => setPage(p => p - 1)}>Sumber sebelumnya</button><span>{page * 8 + 1}–{Math.min((page + 1) * 8, unique.length)} / {unique.length}</span><button disabled={(page + 1) * 8 >= unique.length} onClick={() => setPage(p => p + 1)}>Sumber berikutnya</button></div>}</>;
}
function Precedent({ decision, context, onEvidence }: { decision: Record<string, unknown>; context: DealContext; onEvidence: (id: string) => void }) {
  const text = (value: unknown) => typeof value === 'string' || typeof value === 'number' ? String(value) : 'Tidak dicantumkan';
  const id = text(decision.decision_id);
  const records = context.evidence.filter(e => e.source_id === id);
  return <details className="precedent"><summary><strong>{id}</strong><span>{text(decision.keputusan)} · {text(decision.nilai)}</span></summary><div className="precedent-body"><p>{text(decision.alasan)}</p><dl><dt>Tanggal</dt><dd>{text(decision.tanggal)}</dd><dt>Akun / deal</dt><dd>{text(decision.account_id)} / {text(decision.deal_id)}</dd><dt>Pemutus historis</dt><dd>{text(decision.diputuskan_oleh)}</dd></dl>{records.map(e => <button className="text-button" key={e.id} onClick={() => onEvidence(e.id)}>Buka sumber {e.id}</button>)}<details className="raw-source"><summary>Seluruh field keputusan</summary><pre>{JSON.stringify(decision, null, 2)}</pre></details></div></details>;
}
export function AnalysisReport({ recommendation: r, context, fixture, onEvidence }: { recommendation: Recommendation; context: DealContext; fixture: boolean; onEvidence: (id: string) => void }) {
  const groups = explanationGroups(r.precedent_comparison);
  const labels = { FAKTA: 'Fakta dari sumber', INTERPRETASI: 'Interpretasi analisis', SKENARIO: 'Skenario usulan', PENJELASAN: 'Penjelasan lainnya' };
  const referenced = new Set(r.precedent_ids);
  const missing = r.precedent_ids.filter(id => !context.candidate_decisions.some(d => d.decision_id === id));
  const extra = r.unknowns.filter(item => !context.unknowns.includes(item));
  const allUnknowns = [...new Set([...context.unknowns, ...r.unknowns])];
  return <article className="analysis-report" aria-label="Hasil analisis">
    <section className="panel action-panel has-action report-step"><div className="panel-heading"><h3><span className="step-number">1</span>Tindakan usulan</h3><span className={`badge engine ${r.engine_mode}`}>{({ rules: 'Rules · aturan', jev: 'Jev', replay: 'Replay' })[r.engine_mode]}{fixture ? ' · fixture' : ''}</span></div><p className="proposal-text">{r.action || 'Tindakan belum dicantumkan.'}</p>
      <div className="report-owner"><h4><span className="step-number">2</span>Penanggung jawab</h4><strong>{r.owner_id ?? 'Belum ditentukan'}</strong></div>
      <div className="report-milestone"><h4><span className="step-number">3</span>Milestone</h4><p>{r.milestone || 'Belum ditentukan.'}</p></div>
      <div className="report-approval"><h4><span className="step-number">4</span>Persetujuan yang diperlukan <span className="count">{r.approvals_needed.length}</span></h4><TextList items={r.approvals_needed} empty="Respons tidak mencantumkan persetujuan tambahan. Ini bukan bukti bahwa tindakan telah disetujui."/></div>
    </section>
    <section className="panel report-step"><h3><span className="step-number">5</span>Penjelasan & preseden</h3><p className="muted">Buka penjelasan lengkap dari analisis. Persetujuan kasus lama tidak otomatis berlaku pada deal ini.</p>
      {Object.entries(groups).filter(([, lines]) => lines.length).map(([kind, lines]) => <details key={kind} className={`report-disclosure explanation ${kind.toLowerCase()}`}><summary>{labels[kind as keyof typeof labels]} ({lines.length})</summary><TextList items={lines} empty="Belum dicantumkan."/></details>)}
      {!r.precedent_comparison.length && <p>Penjelasan belum dicantumkan dalam respons.</p>}
      <h4>Preseden yang dirujuk ({r.precedent_ids.length})</h4>
      {!!missing.length && <p className="inline-warning">Preseden belum ditemukan dalam konteks: {missing.join(', ')}.</p>}
      {!r.precedent_ids.length && <p className="muted">Analisis tidak merujuk preseden. Periksa keterbatasan di bawah.</p>}
      {context.candidate_decisions.filter(d => referenced.has(String(d.decision_id))).map((d, i) => <Precedent key={i} decision={d} context={context} onEvidence={onEvidence}/>)}
      <details className="report-disclosure"><summary>Kandidat lain dari konteks ({context.candidate_decisions.filter(d => !referenced.has(String(d.decision_id))).length})</summary>{context.candidate_decisions.filter(d => !referenced.has(String(d.decision_id))).map((d, i) => <Precedent key={i} decision={d} context={context} onEvidence={onEvidence}/>)}</details>
    </section>
    <section className="panel report-step report-unknowns"><h3><span className="step-number">6</span>Informasi belum diketahui <span className="count">{allUnknowns.length}</span></h3><p>Periksa keterbatasan sebelum bertindak. Respons diterima tidak berarti bukti sudah cukup.</p>
      {!!extra.length && <TextList items={extra} empty=""/>}<ContextNotes context={context}/>
      {!allUnknowns.length && <p className="muted">Tidak dicantumkan oleh layanan; bukan konfirmasi bebas risiko.</p>}
    </section>
    <section className="panel report-step"><h3><span className="step-number">7</span>Sumber pendukung</h3><SourceReferences key={r.deal_id + r.evidence_ids.join('|')} ids={r.evidence_ids} context={context} onEvidence={onEvidence}/></section>
  </article>;
}
