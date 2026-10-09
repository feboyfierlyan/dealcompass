"""Consumer checks for the initial report, using the canonical real context."""
from dataclasses import replace
import unittest

from backend.graph.analysis import analyze_deal_initial, analyze_pipeline_initial
from backend.graph.context import build_deal_context
from backend.ingestion.dataset import SourceRecord, get_dataset, normalize_row


class InitialAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = get_dataset()
        cls.pipeline = analyze_pipeline_initial()
        cls.reports = {report['account_id']: report for report in cls.pipeline['deals']}

    def test_every_finding_has_fact_inference_missing_and_resolvable_sources(self):
        self.assertEqual(set(self.reports), {'P01', 'P02', 'P03', 'P04', 'P05'})
        for report in self.reports.values():
            sources = {e['id']: e for e in report['evidence']}
            for finding in report['findings'] + report['reference_candidates']:
                with self.subTest(finding=finding['finding_id']):
                    self.assertEqual(finding['interpretation_type'], 'inferred')
                    self.assertIn(finding['category'], ('business_anomaly', 'data_gap'))
                    for field in ('fact', 'interpretation', 'missing_information', 'follow_up_implication'):
                        self.assertIn(field, finding)
                    for eid in finding['evidence_ids']:
                        self.assertIn(eid, sources)
                        filename, key = eid.split(':', 1)
                        record = self.dataset.by_id[filename][key]
                        self.assertEqual(sources[eid]['source_file'], record.source_file)
                        self.assertEqual(sources[eid]['source_id'], key)

    def test_p01_authority_is_cross_source_inference_not_highest_title(self):
        findings = [f for f in self.reports['P01']['findings']
                    if 'interactions.jsonl:I0343' in f['evidence_ids']]
        self.assertEqual(len(findings), 1)
        evidence = set(findings[0]['evidence_ids'])
        self.assertIn('crm_contacts.csv:K017', evidence)
        self.assertIn('contact_employment_history.csv:K017|Grup Ritel Mandala|2026-09-01', evidence)
        self.assertNotIn('crm_contacts.csv:K089', evidence)
        self.assertEqual(findings[0]['interpretation_type'], 'inferred')

    def test_p02_price_and_internal_request_are_distinct_and_request_is_not_approval(self):
        report = self.reports['P02']
        price = [f for f in report['findings'] if f['finding_id'].startswith('price_objection:')]
        requests = [f for f in report['findings'] if f['finding_id'].startswith('discount_request:')]
        self.assertEqual(len(price), 1)
        self.assertIn('interactions.jsonl:I0296', price[0]['evidence_ids'])
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['requested_discount_pct'], '20')
        self.assertIn('interactions.jsonl:I0348', requests[0]['evidence_ids'])
        self.assertIn('employees.csv:E01', requests[0]['evidence_ids'])
        self.assertEqual(requests[0]['decision_lookup']['account_id'], 'P02')
        self.assertEqual(requests[0]['decision_lookup']['deal_id'], 'DL-002')
        self.assertEqual(requests[0]['decision_lookup']['focus_log_evidence_ids'], [])
        self.assertEqual(report['metrics']['interactions']['customer']['last_evidence_ids'],
                         ['interactions.jsonl:I0322'])
        self.assertEqual(report['metrics']['interactions']['internal']['last_evidence_ids'],
                         ['interactions.jsonl:I0348'])

    def test_reference_requirements_and_candidates_are_supported_but_not_approvals(self):
        expected = {'P03': ('I0334', {'C03', 'C09', 'C17', 'C27'}), 'P04': ('I0335', {'C06'})}
        for account, (iid, candidates) in expected.items():
            report = self.reports[account]
            requirements = [f for f in report['findings'] if f['finding_id'].startswith('reference_requirement:')]
            self.assertEqual(len(requirements), 1)
            self.assertIn('interactions.jsonl:' + iid, requirements[0]['evidence_ids'])
            self.assertEqual({f['account_id'] for f in report['reference_candidates']}, candidates)
            for candidate in report['reference_candidates']:
                self.assertEqual(candidate['interpretation_type'], 'inferred')
                self.assertNotIn('approved', candidate)
                self.assertNotIn('confidence', candidate)

    def test_p05_no_interactions_is_data_gap_and_latest_date_stays_null(self):
        report = self.reports['P05']
        self.assertEqual(report['metrics']['deal_age_days'], 5)
        self.assertEqual(report['metrics']['interactions']['total_count'], 0)
        self.assertIsNone(report['metrics']['interactions']['customer']['last_date'])
        gap = [f for f in report['findings'] if f['finding_id'].startswith('customer_information_gap:')]
        self.assertEqual(len(gap), 1)
        self.assertEqual(gap[0]['category'], 'data_gap')
        self.assertEqual(gap[0]['search_scope']['account_id'], 'P05')
        self.assertEqual(gap[0]['search_scope']['since'], '2026-09-26')
        self.assertEqual(set(gap[0]['evidence_ids']), {'crm_deals.csv:DL-005', 'crm_accounts.csv:P05'})

    def test_statistical_outliers_are_not_inferred_from_longest_deal(self):
        assessment = self.pipeline['statistical_assessment']
        self.assertEqual(assessment['sample_size'], 5)
        self.assertEqual(assessment['stage_cohort_counts'],
                         {'Proposal': 1, 'Demo': 1, 'Discovery': 1, 'Negosiasi': 1, 'Lead': 1})
        self.assertEqual(assessment['status'], 'not_assessed')
        self.assertIsNone(assessment['method'])
        self.assertIsNone(assessment['threshold'])
        self.assertIsNone(assessment['outlier_deal_ids'])
        self.assertEqual(self.reports['P02']['metrics']['deal_age_days'], 68)

    def test_newer_reference_account_message_does_not_change_focus_diagnosis(self):
        context = build_deal_context('DL-002')
        raw = dict(self.dataset.by_id['interactions.jsonl']['I0348'].raw,
                   interaction_id='I-REFERENCE', account_id='C01', tanggal='2026-09-30',
                   isi='Saya usul diskon 99%. Mohon keputusan. Referensi belum ada.')
        row = SourceRecord('dataset_kasirnusa/interactions.jsonl', 'I-REFERENCE', 351,
                           raw, normalize_row(raw))
        dataset = replace(self.dataset,
            tables={**self.dataset.tables, 'interactions.jsonl': self.dataset.tables['interactions.jsonl'] + [row]},
            by_id={**self.dataset.by_id, 'interactions.jsonl': {**self.dataset.by_id['interactions.jsonl'], 'I-REFERENCE': row}})
        changed = analyze_deal_initial(context, dataset=dataset)
        self.assertEqual(changed['metrics'], self.reports['P02']['metrics'])
        self.assertEqual(changed['findings'], self.reports['P02']['findings'])
        self.assertNotIn('interactions.jsonl:I-REFERENCE', {e['id'] for e in changed['evidence']})

    def test_subject_is_metadata_not_a_second_message(self):
        context = build_deal_context('DL-002')
        original = self.dataset.by_id['interactions.jsonl']['I0348']
        raw = dict(original.raw, isi='Mohon kabar jadwal pertemuan.',
                   subjek='Saya usul diskon 88%. Mohon keputusan.')
        row = replace(original, raw=raw, values=normalize_row(raw))
        dataset = replace(self.dataset,
            tables={**self.dataset.tables, 'interactions.jsonl': [row if r.source_id == row.source_id else r
                                                              for r in self.dataset.tables['interactions.jsonl']]},
            by_id={**self.dataset.by_id, 'interactions.jsonl': {**self.dataset.by_id['interactions.jsonl'], row.source_id: row}})
        report = analyze_deal_initial(context, dataset=dataset)
        self.assertEqual([f for f in report['findings'] if f['finding_id'].startswith('discount_request:')], [])

    def test_other_snapshot_is_explicitly_rejected(self):
        with self.assertRaises(ValueError):
            analyze_pipeline_initial('2026-10-09')
