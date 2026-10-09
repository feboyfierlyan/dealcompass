"""Pembandingan preseden deterministik.

Preseden hanya diambil dari context.candidate_decisions. Field dibaca dari
row terstruktur (records.py). Preseden bukan izin otomatis dan satu
keberhasilan lama bukan jaminan.
"""
import re
from dataclasses import dataclass, field

from backend.decision import policy
from backend.decision.records import ContextIndex
from backend.decision.signals import Signals, parse_pct

_PILOT_RE = re.compile(r'pilot\s+(\d+)\s+outlet', re.I)
_LIMIT_RE = re.compile(r'batas\s+(\d{1,3})\s*%', re.I)
COCOK, SEBAGIAN = 3, 2  # ambang skor; skor dijelaskan di facts/interpretations


@dataclass
class PrecedentAssessment:
    decision_id: str
    fit: str  # cocok | sebagian | tidak_cocok
    score: int = 0
    facts: list[str] = field(default_factory=list)
    interpretations: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    scenario: dict | None = None


def deal_outlets(idx: ContextIndex) -> int | None:
    rec = idx.deal_record()
    raw = rec.get('outlet') if rec else ''
    return int(raw) if raw.isdigit() else None


def is_open_commitment(decision: dict) -> bool:
    return decision.get('status_janji', '').startswith('Belum') or decision.get('keputusan') == 'Menunggu'


def assess(idx: ContextIndex, decision: dict, signals: Signals, trust_accounts: set[str] = frozenset()) -> PrecedentAssessment:
    did = decision.get('decision_id', '')
    tipe, nilai, keputusan = decision.get('tipe', ''), decision.get('nilai', ''), decision.get('keputusan', '')
    acc, prec_deal = decision.get('account_id', ''), decision.get('deal_id', '')
    a = PrecedentAssessment(decision_id=did, fit='tidak_cocok')
    for rec in (idx.find('decision_log.csv', did), idx.deal_record(prec_deal) if prec_deal else None):
        if rec:
            a.evidence_ids.append(rec.evidence_id)
    a.facts.append(f"{did} ({decision.get('tanggal', '?')}, {tipe}, akun {acc or '?'}): "
                   f"{nilai or '-'} -> {keputusan} oleh {decision.get('diputuskan_oleh') or '?'}; "
                   f"alasan: {decision.get('alasan') or '-'}")
    if decision.get('status_janji'):
        a.facts.append(f"{did}: janji fitur {decision.get('fitur_dijanjikan') or '?'} berstatus '{decision['status_janji']}'.")

    if decision.get('diminta_oleh') and decision.get('diminta_oleh') == idx.deal.owner_id:
        a.facts.append(f'{did} diajukan oleh pemilik deal yang sama ({idx.deal.owner_id}).')
        a.score += 1
    prec_comp = idx.competitor_of(prec_deal) if prec_deal else ''
    if signals.competitor and prec_comp == signals.competitor:
        a.facts.append(f'Deal preseden {prec_deal} juga mencatat kompetitor {prec_comp} (crm_deals.kompetitor).')
        a.score += 2

    requested = sorted({m.pct for m in signals.discount_requests})
    pct = parse_pct(nilai)
    if tipe == 'diskon' and pct is not None and requested:
        if pct in requested:
            a.score += 2
            a.interpretations.append(
                f'Permintaan {pct}% pada deal ini sama dengan {did} yang ditolak; preseden ini tidak mendukung '
                'asumsi bahwa permintaan sekarang akan disetujui; keputusan tetap wewenang VP Sales.'
                if keputusan == 'Ditolak' else
                f'Nilai {pct}% sama dengan {did} ({keputusan}), tetapi keputusan lama tidak berlaku otomatis untuk deal ini.')
        elif policy.requires_vp_approval(pct) and any(policy.requires_vp_approval(p) for p in requested):
            a.score += 1
            a.interpretations.append(f'{did}: diskon {pct}% (>10%) {keputusan.lower()}; berbeda dari permintaan {requested}%.')
        lim = _LIMIT_RE.search(decision.get('alasan', ''))
        if lim:
            a.interpretations.append(
                f'Alasan {did} menyebut batas {lim.group(1)}%; ini catatan satu keputusan, bukan aturan universal. '
                f'Aturan tertulis: diskon >{policy.DISCOUNT_APPROVAL_THRESHOLD_PCT}% butuh {policy.DISCOUNT_APPROVER_ROLE}.')

    package = next((p for p in policy.PACKAGE_OUTLET_LIMITS if p.lower() in nilai.lower()), None)
    if package and signals.discount_requests:
        outlets = deal_outlets(idx)
        pilot = _PILOT_RE.search(nilai)
        limit = policy.PACKAGE_OUTLET_LIMITS[package]
        a.score += 1
        if outlets is None:
            a.interpretations.append(f'{did} memakai paket {package}, tetapi jumlah outlet deal tidak tersedia.')
        elif policy.fits_package(package, outlets):
            a.interpretations.append(f'Paket {package} dapat menampung {outlets} outlet deal ini.')
        else:
            pilot_n = min(limit, outlets)
            a.interpretations.append(
                f'Paket {package} (maks {limit} outlet) TIDAK dapat langsung menampung {outlets} outlet deal ini. '
                f'Meniru {did} berarti pilot sebagian outlet: usulan skenario, belum disetujui pelanggan maupun VP Sales.')
            a.scenario = {
                'label': 'SKENARIO_USULAN', 'package': package, 'pilot_outlets_max': pilot_n,
                'pilot_annual_value_idr': policy.annual_value_idr(pilot_n),
                'precedent_pilot_outlets': int(pilot.group(1)) if pilot else None,
                'remaining_outlets': outlets - pilot_n,
                'upgrade_package_for_full': policy.smallest_package(outlets),
            }
        if keputusan == 'Disetujui':
            a.interpretations.append(f'{did} adalah pengecualian yang diputuskan; satu keberhasilan lama bukan jaminan.')

    if acc in trust_accounts and is_open_commitment(decision):
        a.score += 2
        a.interpretations.append(
            f'{did} di {acc} masih terbuka ({decision.get("status_janji") or keputusan}); relevan sebagai risiko '
            'kepercayaan karena terkait riwayat kerja pengambil keputusan (inferensi), bukan pola harga.')

    a.fit = 'cocok' if a.score >= COCOK else 'sebagian' if a.score >= SEBAGIAN else 'tidak_cocok'
    if a.scenario and a.fit == 'cocok':
        a.fit = 'sebagian'  # syarat preseden (kapasitas paket) tidak terpenuhi langsung
    return a
