// Redesign checks. REAL HTTP cases read the local rules backend with GET only; MOCK/STATIC cases are labelled.
const { test, before } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const React = require('react');
const { renderToStaticMarkup: render } = require('react-dom/server');
const build = process.env.REDESIGN_TEST_BUILD;
assert.ok(build, 'Compile DealTabs, EvidencePanel and ContextGraph; set REDESIGN_TEST_BUILD');
const { englishText } = require(`${build}/lib/english.js`);
const { ActionTab } = require(path.join(build, 'components/DealTabs.js'));
const { EvidenceDrawer, EvidenceInspector } = require(path.join(build, 'components/EvidencePanel.js'));
const { ContextGraph } = require(path.join(build, 'components/ContextGraph.js'));
const { employeeFromContext, evidenceTitle, interactionMeta } = require(path.join(build, 'lib/present.js'));
const { activeAnalysis } = require(path.join(build, 'lib/activeAnalysis.js'));
const { ApiError, liveApi } = require(path.join(build, 'lib/api.js'));
const p = require(path.join(build, 'lib/phase3.js'));
const base = process.env.GRAPH_API_URL || 'http://127.0.0.1:8000';
const src = path.join(__dirname, '../src');
const signal = () => new AbortController().signal;
const escape = s => s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#x27;');
const noop = () => {};
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
function action({ id, priority, context, rankingState = 'ready', entry = null, service = false }) {
  const view = activeAnalysis({ dealId: id, priority, entry, service });
  return { view, html: render(React.createElement(ActionTab, { context, priority, rankingState, view, fixture: false, snapshot: '2026-10-01', canRefresh: service, onEvidence: noop, onReasons: noop, onShowPaths: noop, onRefresh: noop })) };
}
// MOCK envelope around a real recommendation; label integrity follows the backend metadata.
const envelope = (item, over = {}) => ({ schema_version: 'v1', deal_id: item.deal_id, snapshot_date: '2026-10-01', recommendation: over.recommendation ?? item.recommendation, analysis: {
  analysis_id: 'mock-analysis', analysis_version: 'mock', context_fingerprint: 'mock', engine_mode: (over.recommendation ?? item.recommendation).engine_mode, outcome: 'rules_only',
  analysis_status: item.analysis_status, fallback_reason: null, cache: 'fresh', generated_at: '2026-10-10T03:00:00+00:00', provider_requests: 0, model: null,
  gate: item.factors.find(f => f.name === 'gate_approval_izin').value, evidence_paths: item.evidence_paths, path_limitations: [], ...over.analysis } });
const ready = env => ({ status: 'ready', envelope: env, refreshing: false, error: null });
const acceptance = {
  'DL-001': [/Rina Hapsari \(GM Operations, identitas inferensi yang perlu dikonfirmasi\)/],
  'DL-002': [/Jangan menawarkan atau menjanjikan diskon 20%/, /VP Sales \(E01\): putuskan dan catat di decision_log permintaan diskon 20%/],
  'DL-003': [/memeriksa pengalaman terbaru/, /menanyakan kesediaan serta izin kontak/],
  'DL-004': [/memeriksa pengalaman terbaru/, /menanyakan kesediaan serta izin kontak/],
  'DL-005': [/menjadwalkan discovery/, /bukan berarti tidak ada risiko/, /Missing discovery does not mean the deal is lost or risk-free\./],
};

test('REAL HTTP guided layer: goal and gate precede preparation, full API action and evidence remain available', () => {
  for (const item of ranking.items) {
    const context = joined(item.deal_id), r = item.recommendation;
    const { view, html } = action({ id: item.deal_id, priority: item, context });
    assert.equal(view.source, 'priority');
    const steps = ['Next step', 'Target', 'class="move-boundary"', 'Prepare follow-up', 'Action details', 'Recommended action', escape(r.action), 'Expected outcome', 'View evidence'];
    for (let i = 1; i < steps.length; i++) assert.ok(html.indexOf(steps[i - 1]) >= 0 && html.indexOf(steps[i - 1]) < html.indexOf(steps[i]), `${item.deal_id}: ${steps[i - 1]} before ${steps[i]}`);
    for (const pattern of acceptance[item.deal_id]) assert.match(html, pattern, `${item.deal_id} acceptance`);
    for (const label of ['Status request sesi', 'GET ', 'POST ', 'Tier acceleration', 'tier acceleration', 'Status konteks CRM']) assert.ok(!html.includes(label), `${item.deal_id}: no technical label ${label}`);
    const owner = employeeFromContext(context, r.owner_id);
    assert.ok(owner, `${item.deal_id}: owner record exists in employees.csv`);
    assert.ok(html.includes(escape(owner.name)) && html.includes(`>${r.owner_id}<`));
    if (!r.approvals_needed.length) assert.ok(html.includes('This does not mean the action is approved.'), `${item.deal_id}: empty approvals are not approval`);
  }
});

test('MOCK states: rules stay readable while checking; a failed analysis falls back honestly and never shows a result as new', () => {
  const item = ranking.items.find(i => i.deal_id === 'DL-002'), context = joined('DL-002');
  const running = { status: 'running', envelope: null, refreshing: false, error: null };
  const loading = action({ id: 'DL-002', priority: null, context, rankingState: 'loading', service: true, entry: running }).html;
  assert.ok(loading.includes('Checking context…')); assert.ok(!loading.includes('Recommended action'));
  const checking = action({ id: 'DL-002', priority: item, context, service: true, entry: running }).html;
  assert.ok(checking.includes(escape(item.recommendation.action)) && checking.includes('Checking context…'));
  assert.ok(checking.includes('Rules-based recommendation shown while the deal context is checked.'));
  const failedEntry = { status: 'failed', envelope: null, refreshing: false, error: new ApiError(503, 'MOCK 503 for testing.') };
  const fallback = action({ id: 'DL-002', priority: item, context, service: true, entry: failedEntry }).html;
  assert.ok(fallback.includes('Analysis unavailable · rules shown') && fallback.includes('MOCK 503 for testing.'));
  assert.ok(fallback.includes(escape(item.recommendation.action)) && fallback.includes('VP Sales (E01)'));
  const nothing = action({ id: 'DL-002', priority: null, context, rankingState: 'error', service: true, entry: failedEntry }).html;
  assert.ok(nothing.includes('Analysis could not be loaded') && nothing.includes('Refresh analysis') && nothing.includes('Priorities could not be loaded'));
  assert.ok(!nothing.includes('Recommended action'));
});

test('MOCK hybrid result: becomes the active analysis with its own label, gate and paths; approvals stay', () => {
  const item = ranking.items.find(i => i.deal_id === 'DL-002'), context = joined('DL-002');
  const r = { ...structuredClone(item.recommendation), action: item.recommendation.action + ' MOCK hybrid', engine_mode: 'jev' };
  const env = envelope(item, { recommendation: r, analysis: { outcome: 'jev_applied', provider_requests: 3, model: 'jev-mock', cache: 'hit' } });
  const { view, html } = action({ id: 'DL-002', priority: item, context, service: true, entry: ready(env) });
  assert.equal(view.source, 'analysis'); assert.equal(view.label, 'Rules + Jev');
  assert.ok(html.includes('MOCK hybrid') && html.includes('Rules + Jev') && html.includes('VP Sales (E01)'));
  assert.ok(html.includes('Request a discount decision'), 'title from the gate of the analysis shown');
  assert.ok(html.includes('Saved analysis from') && html.includes('No new provider request was made.') && !html.includes('Generated '));
  const replay = action({ id: 'DL-002', priority: item, context, service: true, entry: ready(envelope(item, { recommendation: { ...r, engine_mode: 'replay' }, analysis: { outcome: 'jev_applied', provider_requests: 3 } })) }).html;
  assert.ok(replay.includes('Rules + Jev · recorded replay') && replay.includes('not a live provider call'));
  const fallback = action({ id: 'DL-002', priority: item, context, service: true, entry: ready(envelope(item, { analysis: { outcome: 'jev_unavailable', fallback_reason: 'usage_budget_blocked' } })) }).html;
  assert.ok(fallback.includes('Jev unavailable · rules shown') && fallback.includes('usage_budget_blocked') && !fallback.includes('>Rules + Jev<'));
  const p05 = ranking.items.find(i => i.deal_id === 'DL-005');
  const discovery = action({ id: 'DL-005', priority: p05, context: joined('DL-005'), service: true, entry: ready(envelope(p05, { analysis: { outcome: 'not_eligible', fallback_reason: 'insufficient_evidence' } })) }).html;
  assert.ok(discovery.includes('More information needed') && discovery.includes('No provider request was made.'));
});

test('REAL HTTP evidence drawer: I0348 opens its own record verbatim, closable, with a route to the graph and its original edge', () => {
  const context = joined('DL-002');
  const record = context.evidence.find(e => e.source_id === 'I0348' && e.source_file.endsWith('interactions.jsonl'));
  assert.ok(record);
  const html = render(React.createElement(EvidenceDrawer, { mode: 'side', titleId: 'drawer-title', onClose: noop },
    React.createElement(EvidenceInspector, { context, selection: { kind: 'evidence', id: record.id }, titleId: 'drawer-title', onGraph: noop })));
  assert.ok(html.includes('aria-labelledby="drawer-title"') && html.includes('id="drawer-title"') && html.includes('aria-label="Close evidence panel"'));
  assert.ok(html.includes(escape(evidenceTitle(record).title)) && html.includes(escape(interactionMeta(record).message)));
  assert.ok(html.includes('>I0348<') && html.includes(escape(record.id)) && html.includes('Show in graph: I0348'));
  assert.ok(!html.includes(`<h4>${escape(evidenceTitle(record).title)}</h4>`), 'Single record: the card does not repeat the drawer title');
  const edge = context.graph.edges.find(e => e.source === 'I0348' && e.target === 'P02' && e.relation === 'interaction_for');
  assert.ok(edge);
  const edgeHtml = render(React.createElement(EvidenceInspector, { context, selection: { kind: 'edge', id: edge.id }, titleId: 't', onGraph: noop }));
  assert.ok(edgeHtml.includes('interaction with account') && edgeHtml.includes('interaction_for') && edgeHtml.includes('I0348 → P02') && edgeHtml.includes('Direct from source'));
});

test('REAL HTTP graph proof: priority paths open as a highlighted union within the 24-node cap, edges keep direction', () => {
  for (const id of ['DL-002', 'DL-004']) {
    const item = ranking.items.find(i => i.deal_id === id), context = joined(id);
    const html = render(React.createElement(ContextGraph, { context, selection: null, onSelect: noop, initialPaths: item.evidence_paths }));
    assert.ok(html.includes(`Showing ${item.evidence_paths.length} supporting paths`));
    const nodes = (html.match(/class="focus-node/g) ?? []).length;
    assert.ok(nodes > 0 && nodes <= 24);
    const pathEdges = new Set(item.evidence_paths.flatMap(path => path.edge_ids));
    assert.equal((html.match(/class="graph-edge [^"]*on-path/g) ?? []).length, pathEdges.size, `${id}: every path edge is drawn and marked`);
    assert.ok(html.includes(`Deal ${escape(context.deal.account_name)}`));
    for (const edgeId of pathEdges) { const edge = context.graph.edges.find(e => e.id === edgeId); assert.ok(html.includes(`${edge.source} to ${edge.target}`), `${id}: ${edgeId} keeps source → target`); }
  }
});

test('STATIC guard: one automatic analysis per opened deal through the store; GET views, tabs and panels never request one', () => {
  const read = file => fs.readFileSync(path.join(src, file), 'utf8');
  const workspace = read('components/DealWorkspace.tsx'), dashboard = read('Dashboard.tsx'), tabs = read('components/DealTabs.tsx'), store = read('lib/analysis.ts');
  assert.equal((workspace.match(/store\.ensure\(/g) ?? []).length, 1);
  assert.match(workspace, /useEffect\(\(\) => \{ if \(store && snapshot && revision\) store\.ensure\(deal\.deal_id, snapshot, revision\); \}, \[store, deal\.deal_id, snapshot, revision\]\)/);
  assert.match(workspace, /contextRevision\(baseContext\)/, 'analysis is keyed by the loaded context revision');
  assert.match(workspace, /<ContextGraph key=\{graph\.key\} initialFocus=\{graph\.focus\} initialPaths=\{graph\.paths\}/, 'graph follows the active analysis version');
  assert.match(workspace, /version: view\.versionKey/, 'graph requests record the analysis version they were made for');
  assert.equal((workspace.match(/store\.refresh\(/g) ?? []).length, 1, 'refresh only from the explicit button handler');
  for (const file of [workspace, dashboard, tabs]) assert.ok(!/api\.analy[sz]e?\w*\(/.test(file), 'components never call the analysis endpoints directly');
  assert.equal((store.match(/request\(dealId, refresh/g) ?? []).length, 1);
  assert.match(store, /ensure\(dealId: string, snapshot: string, revision: string\) \{ if \(!entries\.has/);
  assert.match(dashboard, /analysisStoreFor\(api\)/);
  assert.deepEqual(tabs.match(/[A-Za-z]+=\{(?:canRefresh \? )?onRefresh(?: : undefined)?\}/g), ['retry={canRefresh ? onRefresh : undefined}', 'onClick={onRefresh}']);
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
  assert.ok(visible.includes('Open source I0348:'));
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
  assert.ok(fields.includes('<dl') && fields.includes('Organization') && fields.includes('Not provided'));
  const card = render(React.createElement(EvidenceCard, {evidence:record,context,onGraph:noop}));
  assert.ok(card.includes(escape(record.excerpt)), 'Full raw record remains in source details');
  const message = joined('DL-002').evidence.find(e => e.source_id === 'I0348');
  const quote = render(React.createElement(SourceContent, {evidence:message}));
  assert.ok(quote.includes(escape(englishText(interactionMeta(message).message))));
});


test('REAL HTTP plan export carries the complete action, approval gates, unknowns and source locators for all five deals', () => {
  const { buildFollowUpBrief } = require(path.join(build, 'lib/planning.js'));
  for (const item of ranking.items) {
    const c = joined(item.deal_id), r = item.recommendation;
    const brief = buildFollowUpBrief(r, c, '2026-10-01');
    assert.ok(brief.includes(r.action)); assert.ok(brief.includes(r.milestone));
    assert.ok(brief.includes(c.deal.account_name)); assert.ok(brief.includes('2026-10-01'));
    assert.ok(brief.includes('Not sent, not saved to CRM, and not approval.'));
    for (const line of [...r.approvals_needed, ...r.unknowns, ...c.unknowns]) assert.ok(brief.includes(line));
    for (const id of r.evidence_ids) { const e = c.evidence.find(x => x.id === id); assert.ok(brief.includes(id)); if (e) assert.ok(brief.includes(e.source_file) && brief.includes(e.source_id)); }
    if (!r.approvals_needed.length) assert.ok(brief.includes('This does not mean the action is approved.'));
  }
});
test('MOCK presentation titles only translate exact gate values of the analysis shown', () => {
  const { taskHeading } = require(path.join(build, 'lib/planning.js'));
  const item = ranking.items.find(x => x.deal_id === 'DL-002');
  const { gateSummary } = require(path.join(build, 'lib/present.js'));
  assert.equal(taskHeading(gateSummary(item)).title, 'Request a discount decision');
  assert.equal(taskHeading('MOCK syarat berbeda').title, 'Prepare the next step');
  assert.equal(taskHeading('MOCK syarat berbeda').note, 'MOCK syarat berbeda');
  assert.equal(taskHeading(null).title, 'Prepare the next step');
  assert.equal(taskHeading('approval VP Sales tertunda; kesediaan/izin kandidat referensi belum ada').title, 'Prepare the next step', 'combined gates are not shortened to one');
});
test('MOCK plan with missing owner, source and target never claims a completed task or available evidence', () => {
  const { buildFollowUpBrief } = require(path.join(build, 'lib/planning.js'));
  const r = { ...ranking.items[0].recommendation, owner_id: null, action: 'MOCK jangan bertindak sebelum konfirmasi.', milestone:'', approvals_needed:[], unknowns:[], evidence_ids:['missing-record'], precedent_ids:[] };
  const brief = buildFollowUpBrief(r, null, null);
  assert.ok(brief.includes('Not specified'));
  assert.ok(brief.includes('missing-record (source unavailable)'));
  assert.ok(brief.includes('not confirmation of no risk'));
  assert.ok(brief.includes(r.action));
});

test('REAL HTTP plan dialog keeps approval and consent text visible while original export remains available', () => {
  const { FollowUpPlan } = require(path.join(build, 'components/FollowUpPlan.js'));
  for (const id of ['DL-002','DL-004']) {
    const c = joined(id), r = ranking.items.find(x => x.deal_id === id).recommendation;
    const html = render(React.createElement(FollowUpPlan, { recommendation:r, context:c, snapshot:'2026-10-01', onClose:noop }));
    assert.ok(html.includes('aria-labelledby=') && html.includes('aria-describedby='));
    assert.ok(html.includes('Copy plan') && html.includes('Not sent or saved to CRM.'));
    for (const gate of r.approvals_needed) assert.ok(html.indexOf(escape(englishText(gate))) < html.indexOf('Full text &amp; sources'));
    if (id === 'DL-004') assert.ok(html.indexOf('a candidate is not permission') < html.indexOf('Full text &amp; sources'));
    assert.ok(html.includes('readOnly=""') && html.includes(escape(r.action)));
  }
});


test('compact gates remain visible and follow the gate of the analysis shown', () => {
  const { gateLabel } = require(path.join(build, 'lib/planning.js'));
  const { gateSummary } = require(path.join(build, 'lib/present.js'));
  for (const item of ranking.items) {
    const label = gateLabel(gateSummary(item), item.recommendation.approvals_needed);
    const html = action({ id: item.deal_id, priority: item, context: joined(item.deal_id) }).html;
    const gate = html.match(/<details class="move-boundary">([\s\S]*?)<\/details>/)[1];
    assert.ok(gate.includes(`<span>${escape(label)}</span>`));
    assert.ok(gate.indexOf(escape(label)) < gate.indexOf('</summary>'), 'Condition visible while details are closed');
    assert.equal(gateLabel(null, []), 'Review action conditions');
  }
  assert.equal(gateLabel(null, ['approval pending']), 'Approval required');
});
