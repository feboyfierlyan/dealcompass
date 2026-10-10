"""Run frozen cases through public API; local rules via the same API, never local Jev.

python -m evaluation.deal_benchmark.run --local
python -m evaluation.deal_benchmark.run --live-cloud https://dealcompass-production.up.railway.app
No retries/refresh, no keys, no new usage ledger. Cloud execution is explicitly opt-in.
"""
import argparse
import hashlib
import json
import os
import statistics
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).parent
RESULTS=ROOT/'results'


def load_frozen():
    manifest=json.loads((ROOT/'frozen.json').read_text())
    for name,digest in manifest['files'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Frozen input changed: {name}')
    return json.loads((ROOT/'input.json').read_text()),json.loads((ROOT/'cases.json').read_text()),manifest


def family(action):
    text=action.lower()
    if 'discovery' in text: return 'discovery'
    if 'diskon' in text or 'keberatan harga' in text: return 'price'
    if 'referensi' in text or 'pengguna serupa' in text: return 'reference'
    return 'other'


def audit(context,envelope):
    rec=envelope['recommendation'];meta=envelope['analysis']
    evidence={r['id']:r for r in context['evidence']};nodes={n['id'] for n in context['graph']['nodes']};edges={e['id']:e for e in context['graph']['edges']}
    paths=meta['evidence_paths']
    valid_paths=bool(paths)
    for p in paths:
        ns=p['node_ids'];es=p['edge_ids'];evs=p['evidence_ids']
        valid_paths &= bool(ns) and len(es)==len(ns)-1 and bool(evs) and set(ns)<=nodes and set(evs)<=evidence.keys()
        for i,eid in enumerate(es):
            edge=edges.get(eid)
            valid_paths &= bool(edge) and i+1<len(ns)
            if edge and i+1<len(ns):
                valid_paths &= {edge['source'],edge['target']}=={ns[i],ns[i+1]} and bool(edge['evidence_ids']) and set(edge['evidence_ids'])<=set(evs)
    valid_edges=all(e['source'] in nodes and e['target'] in nodes and e['evidence_type'] in ('direct','inferred') and bool(e['evidence_ids']) and set(e['evidence_ids'])<=evidence.keys() for e in edges.values())
    candidates={r['decision_id'] for r in context['candidate_decisions']}
    return {'identity':rec['deal_id']==context['deal']['deal_id'] and envelope['snapshot_date']==context['snapshot_date'],
            'owner':rec['owner_id']==context['deal']['owner_id'],
            'action_and_target':bool(rec['action'].strip()) and bool(rec['milestone'].strip()),
            'citation_ids_resolve':bool(rec['evidence_ids']) and set(rec['evidence_ids'])<=evidence.keys(),
            'precedent_ids_resolve':set(rec['precedent_ids'])<=candidates,
            'graph_edges_resolve':bool(edges) and valid_edges,
            'supporting_paths_resolve':bool(valid_paths)}


def grade(case,context,envelope):
    checks=audit(context,envelope);rec=envelope['recommendation'];expected=case['expected']
    checks['action_family_screen']=family(rec['action'])==expected['action_family']
    checks['approval_gate_screen']=any('VP Sales' in a for a in rec['approvals_needed'])==expected['vp_gate']
    if expected['comparison_required']:
        checks['precedent_explanation_screen']=any('INTERPRETASI' in s and ('tidak' in s.lower() or 'berbeda' in s.lower() or 'lebih kecil' in s.lower()) for s in rec['precedent_comparison'])
    if expected['capacity_exception_required']:
        checks['capacity_exception_screen']=any('TIDAK dapat langsung menampung 30' in s for s in rec['precedent_comparison'])
    return checks


def run_client(client,arm,live):
    package,cases,manifest=load_frozen();RESULTS.mkdir(exist_ok=True)
    target=RESULTS/f'{arm}.json'
    if target.exists(): raise RuntimeError(f'{target.name} already exists; preserve first-run receipts. Use a versioned suite for another experiment.')
    res=client.post('/api/import',params={'allow_jev':str(live).lower()},json=package)
    res.raise_for_status();receipt=res.json();headers={'X-DealCompass-Workspace':receipt['workspace_id']}
    # Do not publish the workspace access handle.
    result={'started_at':datetime.now(timezone.utc).isoformat(),'arm':arm,'redaction':'Workspace access handle replaced by [workspace], including source_file prefixes.','frozen':manifest,'import':{k:v for k,v in receipt.items() if k!='workspace_id'},'cases':[],'limitations':['AI-authored synthetic challenge set, not independent human gold.','String-based action/approval screens are not semantic action accuracy.','Citation/graph structure checks do not establish claim entailment.','No causal evidence of faster closing or revenue uplift.','Live endpoint exposes request metadata, not per-request token receipts; billing remains in the existing Railway ledger.']}
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2).replace(receipt['workspace_id'],'[workspace]')+'\n')
    for case in cases:
        started=time.perf_counter();row={'id':case['id'],'title':case['title'],'checks':{},'error':None}
        try:
            c=client.get(f"/api/deals/{case['deal_id']}",headers=headers);c.raise_for_status();context=c.json()
            r=client.post(f"/api/deals/{case['deal_id']}/analysis",headers=headers);r.raise_for_status();envelope=r.json()
            row.update(context=context,envelope=envelope,checks=grade(case,context,envelope))
        except Exception as exc:
            # Preserve failed requests in denominators. Do not dump credentials/request headers.
            row['error']=f'{type(exc).__name__}: request/evaluation failed'
        row['latency_ms']=round((time.perf_counter()-started)*1000)
        result['cases'].append(row);target.write_text(json.dumps(result,ensure_ascii=False,indent=2).replace(receipt['workspace_id'],'[workspace]')+'\n')
        print(arm,case['id'], 'ERROR' if row['error'] else ','.join(k for k,v in row['checks'].items() if not v) or 'PASS',flush=True)
    result['completed_at']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(result,ensure_ascii=False,indent=2).replace(receipt['workspace_id'],'[workspace]')+'\n')
    return result


def report():
    rows=[]
    for path in sorted(RESULTS.glob('*.json')):
        if path.stem not in ('rules','hybrid'):continue
        r=json.loads(path.read_text());cases=r['cases'];n=len(json.loads((ROOT/'cases.json').read_text()))
        metrics={key:{'passed':sum(c['checks'].get(key) is True for c in cases),'total':n} for key in ['identity','owner','action_and_target','citation_ids_resolve','precedent_ids_resolve','graph_edges_resolve','supporting_paths_resolve','action_family_screen','approval_gate_screen']}
        for key,ids in [('precedent_explanation_screen',['B05','B06','B15','B16']),('capacity_exception_screen',['B16'])]:
            metrics[key]={'passed':sum(c['checks'].get(key) is True for c in cases if c['id'] in ids),'total':len(ids)}
        outcomes=Counter(c.get('envelope',{}).get('analysis',{}).get('outcome','error') for c in cases)
        rows.append({'arm':r['arm'],'metrics':metrics,'outcomes':dict(outcomes),'cases_completed':len(cases),'all_screens_passed':sum(not c['error'] and all(c['checks'].values()) for c in cases),'precedent_ids_checked':sum(len(c.get('envelope',{}).get('recommendation',{}).get('precedent_ids',[])) for c in cases),'errors':sum(bool(c['error']) for c in cases),'provider_requests_reported':sum(c.get('envelope',{}).get('analysis',{}).get('provider_requests',0) for c in cases),'median_roundtrip_ms':statistics.median(c['latency_ms'] for c in cases) if cases else None,'failed_cases':[{'id':c['id'],'failed':[k for k,v in c['checks'].items() if not v],'error':c['error']} for c in cases if c['error'] or not all(c['checks'].values())]})
    contexts_match=None
    if (RESULTS/'rules.json').exists() and (RESULTS/'hybrid.json').exists():
        local=json.loads((RESULTS/'rules.json').read_text());cloud=json.loads((RESULTS/'hybrid.json').read_text())
        contexts_match=sum(a.get('context')==b.get('context') for a,b in zip(local['cases'],cloud['cases']))
    summary={'normalized_context_pairs_equal':contexts_match,'generated_at':datetime.now(timezone.utc).isoformat(),'arms':rows,'human_review_completed':0,'external_benchmark_run':False}
    (RESULTS/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Deal Acceleration challenge v1 — actual results','', '16 frozen synthetic cases. Labels written by AI before execution; not independent human gold. Action and policy results are automated screens, not whole-app accuracy.','', '| Measure | '+' | '.join(r['arm'] for r in rows)+' |','|---|'+'---|'*len(rows)]
    for key in rows[0]['metrics'] if rows else []:
        lines.append('| '+key+' | '+' | '.join(f"{r['metrics'][key]['passed']}/{r['metrics'][key]['total']}" for r in rows)+' |')
    for r in rows:
        lines+=['',f"## {r['arm']}",f"All applicable screens passed: {r['all_screens_passed']}/16. Referenced precedent IDs checked: {r['precedent_ids_checked']}. Outcomes: {r['outcomes']}. API-reported provider requests: {r['provider_requests_reported']}. Median context + analysis roundtrip: {r['median_roundtrip_ms']} ms (different local/cloud environments; not a speed comparison).",'','Failures:']
        lines += [f"- {f['id']}: {', '.join(f['failed']) or f['error']}" for f in r['failed_cases']]
    lines+=['','## Claim limits',f'- Normalized local/cloud context pairs equal: {contexts_match}/16. Only access-handle prefixes redacted.','- Empty precedent lists satisfy ID integrity vacuously; do not interpret this as 16 precedent correctness judgments.','- Human adjudication: pending. Do not call these expert-labelled results.','- No SalesTranscriptQA run or external benchmark score.','- Graph and citation scores check referential structure, not semantic support.','- Include fallback/not-eligible cases in the deployed-app denominator.','- This suite measures decision-readiness checks; no measured closing uplift.']
    (RESULTS/'REPORT.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))


def main():
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--local',action='store_true');group.add_argument('--live-cloud');group.add_argument('--report',action='store_true');a=parser.parse_args()
    if a.local:
        from fastapi.testclient import TestClient
        from backend.main import app
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'DEALCOMPASS_UPLOAD_DIR':tmp,'DEALCOMPASS_ENGINE_MODE':'rules'}):
            with TestClient(app) as client:run_client(client,'rules',False)
    elif a.live_cloud:
        if a.live_cloud!='https://dealcompass-production.up.railway.app':raise SystemExit('Only the existing shared team backend is allowed. No local live ledger.')
        import httpx
        with httpx.Client(base_url=a.live_cloud,timeout=90,follow_redirects=False) as client:run_client(client,'hybrid',True)
    else:report()

if __name__=='__main__':main()
