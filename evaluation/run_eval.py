"""Jalankan evaluasi ICAL-01 dan simpan hasil aktual.

    python -m evaluation.run_eval            # tulis evaluation/results/latest.{json,md}
    python -m evaluation.run_eval --no-write # hanya cetak ringkasan
"""
import argparse
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.decision.analyze import analyze_deal_trace
from evaluation.cases import CASES, DEAL_IDS, invariant_checks, load_fixture

RESULTS = Path(__file__).resolve().parent / 'results'
WIB = timezone(timedelta(hours=7))


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
            'known_limitation': case.known_limitation,
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
        ctx = load_fixture(deal_id)
        rec, trace = analyze_deal_trace(ctx, mode='rules')
        deals.append({'deal_id': deal_id, 'analysis_status': trace.analysis_status,
                      'main_obstacle': trace.main_obstacle, 'invariants': invariant_checks(rec, trace, ctx),
                      'recommendation': rec.model_dump()})
    core = [r for r in rows if not r['known_limitation']]
    return {
        'generated_wib': datetime.now(WIB).strftime('%Y-%m-%d %H:%M WIB'),
        'context_source': 'FIXTURE_ICAL_SEMENTARA (record asli; bukan graph Bima)',
        'jev': 'Tidak ada panggilan live. Kasus Jev memakai transport mock.',
        'summary': {
            'cases': len(rows), 'passed': sum(r['passed'] for r in rows),
            'core_cases': len(core), 'core_passed': sum(r['passed'] for r in core),
            'known_limitations': [r['id'] for r in rows if r['known_limitation']],
            'known_limitations_passed': [r['id'] for r in rows if r['known_limitation'] and r['passed']],
            'invariants_all_true': all(all(d['invariants'].values()) for d in deals),
        },
        'cases': rows, 'deals': deals,
    }


def to_markdown(res: dict) -> str:
    s = res['summary']
    out = [f"# Hasil evaluasi ICAL-01 ({res['generated_wib']})", '',
           f"Sumber konteks: {res['context_source']}. Jev: {res['jev']}", '',
           f"Kasus: {s['passed']}/{s['cases']} lulus; inti {s['core_passed']}/{s['core_cases']}; "
           f"batas diketahui: {', '.join(s['known_limitations']) or '-'} "
           f"(lulus: {', '.join(s['known_limitations_passed']) or 'tidak ada'}). "
           f"Invarian lima fixture: {'semua benar' if s['invariants_all_true'] else 'ADA YANG GAGAL'}.", '',
           '| ID | Kategori | Lulus | Mode | Hambatan | Pemeriksaan gagal |', '|---|---|---|---|---|---|']
    for r in res['cases']:
        failed = ', '.join(k for k, v in r['checks'].items() if not v) or (r['error'] or '-')
        flag = ' (batas diketahui)' if r['known_limitation'] else ''
        out.append(f"| {r['id']} | {r['category']}{flag} | {'ya' if r['passed'] else 'TIDAK'} | "
                   f"{r['engine_mode']} | {r['main_obstacle']} | {failed} |")
    out += ['', '## Lima deal (mode rules, fixture)', '', '| Deal | Status | Hambatan | Preseden | Approval |', '|---|---|---|---|---|']
    for d in res['deals']:
        rec = d['recommendation']
        out.append(f"| {d['deal_id']} | {d['analysis_status']} | {d['main_obstacle']} | "
                   f"{', '.join(rec['precedent_ids']) or '-'} | {len(rec['approvals_needed'])} |")
    return '\n'.join(out) + '\n'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--no-write', action='store_true')
    args = p.parse_args()
    res = run()
    md = to_markdown(res)
    print(md)
    if not args.no_write:
        RESULTS.mkdir(exist_ok=True)
        (RESULTS / 'latest.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
        (RESULTS / 'latest.md').write_text(md, encoding='utf-8')


if __name__ == '__main__':
    main()
