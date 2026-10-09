"""Pembanding ICAL-04: baseline CRM-only vs graph+rules pada lima deal kanonis yang sama.

    python -m evaluation.baseline_crm            # tulis evaluation/results/baseline_latest.{json,md}
    python -m evaluation.baseline_crm --no-write # hanya cetak markdown

Baseline CRM-only hanya membaca baris `list_deals()` (crm_deals.csv + tipe/nama akun dari
crm_accounts.csv): tahap, nilai potensi tahunan, umur tahap dan owner. Tindakan baseline adalah
template generik per tahap yang dibuat Ical agar pembanding transparan; bukan fitur CRM tertentu.
Graph+rules = rank_deals (production, formula tidak diubah) di atas build_deal_context +
analyze_deal_initial nyata. Ini perbandingan isi alasan/tindakan/sumber, bukan uji akurasi:
tidak ada label hasil closing, tidak ada model yang dilatih, lima kasus bukan sampel uplift.
"""
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.contracts import DealSummary
from backend.decision.analyze import analyze_deal_trace
from backend.decision.ranking import rank_deals
from backend.graph.analysis import analyze_deal_initial
from backend.graph.context import build_deal_context
from backend.ingestion.deals import list_deals

RESULTS = Path(__file__).resolve().parent / 'results'
WIB = timezone(timedelta(hours=7))

STAGE_ORDER = {'Lead': 0, 'Discovery': 1, 'Demo': 2, 'Proposal': 3, 'Negosiasi': 4}

GENERIC_ACTION = {
    'Lead': 'Kualifikasi lead dan jadwalkan kontak pertama.',
    'Discovery': 'Lanjutkan discovery lalu jadwalkan demo.',
    'Demo': 'Follow up hasil demo dan kirim penawaran harga.',
    'Proposal': 'Follow up proposal ke kontak yang tercatat.',
    'Negosiasi': 'Follow up negosiasi dan dorong tanda tangan kontrak.',
}

CRM_FIELDS = ('stage', 'annual_value', 'stage_age_days', 'owner_id')

NOT_USED = (
    'interactions.jsonl: isi email/meeting (hambatan, permintaan diskon, syarat referensi)',
    'decision_log.csv: preseden dan approval VP Sales',
    'crm_contacts.csv + contact_employment_history.csv: pengambil keputusan dan riwayat kerja',
    'feature_usage_monthly.csv, features.csv, support_tickets.csv: bukti kandidat referensi',
    'employees.csv: siapa pemegang approval',
    'crm_deals.kompetitor: kolom CRM yang terlihat tetapi tidak dipakai baseline utama; '
    'tidak memuat permintaan diskon atau status approval',
    'Edge graph/provenance dan diagnostic Bima',
)

BASELINES = {
    'stage_value': ('Tahap lanjut dulu, lalu nilai potensi terbesar (baseline utama)',
                    lambda r: (-STAGE_ORDER.get(r.stage, -1), -r.annual_value, r.deal_id)),
    'value_only': ('Nilai potensi terbesar saja',
                   lambda r: (-r.annual_value, r.deal_id)),
    'stage_age': ('Paling lama di tahap saat ini (deal "macet")',
                  lambda r: (-r.stage_age_days, r.deal_id)),
}


def rank_crm(rows: list[DealSummary], baseline: str = 'stage_value') -> list[dict]:
    """Urutkan baris CRM dengan satu baseline transparan. Tidak membaca sumber lain."""
    _, key = BASELINES[baseline]
    items = []
    for i, r in enumerate(sorted(rows, key=key), 1):
        items.append({
            'rank': i, 'deal_id': r.deal_id, 'account_id': r.account_id, 'stage': r.stage,
            'annual_value': r.annual_value, 'stage_age_days': r.stage_age_days, 'owner_id': r.owner_id,
            'action': GENERIC_ACTION.get(r.stage, 'Follow up deal.'),
            'evidence_ids': [f'crm_deals.csv:{r.deal_id}', f'crm_accounts.csv:{r.account_id}'],
            'approval_visible': None,
            'obstacle_visible': None,
        })
    return items


def source_files(evidence_ids: list[str]) -> list[str]:
    return sorted({e.split(':', 1)[0] for e in evidence_ids})


def graph_rules(deal_ids: list[str]) -> tuple[dict, dict]:
    contexts = [build_deal_context(d) for d in deal_ids]
    diagnostics = [analyze_deal_initial(c) for c in contexts]
    envelope = rank_deals(contexts, diagnostics)
    obstacles = {c.deal.deal_id: analyze_deal_trace(c, mode='rules', diagnostic=d)[1].main_obstacle
                 for c, d in zip(contexts, diagnostics)}
    return envelope, obstacles


def _factor(item: dict, name: str) -> dict:
    return next(f for f in item['factors'] if f['name'] == name)


def compare(rows: list[DealSummary], envelope: dict, obstacles: dict) -> dict:
    crm = {b: rank_crm(rows, b) for b in BASELINES}
    crm_by_id = {x['deal_id']: x for x in crm['stage_value']}
    deals = []
    for item in envelope['items']:
        did = item['deal_id']
        base = crm_by_id[did]
        rec = item['recommendation']
        gr_sources = source_files(item['evidence_ids'])
        obstacle_factor = _factor(item, 'hambatan_dinyatakan_pelanggan')
        gate = _factor(item, 'gate_approval_izin')
        deals.append({
            'deal_id': did, 'account_id': item['account_id'],
            'crm': {'rank': base['rank'], 'action': base['action'],
                    'evidence_count': len(base['evidence_ids']),
                    'source_files': source_files(base['evidence_ids'])},
            'graph_rules': {
                'rank': item['rank'], 'priority_kind': item['priority_kind'],
                'analysis_status': item['analysis_status'], 'main_obstacle': obstacles[did],
                'score': _factor(item, 'skor_prioritas')['value'],
                'owner_id': rec['owner_id'], 'action': rec['action'], 'milestone': rec['milestone'],
                'obstacle_evidence_ids': obstacle_factor['evidence_ids'],
                'gate': gate['value'], 'gate_evidence_ids': gate['evidence_ids'],
                'approvals_needed': rec['approvals_needed'],
                'precedent_ids': rec['precedent_ids'], 'unknowns_count': len(rec['unknowns']),
                'evidence_count': len(item['evidence_ids']), 'paths_count': len(item['evidence_paths']),
                'source_files': gr_sources,
            },
            'rank_changed': base['rank'] != item['rank'],
            'additional_source_files': sorted(set(gr_sources) - set(source_files(base['evidence_ids']))),
        })
    gr_order = [i['deal_id'] for i in envelope['items']]
    orders = {b: [x['deal_id'] for x in items] for b, items in crm.items()}
    return {
        'snapshot_date': envelope['snapshot_date'],
        'graph_rules_method': envelope['methodology']['id'],
        'crm_fields_used': list(CRM_FIELDS),
        'not_used_by_baseline': list(NOT_USED),
        'baselines': {b: {'label': BASELINES[b][0], 'order': orders[b],
                          'same_order_as_graph_rules': orders[b] == gr_order} for b in BASELINES},
        'graph_rules_order': gr_order,
        'deals': deals,
        'summary': {
            'deals': len(deals),
            'rank_changed_vs_stage_value': [d['deal_id'] for d in deals if d['rank_changed']],
            'approval_gates_visible_crm': 0,
            'approval_gates_visible_graph_rules': sum(bool(d['graph_rules']['approvals_needed']) for d in deals),
            'deals_with_named_obstacle_graph_rules': sum(bool(d['graph_rules']['obstacle_evidence_ids']) for d in deals),
            'deals_with_additional_sources': [d['deal_id'] for d in deals if d['additional_source_files']],
        },
        'limits': [
            'Lima deal, satu snapshot; tidak ada label hasil closing sehingga tidak ada klaim akurasi atau uplift.',
            'Urutan yang sama atau berbeda bukan bukti salah satu metode lebih akurat.',
            'Tindakan baseline adalah template generik buatan Ical, bukan perilaku CRM atau sales nyata.',
            'Graph+rules memakai formula production deal-priority-heuristic-v1 tanpa perubahan; bobot tetap pilihan desain.',
        ],
    }


def to_markdown(res: dict) -> str:
    out = [f"# Pembanding CRM-only vs graph+rules ICAL-04 ({res['generated_wib']})", '',
           f"Snapshot {res['snapshot_date']}; lima deal prospek terbuka dari `list_deals()` (data kanonis sama). "
           f"Graph+rules = `{res['graph_rules_method']}` production, mode rules, tanpa Jev.", '',
           f"Field CRM yang dipakai baseline: {', '.join(res['crm_fields_used'])}.", '',
           'Sengaja tidak dipakai baseline:', '']
    out += [f'- {x}' for x in res['not_used_by_baseline']]
    out += ['', '## Urutan', '', '| Metode | Urutan | Sama dengan graph+rules |', '|---|---|---|',
            f"| graph+rules | {' > '.join(res['graph_rules_order'])} | - |"]
    for b in res['baselines'].values():
        out.append(f"| CRM: {b['label']} | {' > '.join(b['order'])} | {'ya' if b['same_order_as_graph_rules'] else 'tidak'} |")
    out += ['', '## Per deal (baseline utama: tahap lalu nilai)', '',
            '| Deal | Rank CRM | Rank G+R | Tindakan CRM | Hambatan G+R (bukti) | Gate G+R | Owner | Preseden | Bukti CRM→G+R | Path | Sumber tambahan |',
            '|---|---|---|---|---|---|---|---|---|---|---|']
    for d in res['deals']:
        g = d['graph_rules']
        obs = f"{g['main_obstacle']} ({', '.join(g['obstacle_evidence_ids']) or 'tidak ada'})"
        out.append(
            f"| {d['deal_id']}/{d['account_id']} | {d['crm']['rank']} | {g['rank']} ({g['priority_kind']}) | "
            f"{d['crm']['action']} | {obs} | {g['gate']} | {g['owner_id']} | {', '.join(g['precedent_ids']) or '-'} | "
            f"{d['crm']['evidence_count']}→{g['evidence_count']} | {g['paths_count']} | "
            f"{', '.join(d['additional_source_files']) or 'tidak ada'} |")
    out += ['', '## Tindakan graph+rules (Recommendation v1, apa adanya)', '']
    for d in res['deals']:
        out.append(f"- **{d['deal_id']}** ({d['graph_rules']['owner_id']}): {d['graph_rules']['action']}")
    s = res['summary']
    out += ['', '## Ringkasan', '',
            f"- Rank berubah vs baseline utama: {', '.join(s['rank_changed_vs_stage_value']) or 'tidak ada'}.",
            f"- Gate approval VP Sales terlihat: CRM {s['approval_gates_visible_crm']}, graph+rules {s['approval_gates_visible_graph_rules']}.",
            f"- Deal dengan hambatan bersumber: graph+rules {s['deals_with_named_obstacle_graph_rules']}/{s['deals']}; CRM tidak membaca percakapan.",
            f"- Deal yang mendapat sumber tambahan: {', '.join(s['deals_with_additional_sources']) or 'tidak ada'}.",
            '', '## Batas', '']
    out += [f'- {x}' for x in res['limits']]
    return '\n'.join(out) + '\n'


def run() -> dict:
    rows = list_deals()
    envelope, obstacles = graph_rules([r.deal_id for r in rows])
    res = compare(rows, envelope, obstacles)
    res['generated_wib'] = datetime.now(WIB).strftime('%Y-%m-%d %H:%M WIB')
    return res


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-write', action='store_true')
    args = parser.parse_args()
    res = run()
    md = to_markdown(res)
    if not args.no_write:
        RESULTS.mkdir(exist_ok=True)
        (RESULTS / 'baseline_latest.json').write_text(json.dumps(res, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (RESULTS / 'baseline_latest.md').write_text(md, encoding='utf-8')
    print(md)


if __name__ == '__main__':
    main()
