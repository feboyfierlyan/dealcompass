// Real HTTP import -> scoped frontend API/validators, using a rules-only backend.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {workspaceApi,liveApi}=require(`${process.env.API_TEST_BUILD}/api.js`);
const {matchPipeline}=require(`${process.env.API_TEST_BUILD}/phase3.js`);
const base=process.env.GRAPH_API_URL || 'http://127.0.0.1:8000';
for(const count of [1,6]) test(`NEW DATA HTTP: ${count} unseen deals render through frontend validators with their own snapshot`,async()=>{
 const transport=global.fetch;
 const sample=await (await transport(`${base}/api/import/template`)).json();
 const original=structuredClone(sample.tables);
 for(let i=2;i<=count;i++) for(const [file,rows] of Object.entries(original)){
  let text=JSON.stringify(rows[0]);
  for(const prefix of ['ACME','SELLER','BUYER','OPP','CALL']) text=text.replaceAll(`${prefix}01`,`${prefix}${String(i).padStart(2,'0')}`);
  sample.tables[file].push(JSON.parse(text.replaceAll('jamie@',`jamie${i}@`).replaceAll('alex@',`alex${i}@`)));
 }
 const imported=await transport(`${base}/api/import`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(sample)});
 assert.equal(imported.status,200); const receipt=await imported.json();
 const api=workspaceApi(receipt.workspace_id), signal=()=>new AbortController().signal;
 global.fetch=(url,opts)=>transport(new URL(url,base),opts);
 try{
  const list=await api.list(signal()); assert.equal(list.items.length,count);assert.equal(list.snapshot_date,'2026-10-10');
  const priorities=await api.priorities(signal());matchPipeline(list,priorities);
  const findings=await api.diagnostics(signal());matchPipeline(list,findings);assert.equal(findings.statistical_assessment.sample_size,count);
  const context=await api.context('OPP01',signal());assert.equal(context.deal.account_name,'Northstar Retail');
  const diagnostic=await api.diagnostic('OPP01',signal());assert.equal(diagnostic.snapshot_date,list.snapshot_date);
  assert.equal((await liveApi.list(signal())).items.length,5);
 }finally{global.fetch=transport;}
});
