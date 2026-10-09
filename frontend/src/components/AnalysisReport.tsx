import { useId, useState } from 'react';
import type { ReactNode } from 'react';
import type { DealContext, Recommendation } from '../lib/contracts';
import { explanationGroups } from '../lib/analysisView';
import { dateLabel } from '../lib/format';
import { employeeFromContext, engineLabel, evidenceTitle, interactionMeta, orderEvidence, splitUnknowns } from '../lib/present';
import { Icon } from './Icon';

type OpenEvidence = (id: string) => void;
export function TextList({ items, empty }: { items: string[]; empty: string }) {
  return items.length ? <ul className="report-list">{items.map((item, i) => <li key={i}>{item}</li>)}</ul> : <p className="muted">{empty}</p>;
}

/** Name only from the employees.csv row with the same employee_id; otherwise the ID, labelled as such. */
export function OwnerLabel({ id, context, onEvidence }: { id: string | null; context: DealContext | null; onEvidence: OpenEvidence }) {
  if (!id) return <span>Belum ditentukan oleh analisis</span>;
  const employee = employeeFromContext(context, id);
  if (!employee) return <span><strong>ID karyawan {id}</strong> <span className="muted">· nama tidak tercantum pada data deal ini</span></span>;
  return <span className="owner"><strong>{employee.name}</strong>{employee.title && <span className="muted"> · {employee.title}</span>} <span className="id-chip">{id}</span> <button className="link-button" aria-label={`Lihat data karyawan ${employee.name}`} onClick={() => onEvidence(employee.evidenceId)}>Lihat sumber</button></span>;
}

/** Layer 1: what to do, who owns it, the next target, and conditions that must stay next to the action. */
export function ActionSummary({ recommendation: r, context, fixture, onEvidence, actions }: { recommendation: Recommendation; context: DealContext | null; fixture: boolean; onEvidence: OpenEvidence; actions?: ReactNode }) {
  const titleId = useId();
  const { specific } = splitUnknowns(r, context);
  return <section className="action-card" aria-labelledby={titleId}>
    <div className="action-card-head"><h3 id={titleId}>Tindakan yang disarankan</h3><span className={`tag engine ${r.engine_mode}`}>{engineLabel[r.engine_mode]}{fixture ? ' · fixture' : ''}</span></div>
    <p className="action-text">{r.action || 'Tindakan belum dicantumkan oleh analisis.'}</p>
    <dl className="action-facts">
      <div><dt><Icon name="user" size={16}/>Penanggung jawab</dt><dd><OwnerLabel id={r.owner_id} context={context} onEvidence={onEvidence}/></dd></div>
      <div><dt><Icon name="target" size={16}/>Target langkah berikutnya</dt><dd>{r.milestone || 'Belum ditentukan oleh analisis.'}</dd></div>
    </dl>
    {r.approvals_needed.length ? <div className="approval-box pending">
      <h4><Icon name="alert" size={17}/>Persetujuan yang diperlukan <span className="count">{r.approvals_needed.length}</span></h4>
      <TextList items={r.approvals_needed} empty=""/>
    </div> : <p className="approval-line"><Icon name="info" size={16}/><span><strong>Persetujuan yang diperlukan:</strong> tidak ada yang dicantumkan. Ini tidak berarti tindakan sudah disetujui.</span></p>}
    {!!specific.length && <div className="check-box"><h4><Icon name="info" size={17}/>Yang masih perlu dipastikan</h4><TextList items={specific} empty=""/></div>}
    {actions && <div className="action-buttons">{actions}</div>}
  </section>;
}

/** Records cited by the recommendation, with human titles from their own fields. */
export function RecommendationSources({ ids, context, onEvidence }: { ids: string[]; context: DealContext; onEvidence: OpenEvidence }) {
  const [page, setPage] = useState(0);
  const unique = [...new Set(ids)];
  const byId = new Map(context.evidence.map(e => [e.id, e]));
  const records = orderEvidence(unique.flatMap(id => byId.has(id) ? [byId.get(id)!] : []));
  const missing = unique.filter(id => !byId.has(id));
  const size = 6, shown = records.slice(page * size, (page + 1) * size);
  return <section className="reason-section" aria-label="Bukti yang dirujuk saran">
    <h3>Bukti yang dirujuk saran ini <span className="count">{unique.length}</span></h3>
    <p className="note">Percakapan ditampilkan lebih dulu. Pilih untuk membaca record aslinya.</p>
    {!unique.length && <p className="inline-warning">Analisis belum menautkan sumber.</p>}
    {!!missing.length && <p className="inline-warning">Sumber belum ditemukan dalam data deal: {missing.join(', ')}.</p>}
    <ul className="evidence-list">{shown.map(e => {
      const { kind, title } = evidenceTitle(e), meta = interactionMeta(e);
      return <li key={e.id}><button className="evidence-item" onClick={() => onEvidence(e.id)}>
        <span className="evidence-item-head"><span className="tag">{kind}</span><span className="muted">{dateLabel(e.date)}</span></span>
        <strong>{title}</strong>
        {meta?.message && <span className="evidence-quote">“{meta.message}”</span>}
        <span className="evidence-item-foot"><span className="id-chip">{e.source_id}</span><span className="link-text">Buka bukti <Icon name="arrow" size={14}/></span></span>
      </button></li>;
    })}</ul>
    {records.length > size && <div className="pagination"><button disabled={!page} onClick={() => setPage(p => p - 1)}>Bukti sebelumnya</button><span>{page * size + 1}–{Math.min((page + 1) * size, records.length)} dari {records.length}</span><button disabled={(page + 1) * size >= records.length} onClick={() => setPage(p => p + 1)}>Bukti berikutnya</button></div>}
  </section>;
}

function Precedent({ decision, context, onEvidence }: { decision: Record<string, unknown>; context: DealContext; onEvidence: OpenEvidence }) {
  const text = (value: unknown) => typeof value === 'string' || typeof value === 'number' ? String(value) : 'Tidak dicantumkan';
  const id = text(decision.decision_id);
  const records = context.evidence.filter(e => e.source_id === id);
  return <article className="precedent">
    <div className="precedent-head"><strong>{id}</strong><span className="tag">{text(decision.keputusan)}</span><span>{text(decision.nilai)}</span></div>
    <p>{text(decision.alasan)}</p>
    <dl className="precedent-facts"><div><dt>Tanggal</dt><dd>{text(decision.tanggal)}</dd></div><div><dt>Akun / deal</dt><dd>{text(decision.account_id)} / {text(decision.deal_id)}</dd></div><div><dt>Pemutus waktu itu</dt><dd>{text(decision.diputuskan_oleh)}</dd></div></dl>
    <div className="inline-actions">{records.map(e => <button className="link-button" key={e.id} onClick={() => onEvidence(e.id)}>Buka record {e.source_id}</button>)}</div>
    <details className="raw-source"><summary>Seluruh field keputusan</summary><pre>{JSON.stringify(decision, null, 2)}</pre></details>
  </article>;
}
export function PrecedentList({ recommendation: r, context, onEvidence }: { recommendation: Recommendation; context: DealContext; onEvidence: OpenEvidence }) {
  const referenced = new Set(r.precedent_ids);
  const missing = r.precedent_ids.filter(id => !context.candidate_decisions.some(d => String(d.decision_id) === id));
  const used = context.candidate_decisions.filter(d => referenced.has(String(d.decision_id)));
  const others = context.candidate_decisions.filter(d => !referenced.has(String(d.decision_id)));
  const note = <p className="note">Keputusan lama hanya pembanding. Persetujuan pada kasus lama tidak otomatis berlaku untuk deal ini.</p>;
  // Nothing referenced and nothing else in the data: the section would only say "none", so it is left out.
  if (!r.precedent_ids.length && !others.length) return null;
  return <section className="reason-section" aria-label="Keputusan terdahulu">
    {!!r.precedent_ids.length && <>
      <h3>Keputusan terdahulu <span className="count">{r.precedent_ids.length}</span></h3>
      {note}
      {!!missing.length && <p className="inline-warning">Keputusan belum ditemukan dalam data deal: {missing.join(', ')}.</p>}
      <div className="precedent-list">{used.map((d, i) => <Precedent key={i} decision={d} context={context} onEvidence={onEvidence}/>)}</div>
    </>}
    {!!others.length && <details className="disclosure"><summary>{r.precedent_ids.length ? 'Keputusan lain di data yang tidak dirujuk' : 'Keputusan terdahulu di data (tidak dirujuk saran ini)'} <span className="count">{others.length}</span></summary>{!r.precedent_ids.length && note}<div className="precedent-list">{others.map((d, i) => <Precedent key={i} decision={d} context={context} onEvidence={onEvidence}/>)}</div></details>}
  </section>;
}

const groupLabel = { FAKTA: 'Fakta dari sumber', INTERPRETASI: 'Interpretasi analisis', SKENARIO: 'Skenario usulan (belum disepakati)', PENJELASAN: 'Penjelasan lainnya' };
/** All precedent_comparison lines, verbatim. Prefixes only choose the visual group. */
export function ExplanationGroups({ recommendation: r }: { recommendation: Recommendation }) {
  const groups = explanationGroups(r.precedent_comparison);
  return <section className="reason-section" aria-label="Penjelasan analisis">
    <h3>Penjelasan analisis</h3>
    {!r.precedent_comparison.length && <p className="muted">Penjelasan belum dicantumkan dalam respons.</p>}
    {Object.entries(groups).filter(([, lines]) => lines.length).map(([kind, lines]) => <details key={kind} className={`disclosure group-${kind.toLowerCase()}`}><summary>{groupLabel[kind as keyof typeof groupLabel]} <span className="count">{lines.length}</span></summary><TextList items={lines} empty=""/></details>)}
  </section>;
}
export function UnknownList({ recommendation, context }: { recommendation: Recommendation; context: DealContext | null }) {
  const { all } = splitUnknowns(recommendation, context);
  return <section className="reason-section" aria-label="Informasi yang belum diketahui">
    <details className="disclosure"><summary>Informasi yang belum diketahui <span className="count">{all.length}</span></summary>
      <p className="note">Hal yang tidak tercantum bukan berarti bebas risiko.</p>
      <TextList items={all} empty="Tidak dicantumkan oleh layanan; ini bukan konfirmasi bebas risiko."/>
    </details>
  </section>;
}
