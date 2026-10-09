import type { DealContext, GraphEdge } from '../lib/contracts';
import type { Diagnostic, EvidencePath, Finding, Priorities, PriorityItem, PipelineDiagnostic } from '../lib/phase3';
import { evidenceIds } from '../lib/phase3';
import { dateLabel, kindLabel } from '../lib/format';
import { pathArrows, pathSteps, priorityKindLabel, relationPhrase } from '../lib/present';
import { TextList } from './AnalysisReport';
import { Icon } from './Icon';

type OpenEvidence = (id: string) => void;
export function Sources({ ids, onEvidence, label = 'Sumber' }: { ids: string[]; onEvidence: OpenEvidence; label?: string }) {
  const unique = [...new Set(ids)];
  return <details className="disclosure compact source-links"><summary>{label} <span className="count">{unique.length}</span></summary><div className="source-chips">{unique.map(id => <button className="id-button" key={id} onClick={() => onEvidence(id)}>{id}</button>)}</div>{!ids.length && <p className="muted">Tidak ada sumber yang ditautkan pada bagian ini; bukan konfirmasi bebas risiko.</p>}</details>;
}
/** Preserve arbitrary producer provenance without flattening null, fact or inferred fields. */
export function DetailData({ value, onEvidence, field = '' }: { value: unknown; onEvidence: OpenEvidence; field?: string }) {
  if (field.endsWith('evidence_ids') && Array.isArray(value)) return <Sources ids={value as string[]} onEvidence={onEvidence}/>;
  if (field.endsWith('evidence_id') && typeof value === 'string') return <button className="id-button" onClick={() => onEvidence(value)}>{value}</button>;
  if (value === null || value === undefined) return <span className="muted">Belum diketahui / tidak tersedia</span>;
  if (Array.isArray(value)) return value.length ? <div className="detail-array">{value.map((v, i) => <div key={i}><DetailData value={v} onEvidence={onEvidence}/></div>)}</div> : <span className="muted">Tidak dicantumkan (daftar kosong)</span>;
  if (typeof value === 'object') return <dl className="detail-data">{Object.entries(value).map(([key, v]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{v !== null && typeof v === 'object' && !key.endsWith('evidence_ids') ? <details><summary>Buka rincian {key.replaceAll('_', ' ')}</summary><DetailData value={v} field={key} onEvidence={onEvidence}/></details> : <DetailData value={v} field={key} onEvidence={onEvidence}/>}</dd></div>)}</dl>;
  return <span>{String(value)}</span>;
}

/** Pipeline-level method. Shown on request: it explains the order, it is not the user's task. */
export function Methodology({ data }: { data: Priorities }) {
  return <details className="disclosure methodology"><summary>Bagaimana urutan ini dibuat?</summary>
    <p>{data.methodology.description}</p>
    <h4>Urutan aturan</h4><TextList items={data.methodology.ordered_rules} empty="Tidak dicantumkan"/>
    <h4>Jika nilainya sama</h4><TextList items={data.methodology.tie_breakers} empty="Tidak dicantumkan"/>
    <h4>Keterbatasan metode</h4><TextList items={[...data.methodology.limitations, ...data.limitations]} empty="Tidak dicantumkan"/>
    <details className="raw-source"><summary>Rincian metode lengkap, termasuk bobot ({data.methodology.label})</summary><pre>{JSON.stringify(data.methodology, null, 2)}</pre></details>
  </details>;
}

/** Layer 2: why this deal has its place in the order. Text is the API rationale, verbatim. */
export function PriorityRationale({ item }: { item: PriorityItem }) {
  return <section className="reason-section" aria-label="Alasan prioritas">
    <details className="disclosure"><summary>Mengapa deal ini prioritas #{item.rank} <span className="count">{item.rationale.length}</span></summary>
      <p className="note">Penjelasan sistem urutan, termasuk skor. Urutan perhatian sales, bukan peluang closing.</p>
      <TextList items={item.rationale} empty="Alasan belum dicantumkan."/>
    </details>
  </section>;
}

function EdgeButton({ edge, onEdge }: { edge: GraphEdge; onEdge: (id: string) => void }) {
  return <button className="edge-row" onClick={() => onEdge(edge.id)}>
    <span><strong>{relationPhrase(edge.relation)}</strong><span className="mono">{edge.source} → {edge.target} · {edge.relation}</span></span>
    <span className={`tag ${edge.evidence_type}`}>{kindLabel[edge.evidence_type]}</span>
    <span className="muted small">{dateLabel(edge.valid_from)} — {edge.valid_to ? dateLabel(edge.valid_to) : 'akhir tidak dicantumkan'}</span>
  </button>;
}
/** API evidence paths in reading order. Arrows keep each original edge direction. */
export function EvidencePaths({ item, context, onEvidence, onEdge, onShowPath }: { item: PriorityItem; context: DealContext; onEvidence: OpenEvidence; onEdge: (id: string) => void; onShowPath: (path: EvidencePath) => void }) {
  const edges = new Map(context.graph.edges.map(e => [e.id, e]));
  return <section className="reason-section" aria-label="Hubungan data yang mendukung">
    <h3>Hubungan data yang mendukung <span className="count">{item.evidence_paths.length}</span></h3>
    <p className="note">Panah menunjukkan arah relasi asli. Label “dugaan” berarti hasil penalaran dari data, bukan fakta langsung.</p>
    {!item.evidence_paths.length && <p className="muted">Ranking tidak mencantumkan jalur graph untuk deal ini; record sumber tetap bisa dibuka.</p>}
    <ol className="path-list">{item.evidence_paths.map((path, i) => <li key={i} className="path-card">
      <ol className="path-chain">{pathSteps(path, context).map((step, j) => <li key={j}>{step.edge && <span className={`path-link ${step.edge.evidence_type}`}><span className={`direction ${step.forward ? 'along' : 'against'}`}><Icon name="arrow" size={14}/></span>{relationPhrase(step.edge.relation)}<span className="visually-hidden">{step.forward ? ' (searah relasi asli)' : ' (dibaca melawan arah relasi asli)'}</span>{step.edge.evidence_type === 'inferred' && <span className="tag inferred">dugaan</span>}</span>}<span className="path-node"><strong>{step.name}</strong>{step.type && <span className="muted"> · {step.type}</span>} <span className="id-chip">{step.id}</span></span></li>)}</ol>
      <div className="path-actions"><button className="button secondary small" onClick={() => onShowPath(path)}><Icon name="graph" size={16}/>Lihat jalur ini di peta</button>
        <details className="disclosure compact"><summary>Relasi dalam jalur ini <span className="count">{path.edge_ids.length}</span></summary><p className="mono path-arrows">{pathArrows(path, context)}</p>{path.edge_ids.map(id => edges.get(id)).filter((e): e is GraphEdge => !!e).map(e => <EdgeButton key={e.id} edge={e} onEdge={onEdge}/>)}<Sources ids={path.evidence_ids} onEvidence={onEvidence}/></details></div>
    </li>)}</ol>
  </section>;
}

/** Layer 3: factor values and effects exactly as reported, including null. */
export function PriorityFactors({ item, onEvidence }: { item: PriorityItem; onEvidence: OpenEvidence }) {
  return <section className="reason-section" aria-label="Faktor penentu urutan">
    <h3>Faktor penentu urutan deal ini <span className="count">{item.factors.length}</span></h3>
    <p className="note">Jenis prioritas: {priorityKindLabel[item.priority_kind]} ({item.priority_kind}). Status bukti: {item.analysis_status}. Status “ready” bukan persetujuan atau janji closing.</p>
    <div className="factor-grid">{item.factors.map((f, i) => <article key={i} className="factor"><h4>{f.name.replaceAll('_', ' ')}</h4><strong>{f.value === null ? 'Belum tersedia (null)' : String(f.value)}</strong><p>{f.effect}</p><Sources ids={f.evidence_ids} onEvidence={onEvidence}/></article>)}</div>
    <h4>Keterbatasan prioritas deal ini</h4><TextList items={item.limitations} empty="Tidak dicantumkan"/>
    <Sources ids={item.evidence_ids} onEvidence={onEvidence} label="Semua sumber prioritas"/>
  </section>;
}

function FindingCard({ item, onEvidence }: { item: Finding; onEvidence: OpenEvidence }) {
  const extra = Object.fromEntries(Object.entries(item).filter(([k]) => !['finding_id', 'category', 'fact', 'interpretation', 'interpretation_type', 'evidence_ids', 'missing_information', 'follow_up_implication'].includes(k)));
  return <article className="finding"><div className="finding-head"><span className="tag">{item.category === 'business_anomaly' ? 'Anomali bisnis' : 'Informasi kurang'}</span><span className="mono">{item.finding_id}</span></div>
    <h5>Fakta yang dilaporkan</h5><p>{item.fact}</p>
    <h5>Interpretasi · {kindLabel[item.interpretation_type]}</h5><p>{item.interpretation}</p>
    <h5>Informasi belum diketahui</h5><TextList items={item.missing_information} empty="Tidak dicantumkan; bukan konfirmasi bebas risiko."/>
    <h5>Yang perlu diperiksa</h5><TextList items={item.follow_up_implication} empty="Tidak dicantumkan."/>
    <Sources ids={evidenceIds(item)} onEvidence={onEvidence}/>
    <details className="disclosure compact"><summary>Seluruh rincian & provenance</summary><DetailData value={extra} onEvidence={onEvidence}/></details></article>;
}
export function DiagnosticPanel({ data, onEvidence }: { data: Diagnostic; onEvidence: OpenEvidence }) {
  const m = data.metrics;
  return <section className="reason-section diagnostic" aria-label="Temuan dari data">
    <h3>Temuan dari data · {data.account_id}</h3>
    <p className="note">Pemeriksaan data otomatis dari layanan initial-analysis. Yang perlu diperiksa di sini bukan saran tindakan dan tidak mengganti saran tindakan.</p>
    <dl className="metric-row"><div><dt>Umur deal</dt><dd>{m.deal_age_days === null ? 'Belum tersedia' : `${m.deal_age_days} hari`}</dd></div><div><dt>Umur tahap</dt><dd>{m.stage_age_days === null ? 'Belum tersedia' : `${m.stage_age_days} hari`}</dd></div><div><dt>Interaksi eksternal terakhir</dt><dd>{dateLabel(m.interactions.customer.last_date)}</dd></div></dl>
    <p className="note">Interaksi eksternal termasuk pesan keluar dari sales, bukan otomatis balasan terakhir pelanggan. Nilai kosong bukan nol atau bebas risiko.</p>
    <details className="disclosure compact"><summary>Seluruh metrik, cakupan & sumber</summary><DetailData value={m} onEvidence={onEvidence}/></details>
    <h4>Temuan <span className="count">{data.findings.length}</span></h4>{data.findings.map(f => <details className="disclosure" key={f.finding_id}><summary>{f.finding_id}</summary><FindingCard item={f} onEvidence={onEvidence}/></details>)}{!data.findings.length && <p className="muted">Tidak ada temuan dicantumkan, bukan bukti tidak ada risiko.</p>}
    <h4>Kandidat referensi <span className="count">{data.reference_candidates.length}</span></h4><p className="note">Kandidat belum berarti sesuai, bersedia, atau mengizinkan kontak. Periksa pengalaman terbaru dan izin sebelum perkenalan.</p>{data.reference_candidates.map(f => <details className="disclosure" key={f.finding_id}><summary>{f.finding_id}</summary><FindingCard item={f} onEvidence={onEvidence}/></details>)}
    <details className="disclosure compact"><summary>Batas pemeriksaan</summary><TextList items={data.boundaries} empty="Tidak dicantumkan"/></details><Sources ids={evidenceIds(data)} onEvidence={onEvidence}/>
  </section>;
}
export function Statistics({ data, onEvidence }: { data: PipelineDiagnostic; onEvidence: OpenEvidence }) {
  const s = data.statistical_assessment;
  return <section className="reason-section statistics" aria-label="Penilaian statistik"><h3>Anomali bisnis ≠ outlier statistik</h3><p>Anomali bisnis adalah hambatan atau ketidakselarasan yang bersumber dari data. Outlier statistik memerlukan distribusi pembanding dan metode.</p><p><strong>Outlier statistik: belum dinilai ({s.status})</strong></p><p>{s.reason}</p><details className="disclosure compact"><summary>Cakupan, metode & sumber statistik</summary><DetailData value={s} onEvidence={onEvidence}/></details></section>;
}
