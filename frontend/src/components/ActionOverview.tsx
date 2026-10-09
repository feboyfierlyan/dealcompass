import { useState } from 'react';
import type { DealContext, Recommendation } from '../lib/contracts';
import type { PriorityItem } from '../lib/phase3';
import { employeeFromContext, engineLabel, gateSummary } from '../lib/present';
import { taskHeading } from '../lib/planning';
import { ActionSummary } from './AnalysisReport';
import { FollowUpPlan } from './FollowUpPlan';
import { Icon } from './Icon';

export function ActionOverview({ recommendation: r, context, priority, source, snapshot, fixture, onEvidence, onReasons, onShowPaths }: {
  recommendation: Recommendation; context: DealContext | null; priority: PriorityItem | null; source: 'priority' | 'session' | null;
  snapshot: string | null; fixture: boolean; onEvidence: (id: string) => void; onReasons: () => void; onShowPaths: () => void;
}) {
  const [planning, setPlanning] = useState(false);
  const heading = taskHeading(priority, source), owner = employeeFromContext(context, r.owner_id);
  return <div className="action-board">
    <section className="next-move" aria-label="Langkah berikutnya">
      <div className="next-move-top"><span className="eyebrow"><Icon name="target" size={15}/>Langkah berikutnya</span><span className={`tag engine ${r.engine_mode}`}>{engineLabel[r.engine_mode]}{fixture ? ' · fixture' : ''}</span></div>
      <h3>{heading.title}</h3>
      <div className="move-owner"><span className="person-avatar" aria-hidden="true">{owner?.name.split(' ').map(x => x[0]).slice(0,2).join('') ?? '—'}</span><span><strong>{owner?.name ?? r.owner_id ?? 'Belum ditentukan'}</strong><span>Penanggung jawab{owner?.title ? ` · ${owner.title}` : ''}</span></span></div>
      <div className="move-target"><span className="eyebrow">Hasil yang ingin dicapai</span><p>{r.milestone || 'Target belum dicantumkan oleh analisis.'}</p></div>
      <div className="move-boundary"><Icon name="info" size={18}/><div><strong>Pastikan sebelum bertindak</strong><p>{heading.note}</p>{!!r.approvals_needed.length && <details><summary>Persetujuan yang diperlukan ({r.approvals_needed.length})</summary><ul>{r.approvals_needed.map((x,i) => <li key={i}>{x}</li>)}</ul></details>}</div></div>
      <div className="move-cta"><button className="button primary" onClick={() => setPlanning(true)}>Siapkan tindak lanjut<Icon name="arrow" size={18}/></button><p>Buka rencana lengkap untuk diperiksa dan disalin.</p></div>
      <details className="full-proposal"><summary>Baca usulan lengkap dan batasannya<Icon name="chevron" size={16}/></summary><p className="original-gate">Syarat pada analisis prioritas: {gateSummary(priority) ?? 'Belum dicantumkan'}</p><ActionSummary recommendation={r} context={context} fixture={fixture} onEvidence={onEvidence}/></details>
    </section>
    <section className="proof-entry" aria-label="Dasar saran"><span className="proof-symbol"><Icon name="graph" size={24}/></span><div><span className="eyebrow">CONTEXT GRAPH</span><h3>Kenapa langkah ini?</h3><p>Telusuri sumber dan hubungan data di balik saran.</p></div><dl className="proof-stats"><div><dt>Bukti yang dirujuk</dt><dd>{new Set(r.evidence_ids).size}</dd></div><div><dt>Jalur prioritas</dt><dd>{priority?.evidence_paths.length ?? '—'}</dd></div></dl><p className="proof-caveat">Jumlah sumber bukan ukuran kepastian. Buka bukti untuk memeriksa konteksnya.</p><div className="proof-entry-actions"><button className="button secondary small" onClick={onReasons}>Lihat alasan & bukti<Icon name="arrow" size={15}/></button><button className="text-button small" onClick={onShowPaths} disabled={!priority?.evidence_paths.length}>{source === 'session' ? 'Peta dari analisis prioritas' : 'Lihat peta hubungan'}<Icon name="graph" size={15}/></button></div></section>
    {planning && <FollowUpPlan recommendation={r} context={context} snapshot={snapshot} onClose={() => setPlanning(false)}/>}
  </div>;
}
