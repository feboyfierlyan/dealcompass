"""Route POST /api/deals/{id}/analysis (pelaksana Ical). MockTransport saja; GET tidak pernah memanggil provider."""
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.decision import hybrid
from backend.decision.hybrid import AnalysisCache, AnalysisEnvelope, AnalysisService
from backend.integrations.jev import JevClient
from backend.main import app
from evaluation.cases import mock_transport


class AnalysisRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_rules_envelope_and_unknown_deal(self):
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': '', 'DEALCOMPASS_ENGINE_MODE': 'rules'}), \
                patch.object(hybrid, '_service', AnalysisService(AnalysisCache(None))):
            ok = self.client.post('/api/deals/DL-002/analysis')
            missing = self.client.post('/api/deals/DL-999/analysis')
        self.assertEqual(ok.status_code, 200, ok.text)
        body = AnalysisEnvelope.model_validate(ok.json())
        self.assertEqual((body.deal_id, body.analysis.outcome, body.analysis.provider_requests), ('DL-002', 'rules_only', 0))
        self.assertEqual(missing.status_code, 404)

    def test_mock_jev_cached_across_both_post_routes_and_refresh_is_explicit(self):
        sent = []

        def factory(mode):
            inner = mock_transport().handler
            return JevClient('MOCK', transport=__import__('httpx').MockTransport(lambda r: (sent.append(1), inner(r))[1]))
        service = AnalysisService(AnalysisCache(None), client_factory=factory)
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': '', 'DEALCOMPASS_ENGINE_MODE': 'jev'}), \
                patch.object(hybrid, '_service', service):
            first = self.client.post('/api/deals/DL-002/analysis').json()
            n = len(sent)
            second = self.client.post('/api/deals/DL-002/analysis').json()
            legacy = self.client.post('/api/deals/DL-002/analyze').json()
            self.assertEqual(len(sent), n, 'cache hit and legacy route add no provider request')
            refreshed = self.client.post('/api/deals/DL-002/analysis?refresh=true').json()
        self.assertEqual((first['analysis']['outcome'], first['analysis']['cache']), ('jev_applied', 'fresh'))
        self.assertEqual(second['analysis']['cache'], 'hit')
        self.assertEqual(legacy, first['recommendation'])
        self.assertEqual(refreshed['analysis']['cache'], 'fresh')
        self.assertEqual(service.workflows, 2)

    def test_gets_never_call_the_provider(self):
        def boom(*a, **k):
            raise AssertionError('GET called the provider')
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'MOCK', 'DEALCOMPASS_ENGINE_MODE': 'jev'}), \
                patch.object(JevClient, 'ask', boom):
            for path in ('/api/deals', '/api/deals/DL-002', '/api/pipeline/priorities',
                         '/api/pipeline/initial-analysis', '/api/deals/DL-002/initial-analysis'):
                with self.subTest(path=path):
                    self.assertEqual(self.client.get(path).status_code, 200)


if __name__ == '__main__':
    unittest.main()
