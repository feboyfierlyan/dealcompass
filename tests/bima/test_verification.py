from pathlib import Path
import tempfile
import unittest

from backend.graph.context import build_deal_context
from backend.graph.store import ContextGraph, get_context_graph
from backend.graph.verification import (
    reference_request_rows, verify_authority_paths, verify_reference_candidates,
)
from backend.ingestion.dataset import get_dataset, load_dataset
from tests.bima.test_ingestion import make_dataset


class FindingAssertions:
    def assert_findings(self, findings, dataset):
        for finding in findings:
            self.assertIn(finding['category'], ('business_anomaly', 'data_gap'))
            self.assertEqual(finding['interpretation_type'], 'inferred')
            for field in ('finding_id', 'fact', 'interpretation', 'missing_information', 'follow_up_implication'):
                self.assertIn(field, finding)
            top_level = set(finding['evidence_ids'])
            self.assertEqual(len(top_level), len(finding['evidence_ids']))
            self.assert_nested_evidence(finding, top_level)
            for identifier in top_level:
                filename, source_id = identifier.split(':', 1)
                self.assertIn(source_id, dataset.by_id[filename], identifier)

    def assert_nested_evidence(self, value, top_level):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == 'evidence_ids':
                    self.assertTrue(set(item) <= top_level, item)
                else:
                    self.assert_nested_evidence(item, top_level)
        elif isinstance(value, list):
            for item in value:
                self.assert_nested_evidence(item, top_level)


class RealVerificationTests(FindingAssertions, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = get_dataset()
        cls.graph = get_context_graph()

    def test_authority_uses_fajar_message_role_and_rina_active_history(self):
        context = build_deal_context('DL-001')
        findings = verify_authority_paths(context)
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding['interaction_id'], 'I0343')
        self.assertEqual(finding['authority_contact_id'], 'K017')
        self.assertEqual(finding['reported_roles'], ['GM Operations'])
        self.assertEqual(finding['reported_joining_month'], '2026-09')
        self.assertEqual(finding['candidate_contacts'][0]['name'], 'Rina Hapsari')
        self.assertEqual(finding['candidate_contacts'][0]['current_account_id'], 'P01')
        self.assertIn('interactions.jsonl:I0343', finding['evidence_ids'])
        self.assertIn('crm_contacts.csv:K017', finding['evidence_ids'])
        self.assertIn('contact_employment_history.csv:K017|Grup Ritel Mandala|2026-09-01', finding['evidence_ids'])
        self.assertIn('crm_contacts.csv:K052', finding['evidence_ids'])
        self.assertIn('contact_employment_history.csv:K052|Grup Ritel Mandala|2022-02-01', finding['evidence_ids'])
        self.assertEqual(finding['reporting_contacts'][0]['name'], 'Fajar Nugraha')
        self.assertNotEqual(finding['authority_contact_id'], 'K089')
        self.assertIn('saya hanya menilai sisi teknis', finding['fact'])
        self.assert_findings(findings, self.dataset)

    def test_historical_email_paths_keep_canonical_three_row_support_and_dates(self):
        context = build_deal_context('DL-001')
        finding = verify_authority_paths(context, dataset=self.dataset)[0]
        self.assertEqual({item['interaction_id'] for path in finding['historical_email_paths']
                          for item in path['interactions']},
                         {'I0051', 'I0066', 'I0159', 'I0223', 'I0224', 'I0290'})
        for path in finding['historical_email_paths']:
            self.assertEqual(path['relation'], 'possible_historical_email_identity')
            self.assertEqual(path['interpretation_type'], 'inferred')
            self.assertEqual(path['email_node'], 'email:rina.hapsari@kopilintas.co.id')
            self.assertEqual(path['valid_from'], '2021-03-01')
            self.assertEqual(path['valid_to'], '2026-08-15')
            self.assertEqual({item.split(':', 1)[0] for item in path['evidence_ids']},
                             {'interactions.jsonl', 'crm_contacts.csv', 'contact_employment_history.csv'})
        past = [history for history in finding['employment_history'] if history['account_id'] == 'C01']
        self.assertEqual(len(past), 1)
        self.assertEqual((past[0]['valid_from'], past[0]['valid_to']), ('2021-03-01', '2026-08-15'))
        self.assert_findings([finding], self.dataset)

    def test_apotek_candidates_group_relations_and_use_latest_real_usage(self):
        findings = verify_reference_candidates(build_deal_context('DL-003'))
        by_account = {finding['candidate_account_id']: finding for finding in findings}
        self.assertEqual(set(by_account), {'C03', 'C09', 'C17', 'C27'})
        self.assertEqual(len(findings), 4)
        for account_id, count in {'C03': 14, 'C09': 11, 'C17': 22, 'C27': 48}.items():
            finding = by_account[account_id]
            self.assertEqual(finding['account_id'], account_id)
            self.assertEqual(finding['focus_account_id'], 'P03')
            self.assertEqual({item['relation'] for item in finding['relationships']},
                             {'related_account_shared_industry', 'related_account_feature_usage'})
            self.assertEqual(finding['reference_requests'][0]['interaction_id'], 'I0334')
            self.assertEqual(finding['feature_usage'], [{
                'feature_id': 'FEAT-05', 'month': '2026-09', 'active_users': count,
                'observation_status': 'recorded',
                'evidence_ids': [f'feature_usage_monthly.csv:2026-09|{account_id}|FEAT-05'],
            }])
            self.assertIn('interactions.jsonl:I0334', finding['evidence_ids'])
            self.assertIn(f'crm_accounts.csv:{account_id}', finding['evidence_ids'])
            self.assertIsNone(finding['suitability'])
            self.assertIsNone(finding['reference_willingness'])
            self.assertIsNone(finding['contact_consent'])
        self.assert_findings(findings, self.dataset)

    def test_nirwana_overlap_computes_interval_and_current_contact_association(self):
        context = build_deal_context('DL-004')
        findings = verify_reference_candidates(context, dataset=self.dataset)
        self.assertEqual([item['candidate_account_id'] for item in findings], ['C06'])
        finding = findings[0]
        self.assertEqual(finding['account_id'], 'C06')
        self.assertEqual(finding['focus_account_id'], 'P04')
        self.assertIn('interactions.jsonl:I0335', finding['evidence_ids'])
        self.assertEqual(finding['account_comparison']['focus']['industry'], 'Hospitality')
        self.assertEqual(finding['account_comparison']['focus']['outlet_count'], 35)
        self.assertEqual(finding['account_comparison']['candidate']['name'], 'Saiyo Group')
        self.assertEqual(finding['account_comparison']['candidate']['industry'], 'Resto Padang')
        self.assertEqual(finding['account_comparison']['candidate']['outlet_count'], 30)
        self.assertEqual(len(finding['work_overlap_paths']), 1)
        path = finding['work_overlap_paths'][0]
        self.assertEqual(path['relation'], 'overlapping_employment')
        self.assertEqual(path['organization'], 'PT Sentosa Abadi Group')
        self.assertEqual((path['valid_from'], path['valid_to']), ('2015-02-01', '2019-11-30'))
        self.assertEqual((path['focus_contact']['contact_id'], path['focus_contact']['name']), ('K028', 'Hartono Gunawan'))
        self.assertEqual((path['candidate_contact']['contact_id'], path['candidate_contact']['name']), ('K116', 'Budi Santoso'))
        self.assertEqual(path['candidate_contact']['role'], 'CFO')
        self.assertEqual(path['candidate_contact']['current_account_id'], 'C06')
        self.assertEqual(path['current_candidate_employments'][0]['valid_from'], '2020-01-02')
        self.assertIsNone(path['acquaintance_confirmed'])
        self.assertIn('contact_employment_history.csv:K028|PT Sentosa Abadi Group|2015-01-01', path['evidence_ids'])
        self.assertIn('contact_employment_history.csv:K116|PT Sentosa Abadi Group|2015-02-01', path['evidence_ids'])
        self.assertIn('contact_employment_history.csv:K116|Saiyo Group|2020-01-02', path['evidence_ids'])
        self.assert_findings(findings, self.dataset)

    def test_other_focus_deals_have_no_fabricated_authority_or_reference_requests(self):
        for deal_id in ('DL-002', 'DL-003', 'DL-004', 'DL-005'):
            with self.subTest(deal_id=deal_id):
                self.assertEqual(verify_authority_paths(build_deal_context(deal_id)), [])
        for deal_id in ('DL-001', 'DL-002', 'DL-005'):
            with self.subTest(deal_id=deal_id):
                self.assertEqual(verify_reference_candidates(build_deal_context(deal_id)), [])


class FixtureVerificationTests(FindingAssertions, unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def authority_fixture(self, *, principal_role='Head of Procurement', histories=True,
                          start='2026-09-01', end='', duplicate=False, message=None,
                          subject='Proposal', sender='tech@focus.test', kind='email',
                          interaction_date='2026-09-24'):
        rows = {
            'crm_accounts.csv': [
                {'account_id': 'P07', 'nama': 'Focus', 'tipe': 'prospek', 'industri': 'Retail', 'jumlah_outlet': '12', 'account_owner_id': 'E07'},
                {'account_id': 'C07', 'nama': 'Former Employer', 'tipe': 'pelanggan', 'industri': 'Other'},
            ],
            'crm_deals.csv': [{'deal_id': 'DL-077', 'account_id': 'P07', 'tipe': 'baru', 'stage': 'Proposal',
                               'stage_sejak': '2026-09-01', 'dibuat': '2026-08-01', 'owner_id': 'E07',
                               'outlet': '12', 'nilai_tahunan': '1000000', 'status': 'Terbuka'}],
            'employees.csv': [{'employee_id': 'E07', 'nama': 'Seller', 'email': 'seller@sales.test', 'jabatan': 'Sales'}],
            'crm_contacts.csv': [
                {'contact_id': 'K201', 'nama': 'Buyer Candidate', 'email': 'buyer@focus.test', 'account_id_saat_ini': 'P07', 'jabatan_saat_ini': principal_role},
                {'contact_id': 'K202', 'nama': 'Highest Title', 'email': 'ceo@focus.test', 'account_id_saat_ini': 'P07', 'jabatan_saat_ini': 'CEO'},
                {'contact_id': 'K203', 'nama': 'Technical Evaluator', 'email': 'tech@focus.test', 'account_id_saat_ini': 'P07', 'jabatan_saat_ini': 'IT Manager'},
            ],
            'contact_employment_history.csv': [
                {'contact_id': 'K201', 'account_id': 'C07', 'organisasi': 'Former Employer', 'jabatan': 'Operations', 'mulai': '2019-01-01', 'selesai': '2026-08-15'},
                {'contact_id': 'K202', 'account_id': 'P07', 'organisasi': 'Focus', 'jabatan': 'CEO', 'mulai': '2020-01-01'},
                {'contact_id': 'K203', 'account_id': 'P07', 'organisasi': 'Focus', 'jabatan': 'IT Manager', 'mulai': '2020-01-01'},
            ],
        }
        if histories:
            rows['contact_employment_history.csv'].append(
                {'contact_id': 'K201', 'account_id': 'P07', 'organisasi': 'Focus', 'jabatan': principal_role, 'mulai': start, 'selesai': end})
        if duplicate:
            rows['crm_contacts.csv'].append({'contact_id': 'K204', 'nama': 'Second Candidate', 'email': 'buyer2@focus.test',
                                              'account_id_saat_ini': 'P07', 'jabatan_saat_ini': principal_role})
            rows['contact_employment_history.csv'].append({'contact_id': 'K204', 'account_id': 'P07', 'organisasi': 'Focus',
                                                           'jabatan': principal_role, 'mulai': start, 'selesai': end})
        if message is None:
            message = ('Proposal saya teruskan ke Head of Procurement yang baru bergabung awal September. '
                       'Keputusan pengadaan ada di beliau, saya hanya menilai teknis.')
        interactions = [
            {'interaction_id': 'I7001', 'tanggal': interaction_date, 'tipe': kind, 'account_id': 'P07', 'dari': sender,
             'ke': 'seller@sales.test', 'peserta': 'K203;E07', 'subjek': subject, 'isi': message, 'membalas_id': ''},
            {'interaction_id': 'I7002', 'tanggal': '2026-08-14', 'tipe': 'email', 'account_id': 'C07',
             'dari': 'buyer@former.test', 'ke': 'seller@sales.test', 'peserta': '', 'subjek': 'Historic',
             'isi': 'Keputusan pengadaan ada di CEO. Kami meminta referensi.', 'membalas_id': ''},
        ]
        make_dataset(self.directory, rows, interactions)
        dataset = load_dataset(self.directory)
        return dataset, ContextGraph(dataset).deal_context('DL-077')

    def reference_fixture(self, *, active='0', include_latest=True, include_historical=True,
                          include_future=True, message=None, subject='Discovery'):
        rows = {
            'crm_accounts.csv': [
                {'account_id': 'P08', 'nama': 'Clinic', 'tipe': 'prospek', 'industri': 'Apotek', 'jumlah_outlet': '9', 'account_owner_id': 'E08'},
                {'account_id': 'C08', 'nama': 'Pharmacy', 'tipe': 'pelanggan', 'industri': 'Apotek', 'jumlah_outlet': '18'},
                {'account_id': 'C09', 'nama': 'Unrelated', 'tipe': 'pelanggan', 'industri': 'Other'},
            ],
            'crm_deals.csv': [{'deal_id': 'DL-088', 'account_id': 'P08', 'tipe': 'baru', 'stage': 'Discovery',
                               'stage_sejak': '2026-09-21', 'dibuat': '2026-09-15', 'owner_id': 'E08',
                               'outlet': '9', 'nilai_tahunan': '1000000', 'status': 'Terbuka'}],
            'employees.csv': [{'employee_id': 'E08', 'nama': 'Seller', 'email': 'seller@sales.test', 'jabatan': 'Sales'}],
            'crm_contacts.csv': [
                {'contact_id': 'K207', 'nama': 'Prospect', 'email': 'prospect@clinic.test', 'account_id_saat_ini': 'P08', 'jabatan_saat_ini': 'Purchasing'},
                {'contact_id': 'K208', 'nama': 'Customer', 'email': 'customer@pharmacy.test', 'account_id_saat_ini': 'C08', 'jabatan_saat_ini': 'Manager'},
            ],
            'contact_employment_history.csv': [
                {'contact_id': 'K207', 'account_id': 'P08', 'organisasi': 'Clinic', 'jabatan': 'Purchasing', 'mulai': '2020-01-01'},
                {'contact_id': 'K208', 'account_id': 'C08', 'organisasi': 'Pharmacy', 'jabatan': 'Manager', 'mulai': '2020-01-01'},
            ],
            'features.csv': [{'feature_id': 'FEAT-05', 'nama': 'Apotek', 'status': 'Aktif', 'target_terkini': 'Tersedia'}],
            'feature_usage_monthly.csv': [
                {'bulan': '2025-10', 'account_id': 'C08', 'feature_id': 'FEAT-05', 'pengguna_aktif': '10'},
                {'bulan': '2026-10', 'account_id': 'C08', 'feature_id': 'FEAT-05', 'pengguna_aktif': '99'},
            ],
        }
        rows['feature_usage_monthly.csv'] = [row for row in rows['feature_usage_monthly.csv']
                                           if (include_historical or row['bulan'] != '2025-10')
                                           and (include_future or row['bulan'] != '2026-10')]
        if include_latest:
            rows['feature_usage_monthly.csv'].append({'bulan': '2026-09', 'account_id': 'C08', 'feature_id': 'FEAT-05', 'pengguna_aktif': active})
        interactions = [
            {'interaction_id': 'I8001', 'tanggal': '2026-09-21', 'tipe': 'catatan_meeting', 'account_id': 'P08',
             'dari': 'seller@sales.test', 'ke': '', 'peserta': 'K207;E08', 'subjek': subject,
             'isi': message if message is not None else 'Butuh apotek; pelanggan meminta referensi pengguna apotek.', 'membalas_id': ''},
            {'interaction_id': 'I8002', 'tanggal': '2026-09-30', 'tipe': 'email', 'account_id': 'C08',
             'dari': 'customer@pharmacy.test', 'ke': 'seller@sales.test', 'peserta': '', 'subjek': 'Latest customer message',
             'isi': 'Kami minta referensi lain.', 'membalas_id': ''},
        ]
        make_dataset(self.directory, rows, interactions)
        dataset = load_dataset(self.directory)
        return dataset, ContextGraph(dataset).deal_context('DL-088')

    def test_changed_contact_and_account_ids_resolve_without_hardcoding(self):
        dataset, context = self.authority_fixture()
        findings = verify_authority_paths(context, dataset=dataset)
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding['account_id'], 'P07')
        self.assertEqual(finding['authority_contact_id'], 'K201')
        self.assertEqual(finding['reported_roles'], ['Head of Procurement'])
        self.assertEqual(finding['historical_email_paths'][0]['email_node'], 'email:buyer@former.test')
        self.assertEqual(finding['historical_email_paths'][0]['valid_to'], '2026-08-15')
        self.assertEqual(finding['interaction_id'], 'I7001')
        self.assertEqual(verify_reference_candidates(context, dataset=dataset), [])
        self.assert_findings([finding], dataset)

    def test_role_without_procurement_conversation_does_not_prove_authority(self):
        dataset, context = self.authority_fixture(message='Head of Procurement baru bergabung September. Demo berjalan baik.',
                                                   subject='Keputusan pengadaan ada di Head of Procurement')
        self.assertEqual(verify_authority_paths(context, dataset=dataset), [])

    def test_outbound_and_internal_claims_are_not_customer_authority_reports(self):
        for sender, kind in [('seller@sales.test', 'email'), ('tech@focus.test', 'email_internal')]:
            with self.subTest(sender=sender, kind=kind):
                dataset, context = self.authority_fixture(sender=sender, kind=kind)
                self.assertEqual(verify_authority_paths(context, dataset=dataset), [])

    def test_no_matching_role_or_history_remains_explicitly_unknown(self):
        for options in [{'principal_role': ''}, {'histories': False}, {'start': '2026-08-01'},
                        {'start': '2026-09-25'}, {'end': '2026-09-23'}]:
            with self.subTest(options=options):
                dataset, context = self.authority_fixture(**options)
                finding = verify_authority_paths(context, dataset=dataset)[0]
                self.assertIsNone(finding['authority_contact_id'])
                self.assertEqual(finding['candidate_contacts'], [])
                self.assertEqual(finding['category'], 'data_gap')
                self.assert_findings([finding], dataset)

    def test_multiple_active_role_matches_are_ambiguous(self):
        dataset, context = self.authority_fixture(duplicate=True)
        finding = verify_authority_paths(context, dataset=dataset)[0]
        self.assertIsNone(finding['authority_contact_id'])
        self.assertEqual({item['contact_id'] for item in finding['candidate_contacts']}, {'K201', 'K204'})
        self.assertEqual(finding['historical_email_paths'], [])
        self.assert_findings([finding], dataset)

    def test_employment_end_is_inclusive_and_joining_month_is_constrained(self):
        dataset, context = self.authority_fixture(end='2026-09-24')
        self.assertEqual(verify_authority_paths(context, dataset=dataset)[0]['authority_contact_id'], 'K201')
        dataset, context = self.authority_fixture(start='2026-08-01')
        self.assertIsNone(verify_authority_paths(context, dataset=dataset)[0]['authority_contact_id'])
        dataset, context = self.authority_fixture(start='2026-08-01', message='Keputusan pengadaan ada di Head of Procurement.')
        self.assertEqual(verify_authority_paths(context, dataset=dataset)[0]['authority_contact_id'], 'K201')

    def test_authority_role_is_target_not_an_unrelated_speakers_title(self):
        dataset, context = self.authority_fixture(
            message='CEO mengatakan keputusan pengadaan ada di Head of Procurement.')
        finding = verify_authority_paths(context, dataset=dataset)[0]
        self.assertEqual(finding['reported_roles'], ['Head of Procurement'])
        self.assertEqual(finding['authority_contact_id'], 'K201')

    def test_explicit_joining_year_is_not_replaced_by_interaction_year(self):
        dataset, context = self.authority_fixture(
            start='2025-09-01',
            message=('Proposal ke Head of Procurement yang bergabung September 2025. '
                     'Keputusan pengadaan ada di beliau.'))
        finding = verify_authority_paths(context, dataset=dataset)[0]
        self.assertEqual(finding['reported_joining_month'], '2025-09')
        self.assertEqual(finding['authority_contact_id'], 'K201')

    def test_missing_interaction_date_cannot_establish_active_authority(self):
        dataset, context = self.authority_fixture(interaction_date='')
        finding = verify_authority_paths(context, dataset=dataset)[0]
        self.assertIsNone(finding['interaction_date'])
        self.assertIsNone(finding['reported_joining_month'])
        self.assertIsNone(finding['authority_contact_id'])
        self.assert_findings([finding], dataset)

    def test_authority_messages_outside_deal_and_snapshot_dates_are_excluded(self):
        for when in ('2026-07-31', '2026-10-02'):
            with self.subTest(when=when):
                dataset, context = self.authority_fixture(interaction_date=when)
                self.assertEqual(verify_authority_paths(context, dataset=dataset), [])

    def test_negated_authority_does_not_select_a_contact(self):
        dataset, context = self.authority_fixture(message='Head of Procurement tidak memutuskan pengadaan.')
        self.assertEqual(verify_authority_paths(context, dataset=dataset), [])

    def test_canonical_employment_edges_are_required_for_identity_resolution(self):
        dataset, context = self.authority_fixture()
        context.graph.edges = [edge for edge in context.graph.edges
                               if not (edge.relation == 'employed_at' and edge.source == 'K201' and edge.target == 'P07')]
        finding = verify_authority_paths(context, dataset=dataset)[0]
        self.assertIsNone(finding['authority_contact_id'])
        self.assertEqual(finding['category'], 'data_gap')

    def test_latest_zero_is_not_replaced_by_old_positive_or_future_usage(self):
        dataset, context = self.reference_fixture(active='0')
        findings = verify_reference_candidates(context, dataset=dataset)
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding['candidate_account_id'], 'C08')
        self.assertEqual(finding['feature_usage'][0]['active_users'], 0)
        self.assertEqual(finding['feature_usage'][0]['month'], '2026-09')
        self.assertEqual(finding['feature_usage'][0]['observation_status'], 'recorded')
        self.assertIn('feature_usage_monthly.csv:2026-09|C08|FEAT-05', finding['evidence_ids'])
        self.assertNotIn('feature_usage_monthly.csv:2026-10|C08|FEAT-05', finding['evidence_ids'])
        self.assertEqual([item['interaction_id'] for item in finding['reference_requests']], ['I8001'])
        self.assertNotIn('interactions.jsonl:I8002', finding['evidence_ids'])
        self.assertIsNone(finding['suitability'])
        self.assert_findings(findings, dataset)

    def test_latest_blank_or_absent_is_unknown_not_old_positive(self):
        for options in [{'active': ''}, {'include_latest': False}]:
            with self.subTest(options=options):
                dataset, context = self.reference_fixture(**options)
                findings = verify_reference_candidates(context, dataset=dataset)
                observation = findings[0]['feature_usage'][0]
                self.assertEqual(observation['month'], '2026-09')
                self.assertIsNone(observation['active_users'])
                self.assertEqual(observation['observation_status'], 'missing')
                if options.get('include_latest') is False:
                    self.assertEqual(observation['evidence_ids'], [])
                else:
                    self.assertEqual(observation['evidence_ids'], ['feature_usage_monthly.csv:2026-09|C08|FEAT-05'])
                self.assert_findings(findings, dataset)

    def test_future_only_or_absent_usage_is_explicitly_unknown_for_canonical_industry_candidate(self):
        for include_future in (True, False):
            with self.subTest(include_future=include_future):
                dataset, context = self.reference_fixture(
                    include_latest=False, include_historical=False, include_future=include_future)
                findings = verify_reference_candidates(context, dataset=dataset)
                self.assertEqual(len(findings), 1)
                finding = findings[0]
                self.assertEqual(finding['account_id'], 'C08')
                self.assertEqual([item['relation'] for item in finding['relationships']],
                                 ['related_account_shared_industry'])
                self.assertEqual(finding['feature_usage'][0]['feature_id'], 'FEAT-05')
                self.assertIsNone(finding['feature_usage'][0]['active_users'])
                self.assertEqual(finding['feature_usage'][0]['observation_status'], 'missing')
                self.assertEqual(finding['feature_usage'][0]['evidence_ids'], [])
                self.assertNotIn('feature_usage_monthly.csv:2026-10|C08|FEAT-05', finding['evidence_ids'])
                self.assert_findings(findings, dataset)


    def test_shared_request_helper_returns_direct_focus_records_not_related_customer_requests(self):
        dataset, context = self.reference_fixture()
        requests = reference_request_rows(context, dataset=dataset)
        self.assertEqual([row.source_id for row in requests], ['I8001'])
        self.assertIs(requests[0], dataset.by_id['interactions.jsonl']['I8001'])
        self.assertEqual(requests[0].values['account_id'], 'P08')
        self.assertEqual(requests[0].raw['isi'], 'Butuh apotek; pelanggan meminta referensi pengguna apotek.')

    def test_reference_subject_only_or_other_account_message_does_not_trigger_request(self):
        dataset, context = self.reference_fixture(message='Butuh modul apotek.', subject='Permintaan referensi')
        self.assertEqual(verify_reference_candidates(context, dataset=dataset), [])

    def test_negated_or_completed_reference_mention_is_not_a_customer_request(self):
        for message in ('Kami tidak membutuhkan referensi apotek.', 'Referensi apotek sudah tersedia.'):
            with self.subTest(message=message):
                dataset, context = self.reference_fixture(message=message)
                self.assertEqual(verify_reference_candidates(context, dataset=dataset), [])
                self.assertEqual(reference_request_rows(context, dataset=dataset), [])


    def test_candidates_start_only_from_focus_canonical_related_edges(self):
        dataset, context = self.reference_fixture()
        for edge in context.graph.edges:
            if edge.relation.startswith('related_account_'):
                edge.relation = 'kandidat_referensi'
        findings = verify_reference_candidates(context, dataset=dataset)
        self.assertEqual(len(findings), 1)
        self.assertNotIn('candidate_account_id', findings[0])
        self.assertEqual(findings[0]['category'], 'data_gap')
        self.assertEqual(findings[0]['evidence_ids'], ['interactions.jsonl:I8001'])
        self.assert_findings(findings, dataset)

    def test_unrelated_deal_edge_or_noncustomer_target_is_not_a_candidate(self):
        dataset, context = self.reference_fixture()
        related = [edge for edge in context.graph.edges if edge.relation.startswith('related_account_')]
        for edge in related:
            edge.source = 'DL-OTHER'
        self.assertNotIn('candidate_account_id', verify_reference_candidates(context, dataset=dataset)[0])
        for edge in related:
            edge.source = context.deal.deal_id
            edge.target = 'P08'
        self.assertNotIn('candidate_account_id', verify_reference_candidates(context, dataset=dataset)[0])

    def test_incomplete_current_contact_history_is_explicit_unknown(self):
        dataset, context = self.reference_fixture()
        context.graph.edges = [edge for edge in context.graph.edges
                               if not (edge.relation == 'employed_at' and edge.source == 'K208')]
        finding = verify_reference_candidates(context, dataset=dataset)[0]
        self.assertIsNone(finding['current_contacts'][0]['active_employment_verified'])
        self.assertEqual(finding['current_contacts'][0]['active_employments'], [])
        self.assert_findings([finding], dataset)

    def test_noncanonical_overlap_name_does_not_claim_completed_contact_path(self):
        context = build_deal_context('DL-004').model_copy(deep=True)
        for edge in context.graph.edges:
            if edge.relation == 'overlapping_employment':
                edge.relation = 'overlap_kerja'
        finding = verify_reference_candidates(context, dataset=get_dataset())[0]
        self.assertEqual(finding['candidate_account_id'], 'C06')
        self.assertEqual(finding['work_overlap_paths'], [])
        self.assertIsNone(finding['contact_consent'])


if __name__ == '__main__':
    unittest.main()
