// Frontend mirror of API v1. The canonical contract belongs to Main.
export type EvidenceType = 'direct' | 'inferred';
export type Deal = {
  deal_id: string; account_id: string; account_name: string; stage: string;
  stage_age_days: number; annual_value: number; owner_id: string; rank: number | null;
  analysis_status: 'not_analyzed' | 'ready' | 'insufficient_evidence';
};
export type DealList = { schema_version: 'v1'; snapshot_date: string; items: Deal[] };
export type Evidence = { id: string; source_file: string; source_id: string; date: string | null; excerpt: string; evidence_type: EvidenceType };
export type GraphNode = { id: string; label: string; type: string };
export type GraphEdge = { id: string; source: string; target: string; relation: string; evidence_ids: string[]; evidence_type: EvidenceType; valid_from: string | null; valid_to: string | null };
export type DealContext = {
  schema_version: 'v1'; snapshot_date: string; deal: Deal; evidence: Evidence[];
  graph: { nodes: GraphNode[]; edges: GraphEdge[] };
  candidate_decisions: Record<string, unknown>[]; unknowns: string[];
};
export type Recommendation = {
  schema_version: 'v1'; deal_id: string; action: string; owner_id: string | null;
  milestone: string; evidence_ids: string[]; precedent_ids: string[];
  precedent_comparison: string[]; approvals_needed: string[]; unknowns: string[];
  engine_mode: 'jev' | 'rules' | 'replay';
};

const object = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);
const str = (v: unknown): v is string => typeof v === 'string';
const nullableString = (v: unknown) => v === null || str(v);
const strings = (v: unknown): v is string[] => Array.isArray(v) && v.every(str);
const natural = (v: unknown): v is number => typeof v === 'number' && Number.isSafeInteger(v) && v >= 0;
const evidenceType = (v: unknown) => v === 'direct' || v === 'inferred';
const unique = (ids: string[]) => new Set(ids).size === ids.length;

export function isDeal(v: unknown): v is Deal {
  return object(v) && ['deal_id','account_id','account_name','stage','owner_id'].every(k => str(v[k]))
    && natural(v.stage_age_days) && natural(v.annual_value)
    && (v.rank === null || (natural(v.rank) && v.rank > 0))
    && ['not_analyzed','ready','insufficient_evidence'].includes(String(v.analysis_status));
}
export function isDealList(v: unknown): v is DealList {
  return object(v) && v.schema_version === 'v1' && str(v.snapshot_date) && Array.isArray(v.items)
    && v.items.every(isDeal) && unique(v.items.map(d => d.deal_id));
}
export function isEvidence(v: unknown): v is Evidence {
  return object(v) && ['id','source_file','source_id','excerpt'].every(k => str(v[k]))
    && nullableString(v.date) && evidenceType(v.evidence_type);
}
export function isGraphNode(v: unknown): v is GraphNode {
  return object(v) && ['id','label','type'].every(k => str(v[k]));
}
export function isGraphEdge(v: unknown): v is GraphEdge {
  return object(v) && ['id','source','target','relation'].every(k => str(v[k]))
    && strings(v.evidence_ids) && evidenceType(v.evidence_type)
    && nullableString(v.valid_from) && nullableString(v.valid_to);
}
export function isContext(v: unknown): v is DealContext {
  if (!object(v) || v.schema_version !== 'v1' || !str(v.snapshot_date) || !isDeal(v.deal)
    || !Array.isArray(v.evidence) || !v.evidence.every(isEvidence) || !object(v.graph)
    || !Array.isArray(v.graph.nodes) || !v.graph.nodes.every(isGraphNode)
    || !Array.isArray(v.graph.edges) || !v.graph.edges.every(isGraphEdge)
    || !Array.isArray(v.candidate_decisions) || !v.candidate_decisions.every(object)
    || !strings(v.unknowns)) return false;
  return unique(v.evidence.map(e => e.id)) && unique(v.graph.nodes.map(n => n.id)) && unique(v.graph.edges.map(e => e.id));
}
export function isRecommendation(v: unknown): v is Recommendation {
  return object(v) && v.schema_version === 'v1' && ['deal_id','action','milestone'].every(k => str(v[k]))
    && nullableString(v.owner_id) && ['evidence_ids','precedent_ids','precedent_comparison','approvals_needed','unknowns'].every(k => strings(v[k]))
    && ['jev','rules','replay'].includes(String(v.engine_mode));
}

export function resolveEvidence(ids: string[], evidence: Evidence[]) {
  const byId = new Map(evidence.map(e => [e.id, e]));
  return { records: [...new Set(ids)].flatMap(id => byId.has(id) ? [byId.get(id)!] : []), missing: [...new Set(ids)].filter(id => !byId.has(id)) };
}
