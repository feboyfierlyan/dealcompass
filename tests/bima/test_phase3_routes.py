"""HTTP adapter behavior; ranking successes here are explicitly SYNTHETIC/MOCK."""
from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app
from tests.bima.test_priorities_api import mock_priorities


class Phase3RouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_unknown_account_id_and_closed_deal_are_404(self):
        for identifier in ('DL-999', 'P02', 'DL-006'):
            response = self.client.get(f'/api/deals/{identifier}/initial-analysis')
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()['detail']['code'], 'DEAL_NOT_FOUND')

    def test_external_clock_and_internal_request_stay_distinct_over_http(self):
        response = self.client.get('/api/deals/DL-002/initial-analysis')
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['schema_version'], 'v1')
        interactions = result['metrics']['interactions']
        self.assertEqual(interactions['customer']['last_date'], '2026-09-05')
        self.assertEqual(interactions['internal']['last_date'], '2026-09-28')
        self.assertEqual(interactions['total_count'], 4)
        self.assertEqual(interactions['customer']['count'], 3)
        request = [f for f in result['findings'] if f['finding_id'].startswith('discount_request:')]
        self.assertEqual([(f['requested_discount_pct'], f['decision_lookup']['focus_log_evidence_ids'])
                          for f in request], [('20', [])])
        self.assertIn('interactions.jsonl:I0348', request[0]['evidence_ids'])

    def test_pipeline_has_all_deals_and_preserves_null_gap_and_statistics(self):
        response = self.client.get('/api/pipeline/initial-analysis')
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual({r['deal_id'] for r in result['deals']},
                         {'DL-001', 'DL-002', 'DL-003', 'DL-004', 'DL-005'})
        p05 = next(r for r in result['deals'] if r['account_id'] == 'P05')
        self.assertEqual(p05['metrics']['interactions']['total_count'], 0)
        self.assertIsNone(p05['metrics']['interactions']['last_date'])
        self.assertEqual(p05['findings'][0]['category'], 'data_gap')
        self.assertEqual(p05['findings'][0]['search_scope']['account_id'], 'P05')
        self.assertEqual(result['statistical_assessment']['status'], 'not_assessed')
        for key in ('method', 'threshold', 'outlier_deal_ids'):
            self.assertIsNone(result['statistical_assessment'][key])

    def test_absent_optional_ranking_is_501_but_missing_dependency_is_503(self):
        for missing, status, code in [('backend.decision.ranking', 501, 'PRIORITIES_NOT_IMPLEMENTED'),
                                      ('ranking_dependency', 503, 'PRIORITIES_UNAVAILABLE')]:
            error = ModuleNotFoundError('SYNTHETIC secret must not escape', name=missing)
            with patch('backend.api.phase3.importlib.import_module', side_effect=error):
                response = self.client.get('/api/pipeline/priorities')
            self.assertEqual(response.status_code, status)
            self.assertEqual(response.json()['detail']['code'], code)
            self.assertNotIn('SYNTHETIC secret', response.text)

    def test_explicit_unimplemented_engine_is_501(self):
        def unimplemented(contexts, diagnostics):
            raise NotImplementedError('SYNTHETIC private engine detail')
        with patch('backend.api.phase3.load_rank_deals', return_value=unimplemented):
            response = self.client.get('/api/pipeline/priorities')
        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.json()['detail']['code'], 'PRIORITIES_NOT_IMPLEMENTED')
        self.assertNotIn('private engine detail', response.text)

    def test_noncallable_entry_point_is_failure_not_missing_implementation(self):
        with patch('backend.api.phase3.importlib.import_module', return_value=SimpleNamespace(rank_deals=7)):
            response = self.client.get('/api/pipeline/priorities')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['detail']['code'], 'PRIORITIES_UNAVAILABLE')

    def test_full_labeled_mock_is_200_and_keeps_graph_sources_and_readiness(self):
        with patch('backend.api.phase3.load_rank_deals', return_value=mock_priorities):
            response = self.client.get('/api/pipeline/priorities')
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['fixture_label'], 'SYNTHETIC/MOCK')
        self.assertEqual([i['rank'] for i in result['items']], [1, 2, 3, 4, 5])
        p05 = next(i for i in result['items'] if i['account_id'] == 'P05')
        self.assertEqual((p05['analysis_status'], p05['priority_kind']), ('insufficient_evidence', 'discovery'))
        path = next(i['evidence_paths'][0] for i in result['items'] if i['evidence_paths'])
        self.assertEqual(path['fixture_note'], 'Original directed edge, MOCK selection.')
        self.assertTrue(set(path['evidence_ids']) <= {e['id'] for i in result['items'] for e in i['evidence']})

    def test_invalid_mock_outputs_are_503_not_partial_success(self):
        def invalid_engine(change):
            def engine(contexts, diagnostics):
                result = mock_priorities(contexts, diagnostics)
                if change == 'missing':
                    result['items'].pop()
                elif change == 'rank':
                    result['items'][0]['rank'] = True
                elif change == 'path':
                    # Not a reverse traversal (now valid, R8): the pair no longer matches the edge endpoints.
                    nodes = result['items'][0]['evidence_paths'][0]['node_ids']
                    nodes[1] = nodes[0]
                elif change == 'source':
                    result['items'][0]['evidence'][0]['excerpt'] = 'SYNTHETIC fabricated row'
                else:
                    result['methodology']['extra'] = float('nan')
                return result
            return engine
        for change in ('missing', 'rank', 'path', 'source', 'nan'):
            with self.subTest(change=change), patch('backend.api.phase3.load_rank_deals', return_value=invalid_engine(change)):
                response = self.client.get('/api/pipeline/priorities')
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()['detail']['code'], 'PRIORITIES_UNAVAILABLE')
                self.assertNotIn('SYNTHETIC fabricated row', response.text)

    def test_engine_cannot_mutate_original_graph_into_a_valid_fake_path(self):
        def mutating_engine(contexts, diagnostics):
            result = mock_priorities(contexts, diagnostics)
            item = result['items'][0]
            context = next(c for c in contexts if c.deal.deal_id == item['deal_id'])
            edge = deepcopy(context.graph.edges[0])
            edge.id = 'SYNTHETIC-injected-edge'
            context.graph.edges.append(edge)
            item['evidence_paths'][0]['edge_ids'] = [edge.id]
            return result
        with patch('backend.api.phase3.load_rank_deals', return_value=mutating_engine):
            response = self.client.get('/api/pipeline/priorities')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['detail']['code'], 'PRIORITIES_UNAVAILABLE')

    def test_engine_exception_is_redacted_in_response_and_logs(self):
        def failing_engine(contexts, diagnostics):
            raise RuntimeError('SYNTHETIC-SECRET-TOKEN')
        with patch('backend.api.phase3.load_rank_deals', return_value=failing_engine), self.assertLogs('backend.api.phase3', level='ERROR') as logs:
            response = self.client.get('/api/pipeline/priorities')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['detail']['code'], 'PRIORITIES_UNAVAILABLE')
        self.assertNotIn('SYNTHETIC-SECRET-TOKEN', response.text + '\n'.join(logs.output))

    def test_diagnostic_service_corruption_is_honest_503(self):
        with patch('backend.api.phase3.analyze_pipeline_initial', return_value={'deals': []}):
            response = self.client.get('/api/pipeline/initial-analysis')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['detail']['code'], 'DIAGNOSTICS_UNAVAILABLE')
