"""Jalankan evaluasi Ical (decision ICAL-01/02 + ranking ICAL-03) dan simpan hasil aktual.

    python -m evaluation.run_eval            # tulis evaluation/results/latest.* dan ranking_latest.*
    python -m evaluation.run_eval --no-write # hanya cetak ringkasan
"""
import argparse
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.decision.analyze import analyze_deal_trace
from backend.decision.ranking import SCORED, rank_deals
from evaluation.cases import CASES, DEAL_IDS, invariant_checks, real
from evaluation.ranking_cases import RANKING_CASES, real_inputs, sensitivity_table

RESULTS = Path(__file__).resolve().parent / 'results'
WIB = timezone(timedelta(hours=7))

SOURCE_LABEL = {
    'dataset_asli': 'dataset asli (konteks/diagnostic nyata tanpa perubahan record)',
    'sintetis': 'mutasi/sintetis berlabel pada salinan konteks',
    'mock_jev': 'transport Jev mock (bukan live)',
    'replay_mock': 'replay rekaman respons mock (bukan live)',
}


def decision_source(case) -> str:
    if case.description.startswith('Sintetis'):
        return 'sintetis'
    if case.category == 'replay':
        return 'replay_mock'
    if case.category.startswith('Jev'):
        return 'mock_jev'
    return 'dataset_asli'


def ranking_source(case) -> str:
    if case.description.startswith('Sintetis') or case.category in ('ID diganti', 'tie'):
        return 'sintetis'
    return 'dataset_asli'


def by_source(rows: list[dict]) -> dict:
    out = {}
    for r in rows:
        s = out.setdefault(r['source'], {'cases': 0, 'passed': 0, 'ids': []})
        s['cases'] += 1
        s['passed'] += r['passed']
        s['ids'].append(r['id'])
    return out


def source_markdown(groups: dict) -> list[str]:
    out = ['| Sumber kasus | Lulus | Kasus |', '|---|---|---|']
    for k, v in groups.items():
        out.append(f"| {SOURCE_LABEL[k]} | {v['passed']}/{v['cases']} | {', '.join(v['ids'])} |")
    return out


def run() -> dict:
    rows = []
    for case in CASES:
        start = time.perf_counter()
        try:
            rec, trace = case.run()
            checks = {name: bool(fn(rec, trace)) for name, fn in case.checks.items()}
            error = None
        except Exception as e:  # dicatat sebagai kegagalan, bukan disembunyikan
            rec = trace = None
            checks, error = {}, f'{type(e).__name__}: {e}'
        rows.append({
            'id': case.id, 'category': case.category, 'description': case.description,
            'source': decision_source(case), 'known_limitation': case.known_limitation,
            'passed': error is None and all(checks.values()),
            'checks': checks, 'error': error,
            'engine_mode': rec.engine_mode if rec else None,
            'main_obstacle': trace.main_obstacle if trace else None,
            'approvals_needed': rec.approvals_needed if rec else None,
            'precedent_ids': rec.precedent_ids if rec else None,
            'latency_ms': round((time.perf_counter() - start) * 1000),
        })
    deals = []
    for deal_id in DEAL_IDS:
        ctx = real(deal_id)
        rec, trace = analyze_deal_trace(ctx, mode='rules')
        deals.append({'deal_id': deal_id, 'analysis_status': trace.analysis_status,
                      'main_obstacle': trace.main_obstacle, 'invariants': invariant_checks(rec, trace, ctx),
                      'recommendation': rec.model_dump()})
    core = [r for r in rows if not r['known_limitation']]
    return {
        'generated_wib': datetime.now(WIB).strftime('%Y-%m-%d %H:%M WIB'),
        'context_source': 'build_deal_context nyata (graph Bima, dataset asli); mutasi kasus sintetis berlabel',
        'jev': 'Tidak ada panggilan live. Kasus Jev memakai transport mock.',
        'summary': {
            'cases': len(rows), 'passed': sum(r['passed'] for r in rows),
            'core_cases': len(core), 'core_passed': sum(r['passed'] for r in core),
            'known_limitations': [r['id'] for r in rows if r['known_limitation']],
            'known_limitations_passed': [r['id'] for r in rows if r['known_limitation'] and r['passed']],
            'invariants_all_true': all(all(d['invariants'].values()) for d in deals),
            'by_source': by_source(rows),
        },
        'cases': rows, 'deals': deals,
    }


def to_markdown(res: dict) -> str:
    s = res['summary']
    out = [f"# Hasil evaluasi decision ICAL-01/02 ({res['generated_wib']})", '',
           f"Sumber konteks: {res['context_source']}. Jev: {res['jev']}", '',
           f"Kasus: {s['passed']}/{s['cases']} lulus; inti {s['core_passed']}/{s['core_cases']}; "
           f"batas diketahui: {', '.join(s['known_limitations']) or '-'} "
           f"(lulus: {', '.join(s['known_limitations_passed']) or 'tidak ada'}). "
           f"Invarian lima deal nyata: {'semua benar' if s['invariants_all_true'] else 'ADA YANG GAGAL'}.", '',
           *source_markdown(s['by_source']), '',
           'Benchmark ini bukan holdout independen: kasus disusun bersama pengembangan rules.', '',
           '| ID | Kategori | Lulus | Mode | Hambatan | Pemeriksaan gagal |', '|---|---|---|---|---|---|']
    for r in res['cases']:
        failed = ', '.join(k for k, v in r['checks'].items() if not v) or (r['error'] or '-')
        flag = ' (batas diketahui)' if r['known_limitation'] else ''
        out.append(f"| {r['id']} | {r['category']}{flag} | {'ya' if r['passed'] else 'TIDAK'} | "
                   f"{r['engine_mode']} | {r['main_obstacle']} | {failed} |")
    out += ['', '## Lima deal (mode rules, graph nyata)', '', '| Deal | Status | Hambatan | Preseden | Approval |', '|---|---|---|---|---|']
    for d in res['deals']:
        rec = d['recommendation']
        out.append(f"| {d['deal_id']} | {d['analysis_status']} | {d['main_obstacle']} | "
                   f"{', '.join(rec['precedent_ids']) or '-'} | {len(rec['approvals_needed'])} |")
    return '\n'.join(out) + '\n'


def run_ranking() -> dict:
    rows = []
    for case in RANKING_CASES:
        start = time.perf_counter()
        try:
            res, ctxs, diags = case.run()
            checks = {name: bool(fn(res, ctxs, diags)) for name, fn in case.checks.items()}
            error, ranked = None, [i['deal_id'] for i in res['items']]
        except Exception as e:  # dicatat sebagai kegagalan, bukan disembunyikan
            checks, error, ranked = {}, f'{type(e).__name__}: {e}', None
        rows.append({'id': case.id, 'category': case.category, 'description': case.description,
                     'source': ranking_source(case), 'passed': error is None and all(checks.values()), 'checks': checks, 'error': error,
                     'order': ranked, 'latency_ms': round((time.perf_counter() - start) * 1000)})
    ctxs, diags = real_inputs()
    start = time.perf_counter()
    res = rank_deals(ctxs, diags)
    rank_ms = round((time.perf_counter() - start) * 1000)
    items = []
    for it in res['items']:
        f = {x['name']: x for x in it['factors']}
        items.append({'rank': it['rank'], 'deal_id': it['deal_id'], 'account_id': it['account_id'],
                      'priority_kind': it['priority_kind'], 'analysis_status': it['analysis_status'],
                      'score': f['skor_prioritas']['value'], 'factor_values': {k: f[k]['value'] for k in SCORED},
                      'action': it['recommendation']['action'], 'owner_id': it['recommendation']['owner_id'],
                      'approvals_needed': it['recommendation']['approvals_needed'],
                      'gates': f['gate_approval_izin']['value'], 'evidence_count': len(it['evidence']),
                      'path_count': len(it['evidence_paths']), 'rationale': it['rationale']})
    return {
        'generated_wib': datetime.now(WIB).strftime('%Y-%m-%d %H:%M WIB'),
        'source': 'build_deal_context + analyze_deal_initial nyata (Bima, dataset asli); kasus mutasi sintetis berlabel',
        'jev': 'Ranking tidak memakai Jev (rules). Tidak ada mock/replay/live pada ranking.',
        'methodology': res['methodology'], 'global_limitations': res['limitations'],
        'rank_deals_ms_warm': rank_ms, 'items': items, 'sensitivity': sensitivity_table(),
        'summary': {'cases': len(rows), 'passed': sum(r['passed'] for r in rows), 'by_source': by_source(rows)},
        'cases': rows,
    }


def ranking_markdown(r: dict) -> str:
    s = r['summary']
    out = [f"# Hasil evaluasi ranking ICAL-03 ({r['generated_wib']})", '',
           f"Sumber: {r['source']}. {r['jev']}", '',
           f"Kasus ranking: {s['passed']}/{s['cases']} lulus. rank_deals lima deal (konteks sudah dibangun): "
           f"{r['rank_deals_ms_warm']} ms.", '',
           *source_markdown(s['by_source']), '',
           'Benchmark ini bukan holdout independen dan bukan validasi hasil closing.', '',
           '## Urutan aktual', '', '| Rank | Deal | Tier | Status | Skor | Tahap | Nilai | Hambatan pelanggan | Preseden | Gate |',
           '|---|---|---|---|---|---|---|---|---|---|']
    for i in r['items']:
        fv = i['factor_values']
        out.append(f"| {i['rank']} | {i['deal_id']}/{i['account_id']} | {i['priority_kind']} | {i['analysis_status']} | "
                   f"{i['score'] if i['score'] is not None else '-'} | {fv['tahap_deal']} | {fv['nilai_potensi_tahunan']} | "
                   f"{fv['hambatan_dinyatakan_pelanggan'] or 'unknown'} | {fv['preseden_relevan']} | {i['gates']} |")
    out += ['', '## Sensitivitas bobot (urutan lengkap)', '', '| Variasi | Urutan | Skor acceleration |', '|---|---|---|']
    for row in r['sensitivity']:
        scores = ', '.join(f'{k} {v}' for k, v in row['scores'].items() if v is not None)
        out.append(f"| {row['variant']} | {' > '.join(row['order'])} | {scores} |")
    out += ['', '## Kasus', '', '| ID | Kategori | Lulus | Urutan | Pemeriksaan gagal |', '|---|---|---|---|---|']
    for c in r['cases']:
        failed = ', '.join(k for k, v in c['checks'].items() if not v) or (c['error'] or '-')
        out.append(f"| {c['id']} | {c['category']} | {'ya' if c['passed'] else 'TIDAK'} | "
                   f"{' > '.join(c['order']) if c['order'] else '-'} | {failed} |")
    return '\n'.join(out) + '\n'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--no-write', action='store_true')
    args = p.parse_args()
    res = run()
    md = to_markdown(res)
    print(md)
    rk = run_ranking()
    rmd = ranking_markdown(rk)
    print(rmd)
    if not args.no_write:
        RESULTS.mkdir(exist_ok=True)
        (RESULTS / 'latest.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
        (RESULTS / 'latest.md').write_text(md, encoding='utf-8')
        (RESULTS / 'ranking_latest.json').write_text(json.dumps(rk, ensure_ascii=False, indent=2), encoding='utf-8')
        (RESULTS / 'ranking_latest.md').write_text(rmd, encoding='utf-8')


if __name__ == '__main__':
    main()
