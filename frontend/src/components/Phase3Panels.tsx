import type { DealContext } from '../lib/contracts';
import type { Diagnostic, Finding, Priorities, PriorityItem, PipelineDiagnostic } from '../lib/phase3';
import { evidenceIds } from '../lib/phase3';
import type { GraphTarget } from '../lib/analysisView';
import { dateLabel, kindLabel, statusLabel } from '../lib/format';
import { TextList } from './AnalysisReport';

type OpenEvidence = (id: string) => void;
export function Sources({ ids, onEvidence }: { ids: string[]; onEvidence: OpenEvidence }) {
  return <details className="report-disclosure source-links"><summary>Sumber ({new Set(ids).size})</summary><div className="source-chips">{[...new Set(ids)].map(id => <button className="text-button" key={id} onClick={() => onEvidence(id)}>{id}</button>)}</div>{!ids.length && <p className="muted">Tidak ada sumber ditautkan pada field ini; bukan konfirmasi bebas risiko.</p>}</details>;
}
/** Preserve arbitrary producer provenance without flattening null, fact or inferred fields. */
export function DetailData({ value, onEvidence, field = '' }: { value: unknown; onEvidence: OpenEvidence; field?: string }) {
  if (field.endsWith('evidence_ids') && Array.isArray(value)) return <Sources ids={value as string[]} onEvidence={onEvidence}/>;
  if (field.endsWith('evidence_id') && typeof value === 'string') return <button className="text-button" onClick={() => onEvidence(value)}>{value}</button>;
  if (value === null || value === undefined) return <span className="muted">Belum diketahui / tidak tersedia</span>;
  if (Array.isArray(value)) return value.length ? <div className="detail-array">{value.map((v,i) => <div key={i}><DetailData value={v} onEvidence={onEvidence}/></div>)}</div> : <span className="muted">Tidak dicantumkan (daftar kosong)</span>;
  if (typeof value === 'object') return <dl className="detail-data">{Object.entries(value).map(([key,v]) => <div key={key}><dt>{key.replaceAll('_',' ')}</dt><dd>{v !== null && typeof v === 'object' && !key.endsWith('evidence_ids') ? <details><summary>Buka rincian {key.replaceAll('_',' ')}</summary><DetailData value={v} field={key} onEvidence={onEvidence}/></details> : <DetailData value={v} field={key} onEvidence={onEvidence}/>}</dd></div>)}</dl>;
  return <span>{String(value)}</span>;
}
export function Methodology({ data }: { data: Priorities }) {
  return <details className="panel methodology"><summary>Metode & keterbatasan ranking · {data.methodology.label}</summary><p>{data.methodology.description}</p><h4>Urutan aturan</h4><TextList items={data.methodology.ordered_rules} empty="Tidak dicantumkan"/><h4>Pemecah nilai sama</h4><TextList items={data.methodology.tie_breakers} empty="Tidak dicantumkan"/><h4>Keterbatasan metode & pipeline</h4><TextList items={[...data.methodology.limitations,...data.limitations]} empty="Tidak dicantumkan"/><details className="raw-source"><summary>Seluruh rincian metode, termasuk bobot</summary><pre>{JSON.stringify(data.methodology,null,2)}</pre></details></details>;
}
export function PriorityPanel({ item, context, onEvidence, onGraph }: { item: PriorityItem; context: DealContext; onEvidence: OpenEvidence; onGraph: (t: GraphTarget) => void }) {
  return <section className="panel priority-panel" aria-label="Alasan prioritas"><div className="panel-heading"><h3>Prioritas #{item.rank} · {item.priority_kind}</h3><span className="badge rules">{statusLabel[item.analysis_status]}</span></div><p className="muted">Sumber: ranking pipeline rules. Ready berarti hasil aturan tersedia, bukan approval atau janji closing.</p><TextList items={item.rationale} empty="Alasan belum dicantumkan"/>
    <details className="report-disclosure"><summary>Faktor, nilai & pengaruh ({item.factors.length})</summary><div className="priority-factors">{item.factors.map((f,i) => <article key={i}><h4>{f.name.replaceAll('_',' ')}</h4><strong>{f.value === null ? 'Belum tersedia (null)' : String(f.value)}</strong><p>{f.effect}</p><Sources ids={f.evidence_ids} onEvidence={onEvidence}/></article>)}</div></details>
    <details className="report-disclosure priority-paths"><summary>Jalur bukti ranking ({item.evidence_paths.length})</summary><p className="small muted">Panah menunjukkan arah relasi asli. Penelusuran dapat melawan arah panah tanpa mengubah arti relasi. Klik relasi untuk fokus graph dan buktinya.</p>{item.evidence_paths.map((p,i) => <article key={i} className="evidence-path"><p className="mono">{p.node_ids.map((id,j) => j === 0 ? id : `${context.graph.edges.find(e => e.id === p.edge_ids[j-1])?.target === id ? ' → ' : ' ← '}${id}`).join('')}</p>{p.edge_ids.map(id => { const e = context.graph.edges.find(e => e.id === id)!; return <button className="source-edge" key={id} onClick={() => onGraph({kind:'edge',id})}><strong>{e.source} → {e.target}</strong><small>{e.relation} · {kindLabel[e.evidence_type]}</small><small>{dateLabel(e.valid_from)} — {e.valid_to ? dateLabel(e.valid_to) : 'Akhir tidak dicantumkan'}</small></button>; })}<Sources ids={p.evidence_ids} onEvidence={onEvidence}/></article>)}</details>
    <details className="report-disclosure"><summary>Keterbatasan prioritas deal</summary><TextList items={item.limitations} empty="Tidak dicantumkan"/></details><Sources ids={item.evidence_ids} onEvidence={onEvidence}/>
  </section>;
}
function FindingCard({ item, onEvidence }: { item: Finding; onEvidence: OpenEvidence }) {
  const extra = Object.fromEntries(Object.entries(item).filter(([k]) => !['finding_id','category','fact','interpretation','interpretation_type','evidence_ids','missing_information','follow_up_implication'].includes(k)));
  return <article className="diagnostic-finding"><h4>{item.finding_id}</h4><span className="badge">{item.category === 'business_anomaly' ? 'Anomali bisnis' : 'Informasi kurang'}</span><h5>Fakta yang dilaporkan</h5><p>{item.fact}</p><h5>Interpretasi · {kindLabel[item.interpretation_type]}</h5><p>{item.interpretation}</p><h5>Informasi belum diketahui</h5><TextList items={item.missing_information} empty="Tidak dicantumkan; bukan konfirmasi bebas risiko."/><h5>Implikasi pemeriksaan informasi</h5><TextList items={item.follow_up_implication} empty="Tidak dicantumkan."/><Sources ids={evidenceIds(item)} onEvidence={onEvidence}/><details className="report-disclosure"><summary>Seluruh rincian & provenance</summary><DetailData value={extra} onEvidence={onEvidence}/></details></article>;
}
export function DiagnosticPanel({ data, onEvidence }: { data: Diagnostic; onEvidence: OpenEvidence }) {
  const m = data.metrics;
  return <section className="panel diagnostic-panel" aria-label="Diagnostic deal"><h3>Diagnostic · {data.account_id}</h3><p className="muted">Pemeriksaan data dari layanan initial-analysis. Implikasi pemeriksaan tidak mengganti rekomendasi ranking atau analisis sesi.</p>
    <div className="diagnostic-metrics"><div><span>Umur deal</span><strong>{m.deal_age_days === null ? 'Belum tersedia' : `${m.deal_age_days} hari`}</strong></div><div><span>Umur tahap</span><strong>{m.stage_age_days === null ? 'Belum tersedia' : `${m.stage_age_days} hari`}</strong></div><div><span>Interaksi eksternal terakhir</span><strong>{dateLabel(m.interactions.customer.last_date)}</strong></div></div><p className="small muted">Interaksi eksternal termasuk outbound sales, bukan otomatis balasan terakhir pelanggan. Null bukan nol atau nihil risiko.</p>
    <details className="report-disclosure"><summary>Seluruh metrik, cakupan & sumber</summary><DetailData value={m} onEvidence={onEvidence}/></details>
    <h4>Temuan ({data.findings.length})</h4>{data.findings.map(f => <details className="report-disclosure" key={f.finding_id}><summary>{f.finding_id}</summary><FindingCard item={f} onEvidence={onEvidence}/></details>)}{!data.findings.length && <p className="muted">Tidak ada temuan dicantumkan, bukan bukti tidak ada risiko.</p>}
    <h4>Kandidat referensi ({data.reference_candidates.length})</h4><p className="small muted">Kandidat belum berarti sesuai, bersedia, atau mengizinkan kontak. Periksa pengalaman terbaru dan izin sebelum perkenalan.</p>{data.reference_candidates.map(f => <details className="report-disclosure" key={f.finding_id}><summary>{f.finding_id}</summary><FindingCard item={f} onEvidence={onEvidence}/></details>)}
    <details className="report-disclosure"><summary>Batas diagnostic</summary><TextList items={data.boundaries} empty="Tidak dicantumkan"/></details><Sources ids={evidenceIds(data)} onEvidence={onEvidence}/>
  </section>;
}
export function Statistics({ data, onEvidence }: { data: PipelineDiagnostic; onEvidence: OpenEvidence }) {
  const s = data.statistical_assessment;
  return <section className="panel statistics" aria-label="Penilaian statistik"><h3>Anomali bisnis ≠ outlier statistik</h3><p>Anomali bisnis adalah hambatan atau ketidakselarasan bersumber. Outlier statistik memerlukan distribusi pembanding dan metode.</p><strong>Outlier statistik: belum dinilai ({s.status})</strong><p>{s.reason}</p><details className="report-disclosure"><summary>Cakupan, metode & sumber statistik</summary><DetailData value={s} onEvidence={onEvidence}/></details></section>;
}
