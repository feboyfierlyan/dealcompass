"""Kasus evaluasi ranking ICAL-03. Satu sumber untuk tests/ical dan evaluation/run_eval.py.

Basis: build_deal_context + analyze_deal_initial NYATA (produsen Bima, dataset asli).
Mutasi (ID ditukar, nilai/tahap/pesan diubah, keputusan ditambah) bersifat SINTETIS pada
salinan input, dengan format produsen. Ranking tidak memakai Jev; tidak ada mock/live di sini.
"""
import copy
import json
import os
import random
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable
from unittest.mock import patch

from backend.contracts import DealContext
from backend.decision.ranking import SCORED, path_is_valid, rank_deals
from backend.graph.analysis import analyze_deal_initial
from backend.graph.context import build_deal_context

DEAL_IDS = ('DL-001', 'DL-002', 'DL-003', 'DL-004', 'DL-005')


@lru_cache(maxsize=1)
def _base() -> tuple[str, str]:
    ctxs = [build_deal_context(d) for d in DEAL_IDS]
    diags = [analyze_deal_initial(c) for c in ctxs]
    return (json.dumps([c.model_dump() for c in ctxs], ensure_ascii=False), json.dumps(diags, ensure_ascii=False))


def real_inputs() -> tuple[list[DealContext], list[dict]]:
    """Salinan baru konteks + diagnostic nyata (mutasi kasus tidak mengenai cache produsen)."""
    c, d = _base()
    return [DealContext.model_validate(x) for x in json.loads(c)], json.loads(d)


def swap_ids(ctxs, diags, pairs: dict[str, str]):
    """Tukar ID secara konsisten di seluruh input (uji tidak ada daftar ID hardcoded)."""
    text = json.dumps([[c.model_dump() for c in ctxs], diags], ensure_ascii=False)
    tokens = {k: f'__SWAP{i}__' for i, k in enumerate(pairs)}
    for k, tok in tokens.items():
        text = re.sub(rf'(?<![A-Za-z0-9]){re.escape(k)}(?![0-9])', tok, text)
    for k, tok in tokens.items():
        text = text.replace(tok, pairs[k])
    c, d = json.loads(text)
    return [DealContext.model_validate(x) for x in c], d


def clone_deal(ctxs, diags, deal_id: str, new_deal: str, new_acc: str):
    """Tambahkan salinan satu deal dengan ID baru (faktor identik) untuk uji tie."""
    src_c = next(c for c in ctxs if c.deal.deal_id == deal_id)
    src_d = next(d for d in diags if d['deal_id'] == deal_id)
    acc = src_c.deal.account_id
    original = {e.id: e.model_dump() for e in src_c.evidence}
    original.update({e['id']: e for e in src_d.get('evidence', [])})
    text = json.dumps([src_c.model_dump(), src_d], ensure_ascii=False)
    text = re.sub(rf'(?<![A-Za-z0-9]){re.escape(deal_id)}(?![0-9])', new_deal, text)
    text = re.sub(rf'(?<![A-Za-z0-9]){re.escape(acc)}(?![0-9])', new_acc, text)
    c, d = json.loads(text)
    # Record yang isinya ikut berubah diberi ID baru agar tidak bentrok dengan record asli (ID sama, isi beda).
    changed = {e['id'] for e in c['evidence'] + d.get('evidence', []) if e['id'] in original and original[e['id']] != e}
    for eid in sorted(changed, key=len, reverse=True):
        text = text.replace(json.dumps(eid, ensure_ascii=False), json.dumps(eid + '~clone', ensure_ascii=False))
    c, d = json.loads(text)
    return ctxs + [DealContext.model_validate(c)], diags + [d]


def set_isi(ctxs, diags, iid, isi):
    """Ubah isi satu interaksi secara konsisten di semua context dan diagnostic (format produsen)."""
    eid = f'interactions.jsonl:{iid}'

    def patch_excerpt(excerpt):
        row = json.loads(excerpt)
        row['isi'] = isi
        return json.dumps(row, ensure_ascii=False)

    for c in ctxs:
        for e in c.evidence:
            if e.id == eid:
                e.excerpt = patch_excerpt(e.excerpt)
    for d in diags:
        for e in d.get('evidence', []):
            if e['id'] == eid:
                e['excerpt'] = patch_excerpt(e['excerpt'])
    return ctxs, diags


def deal_of(ctxs, deal_id) -> DealContext:
    return next(c for c in ctxs if c.deal.deal_id == deal_id)


def order(res) -> list[str]:
    return [i['deal_id'] for i in res['items']]


def item(res, deal_id) -> dict:
    return next(i for i in res['items'] if i['deal_id'] == deal_id)


def referenced_ids(it) -> set[str]:
    ids = set(it['evidence_ids']) | set(it['recommendation']['evidence_ids'])
    for f in it['factors']:
        ids |= set(f['evidence_ids'])
    for p in it['evidence_paths']:
        ids |= set(p['evidence_ids'])
    return ids


def contract_violations(res, ctxs) -> list[str]:
    """Pemeriksaan bentuk kontrak fase 3 + bukti/path terhadap graph konteks."""
    errs = []
    graphs = {c.deal.deal_id: c.graph for c in ctxs}
    if (res.get('schema_version'), res.get('snapshot_date'), res.get('engine_mode')) != ('v1', '2026-10-01', 'rules'):
        errs.append('envelope schema/snapshot/engine_mode salah')
    m = res.get('methodology', {})
    for k in ('id', 'label', 'description', 'ordered_rules', 'tie_breakers', 'limitations', 'weights'):
        if k not in m:
            errs.append(f'methodology.{k} hilang')
    ranks = [i['rank'] for i in res['items']]
    if ranks != list(range(1, len(ctxs) + 1)):
        errs.append(f'rank tidak 1..N berurutan: {ranks}')
    if sorted(i['deal_id'] for i in res['items']) != sorted(graphs):
        errs.append('item tidak sama dengan input')
    try:
        json.dumps(res, allow_nan=False)
    except ValueError as e:
        errs.append(f'JSON tidak strict: {e}')
    for it in res['items']:
        did = it['deal_id']
        if it['priority_kind'] not in ('acceleration', 'discovery') or it['analysis_status'] not in ('ready', 'insufficient_evidence'):
            errs.append(f'{did}: priority_kind/analysis_status tidak valid')
        if (it['priority_kind'] == 'acceleration') != (it['analysis_status'] == 'ready'):
            errs.append(f'{did}: tier tidak cocok dengan status bukti')
        if it['recommendation'].get('engine_mode') != 'rules' or it['recommendation'].get('deal_id') != did:
            errs.append(f'{did}: recommendation bukan rules/deal salah')
        for f in it['factors']:
            if set(f) != {'name', 'value', 'effect', 'evidence_ids'} or not f['effect']:
                errs.append(f'{did}: faktor {f.get("name")} tidak lengkap')
        have = {e['id'] for e in it['evidence']}
        missing = referenced_ids(it) - have
        if missing:
            errs.append(f'{did}: evidence tidak lengkap {sorted(missing)[:3]}')
        if not it['evidence_paths']:
            errs.append(f'{did}: tanpa evidence_paths')
        for p in it['evidence_paths']:
            if not path_is_valid(graphs[did], p):
                errs.append(f'{did}: path tidak cocok graph {p["node_ids"]}')
        if not it['rationale'] or not it['limitations']:
            errs.append(f'{did}: rationale/limitations kosong')
    return errs


@dataclass
class RankCase:
    id: str
    category: str
    description: str
    run: Callable[[], tuple]
    checks: dict[str, Callable] = field(default_factory=dict)


def _ranked(mutate=None):
    ctxs, diags = real_inputs()
    if mutate:
        ctxs, diags = mutate(ctxs, diags)
    return rank_deals(ctxs, diags), ctxs, diags


def _shuffled():
    base, ctxs, diags = _ranked()
    rng = random.Random(20261009)
    outs = []
    for _ in range(5):
        c, d = real_inputs()
        rng.shuffle(c)
        rng.shuffle(d)
        outs.append(json.dumps(rank_deals(c, d), sort_keys=True))
    base['_shuffle_identical'] = all(o == json.dumps({k: v for k, v in base.items()}, sort_keys=True) for o in outs)
    return base, ctxs, diags


def _swap(ctxs, diags):
    return swap_ids(ctxs, diags, {'DL-001': 'DL-004', 'DL-004': 'DL-001', 'P01': 'P04', 'P04': 'P01'})


def _tie(ctxs, diags):
    return clone_deal(ctxs, diags, 'DL-003', 'DL-903', 'P93')


def _big_value_p05(ctxs, diags):
    deal_of(ctxs, 'DL-005').deal.annual_value = 10_000_000_000
    return ctxs, diags


def _p03_negosiasi(ctxs, diags):
    deal_of(ctxs, 'DL-003').deal.stage = 'Negosiasi'
    return ctxs, diags


def _p04_no_hold(ctxs, diags):
    return set_isi(ctxs, diags, 'I0335', 'Pak Bagus, Direktur Utama kami minta rekomendasi dari pengguna yang mirip dengan kami.')


def _p02_big_value(ctxs, diags):
    deal_of(ctxs, 'DL-002').deal.annual_value = 10_000_000_000
    return ctxs, diags


def _p02_decision(deal_id, nilai, keputusan='Disetujui', by='E01'):
    def mutate(ctxs, diags):
        from evaluation.cases import add_decision
        add_decision(deal_of(ctxs, 'DL-002'), decision_id='D-SIM-RANK', tanggal='2026-09-30', tipe='diskon', account_id='P02',
                     deal_id=deal_id, diminta_oleh='E07', diputuskan_oleh=by, keputusan=keputusan, nilai=nilai,
                     alasan='SINTETIS RANKING')
        return ctxs, diags
    return mutate


def _missing_data(ctxs, diags):
    deal_of(ctxs, 'DL-003').deal.stage = 'Tahap Tidak Dikenal'
    for d in diags:
        if d['deal_id'] == 'DL-002':
            d.pop('metrics', None)
    return ctxs, diags


def _jev_env():
    def boom(*a, **k):
        raise AssertionError('ranking tidak boleh melakukan HTTP/Jev')
    with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'dummy-not-a-key', 'DEALCOMPASS_ENGINE_MODE': 'jev'}), \
            patch('httpx.Client.post', boom):
        return _ranked()


def _rank(res, did):
    return item(res, did)['rank']


RANKING_CASES: list[RankCase] = [
    RankCase('K01', 'lima deal nyata', 'Kontrak fase 3 pada lima deal nyata: rank 1..5, faktor, Recommendation v1, bukti dan path.',
             _ranked, {
                 'kontrak & path valid': lambda r, c, d: contract_violations(r, c) == [],
                 'P05 discovery insufficient': lambda r, c, d: (item(r, 'DL-005')['priority_kind'], item(r, 'DL-005')['analysis_status'])
                                                              == ('discovery', 'insufficient_evidence'),
                 'P05 tetap punya tindakan discovery': lambda r, c, d: 'discovery' in item(r, 'DL-005')['recommendation']['action'],
                 'P05 bukan peluang buruk': lambda r, c, d: any('bukan bukti peluang buruk' in x for x in item(r, 'DL-005')['rationale']),
                 'P02 approval gate tetap': lambda r, c, d: item(r, 'DL-002')['recommendation']['approvals_needed'][0].startswith('VP Sales (E01)'),
                 'bukan probabilitas closing': lambda r, c, d: any('bukan probabilitas closing' in x for x in r['limitations']),
             }),
    RankCase('K02', 'input diacak', 'Lima kali urutan contexts dan diagnostics diacak independen: hasil identik.',
             _shuffled, {'output identik': lambda r, c, d: r.pop('_shuffle_identical')}),
    RankCase('K03', 'ID diganti', 'Tukar ID DL-001<->DL-004 dan P01<->P04 di seluruh input: prioritas mengikuti data, bukan ID.',
             lambda: _ranked(_swap), {
                 'rank 1 tetap Nirwana (data P04)': lambda r, c, d: deal_of(c, r['items'][0]['deal_id']).deal.account_name == 'Nirwana Hotel & Resto',
                 'rank 2 tetap Mandala (data P01)': lambda r, c, d: deal_of(c, r['items'][1]['deal_id']).deal.account_name == 'Grup Ritel Mandala',
                 'kontrak valid': lambda r, c, d: contract_violations(r, c) == [],
             }),
    RankCase('K04', 'tie', 'Salinan DL-003 dengan ID DL-903: faktor identik, diputus deal_id dan dijelaskan.',
             lambda: _ranked(_tie), {
                 'DL-003 tepat di atas DL-903': lambda r, c, d: _rank(r, 'DL-903') == _rank(r, 'DL-003') + 1,
                 'tie-break dijelaskan': lambda r, c, d: any('tie-break 4 deal_id' in x for x in item(r, 'DL-903')['rationale']),
                 'rank 1..6': lambda r, c, d: [i['rank'] for i in r['items']] == list(range(1, 7)),
             }),
    RankCase('K05', 'nilai besar bukti kurang', 'Sintetis: nilai P05 Rp10 miliar tanpa interaksi tetap discovery terakhir.',
             lambda: _ranked(_big_value_p05), {
                 'P05 tetap rank 5 discovery': lambda r, c, d: (_rank(r, 'DL-005'), item(r, 'DL-005')['priority_kind']) == (5, 'discovery'),
             }),
    RankCase('K06', 'faktor berubah', 'Sintetis: tahap P03 menjadi Negosiasi -> skor 5 setara P02, menang tie-break tahap.',
             lambda: _ranked(_p03_negosiasi), {
                 'P03 naik di atas P02': lambda r, c, d: _rank(r, 'DL-003') == 3 and _rank(r, 'DL-002') == 4,
                 'tie-break tahap dijelaskan': lambda r, c, d: any('tie-break 2 tahap' in x for x in item(r, 'DL-003')['rationale']),
             }),
    RankCase('K07', 'faktor berubah', 'Sintetis: I0335 tanpa pernyataan tunda -> hambatan pelanggan 1, P01 menjadi rank 1.',
             lambda: _ranked(_p04_no_hold), {
                 'P01 rank 1, P04 rank 2': lambda r, c, d: order(r)[:2] == ['DL-001', 'DL-004'],
             }),
    RankCase('K08', 'approval gate', 'Sintetis: nilai P02 Rp10 miliar tidak menghapus approval VP Sales.',
             lambda: _ranked(_p02_big_value), {
                 'gate tetap': lambda r, c, d: item(r, 'DL-002')['recommendation']['approvals_needed'][0].startswith('VP Sales (E01)'),
                 'skor naik ke 7, tetap di bawah 8': lambda r, c, d: _rank(r, 'DL-002') == 3,
             }),
    RankCase('K09', 'approval gate R6', 'Sintetis: approval 20% untuk deal lain (DL-OLD) tidak menghapus gate P02 di ranking.',
             lambda: _ranked(_p02_decision('DL-OLD', '20%')), {
                 'gate tetap': lambda r, c, d: len(item(r, 'DL-002')['recommendation']['approvals_needed']) == 1,
             }),
    RankCase('K10', 'approval gate R7', 'Sintetis: approval DL-002 dengan nilai kosong tidak menghapus gate P02 di ranking.',
             lambda: _ranked(_p02_decision('DL-002', '')), {
                 'gate tetap': lambda r, c, d: len(item(r, 'DL-002')['recommendation']['approvals_needed']) == 1,
             }),
    RankCase('K11', 'approval gate kontrol', 'Sintetis: approval sah 20% E01 untuk DL-002 menghapus gate tanpa mengubah rank.',
             lambda: _ranked(_p02_decision('DL-002', '20%')), {
                 'gate hilang': lambda r, c, d: item(r, 'DL-002')['recommendation']['approvals_needed'] == [],
                 'rank sama (3)': lambda r, c, d: _rank(r, 'DL-002') == 3,
             }),
    RankCase('K12', 'missing data', 'Sintetis: tahap P03 tidak dikenal dan metrics diagnostic P02 hilang -> unknown eksplisit.',
             lambda: _ranked(_missing_data), {
                 'tahap P03 null': lambda r, c, d: next(f for f in item(r, 'DL-003')['factors'] if f['name'] == 'tahap_deal')['value'] is None,
                 'interaksi terakhir P02 null': lambda r, c, d: next(f for f in item(r, 'DL-002')['factors']
                                                                    if f['name'] == 'interaksi_eksternal_terakhir')['value'] is None,
                 'unknown dicatat': lambda r, c, d: any('tahap_deal unknown' in x for x in item(r, 'DL-003')['limitations']),
                 'kemungkinan naik dicatat': lambda r, c, d: any('dapat naik melewati DL-002' in x for x in item(r, 'DL-003')['limitations']),
                 'P03 tetap acceleration': lambda r, c, d: item(r, 'DL-003')['priority_kind'] == 'acceleration',
                 'kontrak valid': lambda r, c, d: contract_violations(r, c) == [],
             }),
    RankCase('K13', 'tanpa Jev', 'Env meminta Jev dengan key dummy; ranking tetap rules dan tanpa HTTP.',
             _jev_env, {
                 'engine rules': lambda r, c, d: r['engine_mode'] == 'rules'
                                                 and all(i['recommendation']['engine_mode'] == 'rules' for i in r['items']),
             }),
    RankCase('K14', 'referensi', 'P03/P04 memakai verifikasi Bima: usage bulan lengkap terakhir, izin null, overlap bukan saling kenal.',
             _ranked, {
                 'usage C17 2026-09 dari Bima': lambda r, c, d: any('FEAT-05 2026-09: 22 pengguna aktif' in x
                                                                   for x in item(r, 'DL-003')['recommendation']['precedent_comparison']),
                 'C03 dicek belakangan': lambda r, c, d: 'C03 (' in item(r, 'DL-003')['recommendation']['action'],
                 'izin null dinyatakan': lambda r, c, d: any('bukan izin' in x for x in item(r, 'DL-004')['limitations']),
                 'path overlap K028-K116': lambda r, c, d: any(p['node_ids'][1:3] == ['K028', 'K116']
                                                              for p in item(r, 'DL-004')['evidence_paths']),
             }),
    RankCase('K15', 'sensitivitas', 'Sensitivitas tiap faktor dilaporkan; urutan P01/P04 bergantung pada faktor tahap/hambatan/nilai.',
             _ranked, {
                 'semua faktor dilaporkan': lambda r, c, d: all(any(f'faktor {f}' in x for x in r['limitations']) for f in SCORED),
             }),
]


def sensitivity_table() -> list[dict]:
    """Urutan acceleration untuk variasi bobot (dipakai evaluation/ranking.md)."""
    from backend.decision import ranking
    ctxs, diags = real_inputs()
    pairs = ranking._pair_inputs(ctxs, diags)
    profiles = [ranking._profile(c, d) for c, d in pairs]
    variants = {'dasar (semua bobot 1)': {f: 1 for f in SCORED}}
    for f in SCORED:
        variants[f'tanpa {f}'] = {g: 0 if g == f else 1 for g in SCORED}
    variants['nilai x2'] = {g: 2 if g == 'nilai_potensi_tahunan' else 1 for g in SCORED}
    variants['tahap x2'] = {g: 2 if g == 'tahap_deal' else 1 for g in SCORED}
    variants['hambatan pelanggan x2'] = {g: 2 if g == 'hambatan_dinyatakan_pelanggan' else 1 for g in SCORED}
    rows = []
    for name, w in variants.items():
        ordered = ranking._order(profiles, w)
        rows.append({'variant': name, 'order': [p['ctx'].deal.deal_id for p in ordered],
                     'scores': {p['ctx'].deal.deal_id: (sum(p['points'][f] * w[f] for f in SCORED)
                                                        if p['kind'] == 'acceleration' else None) for p in ordered}})
    return rows


def copy_inputs(ctxs, diags):
    return [c.model_copy(deep=True) for c in ctxs], copy.deepcopy(diags)
