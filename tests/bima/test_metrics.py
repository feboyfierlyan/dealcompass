from datetime import date, datetime
from pathlib import Path
import tempfile
import unittest

from backend.ingestion.dataset import get_dataset, load_dataset
from backend.ingestion.metrics import summarize_deal
from tests.bima.test_ingestion import make_dataset


def interaction(source_id, when='2026-09-30', kind='email', account='P01'):
    return {
        'interaction_id': source_id, 'tanggal': when, 'tipe': kind,
        'account_id': account, 'dari': 'sales@kasirnusa.id',
        'ke': 'buyer@example.com', 'peserta': '', 'subjek': 'Follow-up',
        'isi': 'Recorded contact, not a confirmed reply.', 'membalas_id': '',
    }


def ids(*source_ids):
    return ['interactions.jsonl:' + source_id for source_id in source_ids]


class RealMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = get_dataset()

    def test_all_five_prospects_have_actual_ages_and_exact_source_sets(self):
        expected = [
            ('DL-001', 'P01', '2026-08-01', '2026-09-11', 61, 20,
             ('I0279', 'I0310', 'I0325', 'I0343'), '2026-09-24', ('I0343',), (), None),
            ('DL-002', 'P02', '2026-07-25', '2026-08-17', 68, 45,
             ('I0269', 'I0296', 'I0322'), '2026-09-05', ('I0322',), ('I0348',), '2026-09-28'),
            ('DL-003', 'P03', '2026-09-15', '2026-09-21', 16, 10,
             ('I0334',), '2026-09-21', ('I0334',), (), None),
            ('DL-004', 'P04', '2026-08-05', '2026-09-01', 57, 30,
             ('I0284', 'I0314', 'I0335'), '2026-09-22', ('I0335',), (), None),
            ('DL-005', 'P05', '2026-09-26', '2026-09-26', 5, 5,
             (), None, (), (), None),
        ]
        for (deal, account, created, stage, age, stage_age, external,
             last_external, last_ids, internal, last_internal) in expected:
            with self.subTest(deal=deal):
                result = summarize_deal(deal, dataset=self.dataset)
                self.assertEqual(result['deal_id'], deal)
                self.assertEqual(result['account_id'], account)
                self.assertEqual(result['snapshot_date'], '2026-10-01')
                self.assertEqual(result['created_date'], created)
                self.assertEqual(result['stage_since'], stage)
                self.assertEqual(result['deal_age_days'], age)
                self.assertEqual(result['stage_age_days'], stage_age)
                self.assertEqual(result['age_evidence_ids'], ['crm_deals.csv:' + deal])
                latest = max((when for when in (last_external, last_internal) if when), default=None)
                latest_ids = (*last_ids,) if latest == last_external else (*internal,)
                self.assertEqual(result['interactions'], {
                    'total_count': len(external) + len(internal),
                    'last_date': latest, 'last_evidence_ids': ids(*latest_ids),
                    'customer': {'count': len(external), 'last_date': last_external,
                                 'last_evidence_ids': ids(*last_ids), 'evidence_ids': ids(*external)},
                    'internal': {'count': len(internal), 'last_date': last_internal,
                                 'last_evidence_ids': ids(*internal), 'evidence_ids': ids(*internal)},
                    'unclassified': {'count': 0, 'last_date': None,
                                     'last_evidence_ids': [], 'evidence_ids': []},
                    'undated_evidence_ids': [],
                })
                self.assertEqual(result['query_scope'], {
                    'source_file': 'dataset_kasirnusa/interactions.jsonl',
                    'account_id': account, 'since': created, 'through': '2026-10-01',
                })
                self.assertEqual(result['unknowns'], [])

    def test_closed_customer_deals_and_unknown_ids_are_rejected(self):
        for deal in ('DL-006', 'DL-008', 'DL-999'):
            with self.subTest(deal=deal), self.assertRaises(KeyError):
                summarize_deal(deal, dataset=self.dataset)


class IsolatedMetricsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        self.deal = {
            'deal_id': 'DL-001', 'account_id': 'P01', 'tipe': 'baru',
            'stage': 'Proposal', 'stage_sejak': '2026-09-11', 'dibuat': '2026-08-01',
            'owner_id': 'E06', 'outlet': '60', 'nilai_tahunan': '252000000',
            'status': 'Terbuka', 'alasan_kalah': '', 'kompetitor': '',
        }

    def dataset(self, interactions=(), **deal_changes):
        make_dataset(self.path, rows={
            'crm_accounts.csv': [{'account_id': 'P01', 'tipe': 'prospek'}],
            'crm_deals.csv': [{**self.deal, **deal_changes}],
        }, interactions=interactions)
        return load_dataset(self.path)

    def test_account_creation_and_snapshot_bounds_are_inclusive(self):
        dataset = self.dataset([
            interaction('I-FUTURE', '2026-10-02'),
            interaction('I-OTHER', '2026-10-01', account='C01'),
            interaction('I-OTHER-PROSPECT', '2026-10-01', account='P02'),
            interaction('I-BEFORE', '2026-07-31'),
            interaction('I-START', '2026-08-01'),
            interaction('I-SNAPSHOT', '2026-10-01'),
        ])
        result = summarize_deal('DL-001', dataset=dataset)
        self.assertEqual(result['interactions']['total_count'], 2)
        self.assertEqual(result['interactions']['customer']['evidence_ids'], ids('I-SNAPSHOT', 'I-START'))
        self.assertEqual(result['interactions']['customer']['last_date'], '2026-10-01')
        self.assertEqual(result['interactions']['customer']['last_evidence_ids'], ids('I-SNAPSHOT'))
        self.assertEqual(result['unknowns'], [])

    def test_same_date_ties_and_all_source_ids_are_sorted_in_every_group(self):
        rows = [interaction('I-Z'), interaction('I-A'), interaction('I-OLDER', '2026-09-29'),
                interaction('I-IZ', kind='email_internal'), interaction('I-IA', kind='email_internal'),
                interaction('I-UZ', kind='phone'), interaction('I-UA', kind='phone')]
        dataset = self.dataset(rows)
        result = summarize_deal('DL-001', dataset=dataset)
        groups = result['interactions']
        self.assertEqual(groups['total_count'], 7)
        self.assertEqual(groups['last_date'], '2026-09-30')
        self.assertEqual(groups['last_evidence_ids'], ids('I-A', 'I-IA', 'I-IZ', 'I-UA', 'I-UZ', 'I-Z'))
        for group, sources, last_sources in (
            ('customer', ('I-A', 'I-OLDER', 'I-Z'), ('I-A', 'I-Z')),
            ('internal', ('I-IA', 'I-IZ'), ('I-IA', 'I-IZ')),
            ('unclassified', ('I-UA', 'I-UZ'), ('I-UA', 'I-UZ')),
        ):
            self.assertEqual(groups[group], {
                'count': len(sources), 'last_date': '2026-09-30',
                'last_evidence_ids': ids(*last_sources), 'evidence_ids': ids(*sources),
            })
        dataset.tables['interactions.jsonl'].reverse()
        self.assertEqual(summarize_deal('DL-001', dataset=dataset), result)

    def test_missing_dates_are_not_counted_and_missing_types_are_not_customer(self):
        dataset = self.dataset([
            interaction('I-NO-DATE', when=''),
            interaction('I-INTERNAL-NO-DATE', when='', kind='email_internal'),
            interaction('I-NO-TYPE', kind=''),
            interaction('I-NEW-TYPE', kind='call'),
            interaction('I-OTHER-NO-DATE', when='', account='C01'),
        ])
        result = summarize_deal('DL-001', dataset=dataset)
        groups = result['interactions']
        self.assertEqual(groups['total_count'], 2)
        self.assertEqual(groups['customer']['count'], 0)
        self.assertIsNone(groups['customer']['last_date'])
        self.assertEqual(groups['internal']['count'], 0)
        self.assertEqual(groups['unclassified']['evidence_ids'], ids('I-NEW-TYPE', 'I-NO-TYPE'))
        self.assertEqual(groups['undated_evidence_ids'], ids('I-INTERNAL-NO-DATE', 'I-NO-DATE'))
        self.assertEqual(len(result['unknowns']), 4)
        for source_id in ('I-INTERNAL-NO-DATE', 'I-NO-DATE', 'I-NEW-TYPE', 'I-NO-TYPE'):
            self.assertTrue(any('interactions.jsonl:' + source_id + ':' in item for item in result['unknowns']))

    def test_invalid_typed_event_date_stays_unknown_not_an_event(self):
        dataset = self.dataset([interaction('I-BAD')])
        dataset.by_id['interactions.jsonl']['I-BAD'].values['tanggal'] = 'not-a-date'
        result = summarize_deal('DL-001', dataset=dataset)
        self.assertEqual(result['interactions']['total_count'], 0)
        self.assertEqual(result['interactions']['undated_evidence_ids'], ids('I-BAD'))
        self.assertTrue(any('interactions.jsonl:I-BAD' in item for item in result['unknowns']))

    def test_same_day_creation_and_stage_have_zero_elapsed_days(self):
        dataset = self.dataset([interaction('I-TODAY', '2026-10-01')],
                               dibuat='2026-10-01', stage_sejak='2026-10-01')
        result = summarize_deal('DL-001', dataset=dataset)
        self.assertEqual(result['deal_age_days'], 0)
        self.assertEqual(result['stage_age_days'], 0)
        self.assertEqual(result['interactions']['total_count'], 1)
        self.assertEqual(result['unknowns'], [])

    def test_missing_creation_keeps_account_scope_and_known_stage_age(self):
        dataset = self.dataset([interaction('I-HISTORICAL', '2025-01-01'),
                                interaction('I-FUTURE', '2026-10-02')], dibuat='')
        result = summarize_deal('DL-001', dataset=dataset)
        self.assertIsNone(result['created_date'])
        self.assertIsNone(result['deal_age_days'])
        self.assertEqual(result['stage_age_days'], 20)
        self.assertIsNone(result['query_scope']['since'])
        self.assertEqual(result['interactions']['customer']['evidence_ids'], ids('I-HISTORICAL'))
        self.assertTrue(any('crm_deals.csv:DL-001' in item for item in result['unknowns']))

    def test_missing_stage_is_null_not_zero(self):
        result = summarize_deal('DL-001', dataset=self.dataset(stage_sejak=''))
        self.assertEqual(result['deal_age_days'], 61)
        self.assertIsNone(result['stage_since'])
        self.assertIsNone(result['stage_age_days'])
        self.assertTrue(any('crm_deals.csv:DL-001' in item for item in result['unknowns']))

    def test_future_or_inverted_age_dates_never_produce_negative_ages(self):
        for changes, expected_ages in (
            ({'dibuat': '2026-10-02', 'stage_sejak': '2026-10-03'}, (None, None)),
            ({'stage_sejak': '2026-10-02'}, (61, None)),
            ({'stage_sejak': '2026-07-31'}, (61, None)),
        ):
            with self.subTest(changes=changes):
                dataset = self.dataset([interaction('I-EVENT')], **changes)
                result = summarize_deal('DL-001', dataset=dataset)
                self.assertEqual((result['deal_age_days'], result['stage_age_days']), expected_ages)
                self.assertTrue(any('crm_deals.csv:DL-001' in item for item in result['unknowns']))
                self.assertEqual(result['created_date'], changes.get('dibuat', '2026-08-01'))
                self.assertEqual(result['stage_since'], changes['stage_sejak'])
                if 'dibuat' in changes:
                    self.assertEqual(result['interactions']['total_count'], 0)

    def test_invalid_typed_age_values_remain_explicit_nulls(self):
        for invalid in ('bad-date', '2026-08-01', 5, datetime(2026, 8, 1)):
            with self.subTest(invalid=invalid):
                dataset = self.dataset()
                record = dataset.by_id['crm_deals.csv']['DL-001']
                record.values['dibuat'] = invalid
                record.values['stage_sejak'] = invalid
                result = summarize_deal('DL-001', dataset=dataset)
                for field in ('created_date', 'stage_since', 'deal_age_days', 'stage_age_days'):
                    self.assertIsNone(result[field])
                self.assertEqual(record.raw['dibuat'], '2026-08-01')

    def test_only_open_prospects_and_fixed_snapshot_are_supported(self):
        for status in ('Menang', 'Kalah', ''):
            with self.subTest(status=status), self.assertRaises(KeyError):
                summarize_deal('DL-001', dataset=self.dataset(status=status))
        dataset = self.dataset()
        dataset.by_id['crm_accounts.csv']['P01'].values['tipe'] = 'pelanggan'
        with self.assertRaises(KeyError):
            summarize_deal('DL-001', dataset=dataset)
        dataset = self.dataset()
        for snapshot in ('2026-09-30', '2026-10-02', '', date(2026, 10, 1)):
            with self.subTest(snapshot=snapshot), self.assertRaises(ValueError):
                summarize_deal('DL-001', snapshot, dataset=dataset)



if __name__ == '__main__':
    unittest.main()
