import { isEvidence, isRecommendation } from './contracts';
import type { DealContext, DealList, Evidence, Recommendation } from './contracts';

type RecordData = Record<string, unknown>;
export type EvidencePath = { node_ids: string[]; edge_ids: string[]; evidence_ids: string[] };
export type PriorityItem = {
  deal_id: string; account_id: string; rank: number; priority_kind: 'acceleration' | 'discovery';
  analysis_status: 'ready' | 'insufficient_evidence'; rationale: string[];
  factors: { name: string; value: number | string | null; effect: string; evidence_ids: string[] }[];
  recommendation: Recommendation; evidence_ids: string[]; evidence: Evidence[];
  evidence_paths: EvidencePath[]; limitations: string[];
};
export type Priorities = {
  schema_version: 'v1'; snapshot_date: string; engine_mode: 'rules'; items: PriorityItem[];
  methodology: RecordData & { id: string; label: string; description: string; ordered_rules: string[]; tie_breakers: string[]; limitations: string[] };
  limitations: string[];
};
export type Finding = RecordData & {
  finding_id: string; category: string; fact: string; interpretation: string;
  interpretation_type: 'direct' | 'inferred'; evidence_ids: string[];
  missing_information: string[]; follow_up_implication: string[];
};
export type InteractionMetric = RecordData & { count: number; last_date: string | null; last_evidence_ids: string[]; evidence_ids: string[] };
export type Diagnostic = RecordData & {
  deal_id: string; account_id: string; snapshot_date: string;
  metrics: RecordData & { deal_id: string; account_id: string; snapshot_date: string; created_date: string | null; stage_since: string | null; deal_age_days: number | null; stage_age_days: number | null; age_evidence_ids: string[]; unknowns: string[];
    interactions: RecordData & { total_count: number; last_date: string | null; last_evidence_ids: string[]; customer: InteractionMetric; internal: InteractionMetric; unclassified: InteractionMetric; undated_evidence_ids: string[] } };
  findings: Finding[]; reference_candidates: Finding[]; boundaries: string[]; evidence: Evidence[];
};
export type PipelineDiagnostic = {
  schema_version: 'v1'; snapshot_date: string; deals: Diagnostic[];
  statistical_assessment: RecordData & { status: 'not_assessed'; sample_size: number; stage_cohort_counts: Record<string, number>; method: null; threshold: null; outlier_deal_ids: null; evidence_ids: string[]; reason: string };
};
const obj = (v: unknown): v is RecordData => typeof v === 'object' && v !== null && !Array.isArray(v);
const str = (v: unknown): v is string => typeof v === 'string';
const strings = (v: unknown): v is string[] => Array.isArray(v) && v.every(str);
const nat = (v: unknown): v is number => typeof v === 'number' && Number.isSafeInteger(v) && v >= 0;
const date = (v: unknown) => v === null || (str(v) && /^\d{4}-\d{2}-\d{2}$/.test(v));
const unique = (v: string[]) => new Set(v).size === v.length;
const snapshot = (v: unknown) => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v); // Dataset-specific snapshot.
function jsonSafe(v: unknown): boolean {
  if (v === null || str(v) || typeof v === 'boolean') return true;
  if (typeof v === 'number') return Number.isFinite(v);
  return Array.isArray(v) ? v.every(jsonSafe) : obj(v) && Object.values(v).every(jsonSafe);
}
function canonical(v: unknown): string {
  if (Array.isArray(v)) return `[${v.map(canonical).join(',')}]`;
  if (obj(v)) return `{${Object.keys(v).sort().map(k => JSON.stringify(k)+':'+canonical(v[k])).join(',')}}`;
  return JSON.stringify(v);
}
/** Never overwrite an ID with different content, including additional provenance fields. */
export function mergeEvidence(...registries: Evidence[][]): Evidence[] {
  const result = new Map<string, Evidence>();
  for (const registry of registries) for (const record of registry) {
    const existing = result.get(record.id);
    if (existing && canonical(existing) !== canonical(record)) throw new Error(`Conflicting evidence: ${record.id}. Sources were not merged.`);
    result.set(record.id, record);
  }
  return [...result.values()];
}
export function evidenceIds(value: unknown): string[] {
  const ids = new Set<string>();
  function walk(v: unknown) {
    if (Array.isArray(v)) v.forEach(walk);
    else if (obj(v)) for (const [key, child] of Object.entries(v)) {
      if (key.endsWith('evidence_ids')) { if (!strings(child)) throw new Error('Invalid evidence ID list.'); child.forEach(id => ids.add(id)); }
      else if (key.endsWith('evidence_id')) { if (child !== null) { if (!str(child)) throw new Error('Invalid evidence ID.'); ids.add(child); } }
      else if (key !== 'evidence') walk(child);
    }
  }
  walk(value); return [...ids];
}
function registry(v: unknown): v is Evidence[] { return Array.isArray(v) && v.every(isEvidence) && unique(v.map(e => e.id)); }
function resolved(v: unknown, records: Evidence[]): boolean {
  try { const ids = new Set(records.map(e => e.id)); return evidenceIds(v).every(id => ids.has(id)); } catch { return false; }
}
function path(v: unknown): v is EvidencePath {
  return obj(v) && strings(v.node_ids) && v.node_ids.length > 0 && unique(v.node_ids)
    && strings(v.edge_ids) && unique(v.edge_ids) && v.edge_ids.length === v.node_ids.length - 1 && strings(v.evidence_ids);
}
function priority(v: unknown): v is PriorityItem {
  return obj(v) && str(v.deal_id) && str(v.account_id) && nat(v.rank) && v.rank > 0
    && ['acceleration','discovery'].includes(String(v.priority_kind)) && ['ready','insufficient_evidence'].includes(String(v.analysis_status))
    && strings(v.rationale) && Array.isArray(v.factors) && v.factors.every(f => obj(f) && str(f.name) && str(f.effect) && strings(f.evidence_ids) && (f.value === null || str(f.value) || (typeof f.value === 'number' && Number.isFinite(f.value))))
    && isRecommendation(v.recommendation) && v.recommendation.deal_id === v.deal_id && v.recommendation.engine_mode === 'rules'
    && registry(v.evidence) && strings(v.evidence_ids) && Array.isArray(v.evidence_paths) && v.evidence_paths.every(path) && strings(v.limitations) && resolved(v, v.evidence);
}
export function isPriorities(v: unknown): v is Priorities {
  if (!obj(v) || !jsonSafe(v) || v.schema_version !== 'v1' || !snapshot(v.snapshot_date) || v.engine_mode !== 'rules'
    || !obj(v.methodology) || !['id','label','description'].every(k => str(v.methodology && (v.methodology as RecordData)[k]))
    || !['ordered_rules','tie_breakers','limitations'].every(k => strings((v.methodology as RecordData)[k])) || !strings(v.limitations)
    || !Array.isArray(v.items) || v.items.length < 1 || !v.items.every(priority)) return false;
  try { mergeEvidence(...v.items.map(i => i.evidence)); } catch { return false; }
  const count = v.items.length;
  return unique(v.items.map(i => i.deal_id)) && unique(v.items.map(i => i.account_id))
    && unique(v.items.map(i => String(i.rank))) && v.items.every(i => i.rank <= count);
}
function interaction(v: unknown): v is InteractionMetric { return obj(v) && nat(v.count) && date(v.last_date) && strings(v.last_evidence_ids) && strings(v.evidence_ids); }
function finding(v: unknown): v is Finding {
  return obj(v) && ['finding_id','fact','interpretation'].every(k => str(v[k])) && ['business_anomaly','data_gap'].includes(String(v.category))
    && ['direct','inferred'].includes(String(v.interpretation_type)) && ['evidence_ids','missing_information','follow_up_implication'].every(k => strings(v[k]));
}
export function isDiagnostic(v: unknown): v is Diagnostic {
  if (!obj(v) || !jsonSafe(v) || ('schema_version' in v && v.schema_version !== 'v1') || !str(v.deal_id) || !str(v.account_id) || !snapshot(v.snapshot_date)
    || !obj(v.metrics) || !Array.isArray(v.findings) || !v.findings.every(finding) || !Array.isArray(v.reference_candidates) || !v.reference_candidates.every(finding)
    || !strings(v.boundaries) || !registry(v.evidence) || !resolved(v, v.evidence)) return false;
  const m = v.metrics, i = m.interactions, q = m.query_scope;
  return m.deal_id === v.deal_id && m.account_id === v.account_id && m.snapshot_date === v.snapshot_date
    && date(m.created_date) && date(m.stage_since) && (m.deal_age_days === null || nat(m.deal_age_days)) && (m.stage_age_days === null || nat(m.stage_age_days))
    && strings(m.age_evidence_ids) && strings(m.unknowns) && obj(i) && nat(i.total_count) && date(i.last_date) && strings(i.last_evidence_ids)
    && ['customer','internal','unclassified'].every(k => interaction(i[k])) && strings(i.undated_evidence_ids)
    && obj(q) && str(q.source_file) && q.account_id === v.account_id && date(q.since) && q.through === v.snapshot_date;
}
export function isDealDiagnostic(v: unknown): v is Diagnostic { return obj(v) && v.schema_version === 'v1' && isDiagnostic(v); }
export function isPipelineDiagnostic(v: unknown): v is PipelineDiagnostic {
  if (!obj(v) || !jsonSafe(v) || v.schema_version !== 'v1' || !snapshot(v.snapshot_date) || !Array.isArray(v.deals) || v.deals.length < 1 || !v.deals.every(isDiagnostic)
    || !v.deals.every(d => d.snapshot_date === v.snapshot_date)
    || !unique(v.deals.map(d => d.deal_id)) || !unique(v.deals.map(d => d.account_id)) || !obj(v.statistical_assessment)) return false;
  const s = v.statistical_assessment;
  if (s.status !== 'not_assessed' || s.sample_size !== v.deals.length || !obj(s.stage_cohort_counts) || !Object.values(s.stage_cohort_counts).every(nat)
    || (Object.values(s.stage_cohort_counts) as number[]).reduce((a,b) => a + b,0) !== v.deals.length || s.method !== null || s.threshold !== null || s.outlier_deal_ids !== null || !str(s.reason) || !strings(s.evidence_ids)) return false;
  try { return resolved(v, mergeEvidence(...v.deals.map(d => d.evidence))); } catch { return false; }
}
export function matchPipeline(list: DealList, payload: Priorities | PipelineDiagnostic) {
  const items = 'items' in payload ? payload.items : payload.deals;
  if (list.snapshot_date !== payload.snapshot_date || list.items.length < 1 || items.length !== list.items.length
    || items.some(i => !list.items.some(d => d.deal_id === i.deal_id && d.account_id === i.account_id))) throw new Error('Pipeline snapshot or deal/account mismatch. Results were rejected.');
  return payload;
}
export function rankedDeals(list: DealList, p: Priorities) {
  matchPipeline(list, p);
  const byId = new Map(list.items.map(d => [d.deal_id, d]));
  return [...p.items].sort((a,b) => a.rank-b.rank).map(item => ({ ...byId.get(item.deal_id)!, rank: item.rank, analysis_status: item.analysis_status }));
}
export function validatePaths(item: PriorityItem, context: DealContext) {
  const nodes = new Set(context.graph.nodes.map(n => n.id)), edges = new Map(context.graph.edges.map(e => [e.id,e]));
  for (const p of item.evidence_paths) {
    if (!p.node_ids.every(id => nodes.has(id))) throw new Error('Priority path node not found in the context graph.');
    const sources = new Set<string>();
    p.edge_ids.forEach((id,i) => {
      const edge = edges.get(id), a = p.node_ids[i], b = p.node_ids[i+1];
      if (!edge || !((edge.source === a && edge.target === b) || (edge.source === b && edge.target === a))) throw new Error('Priority path does not match the original relationship endpoints.');
      edge.evidence_ids.forEach(id => sources.add(id));
    });
    if (p.edge_ids.length && (p.evidence_ids.some(id => !sources.has(id)) || [...sources].some(id => !p.evidence_ids.includes(id)))) throw new Error('Path provenance does not match the original relationships.');
  }
}
export function enrichContext(context: DealContext, report: PriorityItem | Diagnostic) {
  if (context.deal.deal_id !== report.deal_id || context.deal.account_id !== report.account_id || ('snapshot_date' in report && context.snapshot_date !== report.snapshot_date)) throw new Error('Context and results do not match this deal, account or snapshot.');
  if ('evidence_paths' in report) validatePaths(report as PriorityItem, context);
  return { ...context, evidence: mergeEvidence(context.evidence, report.evidence) };
}
