import test from 'node:test';
import assert from 'node:assert/strict';
import { createAnalysisSession } from '../src/lib/analysisSession.ts';
const deferred = () => { let resolve, reject; const promise = new Promise((a,b) => { resolve=a; reject=b; }); return { promise, resolve, reject }; };
const response = id => ({ deal_id: id, unknowns: ['Still insufficient'], engine_mode: 'rules' });

test('request lifecycle is idle -> running -> received, preserves unknowns without inventing business status', async () => {
  const pending=deferred(), session=createAnalysisSession(() => pending.promise);
  assert.equal(session.getSnapshot().status,'idle');
  const running=session.run();
  assert.equal(session.getSnapshot().status,'running');
  pending.resolve(response('DL-005')); await running;
  assert.equal(session.getSnapshot().status,'received');
  assert.deepEqual(session.getSnapshot().data.unknowns,['Still insufficient']);
  assert.equal(session.getSnapshot().data.analysis_status,undefined);
});
test('failed request can retry and never retains a previous success as current output', async () => {
  let fail=false;
  const session=createAnalysisSession(async()=>{if(fail) throw new Error('503'); return response('DL-002');});
  await session.run(); fail=true; await session.run();
  assert.equal(session.getSnapshot().status,'failed');
  assert.equal(session.getSnapshot().data,null);
  fail=false; await session.run(); assert.equal(session.getSnapshot().status,'received');
});
test('refresh cancels the request and late success cannot repopulate a cleared session', async () => {
  const pending=deferred(); let signal;
  const session=createAnalysisSession(s=>{signal=s; return pending.promise;});
  const run=session.run(); session.reset();
  assert.equal(signal.aborted,true);
  pending.resolve(response('DL-001')); await run;
  assert.deepEqual(session.getSnapshot(),{status:'idle',data:null,error:null});
});
test('fast deal switch: old success and old error cannot affect the active deal', async () => {
  for (const lateError of [false,true]) {
    const pending=deferred(), old=createAnalysisSession(()=>pending.promise), active=createAnalysisSession(async()=>response('DL-005'));
    const run=old.run(); old.reset(); await active.run();
    if(lateError) pending.reject(new Error('late failure')); else pending.resolve(response('DL-002'));
    await run;
    assert.equal(old.getSnapshot().status,'idle');
    assert.equal(active.getSnapshot().data.deal_id,'DL-005');
  }
});
test('superseded request completing after retry cannot replace newer output', async () => {
  const old=deferred(); let calls=0;
  const session=createAnalysisSession(()=>++calls===1?old.promise:Promise.resolve(response('new')));
  const first=session.run(); await session.run();
  old.resolve(response('old')); await first;
  assert.equal(session.getSnapshot().data.deal_id,'new');
});
test('unmounted subscribers stop receiving updates and reset removes a completed result', async () => {
  const session=createAnalysisSession(async()=>response('DL-001')); let changes=0;
  const unsubscribe=session.subscribe(()=>changes++);
  await session.run(); assert.equal(changes,2); unsubscribe(); session.reset();
  assert.equal(changes,2); assert.equal(session.getSnapshot().status,'idle');
});
