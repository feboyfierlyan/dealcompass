// HTTP tests use actual rules backend. Corruption/transport cases below explicitly mock responses.
const { test, before } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const React = require('react');
const { renderToStaticMarkup: render } = require('react-dom/server');
const build = process.env.PHASE3_TEST_BUILD;
assert.ok(build, 'Compile DealTabs, Phase3Panels, api and resource; set PHASE3_TEST_BUILD');
const p = require(path.join(build, 'lib/phase3.js'));
const { liveApi } = require(path.join(build, 'lib/api.js'));
const { createResource } = require(path.join(build, 'lib/resource.js'));
const { PriorityFactors, DiagnosticPanel, Statistics } = require(path.join(build, 'components/Phase3Panels.js'));
const { ActionTab, ReasonsTab } = require(path.join(build, 'components/DealTabs.js'));
const { gateSummary, recommendationView, splitUnknowns } = require(path.join(build, 'lib/present.js'));
const { evidenceGraphLinks } = require(path.join(build, 'lib/analysisView.js'));
const { focusTarget, indexGraph, visibleGraph } = require(path.join(build, 'lib/graphView.js'));
const base = process.env.GRAPH_API_URL || 'http://127.0.0.1:8000';
const signal = () => new AbortController().signal;
const clone = structuredClone;
const escape = s => s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#x27;');
let list, ranking, diagnostic, contexts, singles;
before(async () => {
  const original = global.fetch;
  const paths = [];
  global.fetch = (url, options) => { paths.push(url); assert.equal(options.method,'GET'); return original(new URL(url,base),options); };
  try {
    [list,ranking,diagnostic] = await Promise.all([liveApi.list(signal()),liveApi.priorities(signal()),liveApi.diagnostics(signal())]);
    contexts = new Map(); singles = new Map();
    for (const d of list.items) {
      contexts.set(d.deal_id,await liveApi.context(d.deal_id,signal()));
      singles.set(d.deal_id,await liveApi.diagnostic(d.deal_id,signal()));
    }
    assert.ok(paths.includes('/api/pipeline/priorities') && paths.includes('/api/pipeline/initial-analysis'));
    assert.equal(paths.filter(p => p.startsWith('/api/deals/') && p.endsWith('/initial-analysis')).length,5);
  } finally { global.fetch = original; }
});
test('REAL HTTP: all three phase3 endpoints, ID/snapshot join and API sorting survive shuffled arrays without mutating inputs', () => {
  assert.ok(p.isPriorities(ranking)); assert.ok(p.isPipelineDiagnostic(diagnostic));
  p.matchPipeline(list,diagnostic);
  const shuffled = clone(ranking); shuffled.items.reverse();
  const source = clone(list); source.items.reverse(); const before = clone([source,shuffled]);
  assert.deepEqual(p.rankedDeals(source,shuffled).map(d => d.account_id),['P04','P01','P02','P03','P05']);
  assert.deepEqual([source,shuffled],before);
});
for (const id of ['DL-001','DL-002','DL-003','DL-004','DL-005']) test(`${id} REAL HTTP: priority/diagnostic render intact, sources resolve and original graph edges remain reachable`, () => {
  const item = ranking.items.find(i => i.deal_id === id), d = singles.get(id), context = contexts.get(id);
  assert.deepEqual({...d,schema_version:undefined},{...diagnostic.deals.find(d => d.deal_id === id),schema_version:undefined});
  const joined = p.enrichContext(p.enrichContext(context,item),d);
  // Same composition as the app: ranking recommendation in layer 1, reasons in layer 2, factors/diagnostic in layer 3. No POST.
  const noop = () => {};
  const view = recommendationView({ dealId: id, priority: item, session: { status: 'idle', data: null }, preferred: 'priority' });
  assert.equal(view.source,'priority');
  const action = render(React.createElement(ActionTab,{context:joined,priority:item,rankingState:'ready',view,fixture:false,snapshot:joined.snapshot_date,session:{status:'idle',error:null,receivedAt:null},onEvidence:noop,onReasons:noop,onShowPaths:noop,onAnalyze:noop,onShowVersion:noop}));
  const html = action + render(React.createElement(React.Fragment,null,
    React.createElement(ReasonsTab,{priority:item,view,context:joined,onEvidence:noop,onEdge:noop,onShowPath:noop}),
    React.createElement(PriorityFactors,{item,onEvidence:noop}),
    React.createElement(DiagnosticPanel,{data:d,onEvidence:noop})));
  const gate = gateSummary(item);
  if (gate) assert.ok(action.includes(escape(gate)),'Ranking gate stays in layer 1');
  for (const text of [...item.recommendation.approvals_needed,...splitUnknowns(item.recommendation,joined).specific]) assert.ok(action.includes(escape(text)),`Layer 1 keeps approval/unknown: ${text.slice(0,60)}`);
  assert.ok(action.indexOf('Mengapa perlu diperhatikan') < action.indexOf('Tindakan yang disarankan') && action.indexOf('Tindakan yang disarankan') < action.indexOf('Penanggung jawab'));
  assert.ok(action.includes('Dari urutan prioritas · data per 1 Okt 2026'));
  for (const label of ['Status request sesi','GET ranking','POST analisis','Tier acceleration']) assert.ok(!action.includes(label),`No technical label in layer 1: ${label}`);
  for (const text of [...item.rationale,...item.limitations,item.recommendation.action,item.recommendation.milestone,...item.recommendation.approvals_needed,...item.recommendation.unknowns,...item.recommendation.precedent_comparison,...d.boundaries]) assert.ok(html.includes(escape(text)),text);
  for (const f of [...d.findings,...d.reference_candidates]) for (const text of [f.fact,f.interpretation,...f.missing_information,...f.follow_up_implication]) assert.ok(html.includes(escape(text)),text);
  const index = indexGraph(joined);
  for (const evidenceId of new Set([...p.evidenceIds(item),...p.evidenceIds(d)])) {
    assert.ok(joined.evidence.some(e => e.id === evidenceId), evidenceId);
    for (const edge of evidenceGraphLinks(joined,evidenceId).edges) {
      const focused = focusTarget(index,{kind:'edge',id:edge.id});
      assert.ok(focused.ids.length <= 24);
      assert.ok(visibleGraph(index,focused.ids).edges.some(e => e.id === edge.id));
    }
  }
  if(id==='DL-001') assert.match(item.recommendation.action,/identitas inferensi.*dikonfirmasi/);
  if(id==='DL-002') { assert.match(item.recommendation.approvals_needed.join(' '),/VP Sales.*20%.*Belum ada keputusan sah/); assert.ok(html.includes('DL-002 → P02 ← I0348')); }
  if(id==='DL-003'||id==='DL-004') { assert.match(item.recommendation.action,/memeriksa pengalaman terbaru.*menanyakan kesediaan.*izin kontak.*sebelum perkenalan/); }
  if(id==='DL-004') assert.match(item.recommendation.precedent_comparison.join(' '),/overlap tidak membuktikan saling kenal/);
  if(id==='DL-005') { assert.equal(item.priority_kind,'discovery'); assert.equal(item.analysis_status,'insufficient_evidence'); assert.equal(item.factors.find(f => f.name==='skor_prioritas').value,null); assert.ok(html.includes('Belum tersedia (null)')); assert.ok(action.includes('Ini bukan tanda deal gagal, kalah, atau bebas risiko.')); }
  else assert.ok(!action.includes('Ini bukan tanda deal gagal'),'Discovery wording only for discovery items');
});
test('REAL HTTP: not_assessed reason/nulls and graph identity are preserved', () => {
  const html=render(React.createElement(Statistics,{data:diagnostic,onEvidence:()=>{}}));
  assert.ok(html.includes(escape(diagnostic.statistical_assessment.reason)));
  assert.ok(html.includes('not_assessed')); assert.ok(html.includes('Belum diketahui / tidak tersedia'));
  for(const item of ranking.items) {
    const c=contexts.get(item.deal_id), merged=p.enrichContext(c,item);
    assert.equal(merged.graph,c.graph);
  }
});
test('SYNTHETIC registry: source outside graph stays readable without inventing node/edge; context conflict is rejected', () => {
  const context=contexts.get('DL-005'), item=clone(ranking.items.find(i=>i.deal_id==='DL-005'));
  const extra={id:'synthetic:outside',source_file:'synthetic.csv',source_id:'outside',date:null,excerpt:'SYNTHETIC additional evidence',evidence_type:'direct'};
  item.evidence.push(extra);item.evidence_ids.push(extra.id);
  const joined=p.enrichContext(context,item);assert.deepEqual(joined.evidence.find(e=>e.id===extra.id),extra);
  assert.deepEqual(evidenceGraphLinks(joined,extra.id),{node:null,edges:[]});assert.equal(joined.graph,context.graph);
  item.evidence.push({...context.evidence[0],excerpt:'conflicting'});assert.throws(()=>p.enrichContext(context,item),/Konflik/);
});
test('CORRUPTED PAYLOAD: incomplete/duplicate ranks, unknown enum, nonfinite values and wrong recommendation rejected wholesale', () => {
  for(const mutate of [x=>x.items.pop(),x=>x.items[1].rank=x.items[0].rank,x=>x.items[0].rank=6,x=>x.items[0].rank=1.5,x=>x.items[1].deal_id=x.items[0].deal_id,x=>x.items[0].priority_kind='closing',x=>x.items[0].analysis_status='approved',x=>x.engine_mode='jev',x=>x.items[0].factors[0].value=Infinity,x=>delete x.methodology.ordered_rules,x=>x.items[0].recommendation.deal_id='wrong',x=>x.items[0].recommendation.evidence_ids.push('missing')]) {
    const invalid=clone(ranking);mutate(invalid);assert.equal(p.isPriorities(invalid),false);
  }
});
test('CORRUPTED PAYLOAD: schema/snapshot/account/set mismatches never join by array position', () => {
  for(const mutate of [x=>x.schema_version='v2',x=>x.snapshot_date='2026-10-02']) { const invalid=clone(ranking);mutate(invalid);assert.equal(p.isPriorities(invalid),false); }
  for(const mutate of [x=>x.items[0].account_id='P99',x=>x.items[0].deal_id='DL-999',x=>x.snapshot_date='2026-10-02']) { const invalid=clone(ranking);mutate(invalid);assert.throws(()=>p.matchPipeline(list,invalid)); }
  const invalid=clone(diagnostic);invalid.deals[0].account_id='P99';assert.equal(p.isPipelineDiagnostic(invalid),false);
});
test('CORRUPTED PAYLOAD: diagnostic required metrics, enums, registry and statistical nulls enforced', () => {
  for(const mutate of [x=>delete x.deals[0].metrics.interactions.customer,x=>x.deals[0].metrics.deal_age_days=NaN,x=>x.deals[0].findings[0].interpretation_type='confirmed',x=>x.deals[0].findings[0].category='outlier',x=>x.deals[0].findings[0].evidence_ids.push('missing'),x=>x.deals.push(x.deals[0]),x=>x.statistical_assessment.status='assessed',x=>x.statistical_assessment.outlier_deal_ids=[],x=>x.statistical_assessment.threshold=0,x=>delete x.statistical_assessment.reason]) {
    const invalid=clone(diagnostic);mutate(invalid);assert.equal(p.isPipelineDiagnostic(invalid),false);
  }
});
test('CORRUPTED SOURCES: equal IDs deduplicate independent of field order; conflicting content/provenance is rejected without mutation', () => {
  const e=ranking.items[0].evidence[0], reversed=Object.fromEntries(Object.entries(e).reverse());
  assert.deepEqual(p.mergeEvidence([e],[reversed]),[e]);
  for(const patch of [{excerpt:'different'},{evidence_type:'inferred'},{source_file:'different'}]) assert.throws(()=>p.mergeEvidence([e],[{...e,...patch}]),/Konflik/);
  const invalid=clone(ranking);invalid.items[0].evidence.push({...e,excerpt:'different'});assert.equal(p.isPriorities(invalid),false);
});
test('CORRUPTED PATHS: reverse traversal preserves arrows; fake/shortcut/disconnected edges and missing provenance rejected', () => {
  const item=ranking.items.find(i=>i.deal_id==='DL-002'),context=contexts.get('DL-002');
  p.validatePaths(item,context);
  for(const mutate of [x=>x.evidence_paths[0].node_ids[0]='fake',x=>x.evidence_paths[0].edge_ids[0]='fake',x=>x.evidence_paths[0].node_ids.reverse(),x=>x.evidence_paths[0].evidence_ids.push('fake')]) {
    const invalid=clone(item);mutate(invalid);assert.throws(()=>p.validatePaths(invalid,context));
  }
});
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
test('MOCK lifecycle: refresh clears old ranking before completion; error keeps no ranking and retry recovers', async()=>{
  let mode='ok';const pending=deferred();const resource=createResource(()=>mode==='wait'?pending.promise:mode==='error'?Promise.reject(new Error('503')):Promise.resolve(ranking));
  await resource.run(); mode='wait';const run=resource.run(); assert.equal(resource.getSnapshot().data,null);assert.equal(resource.getSnapshot().status,'loading');
  pending.reject(new Error('503'));await run;assert.equal(resource.getSnapshot().status,'error');assert.equal(resource.getSnapshot().data,null);
  mode='ok';await resource.run();assert.equal(resource.getSnapshot().data,ranking);
});
test('MOCK lifecycle: switch/reset ignores late success and error even when transport ignores abort', async()=>{
  for(const fail of [false,true]) {const pending=deferred();let signal;const r=createResource(s=>{signal=s;return pending.promise;});const run=r.run();r.reset();assert.equal(signal.aborted,true);if(fail)pending.reject(new Error('late'));else pending.resolve(ranking);await run;assert.equal(r.getSnapshot().status,'idle');assert.equal(r.getSnapshot().data,null);}
});
test('MOCK lifecycle: superseded diagnostic cannot replace new result or clear independent priorities', async()=>{
  const pending=deferred();let calls=0;const r=createResource(()=>++calls===1?pending.promise:Promise.resolve('new'));const priorities=createResource(async()=>ranking);await priorities.run();const old=r.run();await r.run();pending.reject(new Error('old error'));await old;assert.equal(r.getSnapshot().data,'new');assert.equal(priorities.getSnapshot().data,ranking);
});
test('MOCK transport: all phase3 methods distinguish 501/503, invalid200, network and timeout', async t=>{
  const methods=[s=>liveApi.priorities(s),s=>liveApi.diagnostics(s),s=>liveApi.diagnostic('DL-001',s)];
  for(const call of methods) {
    for(const status of [501,503,200]) {t.mock.method(global,'fetch',async()=>new Response('{}',{status}));await assert.rejects(call(signal()),e=>e.status===(status===200?502:status));t.mock.restoreAll();}
    t.mock.method(global,'fetch',async()=>{throw new TypeError('offline');});await assert.rejects(call(signal()),e=>e.status===0);t.mock.restoreAll();
    t.mock.timers.enable({apis:['setTimeout']});t.mock.method(global,'fetch',(_,opts)=>new Promise((resolve,reject)=>opts.signal.addEventListener('abort',()=>reject(new Error('abort')))));
    const run=call(signal());t.mock.timers.tick(20000);await assert.rejects(run,e=>e.status===408);t.mock.restoreAll();t.mock.timers.reset();
  }
});
test('MOCK transport: single diagnostic rejects wrong deal response', async t=>{
  t.mock.method(global,'fetch',async()=>new Response(JSON.stringify(singles.get('DL-002'))));
  await assert.rejects(liveApi.diagnostic('DL-001',signal()),e=>e.status===502);
});
