"""Kasus evaluasi ICAL. Satu sumber untuk tests/ical dan evaluation/run_eval.py.

Basis konteks: build_deal_context NYATA (graph Bima, dataset asli). Kasus
mutasi/parafrase menambah atau mengubah record secara SINTETIS di salinan
konteks (format sama dengan produsen: excerpt JSON), bukan data asli.
Jev di sini memakai transport tiruan (mock), BUKAN panggilan live.
"""
import json
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from unittest.mock import patch

import httpx

from backend.contracts import DealContext, EvidenceRecord, GraphEdge, GraphNode
from backend.decision.analyze import analyze_deal_trace
from backend.decision.signals import classify_message
from backend.graph.context import build_deal_context
from backend.integrations.jev import JevClient, ReplayClient

DEAL_IDS = ('DL-001', 'DL-002', 'DL-003', 'DL-004', 'DL-005')
DECISION_FIELDS = ('decision_id', 'tanggal', 'tipe', 'account_id', 'deal_id', 'diminta_oleh', 'diputuskan_oleh',
                   'keputusan', 'nilai', 'alasan', 'bukti_interaction_id', 'fitur_dijanjikan', 'status_janji')


def real(deal_id: str) -> DealContext:
    """Salinan konteks nyata agar mutasi kasus tidak mengubah cache graph Bima."""
    return build_deal_context(deal_id).model_copy(deep=True)


def set_isi(ctx: DealContext, iid: str, text: str) -> DealContext:
    for e in ctx.evidence:
        if e.id == f'interactions.jsonl:{iid}':
            row = json.loads(e.excerpt)
            row['isi'] = text
            e.excerpt = json.dumps(row, ensure_ascii=False)
    return ctx


def add_interaction(ctx: DealContext, iid: str, account_id: str, tanggal: str, isi: str,
                    tipe: str = 'email', subjek: str = 'SINTETIS') -> DealContext:
    row = {'interaction_id': iid, 'tanggal': tanggal, 'tipe': tipe, 'account_id': account_id, 'dari': '', 'ke': '',
           'peserta': '', 'subjek': subjek, 'isi': isi, 'membalas_id': ''}
    eid = f'interactions.jsonl:{iid}'
    ctx.evidence.append(EvidenceRecord(id=eid, source_file='dataset_kasirnusa/interactions.jsonl', source_id=iid,
                                       date=tanggal, excerpt=json.dumps(row, ensure_ascii=False), evidence_type='direct'))
    ctx.graph.nodes.append(GraphNode(id=iid, label=subjek, type='interaction'))
    if account_id and account_id in {n.id for n in ctx.graph.nodes}:
        ctx.graph.edges.append(GraphEdge(id=f'interaction_for:{iid}:{account_id}', source=iid, target=account_id,
                                         relation='interaction_for', evidence_ids=[eid], evidence_type='direct',
                                         valid_from=tanggal))
    return ctx


def add_decision(ctx: DealContext, **kw) -> DealContext:
    row = {k: '' for k in DECISION_FIELDS}
    row.update(kw)
    ctx.candidate_decisions.append(row)
    ctx.evidence.append(EvidenceRecord(id=f'decision_log.csv:{row["decision_id"]}', source_file='dataset_kasirnusa/decision_log.csv',
                                       source_id=row['decision_id'], date=row['tanggal'] or None,
                                       excerpt=json.dumps(row, ensure_ascii=False), evidence_type='direct'))
    return ctx


def add_contact(ctx: DealContext, cid: str, nama: str, account_id: str, jabatan: str) -> DealContext:
    row = {'contact_id': cid, 'nama': nama, 'email': '', 'account_id_saat_ini': account_id, 'jabatan_saat_ini': jabatan}
    ctx.evidence.append(EvidenceRecord(id=f'crm_contacts.csv:{cid}', source_file='dataset_kasirnusa/crm_contacts.csv',
                                       source_id=cid, excerpt=json.dumps(row, ensure_ascii=False), evidence_type='direct'))
    return ctx


# --- Jev tiruan -----------------------------------------------------------------------

def mock_transport(mode: str = 'ok', choice_fn=classify_message, noul_value=0.0, score_value=1, delay_s=0.0):
    def handler(request: httpx.Request) -> httpx.Response:
        if delay_s:
            time.sleep(delay_s)
        if mode == 'timeout':
            raise httpx.ReadTimeout('mock timeout', request=request)
        if mode == 'unauthorized':
            return httpx.Response(401, json={'error': 'unauthorized'})
        body = json.loads(request.content)
        answers = {}
        for key, q in body['questions'].items():
            if q['type'] == 'choice':
                pick = 'di_luar_criteria' if mode == 'bad_choice' else choice_fn(body['state'])
                answers[key] = {'type': 'choice', 'choice': pick, 'probabilities': {pick: 0.9}, 'confidence': 0.9}
            elif q['type'] == 'noul':
                answers[key] = {'type': 'noul', 'noul': noul_value}
            else:
                answers[key] = {'type': 'score', 'score': score_value, 'legend': {'1': q['criteria'][1]},
                                'probabilities': {'1': 0.8}, 'confidence': 0.8}
        return httpx.Response(200, json={'model': 'jev-mock', 'answers': answers,
                                         'usage': {'input_tokens': 1, 'output_tokens': 1}})
    return httpx.MockTransport(handler)


def mock_client(mode='ok', **kw) -> JevClient:
    return JevClient('test-key', transport=mock_transport(mode, **kw), timeout_s=5)


# --- Definisi kasus --------------------------------------------------------------------

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


def _all_text(rec) -> str:
    return ' '.join([rec.action, rec.milestone, *rec.precedent_comparison, *rec.approvals_needed])


def _mentions(t):
    return [(m['source_id'], m['pct'], m['kind']) for m in t.discount_mentions]


def _needs_vp(r, t):
    return any(a.startswith('VP Sales') for a in r.approvals_needed)


def _fallback(code):
    return {
        'mode rules': lambda r, t: r.engine_mode == 'rules',
        f'unknown {code}': lambda r, t: any(code in u and 'rules deterministik' in u for u in r.unknowns),
        'policy tetap': _needs_vp,
        'tanpa label Jev': lambda r, t: all(o['source'] == 'rules' for o in t.obstacles),
    }


def _approve(deal_id='DL-002', nilai='20%'):
    return add_decision(real('DL-002'), decision_id='D-SIM-R6', tanggal='2026-09-30', tipe='diskon', account_id='P02',
                        deal_id=deal_id, diminta_oleh='E07', diputuskan_oleh='E01', keputusan='Disetujui', nilai=nilai,
                        alasan='SINTETIS REVIEW R6/R7')


def _not_approved(r, t):
    return not any('sudah disetujui' in i for i in t.interpretations)


def _replay_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        first, _ = analyze_deal_trace(real('DL-002'), client=JevClient('test-key', transport=mock_transport(), record_dir=tmp))
        rec, tr = analyze_deal_trace(real('DL-002'), client=ReplayClient(tmp))
        tr.calculations['same_action_as_recorded'] = first.action == rec.action and first.engine_mode == 'jev'
        return rec, tr


def _replay_corrupt():
    with tempfile.TemporaryDirectory() as tmp:
        analyze_deal_trace(real('DL-002'), client=JevClient('test-key', transport=mock_transport(), record_dir=tmp))
        for p in Path(tmp).iterdir():
            p.write_text('{"response": {"answers": {"hambatan": {"type": "choice", "choice": 7}}}}', encoding='utf-8')
        return analyze_deal_trace(real('DL-002'), client=ReplayClient(tmp))


def _budget():
    with patch.dict(os.environ, {'DEALCOMPASS_ANALYSIS_BUDGET_S': '0.8'}):
        return analyze_deal_trace(real('DL-002'), client=mock_client(delay_s=0.4))


CASES: list[Case] = [
    Case('E01', 'P02 nyata', 'P02 graph nyata: hambatan harga, I0348 20% sekali, tanpa 15% C01, preseden D-2025-02/06.',
         lambda: _rules(real('DL-002')), {
             'I0348 20% sekali': lambda r, t: _mentions(t) == [('I0348', 20, 'request')],
             'tanpa permintaan 15% / I0054/I0061/I0066': lambda r, t: not any(
                 m[1] == 15 or m[0] in ('I0054', 'I0061', 'I0066') for m in _mentions(t)) and '15%/' not in r.action,
             'approval VP Sales E01': lambda r, t: any(a.startswith('VP Sales (E01)') for a in r.approvals_needed),
             'satu approval tertunda': lambda r, t: len(r.approvals_needed) == 1,
             'KasirPro terbaca': lambda r, t: 'kompetitor tercatat: KasirPro' in _all_text(r)
                                              and 'Deal preseden DL-006 juga mencatat kompetitor KasirPro' in _all_text(r),
             'hambatan utama harga': lambda r, t: t.main_obstacle == 'harga',
             'tidak menyatakan approval': lambda r, t: 'sudah disetujui' not in _all_text(r).lower(),
             'preseden D-2025-02 & D-2025-06': lambda r, t: {'D-2025-02', 'D-2025-06'} <= set(r.precedent_ids),
             'Starter tidak menampung 15 outlet': lambda r, t: 'TIDAK dapat langsung menampung 15 outlet' in _all_text(r),
             'pilot berlabel skenario': lambda r, t: t.scenarios and t.scenarios[0]['label'] == 'SKENARIO_USULAN'
                                                     and t.scenarios[0]['pilot_annual_value_idr'] == 42_000_000,
             'batas 15% bukan aturan universal': lambda r, t: 'bukan aturan universal' in _all_text(r),
             'mode rules': lambda r, t: r.engine_mode == 'rules',
         }),
    Case('E02', 'request vs approval', 'Sintetis: VP Sales (E01) menyetujui 20% untuk DL-002 di decision_log.',
         lambda: _rules(add_decision(real('DL-002'), decision_id='D-SIM-01', tanggal='2026-09-30', tipe='diskon',
                                     account_id='P02', deal_id='DL-002', diminta_oleh='E07', diputuskan_oleh='E01',
                                     keputusan='Disetujui', nilai='20%')), {
             'tidak ada approval tertunda': lambda r, t: r.approvals_needed == [],
             'approval dikenali': lambda r, t: any('sudah disetujui VP Sales' in i for i in t.interpretations),
         }),
    Case('E03', 'request vs approval', 'Sintetis: "persetujuan" 20% oleh E07 (Sales Executive) tidak sah.',
         lambda: _rules(add_decision(real('DL-002'), decision_id='D-SIM-02', tanggal='2026-09-30', tipe='diskon',
                                     account_id='P02', deal_id='DL-002', diputuskan_oleh='E07', keputusan='Disetujui', nilai='20%')), {
             'approval VP masih dibutuhkan': _needs_vp,
             'pemutus bukan VP dicatat': lambda r, t: any('bukan VP Sales' in i for i in t.interpretations),
         }),
    Case('E04', 'request vs approval', 'Sintetis: persetujuan oleh E99 yang jabatannya tidak ada di konteks.',
         lambda: _rules(add_decision(real('DL-002'), decision_id='D-SIM-03', tanggal='2026-09-30', tipe='diskon',
                                     account_id='P02', deal_id='DL-002', diputuskan_oleh='E99', keputusan='Disetujui', nilai='20%')), {
             'approval VP masih dibutuhkan': _needs_vp,
             'unknown jabatan pemutus': lambda r, t: any('tidak dapat diverifikasi' in u for u in r.unknowns),
         }),
    Case('E05', 'request vs approval', 'Sintetis: penolakan 20% tercatat oleh E01 untuk DL-002.',
         lambda: _rules(add_decision(real('DL-002'), decision_id='D-SIM-04', tanggal='2026-09-30', tipe='diskon',
                                     account_id='P02', deal_id='DL-002', diputuskan_oleh='E01', keputusan='Ditolak', nilai='20%')), {
             'tanpa approval tertunda': lambda r, t: r.approvals_needed == [],
             'penolakan dikenali': lambda r, t: any('sudah ditolak (D-SIM-04)' in i for i in t.interpretations),
         }),
    Case('E06', 'request vs approval', 'Sintetis: pesan P02 mengklaim "diskon 20% sudah disetujui" tanpa decision_log.',
         lambda: _rules(add_interaction(real('DL-002'), 'I9001', 'P02', '2026-09-29',
                                        'Pak Teddy, diskon 20% sudah disetujui ya.')), {
             'approval VP masih dibutuhkan': _needs_vp,
             'klaim dicatat bukan approval': lambda r, t: ('I9001', 20, 'approval_claim') in _mentions(t)
                                                          and any('klaim persetujuan' in u for u in r.unknowns),
         }),
    Case('E31', 'R6 cakupan approval', 'Sintetis: E01 menyetujui 20% untuk deal lain (DL-OLD) di akun P02 -> tidak berlaku untuk DL-002.',
         lambda: _rules(_approve(deal_id='DL-OLD')), {
             'approval VP masih dibutuhkan': _needs_vp,
             'tidak diklaim disetujui': _not_approved,
             'dinyatakan tidak berlaku otomatis': lambda r, t: any('D-SIM-R6' in i and 'tidak berlaku otomatis' in i for i in t.interpretations),
         }),
    Case('E32', 'R6 cakupan approval', 'Sintetis: E01 menyetujui 20% di level akun P02 tanpa deal_id -> cakupan tidak terbukti.',
         lambda: _rules(_approve(deal_id='')), {
             'approval VP masih dibutuhkan': _needs_vp,
             'tidak diklaim disetujui': _not_approved,
             'cakupan tidak terbukti': lambda r, t: any('tanpa deal_id' in f for f in t.facts),
         }),
    Case('E33', 'R7 persentase', 'Sintetis: E01 menyetujui DL-002 dengan nilai kosong -> unknown, bukan approval.',
         lambda: _rules(_approve(nilai='')), {
             'approval VP masih dibutuhkan': _needs_vp,
             'tidak diklaim disetujui': _not_approved,
             'unknown persentase': lambda r, t: any('D-SIM-R6' in u and 'tidak terbaca' in u for u in r.unknowns),
         }),
    Case('E34', 'R7 persentase', 'Sintetis: E01 menyetujui DL-002 dengan nilai malformed "dua puluh persen" -> unknown.',
         lambda: _rules(_approve(nilai='dua puluh persen')), {
             'approval VP masih dibutuhkan': _needs_vp,
             'tidak diklaim disetujui': _not_approved,
             'unknown persentase': lambda r, t: any('dua puluh persen' in u for u in r.unknowns),
         }),
    Case('E35', 'R7 persentase', 'Sintetis: E01 menyetujui 15% untuk DL-002 sedangkan permintaan 20% -> tidak mencakup.',
         lambda: _rules(_approve(nilai='15%')), {
             'approval VP masih dibutuhkan': _needs_vp,
             'tidak diklaim disetujui': _not_approved,
             'dinyatakan tidak mencakup': lambda r, t: any('tidak mencakup 20%' in i for i in t.interpretations),
         }),
    Case('E07', 'hitungan diskon', 'Sintetis: I0348 menjadi diskon 10% (batas): tidak butuh VP Sales.',
         lambda: _rules(set_isi(real('DL-002'), 'I0348', 'Pak Andi, saya usul diskon 10% untuk Teras Kafe. Mohon keputusan.')), {
             'tanpa approval VP': lambda r, t: r.approvals_needed == [],
             'nilai Rp56.700.000': lambda r, t: t.calculations['discount_10pct']['annual_value_idr'] == 56_700_000,
         }),
    Case('E08', 'hitungan diskon', 'Sintetis: I0348 menjadi diskon 11%: melewati batas 10%.',
         lambda: _rules(set_isi(real('DL-002'), 'I0348', 'Pak Andi, saya usul diskon 11% untuk Teras Kafe. Mohon keputusan.')), {
             'approval VP dibutuhkan': _needs_vp,
             'nilai Rp56.070.000, turun Rp6.930.000': lambda r, t: t.calculations['discount_11pct'] == {
                 'annual_value_idr': 56_070_000, 'reduction_idr': 6_930_000},
         }),
    Case('E09', 'hitungan diskon', 'P02 nyata 20%: Rp63.000.000 -> Rp50.400.000.',
         lambda: _rules(real('DL-002')), {
             'outlet 15 dari crm_deals': lambda r, t: t.calculations['outlets'] == 15,
             'nilai diskon': lambda r, t: t.calculations['discount_20pct'] == {'annual_value_idr': 50_400_000, 'reduction_idr': 12_600_000},
             'paket terkecil Growth': lambda r, t: t.calculations['smallest_package'] == 'Growth',
         }),
    Case('E10', 'lintas akun', 'Sintetis: interaksi C23 lebih baru (minta referensi + diskon 15%) tidak mengubah P02.',
         lambda: _rules(add_interaction(real('DL-002'), 'I9002', 'C23', '2026-09-30',
                                        'Kami minta referensi dan usul diskon 15% untuk outlet baru.')), {
             'hambatan tetap harga': lambda r, t: t.main_obstacle == 'harga',
             'mention tetap I0348 saja': lambda r, t: _mentions(t) == [('I0348', 20, 'request')],
             'I9002 tidak jadi bukti fokus': lambda r, t: 'interactions.jsonl:I9002' not in r.evidence_ids,
         }),
    Case('E11', 'preseden tidak cocok', 'P02 nyata: D-2026-11 (pengecualian migrasi data C19) tidak dipakai sebagai preseden.',
         lambda: _rules(real('DL-002')), {
             'D-2026-11 tidak di precedent_ids': lambda r, t: 'D-2026-11' not in r.precedent_ids,
             'tercatat diperiksa': lambda r, t: any('D-2026-11' in i and 'tidak cocok' in i for i in t.interpretations),
         }),
    Case('E12', 'bukti kurang', 'P05 nyata: lead tanpa interaksi.',
         lambda: _rules(real('DL-005')), {
             'status insufficient_evidence': lambda r, t: t.analysis_status == 'insufficient_evidence',
             'tanpa preseden': lambda r, t: r.precedent_ids == [],
             'unknown bukti kurang': lambda r, t: any('tidak cukup' in u for u in r.unknowns),
             'tidak memakai C11': lambda r, t: 'C11' not in ' '.join(r.evidence_ids + [r.action]),
         }),
    Case('E13', 'ID tidak valid', 'Sintetis: edge merujuk evidence_id EV-NOPE.',
         lambda: _rules((lambda c: (c.graph.edges.append(GraphEdge(id='bad', source='DL-002', target='P02', relation='x',
                                                                    evidence_ids=['EV-NOPE'], evidence_type='direct')), c)[1])(real('DL-002'))), {
             'issue dilaporkan': lambda r, t: any('EV-NOPE' in u for u in r.unknowns),
             'EV-NOPE tidak dikeluarkan': lambda r, t: 'EV-NOPE' not in r.evidence_ids,
         }),
    Case('E14', 'parafrase', 'Sintetis: I0296 "biayanya kemahalan dibanding tawaran pesaing".',
         lambda: _rules(set_isi(real('DL-002'), 'I0296', 'Pak Teddy bilang biayanya kemahalan dibanding tawaran pesaing.')), {
             'I0296 tetap harga': lambda r, t: next(o for o in t.obstacles if o['source_id'] == 'I0296')['category'] == 'harga',
         }),
    Case('E15', 'parafrase', 'Sintetis sulit: "KasirPro lebih ramah di kantong". Batas rules diketahui.',
         lambda: _rules(set_isi(real('DL-002'), 'I0296', 'Pak Teddy merasa KasirPro lebih ramah di kantong.')), {
             'I0296 terdeteksi harga': lambda r, t: next(o for o in t.obstacles if o['source_id'] == 'I0296')['category'] == 'harga',
         }, known_limitation=True),
    Case('E16', 'Jev gagal', 'Jev (mock) timeout -> fallback rules penuh.',
         lambda: analyze_deal_trace(real('DL-002'), client=mock_client('timeout')),
         {**_fallback('timeout'), 'latensi tercatat': lambda r, t: t.jev_calls and t.jev_calls[0]['latency_ms'] is not None}),
    Case('E17', 'Jev gagal', 'Jev (mock) 401 -> fallback rules, key tidak bocor.',
         lambda: analyze_deal_trace(real('DL-002'), client=mock_client('unauthorized')),
         {**_fallback('unauthorized'), 'key tidak bocor': lambda r, t: 'test-key' not in json.dumps([r.model_dump(), t.to_dict()])}),
    Case('E18', 'Jev rusak', 'Jev (mock) choice di luar criteria -> invalid_response.',
         lambda: analyze_deal_trace(real('DL-002'), client=mock_client('bad_choice')), _fallback('invalid_response')),
    Case('E19', 'Jev rusak', 'Jev (mock) noul="not-a-number" -> invalid_response.',
         lambda: analyze_deal_trace(real('DL-002'), client=mock_client(noul_value='not-a-number')), _fallback('invalid_response')),
    Case('E20', 'Jev rusak', 'Jev (mock) score=7 (di luar 0..2) -> invalid_response.',
         lambda: analyze_deal_trace(real('DL-002'), client=mock_client(score_value=7)), _fallback('invalid_response')),
    Case('E21', 'Jev rusak', 'Jev (mock) noul=true (bool) -> invalid_response.',
         lambda: analyze_deal_trace(real('DL-002'), client=mock_client(noul_value=True)), _fallback('invalid_response')),
    Case('E22', 'Jev mock', 'Jev (mock) sukses -> engine_mode jev; policy tetap rules.',
         lambda: analyze_deal_trace(real('DL-002'), client=mock_client()), {
             'mode jev': lambda r, t: r.engine_mode == 'jev',
             'policy tetap': _needs_vp,
             'Score bukan probabilitas': lambda r, t: any('bukan probabilitas closing' in c for c in r.precedent_comparison),
             'Jev hanya pesan fokus': lambda r, t: sum('hambatan' in c['question_keys'] for c in t.jev_calls) == 4,
         }),
    Case('E23', 'Jev mock', 'Jev Noul (mock) menilai I0348 menyiratkan approval -> tetap bukan approval.',
         lambda: analyze_deal_trace(real('DL-002'), client=mock_client(noul_value=0.9)), {
             'approval VP masih dibutuhkan': _needs_vp,
             'unknown dicatat': lambda r, t: any('hanya diakui dari decision_log' in u for u in r.unknowns),
         }),
    Case('E24', 'Jev waktu', 'Anggaran 0,8 dtk, tiap panggilan mock 0,4 dtk -> budget_exceeded, fallback rules.',
         _budget, {**_fallback('budget_exceeded'), 'selesai < 2 dtk': lambda r, t: t.elapsed_ms < 2000}),
    Case('E25', 'replay', 'Rekam respons Jev (mock) lalu putar ulang -> engine_mode replay, hasil sama.',
         _replay_roundtrip, {
             'mode replay': lambda r, t: r.engine_mode == 'replay',
             'aksi sama': lambda r, t: t.calculations['same_action_as_recorded'],
         }),
    Case('E26', 'replay', 'Rekaman replay rusak -> invalid_replay, fallback rules.',
         _replay_corrupt, _fallback('invalid_replay')),
    Case('E27', 'P01 nyata', 'P01: I0343 + kontak CRM + riwayat kerja -> K017 Rina Hapsari (inferensi), risiko FEAT-07 C01.',
         lambda: _rules(real('DL-001')), {
             'hambatan pengambil keputusan': lambda r, t: t.main_obstacle == 'pengambil_keputusan',
             'Rina Hapsari inferensi': lambda r, t: 'Rina Hapsari' in r.action and t.decision_maker['evidence_type'] == 'inferred',
             'belum dikonfirmasi': lambda r, t: any('Belum dikonfirmasi langsung' in c for c in r.precedent_comparison),
             'risiko FEAT-07': lambda r, t: {'D-2025-11', 'D-2026-08'} <= set(r.precedent_ids),
             'tanpa approval diskon': lambda r, t: r.approvals_needed == [],
         }),
    Case('E28', 'P01 sintetis', 'Sintetis: dua kontak P01 berjabatan GM Operations -> identitas tidak dipastikan.',
         lambda: _rules(add_contact(real('DL-001'), 'K999', 'Kontak Sintetis', 'P01', 'GM Operations')), {
             'identitas tidak ditebak': lambda r, t: t.decision_maker is None and 'Rina Hapsari' not in r.action,
             'unknown identitas': lambda r, t: any('belum dapat dipastikan' in u for u in r.unknowns),
         }),
    Case('E29', 'P03 nyata', 'P03: kandidat related_account C03/C09/C17/C27 dipertimbangkan.',
         lambda: _rules(real('DL-003')), {
             'hambatan referensi': lambda r, t: t.main_obstacle == 'referensi',
             'C09 & C17 dicek pertama': lambda r, t: 'C09' in r.action and 'C17' in r.action,
             'C03 dicek belakangan dengan alasan tiket': lambda r, t: any(i.startswith('C03 dicek belakangan') and 'tiket terbuka' in i
                                                                         for i in t.interpretations),
             'C27 tidak ditolak karena health saja': lambda r, t: next(c for c in t.reference_candidates
                                                                    if c['account_id'] == 'C27')['status'] == 'cek_pertama',
             'izin/kesediaan unknown': lambda r, t: any('kandidat bukan izin' in u for u in r.unknowns),
             'tidak bilang kandidat tidak tersedia': lambda r, t: not any('belum tersedia' in u and 'referensi' in u for u in r.unknowns),
         }),
    Case('E30', 'P04 nyata', 'P04: C06 via related_account_work_overlap; overlap bukan bukti saling kenal.',
         lambda: _rules(real('DL-004')), {
             'hambatan referensi': lambda r, t: t.main_obstacle == 'referensi',
             'C06 dicek dengan izin': lambda r, t: 'Saiyo Group (C06' in r.action and 'izin kontak' in r.action,
             'industri berbeda dicatat': lambda r, t: any('C06 catatan: industri' in i for i in t.interpretations),
             'overlap bukan bukti': lambda r, t: any('tidak membuktikan saling kenal' in c for c in r.precedent_comparison),
         }),
]


def invariant_checks(rec, trace, ctx: DealContext) -> dict[str, bool]:
    ev = {e.id for e in ctx.evidence}
    dec = {d.get('decision_id') for d in ctx.candidate_decisions}
    focus = ctx.deal.account_id
    by_id = {e.id: e for e in ctx.evidence}
    other_msgs = [e for e in rec.evidence_ids if e.startswith('interactions.jsonl:')
                  and json.loads(by_id[e].excerpt).get('account_id') != focus]
    return {
        'evidence_ids valid': set(rec.evidence_ids) <= ev,
        'precedent_ids dari candidate_decisions': set(rec.precedent_ids) <= dec,
        'action berlabel USULAN': rec.action.startswith('USULAN:'),
        'interaksi output hanya akun fokus': not other_msgs,
        'mention diskon hanya akun fokus': all(m['source_id'] in {json.loads(by_id[e].excerpt)['interaction_id']
                                                                for e in ev if e.startswith('interactions.jsonl:')
                                                                and json.loads(by_id[e].excerpt).get('account_id') == focus}
                                               for m in trace.discount_mentions),
    }
