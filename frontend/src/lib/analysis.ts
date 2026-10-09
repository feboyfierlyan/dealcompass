// Active deal analysis: POST /api/deals/{id}/analysis (Recommendation v1 + analysis metadata).
// The backend runs rules first, lets Jev enrich eligible deals once per context, and caches the result.
// Type-only imports keep this module runnable by node --test without a build step.
import type { Recommendation } from './contracts';
import type { EvidencePath } from './phase3';

export type AnalysisOutcome = 'jev_applied' | 'rules_only' | 'jev_unavailable' | 'not_eligible';
export type AnalysisMeta = {
  analysis_id: string; analysis_version: string; context_fingerprint: string;
  engine_mode: 'jev' | 'rules' | 'replay'; outcome: AnalysisOutcome; analysis_status: 'ready' | 'insufficient_evidence';
  fallback_reason: string | null; cache: 'fresh' | 'hit' | 'shared' | 'none'; generated_at: string;
  provider_requests: number; model: string | null; gate: string; evidence_paths: EvidencePath[]; path_limitations: string[];
};
export type AnalysisEnvelope = { schema_version: 'v1'; deal_id: string; snapshot_date: string; recommendation: Recommendation; analysis: AnalysisMeta };

const obj = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);
const str = (v: unknown): v is string => typeof v === 'string';
const strings = (v: unknown): v is string[] => Array.isArray(v) && v.every(str);
const oneOf = (v: unknown, values: string[]) => str(v) && values.includes(v);
const recommendation = (v: unknown): v is Recommendation => obj(v) && v.schema_version === 'v1' && ['deal_id', 'action', 'milestone'].every(k => str(v[k]))
  && (v.owner_id === null || str(v.owner_id)) && ['evidence_ids', 'precedent_ids', 'precedent_comparison', 'approvals_needed', 'unknowns'].every(k => strings(v[k]))
  && oneOf(v.engine_mode, ['jev', 'rules', 'replay']);
const path = (v: unknown): v is EvidencePath => obj(v) && strings(v.node_ids) && strings(v.edge_ids) && strings(v.evidence_ids)
  && v.node_ids.length > 1 && v.edge_ids.length === v.node_ids.length - 1;

/** Shape plus label integrity: "Rules + Jev" needs a successful Jev/replay result with at least one provider answer. */
export function isAnalysisEnvelope(v: unknown): v is AnalysisEnvelope {
  if (!obj(v) || v.schema_version !== 'v1' || !str(v.deal_id) || !str(v.snapshot_date) || !recommendation(v.recommendation) || !obj(v.analysis)) return false;
  const m = v.analysis, r = v.recommendation;
  if (!['analysis_id', 'analysis_version', 'context_fingerprint', 'generated_at', 'gate'].every(k => str(m[k]))
    || !oneOf(m.engine_mode, ['jev', 'rules', 'replay']) || !oneOf(m.outcome, ['jev_applied', 'rules_only', 'jev_unavailable', 'not_eligible'])
    || !oneOf(m.analysis_status, ['ready', 'insufficient_evidence']) || !oneOf(m.cache, ['fresh', 'hit', 'shared', 'none'])
    || !(m.fallback_reason === null || str(m.fallback_reason)) || !(m.model === null || str(m.model))
    || typeof m.provider_requests !== 'number' || !Number.isSafeInteger(m.provider_requests) || m.provider_requests < 0
    || !Array.isArray(m.evidence_paths) || !m.evidence_paths.every(path) || !strings(m.path_limitations)) return false;
  if (r.deal_id !== v.deal_id || m.engine_mode !== r.engine_mode || Number.isNaN(Date.parse(m.generated_at as string))) return false;
  if (m.outcome === 'jev_applied') return r.engine_mode !== 'rules' && m.provider_requests > 0 && m.fallback_reason === null;
  return r.engine_mode === 'rules' && (m.outcome !== 'not_eligible' || (m.provider_requests === 0 && m.analysis_status === 'insufficient_evidence'));
}

export type AnalysisEntry = {
  status: 'running' | 'ready' | 'failed';
  envelope: AnalysisEnvelope | null; // last valid result for this deal + snapshot
  refreshing: boolean;               // a deliberate refresh is running; envelope above is the previous result
  error: Error | null;
};
type Request = (dealId: string, refresh: boolean, signal: AbortSignal) => Promise<AnalysisEnvelope>;

/** Revision of a loaded DealContext (FNV-1a, two seeds). Same-date source changes give a new revision. */
export function contextRevision(context: unknown): string {
  const text = JSON.stringify(context);
  let a = 0x811c9dc5, b = 0x01000193 ^ text.length;
  for (let i = 0; i < text.length; i++) {
    const c = text.charCodeAt(i);
    a = Math.imul(a ^ c, 0x01000193); b = Math.imul(b ^ c, 0x5bd1e995);
  }
  return (a >>> 0).toString(16).padStart(8, '0') + (b >>> 0).toString(16).padStart(8, '0');
}

/**
 * One analysis workflow per deal + snapshot + loaded context revision for the life of the app.
 * A changed context (even on the same snapshot date) is a new key: an ordinary backend lookup, never a forced refresh. Re-rendering, switching tabs,
 * opening the plan or returning to a deal reads the stored entry instead of sending a request.
 * Requests are not aborted on navigation: cancelling in the browser does not stop provider usage,
 * and the finished result is kept for when the user comes back. The backend deduplicates as well.
 */
export function createAnalysisStore(request: Request) {
  const entries = new Map<string, AnalysisEntry>();
  const listeners = new Set<() => void>();
  let sent = 0;
  const key = (dealId: string, snapshot: string, revision: string) => `${dealId}|${snapshot}|${revision}`;
  function set(k: string, next: AnalysisEntry) { entries.set(k, next); listeners.forEach(l => l()); }
  async function start(dealId: string, snapshot: string, revision: string, refresh: boolean) {
    const k = key(dealId, snapshot, revision), previous = entries.get(k)?.envelope ?? null;
    set(k, { status: previous ? 'ready' : 'running', envelope: previous, refreshing: !!previous, error: null });
    sent++;
    try {
      const envelope = await request(dealId, refresh, new AbortController().signal);
      if (envelope.deal_id !== dealId || envelope.recommendation.deal_id !== dealId || envelope.snapshot_date !== snapshot) throw new Error('The analysis does not match this deal or snapshot.');
      set(k, { status: 'ready', envelope, refreshing: false, error: null });
    } catch (error) {
      const e = error instanceof Error ? error : new Error('Analysis could not be loaded.');
      set(k, previous ? { status: 'ready', envelope: previous, refreshing: false, error: e } : { status: 'failed', envelope: null, refreshing: false, error: e });
    }
  }
  return {
    get: (dealId: string, snapshot: string, revision: string) => entries.get(key(dealId, snapshot, revision)) ?? null,
    subscribe(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener); }; },
    /** First visit only. A failed entry is not retried automatically. */
    ensure(dealId: string, snapshot: string, revision: string) { if (!entries.has(key(dealId, snapshot, revision))) void start(dealId, snapshot, revision, false); },
    /** Deliberate user request; ignored while a request for this deal is already running. */
    refresh(dealId: string, snapshot: string, revision: string) {
      const e = entries.get(key(dealId, snapshot, revision));
      if (e && (e.status === 'running' || e.refreshing)) return;
      void start(dealId, snapshot, revision, true);
    },
    requestCount: () => sent,
  };
}
export type AnalysisStore = ReturnType<typeof createAnalysisStore>;

const stores = new WeakMap<object, AnalysisStore>();
/** One store per API object (live or fixture), shared by every view that opens a deal. */
export function analysisStoreFor(api: { analysis?: Request }): AnalysisStore | null {
  if (!api.analysis) return null;
  let store = stores.get(api);
  if (!store) { store = createAnalysisStore(api.analysis); stores.set(api, store); }
  return store;
}
