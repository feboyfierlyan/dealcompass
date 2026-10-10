"""Prepare empty review forms or summarize actual, identified human reviews only."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).parent
CRITERIA=('action_acceptable','claims_supported_by_citations','approval_handling_correct','precedent_handling_correct')


def summarize(rows):
    seen=set();out={k:{'passed':0,'reviewed':0,'unreviewed':0} for k in CRITERIA}
    for row in rows:
        key=(row['case_id'],row['arm'])
        if key in seen:raise ValueError('Duplicate case/arm review; adjudicate before aggregating.')
        seen.add(key)
        for k in CRITERIA:
            value=row[k]
            if value is None:out[k]['unreviewed']+=1;continue
            if type(value) is not bool:raise ValueError('Ratings must be true, false or null.')
            if not row.get('reviewer','').strip() or not row.get('notes','').strip():raise ValueError('Completed ratings require reviewer and justification.')
            out[k]['reviewed']+=1;out[k]['passed']+=int(value)
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--score',type=Path);a=p.parse_args()
    if a.prepare:
        path=ROOT/'human_review_template.json'
        if path.exists():raise SystemExit('Template exists; preserve any filled reviews.')
        cases=json.loads((ROOT/'cases.json').read_text())
        rows=[{'case_id':c['id'],'arm':arm,'reviewer':'','notes':'',**{k:None for k in CRITERIA}} for c in cases for arm in ('rules','hybrid')]
        path.write_text(json.dumps(rows,indent=2)+'\n')
        ranking={'instructions':'Independently rank P01–P05 from sources before seeing system order. Ties allowed. Include rationale and evidence IDs. No expert labels have been supplied.','reviewer':'','tiers':[],'rationale':'','evidence_ids':[]}
        (ROOT/'human_ranking_template.json').write_text(json.dumps(ranking,indent=2)+'\n')
    elif a.score:
        print(json.dumps(summarize(json.loads(a.score.read_text())),indent=2))
    else:p.error('Choose --prepare or --score FILE')
