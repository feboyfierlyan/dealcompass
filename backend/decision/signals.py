"""Ekstraksi sinyal deterministik dari DealContext (mode rules).

Sinyal adalah interpretasi atas bukti; setiap sinyal menyimpan evidence_id asal.
"""
import re
from dataclasses import dataclass, field

from backend.contracts import DealContext, EvidenceRecord

# Kategori hambatan satu pesan; dipakai juga sebagai criteria Choice Jev.
OBSTACLES: dict[str, str] = {
    'harga': 'Keberatan harga, tekanan harga kompetitor, atau permintaan diskon.',
    'pengambil_keputusan': 'Pengambil keputusan berubah, belum dilibatkan, atau tidak jelas.',
    'referensi': 'Calon pelanggan meminta referensi atau bukti dari pengguna serupa.',
    'kebutuhan_produk': 'Menyebut kebutuhan fitur/produk tanpa keberatan eksplisit.',
    'tanpa_hambatan': 'Pesan netral/positif tanpa hambatan.',
    'bukti_kurang': 'Pesan tidak cukup jelas untuk menyimpulkan hambatan.',
}

_DISCOUNT_RE = re.compile(r'(?:diskon|potongan(?:\s+harga)?)\s*(\d{1,3})\s*%', re.I)
_GAP_RE = re.compile(r'(\d{1,3})\s*%\s*lebih\s+murah', re.I)
_PRICE_WORDS = ('terlalu tinggi', 'terlalu mahal', 'kemahalan', 'lebih murah', 'anggaran', 'budget', 'potongan harga')
_DM_WORDS = ('keputusan pengadaan', 'ada di beliau', 'baru bergabung', 'hanya menilai sisi teknis', 'pengambil keputusan')
_REF_WORDS = ('referensi', 'rekomendasi dari pengguna', 'testimoni')
_NEED_WORDS = ('butuh', 'membutuhkan', 'perlu ')
_OK_WORDS = ('berjalan baik', 'positif', 'suka produk', 'terima kasih')

INTERACTION_FILE = 'interactions.jsonl'
DECISION_FILE = 'decision_log.csv'
EMPLOYEE_FILE = 'employees.csv'


@dataclass
class MessageObstacle:
    evidence_id: str
    category: str
    source: str  # rules | jev | replay
    note: str = ''


@dataclass
class DiscountRequest:
    evidence_id: str
    pct: int
    date: str | None


@dataclass
class DiscountApproval:
    decision_id: str
    pct: int | None
    decided_by: str
    keputusan: str
    approver_is_vp: bool | None  # None = jabatan pemutus tidak dapat diverifikasi dari konteks


@dataclass
class Signals:
    obstacles: list[MessageObstacle] = field(default_factory=list)
    discount_requests: list[DiscountRequest] = field(default_factory=list)
    competitor_gaps: list[tuple[str, int]] = field(default_factory=list)
    competitors: list[str] = field(default_factory=list)
    discount_decisions: list[DiscountApproval] = field(default_factory=list)


def is_interaction(ev: EvidenceRecord) -> bool:
    return ev.source_file.endswith(INTERACTION_FILE)


def classify_message(text: str) -> str:
    t = text.lower()
    if _DISCOUNT_RE.search(t) or any(w in t for w in _PRICE_WORDS):
        return 'harga'
    if any(w in t for w in _DM_WORDS):
        return 'pengambil_keputusan'
    if any(w in t for w in _REF_WORDS):
        return 'referensi'
    if any(w in t for w in _NEED_WORDS):
        return 'kebutuhan_produk'
    if any(w in t for w in _OK_WORDS):
        return 'tanpa_hambatan'
    return 'bukti_kurang'


def parse_pct(value: str) -> int | None:
    m = re.fullmatch(r'\s*(\d{1,3})\s*%\s*', value or '')
    return int(m.group(1)) if m else None


def vp_sales_ids(context: DealContext) -> set[str]:
    """ID karyawan berjabatan VP Sales menurut bukti employees.csv di konteks."""
    return {ev.source_id for ev in context.evidence
            if ev.source_file.endswith(EMPLOYEE_FILE) and ',VP Sales,' in ev.excerpt}


def extract(context: DealContext) -> Signals:
    s = Signals()
    s.competitors = sorted({n.label for n in context.graph.nodes if n.type.lower() in ('competitor', 'kompetitor')})
    for ev in context.evidence:
        if not is_interaction(ev):
            continue
        s.obstacles.append(MessageObstacle(ev.id, classify_message(ev.excerpt), 'rules'))
        for m in _DISCOUNT_RE.finditer(ev.excerpt):
            s.discount_requests.append(DiscountRequest(ev.id, int(m.group(1)), ev.date))
        for m in _GAP_RE.finditer(ev.excerpt):
            s.competitor_gaps.append((ev.id, int(m.group(1))))
    vps = vp_sales_ids(context)
    for d in context.candidate_decisions:
        if d.get('deal_id') == context.deal.deal_id and d.get('tipe') == 'diskon':
            by = d.get('diputuskan_oleh', '')
            s.discount_decisions.append(DiscountApproval(
                decision_id=d.get('decision_id', ''), pct=parse_pct(d.get('nilai', '')),
                decided_by=by, keputusan=d.get('keputusan', ''),
                approver_is_vp=(by in vps) if vps else None))
    return s
