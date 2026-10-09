"""Snapshot graph and evidence lookup; no decision or approval inference."""
from collections import defaultdict
from datetime import date
from functools import lru_cache
import calendar
import json
import re

import networkx as nx

from backend.contracts import DealContext, EvidenceGraph, EvidenceRecord, GraphEdge, GraphNode
from backend.ingestion.dataset import Dataset, SNAPSHOT_DATE, SourceRecord, get_dataset
from backend.ingestion.deals import deal_summary


def _iso(value):
    return value.isoformat() if isinstance(value, date) else value

def _line_locator(rows):
    """Compress exact physical row starts into a readable CSV locator."""
    lines = sorted(row.line for row in rows)
    ranges = []
    start = end = lines[0]
    for line in lines[1:]:
        if line == end + 1:
            end = line
        else:
            ranges.append(str(start) if start == end else f'{start}-{end}')
            start = end = line
    ranges.append(str(start) if start == end else f'{start}-{end}')
    return 'lines:' + ','.join(ranges)



class ContextGraph:
    """Historical events plus current master data at the one supported snapshot."""

    def __init__(self, dataset: Dataset):
        self.dataset = dataset
        self.graph = nx.MultiDiGraph(snapshot_date=SNAPSHOT_DATE.isoformat())
        self.evidence: dict[str, EvidenceRecord] = {}
        self._sources: dict[str, list[SourceRecord]] = {}
        self._node_accounts = defaultdict(set)
        self._node_evidence = defaultdict(set)
        self._issues = defaultdict(set)
        self._histories = defaultdict(list)
        self._build()

    def _rows(self, filename, date_field=None):
        for row in self.dataset.tables[filename]:
            when = row.values.get(date_field) if date_field else None
            if when is None or when <= SNAPSHOT_DATE:
                yield row

    def _evidence(self, row):
        eid = f'{row.source_file.rsplit("/", 1)[-1]}:{row.source_id}'
        if eid not in self.evidence:
            when = next((row.values.get(k) for k in ('tanggal', 'dibuat', 'mulai', 'tanggal_rilis')
                         if isinstance(row.values.get(k), date)), None)
            self.evidence[eid] = EvidenceRecord(
                id=eid, source_file=row.source_file, source_id=row.source_id,
                date=_iso(when), excerpt=json.dumps(row.raw, ensure_ascii=False), evidence_type='direct',
            )
            self._sources[eid] = [row]
        return eid

    def _node(self, nid, label, kind, accounts=(), evidence_ids=()):
        if nid not in self.graph:
            self.graph.add_node(nid, id=nid, label=label, type=kind)
        self._node_accounts[nid].update(a for a in accounts if a)
        self._node_evidence[nid].update(evidence_ids)

    def _record_node(self, row, nid, label, kind, accounts=()):
        self._node(nid, label, kind, accounts, [self._evidence(row)])

    def _edge(self, source, target, relation, evidence_ids, kind='direct', start=None, end=None):
        if source not in self.graph or target not in self.graph:
            raise ValueError(f'Graph endpoints missing: {source} -> {target} ({relation})')
        eid = f'{relation}:{source}:{target}:{";".join(evidence_ids)}'
        edge = GraphEdge(id=eid, source=source, target=target, relation=relation,
                         evidence_ids=evidence_ids, evidence_type=kind,
                         valid_from=_iso(start), valid_to=_iso(end))
        self.graph.add_edge(source, target, key=eid, **edge.model_dump())

    def _link(self, row, source, target, relation, start=None, end=None):
        if not target:
            return
        if target not in self.graph:
            account = row.values.get('account_id') or row.values.get('account_id_saat_ini') or ''
            self._issues[account].add(f'{row.source_file}:{row.source_id}: referensi {target} tidak tersedia.')
            return
        self._edge(source, target, relation, [self._evidence(row)], start=start, end=end)

    def _build(self):
        # Master entities are current-state records, not reconstructed historical states.
        specs = [
            ('crm_accounts.csv', 'account_id', 'nama', 'account', None),
            ('crm_contacts.csv', 'contact_id', 'nama', 'contact', 'account_id_saat_ini'),
            ('employees.csv', 'employee_id', 'nama', 'employee', None),
            ('features.csv', 'feature_id', 'nama', 'feature', None),
            ('bugs.csv', 'bug_id', 'judul', 'bug', None),
            ('outlets.csv', 'outlet_id', 'outlet_id', 'outlet', 'account_id'),
            ('crm_deals.csv', 'deal_id', 'deal_id', 'deal', 'account_id'),
            ('interactions.jsonl', 'interaction_id', 'subjek', 'interaction', 'account_id'),
            ('decision_log.csv', 'decision_id', 'decision_id', 'decision', 'account_id'),
            ('contracts_billing.csv', 'contract_id', 'contract_id', 'contract', 'account_id'),
            ('support_tickets.csv', 'ticket_id', 'judul', 'ticket', 'account_id'),
        ]
        event_fields = {'bugs.csv': 'dibuat', 'crm_deals.csv': 'dibuat',
                        'interactions.jsonl': 'tanggal', 'decision_log.csv': 'tanggal',
                        'contracts_billing.csv': 'mulai', 'support_tickets.csv': 'dibuat'}
        for filename, pk, label, kind, account_field in specs:
            for row in self._rows(filename, event_fields.get(filename)):
                v = row.values
                accounts = [v[pk]] if kind == 'account' else [v.get(account_field)] if account_field else []
                self._record_node(row, v[pk], v[label] or v[pk], kind, accounts)
        for row in self._rows('releases.csv', 'tanggal_rilis'):
            self._record_node(row, f'release:{row.values["versi"]}', row.values['versi'], 'release')
        for row in self._rows('contact_employment_history.csv', 'mulai'):
            v = row.values
            target = v['account_id'] or f'organization:{v["organisasi"]}'
            if not v['account_id']:
                self._node(target, v['organisasi'], 'organization')
            self._link(row, v['contact_id'], target, 'employed_at', v['mulai'], v['selesai'])
            self._histories[v['contact_id']].append(row)
            self._node_accounts[v['contact_id']].add(v['account_id'])
            self._node_evidence[v['contact_id']].add(self._evidence(row))

        for row in self._rows('crm_accounts.csv'):
            v = row.values
            for field, rel in [('account_owner_id', 'owned_by'), ('champion_contact_id', 'crm_champion')]:
                self._link(row, v['account_id'], v[field], rel)
                if v[field] in self.graph:
                    self._node_accounts[v[field]].add(v['account_id'])
        for row in self._rows('crm_contacts.csv'):
            v = row.values
            active = [h for h in self._histories[v['contact_id']]
                      if h.values['account_id'] == v['account_id_saat_ini']
                      and (h.values['selesai'] is None or h.values['selesai'] >= SNAPSHOT_DATE)]
            self._link(row, v['contact_id'], v['account_id_saat_ini'], 'current_crm_account',
                       min(h.values['mulai'] for h in active) if active else SNAPSHOT_DATE)
        for row in self._rows('outlets.csv'):
            self._link(row, row.values['outlet_id'], row.values['account_id'], 'outlet_of')
        for row in self._rows('crm_deals.csv', 'dibuat'):
            v = row.values
            end = v['stage_sejak'] if v['status'] != 'Terbuka' else None
            self._link(row, v['deal_id'], v['account_id'], 'deal_for', v['dibuat'], end)
            self._link(row, v['deal_id'], v['owner_id'], 'owned_by', v['dibuat'], end)
            self._node_accounts[v['owner_id']].add(v['account_id'])
        for row in self._rows('decision_log.csv', 'tanggal'):
            v = row.values
            for field, rel in [('account_id', 'decision_for'), ('deal_id', 'decision_on_deal'),
                               ('diminta_oleh', 'requested_by'), ('diputuskan_oleh', 'decided_by'),
                               ('bukti_interaction_id', 'supported_by'), ('fitur_dijanjikan', 'promises_feature')]:
                self._link(row, v['decision_id'], v[field], rel, v['tanggal'])
                if v[field] in self.graph and field in ('diminta_oleh', 'diputuskan_oleh', 'fitur_dijanjikan'):
                    self._node_accounts[v[field]].add(v['account_id'])
            self._mentions(row, v['decision_id'], ('alasan', 'nilai'))
        for row in self._rows('contracts_billing.csv', 'mulai'):
            v = row.values
            self._link(row, v['contract_id'], v['account_id'], 'contract_for', v['mulai'], v['tanggal_renewal'])
            self._link(row, v['contract_id'], v['decision_id'], 'contract_decision', v['mulai'], v['tanggal_renewal'])
        for row in self._rows('bugs.csv', 'dibuat'):
            v = row.values
            self._link(row, v['bug_id'], v['fitur_terkait'], 'affects_feature', v['dibuat'], v['selesai'])
            self._link(row, v['bug_id'], f'release:{v["versi_terdampak"]}', 'affects_version', v['dibuat'], v['selesai'])
        for row in self._rows('support_tickets.csv', 'dibuat'):
            v = row.values
            for field, rel in [('account_id', 'ticket_for'), ('outlet_id', 'reported_at'),
                               ('pelapor_contact_id', 'reported_by'), ('bug_id', 'linked_bug')]:
                self._link(row, v['ticket_id'], v[field], rel, v['dibuat'], v['diselesaikan'])
            self._link(row, v['ticket_id'], f'release:{v["versi_aplikasi"]}', 'observed_version', v['dibuat'])
        self._build_interactions()
        self._build_overlap()
        self._build_usage()

    def _mentions(self, row, source, fields):
        text = ' '.join(str(row.values.get(f) or '') for f in fields)
        for target in sorted(set(re.findall(r'\b(?:FEAT-\d+|BUG-\d+|DL-\d+|D-\d{4}-\d+|[CP]\d{2})\b', text))):
            self._link(row, source, target, 'mentions')
            if target in self.graph:
                self._node_accounts[target].add(row.values.get('account_id'))
        # Lexical feature matches are search candidates, not asserted requirements.
        stop = {'manajemen', 'multi-gudang', 'integrasi', 'dashboard', 'program', 'pelanggan', 'sinkronisasi', 'jurnal', 'accurate', 'pajak'}
        for feature in self._rows('features.csv'):
            words = set(re.findall(r'[\w-]+', feature.values['nama'].lower())) - stop
            words = {w for w in words if len(w) >= 4 and w not in {'mode', 'modul', 'resep', 'batch', 'obat', 'inti'}}
            if any(re.search(r'(?<!\w)' + re.escape(w) + r'(?!\w)', text.lower()) for w in words):
                fid = feature.values['feature_id']
                self._edge(source, fid, 'possibly_mentions_feature', [self._evidence(row), self._evidence(feature)], 'inferred', row.values.get('tanggal'))
                self._node_accounts[fid].add(row.values.get('account_id'))

    def _build_interactions(self):
        email_people = defaultdict(list)
        contacts = self.dataset.by_id['crm_contacts.csv']
        for filename, pk in [('crm_contacts.csv', 'contact_id'), ('employees.csv', 'employee_id')]:
            for person in self._rows(filename):
                if person.values['email']:
                    email_people[person.values['email']].append((person.values[pk], person))
        for row in self._rows('interactions.jsonl', 'tanggal'):
            v = row.values
            iid, account, when = v['interaction_id'], v['account_id'], v['tanggal']
            self._link(row, iid, account, 'interaction_for', when)
            self._link(row, iid, v['membalas_id'], 'replies_to', when)
            for participant in (v['peserta'] or '').split(';'):
                self._link(row, iid, participant.strip(), 'participant', when)
                if participant.strip() in self.graph:
                    self._node_accounts[participant.strip()].add(account)
            for field, relation in [('dari', 'sent_from'), ('ke', 'sent_to')]:
                for address in (v[field] or '').split(';'):
                    address = address.strip().lower()
                    if not address:
                        continue
                    email_node = f'email:{address}'
                    self._node(email_node, address, 'email', [account])
                    self._edge(iid, email_node, relation, [self._evidence(row)], start=when)
                    exact = email_people.get(address, [])
                    if len(exact) == 1:
                        pid, person = exact[0]
                        self._edge(email_node, pid, 'current_email_identity', [self._evidence(person)])
                        self._node_accounts[pid].add(account)
                        continue
                    # A former corporate address is only a candidate identity. Require
                    # both an exact local-part and employment in this account on that day.
                    candidates = []
                    for cid, person in contacts.items():
                        if (person.values['email'] or '').split('@')[0] != address.split('@')[0]:
                            continue
                        for history in self._histories[cid]:
                            h = history.values
                            if account and h['account_id'] == account and h['mulai'] <= when and (h['selesai'] is None or when <= h['selesai']):
                                candidates.append((cid, person, history))
                    identities = {c[0] for c in candidates}
                    if len(identities) == 1:
                        cid, person, history = candidates[0]
                        self._edge(email_node, cid, 'possible_historical_email_identity',
                                   [self._evidence(row), self._evidence(person), self._evidence(history)],
                                   'inferred', history.values['mulai'], history.values['selesai'])
                        self._node_accounts[cid].add(account)
                        self._issues[account].add(f'Identitas {address} → {cid} inferred dari local-part dan riwayat kerja; belum dikonfirmasi langsung.')
                    else:
                        self._issues[account or ''].add(f'Identitas email {address} belum dapat di-resolve secara unik pada {when.isoformat()}.')
            self._mentions(row, iid, ('subjek', 'isi'))

    def _build_overlap(self):
        organizations = defaultdict(list)
        for histories in self._histories.values():
            for row in histories:
                organizations[row.values['account_id'] or row.values['organisasi']].append(row)
        for rows in organizations.values():
            for i, first in enumerate(rows):
                for second in rows[i + 1:]:
                    a, b = first.values, second.values
                    if a['contact_id'] == b['contact_id']:
                        continue
                    start = max(a['mulai'], b['mulai'])
                    ends = [d for d in (a['selesai'], b['selesai']) if d is not None]
                    end = min(ends) if ends else None
                    if start > (end or SNAPSHOT_DATE):
                        continue
                    self._edge(a['contact_id'], b['contact_id'], 'overlapping_employment',
                               [self._evidence(first), self._evidence(second)], 'inferred', start, end)

    def _build_usage(self):
        for row in self.dataset.tables['feature_usage_monthly.csv']:
            v = row.values
            start = date.fromisoformat(v['bulan'] + '-01')
            end = date(start.year, start.month, calendar.monthrange(start.year, start.month)[1])
            # A monthly total cannot be known before the month is complete.
            if end >= SNAPSHOT_DATE:
                continue
            nid = f'feature-usage:{row.source_id}'
            self._record_node(row, nid, f'{v["bulan"]}: {v["pengguna_aktif"]} pengguna aktif', 'feature_usage', [v['account_id']])
            self._link(row, nid, v['account_id'], 'feature_usage_for', start, end)
            self._link(row, nid, v['feature_id'], 'measures_feature', start, end)
        groups = defaultdict(list)
        for row in self._rows('product_usage_daily.csv', 'tanggal'):
            v = row.values
            groups[(v['account_id'], v['tanggal'].strftime('%Y-%m'), v['versi_aplikasi'])].append(row)
        for (account, month, version), rows in groups.items():
            source_id = f'account_id={account};bulan={month};versi_aplikasi={version}'
            eid = f'product_usage_daily.csv:aggregate:{source_id}'
            values = [r.values for r in rows]
            offline = [v['transaksi_offline_tersinkron'] for v in values if v['transaksi_offline_tersinkron'] is not None]
            summary = dict(account_id=account, bulan=month, versi_aplikasi=version,
                           record_count=len(rows), jumlah_transaksi=sum(v['jumlah_transaksi'] for v in values),
                           transaksi_offline_tersinkron=sum(offline) if offline else None,
                           offline_observed_count=len(offline), offline_missing_count=len(rows) - len(offline),
                           outlet_count=len({v['outlet_id'] for v in values}))
            start, end = min(v['tanggal'] for v in values), max(v['tanggal'] for v in values)
            self.evidence[eid] = EvidenceRecord(id=eid, source_file=rows[0].source_file,
                source_id=_line_locator(rows), date=end.isoformat(), excerpt=json.dumps(summary, ensure_ascii=False), evidence_type='inferred')
            self._sources[eid] = rows
            nid = f'usage:{account}:{month}:{version}'
            self._node(nid, f'{month} v{version}: {summary["jumlah_transaksi"]} transaksi server', 'usage_summary', [account], [eid])
            self._edge(nid, account, 'usage_for', [eid], 'inferred', start, end)
            release = f'release:{version}'
            if release in self.graph:
                self._edge(nid, release, 'observed_version', [eid], 'inferred', start, end)
            else:
                self._issues[account].add(f'Usage {source_id}: metadata versi {version} tidak tersedia.')

    def lookup_evidence(self, evidence_id: str) -> list[SourceRecord]:
        """Resolve a direct row or every constituent row of a computed summary."""
        return list(self._sources[evidence_id])

    def subgraph(self, account_ids: set[str]) -> tuple[EvidenceGraph, list[EvidenceRecord]]:
        selected = {nid for nid, accounts in self._node_accounts.items() if accounts & account_ids}
        # Include explicit referenced entities, but never expand through shared owners
        # into unrelated deals/accounts or through features into all usage records.
        for source in list(selected):
            for _, target, attrs in self.graph.out_edges(source, data=True):
                if self.graph.nodes[target]['type'] not in {'account', 'deal', 'decision', 'interaction', 'ticket', 'contract', 'feature_usage', 'usage_summary'}:
                    selected.add(target)
        edges = [GraphEdge(**attrs) for source, target, attrs in self.graph.edges(data=True)
                 if source in selected and target in selected]
        evidence_ids = {eid for edge in edges for eid in edge.evidence_ids}
        evidence_ids.update(eid for nid in selected for eid in self._node_evidence[nid])
        return EvidenceGraph(nodes=[GraphNode(**self.graph.nodes[nid]) for nid in sorted(selected)],
                             edges=sorted(edges, key=lambda e: e.id)), [self.evidence[eid] for eid in sorted(evidence_ids)]

    def _related_accounts(self, deal):
        v = deal.values
        account = v['account_id']
        reasons = defaultdict(list)
        accounts = self.dataset.by_id['crm_accounts.csv']
        target = accounts[account]
        if v['kompetitor']:
            for other in self._rows('crm_deals.csv', 'dibuat'):
                if other.values['account_id'] != account and other.values['kompetitor'] == v['kompetitor']:
                    reasons[other.values['account_id']].append(('same_competitor', [self._evidence(deal), self._evidence(other)]))
        industry_words = set(re.findall(r'[\w&]+', (target.values['industri'] or '').lower())) - {'klinik'}
        for other in accounts.values():
            if other.values['tipe'] == 'pelanggan' and industry_words & set(re.findall(r'[\w&]+', (other.values['industri'] or '').lower())):
                reasons[other.values['account_id']].append(('shared_industry', [self._evidence(target), self._evidence(other)]))
        current_contacts = [c.values['contact_id'] for c in self._rows('crm_contacts.csv') if c.values['account_id_saat_ini'] == account]
        for cid in current_contacts:
            for history in self._histories[cid]:
                prior = history.values['account_id']
                if prior and prior != account:
                    reasons[prior].append(('prior_employment', [self._evidence(self.dataset.by_id['crm_contacts.csv'][cid]), self._evidence(history)]))
            overlap_edges = list(self.graph.in_edges(cid, data=True)) + list(self.graph.out_edges(cid, data=True))
            for source, target_id, attrs in overlap_edges:
                if attrs['relation'] != 'overlapping_employment':
                    continue
                other_id = target_id if source == cid else source
                for history in self._histories[other_id]:
                    prior = history.values['account_id']
                    if prior and prior != account:
                        reasons[prior].append(('work_overlap', attrs['evidence_ids'] + [self._evidence(history)]))
        reference_ids = {row.values['interaction_id'] for row in self._rows('interactions.jsonl', 'tanggal')
                         if row.values['account_id'] == account
                         and re.search(r'\breferensi\b|rekomendasi dari pengguna',
                                       ' '.join(str(row.values.get(f) or '') for f in ('subjek', 'isi')), re.IGNORECASE)}
        mentioned_features = {target_id for source, target_id, attrs in self.graph.edges(data=True)
                              if source in reference_ids and self.graph.nodes[target_id]['type'] == 'feature'}
        for usage in self.dataset.tables['feature_usage_monthly.csv']:
            u = usage.values
            if u['feature_id'] not in mentioned_features or not u['pengguna_aktif'] or u['bulan'] >= SNAPSHOT_DATE.strftime('%Y-%m'):
                continue
            # One sourced example establishes usage, not suitability as a reference.
            related = u['account_id']
            if not any(kind == 'feature_usage' for kind, _ in reasons[related]):
                mention_edges = [attrs for source, target_id, attrs in self.graph.edges(data=True)
                                 if source in reference_ids and target_id == u['feature_id']]
                support = mention_edges[0]['evidence_ids'] + [self._evidence(usage)]
                reasons[related].append(('feature_usage', support))
        reasons.pop(account, None)
        return reasons

    def deal_context(self, deal_id: str) -> DealContext:
        deal = self.dataset.by_id['crm_deals.csv'].get(deal_id)
        if deal is None or deal_id not in self.graph:
            raise KeyError(deal_id)
        account_id = deal.values['account_id']
        account = self.dataset.by_id['crm_accounts.csv'][account_id]
        if deal.values['status'] != 'Terbuka' or account.values['tipe'] != 'prospek':
            raise KeyError(deal_id)
        related = self._related_accounts(deal)
        scope = {account_id, *related}
        graph, evidence = self.subgraph(scope)
        evidence_map = {e.id: e for e in evidence}
        candidates = [row for row in self._rows('decision_log.csv', 'tanggal') if row.values['account_id'] in scope]
        for decision in candidates:
            did = decision.values['decision_id']
            for kind, support in related.get(decision.values['account_id'], []):
                ids = sorted(set(support + [self._evidence(decision)]))
                graph.edges.append(GraphEdge(id=f'candidate:{deal_id}:{did}:{kind}:{";".join(ids)}',
                    source=deal_id, target=did, relation=f'candidate_precedent_{kind}', evidence_ids=ids,
                    evidence_type='inferred', valid_from=decision.values['tanggal'].isoformat()))
                evidence_map.update((eid, self.evidence[eid]) for eid in ids)
        for related_id, reasons in sorted(related.items()):
            for kind, support in reasons:
                ids = sorted(set(support))
                graph.edges.append(GraphEdge(id=f'related:{deal_id}:{related_id}:{kind}:{";".join(ids)}',
                    source=deal_id, target=related_id, relation=f'related_account_{kind}', evidence_ids=ids,
                    evidence_type='inferred'))
                evidence_map.update((eid, self.evidence[eid]) for eid in ids)
        unknowns = set(self._issues[''])
        for aid in scope:
            unknowns.update(self._issues[aid])
        if not account.values['industri']:
            unknowns.add(f'Industri {account_id} belum tersedia; keterkaitan berdasarkan industri tidak dapat dihitung.')
        if not account.values['champion_contact_id']:
            unknowns.add(f'Champion {account_id} belum tercatat di CRM; jabatan/peserta meeting bukan bukti champion atau approval.')
        if not any(r.values['account_id'] == account_id for r in self._rows('interactions.jsonl', 'tanggal')):
            unknowns.add(f'Tidak ada interaksi {account_id} dalam sumber; kebutuhan, hambatan dan pengambil keputusan belum tersedia.')
        if not any(r.values['account_id'] == account_id for r in candidates):
            unknowns.add(f'Tidak ada keputusan/approval tercatat untuk {deal_id}; permintaan bukan approval.')
        if not candidates:
            unknowns.add('Tidak ada candidate decision melalui penghubung yang tersedia; bukan bukti tidak ada risiko.')
        for candidate in candidates:
            if not candidate.values['bukti_interaction_id']:
                unknowns.add(f'{candidate.values["decision_id"]}: bukti_interaction_id kosong; bukti hanya log keputusan, bukan email rekaan.')
        if related:
            unknowns.add('Keterkaitan lintas akun dan candidate decisions adalah inferensi pencarian, bukan ranking, rekomendasi atau jaminan berlaku pada deal ini.')
        if any(e.relation == 'overlapping_employment' for e in graph.edges):
            unknowns.add('Overlap masa kerja hanya menunjukkan organisasi/periode yang sama; tidak membuktikan saling kenal atau bersedia memberi referensi.')
        if not any(r.values['account_id'] == account_id for r in self.dataset.tables['product_usage_daily.csv']):
            unknowns.add(f'{account_id} belum memiliki usage pelanggan sendiri; agregat akun lain hanya konteks referensi. Transaksi server/gejala tidak membuktikan penyebab bug.')
        feature_ids = {node.id for node in graph.nodes if node.type == 'feature'}
        for fid in feature_ids:
            feature = self.dataset.by_id['features.csv'][fid]
            if feature.values['target_terkini'] == 'Belum ditetapkan':
                unknowns.add(f'{fid}: target terkini belum ditetapkan; tidak ada tanggal rilis pasti dalam sumber.')
        return DealContext(snapshot_date=SNAPSHOT_DATE.isoformat(), deal=deal_summary(deal, self.dataset),
            evidence=[evidence_map[eid] for eid in sorted(evidence_map)], graph=graph,
            candidate_decisions=[dict(row.raw) for row in candidates], unknowns=sorted(unknowns))


@lru_cache(maxsize=1)
def get_context_graph() -> ContextGraph:
    return ContextGraph(get_dataset())
