"""Small, pre-labelled synthetic language probe; never changes the source dataset.

python -m evaluation.paraphrases                 # rules only, no network
python -m evaluation.paraphrases --live --env-file .env  # explicit paid test
Live uses the existing team ledger. No retries, no prompt tuning within a run.
"""
import argparse
import ast
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path

from backend.decision.signals import OBSTACLES, classify_message
from backend.integrations.jev import JevClient, JevError, choice
from backend.integrations.jev_live import load_env_file, configuration, receipt

PROMPT = ('Klasifikasikan hambatan penjualan utama yang dinyatakan pesan ini. '
          'Pilih bukti_kurang bila pesan tidak cukup jelas.')
# Expected labels are fixed before observing provider outputs. Not an independent holdout.
CASES = [
    ('PAR-01', 'E15 idiom', 'Pak Teddy merasa KasirPro lebih ramah di kantong.', 'harga'),
    ('PAR-02', 'Budget paraphrase', 'Biaya langganan ini sulit masuk alokasi dana kami.', 'harga'),
    ('PAR-03', 'Competitor paraphrase', 'Paket pesaing lebih terjangkau untuk usaha kami.', 'harga'),
    ('PAR-04', 'Literal price control', 'Harganya terlalu mahal dibanding KasirPro.', 'harga'),
    ('PAR-05', 'Negated price / reference', 'Harga sudah cocok, tinggal menunggu referensi pelanggan serupa.', 'referensi'),
    ('PAR-06', 'Negated price / authority', 'Bukan anggaran yang menghambat. Kami masih menunggu pengambil keputusan yang baru.', 'pengambil_keputusan'),
    ('PAR-07', 'Positive price control', 'Harganya sudah sesuai dan kami tidak punya keberatan. Terima kasih.', 'tanpa_hambatan'),
    ('PAR-08', 'Product requirement', 'Kami membutuhkan modul apotek untuk sembilan klinik.', 'kebutuhan_produk'),
    ('PAR-09', 'Ambiguous message', 'Kami masih mempertimbangkannya.', 'bukti_kurang'),
    ('PAR-10', 'Discount request, not approval', 'Saya mengusulkan diskon 20%. Mohon keputusan VP Sales; belum ada persetujuan.', 'harga'),
    ('PAR-11', 'Reference paraphrase', 'Bisa pertemukan kami dengan pelanggan yang sudah memakai sistem ini?', 'referensi'),
    ('PAR-12', 'Authority paraphrase', 'Saya hanya mengecek teknis; keputusan pembelian ada pada kepala operasional.', 'pengambil_keputusan'),
]


def run(live=False, env_file=None):
    # Stop if the production prompt changes, rather than silently testing a different prompt.
    source = inspect.getsource(__import__('backend.decision.analyze', fromlist=['x']))
    assert any(isinstance(n, ast.Constant) and n.value == PROMPT for n in ast.walk(ast.parse(source)))
    result = {'generated_at': datetime.now(timezone.utc).isoformat(), 'synthetic': True,
              'scope': '12 synthetic message classifications using the production obstacle prompt',
              'limitations': ['Developer-labelled diagnostic set, not independent holdout.',
                              'One observation per case; no stability or production accuracy claim.',
                              'E15 rules benchmark remains separate; no closing-time claim.'],
              'prompt': PROMPT, 'criteria': OBSTACLES, 'live': live, 'cases': []}
    client = None
    if live:
        load_env_file(env_file)
        config, _ = configuration()
        client = JevClient(**config)
        result['ledger_before'] = client.ledger.summary()
    for cid, group, text, expected in CASES:
        observed = classify_message(text)
        row = {'id': cid, 'group': group, 'text': text, 'expected': expected,
               'rules': observed, 'rules_pass': observed == expected}
        if client:
            try:
                row['jev'] = client.ask(text, {'hambatan': choice(PROMPT, OBSTACLES)})['hambatan']['choice']
                row['jev_pass'] = row['jev'] == expected
            except JevError as error:
                row.update(jev=None, jev_pass=False, error=error.code)
                result['cases'].append(row)
                result['stopped'] = 'Provider error; no automatic retry.'
                break
        result['cases'].append(row)
        print(json.dumps({'case': cid, 'rules': observed, 'jev': row.get('jev'), 'expected': expected}), flush=True)
    result['e15_workflow'] = {'status': 'not_run', 'reason': 'No dataset-derived context transmitted. This run evaluates message classification only.'}
    result['summary'] = {'tested': len(result['cases']), 'rules_pass': sum(r['rules_pass'] for r in result['cases']),
                         'jev_pass': sum(r.get('jev_pass', False) for r in result['cases']) if live else None}
    if client:
        result['receipt'] = receipt(client)
        result['ledger_after'] = client.ledger.summary()
        result['run_input_tokens'] = sum(c['usage'].get('input_tokens', 0) for c in result['receipt']['calls'])
        result['run_output_tokens'] = sum(c['usage'].get('output_tokens', 0) for c in result['receipt']['calls'])
    return result


def markdown(r):
    lines = ['# Synthetic paraphrase evaluation', '', f"Run: {r['generated_at']}",
             f"Live: {r['live']}. Rules {r['summary']['rules_pass']}/{r['summary']['tested']}; Jev {r['summary']['jev_pass']}/{r['summary']['tested']}.", '',
             '| Case | Message | Expected | Rules | Jev |', '|---|---|---|---|---|']
    for c in r['cases']:
        lines.append(f"| {c['id']} | {c['text']} | {c['expected']} | {c['rules']} | {c.get('jev', 'not run')} |")
    lines += ['', '## Full E15 workflow', '', '```json', json.dumps(r.get('e15_workflow', {}), ensure_ascii=False, indent=2), '```',
              '', '## Usage', '', f"This run: {r.get('run_input_tokens',0)} input / {r.get('run_output_tokens',0)} output tokens.",
              '', '## Limits', '', *['- '+s for s in r['limitations']]]
    return '\n'.join(lines)+'\n'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--env-file')
    args = parser.parse_args()
    report = run(args.live, args.env_file)
    stem = 'paraphrases_live' if args.live else 'paraphrases_rules'
    dest = Path('evaluation/results'); dest.mkdir(exist_ok=True)
    (dest / (stem+'.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    (dest / (stem+'.md')).write_text(markdown(report))
    print(json.dumps(report['summary']))
