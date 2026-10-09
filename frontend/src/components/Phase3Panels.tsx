import type { DealContext, GraphEdge } from '../lib/contracts';
import type { Diagnostic, EvidencePath, Finding, Priorities, PriorityItem, PipelineDiagnostic } from '../lib/phase3';
import { evidenceIds } from '../lib/phase3';
import { dateLabel, kindLabel } from '../lib/format';
import { pathArrows, pathSteps, priorityKindLabel, relationPhrase } from '../lib/present';
import { TextList } from './AnalysisReport';
import { Icon } from './Icon';

type OpenEvidence = (id: string) => void;
export function Sources({ ids, onEvidence, label = 'Sources' }: { ids: string[]; onEvidence: OpenEvidence; label?: string }) {
  const unique = [...new Set(ids)];
  return <details className="disclosure compact source-links"><summary>{label} <span className="count">{unique.length}</span></summary><div className="source-chips">{unique.map(id => <button className="id-button" key={id} onClick={() => onEvidence(id)}>{id}</button>)}</div>{!ids.length && <p className="muted">No linked sources; not confirmation of no risk.</p>}</details>;
}
/** Preserve arbitrary producer provenance without flattening null, fact or inferred fields. */
export function DetailData({ value, onEvidence, field = '' }: { value: unknown; onEvidence: OpenEvidence; field?: string }) {
  if (field.endsWith('evidence_ids') && Array.isArray(value)) return <Sources ids={value as string[]} onEvidence={onEvidence}/>;
  if (field.endsWith('evidence_id') && typeof value === 'string') return <button className="id-button" onClick={() => onEvidence(value)}>{value}</button>;
  if (value === null || value === undefined) return <span className="muted">Unknown / unavailable</span>;
  if (Array.isArray(value)) return value.length ? <div className="detail-array">{value.map((v, i) => <div key={i}><DetailData value={v} onEvidence={onEvidence}/></div>)}</div> : <span className="muted">Not provided (empty list)</span>;
  if (typeof value === 'object') return <dl className="detail-data">{Object.entries(value).map(([key, v]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{v !== null && typeof v === 'object' && !key.endsWith('evidence_ids') ? <details><summary>Buka rincian {key.replaceAll('_', ' ')}</summary><DetailData value={v} field={key} onEvidence={onEvidence}/></details> : <DetailData value={v} field={key} onEvidence={onEvidence}/>}</dd></div>)}</dl>;
  return <span>{String(value)}</span>;
}

/** Pipeline-level method. Shown on request: it explains the order, it is not the user's task. */
export function Methodology({ data }: { data: Priorities }) {
  return <details className="disclosure methodology"><summary>How priorities are calculated</summary>
    <p>{data.methodology.description}</p>
    <h4>Ranking rules</h4><TextList items={data.methodology.ordered_rules} empty="Not provided"/>
    <h4>Tie-breaking rules</h4><TextList items={data.methodology.tie_breakers} empty="Not provided"/>
    <h4>Method limitations</h4><TextList items={[...data.methodology.limitations, ...data.limitations]} empty="Not provided"/>
    <details className="raw-source"><summary>Rincian metode lengkap, termasuk bobot ({data.methodology.label})</summary><pre>{JSON.stringify(data.methodology, null, 2)}</pre></details>
  </details>;
}

/** Layer 2: why this deal has its place in the order. Text is the API rationale, verbatim. */
export function PriorityRationale({ item }: { item: PriorityItem }) {
  return <section className="reason-section" aria-label="Priority reasoning">
    <details className="disclosure"><summary>Why this deal is priority #{item.rank} <span className="count">{item.rationale.length}</span></summary>
      <p className="note">Ranking methodology and scores. An order of sales attention, not a closing probability.</p>
      <TextList items={item.rationale} empty="No reason recorded."/>
    </details>
  </section>;
}

function EdgeButton({ edge, onEdge }: { edge: GraphEdge; onEdge: (id: string) => void }) {
  return <button className="edge-row" onClick={() => onEdge(edge.id)}>
    <span><strong>{relationPhrase(edge.relation)}</strong><span className="mono">{edge.source} → {edge.target} · {edge.relation}</span></span>
    <span className={`tag ${edge.evidence_type}`}>{kindLabel[edge.evidence_type]}</span>
    <span className="muted small">{dateLabel(edge.valid_from)} — {edge.valid_to ? dateLabel(edge.valid_to) : 'no end date recorded'}</span>
  </button>;
}
/** Graph paths of the displayed analysis, in reading order. Arrows keep each original edge direction. */
export function EvidencePaths({ paths, limitations = [], context, onEvidence, onEdge, onShowPath }: { paths: EvidencePath[]; limitations?: string[]; context: DealContext; onEvidence: OpenEvidence; onEdge: (id: string) => void; onShowPath: (path: EvidencePath) => void }) {
  const edges = new Map(context.graph.edges.map(e => [e.id, e]));
  return <section className="reason-section" aria-label="Supporting relationships">
    <h3>Supporting relationships <span className="count">{paths.length}</span></h3>
    <p className="note">Paths follow recorded relationships for the analysis shown. Arrows retain the original direction. Inferred relationships are interpretations, not direct facts.</p>
    {!paths.length && <p className="muted">No graph path is available for this analysis. Cited source records remain available; no relationship is drawn without a recorded edge.</p>}
    {!!limitations.length && <details className="disclosure compact"><summary>Path limitations <span className="count">{limitations.length}</span></summary><TextList items={limitations} empty="None"/></details>}
    <ol className="path-list">{paths.map((path, i) => <li key={i}><details className="path-card">
      <summary><span>Path {i + 1}</span><strong>{pathSteps(path, context).at(-1)?.name ?? 'Supporting evidence'}</strong><span className="count">{path.edge_ids.length} edges</span></summary>
      <ol className="path-chain">{pathSteps(path, context).map((step, j) => <li key={j}>{step.edge && <span className={`path-link ${step.edge.evidence_type}`}><span className={`direction ${step.forward ? 'along' : 'against'}`}><Icon name="arrow" size={14}/></span>{relationPhrase(step.edge.relation)}<span className="visually-hidden">{step.forward ? ' (along the original direction)' : ' (read against the original direction)'}</span>{step.edge.evidence_type === 'inferred' && <span className="tag inferred">dugaan</span>}</span>}<span className="path-node"><strong>{step.name}</strong>{step.type && <span className="muted"> · {step.type}</span>} <span className="id-chip">{step.id}</span></span></li>)}</ol>
      <div className="path-actions"><button className="button secondary small" onClick={() => onShowPath(path)}><Icon name="graph" size={16}/>View path in graph</button>
        <details className="disclosure compact"><summary>Relationships in this path <span className="count">{path.edge_ids.length}</span></summary><p className="mono path-arrows">{pathArrows(path, context)}</p>{path.edge_ids.map(id => edges.get(id)).filter((e): e is GraphEdge => !!e).map(e => <EdgeButton key={e.id} edge={e} onEdge={onEdge}/>)}<Sources ids={path.evidence_ids} onEvidence={onEvidence}/></details></div>
    </details></li>)}</ol>
  </section>;
}

/** Layer 3: factor values and effects exactly as reported, including null. */
export function PriorityFactors({ item, onEvidence }: { item: PriorityItem; onEvidence: OpenEvidence }) {
  return <section className="reason-section" aria-label="Priority factors">
    <h3>Priority factors <span className="count">{item.factors.length}</span></h3>
    <p className="note">Priority type: {priorityKindLabel[item.priority_kind]} ({item.priority_kind}). Evidence status: {item.analysis_status}. Ready is not approval or a promise of closing.</p>
    <div className="factor-grid">{item.factors.map((f, i) => <article key={i} className="factor"><h4>{f.name.replaceAll('_', ' ')}</h4><strong>{f.value === null ? 'Unavailable (null)' : String(f.value)}</strong><p>{f.effect}</p><Sources ids={f.evidence_ids} onEvidence={onEvidence}/></article>)}</div>
    <h4>Priority limitations</h4><TextList items={item.limitations} empty="Not provided"/>
    <Sources ids={item.evidence_ids} onEvidence={onEvidence} label="All priority sources"/>
  </section>;
}

function FindingCard({ item, onEvidence }: { item: Finding; onEvidence: OpenEvidence }) {
  const extra = Object.fromEntries(Object.entries(item).filter(([k]) => !['finding_id', 'category', 'fact', 'interpretation', 'interpretation_type', 'evidence_ids', 'missing_information', 'follow_up_implication'].includes(k)));
  return <article className="finding"><div className="finding-head"><span className="tag">{item.category === 'business_anomaly' ? 'Business anomaly' : 'Missing information'}</span><span className="mono">{item.finding_id}</span></div>
    <h5>Recorded fact</h5><p>{item.fact}</p>
    <h5>Interpretation · {kindLabel[item.interpretation_type]}</h5><p>{item.interpretation}</p>
    <h5>Unknown information</h5><TextList items={item.missing_information} empty="Not provided; not confirmation of no risk."/>
    <h5>What to check</h5><TextList items={item.follow_up_implication} empty="Not provided."/>
    <Sources ids={evidenceIds(item)} onEvidence={onEvidence}/>
    <details className="disclosure compact"><summary>Full details & provenance</summary><DetailData value={extra} onEvidence={onEvidence}/></details></article>;
}
export function DiagnosticPanel({ data, onEvidence }: { data: Diagnostic; onEvidence: OpenEvidence }) {
  const m = data.metrics;
  return <section className="reason-section diagnostic" aria-label="Data findings">
    <h3>Data findings · {data.account_id}</h3>
    <p className="note">Automated data findings. These checks do not replace the recommended action.</p>
    <dl className="metric-row"><div><dt>Deal age</dt><dd>{m.deal_age_days === null ? 'Unavailable' : `${m.deal_age_days} days`}</dd></div><div><dt>Stage age</dt><dd>{m.stage_age_days === null ? 'Unavailable' : `${m.stage_age_days} days`}</dd></div><div><dt>Last external interaction</dt><dd>{dateLabel(m.interactions.customer.last_date)}</dd></div></dl>
    <p className="note">External interactions include outbound sales messages, not just customer replies. Missing values are not zero or risk-free.</p>
    <details className="disclosure compact"><summary>All metrics, scope & sources</summary><DetailData value={m} onEvidence={onEvidence}/></details>
    <h4>Findings <span className="count">{data.findings.length}</span></h4>{data.findings.map(f => <details className="disclosure" key={f.finding_id}><summary>{f.finding_id}</summary><FindingCard item={f} onEvidence={onEvidence}/></details>)}{!data.findings.length && <p className="muted">No findings listed; not proof of no risk.</p>}
    <h4>Reference candidates <span className="count">{data.reference_candidates.length}</span></h4><p className="note">Candidates are not confirmed as suitable, willing or consenting. Check recent experience and permission before an introduction.</p>{data.reference_candidates.map(f => <details className="disclosure" key={f.finding_id}><summary>{f.finding_id}</summary><FindingCard item={f} onEvidence={onEvidence}/></details>)}
    <details className="disclosure compact"><summary>Audit limitations</summary><TextList items={data.boundaries} empty="Not provided"/></details><Sources ids={evidenceIds(data)} onEvidence={onEvidence}/>
  </section>;
}
export function Statistics({ data, onEvidence }: { data: PipelineDiagnostic; onEvidence: OpenEvidence }) {
  const s = data.statistical_assessment;
  return <section className="reason-section statistics" aria-label="Statistical assessment"><h3>Business anomalies ≠ statistical outliers</h3><p>Business anomalies are blockers or inconsistencies in the data. Statistical outliers require a comparison distribution and method.</p><p><strong>Statistical outliers: not assessed ({s.status})</strong></p><p>{s.reason}</p><details className="disclosure compact"><summary>Statistical scope, method & sources</summary><DetailData value={s} onEvidence={onEvidence}/></details></section>;
}
