// Redesign checks. REAL HTTP cases read the local rules backend with GET only; MOCK/STATIC cases are labelled.
const { test, before } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const React = require('react');
const { renderToStaticMarkup: render } = require('react-dom/server');
const build = process.env.REDESIGN_TEST_BUILD;
assert.ok(build, 'Compile DealTabs, EvidencePanel and ContextGraph; set REDESIGN_TEST_BUILD');
const { ActionTab } = require(path.join(build, 'components/DealTabs.js'));
const { EvidenceDrawer, EvidenceInspector } = require(path.join(build, 'components/EvidencePanel.js'));
const { ContextGraph } = require(path.join(build, 'components/ContextGraph.js'));
const { employeeFromContext, evidenceTitle, interactionMeta, recommendationView } = require(path.join(build, 'lib/present.js'));
const { ApiError, liveApi } = require(path.join(build, 'lib/api.js'));
const p = require(path.join(build, 'lib/phase3.js'));
const base = process.env.GRAPH_API_URL || 'http://127.0.0.1:8000';
const src = path.join(__dirname, '../src');
const signal = () => new AbortController().signal;
const escape = s => s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#x27;');
const noop = () => {};
const idle = { status: 'idle', error: null, receivedAt: null };
let ranking, contexts;
before(async () => {
  const original = global.fetch, methods = [];
  global.fetch = (url, options) => { methods.push(options.method); return original(new URL(url, base), options); };
  try {
    const list = await liveApi.list(signal());
    ranking = await liveApi.priorities(signal());
    p.matchPipeline(list, ranking);
    contexts = new Map();
    for (const deal of list.items) contexts.set(deal.deal_id, await liveApi.context(deal.deal_id, signal()));
    assert.deepEqual([...new Set(methods)], ['GET'], 'Data for the redesigned views is read with GET only');
  } finally { global.fetch = original; }
});
const joined = id => p.enrichContext(contexts.get(id), ranking.items.find(i => i.deal_id === id));
function action({ id, priority, context, rankingState = 'ready', snapshot = { status: 'idle', data: null }, session = idle, preferred = 'priority' }) {
  const view = recommendationView({ dealId: id, priority, session: snapshot, preferred });
  return { view, html: render(React.createElement(ActionTab, { context, priority, rankingState, view, fixture: false, snapshot: '2026-10-01', session, onEvidence: noop, onReasons: noop, onShowPaths: noop, onAnalyze: noop, onShowVersion: noop })) };
}
const acceptance = {
  'DL-001': [/Rina Hapsari \(GM Operations, identitas inferensi yang perlu dikonfirmasi\)/],
  'DL-002': [/Jangan menawarkan atau menjanjikan diskon 20%/, /VP Sales \(E01\): putuskan dan catat di decision_log permintaan diskon 20%/],
  'DL-003': [/memeriksa pengalaman terbaru/, /menanyakan kesediaan serta izin kontak/],
  'DL-004': [/memeriksa pengalaman terbaru/, /menanyakan kesediaan serta izin kontak/],
  'DL-005': [/menjadwalkan discovery/, /bukan berarti tidak ada risiko/, /Ini bukan tanda deal gagal, kalah, atau bebas risiko\./],
};

test('REAL HTTP layer 1: each API priority shows action and proof controls first, then owner, target, approvals and context, in plain words', () => {
  for (const item of ranking.items) {
    const context = joined(item.deal_id), r = item.recommendation;
    const { view, html } = action({ id: item.deal_id, priority: item, context });
    assert.equal(view.source, 'priority');
    const steps = ['Tindakan yang disarankan', 'Lihat alasan &amp; bukti', escape(r.action), 'Penanggung jawab', 'Target langkah berikutnya', 'Persetujuan yang diperlukan', 'Mengapa perlu diperhatikan'];
    for (let i = 1; i < steps.length; i++) assert.ok(html.indexOf(steps[i - 1]) >= 0 && html.indexOf(steps[i - 1]) < html.indexOf(steps[i]), `${item.deal_id}: ${steps[i - 1]} before ${steps[i]}`);
    for (const pattern of acceptance[item.deal_id]) assert.match(html, pattern, `${item.deal_id} acceptance`);
    for (const label of ['Status request sesi', 'GET ', 'POST ', 'Tier acceleration', 'tier acceleration', 'Status konteks CRM']) assert.ok(!html.includes(label), `${item.deal_id}: no technical label ${label}`);
    const owner = employeeFromContext(context, r.owner_id);
    assert.ok(owner, `${item.deal_id}: owner record exists in employees.csv`);
    assert.ok(html.includes(escape(owner.name)) && html.includes(`>${r.owner_id}<`));
    if (!r.approvals_needed.length) assert.ok(html.includes('Ini tidak berarti tindakan sudah disetujui.'), `${item.deal_id}: empty approvals are not approval`);
  }
});

test('MOCK states: loading and failed requests never present a recommendation as a success', () => {
  const item = ranking.items.find(i => i.deal_id === 'DL-002'), context = joined('DL-002');
  const loading = action({ id: 'DL-002', priority: null, context, rankingState: 'loading' }).html;
  assert.ok(loading.includes('Menyiapkan saran dari urutan prioritas')); assert.ok(!loading.includes('Tindakan yang disarankan'));
  const failedSession = { status: 'failed', error: new ApiError(503, 'MOCK 503 untuk uji.'), receivedAt: null };
  const failed = action({ id: 'DL-002', priority: null, context, rankingState: 'error', snapshot: { status: 'failed', data: null }, session: failedSession, preferred: 'session' }).html;
  assert.ok(failed.includes('Analisis belum dapat dimuat') && failed.includes('MOCK 503 untuk uji.') && failed.includes('Coba lagi'));
  assert.ok(failed.includes('Urutan prioritas gagal dimuat'));
  assert.ok(!failed.includes('Tindakan yang disarankan') && !failed.includes('Jalankan analisis untuk deal ini'), 'One recovery action, no result');
  const running = action({ id: 'DL-002', priority: item, context, snapshot: { status: 'running', data: null }, session: { status: 'running', error: null, receivedAt: null }, preferred: 'session' }).html;
  assert.ok(running.includes(escape(item.recommendation.action)) && running.includes('Dari urutan prioritas'));
  assert.ok(running.includes('Analisis ulang sedang berjalan. Saran yang tampil belum berubah.'));
  const retryFailed = action({ id: 'DL-002', priority: item, context, snapshot: { status: 'failed', data: null }, session: failedSession, preferred: 'session' }).html;
  assert.ok(retryFailed.includes('Analisis ulang belum dapat dimuat') && !retryFailed.includes('Hasil analisis ulang yang Anda minta'));
});

test('MOCK session result: an explicit re-analysis is labelled with its own mode and time; the ranking version stays one click away', () => {
  const item = ranking.items.find(i => i.deal_id === 'DL-004'), context = joined('DL-004');
  const posted = { ...structuredClone(item.recommendation), action: 'MOCK hasil analisis ulang DL-004', engine_mode: 'replay' };
  const { view, html } = action({ id: 'DL-004', priority: item, context, snapshot: { status: 'received', data: posted }, session: { status: 'received', error: null, receivedAt: '10.00.00' }, preferred: 'session' });
  assert.equal(view.source, 'session');
  assert.ok(html.includes('MOCK hasil analisis ulang DL-004') && !html.includes(escape(item.recommendation.action)));
  assert.ok(html.includes('Rekaman analisis (replay)') && !html.includes('Analisis dengan Jev'));
  assert.ok(html.includes('Hasil analisis ulang yang Anda minta pukul 10.00.00 · urutan prioritas tidak dihitung ulang'));
  assert.ok(html.includes('Saran dari urutan prioritas') && html.includes('Hasil analisis ulang · 10.00.00'));
  const back = action({ id: 'DL-004', priority: item, context, snapshot: { status: 'received', data: posted }, session: { status: 'received', error: null, receivedAt: '10.00.00' }, preferred: 'priority' }).html;
  assert.ok(back.includes(escape(item.recommendation.action)) && back.includes('Hasil analisis ulang sudah diterima; pilih versinya di atas untuk melihat.'));
});

test('REAL HTTP evidence drawer: I0348 opens its own record verbatim, closable, with a route to the graph and its original edge', () => {
  const context = joined('DL-002');
  const record = context.evidence.find(e => e.source_id === 'I0348' && e.source_file.endsWith('interactions.jsonl'));
  assert.ok(record);
  const html = render(React.createElement(EvidenceDrawer, { mode: 'side', titleId: 'drawer-title', onClose: noop },
    React.createElement(EvidenceInspector, { context, selection: { kind: 'evidence', id: record.id }, titleId: 'drawer-title', onGraph: noop })));
  assert.ok(html.includes('aria-labelledby="drawer-title"') && html.includes('id="drawer-title"') && html.includes('aria-label="Tutup panel bukti"'));
  assert.ok(html.includes(escape(evidenceTitle(record).title)) && html.includes(escape(interactionMeta(record).message)));
  assert.ok(html.includes('>I0348<') && html.includes(escape(record.id)) && html.includes('Tampilkan di peta hubungan: I0348'));
  assert.ok(!html.includes(`<h4>${escape(evidenceTitle(record).title)}</h4>`), 'Single record: the card does not repeat the drawer title');
  const edge = context.graph.edges.find(e => e.source === 'I0348' && e.target === 'P02' && e.relation === 'interaction_for');
  assert.ok(edge);
  const edgeHtml = render(React.createElement(EvidenceInspector, { context, selection: { kind: 'edge', id: edge.id }, titleId: 't', onGraph: noop }));
  assert.ok(edgeHtml.includes('interaksi dengan akun') && edgeHtml.includes('interaction_for') && edgeHtml.includes('I0348 → P02') && edgeHtml.includes('Langsung dari data'));
});

test('REAL HTTP graph proof: priority paths open as a highlighted union within the 24-node cap, edges keep direction', () => {
  for (const id of ['DL-002', 'DL-004']) {
    const item = ranking.items.find(i => i.deal_id === id), context = joined(id);
    const html = render(React.createElement(ContextGraph, { context, selection: null, onSelect: noop, initialPaths: item.evidence_paths }));
    assert.ok(html.includes(`Menampilkan ${item.evidence_paths.length} jalur data yang mendukung saran`));
    const nodes = (html.match(/class="focus-node/g) ?? []).length;
    assert.ok(nodes > 0 && nodes <= 24);
    const pathEdges = new Set(item.evidence_paths.flatMap(path => path.edge_ids));
    assert.equal((html.match(/class="graph-edge [^"]*on-path/g) ?? []).length, pathEdges.size, `${id}: every path edge is drawn and marked`);
    assert.ok(html.includes(`Deal ${escape(context.deal.account_name)}`));
    for (const edgeId of pathEdges) { const edge = context.graph.edges.find(e => e.id === edgeId); assert.ok(html.includes(`${edge.source} ke ${edge.target}`), `${id}: ${edgeId} keeps source → target`); }
  }
});

test('STATIC guard: the analysis POST only starts from an explicit button, never from an effect or page load', () => {
  const read = file => fs.readFileSync(path.join(src, file), 'utf8');
  const workspace = read('components/DealWorkspace.tsx'), dashboard = read('Dashboard.tsx'), tabs = read('components/DealTabs.tsx');
  assert.equal((workspace.match(/session\.run\(/g) ?? []).length, 1);
  assert.match(workspace, /function analyze\(\) \{[^}]*session\.run\(\)/);
  assert.match(workspace, /onAnalyze=\{analyze\}/);
  assert.equal((workspace.match(/[{\s]analyze\b/g) ?? []).length, 2, 'analyze is defined once and only passed as onAnalyze');
  assert.equal((workspace.match(/api\.analyze\(/g) ?? []).length, 1);
  assert.match(workspace, /createAnalysisSession\(signal => api\.analyze\(deal\.deal_id, signal\)\)/);
  assert.ok(!/analy[sz]e/i.test(dashboard.replace(/initial-analysis/g, '')), 'Dashboard never requests an analysis');
  assert.deepEqual(tabs.match(/[A-Za-z]+=\{onAnalyze\}/g), ['onClick={onAnalyze}', 'retry={onAnalyze}', 'onClick={onAnalyze}', 'retry={onAnalyze}']);
});

// Desktop copy improvement must never guess identity or discard policy words.
test('verified source links preserve original action and negation; unknown IDs stay literal', () => {
  const { ReadableAction } = require(path.join(build, 'components/AnalysisReport.js'));
  const context = joined('DL-002');
  const text = 'USULAN: E07 membaca I0348. Jangan menjanjikan diskon sebelum persetujuan. E999 I9999 tetap belum diketahui.';
  const html = render(React.createElement(ReadableAction, {text, context, onEvidence: noop}));
  const visible = html.split('<details')[0];
  const owner = employeeFromContext(context, 'E07');
  assert.ok(owner && visible.includes(escape(owner.name)));
  assert.ok(visible.includes('Buka sumber I0348:'));
  assert.ok(visible.includes('Jangan menjanjikan diskon sebelum persetujuan. E999 I9999 tetap belum diketahui.'));
  assert.ok(html.includes(escape(text)), 'Complete original action is still available');
});
test('source link refuses interaction identity mismatch and ambiguous matching records', () => {
  const { ReadableAction } = require(path.join(build, 'components/AnalysisReport.js'));
  const record = {id:'interactions.jsonl:I1234',source_file:'dataset_kasirnusa/interactions.jsonl',source_id:'I1234',date:null,excerpt:JSON.stringify({interaction_id:'I9999',isi:'x'})};
  for (const evidence of [[record], [record, {...record,id:'duplicate'}]]) {
    const html = render(React.createElement(ReadableAction, {text:'Baca I1234 sebelum menawarkan.',context:{evidence},onEvidence:noop}));
    assert.ok(html.includes('Baca I1234 sebelum menawarkan.'));
    assert.ok(!html.includes('<button'));
  }
});

test('structured evidence reads as source fields; missing is not zero and raw source is retained', () => {
  const { SourceContent, EvidenceCard } = require(path.join(build, 'components/EvidencePanel.js'));
  const context = joined('DL-004');
  const record = context.evidence.find(e => e.source_file.endsWith('contact_employment_history.csv'));
  assert.ok(record);
  const fields = render(React.createElement(SourceContent, {evidence:record}));
  assert.ok(fields.includes('<dl') && fields.includes('Organisasi') && fields.includes('Tidak dicantumkan'));
  const card = render(React.createElement(EvidenceCard, {evidence:record,context,onGraph:noop}));
  assert.ok(card.includes(escape(record.excerpt)), 'Full raw record remains in source details');
  const message = joined('DL-002').evidence.find(e => e.source_id === 'I0348');
  const quote = render(React.createElement(SourceContent, {evidence:message}));
  assert.ok(quote.includes(escape(interactionMeta(message).message)));
});
