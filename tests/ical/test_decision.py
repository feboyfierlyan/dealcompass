import csv
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from backend.contracts import DealContext
from backend.decision import policy
from backend.decision.analyze import analyze_deal, analyze_deal_trace, resolve_mode
from backend.integrations import jev
from backend.main import app
from evaluation.cases import CASES, DEAL_IDS, FIXTURES, invariant_checks, load_fixture

ROOT = Path(__file__).resolve().parents[2]


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
        self.assertTrue(policy.fits_package('Starter', 10))
        self.assertEqual(policy.smallest_package(15), 'Growth')
        self.assertEqual(policy.smallest_package(60), 'Enterprise')

    def test_constants_match_dataset(self):
        with (ROOT / 'dataset_kasirnusa/contracts_billing.csv').open(encoding='utf-8-sig', newline='') as f:
            prices = {r['harga_per_outlet_bulan'] for r in csv.DictReader(f)}
        self.assertEqual(prices, {str(policy.PRICE_PER_OUTLET_MONTH_IDR)})


class FixtureProvenanceTests(unittest.TestCase):
    """Fixture wajib berlabel dan setiap excerpt direct ada verbatim di sumber asli."""

    def test_fixtures_are_labeled_and_traceable(self):
        for deal_id in DEAL_IDS:
            raw = json.loads((FIXTURES / f'{deal_id}.json').read_text(encoding='utf-8'))
            self.assertEqual(raw['_fixture']['label'], 'FIXTURE_ICAL_SEMENTARA')
            ctx = DealContext.model_validate(raw)
            self.assertTrue(any(u.startswith('FIXTURE:') for u in ctx.unknowns))
            ev_ids = {e.id for e in ctx.evidence}
            node_ids = {n.id for n in ctx.graph.nodes}
            for e in ctx.graph.edges:
                self.assertTrue({e.source, e.target} <= node_ids, e.id)
                self.assertTrue(set(e.evidence_ids) <= ev_ids, e.id)
            for e in ctx.evidence:
                text = (ROOT / e.source_file).read_text(encoding='utf-8-sig')
                if e.evidence_type == 'direct':
                    self.assertIn(e.excerpt, text, f'{deal_id} {e.id}')
                    if e.source_file.endswith('.jsonl'):
                        row = next(json.loads(l) for l in text.splitlines() if f'"{e.source_id}"' in l)
                        self.assertEqual(row['isi'], e.excerpt)
                for loc in e.source_id.split(';'):
                    if '#L' in loc:
                        n = int(loc.split('#L')[1])
                        self.assertLessEqual(n, len(text.splitlines()))

    def test_fixture_deals_match_crm_list(self):
        from backend.ingestion.deals import list_deals
        crm = {d.deal_id: d for d in list_deals()}
        for deal_id in DEAL_IDS:
            self.assertEqual(load_fixture(deal_id).deal, crm[deal_id])


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

    def test_invariants_on_all_five_fixtures(self):
        for deal_id in DEAL_IDS:
            ctx = load_fixture(deal_id)
            rec, trace = analyze_deal_trace(ctx, mode='rules')
            with self.subTest(deal=deal_id):
                self.assertEqual({k for k, v in invariant_checks(rec, trace, ctx).items() if not v}, set())


class ModeTests(unittest.TestCase):
    def test_auto_without_key_is_rules(self):
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': '', 'DEALCOMPASS_ENGINE_MODE': ''}):
            self.assertEqual(resolve_mode(), 'rules')
            self.assertEqual(analyze_deal(load_fixture('DL-002')).engine_mode, 'rules')

    def test_explicit_jev_without_key_falls_back(self):
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': '', 'DEALCOMPASS_ENGINE_MODE': 'jev'}):
            rec = analyze_deal(load_fixture('DL-002'))
        self.assertEqual(rec.engine_mode, 'rules')
        self.assertTrue(any('missing_key' in u for u in rec.unknowns))

    def test_replay_without_recordings_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.dict(os.environ, {'DEALCOMPASS_ENGINE_MODE': 'replay', 'DEALCOMPASS_REPLAY_DIR': tmp}):
            rec = analyze_deal(load_fixture('DL-002'))
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
        self.assertEqual(c.calls[0].model, 'jev-x')

    def test_documented_error_codes(self):
        for status, code in [(401, 'unauthorized'), (422, 'invalid_request'), (429, 'rate_limited'), (529, 'overloaded')]:
            c = jev.JevClient('k', transport=httpx.MockTransport(lambda r, s=status: httpx.Response(s)))
            with self.assertRaises(jev.JevError) as cm:
                c.ask('x', {'q': jev.noul('?')})
            self.assertEqual(cm.exception.code, code)

    def test_score_criteria_bounds(self):
        with self.assertRaises(ValueError):
            jev.score('x', ['satu'])


class RouteIntegrationTests(unittest.TestCase):
    """Route milik Bima memanggil analyze_deal; konteks dipatch dengan fixture (graph Bima belum siap)."""

    def test_analyze_endpoint_returns_recommendation_with_fixture_context(self):
        with patch('backend.main.build_deal_context', return_value=load_fixture('DL-002')), \
                patch.dict(os.environ, {'TYPESAFE_API_KEY': '', 'DEALCOMPASS_ENGINE_MODE': 'rules'}):
            r = TestClient(app).post('/api/deals/DL-002/analyze')
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body['engine_mode'], 'rules')
        self.assertEqual(set(body['precedent_ids']), {'D-2025-02', 'D-2025-06'})


if __name__ == '__main__':
    unittest.main()
