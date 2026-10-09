"""Kasus evaluasi ICAL-01. Satu sumber untuk tests/ical dan evaluation/run_eval.py.

Basis konteks: fixture berlabel FIXTURE_ICAL_SEMENTARA (record asli). Kasus
mutasi/parafrase adalah variasi SINTETIS untuk menguji aturan, bukan data asli.
Jev pada kasus ini memakai transport tiruan (mock), BUKAN panggilan live.
"""
import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import httpx

from backend.contracts import DealContext, EvidenceRecord, GraphEdge
from backend.decision.analyze import analyze_deal_trace
from backend.decision.signals import classify_message
from backend.integrations.jev import JevClient, ReplayClient

FIXTURES = Path(__file__).resolve().parent / 'fixtures'
DEAL_IDS = ('DL-001', 'DL-002', 'DL-003', 'DL-004', 'DL-005')


def load_fixture(deal_id: str) -> DealContext:
    return DealContext.model_validate(json.loads((FIXTURES / f'{deal_id}.json').read_text(encoding='utf-8')))


def _set_excerpt(ctx: DealContext, eid: str, text: str) -> DealContext:
    for e in ctx.evidence:
        if e.id == eid:
            e.excerpt = text
    return ctx


def _add_decision(ctx: DealContext, **kw) -> DealContext:
    base = {k: '' for k in ('decision_id', 'tanggal', 'tipe', 'account_id', 'deal_id', 'diminta_oleh',
                            'diputuskan_oleh', 'keputusan', 'nilai', 'alasan', 'bukti_interaction_id',
                            'fitur_dijanjikan', 'status_janji')}
    base.update(kw)
    ctx.candidate_decisions.append(base)
    return ctx


# --- Jev tiruan -------------------------------------------------------------------

def mock_transport(mode: str = 'ok', choice_fn=classify_message, noul_value: float = 0.0):
    def handler(request: httpx.Request) -> httpx.Response:
        if mode == 'timeout':
            raise httpx.ReadTimeout('mock timeout', request=request)
        if mode == 'unauthorized':
            return httpx.Response(401, json={'error': 'unauthorized'})
        body = json.loads(request.content)
        assert request.headers['authorization'] == 'Bearer test-key'
        answers = {}
        for key, q in body['questions'].items():
            if q['type'] == 'choice':
                pick = 'di_luar_criteria' if mode == 'bad_choice' else choice_fn(body['state'])
                answers[key] = {'type': 'choice', 'choice': pick, 'probabilities': {pick: 0.9}, 'confidence': 0.9}
            elif q['type'] == 'noul':
                answers[key] = {'type': 'noul', 'noul': noul_value}
            else:
                answers[key] = {'type': 'score', 'score': 1, 'legend': {'1': q['criteria'][1]},
                                'probabilities': {'1': 0.8}, 'confidence': 0.8}
        return httpx.Response(200, json={'model': 'jev-mock', 'answers': answers,
                                         'usage': {'input_tokens': 1, 'output_tokens': 1}})
    return httpx.MockTransport(handler)


def mock_client(mode='ok', **kw) -> JevClient:
    return JevClient('test-key', transport=mock_transport(mode, **kw), timeout_s=1)


# --- Definisi kasus -----------------------------------------------------------------

@dataclass
class Case:
    id: str
    category: str
    description: str
    run: Callable[[], tuple]
    checks: dict[str, Callable] = field(default_factory=dict)
    known_limitation: bool = False


def _rules(ctx):
    return analyze_deal_trace(ctx, mode='rules')


def _p02():
    return load_fixture('DL-002')


def _replay_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        live = JevClient('test-key', transport=mock_transport(), timeout_s=1, record_dir=tmp)
        first, _ = analyze_deal_trace(_p02(), client=live)
        rec, tr = analyze_deal_trace(_p02(), client=ReplayClient(tmp))
        tr.calculations['recorded_mode'] = first.engine_mode
        tr.calculations['same_action_as_recorded'] = first.action == rec.action
        return rec, tr


def _all_text(rec) -> str:
    return ' '.join([rec.action, rec.milestone, *rec.precedent_comparison, *rec.approvals_needed])


CASES: list[Case] = [
    Case('E01', 'P02 dasar', 'P02: hambatan harga + permintaan diskon 20% (I0348), preseden D-2025-02/06.',
         lambda: _rules(_p02()), {
             'hambatan utama harga': lambda r, t: t.main_obstacle == 'harga',
             'approval VP Sales dibutuhkan': lambda r, t: any(a.startswith('VP Sales') for a in r.approvals_needed),
             'tidak menyatakan approval': lambda r, t: 'sudah disetujui' not in _all_text(r).lower(),
             'preseden D-2025-02 & D-2025-06': lambda r, t: set(r.precedent_ids) == {'D-2025-02', 'D-2025-06'},
             'Starter tidak menampung 15 outlet': lambda r, t: 'TIDAK dapat langsung menampung 15 outlet' in _all_text(r),
             'pilot berlabel skenario': lambda r, t: t.scenarios and t.scenarios[0]['label'] == 'SKENARIO_USULAN'
                                                     and t.scenarios[0]['pilot_annual_value_idr'] == 42_000_000,
             'batas 15% bukan aturan universal': lambda r, t: 'bukan aturan universal' in _all_text(r),
             'mode rules': lambda r, t: r.engine_mode == 'rules',
         }),
    Case('E02', 'request vs approval', 'Ada keputusan sah: VP Sales (E01) menyetujui 20% untuk DL-002 (sintetis).',
         lambda: _rules(_add_decision(_p02(), decision_id='D-SIM-01', tanggal='2026-09-30', tipe='diskon',
                                      account_id='P02', deal_id='DL-002', diminta_oleh='E07',
                                      diputuskan_oleh='E01', keputusan='Disetujui', nilai='20%')), {
             'tidak ada approval tertunda': lambda r, t: r.approvals_needed == [],
             'approval dikenali': lambda r, t: any('sudah disetujui VP Sales' in i for i in t.interpretations),
         }),
    Case('E03', 'request vs approval', 'Persetujuan 20% oleh E07 (bukan VP Sales) tidak sah (sintetis).',
         lambda: _rules(_add_decision(_p02(), decision_id='D-SIM-02', tipe='diskon', deal_id='DL-002',
                                      diputuskan_oleh='E07', keputusan='Disetujui', nilai='20%')), {
             'approval VP masih dibutuhkan': lambda r, t: any(a.startswith('VP Sales') for a in r.approvals_needed),
         }),
    Case('E04', 'request vs approval', 'Persetujuan ada tetapi jabatan pemutus tak dapat diverifikasi (EV-E01 dihapus).',
         lambda: _rules(_add_decision(
             _p02().model_copy(update={'evidence': [e for e in _p02().evidence if e.id != 'EV-E01']}),
             decision_id='D-SIM-03', tipe='diskon', deal_id='DL-002', diputuskan_oleh='E01',
             keputusan='Disetujui', nilai='20%')), {
             'approval VP masih dibutuhkan': lambda r, t: any(a.startswith('VP Sales') for a in r.approvals_needed),
             'unknown jabatan pemutus': lambda r, t: any('tidak dapat diverifikasi' in u for u in r.unknowns),
         }),
    Case('E05', 'hitungan diskon', 'Permintaan diskon 10% (batas, sintetis): tidak butuh VP Sales.',
         lambda: _rules(_set_excerpt(_p02(), 'EV-I0348', 'Pak Andi, saya usul diskon 10% untuk Teras Kafe. Mohon keputusan.')), {
             'tanpa approval VP': lambda r, t: r.approvals_needed == [],
             'nilai Rp56.700.000': lambda r, t: t.calculations['discount_10pct']['annual_value_idr'] == 56_700_000,
         }),
    Case('E06', 'hitungan diskon', 'Permintaan diskon 11% (sintetis): melewati batas 10%.',
         lambda: _rules(_set_excerpt(_p02(), 'EV-I0348', 'Pak Andi, saya usul diskon 11% untuk Teras Kafe. Mohon keputusan.')), {
             'approval VP dibutuhkan': lambda r, t: any(a.startswith('VP Sales') for a in r.approvals_needed),
             'nilai Rp56.070.000, turun Rp6.930.000': lambda r, t: t.calculations['discount_11pct'] == {
                 'annual_value_idr': 56_070_000, 'reduction_idr': 6_930_000},
         }),
    Case('E07', 'hitungan diskon', 'P02 20%: Rp63.000.000 -> Rp50.400.000 (turun Rp12.600.000).',
         lambda: _rules(_p02()), {
             'outlet 15': lambda r, t: t.calculations['outlets'] == 15,
             'nilai diskon': lambda r, t: t.calculations['discount_20pct'] == {
                 'annual_value_idr': 50_400_000, 'reduction_idr': 12_600_000},
             'paket terkecil Growth': lambda r, t: t.calculations['smallest_package'] == 'Growth',
         }),
    Case('E08', 'preseden tidak cocok', 'D-2024-05 (janji_fitur C09, ditepati) ditambahkan ke P02: harus tidak dipakai.',
         lambda: _rules(_add_decision(_p02(), decision_id='D-2024-05', tanggal='2024-08-15', tipe='janji_fitur',
                                      account_id='C09', diminta_oleh='E04', diputuskan_oleh='E09',
                                      keputusan='Disetujui', alasan='Program loyalti untuk klien F&B',
                                      fitur_dijanjikan='FEAT-03', status_janji='Ditepati (rilis Feb 2026)')), {
             'D-2024-05 tidak di precedent_ids': lambda r, t: 'D-2024-05' not in r.precedent_ids,
             'tercatat diperiksa': lambda r, t: any('D-2024-05 diperiksa' in i for i in t.interpretations),
         }),
    Case('E09', 'bukti kurang', 'P05: lead tanpa interaksi.',
         lambda: _rules(load_fixture('DL-005')), {
             'status insufficient_evidence': lambda r, t: t.analysis_status == 'insufficient_evidence',
             'tanpa preseden': lambda r, t: r.precedent_ids == [],
             'unknown bukti kurang': lambda r, t: any('tidak cukup' in u for u in r.unknowns),
             'tidak memakai C11': lambda r, t: 'C11' not in ' '.join(r.evidence_ids + [r.action]),
         }),
    Case('E10', 'ID tidak valid', 'Edge merujuk evidence_id EV-NOPE yang tidak ada (sintetis).',
         lambda: _rules(_p02().model_copy(update={'graph': _p02().graph.model_copy(update={'edges': [
             *_p02().graph.edges, GraphEdge(id='bad', source='deal:DL-002', target='account:P02', relation='x',
                                            evidence_ids=['EV-NOPE'], evidence_type='direct')]})})), {
             'issue dilaporkan': lambda r, t: any('EV-NOPE' in u for u in r.unknowns),
             'EV-NOPE tidak dikeluarkan': lambda r, t: 'EV-NOPE' not in r.evidence_ids,
         }),
    Case('E11', 'parafrase', 'I0296 diparafrasekan: "biayanya kemahalan dibanding tawaran pesaing" (sintetis).',
         lambda: _rules(_set_excerpt(_p02(), 'EV-I0296', 'Pak Teddy bilang biayanya kemahalan dibanding tawaran pesaing.')), {
             'I0296 tetap harga': lambda r, t: next(o for o in t.obstacles if o['evidence_id'] == 'EV-I0296')['category'] == 'harga',
         }),
    Case('E12', 'parafrase', 'Parafrase sulit: "KasirPro lebih ramah di kantong" (sintetis). Batas rules diketahui.',
         lambda: _rules(_set_excerpt(_p02(), 'EV-I0296', 'Pak Teddy merasa KasirPro lebih ramah di kantong.')), {
             'I0296 terdeteksi harga': lambda r, t: next(o for o in t.obstacles if o['evidence_id'] == 'EV-I0296')['category'] == 'harga',
         }, known_limitation=True),
    Case('E13', 'Jev timeout', 'Jev (mock) timeout -> fallback rules eksplisit.',
         lambda: analyze_deal_trace(_p02(), client=mock_client('timeout')), {
             'mode rules': lambda r, t: r.engine_mode == 'rules',
             'unknown timeout': lambda r, t: any('timeout' in u for u in r.unknowns),
             'policy tetap': lambda r, t: any(a.startswith('VP Sales') for a in r.approvals_needed),
             'latensi tercatat': lambda r, t: t.jev_calls and t.jev_calls[0]['latency_ms'] is not None,
         }),
    Case('E14', 'Jev gagal', 'Jev (mock) 401 -> fallback rules, tanpa membocorkan key.',
         lambda: analyze_deal_trace(_p02(), client=mock_client('unauthorized')), {
             'mode rules': lambda r, t: r.engine_mode == 'rules',
             'unknown unauthorized': lambda r, t: any('unauthorized' in u for u in r.unknowns),
             'key tidak bocor': lambda r, t: 'test-key' not in json.dumps([r.model_dump(), t.to_dict()]),
         }),
    Case('E15', 'Jev mock', 'Jev (mock) sukses -> engine_mode jev; policy tetap rules.',
         lambda: analyze_deal_trace(_p02(), client=mock_client()), {
             'mode jev': lambda r, t: r.engine_mode == 'jev',
             'policy tetap': lambda r, t: any(a.startswith('VP Sales') for a in r.approvals_needed),
             'Score bukan probabilitas': lambda r, t: any('bukan probabilitas closing' in c for c in r.precedent_comparison),
         }),
    Case('E16', 'Jev mock', 'Jev Noul (mock) menilai I0348 menyiratkan approval -> tetap bukan approval.',
         lambda: analyze_deal_trace(_p02(), client=mock_client(noul_value=0.9)), {
             'approval VP masih dibutuhkan': lambda r, t: any(a.startswith('VP Sales') for a in r.approvals_needed),
             'unknown dicatat': lambda r, t: any('hanya diakui dari decision_log' in u for u in r.unknowns),
         }),
    Case('E17', 'Jev gagal', 'Jev (mock) memberi choice di luar criteria -> invalid_response, fallback rules.',
         lambda: analyze_deal_trace(_p02(), client=mock_client('bad_choice')), {
             'mode rules': lambda r, t: r.engine_mode == 'rules',
             'unknown invalid': lambda r, t: any('invalid_response' in u for u in r.unknowns),
         }),
    Case('E18', 'replay', 'Rekam respons Jev (mock) lalu putar ulang -> engine_mode replay, hasil sama.',
         _replay_roundtrip, {
             'mode replay': lambda r, t: r.engine_mode == 'replay',
             'aksi sama': lambda r, t: t.calculations['same_action_as_recorded'],
         }),
    Case('E19', 'P01', 'P01: pengambil keputusan baru (I0343) + riwayat K017 di C01 (FEAT-07 belum ditepati).',
         lambda: _rules(load_fixture('DL-001')), {
             'hambatan pengambil keputusan': lambda r, t: t.main_obstacle == 'pengambil_keputusan',
             'menyebut Rina Hapsari': lambda r, t: 'Rina Hapsari' in r.action,
             'risiko FEAT-07 inferensi': lambda r, t: any('FEAT-07' in c and 'inferensi' in c for c in r.precedent_comparison),
             'tanpa approval diskon': lambda r, t: r.approvals_needed == [],
         }),
    Case('E20', 'P04', 'P04: minta referensi; overlap K028-K116 bukan bukti saling kenal.',
         lambda: _rules(load_fixture('DL-004')), {
             'hambatan referensi': lambda r, t: t.main_obstacle == 'referensi',
             'Saiyo Group diusulkan': lambda r, t: 'Saiyo Group' in r.action,
             'overlap bukan bukti': lambda r, t: any('tidak membuktikan saling kenal' in c for c in r.precedent_comparison),
         }),
    Case('E21', 'P03', 'P03: minta referensi apotek.',
         lambda: _rules(load_fixture('DL-003')), {
             'hambatan referensi': lambda r, t: t.main_obstacle == 'referensi',
             'C09/C17 diusulkan': lambda r, t: 'Apotek Medika Farma' in r.action and 'Apotek Bunda Sehat' in r.action,
         }),
]


def invariant_checks(rec, trace, ctx: DealContext) -> dict[str, bool]:
    ev = {e.id for e in ctx.evidence}
    dec = {d.get('decision_id') for d in ctx.candidate_decisions}
    return {
        'evidence_ids valid': set(rec.evidence_ids) <= ev,
        'precedent_ids dari candidate_decisions': set(rec.precedent_ids) <= dec,
        'action berlabel USULAN': rec.action.startswith('USULAN:'),
        'tanpa probabilitas closing': 'probabilitas closing' not in rec.action,
    }
