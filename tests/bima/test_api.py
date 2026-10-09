import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app


class DealApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_p02_detail_returns_real_context_and_snapshot(self):
        response = self.client.get('/api/deals/DL-002')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['schema_version'], 'v1')
        self.assertEqual(body['snapshot_date'], '2026-10-01')
        self.assertEqual(body['deal']['deal_id'], 'DL-002')
        self.assertEqual(body['deal']['account_id'], 'P02')
        self.assertEqual(body['deal']['stage_age_days'], 45)
        self.assertEqual(body['deal']['annual_value'], 63000000)
        self.assertIn('I0296', {e['source_id'] for e in body['evidence']})
        self.assertIn('I0348', {e['source_id'] for e in body['evidence']})
        self.assertIn('D-2025-02', {d['decision_id'] for d in body['candidate_decisions']})
        self.assertIn('D-2025-06', {d['decision_id'] for d in body['candidate_decisions']})

    def test_unknown_deal_is_404_for_detail_and_analyze(self):
        for method, path in [('get', '/api/deals/DL-999'),
                             ('post', '/api/deals/DL-999/analyze')]:
            with self.subTest(method=method):
                response = getattr(self.client, method)(path)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json()['detail']['code'], 'DEAL_NOT_FOUND')

    def test_unavailable_analysis_is_501_not_a_fabricated_recommendation(self):
        with patch('backend.main.analyze_deal', side_effect=NotImplementedError('Decision engine belum tersedia')):
            response = self.client.post('/api/deals/DL-002/analyze')
        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.json()['detail']['code'], 'NOT_IMPLEMENTED')
