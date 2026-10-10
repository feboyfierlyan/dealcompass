"""Reproduce the presentation scorecard from actual eval receipts, without paid calls.

Run run_eval and baseline_crm first. Historical live classification stays separate.
Counts are scenario checks, not a held-out estimate of product accuracy.
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
ROOT=Path(__file__).parent
RESULTS=ROOT/'results'


def run():
    decision=json.loads((RESULTS/'latest.json').read_text())
    ranking=json.loads((RESULTS/'ranking_latest.json').read_text())
    baseline=json.loads((RESULTS/'baseline_latest.json').read_text())
    live=json.loads((RESULTS/'paraphrases_live.json').read_text())
    rows=decision['cases']
    real_rules=[r for r in rows if r['source'] in ('dataset_asli','sintetis')]
    transport=[r for r in rows if r['source'] in ('mock_jev','replay_mock')]
    metrics=[
        dict(id='decision',label='Rules decision scenario acceptance',passed=sum(r['passed'] for r in real_rules),total=len(real_rules),source='latest.json',scope='Original-data and developer-authored synthetic scenarios. Excludes mock/replay Jev.',measures='Specified action, approval, precedent and evidence checks; not human-rated answer accuracy.'),
        dict(id='ranking',label='Ranking rule conformance',passed=ranking['summary']['passed'],total=ranking['summary']['cases'],source='ranking_latest.json',scope='5 original-data + 10 synthetic scenarios.',measures='Ordering obeys declared heuristic and preserves gates/provenance; not best-deal prediction.'),
        dict(id='integrity',label='Demo recommendation integrity',passed=sum(all(d['invariants'].values()) for d in decision['deals']),total=len(decision['deals']),source='latest.json',scope='Five built-in deals; rules mode.',measures='Citations resolve, precedents belong to candidate records, account scope and proposal labels hold. Does not prove that every citation entails each claim.'),
        dict(id='mock',label='Mock/replay Jev integration checks',passed=sum(r['passed'] for r in transport),total=len(transport),source='latest.json',scope='Transport mocks/replay only.',measures='Fallback and policy integration behavior, not provider quality.'),
        dict(id='live_rules',label='Historical paraphrases: rules',passed=live['summary']['rules_pass'],total=live['summary']['tested'],source='paraphrases_live.json',scope=f"12 pre-labelled synthetic messages, historical run {live['generated_at']}.",measures='Exact match to the developer-assigned obstacle label; classification only.'),
        dict(id='live_jev',label='Historical paraphrases: live Jev',passed=live['summary']['jev_pass'],total=live['summary']['tested'],source='paraphrases_live.json',scope=f"Same messages and labels, historical run {live['generated_at']}; no new provider call.",measures='Exact match for obstacle classification only, not whole-app accuracy.'),
    ]
    result={'generated_wib':datetime.now(timezone(timedelta(hours=7))).strftime('%Y-%m-%d %H:%M WIB'),
            'decision_run_wib':decision['generated_wib'],'metrics':metrics,
            'known_failures':[{'id':r['id'],'description':r['description'],'failed_checks':[k for k,v in r['checks'].items() if not v]} for r in real_rules if not r['passed']],
            'baseline':baseline['summary'],
            'limitations':['Not an independent holdout. Development cases and synthetic labels may favor the implementation.',
                           'No benchmark-wide SalesTranscriptQA run and no comparable external accuracy score.',
                           'No measured sales uplift, time-to-close improvement, novice-user study or independent ranking ground truth.',
                           'Do not average these percentages: they measure different things, with overlapping inputs.']}
    return result


def markdown(r):
    lines=['# DealCompass — accuracy evidence scorecard','',f"Generated: {r['generated_wib']}. Decision/ranking suite rerun: {r['decision_run_wib']}.",'',
           'Use the individual metrics below. There is no single validated whole-app accuracy score.','']
    for m in r['metrics']:
        lines += [f"## {m['label']}: {m['passed']}/{m['total']} ({100*m['passed']/m['total']:.1f}%)",'',m['scope'],m['measures'],f"Receipt: `{m['source']}`.",'']
    lines+=['## Visible failure','']
    for f in r['known_failures']:lines += [f"- {f['id']}: {f['description']}. Failed checks: {', '.join(f['failed_checks'])}."]
    lines+=['','## CRM-only comparison','',
            'On the five demo deals, the primary stage/value CRM baseline and graph+rules have the same ordering. This does not establish better ranking accuracy.',
            f"Graph+rules exposes {r['baseline']['approval_gates_visible_graph_rules']} approval gate versus {r['baseline']['approval_gates_visible_crm']} in the deliberately limited CRM baseline, and named obstacles for {r['baseline']['deals_with_named_obstacle_graph_rules']}/5 deals. This measures surfaced context, not measured sales-team usefulness.",'',
            '## Claim boundaries','',*['- '+s for s in r['limitations']],'',
            'Benchmark protocol and next human evaluation: `evaluation/BENCHMARK_PROTOCOL.md`.']
    return '\n'.join(lines)+'\n'


if __name__=='__main__':
    result=run()
    (RESULTS/'scorecard_latest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (RESULTS/'scorecard_latest.md').write_text(markdown(result))
    print(markdown(result))
