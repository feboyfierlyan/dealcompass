"""Preliminary, sourced authority and reference checks, not recommendations."""
from collections import defaultdict
from datetime import date
import re

from backend.contracts import DealContext
from backend.ingestion.dataset import Dataset, SourceRecord, get_dataset
from backend.ingestion.metrics import evidence_id


_AUTHORITY = re.compile(
    r'\b(?:keputusan|wewenang|otoritas)\s+(?:akhir\s+)?(?:pengadaan|pembelian)\b'
    r'|\b(?:memutuskan|menentukan|menyetujui)\s+(?:pengadaan|pembelian)\b',
    re.IGNORECASE,
)
_REFERENCE = re.compile(r'\breferensi\b|rekomendasi dari pengguna', re.IGNORECASE)
_MONTHS = {
    'januari': 1, 'februari': 2, 'maret': 3, 'april': 4, 'mei': 5,
    'juni': 6, 'juli': 7, 'agustus': 8, 'september': 9, 'oktober': 10,
    'november': 11, 'desember': 12,
}
_JOINING = re.compile(
    r'\b(?:bergabung|mulai bekerja|masuk)\s+(?:pada\s+)?'
    r'(?:(?:awal|pertengahan|akhir)\s+)?(' + '|'.join(_MONTHS) + r')'
    r'(?:\s+(\d{4}))?\b', re.IGNORECASE,
)


def _iso(value):
    return value.isoformat() if isinstance(value, date) else None


def _resolve(dataset, identifier):
    filename, separator, source_id = identifier.partition(':')
    if not separator:
        return None
    return dataset.by_id.get(filename, {}).get(source_id)


def _records(dataset, identifiers, filename=None):
    records = {}
    for identifier in identifiers:
        record = _resolve(dataset, identifier)
        if record is not None and (filename is None or record.source_file.endswith('/' + filename)):
            records[evidence_id(record)] = record
    return list(records.values())


def _active(history, when):
    start, end = history.values.get('mulai'), history.values.get('selesai')
    return (isinstance(when, date) and isinstance(start, date) and start <= when
            and (end is None or isinstance(end, date) and start <= end and when <= end))


def _histories(context, dataset, contact_id, account_id=None):
    identifiers = [identifier for edge in context.graph.edges
                   if edge.relation == 'employed_at' and edge.source == contact_id
                   and (account_id is None or edge.target == account_id)
                   for identifier in edge.evidence_ids]
    return [row for row in _records(dataset, identifiers, 'contact_employment_history.csv')
            if row.values.get('contact_id') == contact_id
            and (account_id is None or row.values.get('account_id') == account_id)]


def _employment(row: SourceRecord):
    v = row.values
    return {'contact_id': v.get('contact_id'), 'account_id': v.get('account_id'),
            'organization': v.get('organisasi'), 'role': v.get('jabatan'),
            'valid_from': _iso(v.get('mulai')), 'valid_to': _iso(v.get('selesai')),
            'evidence_ids': [evidence_id(row)]}


def _contact(row: SourceRecord):
    v = row.values
    return {'contact_id': v['contact_id'], 'name': v.get('nama'),
            'role': v.get('jabatan_saat_ini'), 'email': v.get('email'),
            'current_account_id': v.get('account_id_saat_ini'),
            'evidence_ids': [evidence_id(row)]}


def _message_contacts(context, dataset, row):
    contacts = dataset.by_id['crm_contacts.csv']
    v = row.values
    if v.get('tipe') == 'email':
        senders = {value.strip() for value in (v.get('dari') or '').split(';') if value.strip()}
        people = {person.values['contact_id']: person for person in contacts.values()
                  if person.values.get('email') in senders}
        email_nodes = {f'email:{sender}' for sender in senders}
        for edge in context.graph.edges:
            if (edge.relation == 'possible_historical_email_identity' and edge.source in email_nodes
                    and evidence_id(row) in edge.evidence_ids and edge.target in contacts):
                people[edge.target] = contacts[edge.target]
    else:
        people = {cid: contacts[cid] for cid in (v.get('peserta') or '').split(';') if cid in contacts}
    return [person for person in people.values()
            if person.values.get('account_id_saat_ini') == context.deal.account_id
            or any(_active(history, v.get('tanggal')) for history in
                   _histories(context, dataset, person.values['contact_id'], context.deal.account_id))]


def _customer_messages(context, dataset):
    """Read isi only, scoped through the producer's interaction_for relation."""
    account_id = context.deal.account_id
    snapshot = date.fromisoformat(context.snapshot_date)
    deal = dataset.by_id['crm_deals.csv'].get(context.deal.deal_id)
    created = deal.values.get('dibuat') if deal else None
    employees = {row.values.get('email') for row in dataset.tables['employees.csv']}
    allowed_types = {'email', 'catatan_meeting'}
    interaction_ids = sorted({edge.source for edge in context.graph.edges
                              if edge.relation == 'interaction_for' and edge.target == account_id})
    for interaction_id in interaction_ids:
        row = dataset.by_id['interactions.jsonl'].get(interaction_id)
        if row is None or row.values.get('account_id') != account_id:
            continue
        v, when = row.values, row.values.get('tanggal')
        if isinstance(when, date) and (when > snapshot or isinstance(created, date) and when < created):
            continue
        if v.get('tipe') == 'email':
            senders = {value.strip() for value in (v.get('dari') or '').split(';') if value.strip()}
            if not senders or senders & employees:
                continue
        if v.get('tipe') not in allowed_types or not _message_contacts(context, dataset, row):
            continue
        yield row


def _reported_authority(text, roles):
    """Resolve explicit role statements; a title elsewhere is not authority."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    statements = []
    for index, sentence in enumerate(sentences):
        authority = _AUTHORITY.search(sentence)
        if authority is None:
            continue
        if re.search(r'\b(?:bukan|tidak|belum)\b', sentence, re.IGNORECASE):
            continue
        if re.match(r'keputusan|wewenang|otoritas', authority.group(), re.IGNORECASE):
            scope = sentence[authority.end():]
        else:
            scope = sentence[:authority.start()]
        if index and re.search(r'\b(?:beliau|peran tersebut|jabatan tersebut)\b', scope, re.IGNORECASE):
            scope = sentences[index - 1] + ' ' + scope
        matched = [role for role in roles if re.search(
            r'(?<!\w)' + re.escape(role) + r'(?!\w)', scope, re.IGNORECASE)]
        # A shorter title contained inside a stated title is not a second role.
        matched = [role for role in matched if not any(
            role.casefold() != other.casefold() and role.casefold() in other.casefold()
            for other in matched)]
        statements.append((scope, matched))
    return statements


def _requests_reference(text):
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        if (_REFERENCE.search(sentence)
                and re.search(r'\b(?:minta|meminta|mohon|butuh|membutuhkan|perlu|memerlukan|menunggu|tunda|tunggu)\b',
                              sentence, re.IGNORECASE)
                and not re.search(r'\b(?:tidak|bukan)\b', sentence, re.IGNORECASE)):
            return True
    return False


def _historical_email_paths(context, dataset, contact_id):
    paths = []
    for edge in context.graph.edges:
        if edge.relation != 'possible_historical_email_identity' or edge.target != contact_id:
            continue
        rows = _records(dataset, edge.evidence_ids)
        interactions = [row for row in rows if row.source_file.endswith('/interactions.jsonl')]
        histories = [row for row in rows if row.source_file.endswith('/contact_employment_history.csv')
                     and row.values.get('contact_id') == contact_id]
        contact_rows = [row for row in rows if row.source_file.endswith('/crm_contacts.csv')
                        and row.values.get('contact_id') == contact_id]
        if not interactions or not contact_rows or not histories:
            continue
        paths.append({'relation': edge.relation, 'email_node': edge.source,
                      'contact_id': contact_id, 'interpretation_type': 'inferred',
                      'valid_from': edge.valid_from, 'valid_to': edge.valid_to,
                      'interactions': [{'interaction_id': row.values['interaction_id'],
                                        'account_id': row.values.get('account_id'),
                                        'date': _iso(row.values.get('tanggal')),
                                        'evidence_ids': [evidence_id(row)]} for row in interactions],
                      'employments': [_employment(row) for row in histories],
                      'evidence_ids': sorted(evidence_id(row) for row in rows)})
    return paths


def verify_authority_paths(context: DealContext, *, dataset: Dataset | None = None) -> list[dict]:
    """Infer candidates only from customer authority reports plus active history."""
    dataset = get_dataset() if dataset is None else dataset
    contacts = dataset.tables['crm_contacts.csv']
    roles = sorted({str(row.values[field]) for filename, field in
                    [('crm_contacts.csv', 'jabatan_saat_ini'),
                     ('contact_employment_history.csv', 'jabatan')]
                    for row in dataset.tables[filename] if row.values.get(field)})
    findings = []
    for interaction in _customer_messages(context, dataset):
        v, when = interaction.values, interaction.values.get('tanggal')
        statements = _reported_authority(v.get('isi') or '', roles)
        if not statements:
            continue
        reported_roles = sorted({role for _, matched in statements for role in matched})
        role_keys = {role.casefold() for role in reported_roles}
        joining = _JOINING.search(' '.join(scope for scope, _ in statements))
        joining_month = None
        if joining and isinstance(when, date):
            month = _MONTHS[joining.group(1).lower()]
            year = int(joining.group(2)) if joining.group(2) else when.year - (month > when.month)
            joining_month = f'{year:04d}-{month:02d}'
        matches = []
        role_contacts = []
        ids = {evidence_id(interaction)}
        reporting_contacts = []
        for reporter in _message_contacts(context, dataset, interaction):
            reporter_histories = [row for row in _histories(context, dataset, reporter.values['contact_id'],
                                                           context.deal.account_id) if _active(row, when)]
            reporting_contacts.append({**_contact(reporter),
                                       'active_employments': [_employment(row) for row in reporter_histories]})
            ids.add(evidence_id(reporter))
            ids.update(evidence_id(row) for row in reporter_histories)
        for person in contacts:
            p = person.values
            if (p.get('account_id_saat_ini') != context.deal.account_id
                    or (p.get('jabatan_saat_ini') or '').casefold()
                    not in role_keys):
                continue
            histories = _histories(context, dataset, p['contact_id'], context.deal.account_id)
            ids.add(evidence_id(person))
            ids.update(evidence_id(history) for history in histories)
            active = [history for history in histories if _active(history, when)
                      and (history.values.get('jabatan') or '').casefold()
                      == (p.get('jabatan_saat_ini') or '').casefold()
                      and (joining_month is None
                           or history.values['mulai'].strftime('%Y-%m') == joining_month)]
            observed = {**_contact(person), 'employments': [_employment(row) for row in histories],
                        'matched_active_employments': [_employment(row) for row in active]}
            role_contacts.append(observed)
            if active:
                matches.append(observed)
        unique = matches[0] if len(matches) == 1 and len(role_keys) == 1 else None
        missing = ['Konfirmasi langsung identitas dan wewenang pengadaan dari pelanggan belum tersedia.']
        if not isinstance(when, date):
            missing.append('Tanggal interaksi tidak tersedia; masa kerja aktif tidak dapat diverifikasi.')
        if joining and joining_month is None:
            missing.append('Tahun/bulan bergabung belum dapat ditentukan tanpa tanggal interaksi.')
        if not reported_roles:
            missing.append('Jabatan yang disebut sebagai pemegang wewenang belum cocok dengan sumber kontak/riwayat.')
        elif len(role_keys) > 1:
            missing.append('Pesan menyebut lebih dari satu jabatan; penetapan peran pemegang wewenang masih ambigu.')
        if not matches:
            missing.append('Belum ada kontak dengan jabatan, masa kerja aktif dan bulan bergabung yang cocok.')
        elif len(matches) > 1:
            missing.append('Lebih dari satu kontak cocok; identitas pemegang wewenang masih ambigu.')
        historical_paths = []
        employment_history = []
        fact = f'{v["interaction_id"]} mencatat pesan pelanggan: {v.get("isi") or ""}'
        if unique:
            cid = unique['contact_id']
            historical_paths = _historical_email_paths(context, dataset, cid)
            employment_history = [_employment(row) for row in _histories(context, dataset, cid)]
            for path in historical_paths:
                ids.update(path['evidence_ids'])
            for history in employment_history:
                ids.update(history['evidence_ids'])
            fact += (f' CRM mencatat {unique["name"]} ({cid}) sebagai {unique["role"]}'
                     f' di {unique["current_account_id"]}; riwayat cocok pada tanggal pesan.')
            interpretation = (f'{unique["name"]} ({cid}) merupakan kandidat identitas pemegang wewenang'
                              ' dari gabungan pesan, jabatan dan masa kerja, bukan penetapan langsung.')
            if historical_paths:
                missing.append('Identitas email historis inferred dari graph belum dikonfirmasi langsung.')
        else:
            interpretation = ('Pesan menyebut wewenang pengadaan, tetapi identitas belum dapat'
                              ' di-resolve secara unik; jabatan tertinggi tidak menggantikan bukti.')
        findings.append({
            'finding_id': f'{context.deal.deal_id}:authority:{v["interaction_id"]}',
            'category': 'business_anomaly' if unique else 'data_gap',
            'fact': fact, 'evidence_ids': sorted(ids), 'interpretation': interpretation,
            'interpretation_type': 'inferred', 'missing_information': missing,
            'follow_up_implication': ['Konfirmasikan siapa pemegang wewenang pengadaan dan jalur komunikasi langsung sebelum meneruskan proposal.'],
            'account_id': context.deal.account_id, 'interaction_id': v['interaction_id'],
            'interaction_date': _iso(when), 'reported_roles': reported_roles,
            'reported_joining_month': joining_month, 'authority_contact_id': unique['contact_id'] if unique else None,
            'candidate_contacts': matches, 'role_contacts': role_contacts,
            'reporting_contacts': reporting_contacts,
            'historical_email_paths': historical_paths, 'employment_history': employment_history,
        })
    return findings


def _account(row: SourceRecord):
    v = row.values
    return {'account_id': v['account_id'], 'name': v.get('nama'),
            'industry': v.get('industri'), 'outlet_count': v.get('jumlah_outlet'),
            'nps_last': v.get('nps_terakhir'), 'dashboard_health': v.get('health_score_dashboard'),
            'evidence_ids': [evidence_id(row)]}


def _latest_usage(dataset, account_id, feature_id, snapshot):
    completed_month = date(snapshot.year, snapshot.month, 1).toordinal() - 1
    month = date.fromordinal(completed_month).strftime('%Y-%m')
    row = dataset.by_id['feature_usage_monthly.csv'].get(f'{month}|{account_id}|{feature_id}')
    return {'feature_id': feature_id, 'month': month,
            'active_users': row.values.get('pengguna_aktif') if row else None,
            'observation_status': 'recorded' if row and row.values.get('pengguna_aktif') is not None else 'missing',
            'evidence_ids': [evidence_id(row)] if row else []}


def _overlap_paths(context, dataset, account_id, related_edges):
    support_ids = {identifier for edge in related_edges if edge.relation == 'related_account_work_overlap'
                   for identifier in edge.evidence_ids}
    contacts = dataset.by_id['crm_contacts.csv']
    snapshot = date.fromisoformat(context.snapshot_date)
    paths = []
    for edge in context.graph.edges:
        if edge.relation != 'overlapping_employment' or not set(edge.evidence_ids) <= support_ids:
            continue
        first, second = contacts.get(edge.source), contacts.get(edge.target)
        if first is None or second is None:
            continue
        if (first.values.get('account_id_saat_ini'), second.values.get('account_id_saat_ini')) == (account_id, context.deal.account_id):
            first, second = second, first
        if (first.values.get('account_id_saat_ini'), second.values.get('account_id_saat_ini')) != (context.deal.account_id, account_id):
            continue
        histories = _records(dataset, edge.evidence_ids, 'contact_employment_history.csv')
        a = next((row for row in histories if row.values.get('contact_id') == first.values['contact_id']), None)
        b = next((row for row in histories if row.values.get('contact_id') == second.values['contact_id']), None)
        if a is None or b is None:
            continue
        av, bv = a.values, b.values
        organization_a, organization_b = av.get('account_id') or av.get('organisasi'), bv.get('account_id') or bv.get('organisasi')
        if not organization_a or organization_a != organization_b:
            continue
        if not isinstance(av.get('mulai'), date) or not isinstance(bv.get('mulai'), date):
            continue
        start = max(av['mulai'], bv['mulai'])
        ends = [value for value in (av.get('selesai'), bv.get('selesai')) if isinstance(value, date)]
        end = min(ends) if ends else None
        if start > (end or snapshot):
            continue
        current_first = [row for row in _histories(context, dataset, first.values['contact_id'], context.deal.account_id) if _active(row, snapshot)]
        current_second = [row for row in _histories(context, dataset, second.values['contact_id'], account_id) if _active(row, snapshot)]
        evidence = {evidence_id(row) for row in [first, second, a, b, *current_first, *current_second]}
        paths.append({'relation': 'overlapping_employment', 'organization': av.get('organisasi'),
                      'valid_from': start.isoformat(), 'valid_to': _iso(end),
                      'interpretation_type': 'inferred', 'acquaintance_confirmed': None,
                      'focus_contact': _contact(first), 'candidate_contact': _contact(second),
                      'historical_employments': [_employment(a), _employment(b)],
                      'current_focus_employments': [_employment(row) for row in current_first],
                      'current_candidate_employments': [_employment(row) for row in current_second],
                      'evidence_ids': sorted(evidence)})
    return paths


def reference_request_rows(context: DealContext, *, dataset: Dataset | None = None) -> list[SourceRecord]:
    """Return direct focus-customer request rows using the verification scope."""
    dataset = get_dataset() if dataset is None else dataset
    return [row for row in _customer_messages(context, dataset)
            if _requests_reference(row.values.get('isi') or '')]


def verify_reference_candidates(context: DealContext, *, dataset: Dataset | None = None) -> list[dict]:
    """Describe canonical customer candidates without suitability or permission rules."""
    dataset = get_dataset() if dataset is None else dataset
    requests = reference_request_rows(context, dataset=dataset)
    if not requests:
        return []
    grouped = defaultdict(list)
    accounts = dataset.by_id['crm_accounts.csv']
    for edge in context.graph.edges:
        account = accounts.get(edge.target)
        if (edge.source == context.deal.deal_id and edge.relation.startswith('related_account_')
                and edge.target != context.deal.account_id and account is not None
                and account.values.get('tipe') == 'pelanggan'):
            grouped[edge.target].append(edge)
    request_ids = {evidence_id(row) for row in requests}
    request_observations = [{'interaction_id': row.values['interaction_id'],
                             'date': _iso(row.values.get('tanggal')), 'message': row.values.get('isi'),
                             'evidence_ids': [evidence_id(row)]} for row in requests]
    if not grouped:
        return [{'finding_id': f'{context.deal.deal_id}:reference:missing', 'category': 'data_gap',
                 'fact': 'Pesan pelanggan meminta referensi: ' + ' '.join(row.values.get('isi') or '' for row in requests),
                 'evidence_ids': sorted(request_ids), 'interpretation_type': 'inferred',
                 'interpretation': 'Belum ada kandidat akun pelanggan melalui relasi related_account_* kanonis; bukan bukti bahwa referensi tidak tersedia.',
                 'missing_information': ['Kandidat dengan hubungan bersumber, kesesuaian, pengalaman terbaru dan izin kontak belum tersedia.'],
                 'follow_up_implication': ['Cari hubungan bersumber, lalu cek kesesuaian, pengalaman terbaru dan persetujuan kontak pelanggan.'],
                 'account_id': None, 'focus_account_id': context.deal.account_id,
                 'reference_requests': request_observations}]
    snapshot = date.fromisoformat(context.snapshot_date)
    focus = accounts.get(context.deal.account_id)
    request_interaction_ids = {row.values['interaction_id'] for row in requests}
    feature_context = []
    for edge in context.graph.edges:
        if (edge.source in request_interaction_ids and edge.relation in {'mentions', 'possibly_mentions_feature'}
                and edge.target in dataset.by_id['features.csv']):
            feature_context.append({'feature_id': edge.target, 'relation': edge.relation,
                                    'interpretation_type': 'inferred',
                                    'evidence_ids': sorted(evidence_id(row) for row in _records(dataset, edge.evidence_ids))})
    findings = []
    for account_id, edges in sorted(grouped.items()):
        account = accounts[account_id]
        ids = request_ids | {evidence_id(account)}
        ids.update(identifier for item in feature_context for identifier in item['evidence_ids'])
        missing = ['Kesesuaian kandidat dengan kebutuhan prospek belum dikonfirmasi.',
                   'Pengalaman terbaru pelanggan perlu dikonfirmasi; usage/indikator CRM bukan penilaian kelayakan.',
                   'Kesediaan memberi referensi dan persetujuan untuk dihubungi belum tersedia.']
        relationships = []
        features = {item['feature_id'] for item in feature_context}
        for edge in edges:
            records = _records(dataset, edge.evidence_ids)
            resolved_ids = sorted(evidence_id(row) for row in records)
            ids.update(resolved_ids)
            if len(resolved_ids) != len(set(edge.evidence_ids)):
                missing.append(f'Bukti relasi {edge.relation} belum seluruhnya dapat di-resolve.')
            relationships.append({'relation': edge.relation, 'interpretation_type': 'inferred',
                                  'evidence_ids': resolved_ids})
            if edge.relation == 'related_account_feature_usage':
                features.update(row.values['feature_id'] for row in records
                                if row.source_file.endswith('/feature_usage_monthly.csv')
                                and row.values.get('account_id') == account_id)
        usage = [_latest_usage(dataset, account_id, feature_id, snapshot) for feature_id in sorted(features)]
        for observation in usage:
            ids.update(observation['evidence_ids'])
            if observation['observation_status'] == 'missing':
                missing.append(f'Usage {observation["feature_id"]} bulan lengkap terakhir {observation["month"]} tidak tersedia/lengkap; nilai belum diketahui.')
        current_contacts = []
        for person in dataset.tables['crm_contacts.csv']:
            if person.values.get('account_id_saat_ini') != account_id:
                continue
            histories = [row for row in _histories(context, dataset, person.values['contact_id'], account_id) if _active(row, snapshot)]
            observation = {**_contact(person), 'active_employments': [_employment(row) for row in histories],
                           'active_employment_verified': True if histories else None}
            current_contacts.append(observation)
            ids.add(evidence_id(person))
            ids.update(evidence_id(row) for row in histories)
            if not histories:
                missing.append(f'Masa kerja aktif {person.values["contact_id"]} pada akun saat ini belum terverifikasi.')
        if not current_contacts:
            missing.append('Kontak akun saat ini belum tersedia dalam CRM.')
        overlap_paths = _overlap_paths(context, dataset, account_id, edges)
        for path in overlap_paths:
            ids.update(path['evidence_ids'])
            if not path['current_focus_employments'] or not path['current_candidate_employments']:
                missing.append('Jalur overlap belum memiliki masa kerja aktif terverifikasi untuk kedua kontak saat ini.')
        if any(edge.relation == 'related_account_work_overlap' for edge in edges):
            missing.append('Overlap masa kerja tidak membuktikan saling kenal; hubungan pribadi dan izin pengantar belum dikonfirmasi.')
            if not overlap_paths:
                missing.append('Jalur overlap kanonis dengan kontak/masa kerja saat ini belum dapat dilengkapi.')
        comparison = {'focus': _account(focus) if focus else None, 'candidate': _account(account)}
        if focus:
            ids.add(evidence_id(focus))
        fact = ('Pesan pelanggan meminta referensi: ' + ' '.join(row.values.get('isi') or '' for row in requests)
                + f' CRM mencatat {account.values.get("nama")} ({account_id}), industri {account.values.get("industri")},'
                f' {account.values.get("jumlah_outlet")} outlet.')
        for observation in usage:
            count = observation['active_users']
            if observation['evidence_ids']:
                fact += (f' Usage {observation["feature_id"]} {observation["month"]} mencatat '
                         + (f'{count} pengguna aktif.' if count is not None else 'pengguna aktif tidak diisi.'))
        for path in overlap_paths:
            fact += (f' Riwayat {path["focus_contact"]["name"]} dan {path["candidate_contact"]["name"]}'
                     f' di {path["organization"]} menghasilkan overlap {path["valid_from"]} sampai {path["valid_to"] or "tanggal akhir belum tercatat"}.')
            fact += (f' CRM saat ini mengaitkan {path["candidate_contact"]["name"]}'
                     f' ({path["candidate_contact"]["role"]}) dengan {account.values.get("nama")} ({account_id}).')
            for employment in path['current_candidate_employments']:
                fact += f' Riwayat masa kerja aktif di akun tersebut mulai {employment["valid_from"]}.'
        findings.append({'finding_id': f'{context.deal.deal_id}:reference:{account_id}',
                         'category': 'data_gap', 'fact': fact, 'evidence_ids': sorted(ids),
                         'interpretation_type': 'inferred',
                         'interpretation': 'Relasi kanonis mendukung kandidat untuk pemeriksaan referensi, bukan ranking, kelayakan, perkenalan atau kesediaan pelanggan.',
                         'missing_information': sorted(set(missing)),
                         'follow_up_implication': ['Periksa kesesuaian industri, skala dan kebutuhan; konfirmasikan pengalaman terbaru serta persetujuan kontak sebelum memakai kandidat sebagai referensi.'],
                         'account_id': account_id, 'candidate_account_id': account_id,
                         'focus_account_id': context.deal.account_id,
                         'reference_requests': request_observations, 'relationships': relationships,
                         'account_comparison': comparison, 'current_contacts': current_contacts,
                         'feature_context': feature_context,
                         'feature_usage': usage, 'work_overlap_paths': overlap_paths,
                         'suitability': None, 'reference_willingness': None, 'contact_consent': None})
    return findings
