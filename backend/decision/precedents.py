"""Pembandingan preseden deterministik.

Preseden hanya diambil dari context.candidate_decisions. Preseden bukan izin
otomatis dan satu keberhasilan lama bukan jaminan.
"""
import re
from dataclasses import dataclass, field

from backend.contracts import DealContext
from backend.decision import policy
from backend.decision.signals import Signals, parse_pct

_PILOT_RE = re.compile(r'pilot\s+(\d+)\s+outlet', re.I)
_LIMIT_RE = re.compile(r'batas\s+(\d{1,3})\s*%', re.I)


@dataclass
class PrecedentAssessment:
    decision_id: str
    fit: str  # cocok | sebagian | tidak_cocok
    facts: list[str] = field(default_factory=list)
    interpretations: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    scenario: dict | None = None


def _deal_outlets(context: DealContext) -> int | None:
    """Jumlah outlet deal dihitung balik dari annual_value (harga tetap per outlet)."""
    per_outlet_year = policy.PRICE_PER_OUTLET_MONTH_IDR * 12
    n, rem = divmod(context.deal.annual_value, per_outlet_year)
    return n if not rem else None


def _evidence_for(context: DealContext, source_id: str) -> list[str]:
    return [ev.id for ev in context.evidence if source_id and ev.source_id == source_id]


def _competitors_of_deal(context: DealContext, deal_id: str) -> set[str]:
    """Kompetitor dari bukti baris CRM deal preseden (kolom kompetitor), bila ada di konteks."""
    found = set()
    for ev in context.evidence:
        if ev.source_id == deal_id and ev.source_file.endswith('crm_deals.csv'):
            last = ev.excerpt.rsplit(',', 1)[-1].strip()
            if last:
                found.add(last)
    return found


def assess(context: DealContext, decision: dict, signals: Signals) -> PrecedentAssessment:
    did = decision.get('decision_id', '')
    tipe = decision.get('tipe', '')
    nilai = decision.get('nilai', '')
    keputusan = decision.get('keputusan', '')
    a = PrecedentAssessment(decision_id=did, fit='tidak_cocok')
    a.evidence_ids = _evidence_for(context, did) + _evidence_for(context, decision.get('deal_id', ''))
    a.facts.append(f"{did} ({decision.get('tanggal', '?')}, {tipe}, akun {decision.get('account_id', '?')}): "
                   f"{nilai or '-'} -> {keputusan} oleh {decision.get('diputuskan_oleh') or '?'}; "
                   f"alasan: {decision.get('alasan') or '-'}")
    if decision.get('status_janji'):
        a.facts.append(f"{did}: janji fitur {decision.get('fitur_dijanjikan') or '?'} berstatus '{decision['status_janji']}'.")

    points = 0
    if decision.get('diminta_oleh') and decision.get('diminta_oleh') == context.deal.owner_id:
        a.facts.append(f'{did} diajukan oleh pemilik deal yang sama ({context.deal.owner_id}).')
        points += 1
    shared = _competitors_of_deal(context, decision.get('deal_id', '')) & set(signals.competitors)
    if shared:
        a.facts.append(f"Deal preseden {decision.get('deal_id')} juga melawan {', '.join(sorted(shared))}.")
        points += 1

    requested = [r.pct for r in signals.discount_requests]
    pct = parse_pct(nilai)
    if tipe == 'diskon' and pct is not None and requested:
        if pct in requested:
            points += 2
            a.interpretations.append(
                f'Permintaan {pct}% pada deal ini identik dengan {did} yang {keputusan.lower()}; '
                'preseden ini tidak mendukung asumsi bahwa permintaan sekarang akan disetujui; keputusan tetap wewenang VP Sales.' if keputusan == 'Ditolak' else
                f'Nilai {pct}% sama dengan {did}, tetapi persetujuan lama tidak berlaku otomatis untuk deal ini.')
        else:
            points += 1
            a.interpretations.append(f'{did} memakai diskon {pct}%, berbeda dari permintaan {requested}%.')
        lim = _LIMIT_RE.search(decision.get('alasan', ''))
        if lim:
            a.interpretations.append(
                f'Alasan {did} menyebut batas {lim.group(1)}%; ini catatan satu keputusan, bukan aturan universal. '
                f'Aturan tertulis: diskon >{policy.DISCOUNT_APPROVAL_THRESHOLD_PCT}% butuh {policy.DISCOUNT_APPROVER_ROLE}.')

    package = next((p for p in policy.PACKAGE_OUTLET_LIMITS if p.lower() in nilai.lower()), None)
    if package:
        outlets = _deal_outlets(context)
        pilot = _PILOT_RE.search(nilai)
        limit = policy.PACKAGE_OUTLET_LIMITS[package]
        if outlets is None:
            a.interpretations.append(f'{did} memakai paket {package}, tetapi jumlah outlet deal tidak dapat dihitung.')
        elif policy.fits_package(package, outlets):
            points += 2
            a.interpretations.append(f'Paket {package} dapat menampung {outlets} outlet deal ini.')
        else:
            points += 1
            pilot_n = min(limit, outlets) if limit else outlets
            a.interpretations.append(
                f'Paket {package} (maks {limit} outlet) TIDAK dapat langsung menampung {outlets} outlet deal ini. '
                f'Meniru {did} berarti pilot sebagian outlet: usulan skenario, belum disetujui pelanggan maupun VP Sales.')
            a.scenario = {
                'label': 'SKENARIO_USULAN',
                'package': package,
                'pilot_outlets_max': pilot_n,
                'pilot_annual_value_idr': policy.annual_value_idr(pilot_n),
                'precedent_pilot_outlets': int(pilot.group(1)) if pilot else None,
                'remaining_outlets': outlets - pilot_n,
                'upgrade_package_for_full': policy.smallest_package(outlets),
            }
        if keputusan == 'Disetujui':
            a.interpretations.append(f'{did} adalah pengecualian yang diputuskan; satu keberhasilan lama bukan jaminan.')

    if decision.get('status_janji', '').startswith('Belum') or keputusan == 'Menunggu':
        a.interpretations.append(f'{did} masih terbuka ({decision.get("status_janji") or keputusan}); '
                                 'relevan sebagai risiko kepercayaan, bukan pola harga.')
        points = max(points, 1)

    a.fit = 'cocok' if points >= 3 else 'sebagian' if points >= 1 else 'tidak_cocok'
    if a.scenario and a.fit == 'cocok':
        a.fit = 'sebagian'  # syarat preseden (kapasitas paket) tidak terpenuhi langsung
    return a
