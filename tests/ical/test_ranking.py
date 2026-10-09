"""ICAL-03: rank_deals pada konteks + diagnostic nyata Bima. Tidak ada Jev/mock/live di sini."""
import json
import unittest

from backend.contracts import Recommendation
from backend.decision.ranking import METHOD_ID, SCORED, path_is_valid, rank_deals
from backend.graph.store import get_context_graph
from evaluation.ranking_cases import (RANKING_CASES, contract_violations, deal_of, item, order, real_inputs,
                                      referenced_ids)


class RankingRealDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctxs, cls.diags = real_inputs()
        cls.res = rank_deals(cls.ctxs, cls.diags)

    def test_contract_shape_for_five_real_deals(self):
        self.assertEqual(contract_violations(self.res, self.ctxs), [])
        self.assertEqual(self.res['methodology']['id'], METHOD_ID)
        self.assertEqual(set(self.res['methodology']['weights']), set(SCORED))
        self.assertEqual(len(self.res['items']), 5)
        for it in self.res['items']:
            Recommendation.model_validate(it['recommendation'])
            self.assertTrue(it['rationale'] and it['limitations'] and it['evidence_paths'])

    def test_actual_order_and_tier(self):
        # Hasil metode pada snapshot ini (bukan urutan yang dipaksakan); lihat evaluation/ranking.md.
        self.assertEqual(order(self.res), ['DL-004', 'DL-001', 'DL-002', 'DL-003', 'DL-005'])
        kinds = {i['deal_id']: (i['priority_kind'], i['analysis_status']) for i in self.res['items']}
        self.assertEqual(kinds['DL-005'], ('discovery', 'insufficient_evidence'))
        self.assertTrue(all(v == ('acceleration', 'ready') for k, v in kinds.items() if k != 'DL-005'))

    def test_p05_discovery_action_not_bad_opportunity(self):
        p5 = item(self.res, 'DL-005')
        self.assertIn('discovery', p5['recommendation']['action'])
        self.assertIsNone(next(f for f in p5['factors'] if f['name'] == 'skor_prioritas')['value'])
        self.assertTrue(any('bukan bukti peluang buruk' in r for r in p5['rationale']))
        self.assertTrue(p5['recommendation']['unknowns'])

    def test_every_evidence_id_resolves_to_source_row(self):
        store = get_context_graph()
        for it in self.res['items']:
            by_id = {e['id']: e for e in it['evidence']}
            self.assertLessEqual(referenced_ids(it), set(by_id))
            for eid, e in by_id.items():
                rows = store.lookup_evidence(eid)
                self.assertTrue(rows, eid)
                if e['evidence_type'] == 'direct':
                    self.assertEqual(json.loads(e['excerpt']), rows[0].raw, eid)

    def test_paths_follow_original_graph_edges(self):
        for it in self.res['items']:
            graph = deal_of(self.ctxs, it['deal_id']).graph
            edges = {e.id: e for e in graph.edges}
            for p in it['evidence_paths']:
                self.assertTrue(path_is_valid(graph, p), p['node_ids'])
                for eid in p['edge_ids']:
                    self.assertIn(eid, edges)

    def test_inputs_not_mutated(self):
        ctxs, diags = real_inputs()
        before = json.dumps([[c.model_dump() for c in ctxs], diags], sort_keys=True)
        rank_deals(ctxs, diags)
        self.assertEqual(json.dumps([[c.model_dump() for c in ctxs], diags], sort_keys=True), before)

    def test_approval_gate_kept_for_p02(self):
        p2 = item(self.res, 'DL-002')['recommendation']
        self.assertEqual(len(p2['approvals_needed']), 1)
        self.assertTrue(p2['approvals_needed'][0].startswith('VP Sales (E01)'))
        self.assertIn('diskon 20%', p2['approvals_needed'][0])


class RankingInputValidationTests(unittest.TestCase):
    def assertRejects(self, ctxs, diags, fragment):
        with self.assertRaises(ValueError) as cm:
            rank_deals(ctxs, diags)
        self.assertIn(fragment, str(cm.exception))

    def test_rejects_invalid_inputs(self):
        ctxs, diags = real_inputs()
        self.assertRejects([], [], 'kosong')
        self.assertRejects('x', diags, 'harus list')
        self.assertRejects(ctxs + [ctxs[0]], diags, 'duplikat pada contexts')
        self.assertRejects(ctxs, diags + [diags[0]], 'duplikat pada diagnostics')
        self.assertRejects(ctxs[:4], diags, 'Set deal berbeda')
        bad = json.loads(json.dumps(diags))
        bad[0]['snapshot_date'] = '2026-09-01'
        self.assertRejects(ctxs, bad, 'Snapshot')
        bad = json.loads(json.dumps(diags))
        bad[1]['account_id'] = 'P99'
        self.assertRejects(ctxs, bad, 'account_id diagnostic')
        bad = json.loads(json.dumps(diags))
        bad[1]['evidence'][0]['excerpt'] = '{"diubah": true}'
        self.assertRejects(ctxs, bad, 'isi berbeda')
        bad = json.loads(json.dumps(diags))
        del bad[2]['deal_id']
        self.assertRejects(ctxs, bad, 'tanpa deal_id')


class RankingCaseTests(unittest.TestCase):
    def test_all_ranking_cases(self):
        self.assertGreaterEqual(len(RANKING_CASES), 10)
        for case in RANKING_CASES:
            with self.subTest(case=case.id):
                res, ctxs, diags = case.run()
                failed = [n for n, fn in case.checks.items() if not fn(res, ctxs, diags)]
                self.assertEqual(failed, [], case.description)


if __name__ == '__main__':
    unittest.main()
