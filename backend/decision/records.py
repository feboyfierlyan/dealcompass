"""Normalisasi EvidenceRecord dari produsen konteks (Bima) menjadi field terstruktur.

Kontrak v1 (klarifikasi Main): excerpt row sumber = string JSON object dari
field row asli. Interaksi: `isi` = pesan, `account_id` = pemilik, `subjek` =
metadata. Agregat usage = inferred. Tidak ada parsing berbasis posisi koma.
"""
import json
from dataclasses import dataclass, field

from backend.contracts import DealContext, EvidenceRecord


@dataclass
class Record:
    evidence_id: str
    file: str            # nama file sumber, mis. interactions.jsonl
    source_id: str
    date: str | None
    evidence_type: str
    fields: dict = field(default_factory=dict)
    parse_error: str | None = None

    def get(self, key: str, default: str = '') -> str:
        value = self.fields.get(key)
        return default if value is None else str(value)

    @property
    def text(self) -> str:
        """Isi pesan untuk interaksi; selain itu string kosong (bukan seluruh JSON)."""
        return self.get('isi') if self.file == 'interactions.jsonl' else ''


def parse(ev: EvidenceRecord) -> Record:
    rec = Record(ev.id, ev.source_file.rsplit('/', 1)[-1], ev.source_id, ev.date, ev.evidence_type)
    try:
        data = json.loads(ev.excerpt)
    except (TypeError, ValueError) as e:
        rec.parse_error = f'excerpt {ev.id} bukan JSON object: {type(e).__name__}'
        return rec
    if not isinstance(data, dict):
        rec.parse_error = f'excerpt {ev.id} bukan JSON object'
        return rec
    rec.fields = data
    return rec


class ContextIndex:
    """Indeks baca-saja atas DealContext; tidak memuat dataset sendiri."""

    def __init__(self, context: DealContext):
        self.context = context
        self.deal = context.deal
        self.records = [parse(e) for e in context.evidence]
        self.by_id = {r.evidence_id: r for r in self.records}
        self.parse_errors = [r.parse_error for r in self.records if r.parse_error and r.evidence_type == 'direct']
        self._by_file_pk: dict[tuple[str, str], list[Record]] = {}
        for r in self.records:
            self._by_file_pk.setdefault((r.file, r.source_id), []).append(r)

    def find(self, file: str, source_id: str) -> Record | None:
        rows = self._by_file_pk.get((file, source_id))
        return rows[0] if rows else None

    def rows(self, file: str) -> list[Record]:
        return [r for r in self.records if r.file == file and not r.parse_error]

    # --- akun fokus vs akun lain -------------------------------------------------
    def focus_interactions(self) -> list[Record]:
        """Interaksi milik akun/deal fokus saja (field account_id), urut tanggal lalu ID."""
        acc = self.deal.account_id
        out = [r for r in self.rows('interactions.jsonl') if r.get('account_id') == acc]
        return sorted(out, key=lambda r: (r.get('tanggal'), r.source_id))

    def focus_decisions(self) -> list[dict]:
        return [d for d in self.context.candidate_decisions
                if d.get('deal_id') == self.deal.deal_id or d.get('account_id') == self.deal.account_id]

    def deal_record(self, deal_id: str | None = None) -> Record | None:
        return self.find('crm_deals.csv', deal_id or self.deal.deal_id)

    def competitor_of(self, deal_id: str) -> str:
        rec = self.deal_record(deal_id)
        return rec.get('kompetitor').strip() if rec else ''

    def employee_title(self, employee_id: str) -> str | None:
        rec = self.find('employees.csv', employee_id)
        return rec.get('jabatan') if rec else None

    def vp_sales_ids(self) -> set[str]:
        return {r.get('employee_id') for r in self.rows('employees.csv') if r.get('jabatan') == 'VP Sales'}

    def account(self, account_id: str) -> Record | None:
        return self.find('crm_accounts.csv', account_id)

    def related_accounts(self) -> dict[str, list[tuple[str, list[str]]]]:
        """related_account_<alasan> dari deal fokus: {account_id: [(alasan, evidence_ids)]}."""
        out: dict[str, list[tuple[str, list[str]]]] = {}
        for e in self.context.graph.edges:
            if e.source == self.deal.deal_id and e.relation.startswith('related_account_'):
                out.setdefault(e.target, []).append((e.relation.removeprefix('related_account_'), e.evidence_ids))
        return out

    def contacts_at(self, account_id: str) -> list[Record]:
        return [r for r in self.rows('crm_contacts.csv') if r.get('account_id_saat_ini') == account_id]

    def employment(self, contact_id: str) -> list[Record]:
        rows = [r for r in self.rows('contact_employment_history.csv') if r.get('contact_id') == contact_id]
        return sorted(rows, key=lambda r: r.get('mulai'))
