import unittest
import json
from datetime import date
from unittest.mock import patch

from backend.contracts import DealContext
from backend.graph.context import build_deal_context
from backend.graph.store import ContextGraph, get_context_graph
from backend.ingestion.dataset import get_dataset, load_dataset
from tests.bima.test_ingestion import make_dataset
import tempfile
from pathlib import Path


class RealGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = get_dataset()
        cls.graph = get_context_graph()

    def test_all_five_deals_have_source_ids_values_and_fixed_stage_ages(self):
        expected = {
            'DL-001': ('P01', 252000000, 20, 'E06'),
            'DL-002': ('P02', 63000000, 45, 'E07'),
            'DL-003': ('P03', 37800000, 10, 'E08'),
            'DL-004': ('P04', 147000000, 30, 'E06'),
            'DL-005': ('P05', 168000000, 5, 'E07'),
        }
        for deal_id, (account_id, annual_value, age, owner_id) in expected.items():
            with self.subTest(deal_id=deal_id):
                context = build_deal_context(deal_id)
                self.assertIsInstance(context, DealContext)
                self.assertEqual(context.schema_version, 'v1')
                self.assertEqual(context.snapshot_date, '2026-10-01')
                self.assertEqual((context.deal.deal_id, context.deal.account_id,
                                  context.deal.annual_value, context.deal.stage_age_days,
                                  context.deal.owner_id),
                                 (deal_id, account_id, annual_value, age, owner_id))
                self.assertIn(deal_id, {node.id for node in context.graph.nodes})
                self.assertIn(account_id, {node.id for node in context.graph.nodes})
                self.assertIsInstance(context.unknowns, list)
                self.assert_context_provenance(context)

    def assert_context_provenance(self, context):
        node_ids = {node.id for node in context.graph.nodes}
        evidence_ids = {item.id for item in context.evidence}
        self.assertEqual(len(node_ids), len(context.graph.nodes))
        self.assertEqual(len(evidence_ids), len(context.evidence))
        for evidence in context.evidence:
            self.assertEqual(evidence.source_file.split('/')[-1] in self.dataset.tables, True)
            self.assertTrue(evidence.excerpt)
            self.assertTrue(self.graph.lookup_evidence(evidence.id), evidence.id)
        for edge in context.graph.edges:
            with self.subTest(edge=edge.id):
                self.assertIn(edge.source, node_ids)
                self.assertIn(edge.target, node_ids)
                self.assertTrue(edge.evidence_ids)
                self.assertIn(edge.evidence_type, ('direct', 'inferred'))
                for evidence_id in edge.evidence_ids:
                    self.assertIn(evidence_id, evidence_ids)
                    self.assertTrue(self.graph.lookup_evidence(evidence_id), evidence_id)
                for bound in (edge.valid_from, edge.valid_to):
                    if bound is not None:
                        date.fromisoformat(bound)
                if edge.valid_from and edge.valid_to:
                    self.assertLessEqual(edge.valid_from, edge.valid_to)

    def test_p02_request_is_not_approval_and_precedents_keep_original_csv(self):
        context = build_deal_context('DL-002')
        evidence = {record.source_id: record for record in context.evidence}
        for interaction_id in ('I0269', 'I0296', 'I0322', 'I0348'):
            self.assertIn(interaction_id, evidence)
            self.assertEqual(evidence[interaction_id].source_file,
                             'dataset_kasirnusa/interactions.jsonl')
            self.assertEqual(evidence[interaction_id].evidence_type, 'direct')
        self.assertIn('20%', self.dataset.by_id['interactions.jsonl']['I0296'].raw['isi'])
        self.assertIn('Mohon keputusan', self.dataset.by_id['interactions.jsonl']['I0348'].raw['isi'])
        self.assertFalse(any(row.raw['account_id'] == 'P02' and
                             row.raw['keputusan'] == 'Disetujui'
                             for row in self.dataset.tables['decision_log.csv']))
        decisions = {item['decision_id']: item for item in context.candidate_decisions}
        for decision_id, deal_id, outcome in [
            ('D-2025-02', 'DL-006', 'Ditolak'),
            ('D-2025-06', 'DL-007', 'Disetujui'),
        ]:
            with self.subTest(decision=decision_id):
                self.assertIn(decision_id, decisions)
                for field, raw_value in self.dataset.by_id['decision_log.csv'][decision_id].raw.items():
                    self.assertEqual(decisions[decision_id][field], raw_value)
                self.assertEqual(decisions[decision_id]['deal_id'], deal_id)
                self.assertEqual(decisions[decision_id]['keputusan'], outcome)
                self.assertEqual(decisions[decision_id]['bukti_interaction_id'], '')
                self.assertFalse(any(edge.source == decision_id and edge.target.startswith('I0')
                                     or edge.target == decision_id and edge.source.startswith('I0')
                                     for edge in context.graph.edges))
        self.assertEqual(self.dataset.by_id['crm_deals.csv']['DL-006'].raw['status'], 'Kalah')
        self.assertEqual(self.dataset.by_id['crm_deals.csv']['DL-007'].raw['status'], 'Menang')
        self.assertFalse(any(item['account_id'] == 'P02' and
                             item['keputusan'] == 'Disetujui'
                             for item in context.candidate_decisions))
        self.assertIn('K076', {node.id for node in context.graph.nodes})
        self.assertIn('E07', {node.id for node in context.graph.nodes})

    def test_rina_old_email_identity_is_temporal_inference_not_new_address(self):
        context = build_deal_context('DL-001')
        self.assertIn('K017', {node.id for node in context.graph.nodes})
        old_email = 'rina.hapsari@kopilintas.co.id'
        old_email_edges = [edge for edge in context.graph.edges
                           if edge.evidence_type == 'inferred'
                           and 'K017' in (edge.source, edge.target)
                           and old_email in (edge.source + edge.target)]
        self.assertTrue(old_email_edges)
        for edge in old_email_edges:
            source_rows = [row for evidence_id in edge.evidence_ids
                           for row in self.graph.lookup_evidence(evidence_id)]
            self.assertTrue(any(row.source_file.endswith('interactions.jsonl') and
                                row.raw['account_id'] == 'C01' and
                                old_email in (row.raw['dari'], row.raw['ke'])
                                for row in source_rows))
            self.assertTrue(any(row.source_file.endswith('contact_employment_history.csv')
                                and row.raw['contact_id'] == 'K017'
                                and row.raw['account_id'] == 'C01'
                                and row.raw['selesai'] == '2026-08-15'
                                for row in source_rows))
            self.assertTrue(any(row.source_file.endswith('crm_contacts.csv')
                                and row.raw['contact_id'] == 'K017'
                                for row in source_rows))
        self.assertEqual(self.dataset.by_id['crm_contacts.csv']['K017'].raw['email'],
                         'rina.hapsari@mandalaritel.co.id')

    def test_workplace_overlap_remains_inferred_without_acquaintance_claim(self):
        context = build_deal_context('DL-001')
        overlaps = [edge for edge in context.graph.edges
                    if edge.relation == 'overlapping_employment']
        self.assertTrue(overlaps)
        for edge in overlaps:
            self.assertEqual(edge.evidence_type, 'inferred')
            records = [row for evidence_id in edge.evidence_ids
                       for row in self.graph.lookup_evidence(evidence_id)]
            histories = [row for row in records
                         if row.source_file.endswith('contact_employment_history.csv')]
            self.assertGreaterEqual(len({row.raw['contact_id'] for row in histories}), 2)
        self.assertFalse(any('acquaint' in edge.relation.lower() or
                             'kenal' in edge.relation.lower()
                             for edge in context.graph.edges))

    def test_snapshot_and_open_prospect_gate_are_explicit(self):
        for deal_id in ('DL-999', 'DL-006'):
            with self.subTest(deal_id=deal_id), self.assertRaises(KeyError):
                build_deal_context(deal_id)
        with self.assertRaises(ValueError):
            build_deal_context('DL-002', '2026-09-30')


class SnapshotFixtureTests(unittest.TestCase):
    def test_future_interaction_is_ingested_but_not_graph_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            make_dataset(directory, {
                'crm_accounts.csv': [{
                    'account_id': 'P02', 'nama': 'Teras Kafe Group', 'tipe': 'prospek',
                    'jumlah_outlet': '15', 'account_owner_id': 'E07',
                }],
                'crm_deals.csv': [{
                    'deal_id': 'DL-002', 'account_id': 'P02', 'tipe': 'baru',
                    'stage': 'Demo', 'stage_sejak': '2026-08-17',
                    'dibuat': '2026-07-25', 'owner_id': 'E07', 'outlet': '15',
                    'nilai_tahunan': '63000000', 'status': 'Terbuka',
                }],
                'employees.csv': [{
                    'employee_id': 'E07', 'nama': 'Citra', 'jabatan': 'Sales',
                    'email': 'citra@kasirnusa.id',
                }],
            }, interactions=[
                {'interaction_id': interaction_id, 'tanggal': when,
                 'tipe': 'catatan_meeting', 'account_id': 'P02',
                 'dari': 'citra@kasirnusa.id', 'ke': '', 'peserta': 'E07',
                 'subjek': 'Demo', 'isi': 'Pertemuan Teras Kafe', 'membalas_id': ''}
                for interaction_id, when in [('I0001', '2026-09-30'),
                                             ('I9999', '2026-10-02')]
            ])
            dataset = load_dataset(directory)
            self.assertIn('I9999', dataset.by_id['interactions.jsonl'])
            graph = ContextGraph(dataset)
            with patch('backend.graph.context.get_context_graph', return_value=graph):
                context = build_deal_context('DL-002')
            self.assertEqual(context.snapshot_date, '2026-10-01')
            self.assertIn('I0001', {record.source_id for record in context.evidence})
            self.assertNotIn('I9999', {record.source_id for record in context.evidence})
            self.assertNotIn('interactions.jsonl:I9999', graph.evidence)
            self.assertNotIn('I9999', {node.id for node in context.graph.nodes})

    def test_usage_aggregate_resolves_exact_rows_and_preserves_missing_vs_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            make_dataset(directory, {
                'crm_accounts.csv': [{'account_id': 'C01', 'nama': 'Customer', 'tipe': 'pelanggan'}],
                'outlets.csv': [{'outlet_id': 'C01-O01', 'account_id': 'C01'}],
                'product_usage_daily.csv': [
                    {'tanggal': '2026-09-29', 'outlet_id': 'C01-O01', 'account_id': 'C01',
                     'versi_aplikasi': '4.12', 'jumlah_transaksi': '7', 'transaksi_offline_tersinkron': ''},
                    {'tanggal': '2026-09-30', 'outlet_id': 'C01-O01', 'account_id': 'C01',
                     'versi_aplikasi': '4.12', 'jumlah_transaksi': '13', 'transaksi_offline_tersinkron': '0'},
                    {'tanggal': '2026-10-02', 'outlet_id': 'C01-O01', 'account_id': 'C01',
                     'versi_aplikasi': '4.12', 'jumlah_transaksi': '999', 'transaksi_offline_tersinkron': '999'},
                ],
            })
            graph = ContextGraph(load_dataset(directory))
            aggregates = [e for e in graph.evidence.values() if e.source_file.endswith('product_usage_daily.csv')]
            self.assertEqual(len(aggregates), 1)
            evidence = aggregates[0]
            summary = json.loads(evidence.excerpt)
            self.assertEqual(summary['record_count'], 2)
            self.assertEqual(summary['jumlah_transaksi'], 20)
            self.assertEqual(summary['transaksi_offline_tersinkron'], 0)
            self.assertEqual(summary['offline_observed_count'], 1)
            self.assertEqual(summary['offline_missing_count'], 1)
            self.assertEqual(summary['outlet_count'], 1)
            self.assertEqual(evidence.evidence_type, 'inferred')
            self.assertEqual(evidence.source_id, 'lines:2-3')
            records = graph.lookup_evidence(evidence.id)
            self.assertEqual([row.source_id for row in records],
                             ['2026-09-29|C01-O01', '2026-09-30|C01-O01'])
            self.assertEqual([row.line for row in records], [2, 3])

    def test_old_email_without_unique_temporal_identity_stays_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            make_dataset(directory, {
                'crm_accounts.csv': [{'account_id': aid, 'nama': aid, 'tipe': kind}
                                     for aid, kind in [('C01', 'pelanggan'), ('P01', 'prospek')]],
                'crm_contacts.csv': [
                    {'contact_id': 'K001', 'nama': 'Rina One', 'email': 'rina@new-one.id',
                     'account_id_saat_ini': 'P01'},
                    {'contact_id': 'K002', 'nama': 'Rina Two', 'email': 'rina@new-two.id',
                     'account_id_saat_ini': 'P01'},
                ],
                'contact_employment_history.csv': [
                    {'contact_id': cid, 'account_id': 'C01', 'organisasi': 'C01',
                     'mulai': '2025-01-01', 'selesai': '2026-08-15'}
                    for cid in ('K001', 'K002')
                ],
            }, interactions=[
                {'interaction_id': iid, 'tanggal': when, 'account_id': 'C01',
                 'dari': 'rina@old.id', 'ke': '', 'peserta': '', 'tipe': 'email',
                 'subjek': 'Contract', 'isi': 'Follow up', 'membalas_id': ''}
                for iid, when in [('I0001', '2026-08-14'), ('I0002', '2026-08-16')]
            ])
            graph = ContextGraph(load_dataset(directory))
            self.assertIn('email:rina@old.id', graph.graph)
            identities = [(source, target) for source, target, edge in graph.graph.edges(data=True)
                          if edge['relation'] == 'possible_historical_email_identity']
            self.assertEqual(identities, [])
