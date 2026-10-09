"""ICAL-04: laporan evaluasi memisahkan dataset asli, sintetis, mock dan replay."""
import unittest

from evaluation.cases import CASES
from evaluation.ranking_cases import RANKING_CASES
from evaluation.run_eval import SOURCE_LABEL, decision_source, ranking_source


class EvalSourceTests(unittest.TestCase):
    def test_every_decision_case_has_one_known_source(self):
        sources = {c.id: decision_source(c) for c in CASES}
        self.assertTrue(set(sources.values()) <= set(SOURCE_LABEL))
        self.assertEqual(sources['E01'], 'dataset_asli')
        self.assertEqual(sources['E15'], 'sintetis')
        self.assertEqual(sources['E22'], 'mock_jev')
        self.assertEqual(sources['E25'], 'replay_mock')
        for c in CASES:
            if 'nyata' in c.category:
                self.assertEqual(sources[c.id], 'dataset_asli' if 'sintetis' not in c.category else 'sintetis')

    def test_ranking_mutations_are_not_counted_as_real(self):
        sources = {c.id: ranking_source(c) for c in RANKING_CASES}
        self.assertEqual(sources['K01'], 'dataset_asli')
        for cid in ('K03', 'K04', 'K05', 'K12'):
            self.assertEqual(sources[cid], 'sintetis')


if __name__ == '__main__':
    unittest.main()
