import { englishText, fieldLabel } from '../lib/english';
import type { DealContext, GraphEdge } from '../lib/contracts';
import type { Diagnostic, EvidencePath, Finding, Priorities, PriorityItem, PipelineDiagnostic } from '../lib/phase3';
import { evidenceIds } from '../lib/phase3';
import { dateLabel, kindLabel, rupiah } from '../lib/format';
import { pathArrows, pathSteps, relationPhrase } from '../lib/present';
import { gateLabel } from '../lib/planning';
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
  if (typeof value === 'object') return <dl className="detail-data">{Object.entries(value).map(([key, v]) => <div key={key}><dt>{fieldLabel(key)}</dt><dd>{v !== null && typeof v === 'object' && !key.endsWith('evidence_ids') ? <details><summary>View details: {fieldLabel(key)}</summary><DetailData value={v} field={key} onEvidence={onEvidence}/></details> : <DetailData value={v} field={key} onEvidence={onEvidence}/>}</dd></div>)}</dl>;
  return <span>{englishText(String(value))}</span>;
}

/** Pipeline-level method. Shown on request: it explains the order, it is not the user's task. */
export function Methodology({ data }: { data: Priorities }) {
  return <details className="insight-details methodology"><summary>How priorities are calculated</summary><div className="insight-detail-body">
    <p>The ranking uses fixed rules. It helps plan sales attention; it does not predict a close.</p>
    <details className="insight-details"><summary>Scoring rules</summary><div className="insight-detail-body"><p>{englishText(data.methodology.description)}</p><TextList items={data.methodology.ordered_rules} empty="Not provided"/></div></details>
    <details className="insight-details"><summary>When deals have the same score</summary><div className="insight-detail-body"><TextList items={data.methodology.tie_breakers} empty="Not provided"/></div></details>
    <details className="insight-details"><summary>Method limitations</summary><div className="insight-detail-body"><TextList items={[...data.methodology.limitations, ...data.limitations]} empty="Not provided"/></div></details>
    <details className="raw-source"><summary>Technical methodology & weights</summary><pre>{JSON.stringify(data.methodology, null, 2)}</pre></details>
  </div></details>;
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
      <ol className="path-chain">{pathSteps(path, context).map((step, j) => <li key={j}>{step.edge && <span className={`path-link ${step.edge.evidence_type}`}><span className={`direction ${step.forward ? 'along' : 'against'}`}><Icon name="arrow" size={14}/></span>{relationPhrase(step.edge.relation)}<span className="visually-hidden">{step.forward ? ' (along the original direction)' : ' (read against the original direction)'}</span>{step.edge.evidence_type === 'inferred' && <span className="tag inferred">Inferred</span>}</span>}<span className="path-node"><strong>{step.name}</strong>{step.type && <span className="muted"> · {step.type}</span>} <span className="id-chip">{step.id}</span></span></li>)}</ol>
      <div className="path-actions"><button className="button secondary small" onClick={() => onShowPath(path)}><Icon name="graph" size={16}/>View path in graph</button>
        <details className="disclosure compact"><summary>Relationships in this path <span className="count">{path.edge_ids.length}</span></summary><p className="mono path-arrows">{pathArrows(path, context)}</p>{path.edge_ids.map(id => edges.get(id)).filter((e): e is GraphEdge => !!e).map(e => <EdgeButton key={e.id} edge={e} onEdge={onEdge}/>)}<Sources ids={path.evidence_ids} onEvidence={onEvidence}/></details></div>
    </details></li>)}</ol>
  </section>;
}

/** Compact overview; producer values, effects and provenance remain inspectable. */
function factorValue(f: PriorityItem['factors'][number]) {
  if (f.value === null) return 'Not enough information';
  if (f.name === 'nilai_potensi_tahunan' && typeof f.value === 'number') return rupiah(f.value);
  if (f.name === 'preseden_relevan') return `${f.value} relevant decisions`;
  return englishText(String(f.value));
}
export function PriorityFactors({ item, onEvidence }: { item: PriorityItem; onEvidence: OpenEvidence }) {
  const primary = new Set(['tahap_deal', 'nilai_potensi_tahunan', 'hambatan_dinyatakan_pelanggan', 'preseden_relevan']);
  const gate = item.factors.find(f => f.name === 'gate_approval_izin');
  const labels: Record<string, string> = { tahap_deal: 'Deal stage', nilai_potensi_tahunan: 'Annual potential', hambatan_dinyatakan_pelanggan: 'Customer blocker', preseden_relevan: 'Past decisions' };
  return <section className="reason-section insight-panel" aria-label="Priority factors">
    <header className="insight-heading"><div><h3>Why this priority</h3><p>Understand where this deal sits in your follow-up queue.</p></div><span className="insight-rank">#{item.rank}</span></header>
    <p className="insight-context">{item.priority_kind === 'discovery' ? 'Discovery comes first for this deal. There is not enough evidence to score it yet.' : 'The order considers deal stage, annual potential, customer blockers and relevant past decisions.'}</p>
    <div className="factor-rows">{item.factors.filter(f => primary.has(f.name)).map(f => <details className="factor-row" key={f.name}>
      <summary><span>{labels[f.name]}</span><strong>{factorValue(f)}</strong><Icon name="chevron" size={15}/></summary>
      <div className="factor-explanation"><p>{englishText(f.effect)}</p><Sources ids={f.evidence_ids} onEvidence={onEvidence}/></div>
    </details>)}</div>
    {gate && <div className="insight-gate"><Icon name="flag" size={16}/><span>{gateLabel(typeof gate.value === 'string' ? gate.value : null, item.recommendation.approvals_needed)}<small>Priority does not remove approval or consent requirements.</small></span></div>}
    <details className="insight-details"><summary>Score breakdown & full reasoning</summary><div className="insight-detail-body">
      <TextList items={item.rationale} empty="No reason recorded."/>
      {item.factors.filter(f => !primary.has(f.name)).map(f => <details className="factor-row" key={f.name}><summary><span>{fieldLabel(f.name)}</span><strong>{f.value === null ? 'Unavailable (null)' : factorValue(f)}</strong><Icon name="chevron" size={15}/></summary><div className="factor-explanation"><p>{englishText(f.effect)}</p><Sources ids={f.evidence_ids} onEvidence={onEvidence}/></div></details>)}
      <h4>Limits of this ranking</h4><TextList items={item.limitations} empty="Not provided"/><Sources ids={item.evidence_ids} onEvidence={onEvidence} label="All priority sources"/>
    </div></details><p className="insight-footnote">Order of attention · not a closing probability</p>
  </section>;
}

/** Labels describe the recorded finding type, never a guessed business outcome. */
function findingTitle(item: Finding) {
  const comparison = item.account_comparison as { candidate?: { name?: string } } | undefined;
  if (comparison?.candidate?.name) return comparison.candidate.name;
  if (item.finding_id.startsWith('price_objection:')) return 'Clarify the price objection';
  if (item.finding_id.startsWith('discount_request:')) return 'Check discount approval';
  if (item.finding_id.startsWith('reference_requirement:')) return 'Validate the customer reference request';
  if (item.finding_id.includes(':authority:')) return 'Confirm who makes the decision';
  if (item.finding_id.startsWith('customer_information_gap:')) return 'Complete customer discovery';
  return item.category === 'data_gap' ? 'Confirm missing information' : 'Review the recorded business issue';
}
function FindingCard({ item, onEvidence }: { item: Finding; onEvidence: OpenEvidence }) {
  const extra = Object.fromEntries(Object.entries(item).filter(([k]) => !['finding_id', 'category', 'fact', 'interpretation', 'interpretation_type', 'evidence_ids', 'missing_information', 'follow_up_implication'].includes(k)));
  return <div className="finding-detail">
    <section className="finding-next"><h4>Next check</h4><TextList items={item.follow_up_implication} empty="No follow-up recorded."/></section>
    <section><h4>What the records say</h4><p>{englishText(item.fact)}</p></section>
    <section><h4>What this may mean <span className="tag">{kindLabel[item.interpretation_type]}</span></h4><p>{englishText(item.interpretation)}</p></section>
    <section><h4>Still unknown</h4><TextList items={item.missing_information} empty="Not provided; not confirmation of no risk."/></section>
    <Sources ids={evidenceIds(item)} onEvidence={onEvidence} label="View source records"/>
    <details className="insight-details"><summary>Technical record & provenance</summary><p className="mono small">{item.finding_id}</p><DetailData value={extra} onEvidence={onEvidence}/></details>
  </div>;
}
function FindingRow({ item, onEvidence, candidate = false }: { item: Finding; onEvidence: OpenEvidence; candidate?: boolean }) {
  return <details className="finding-row"><summary><span className="finding-row-icon"><Icon name={candidate ? 'user' : 'flag'} size={17}/></span><span className="finding-row-title"><strong>{findingTitle(item)}</strong><small>{candidate ? 'Suitability & contact consent unconfirmed' : item.category === 'data_gap' ? 'Missing information' : 'Business issue to review'}</small></span><Icon name="chevron" size={16}/></summary><FindingCard item={item} onEvidence={onEvidence}/></details>;
}
export function DiagnosticPanel({ data, onEvidence }: { data: Diagnostic; onEvidence: OpenEvidence }) {
  const m = data.metrics;
  return <section className="reason-section diagnostic insight-panel" aria-label="Data findings">
    <header className="insight-heading"><div><h3>What to check</h3><p>Review these findings before your next conversation.</p></div><span className="count">{data.findings.length}</span></header>
    <div className="finding-list">{data.findings.map(f => <FindingRow key={f.finding_id} item={f} onEvidence={onEvidence}/>)}{!data.findings.length && <p className="insight-context">No findings recorded. This does not confirm that the deal is risk-free.</p>}</div>
    {!!data.reference_candidates.length && <details className="insight-details reference-disclosure"><summary>Potential customer references <span className="count">{data.reference_candidates.length}</span></summary><div className="insight-detail-body"><p className="note">Confirm suitability, recent experience and contact consent before an introduction.</p>{data.reference_candidates.map(f => <FindingRow key={f.finding_id} item={f} onEvidence={onEvidence} candidate/>)}</div></details>}
    <details className="insight-details"><summary>Activity & data coverage</summary><div className="insight-detail-body">
      <dl className="metric-row"><div><dt>Deal age</dt><dd>{m.deal_age_days === null ? 'Unavailable' : `${m.deal_age_days} days`}</dd></div><div><dt>Stage age</dt><dd>{m.stage_age_days === null ? 'Unavailable' : `${m.stage_age_days} days`}</dd></div><div><dt>Last external interaction</dt><dd>{dateLabel(m.interactions.customer.last_date)}</dd></div></dl>
      <p className="note">External interactions include outbound sales messages, not just customer replies. Missing values are not zero or risk-free.</p>
      <details className="insight-details"><summary>All metrics & sources</summary><DetailData value={m} onEvidence={onEvidence}/></details>
      <h4>Data limitations</h4><TextList items={data.boundaries} empty="Not provided"/><Sources ids={evidenceIds(data)} onEvidence={onEvidence}/>
    </div></details>
  </section>;
}
export function Statistics({ data, onEvidence }: { data: PipelineDiagnostic; onEvidence: OpenEvidence }) {
  const s = data.statistical_assessment;
  return <details className="insight-details statistics" aria-label="Statistical assessment"><summary>How to interpret these findings</summary><div className="insight-detail-body"><p>These are business issues or missing information, not proven statistical outliers.</p><p><strong>Statistical outliers: not assessed ({s.status})</strong></p><p>{englishText(s.reason)}</p><details className="insight-details"><summary>Statistical scope & sources</summary><DetailData value={s} onEvidence={onEvidence}/></details></div></details>;
}
