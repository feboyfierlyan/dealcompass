import csv
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from backend.decision import policy
from backend.decision.analyze import analyze_deal, analyze_deal_trace, resolve_mode
from backend.decision.records import ContextIndex
from backend.decision.signals import extract
from backend.integrations import jev
from backend.main import app
from evaluation.cases import CASES, DEAL_IDS, add_decision, add_interaction, invariant_checks, mock_client, real

ROOT = Path(__file__).resolve().parents[2]
RULES_ENV = {'TYPESAFE_API_KEY': '', 'DEALCOMPASS_ENGINE_MODE': 'rules'}


class PolicyTests(unittest.TestCase):
    def test_annual_value_integer_math(self):
        self.assertEqual(policy.annual_value_idr(15), 63_000_000)
        self.assertEqual(policy.annual_value_idr(15, 20), 50_400_000)
        self.assertEqual(policy.annual_value_idr(10), 42_000_000)
        with self.assertRaises(ValueError):
            policy.annual_value_idr(15, 101)

    def test_discount_threshold_is_strictly_above_10(self):
        self.assertFalse(policy.requires_vp_approval(10))
        self.assertTrue(policy.requires_vp_approval(11))

    def test_starter_cannot_hold_15_outlets(self):
        self.assertFalse(policy.fits_package('Starter', 15))
        self.assertEqual(policy.smallest_package(15), 'Growth')
        self.assertEqual(policy.smallest_package(60), 'Enterprise')

    def test_constants_match_dataset(self):
        with (ROOT / 'dataset_kasirnusa/contracts_billing.csv').open(encoding='utf-8-sig', newline='') as f:
            prices = {r['harga_per_outlet_bulan'] for r in csv.DictReader(f)}
        self.assertEqual(prices, {str(policy.PRICE_PER_OUTLET_MONTH_IDR)})


class RealGraphIntegrationTests(unittest.TestCase):
    """Wajib ICAL-02: memakai build_deal_context nyata (graph Bima), bukan fixture."""

    def test_p02_has_single_20pct_request_from_i0348_and_no_c01_15pct(self):
        ctx = real('DL-002')
        s = extract(ContextIndex(ctx))
        self.assertEqual([(m.source_id, m.pct, m.kind) for m in s.discount_mentions], [('I0348', 20, 'request')])
        rec, _ = analyze_deal_trace(ctx, mode='rules')
        joined = json.dumps(rec.model_dump(), ensure_ascii=False)
        for iid in ('I0054', 'I0061', 'I0066'):
            self.assertNotIn(f'interactions.jsonl:{iid}', rec.evidence_ids)
        self.assertNotIn('15%/', rec.action)
        self.assertEqual(len(rec.approvals_needed), 1)
        self.assertIn('diskon 20%', rec.approvals_needed[0])
        self.assertNotIn('diskon 15%', ' '.join(rec.approvals_needed))
        self.assertIn('I0348', joined)

    def test_e01_recognized_as_vp_sales(self):
        idx = ContextIndex(real('DL-002'))
        self.assertEqual(idx.vp_sales_ids(), {'E01'})
        self.assertEqual(idx.employee_title('E01'), 'VP Sales')
        rec, _ = analyze_deal_trace(real('DL-002'), mode='rules')
        self.assertTrue(rec.approvals_needed[0].startswith('VP Sales (E01)'))

    def test_kasirpro_read_from_json_fields(self):
        idx = ContextIndex(real('DL-002'))
        self.assertEqual(idx.competitor_of('DL-002'), 'KasirPro')
        self.assertEqual(idx.competitor_of('DL-006'), 'KasirPro')
        self.assertEqual(idx.competitor_of('DL-007'), 'KasirPro')
        self.assertEqual(idx.parse_errors, [])

    def test_newer_other_account_evidence_does_not_change_prospect_obstacle(self):
        base, _ = analyze_deal_trace(real('DL-002'), mode='rules')
        ctx = add_interaction(real('DL-002'), 'I9002', 'C23', '2026-09-30',
                              'Kami minta referensi dan usul diskon 15% untuk outlet baru.')
        rec, trace = analyze_deal_trace(ctx, mode='rules')
        self.assertEqual(trace.main_obstacle, 'harga')
        self.assertEqual(rec.approvals_needed, base.approvals_needed)
        self.assertEqual(rec.action, base.action)
        self.assertNotIn('interactions.jsonl:I9002', rec.evidence_ids)

    def test_p03_p04_read_available_reference_candidates(self):
        rec3, t3 = analyze_deal_trace(real('DL-003'), mode='rules')
        status = {c['account_id']: c['status'] for c in t3.reference_candidates}
        self.assertEqual(status, {'C03': 'cek_dengan_catatan', 'C09': 'cek_pertama', 'C17': 'cek_pertama', 'C27': 'cek_pertama'})
        self.assertTrue(all(c['suitability'] is None and c['contact_consent'] is None for c in t3.reference_candidates))
        self.assertIn('C09', rec3.action)
        self.assertIn('C17', rec3.action)
        rec4, t4 = analyze_deal_trace(real('DL-004'), mode='rules')
        self.assertEqual([c['account_id'] for c in t4.reference_candidates], ['C06'])
        self.assertIn('Saiyo Group (C06', rec4.action)
        self.assertTrue(any('tidak membuktikan saling kenal' in c for c in rec4.precedent_comparison))

    def test_p05_states_insufficient_information(self):
        rec, trace = analyze_deal_trace(real('DL-005'), mode='rules')
        self.assertEqual(trace.analysis_status, 'insufficient_evidence')
        self.assertEqual(rec.precedent_ids, [])
        self.assertTrue(any('tidak cukup' in u for u in rec.unknowns))

    def test_broken_jev_response_falls_back_clearly(self):
        for kw, code in [({'noul_value': 'not-a-number'}, 'invalid_response'), ({'score_value': 'x'}, 'invalid_response'),
                         ({'mode': 'bad_choice'}, 'invalid_response'), ({'mode': 'timeout'}, 'timeout')]:
            with self.subTest(kw=kw):
                rec, trace = analyze_deal_trace(real('DL-002'), client=mock_client(**kw))
                self.assertEqual(rec.engine_mode, 'rules')
                self.assertTrue(any(f'gagal: {code}' in u for u in rec.unknowns), rec.unknowns)
                self.assertTrue(all(o['source'] == 'rules' for o in trace.obstacles))
                self.assertTrue(rec.approvals_needed[0].startswith('VP Sales (E01)'))

    def _approval(self, deal_id='DL-002', account_id='P02', nilai='20%'):
        ctx = add_decision(real('DL-002'), decision_id='D-REG', tanggal='2026-09-30', tipe='diskon', account_id=account_id,
                           deal_id=deal_id, diminta_oleh='E07', diputuskan_oleh='E01', keputusan='Disetujui', nilai=nilai)
        return analyze_deal_trace(ctx, mode='rules')

    def test_valid_vp_approval_for_focus_deal_is_recognized(self):
        rec, trace = self._approval()
        self.assertEqual(rec.approvals_needed, [])
        self.assertTrue(any('DL-002 sudah disetujui VP Sales' in i and 'D-REG' in i for i in trace.interpretations))

    def test_r6_approval_for_other_deal_or_account_level_does_not_apply(self):
        for deal_id, account_id in [('DL-OLD', 'P02'), ('', 'P02'), ('DL-002', 'C23')]:
            with self.subTest(deal_id=deal_id, account_id=account_id):
                rec, trace = self._approval(deal_id=deal_id, account_id=account_id)
                self.assertEqual(len(rec.approvals_needed), 1)
                self.assertTrue(rec.approvals_needed[0].startswith('VP Sales (E01)'))
                self.assertFalse(any('sudah disetujui' in i for i in trace.interpretations))

    def test_r7_empty_or_malformed_percentage_is_unknown_not_approval(self):
        for nilai in ('', 'dua puluh persen', '20', '15%'):
            with self.subTest(nilai=nilai):
                rec, trace = self._approval(nilai=nilai)
                self.assertEqual(len(rec.approvals_needed), 1)
                self.assertFalse(any('sudah disetujui' in i for i in trace.interpretations))
                if nilai != '15%':
                    self.assertTrue(any('D-REG' in u and 'tidak terbaca' in u for u in rec.unknowns))

    def test_invariants_on_all_five_real_contexts(self):
        for deal_id in DEAL_IDS:
            ctx = real(deal_id)
            rec, trace = analyze_deal_trace(ctx, mode='rules')
            with self.subTest(deal=deal_id):
                self.assertEqual({k for k, v in invariant_checks(rec, trace, ctx).items() if not v}, set())

    def test_analyze_endpoint_with_real_context(self):
        with patch.dict(os.environ, RULES_ENV):
            r = TestClient(app).post('/api/deals/DL-002/analyze')
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body['engine_mode'], 'rules')
        self.assertIn('D-2025-02', body['precedent_ids'])


class EvaluationCaseTests(unittest.TestCase):
    def test_core_cases_pass(self):
        self.assertGreaterEqual(len(CASES), 10)
        for case in CASES:
            if case.known_limitation:
                continue
            with self.subTest(case=case.id):
                rec, trace = case.run()
                failed = [n for n, fn in case.checks.items() if not fn(rec, trace)]
                self.assertEqual(failed, [], case.description)


class ModeTests(unittest.TestCase):
    def test_auto_without_key_is_rules(self):
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': '', 'DEALCOMPASS_ENGINE_MODE': ''}):
            self.assertEqual(resolve_mode(), 'rules')
            self.assertEqual(analyze_deal(real('DL-002')).engine_mode, 'rules')

    def test_explicit_jev_without_key_falls_back(self):
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': '', 'DEALCOMPASS_ENGINE_MODE': 'jev'}):
            rec = analyze_deal(real('DL-002'))
        self.assertEqual(rec.engine_mode, 'rules')
        self.assertTrue(any('missing_key' in u for u in rec.unknowns))

    def test_replay_without_recordings_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.dict(os.environ, {'DEALCOMPASS_ENGINE_MODE': 'replay', 'DEALCOMPASS_REPLAY_DIR': tmp}):
            rec = analyze_deal(real('DL-002'))
        self.assertEqual(rec.engine_mode, 'rules')
        self.assertTrue(any('replay_missing' in u for u in rec.unknowns))


class JevAdapterTests(unittest.TestCase):
    def test_request_follows_documented_shape_and_hides_key(self):
        seen = {}

        def handler(req: httpx.Request):
            seen['url'], seen['auth'], seen['body'] = str(req.url), req.headers['authorization'], json.loads(req.content)
            return httpx.Response(200, json={'model': 'jev-x', 'answers': {
                'q': {'type': 'choice', 'choice': 'a', 'probabilities': {'a': 1.0}, 'confidence': 1.0}}, 'usage': {}})

        with tempfile.TemporaryDirectory() as tmp:
            c = jev.JevClient('secret-123', transport=httpx.MockTransport(handler), record_dir=tmp)
            ans = c.ask('teks', {'q': jev.choice('pilih', {'a': 'A', 'b': 'B'})})
            recorded = ''.join(p.read_text(encoding='utf-8') for p in Path(tmp).iterdir())
        self.assertEqual(seen['url'], 'https://api.typesafe.ai/v1/systemone')
        self.assertEqual(seen['auth'], 'Bearer secret-123')
        self.assertEqual(seen['body']['model'], 'jev-latest')
        self.assertEqual(set(seen['body']), {'state', 'model', 'questions'})
        self.assertEqual(ans['q']['choice'], 'a')
        self.assertNotIn('secret-123', repr(c) + json.dumps([vars(x) for x in c.calls]) + recorded)

    def test_documented_error_codes(self):
        for status, code in [(401, 'unauthorized'), (422, 'invalid_request'), (429, 'rate_limited'), (529, 'overloaded')]:
            c = jev.JevClient('k', transport=httpx.MockTransport(lambda r, s=status: httpx.Response(s)))
            with self.assertRaises(jev.JevError) as cm:
                c.ask('x', {'q': jev.noul('?')})
            self.assertEqual(cm.exception.code, code)

    def test_numeric_validation_rejects_bad_values(self):
        q = {'n': jev.noul('?'), 's': jev.score('?', ['a', 'b', 'c'])}
        good = {'n': {'type': 'noul', 'noul': 0.2}, 's': {'type': 'score', 'score': 2, 'confidence': 0.5}}
        jev._validate_answers(q, {'answers': good})
        bad_values = [('n', 'noul', 'not-a-number'), ('n', 'noul', True), ('n', 'noul', 1.5), ('n', 'noul', float('nan')),
                      ('s', 'score', 'not-a-number'), ('s', 'score', 3), ('s', 'score', -1), ('s', 'confidence', 2)]
        for key, fld, val in bad_values:
            with self.subTest(key=key, fld=fld, val=val):
                answers = json.loads(json.dumps(good))
                answers[key][fld] = val
                with self.assertRaises(jev.JevError) as cm:
                    jev._validate_answers(q, {'answers': answers})
                self.assertEqual(cm.exception.code, 'invalid_response')
        for body in (None, [], {'answers': []}, {'answers': {'n': 'x'}}):
            with self.assertRaises(jev.JevError):
                jev._validate_answers(q, body)

    def test_score_criteria_bounds(self):
        with self.assertRaises(ValueError):
            jev.score('x', ['satu'])


if __name__ == '__main__':
    unittest.main()
