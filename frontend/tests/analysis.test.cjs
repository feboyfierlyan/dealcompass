const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const build = process.env.ANALYSIS_TEST_BUILD;
assert.ok(build, 'Compile frontend components and set ANALYSIS_TEST_BUILD first');
const { ActionTab, ReasonsTab } = require(path.join(build, 'components/DealTabs.js'));
const { employeeFromContext, recommendationView, splitUnknowns } = require(path.join(build, 'lib/present.js'));
const { explanationGroups, evidenceGraphLinks } = require(path.join(build, 'lib/analysisView.js'));
const { indexGraph, focusTarget, visibleGraph } = require(path.join(build, 'lib/graphView.js'));
const { isContext, isRecommendation } = require(path.join(build, 'lib/contracts.js'));
const base = process.env.GRAPH_API_URL || 'http://127.0.0.1:8000';
const cases = [
  ['DL-001', /Rina Hapsari.*inferensi.*dikonfirmasi/i],
  ['DL-002', /Jangan menawarkan.*diskon 20%.*sebelum VP Sales/i],
  ['DL-003', /memeriksa pengalaman terbaru.*sebelum perkenalan/i],
  ['DL-004', /memeriksa pengalaman terbaru.*sebelum perkenalan/i],
  ['DL-005', /discovery.*sebelum menawarkan/i],
];
const escape = s => s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#x27;');
for (const [id, acceptance] of cases) test(`${id}: real rules response renders intact, retains uncertainty, and evidence opens actual graph`, async () => {
  const contextResponse=await fetch(`${base}/api/deals/${id}`), analysisResponse=await fetch(`${base}/api/deals/${id}/analyze`,{method:'POST'});
  assert.equal(contextResponse.status,200); assert.equal(analysisResponse.status,200);
  const context=await contextResponse.json(), r=await analysisResponse.json();
  assert.ok(isContext(context)); assert.ok(isRecommendation(r));
  assert.equal(r.engine_mode,'rules'); assert.equal(context.deal.rank,null);
  assert.match(r.action,acceptance, `${id}: action retains its business gate (P03/P04: verify latest experience before introduction)`);
  if(id==='DL-003'||id==='DL-004') {
    assert.match(r.action,/menanyakan kesediaan.*sebelum perkenalan/i, `${id}: ask willingness before introduction`);
    assert.match(r.action,/izin kontak.*sebelum perkenalan/i, `${id}: obtain contact permission before introduction`);
    assert.ok(r.unknowns.some(x=>/Kesesuaian, kesediaan dan izin kontak.*belum diketahui.*kandidat bukan izin/i.test(x)), `${id}: candidate suitability and consent remain unknown`);
  }
  if(id==='DL-002') assert.ok(r.approvals_needed.some(x=>/VP Sales.*20%.*Belum ada keputusan sah/.test(x)));
  if(id==='DL-004') assert.ok(r.precedent_comparison.some(x=>/overlap tidak membuktikan saling kenal/.test(x)));
  if(id==='DL-005') assert.ok(r.unknowns.some(x=>/tidak cukup.*bukan berarti tidak ada risiko/.test(x)));
  // An explicit re-analysis (POST) result, rendered by the same components the app uses.
  const view=recommendationView({dealId:id, priority:null, session:{status:'received', data:r}, preferred:'session'});
  assert.equal(view.source,'session');
  const noop=()=>{};
  const action=renderToStaticMarkup(React.createElement(ActionTab,{context, priority:null, rankingState:'unavailable', view, fixture:false, snapshot:context.snapshot_date, session:{status:'received', error:null, receivedAt:'10.00.00'}, onEvidence:noop, onReasons:noop, onShowPaths:noop, onAnalyze:noop, onShowVersion:noop}));
  const reasons=renderToStaticMarkup(React.createElement(ReasonsTab,{priority:null, view, context, onEvidence:noop, onEdge:noop, onShowPath:noop}));
  const html=action+reasons;
  for(const text of [r.action,r.milestone,...r.approvals_needed,...r.precedent_comparison,...r.unknowns,...context.unknowns]) assert.ok(html.includes(escape(text)), `Full API text retained: ${text.slice(0,80)}`);
  // Layer 1 reads action -> owner -> target -> approvals -> analysis-specific unknowns; reasons follow in the second tab.
  const order=(markup,headings)=>{for(let i=1;i<headings.length;i++) assert.ok(markup.indexOf(headings[i-1])>=0&&markup.indexOf(headings[i-1])<markup.indexOf(headings[i]),`${headings[i-1]} before ${headings[i]}`);};
  const specific=splitUnknowns(r,context).specific;
  order(action,['Tindakan yang disarankan','Lihat alasan &amp; bukti',escape(r.action),'Penanggung jawab','Target langkah berikutnya','Persetujuan yang diperlukan',...(specific.length?['Yang masih perlu dipastikan']:[]),'Mengapa perlu diperhatikan']);
  for(const text of specific) assert.ok(action.includes(escape(text)),`Analysis-specific unknown stays next to the action: ${text.slice(0,60)}`);
  for(const text of r.approvals_needed) assert.ok(action.includes(escape(text)),'Approvals stay in layer 1');
  if(!r.approvals_needed.length) assert.ok(action.includes('Ini tidak berarti tindakan sudah disetujui.'));
  // The precedent section only appears when the data holds candidate decisions; an empty "none" block is not rendered.
  order(reasons,['Bukti yang dirujuk saran ini',...(r.precedent_ids.length||context.candidate_decisions.length?['Keputusan terdahulu']:[]),'Penjelasan analisis','Informasi yang belum diketahui']);
  assert.ok(action.includes('Analisis berbasis aturan')); assert.ok(!html.includes('Jev live'));
  assert.ok(action.includes('Hasil analisis ulang yang Anda minta pukul 10.00.00 · urutan prioritas tidak dihitung ulang'));
  const owner=employeeFromContext(context,r.owner_id);
  if(owner) assert.ok(action.includes(escape(owner.name))&&action.includes(`>${r.owner_id}<`),'Owner name only from the employees.csv record, ID kept');
  else if(r.owner_id) assert.ok(action.includes(`ID karyawan ${r.owner_id}`),'Owner without a verifiable name stays an ID');
  const index=indexGraph(context);
  for(const evidenceId of r.evidence_ids) {
    const record=context.evidence.find(e=>e.id===evidenceId); assert.ok(record);
    const links=evidenceGraphLinks(context,evidenceId);
    for(const edge of links.edges) {
      assert.ok(edge.evidence_ids.includes(evidenceId));
      const focus=focusTarget(index,{kind:'edge',id:edge.id});
      assert.ok(focus.ids.length<=24);
      assert.ok(visibleGraph(index,focus.ids).edges.some(e=>e.id===edge.id));
    }
    if(links.node) { assert.equal(links.node.id,record.source_id); assert.ok(focusTarget(index,{kind:'node',id:links.node.id}).ids.includes(record.source_id)); }
  }
});
test('unprefixed statements remain explanation, not facts guessed by the UI',()=>{
  const lines=['FAKTA | original','INTERPRETASI | inference','SKENARIO | proposal','An untyped assertion','FAKTA without delimiter'];
  const groups=explanationGroups(lines);
  assert.deepEqual(groups.PENJELASAN,lines.slice(3));
  assert.deepEqual(Object.values(groups).flat().sort(),[...lines].sort());
});
test('non-node evidence uses citing relations only; missing evidence or unsupported aliases never create links',()=>{
  const context={ evidence:[{id:'history:row',source_id:'K01|Company|2020'},{id:'uncited',source_id:'K01'}], graph:{nodes:[{id:'K01'},{id:'Company'}],edges:[{id:'edge',source:'K01',target:'Company',evidence_ids:['history:row']}]}};
  assert.equal(evidenceGraphLinks(context,'history:row').node,null);
  assert.equal(evidenceGraphLinks(context,'history:row').edges[0].id,'edge');
  assert.deepEqual(evidenceGraphLinks(context,'missing'),{node:null,edges:[]});
  assert.deepEqual(evidenceGraphLinks(context,'uncited'),{node:null,edges:[]});
});
test('long evidence paths disclose truncation and still include exact selected edge endpoints',()=>{
  const nodes=Array.from({length:40},(_,i)=>({id:String(i),label:String(i),type:'test'}));
  const edges=nodes.slice(1).map((node,i)=>({id:`edge-${i}`,source:String(i),target:node.id,evidence_ids:[],evidence_type:'direct'}));
  const index=indexGraph({deal:{deal_id:'0'},graph:{nodes,edges}});
  const focused=focusTarget(index,{kind:'edge',id:'edge-38'});
  assert.equal(focused.truncated,true); assert.equal(focused.ids.length,24);
  assert.ok(focused.ids.includes('38')&&focused.ids.includes('39'));
  assert.equal(focusTarget(index,{kind:'node',id:'missing'}).ids.length,0);
});
