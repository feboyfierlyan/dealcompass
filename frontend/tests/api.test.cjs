const test = require('node:test');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const { join } = require('node:path');
const buildDir = process.env.API_TEST_BUILD;
if (!buildDir) throw new Error('Set API_TEST_BUILD to the temporary CommonJS compilation directory; see frontend/TESTING.md.');
const { liveApi } = createRequire(join(buildDir, 'test-entry.cjs'))('./api.js');
const response = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
const list = { schema_version: 'v1', snapshot_date: '2026-10-01', items: [] };

test('API status 404/501/503 remains distinguishable to the UI', async t => {
  for (const status of [404, 501, 503]) {
    t.mock.method(global, 'fetch', async () => response({}, status));
    await assert.rejects(liveApi.list(new AbortController().signal), error => error.status === status);
    t.mock.restoreAll();
  }
});
test('non-JSON success and malformed contract are rejected instead of rendering data', async t => {
  t.mock.method(global, 'fetch', async () => new Response('<html>failure</html>'));
  await assert.rejects(liveApi.list(new AbortController().signal), error => error.status === 502);
  t.mock.restoreAll();
  t.mock.method(global, 'fetch', async () => response({ items: null }));
  await assert.rejects(liveApi.list(new AbortController().signal), error => error.status === 502);
});
test('network outage is not mistaken for a valid empty list', async t => {
  t.mock.method(global, 'fetch', async () => { throw new TypeError('Failed to fetch'); });
  await assert.rejects(liveApi.list(new AbortController().signal), error => error.status === 0);
});
test('valid empty response remains empty', async t => {
  t.mock.method(global, 'fetch', async () => response(list));
  assert.deepEqual(await liveApi.list(new AbortController().signal), list);
});
test('changing deal aborts the old request without turning it into an error notice', async t => {
  t.mock.method(global, 'fetch', (_, { signal }) => new Promise((resolve, reject) => {
    signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
  }));
  const controller = new AbortController();
  const pending = liveApi.context('DL-001', controller.signal);
  controller.abort();
  await assert.rejects(pending, error => error.name === 'AbortError');
});
test('20-second timeout is explicitly reported', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  t.mock.method(global, 'fetch', (_, { signal }) => new Promise((resolve, reject) => {
    signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
  }));
  const pending = liveApi.list(new AbortController().signal);
  t.mock.timers.tick(20000);
  await assert.rejects(pending, error => error.status === 408);
});
test('recommendation for a different deal is rejected and uses POST', async t => {
  t.mock.method(global, 'fetch', async (url, options) => {
    assert.equal(url, '/api/deals/DL-001/analyze');
    assert.equal(options.method, 'POST');
    return response({schema_version:'v1',deal_id:'DL-002',action:'fixture',owner_id:null,milestone:'fixture',evidence_ids:[],precedent_ids:[],precedent_comparison:[],approvals_needed:[],unknowns:[],engine_mode:'rules'});
  });
  await assert.rejects(liveApi.analyze('DL-001', new AbortController().signal), error => error.status === 502);
});
test('active analysis uses POST /analysis, refresh only when asked, and rejects a Jev label without provider answers', async t => {
  const rec = { schema_version: 'v1', deal_id: 'DL-002', action: 'USULAN: x', owner_id: null, milestone: 'm', evidence_ids: [], precedent_ids: [], precedent_comparison: [], approvals_needed: [], unknowns: [], engine_mode: 'jev' };
  const meta = { analysis_id: 'a', analysis_version: 'v', context_fingerprint: 'f', engine_mode: 'jev', outcome: 'jev_applied', analysis_status: 'ready', fallback_reason: null, cache: 'fresh', generated_at: '2026-10-10T03:00:00+00:00', provider_requests: 2, model: 'jev-x', gate: 'g', evidence_paths: [], path_limitations: [] };
  const urls = [];
  let body = { schema_version: 'v1', deal_id: 'DL-002', snapshot_date: '2026-10-01', recommendation: rec, analysis: meta };
  t.mock.method(global, 'fetch', async (url, options) => { urls.push([url, options.method]); return response(body); });
  assert.equal((await liveApi.analysis('DL-002', false, new AbortController().signal)).analysis.outcome, 'jev_applied');
  await liveApi.analysis('DL-002', true, new AbortController().signal);
  assert.deepEqual(urls, [['/api/deals/DL-002/analysis', 'POST'], ['/api/deals/DL-002/analysis?refresh=true', 'POST']]);
  body = { ...body, analysis: { ...meta, provider_requests: 0 } };
  await assert.rejects(liveApi.analysis('DL-002', false, new AbortController().signal), error => error.status === 502);
  body = { ...body, deal_id: 'DL-001', recommendation: { ...rec, deal_id: 'DL-001' }, analysis: meta };
  await assert.rejects(liveApi.analysis('DL-002', false, new AbortController().signal), error => error.status === 502);
});

test('missing local analysis route is not reported as a TypeSafe outage or unknown deal', async t => {
  t.mock.method(global, 'fetch', async () => response({ detail: 'Not Found' }, 404));
  await assert.rejects(liveApi.analysis('DL-002', false, new AbortController().signal), e => e.status === 404 && /endpoint is missing/.test(e.message) && /Restart the backend/.test(e.message));
  t.mock.restoreAll();
  t.mock.method(global, 'fetch', async () => response({ detail: { code: 'DEAL_NOT_FOUND' } }, 404));
  await assert.rejects(liveApi.analysis('DL-999', false, new AbortController().signal), e => e.status === 404 && /deal was not found/.test(e.message));
});
