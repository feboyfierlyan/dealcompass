// Default deal analysis: one workflow per deal, honest labels, one version on screen. MOCK promises only.
import test from 'node:test';
import assert from 'node:assert/strict';
import { analysisStoreFor, createAnalysisStore, isAnalysisEnvelope } from '../src/lib/analysis.ts';
import { activeAnalysis, provenance, statusLabel } from '../src/lib/activeAnalysis.ts';

const deferred = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; };
const tick = () => new Promise(r => setTimeout(r, 0));
const rec = (deal_id, engine_mode = 'jev', action = `USULAN: MOCK ${deal_id}`) => ({ schema_version: 'v1', deal_id, action, owner_id: 'E07', milestone: 'M', evidence_ids: ['x'], precedent_ids: [], precedent_comparison: [], approvals_needed: ['VP Sales (E01): MOCK'], unknowns: [], engine_mode });
const hybridPath = { node_ids: ['DL-002', 'P02', 'I0348'], edge_ids: ['e1', 'e2'], evidence_ids: ['x'] };
const rankingPath = { node_ids: ['DL-002', 'P02'], edge_ids: ['r1'], evidence_ids: ['y'] };
function envelope(deal_id, { outcome = 'jev_applied', engine = outcome === 'jev_applied' ? 'jev' : 'rules', cache = 'fresh', status = 'ready', requests = outcome === 'jev_applied' ? 3 : 0, reason = null, id = `id-${deal_id}`, at = '2026-10-10T03:00:00+00:00', action } = {}) {
  return { schema_version: 'v1', deal_id, snapshot_date: '2026-10-01', recommendation: rec(deal_id, engine, action), analysis: {
    analysis_id: id, analysis_version: 'rules+jev/1+abc', context_fingerprint: 'f', engine_mode: engine, outcome, analysis_status: status,
    fallback_reason: reason, cache, generated_at: at, provider_requests: requests, model: engine === 'jev' ? 'jev-mock' : null,
    gate: 'approval VP Sales tertunda', evidence_paths: [hybridPath], path_limitations: [] } };
}
const priority = (deal_id, status = 'ready') => ({ deal_id, account_id: 'P02', rank: 3, priority_kind: status === 'ready' ? 'acceleration' : 'discovery', analysis_status: status,
  factors: [{ name: 'gate_approval_izin', value: 'approval VP Sales tertunda', effect: '', evidence_ids: [] }], rationale: [], limitations: [], evidence_ids: [], evidence: [],
  evidence_paths: [rankingPath], recommendation: rec(deal_id, 'rules', 'USULAN: ranking rules') });

test('first open starts one workflow; rerenders, tab switches and returning to the deal reuse it', async () => {
  const pending = deferred(); let calls = 0;
  const store = createAnalysisStore(() => { calls++; return pending.promise; });
  for (let i = 0; i < 5; i++) store.ensure('DL-002', '2026-10-01');
  assert.equal(store.get('DL-002', '2026-10-01').status, 'running');
  pending.resolve(envelope('DL-002')); await tick();
  store.ensure('DL-002', '2026-10-01');
  assert.equal(calls, 1); assert.equal(store.requestCount(), 1);
  assert.equal(store.get('DL-002', '2026-10-01').envelope.analysis.analysis_id, 'id-DL-002');
  const api = { analysis: async () => envelope('DL-001') };
  assert.equal(analysisStoreFor(api), analysisStoreFor(api), 'one store per API object survives remounts');
  assert.equal(analysisStoreFor({}), null, 'no analysis endpoint: no automatic request');
});

test('only the opened deal is analysed, and a late response cannot appear under another deal', async () => {
  const slow = deferred(), seen = [];
  const store = createAnalysisStore(id => { seen.push(id); return id === 'DL-002' ? slow.promise : Promise.resolve(envelope(id)); });
  store.ensure('DL-002', '2026-10-01'); store.ensure('DL-004', '2026-10-01'); await tick();
  slow.resolve(envelope('DL-002')); await tick();
  assert.deepEqual(seen, ['DL-002', 'DL-004']);
  assert.equal(store.get('DL-004', '2026-10-01').envelope.deal_id, 'DL-004');
  assert.equal(store.get('DL-002', '2026-10-01').envelope.deal_id, 'DL-002');
  const view = activeAnalysis({ dealId: 'DL-004', priority: priority('DL-004'), entry: store.get('DL-002', '2026-10-01'), service: true });
  assert.notEqual(view.recommendation?.deal_id, 'DL-002', 'a foreign entry is never shown');
});

test('a response for the wrong deal or snapshot is rejected', async () => {
  const store = createAnalysisStore(async () => ({ ...envelope('DL-001') }));
  store.ensure('DL-002', '2026-10-01'); await tick();
  assert.equal(store.get('DL-002', '2026-10-01').status, 'failed');
  const other = createAnalysisStore(async id => ({ ...envelope(id), snapshot_date: '2026-09-01' }));
  other.ensure('DL-002', '2026-10-01'); await tick();
  assert.equal(other.get('DL-002', '2026-10-01').status, 'failed');
});

test('failure is not retried by navigation; only Refresh analysis asks again', async () => {
  let calls = 0, fail = true;
  const store = createAnalysisStore(async (id, refresh) => { calls++; if (fail) throw new Error('HTTP 503'); return envelope(id, { cache: refresh ? 'fresh' : 'hit' }); });
  store.ensure('DL-002', '2026-10-01'); await tick();
  store.ensure('DL-002', '2026-10-01'); await tick();
  assert.equal(calls, 1);
  const failed = activeAnalysis({ dealId: 'DL-002', priority: priority('DL-002'), entry: store.get('DL-002', '2026-10-01'), service: true });
  assert.equal(failed.label, 'Jev unavailable · rules shown'); assert.equal(failed.recommendation.action, 'USULAN: ranking rules');
  fail = false; store.refresh('DL-002', '2026-10-01'); await tick();
  assert.equal(calls, 2); assert.equal(store.get('DL-002', '2026-10-01').status, 'ready');
});

test('refresh keeps the previous analysis labelled as previous; a failed refresh never shows it as new', async () => {
  const next = deferred(); let n = 0;
  const store = createAnalysisStore(async () => (++n === 1 ? envelope('DL-002', { id: 'old' }) : next.promise));
  store.ensure('DL-002', '2026-10-01'); await tick();
  store.refresh('DL-002', '2026-10-01'); store.refresh('DL-002', '2026-10-01');
  let view = activeAnalysis({ dealId: 'DL-002', priority: priority('DL-002'), entry: store.get('DL-002', '2026-10-01'), service: true });
  assert.equal(view.refreshing, true); assert.equal(view.meta.analysis_id, 'old'); assert.equal(n, 2, 'double click sends one refresh');
  next.reject(new Error('timeout')); await tick();
  view = activeAnalysis({ dealId: 'DL-002', priority: priority('DL-002'), entry: store.get('DL-002', '2026-10-01'), service: true });
  assert.equal(view.meta.analysis_id, 'old'); assert.equal(view.error.message, 'timeout'); assert.equal(view.refreshing, false);
  assert.equal(view.versionKey, 'analysis:old:2026-10-10T03:00:00+00:00', 'the failed refresh did not replace the displayed version');
});

test('labels: rules while checking, Rules + Jev only for a validated Jev result, honest fallback, replay and discovery', () => {
  const p = priority('DL-002');
  const checking = activeAnalysis({ dealId: 'DL-002', priority: p, entry: { status: 'running', envelope: null, refreshing: false, error: null }, service: true });
  assert.equal(checking.label, 'Checking context…'); assert.equal(checking.source, 'priority'); assert.equal(checking.recommendation.engine_mode, 'rules');
  const first = activeAnalysis({ dealId: 'DL-002', priority: p, entry: null, service: true });
  assert.equal(first.label, 'Checking context…');
  const entry = env => ({ status: 'ready', envelope: env, refreshing: false, error: null });
  const hybrid = activeAnalysis({ dealId: 'DL-002', priority: p, entry: entry(envelope('DL-002')), service: true });
  assert.equal(hybrid.label, 'Rules + Jev'); assert.equal(hybrid.source, 'analysis');
  assert.deepEqual(hybrid.paths, [hybridPath], 'graph paths come from the active analysis, not the ranking');
  assert.equal(hybrid.gate, 'approval VP Sales tertunda');
  assert.equal(activeAnalysis({ dealId: 'DL-002', priority: p, entry: entry(envelope('DL-002', { engine: 'replay' })), service: true }).label, 'Rules + Jev · recorded replay');
  const fallback = activeAnalysis({ dealId: 'DL-002', priority: p, entry: entry(envelope('DL-002', { outcome: 'jev_unavailable', reason: 'timeout', requests: 2 })), service: true });
  assert.equal(fallback.label, 'Jev unavailable · rules shown');
  assert.match(provenance(fallback).join(' '), /Jev was not used \(timeout; 2 requests made\)/);
  assert.equal(activeAnalysis({ dealId: 'DL-002', priority: p, entry: entry(envelope('DL-002', { outcome: 'rules_only' })), service: true }).label, 'Rules-based');
  const p05 = activeAnalysis({ dealId: 'DL-005', priority: priority('DL-005', 'insufficient_evidence'), entry: entry(envelope('DL-005', { outcome: 'not_eligible', status: 'insufficient_evidence' })), service: true });
  assert.equal(p05.label, 'More information needed'); assert.match(provenance(p05).join(' '), /No provider request was made/);
  assert.equal(activeAnalysis({ dealId: 'DL-002', priority: p, entry: null, service: false }).label, 'Rules-based');
  assert.equal(activeAnalysis({ dealId: 'DL-002', priority: priority('DL-001'), entry: null, service: false }).recommendation, null);
  assert.equal(statusLabel.hybrid, 'Rules + Jev');
});

test('provenance never calls a saved result new; replay is never live', () => {
  const entry = env => ({ status: 'ready', envelope: env, refreshing: false, error: null });
  const hit = provenance(activeAnalysis({ dealId: 'DL-002', priority: null, entry: entry(envelope('DL-002', { cache: 'hit' })), service: true })).join(' ');
  assert.match(hit, /Saved analysis from .* No new provider request was made\./); assert.ok(!/Generated|fresh|new analysis/i.test(hit.replace('No new provider request', '')));
  const fresh = provenance(activeAnalysis({ dealId: 'DL-002', priority: null, entry: entry(envelope('DL-002')), service: true })).join(' ');
  assert.match(fresh, /Generated .* WIB/); assert.match(fresh, /3 requests, jev-mock/);
  const replay = provenance(activeAnalysis({ dealId: 'DL-002', priority: null, entry: entry(envelope('DL-002', { engine: 'replay' })), service: true })).join(' ');
  assert.match(replay, /Recorded replay of earlier Jev answers, not a live provider call\./);
});

test('version key changes when the displayed analysis changes, so evidence, graph and plan follow one version', () => {
  const p = priority('DL-002');
  const a = activeAnalysis({ dealId: 'DL-002', priority: p, entry: null, service: true });
  const env = envelope('DL-002');
  const b = activeAnalysis({ dealId: 'DL-002', priority: p, entry: { status: 'ready', envelope: env, refreshing: false, error: null }, service: true });
  assert.notEqual(a.versionKey, b.versionKey);
  assert.deepEqual(a.paths, [rankingPath]); assert.deepEqual(b.paths, [hybridPath]);
  assert.equal(b.recommendation, env.recommendation); assert.equal(b.meta, env.analysis, 'recommendation and metadata come from one envelope');
});

test('envelope validator enforces label integrity', () => {
  assert.ok(isAnalysisEnvelope(envelope('DL-002')));
  assert.ok(isAnalysisEnvelope(envelope('DL-002', { outcome: 'jev_unavailable', reason: 'timeout' })));
  const bad = (mut) => { const e = structuredClone(envelope('DL-002')); mut(e); return isAnalysisEnvelope(e); };
  assert.equal(bad(e => { e.recommendation.engine_mode = 'rules'; e.analysis.engine_mode = 'rules'; }), false, 'Rules + Jev needs a Jev engine');
  assert.equal(bad(e => { e.analysis.provider_requests = 0; }), false, 'HTTP 200 without provider answers is not Jev');
  assert.equal(bad(e => { e.analysis.engine_mode = 'replay'; }), false, 'metadata and recommendation must agree');
  assert.equal(bad(e => { e.analysis.cache = 'new'; }), false);
  assert.equal(bad(e => { e.recommendation.deal_id = 'DL-001'; }), false);
  assert.equal(isAnalysisEnvelope(envelope('DL-005', { outcome: 'not_eligible', status: 'insufficient_evidence', requests: 1 })), false, 'P05 must not report provider usage');
  assert.equal(bad(e => { e.analysis.evidence_paths = [{ node_ids: ['a'], edge_ids: [], evidence_ids: [] }]; }), false);
});
