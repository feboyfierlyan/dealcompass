"""BIMA-02 internal factual analysis, not the Ical Recommendation API.

Conversation rules inspect only dated focus-account messages in the deal window.
Follow-up implications describe missing checks, not approved sales actions.
"""
from collections import Counter
from backend.ingestion.scope import snapshot_date as active_snapshot
from datetime import date
from decimal import Decimal
import json
import re

from backend.contracts import DealContext, EvidenceRecord
from backend.graph.store import ContextGraph, get_context_graph
from backend.graph.verification import reference_request_rows, verify_authority_paths, verify_reference_candidates
from backend.ingestion.dataset import Dataset, get_dataset
from backend.ingestion.metrics import evidence_id, summarize_deal


_PRICE = re.compile(r'harga\s+(?:terlalu\s+tinggi|terlalu\s+mahal)|lebih\s+murah', re.IGNORECASE)
_REQUEST = re.compile(r'usul|mohon|minta|ajukan', re.IGNORECASE)
_DISCOUNT = re.compile(r'diskon\s+(\d+(?:[.,]\d+)?)\s*%', re.IGNORECASE)


def _finding(identifier, category, fact, ids, interpretation, missing, implication):
    return dict(finding_id=identifier, category=category, fact=fact,
                evidence_ids=sorted(set(ids)), interpretation=interpretation,
                interpretation_type='inferred', missing_information=missing,
                follow_up_implication=implication)


def _record(dataset, identifier):
    filename, source_id = identifier.split(':', 1)
    return dataset.by_id[filename][source_id]


def _sources(dataset, value):
    identifiers = set()

    def visit(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if key.endswith('evidence_ids'):
                    identifiers.update(child)
                else:
                    visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    evidence = []
    for identifier in sorted(identifiers):
        row = _record(dataset, identifier)
        when = next((row.values.get(key) for key in ('tanggal', 'dibuat', 'mulai')
                     if isinstance(row.values.get(key), date)), None)
        evidence.append(EvidenceRecord(id=identifier, source_file=row.source_file,
            source_id=row.source_id, date=when.isoformat() if when else None,
            excerpt=json.dumps(row.raw, ensure_ascii=False), evidence_type='direct').model_dump())
    return evidence


def analyze_deal_initial(context: DealContext, *, dataset: Dataset | None = None) -> dict:
    """Return sourced metrics/findings for one canonical context, without ranking."""
    if context.snapshot_date != active_snapshot().isoformat():
        raise ValueError('Requested snapshot does not match this workspace.')
    dataset = dataset if dataset is not None else get_dataset()
    metrics = summarize_deal(context.deal.deal_id, dataset=dataset)
    if metrics['account_id'] != context.deal.account_id:
        raise ValueError('Akun konteks tidak sesuai sumber deal.')
    deal_id, account_id = context.deal.deal_id, context.deal.account_id
    deal = dataset.by_id['crm_deals.csv'][deal_id]
    account = dataset.by_id['crm_accounts.csv'][account_id]
    root_ids = [evidence_id(deal), evidence_id(account)]
    buckets = metrics['interactions']
    customer_rows = [_record(dataset, eid) for eid in buckets['customer']['evidence_ids']]
    internal_rows = [_record(dataset, eid) for eid in buckets['internal']['evidence_ids']]
    findings = verify_authority_paths(context, dataset=dataset)
    reference_rows = reference_request_rows(context, dataset=dataset)
    for row in customer_rows:
        message = row.values.get('isi') or ''
        if _PRICE.search(message):
            findings.append(_finding(f'price_objection:{deal_id}:{row.source_id}', 'business_anomaly',
                f'{row.source_id} ({row.values["tanggal"].isoformat()}): {row.raw["isi"]}',
                [evidence_id(row), evidence_id(deal)],
                'Percakapan mendukung keberatan harga; harga kompetitor yang disebut bukan permintaan atau approval diskon prospek.',
                ['Batas anggaran dan perbandingan cakupan penawaran belum dikonfirmasi.',
                 'Lamanya tahap tidak membuktikan harga sebagai satu-satunya penyebab.'],
                ['Klarifikasi anggaran dan lingkup pembandingan kepada pelanggan; jangan menganggap angka kompetitor sebagai diskon yang disetujui.']))
    for row in reference_rows:
        message = row.values.get('isi') or ''
        when = row.values.get('tanggal')
        dated = isinstance(when, date)
        when_text = when.isoformat() if dated else 'tanggal belum tersedia'
        paused = bool(re.search(r'tunda|sampai ada referensi', message, re.IGNORECASE))
        missing = ['Kriteria pengguna yang dianggap mirip dan format referensi yang diterima belum lengkap.',
                   'Kelayakan, pengalaman terkini, serta izin kandidat untuk berbagi pengalaman belum dikonfirmasi.']
        if not dated:
            missing.append('Posisi waktu percakapan terhadap snapshot belum dapat diverifikasi.')
        findings.append(_finding(f'reference_requirement:{deal_id}:{row.source_id}',
            'business_anomaly' if dated else 'data_gap',
            f'{row.source_id} ({when_text}): {row.raw["isi"]}',
            [evidence_id(row), evidence_id(deal)],
            'Pelanggan menyatakan menunda sampai ada referensi.' if paused else
            'Pelanggan meminta referensi; permintaan saja tidak membuktikan deal sudah tertunda atau referensi sudah diberikan.',
            missing,
            ['Validasi kriteria referensi dengan prospek; periksa kandidat bersumber bersama account owner dan minta izin sebelum memperkenalkan.']))
    for row in internal_rows:
        message = row.values.get('isi') or ''
        if not _REQUEST.search(message):
            continue
        percentages = sorted({Decimal(match.replace(',', '.')) for match in _DISCOUNT.findall(message)})
        for percent in percentages:
            focus_logs = [r for r in dataset.tables['decision_log.csv']
                          if r.values['account_id'] == account_id and r.values['deal_id'] == deal_id
                          and isinstance(r.values['tanggal'], date) and r.values['tanggal'] <= active_snapshot()]
            account_only = [r for r in dataset.tables['decision_log.csv']
                            if r.values['account_id'] == account_id and r.values['deal_id'] is None
                            and isinstance(r.values['tanggal'], date) and r.values['tanggal'] <= active_snapshot()]
            ids = [evidence_id(row), evidence_id(deal)] + [evidence_id(r) for r in focus_logs + account_only]
            recipients = {address.strip() for address in (row.values.get('ke') or '').split(';')}
            vp_recipients = [r for r in dataset.tables['employees.csv']
                             if r.values['email'] in recipients and r.values['jabatan'] == 'VP Sales']
            ids.extend(evidence_id(r) for r in vp_recipients)
            finding = _finding(f'discount_request:{deal_id}:{row.source_id}:{percent}', 'business_anomaly',
                f'{row.source_id} ({row.values["tanggal"].isoformat()}) email internal: {row.raw["isi"]} '
                f'Pencarian log pada snapshot menemukan {len(focus_logs)} keputusan dengan account_id dan deal_id fokus.',
                ids, 'Usulan sales adalah permintaan, bukan approval. Log akun lain atau log tanpa deal_id tidak mengesahkan permintaan deal fokus.',
                ['Keputusan atas permintaan dan justifikasi komersial perlu dikonfirmasi; tidak disimpulkan dari email permintaan.'],
                ['Periksa keputusan dan log sebelum penawaran; diskon >10% memerlukan VP Sales serta pencatatan menurut kontrak tim.'] if percent > 10 else
                ['Periksa keputusan dan log sebelum menganggap permintaan sebagai persetujuan.'])
            finding['requested_discount_pct'] = str(percent)
            finding['decision_lookup'] = dict(source_file=dataset.source_files['decision_log.csv'],
                account_id=account_id, deal_id=deal_id, through=active_snapshot().isoformat(),
                focus_log_evidence_ids=[evidence_id(r) for r in focus_logs],
                account_only_log_evidence_ids=[evidence_id(r) for r in account_only],
                inspected_record_count=len(dataset.tables['decision_log.csv']))
            finding['policy_source'] = 'docs/coordination/API_CONTRACT.md:73-78'
            findings.append(finding)
    if buckets['customer']['count'] == 0:
        finding = _finding(f'customer_information_gap:{deal_id}', 'data_gap',
            f'{account_id}: tidak ada interaksi eksternal bertanggal dalam jendela sumber; '
            f'{buckets["internal"]["count"]} email internal tercatat. '
            + (f'Umur deal {metrics["deal_age_days"]} hari.' if metrics['deal_age_days'] is not None else 'Umur deal belum dapat dihitung.'),
            root_ids, 'Kekurangan percakapan adalah batas pengetahuan, bukan bukti deal kalah, tidak berminat, atau outlier statistik.',
            ['Kebutuhan, hambatan, proses pengadaan, pengambil keputusan dan kontak pelanggan belum cukup didukung percakapan.',
             'Aktivitas yang tidak dicatat di dataset tidak dapat disimpulkan ada atau tidak ada.'],
            ['Lengkapi discovery dan pencatatan kontak/interaksi terlebih dahulu; jangan memberi diagnosis komersial dari kekosongan sumber.'])
        finding['search_scope'] = metrics['query_scope']
        findings.append(finding)
    references = verify_reference_candidates(context, dataset=dataset) if reference_rows else []
    report = dict(deal_id=deal_id, account_id=account_id, snapshot_date=context.snapshot_date,
                  metrics=metrics, findings=findings, reference_candidates=references,
                  boundaries=['business_anomaly berarti hambatan/ketidakselarasan yang didukung percakapan, bukan pelanggaran SLA yang belum tersedia.',
                              'Interaksi eksternal mencakup email keluar dan catatan meeting; tanggal terakhir bukan otomatis tanggal balasan pelanggan.',
                              'Implikasi tindak lanjut adalah pemeriksaan informasi, bukan Recommendation Ical, approval, ranking atau confidence.'])
    report['evidence'] = _sources(dataset, report)
    return report


def analyze_pipeline_initial(snapshot_date: str | None = None, *, dataset: Dataset | None = None) -> dict:
    """Analyze all open prospects; a heterogeneous five-deal set is not an outlier model."""
    snapshot_date = active_snapshot().isoformat() if snapshot_date is None else snapshot_date
    if snapshot_date != active_snapshot().isoformat():
        raise ValueError('Requested snapshot does not match this workspace.')
    store = get_context_graph() if dataset is None else ContextGraph(dataset)
    dataset = store.dataset
    reports = []
    stage_counts = Counter()
    deal_ids = []
    for row in dataset.tables['crm_deals.csv']:
        account = dataset.by_id['crm_accounts.csv'][row.values['account_id']]
        if row.values['status'] == 'Terbuka' and account.values['tipe'] == 'prospek':
            if isinstance(row.values['dibuat'], date) and row.values['dibuat'] > active_snapshot():
                continue
            reports.append(analyze_deal_initial(store.deal_context(row.values['deal_id']), dataset=dataset))
            stage_counts[row.values['stage']] += 1
            deal_ids.append(evidence_id(row))
    return dict(snapshot_date=snapshot_date, deals=reports,
        statistical_assessment=dict(status='not_assessed', sample_size=len(reports),
            stage_cohort_counts=dict(stage_counts), method=None, threshold=None, outlier_deal_ids=None,
            evidence_ids=deal_ids,
            reason='Pengamatan umur prospek lintas tahap bukan distribusi pembanding per tahap/segmen; SLA juga belum tersedia. '
                   'Nilai paling lama adalah deskripsi sampel, bukan dasar menyatakan outlier statistik.'))
