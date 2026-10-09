import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app

class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_all_five_prospects_and_values_use_business_snapshot(self):
        r = self.client.get('/api/deals')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['snapshot_date'], '2026-10-01')
        rows = {d['account_id']: d for d in data['items']}
        self.assertEqual(set(rows), {'P01', 'P02', 'P03', 'P04', 'P05'})
        self.assertEqual(sum(d['annual_value'] for d in rows.values()), 667800000)
        self.assertEqual({k:v['stage_age_days'] for k,v in rows.items()}, {'P01':20,'P02':45,'P03':10,'P04':30,'P05':5})

    def test_unknown_deal_cannot_produce_analysis(self):
        for method, path in [('get','/api/deals/DL-999'), ('post','/api/deals/DL-999/analyze')]:
            r = getattr(self.client, method)(path)
            self.assertEqual(r.status_code, 404)
            self.assertEqual(r.json()['detail']['code'], 'DEAL_NOT_FOUND')

    def test_unavailable_graph_is_explicit_not_fake_analysis(self):
        with patch('backend.main.build_deal_context', side_effect=NotImplementedError('Belum siap')):
            r = self.client.post('/api/deals/DL-002/analyze')
        self.assertEqual(r.status_code, 501)
        self.assertEqual(r.json()['detail']['code'], 'NOT_IMPLEMENTED')

