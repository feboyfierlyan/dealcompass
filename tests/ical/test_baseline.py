"""ICAL-04: pembanding CRM-only vs graph+rules. Data nyata; tidak ada Jev/mock/live."""
import unittest

from backend.contracts import DealSummary
from backend.ingestion.deals import list_deals
from evaluation.baseline_crm import BASELINES, GENERIC_ACTION, rank_crm, run, to_markdown


def row(deal_id, stage, value, age):
    return DealSummary(deal_id=deal_id, account_id='X' + deal_id[-2:], account_name='n', stage=stage,
                       stage_age_days=age, annual_value=value, owner_id='E00')


class BaselineUnitTests(unittest.TestCase):
    def test_stage_then_value_with_deterministic_tie(self):
        rows = [row('DL-9', 'Demo', 10, 1), row('DL-8', 'Demo', 10, 9), row('DL-7', 'Demo', 50, 2),
                row('DL-6', 'Negosiasi', 1, 3)]
        self.assertEqual([x['deal_id'] for x in rank_crm(rows)], ['DL-6', 'DL-7', 'DL-8', 'DL-9'])
        self.assertEqual([x['deal_id'] for x in rank_crm(rows, 'value_only')], ['DL-7', 'DL-8', 'DL-9', 'DL-6'])
        self.assertEqual([x['deal_id'] for x in rank_crm(rows, 'stage_age')], ['DL-8', 'DL-6', 'DL-7', 'DL-9'])

    def test_baseline_only_sees_crm_rows(self):
        for item in rank_crm(list_deals()):
            self.assertTrue(all(e.split(':')[0] in ('crm_deals.csv', 'crm_accounts.csv') for e in item['evidence_ids']))
            self.assertIsNone(item['approval_visible'])
            self.assertIsNone(item['obstacle_visible'])
            self.assertEqual(item['action'], GENERIC_ACTION[item['stage']])


class BaselineRealComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = run()
        cls.deals = {d['deal_id']: d for d in cls.res['deals']}

    def test_same_five_canonical_deals(self):
        ids = sorted(r.deal_id for r in list_deals())
        self.assertEqual(sorted(self.deals), ids)
        for b in BASELINES:
            self.assertEqual(sorted(self.res['baselines'][b]['order']), ids)

    def test_same_order_flag_is_computed_not_claimed(self):
        for b in self.res['baselines'].values():
            self.assertEqual(b['same_order_as_graph_rules'], b['order'] == self.res['graph_rules_order'])
        changed = [d for d, x in self.deals.items() if x['rank_changed']]
        self.assertEqual(changed, self.res['summary']['rank_changed_vs_stage_value'])

    def test_stage_age_baseline_puts_oldest_first(self):
        oldest = max(list_deals(), key=lambda r: (r.stage_age_days, r.deal_id)).deal_id
        self.assertEqual(self.res['baselines']['stage_age']['order'][0], oldest)

    def test_approval_gate_only_visible_with_graph_rules(self):
        gated = [d for d, x in self.deals.items() if x['graph_rules']['approvals_needed']]
        self.assertEqual(gated, ['DL-002'])
        self.assertEqual(self.res['summary']['approval_gates_visible_crm'], 0)
        self.assertIn('interactions.jsonl:I0348', self.deals['DL-002']['graph_rules']['gate_evidence_ids'])

    def test_extra_sources_and_discovery(self):
        for did, d in self.deals.items():
            g = d['graph_rules']
            self.assertGreaterEqual(g['evidence_count'], d['crm']['evidence_count'])
            if g['priority_kind'] == 'acceleration':
                self.assertIn('interactions.jsonl', d['additional_source_files'])
                self.assertTrue(g['obstacle_evidence_ids'])
            else:
                self.assertEqual(g['analysis_status'], 'insufficient_evidence')
                self.assertIsNone(g['score'])

    def test_markdown_reports_limits(self):
        md = to_markdown(self.res)
        self.assertIn('bukan bukti salah satu metode lebih akurat', md)
        self.assertIn('Sengaja tidak dipakai baseline', md)


if __name__ == '__main__':
    unittest.main()
