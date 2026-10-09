"""Ekstraksi sinyal deterministik (mode rules) untuk akun/deal FOKUS saja.

Bukti akun lain hanya dipakai untuk preseden/pembandingan (precedents.py),
tidak pernah menjadi hambatan, permintaan, atau approval deal fokus.
"""
import re
from dataclasses import dataclass, field

from backend.decision.records import ContextIndex

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
_REJECT_RE = re.compile(r'\b(?:ditolak|tidak\s+disetujui|menolak)\b', re.I)
_APPROVE_RE = re.compile(r'\b(?:disetujui|menyetujui|sudah\s+setuju|approved?)\b', re.I)
_PRICE_WORDS = ('terlalu tinggi', 'terlalu mahal', 'kemahalan', 'lebih murah', 'anggaran', 'budget', 'potongan harga')
_DM_WORDS = ('keputusan pengadaan', 'ada di beliau', 'baru bergabung', 'hanya menilai sisi teknis', 'pengambil keputusan')
_REF_WORDS = ('referensi', 'rekomendasi dari pengguna', 'testimoni')
_NEED_WORDS = ('butuh', 'membutuhkan', 'perlu ')
_OK_WORDS = ('berjalan baik', 'positif', 'suka produk', 'terima kasih')


@dataclass
class MessageObstacle:
    evidence_id: str
    source_id: str
    date: str
    category: str
    source: str  # rules | jev | replay


@dataclass
class DiscountMention:
    evidence_id: str
    source_id: str
    pct: int
    date: str
    kind: str  # request | approval_claim | rejection_claim (klaim di pesan, bukan keputusan tercatat)


@dataclass
class DiscountDecision:
    decision_id: str
    pct: int | None  # None = nilai kosong/tidak terbaca -> unknown, tidak pernah approval
    raw_value: str
    decided_by: str
    keputusan: str  # Disetujui | Ditolak | Menunggu
    approver_title: str | None  # None = jabatan pemutus tidak ada di konteks


@dataclass
class Signals:
    obstacles: list[MessageObstacle] = field(default_factory=list)
    discount_mentions: list[DiscountMention] = field(default_factory=list)
    competitor_gaps: list[tuple[str, int]] = field(default_factory=list)
    competitor: str = ''
    discount_decisions: list[DiscountDecision] = field(default_factory=list)
    out_of_scope_decisions: list[tuple[dict, str]] = field(default_factory=list)
    vp_sales_ids: set[str] = field(default_factory=set)

    @property
    def discount_requests(self) -> list[DiscountMention]:
        return [m for m in self.discount_mentions if m.kind == 'request']


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


def mention_kind(text: str) -> str:
    if _REJECT_RE.search(text):
        return 'rejection_claim'
    if _APPROVE_RE.search(text):
        return 'approval_claim'
    return 'request'


def parse_pct(value: str) -> int | None:
    m = re.fullmatch(r'\s*(\d{1,3})\s*%\s*', value or '')
    return int(m.group(1)) if m else None


def extract(idx: ContextIndex) -> Signals:
    s = Signals(competitor=idx.competitor_of(idx.deal.deal_id), vp_sales_ids=idx.vp_sales_ids())
    seen: set[tuple[str, int]] = set()
    for r in idx.focus_interactions():
        text = r.text
        s.obstacles.append(MessageObstacle(r.evidence_id, r.source_id, r.get('tanggal'), classify_message(text), 'rules'))
        for m in _DISCOUNT_RE.finditer(text):
            key = (r.source_id, int(m.group(1)))
            if key not in seen:  # satu pesan + persentase = satu mention
                seen.add(key)
                s.discount_mentions.append(DiscountMention(r.evidence_id, r.source_id, key[1], r.get('tanggal'), mention_kind(text)))
        for m in _GAP_RE.finditer(text):
            s.competitor_gaps.append((r.evidence_id, int(m.group(1))))
    scoped, other = idx.focus_decisions()
    for d in scoped:
        if d.get('tipe') == 'diskon':
            by = d.get('diputuskan_oleh', '')
            s.discount_decisions.append(DiscountDecision(
                d.get('decision_id', ''), parse_pct(d.get('nilai', '')), d.get('nilai', ''), by,
                d.get('keputusan', ''), idx.employee_title(by)))
    s.out_of_scope_decisions = [(d, why) for d, why in other if d.get('tipe') == 'diskon']
    return s
