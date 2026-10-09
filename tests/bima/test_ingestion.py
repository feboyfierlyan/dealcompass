import csv
from datetime import date
import json
import tempfile
import unittest
from pathlib import Path

from backend.ingestion.dataset import SNAPSHOT_DATE, get_dataset, load_dataset


# Headers copied from dataset_kasirnusa, so the fixture exercises the real loader
# with all fifteen sources rather than a special test-only subset of its schema.
HEADERS = {
    'bugs.csv': 'bug_id,judul,versi_terdampak,status,dibuat,selesai,fitur_terkait',
    'contact_employment_history.csv': 'contact_id,account_id,organisasi,jabatan,mulai,selesai',
    'contracts_billing.csv': 'contract_id,account_id,paket,outlet_kontrak,batas_outlet_paket,mulai,tanggal_renewal,harga_per_outlet_bulan,diskon_pct,nilai_tahunan,keterlambatan_bayar_12bln,decision_id',
    'crm_accounts.csv': 'account_id,nama,tipe,industri,kota,paket,jumlah_outlet,account_owner_id,champion_contact_id,nps_terakhir,health_score_dashboard',
    'crm_contacts.csv': 'contact_id,nama,email,account_id_saat_ini,jabatan_saat_ini',
    'crm_deals.csv': 'deal_id,account_id,tipe,stage,stage_sejak,dibuat,owner_id,outlet,nilai_tahunan,status,alasan_kalah,kompetitor',
    'decision_log.csv': 'decision_id,tanggal,tipe,account_id,deal_id,diminta_oleh,diputuskan_oleh,keputusan,nilai,alasan,bukti_interaction_id,fitur_dijanjikan,status_janji',
    'employees.csv': 'employee_id,nama,jabatan,email',
    'feature_usage_monthly.csv': 'bulan,account_id,feature_id,pengguna_aktif',
    'features.csv': 'feature_id,nama,status,target_awal,target_terkini,catatan',
    'outlets.csv': 'outlet_id,account_id,kota,mode_offline_aktif',
    'product_usage_daily.csv': 'tanggal,outlet_id,account_id,versi_aplikasi,jumlah_transaksi,transaksi_offline_tersinkron',
    'releases.csv': 'versi,tanggal_rilis',
    'support_tickets.csv': 'ticket_id,dibuat,account_id,outlet_id,pelapor_contact_id,kategori,prioritas,status,versi_aplikasi,judul,deskripsi,bug_id,diselesaikan',
}
COUNTS = {
    'bugs.csv': 4, 'contact_employment_history.csv': 217,
    'contracts_billing.csv': 40, 'crm_accounts.csv': 45,
    'crm_contacts.csv': 160, 'crm_deals.csv': 22,
    'decision_log.csv': 30, 'employees.csv': 10,
    'feature_usage_monthly.csv': 1178, 'features.csv': 8,
    'interactions.jsonl': 350, 'outlets.csv': 620,
    'product_usage_daily.csv': 226300, 'releases.csv': 3,
    'support_tickets.csv': 640,
}


def make_dataset(directory, rows=None, interactions=None):
    """Create valid, independently editable copies of every source header."""
    rows = rows or {}
    for name, header in HEADERS.items():
        with (directory / name).open('w', newline='', encoding='utf-8') as output:
            writer = csv.DictWriter(output, fieldnames=header.split(','))
            writer.writeheader()
            writer.writerows(rows.get(name, []))
    with (directory / 'interactions.jsonl').open('w', encoding='utf-8') as output:
        for interaction in interactions or []:
            output.write(json.dumps(interaction, ensure_ascii=False) + '\n')


class RealDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = get_dataset()

    def test_inventory_covers_all_sources_without_xlsx_or_dropping_daily_usage(self):
        self.assertEqual(SNAPSHOT_DATE.isoformat(), '2026-10-01')
        inventory = {item['source_file'].split('/')[-1]: item
                     for item in self.dataset.inventory()}
        self.assertEqual({name: item['count'] for name, item in inventory.items()}, COUNTS)
        self.assertEqual(set(self.dataset.tables), set(COUNTS))
        self.assertEqual(len(self.dataset.tables['product_usage_daily.csv']), 226300)
        for filename, item in inventory.items():
            self.assertEqual(item['source_file'], 'dataset_kasirnusa/' + filename)
            self.assertTrue(item['columns'])
            self.assertTrue(item['key_fields'])
            self.assertIn(filename, self.dataset.by_id)
        self.assertEqual(self.dataset.by_id['interactions.jsonl']['I0296'].line, 296)

    def test_normalization_preserves_raw_values_and_source_provenance(self):
        deal = self.dataset.by_id['crm_deals.csv']['DL-002']
        self.assertEqual(deal.source_id, 'DL-002')
        self.assertEqual(deal.source_file, 'dataset_kasirnusa/crm_deals.csv')
        self.assertEqual(deal.line, 3)
        self.assertEqual(deal.raw['nilai_tahunan'], '63000000')
        self.assertEqual(deal.values['nilai_tahunan'], 63000000)
        self.assertEqual(deal.raw['stage_sejak'], '2026-08-17')
        self.assertEqual(deal.values['stage_sejak'], date(2026, 8, 17))
        self.assertEqual(self.dataset.query('crm_deals.csv', account_id='P02'), [deal])
        self.assertEqual(self.dataset.by_id['decision_log.csv']['D-2025-06'].raw['nilai'],
                         'Paket Starter tanpa diskon, pilot 6 outlet')


class SmallDatasetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def test_usage_exact_totals_and_missing_offline_not_zero(self):
        make_dataset(self.directory, {'product_usage_daily.csv': [
            {'tanggal': '2026-09-29', 'outlet_id': 'C01-O01', 'account_id': 'C01',
             'versi_aplikasi': '4.12', 'jumlah_transaksi': '7', 'transaksi_offline_tersinkron': ''},
            {'tanggal': '2026-09-30', 'outlet_id': 'C01-O01', 'account_id': 'C01',
             'versi_aplikasi': '4.12', 'jumlah_transaksi': '13', 'transaksi_offline_tersinkron': '0'},
            {'tanggal': '2026-10-01', 'outlet_id': 'C01-O01', 'account_id': 'C01',
             'versi_aplikasi': '4.12', 'jumlah_transaksi': '5', 'transaksi_offline_tersinkron': '3'},
        ]})
        dataset = load_dataset(self.directory)
        usage = dataset.query('product_usage_daily.csv', account_id='C01')
        self.assertEqual([row.values['tanggal'] for row in usage],
                         [date(2026, 9, 29), date(2026, 9, 30), date(2026, 10, 1)])
        self.assertEqual(len(usage), 3)
        self.assertEqual(sum(row.values['jumlah_transaksi'] for row in usage), 25)
        self.assertEqual([row.values['transaksi_offline_tersinkron'] for row in usage],
                         [None, 0, 3])
        self.assertEqual([row.raw['transaksi_offline_tersinkron'] for row in usage],
                         ['', '0', '3'])
        self.assertEqual(len(dataset.by_id['product_usage_daily.csv']), 3)
        self.assertEqual([row.line for row in usage], [2, 3, 4])

    def test_bad_numeric_and_duplicate_keys_identify_source_and_physical_line(self):
        for name, rows, line in [
            ('crm_deals.csv', [{'deal_id': 'DL-002', 'nilai_tahunan': 'invalid'}], 2),
            ('bugs.csv', [{'bug_id': 'BUG-412', 'dibuat': '2026-02-30'}], 2),
            ('bugs.csv', [{'bug_id': 'BUG-412'}, {'bug_id': 'BUG-412'}], 3),
        ]:
            with self.subTest(source=name, line=line):
                make_dataset(self.directory, {name: rows})
                with self.assertRaises(ValueError) as caught:
                    load_dataset(self.directory)
                self.assertIn(name, str(caught.exception))
                self.assertIn(str(line), str(caught.exception))

    def test_bad_jsonl_identifies_source_and_line(self):
        make_dataset(self.directory)
        (self.directory / 'interactions.jsonl').write_text('{bad json}\n', encoding='utf-8')
        with self.assertRaises(ValueError) as caught:
            load_dataset(self.directory)
        self.assertIn('interactions.jsonl', str(caught.exception))
        self.assertIn('1', str(caught.exception))

    def test_case_and_whitespace_in_join_ids_resolve_without_changing_raw_sources(self):
        make_dataset(self.directory, {
            'crm_contacts.csv': [{'contact_id': ' k076 ', 'nama': 'Teddy',
                                  'email': ' Teddy@Example.ID ', 'account_id_saat_ini': ' p02 '}],
            'decision_log.csv': [{'decision_id': ' d-2025-06 ', 'tanggal': '2025-08-12',
                                  'account_id': ' c23 ', 'diminta_oleh': ' e07 ',
                                  'diputuskan_oleh': ' e01 ', 'fitur_dijanjikan': ' feat-05 '}],
        }, interactions=[{'interaction_id': ' i0001 ', 'tanggal': '2026-09-30',
                          'peserta': ' k076 ; e07 ', 'account_id': ' p02 '}])
        dataset = load_dataset(self.directory)
        contact = dataset.by_id['crm_contacts.csv']['K076']
        self.assertEqual(contact.values['account_id_saat_ini'], 'P02')
        self.assertEqual(contact.values['email'], 'teddy@example.id')
        self.assertEqual(contact.raw['contact_id'], ' k076 ')
        decision = dataset.by_id['decision_log.csv']['D-2025-06']
        self.assertEqual((decision.values['diminta_oleh'], decision.values['diputuskan_oleh'],
                          decision.values['fitur_dijanjikan']), ('E07', 'E01', 'FEAT-05'))
        self.assertEqual(dataset.by_id['interactions.jsonl']['I0001'].values['peserta'], 'K076;E07')
