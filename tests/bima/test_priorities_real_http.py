"""R8 REAL integration: GET /api/pipeline/priorities with the canonical dataset and Ical rank_deals.

No mock engine, loader, context or diagnostic. Jev is not involved (ranking is rules).
"""
import json
import unittest

from fastapi.testclient import TestClient

from backend.contracts import Recommendation
from backend.graph.context import build_deal_context
from backend.graph.store import get_context_graph
from backend.main import app


class RealPrioritiesHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.response = TestClient(app).get('/api/pipeline/priorities')
        cls.result = cls.response.json()

    def test_real_endpoint_returns_200_with_exactly_p01_to_p05(self):
        self.assertEqual(self.response.status_code, 200, self.response.text[:500])
        r = self.result
        self.assertEqual((r['schema_version'], r['snapshot_date'], r['engine_mode']), ('v1', '2026-10-01', 'rules'))
        self.assertNotIn('fixture_label', r)
        self.assertEqual(r['methodology']['id'], 'deal-priority-heuristic-v1')
        self.assertEqual(sorted(i['account_id'] for i in r['items']), ['P01', 'P02', 'P03', 'P04', 'P05'])
        self.assertEqual([i['rank'] for i in r['items']], [1, 2, 3, 4, 5])
        json.dumps(r, allow_nan=False)

    def test_p02_gate_and_p05_discovery_preserved(self):
        items = {i['account_id']: i for i in self.result['items']}
        p02 = items['P02']['recommendation']
        Recommendation.model_validate(p02)
        self.assertEqual(len(p02['approvals_needed']), 1)
        self.assertTrue(p02['approvals_needed'][0].startswith('VP Sales (E01)'))
        self.assertIn('diskon 20%', p02['approvals_needed'][0])
        p05 = items['P05']
        self.assertEqual((p05['priority_kind'], p05['analysis_status']), ('discovery', 'insufficient_evidence'))
        self.assertIn('discovery', p05['recommendation']['action'])
        self.assertTrue(p05['recommendation']['unknowns'])

    def test_every_path_uses_original_edges_and_every_source_resolves(self):
        store = get_context_graph()
        reverse_steps = 0
        for item in self.result['items']:
            graph = build_deal_context(item['deal_id']).graph
            nodes = {n.id for n in graph.nodes}
            edges = {e.id: e for e in graph.edges}
            registry = {e['id']: e for e in item['evidence']}
            self.assertTrue(item['evidence_paths'])
            for path in item['evidence_paths']:
                self.assertEqual(len(path['node_ids']), len(path['edge_ids']) + 1)
                self.assertLessEqual(set(path['node_ids']), nodes)
                self.assertLessEqual(set(path['evidence_ids']), set(registry))
                for (a, b), eid in zip(zip(path['node_ids'], path['node_ids'][1:]), path['edge_ids']):
                    edge = edges[eid]
                    self.assertIn((a, b), ((edge.source, edge.target), (edge.target, edge.source)))
                    self.assertLessEqual(set(edge.evidence_ids), set(path['evidence_ids']))
                    reverse_steps += (a, b) == (edge.target, edge.source)
            for eid, record in registry.items():
                rows = store.lookup_evidence(eid)
                self.assertTrue(rows, eid)
                if record['evidence_type'] == 'direct':
                    self.assertEqual(json.loads(record['excerpt']), rows[0].raw, eid)
        self.assertGreater(reverse_steps, 0, 'real ranking uses reverse traversal (e.g. DL-002 -> P02 <- I0348)')

    def test_known_reverse_path_dl002_p02_i0348_present(self):
        p02 = next(i for i in self.result['items'] if i['deal_id'] == 'DL-002')
        self.assertIn(['DL-002', 'P02', 'I0348'], [p['node_ids'] for p in p02['evidence_paths']])


if __name__ == '__main__':
    unittest.main()
