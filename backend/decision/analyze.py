"""ICAL decision engine: analyze_deal(context) -> Recommendation.

Pemisahan keluaran (kontrak v1 tidak punya field terpisah):
- action diawali "USULAN:" (rekomendasi, bukan fakta);
- precedent_comparison berisi baris "FAKTA | ...", "INTERPRETASI | ...", "SKENARIO | ...";
- unknowns berisi celah bukti dan kegagalan mesin.
Struktur lengkap tersedia lewat analyze_deal_trace() untuk evaluasi/UI.

Lingkup: hambatan, permintaan dan approval hanya dari akun/deal fokus
(account_id interaksi = context.deal.account_id). Bukti akun lain hanya untuk
preseden dan kandidat referensi.

Mode (DEALCOMPASS_ENGINE_MODE): auto (default; jev bila TYPESAFE_API_KEY ada,
selain itu rules) | rules | jev | replay. Jev hanya mengklasifikasi hambatan
(Choice), menilai kecocokan preseden (Score) dan memeriksa klaim approval
(Noul). Policy gate diskon selalu deterministik. Kegagalan Jev apa pun (HTTP,
respons rusak, melewati anggaran waktu) -> seluruh analisis diulang dalam
mode rules, engine_mode='rules', alasan dicatat di unknowns.
"""
import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta

from backend.contracts import DealContext, Recommendation
from backend.decision import policy
from backend.decision.precedents import PrecedentAssessment, assess, deal_outlets, is_open_commitment
from backend.decision.records import ContextIndex
from backend.decision.signals import OBSTACLES, Signals, extract, parse_pct
from backend.integrations import jev

NON_BLOCKING = {'tanpa_hambatan', 'bukti_kurang', 'kebutuhan_produk'}
FIT_LEVELS = ['tidak relevan', 'relevan sebagian', 'sangat relevan']
DEFAULT_BUDGET_S = 15.0  # di bawah batas tunggu UI 20 detik
MIN_CALL_S = 0.5
REASON_WEIGHT = {'feature_usage': 3, 'work_overlap': 3, 'prior_employment': 2, 'same_competitor': 2, 'shared_industry': 1}
MAX_REFERENCE_SHORTLIST = 3


@dataclass
class DecisionTrace:
    deal_id: str
    engine_mode: str
    analysis_status: str = 'ready'  # ready | insufficient_evidence
    main_obstacle: str = 'bukti_kurang'
    facts: list[str] = field(default_factory=list)
    interpretations: list[str] = field(default_factory=list)
    proposals: list[str] = field(default_factory=list)
    scenarios: list[dict] = field(default_factory=list)
    obstacles: list[dict] = field(default_factory=list)
    discount_mentions: list[dict] = field(default_factory=list)
    precedents: list[dict] = field(default_factory=list)
    reference_candidates: list[dict] = field(default_factory=list)
    decision_maker: dict | None = None
    calculations: dict = field(default_factory=dict)
    approvals_needed: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    validation_issues: list[str] = field(default_factory=list)
    jev_calls: list[dict] = field(default_factory=list)
    elapsed_ms: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_deal(context: DealContext) -> Recommendation:
    return analyze_deal_trace(context)[0]


def resolve_mode(explicit: str | None = None) -> str:
    mode = (explicit or os.environ.get('DEALCOMPASS_ENGINE_MODE') or 'auto').lower()
    if mode == 'auto':
        return 'jev' if os.environ.get('TYPESAFE_API_KEY') else 'rules'
    if mode not in ('rules', 'jev', 'replay'):
        raise ValueError(f'engine mode tidak dikenal: {mode}')
    return mode


def budget_s() -> float:
    try:
        return float(os.environ.get('DEALCOMPASS_ANALYSIS_BUDGET_S') or DEFAULT_BUDGET_S)
    except ValueError:
        return DEFAULT_BUDGET_S


def validate_context(context: DealContext, idx: ContextIndex) -> list[str]:
    issues = []
    ev_ids = {e.id for e in context.evidence}
    node_ids = {n.id for n in context.graph.nodes}
    for e in context.graph.edges:
        for ref in (e.source, e.target):
            if ref not in node_ids:
                issues.append(f'Edge {e.id} menunjuk node tidak ada: {ref}')
        for eid in e.evidence_ids:
            if eid not in ev_ids:
                issues.append(f'Edge {e.id} merujuk evidence_id tidak dapat di-resolve: {eid}')
    for i, d in enumerate(context.candidate_decisions):
        if not d.get('decision_id'):
            issues.append(f'candidate_decisions[{i}] tanpa decision_id; diabaikan.')
    issues.extend(idx.parse_errors)
    if idx.deal_record() is None:
        issues.append(f'Bukti crm_deals.csv:{context.deal.deal_id} tidak ada di konteks; outlet/kompetitor tidak terbaca.')
    return issues


def analyze_deal_trace(context: DealContext, mode: str | None = None, client=None,
                       diagnostic: dict | None = None) -> tuple[Recommendation, DecisionTrace]:
    """diagnostic (opsional): laporan analyze_deal_initial Bima untuk deal yang sama, dipakai untuk
    pemeriksaan silang referensi/kewenangan/approval. Tanpa diagnostic hasil tetap dari konteks saja."""
    started = time.monotonic()
    if diagnostic is not None and diagnostic.get('deal_id') != context.deal.deal_id:
        raise ValueError(f'diagnostic deal_id {diagnostic.get("deal_id")!r} tidak cocok dengan konteks {context.deal.deal_id}')
    mode = client.mode if client is not None else resolve_mode(mode)
    idx = ContextIndex(context)
    if mode == 'rules':
        rec, trace = _analyze(context, idx, 'rules', None, None, diagnostic=diagnostic)
    else:
        deadline = started + budget_s()
        failure = None
        calls_before = 0
        try:
            if client is None:
                client = jev.client_from_env(mode)
            calls_before = len(getattr(client, 'calls', []))
            rec, trace = _analyze(context, idx, mode, client, deadline, diagnostic=diagnostic)
            if len(getattr(client, 'calls', [])) == calls_before:
                failure = 'no_eligible_questions'  # P05: no provider request, no live label.
        except jev.JevError as e:
            failure = e.code
        except Exception as e:  # respons tak terduga tidak boleh menjatuhkan endpoint
            failure = f'internal_error:{type(e).__name__}'
        calls = [asdict(c) for c in getattr(client, 'calls', [])[calls_before:]] if client is not None else []
        if failure:
            reason = (f'Jev ({mode}) tidak dipanggil: no_eligible_questions.'
                      if failure == 'no_eligible_questions' else f'Jev ({mode}) gagal: {failure}.')
            rec, trace = _analyze(context, idx, 'rules', None, None, extra_unknowns=[
                reason + ' Seluruh analisis memakai rules deterministik; '
                'tidak ada label Jev yang dipakai.'], diagnostic=diagnostic)
        trace.jev_calls = calls
    trace.elapsed_ms = round((time.monotonic() - started) * 1000)
    return rec, trace


# --- Inti analisis --------------------------------------------------------------------

class _Jev:
    """Pembungkus panggilan Jev dengan anggaran waktu total."""

    def __init__(self, client, deadline):
        self.client, self.deadline = client, deadline

    def ask(self, state, questions):
        remaining = self.deadline - time.monotonic()
        if remaining < MIN_CALL_S:
            raise jev.JevError('budget_exceeded', 'anggaran waktu analisis habis')
        return self.client.ask(state, questions, timeout_s=remaining)


def _analyze(context, idx: ContextIndex, mode, client, deadline, extra_unknowns=(), diagnostic=None):
    deal = context.deal
    trace = DecisionTrace(deal_id=deal.deal_id, engine_mode=mode)
    trace.validation_issues = validate_context(context, idx)
    trace.unknowns.extend(context.unknowns)
    trace.unknowns.extend(extra_unknowns)
    trace.unknowns.extend(f'Validasi konteks: {i}' for i in trace.validation_issues)
    valid_ev = {e.id for e in context.evidence}
    used: list[str] = []

    def use(*eids):
        for eid in eids:
            if eid in valid_ev and eid not in used:
                used.append(eid)

    signals = extract(idx)
    j = _Jev(client, deadline) if client is not None else None

    # Jev fase 1: hambatan per pesan fokus + klaim approval eksplisit.
    if j:
        for o in signals.obstacles:
            ans = j.ask(idx.by_id[o.evidence_id].text, {'hambatan': jev.choice(
                'Klasifikasikan hambatan penjualan utama yang dinyatakan pesan ini. '
                'Pilih bukti_kurang bila pesan tidak cukup jelas.', OBSTACLES)})['hambatan']['choice']
            if ans != o.category:
                trace.interpretations.append(f'Jev mengklasifikasi {o.source_id} sebagai {ans}; rules: {o.category}. Label Jev dipakai.')
            o.category, o.source = ans, mode
        for eid in dict.fromkeys(m.evidence_id for m in signals.discount_mentions):
            p = j.ask(idx.by_id[eid].text, {'persetujuan_eksplisit': jev.noul(
                'Apakah pesan ini menyatakan secara eksplisit bahwa diskon SUDAH disetujui oleh pihak berwenang?')})
            p = p['persetujuan_eksplisit']['noul']
            if p >= 0.5:
                trace.unknowns.append(f'Jev menilai {idx.by_id[eid].source_id} menyiratkan persetujuan (noul={p:.2f}), '
                                      'tetapi persetujuan hanya diakui dari decision_log; tidak dianggap approval.')
    trace.obstacles = [asdict(o) for o in signals.obstacles]
    trace.discount_mentions = [asdict(m) for m in signals.discount_mentions]

    # Fakta dasar & hitungan.
    drec = idx.deal_record()
    if drec:
        use(drec.evidence_id)
    trace.facts.append(
        f'{deal.deal_id} {deal.account_name}: stage {deal.stage} sejak '
        f'{policy.stage_start(context.snapshot_date, deal.stage_age_days)} ({deal.stage_age_days} hari per '
        f'{context.snapshot_date}); nilai potensi tahunan {policy.rupiah(deal.annual_value)} (bukan pendapatan)'
        + (f'; kompetitor tercatat: {signals.competitor}.' if signals.competitor else '.'))
    outlets = deal_outlets(idx)
    if outlets is None:
        trace.unknowns.append('Jumlah outlet deal tidak terbaca dari crm_deals; hitungan paket/diskon dilewati.')
    else:
        trace.calculations.update(outlets=outlets, list_annual_value_idr=policy.annual_value_idr(outlets),
                                  smallest_package=policy.smallest_package(outlets))
        if policy.annual_value_idr(outlets) != deal.annual_value:
            trace.unknowns.append(f'annual_value {policy.rupiah(deal.annual_value)} berbeda dari {outlets} outlet x harga '
                                  f'standar ({policy.rupiah(policy.annual_value_idr(outlets))}).')

    blocking = [o for o in signals.obstacles if o.category not in NON_BLOCKING]
    for o in signals.obstacles:
        if o.category not in ('bukti_kurang', 'tanpa_hambatan'):
            use(o.evidence_id)
            trace.facts.append(f'{o.source_id} ({o.date}, {deal.account_id}): "{idx.by_id[o.evidence_id].text}"')
    trust_accounts: set[str] = set()
    if not blocking:
        trace.analysis_status = 'insufficient_evidence'
        trace.unknowns.append('Bukti interaksi akun fokus tidak cukup untuk menyimpulkan hambatan; bukan berarti tidak ada risiko.')
        trace.proposals.append(
            f'USULAN: {deal.owner_id} menjadwalkan discovery dengan {deal.account_name} untuk mengidentifikasi '
            'pengambil keputusan, kebutuhan, jumlah outlet dan anggaran sebelum menawarkan harga atau paket.')
        milestone = 'Catatan discovery pertama berisi pengambil keputusan, kebutuhan dan jadwal pengadaan.'
    else:
        latest = max(blocking, key=lambda o: (o.date or '', o.source_id))
        trace.main_obstacle = latest.category
        milestone = _PLAYBOOKS[latest.category](idx, signals, trace, use, outlets, latest, trust_accounts,
                                                diagnostic=diagnostic)

    # Preseden.
    assessments: list[PrecedentAssessment] = [assess(idx, d, signals, trust_accounts)
                                              for d in context.candidate_decisions if d.get('decision_id')]
    relevant = sorted((a for a in assessments if a.fit != 'tidak_cocok'), key=lambda a: (-a.score, a.decision_id))
    if j:
        for a in relevant:
            d = next(x for x in context.candidate_decisions if x.get('decision_id') == a.decision_id)
            state = {'deal': deal.model_dump(), 'hambatan_pesan': [
                {'source_id': o.source_id, 'isi': idx.by_id[o.evidence_id].text} for o in blocking], 'preseden': d}
            ans = j.ask(state, {'kecocokan': jev.score(
                'Seberapa cocok keputusan preseden ini sebagai pembanding untuk hambatan deal saat ini? '
                'Preseden bukan izin otomatis.', FIT_LEVELS)})['kecocokan']
            a.interpretations.append(f'Jev Score kecocokan {a.decision_id}: {FIT_LEVELS[int(round(ans["score"]))]} '
                                     '(penilaian relevansi, bukan probabilitas closing).')
    comparison = []
    for a in assessments:
        trace.precedents.append(asdict(a))
    for a in relevant:
        use(*a.evidence_ids)
        comparison += [f'FAKTA | {f}' for f in a.facts]
        comparison += [f'INTERPRETASI | [{a.fit}] {i}' for i in a.interpretations]
        if a.scenario:
            trace.scenarios.append({'decision_id': a.decision_id, **a.scenario})
            s = a.scenario
            comparison.append(
                f'SKENARIO | Pilot maks {s["pilot_outlets_max"]} outlet paket {s["package"]} = '
                f'{policy.rupiah(s["pilot_annual_value_idr"])}/tahun; {s["remaining_outlets"]} outlet sisanya '
                f'butuh paket {s["upgrade_package_for_full"]}. Usulan, belum disetujui pelanggan/VP Sales.')
    skipped = [a.decision_id for a in assessments if a.fit == 'tidak_cocok']
    if skipped:
        trace.interpretations.append(f'Diperiksa tetapi tidak cocok untuk hambatan ini: {", ".join(skipped)}.')
    if not relevant:
        trace.unknowns.append('Tidak ada preseden relevan di candidate_decisions; perbandingan historis terbatas.')
    comparison = [f'FAKTA | {f}' for f in trace.facts] + comparison + [f'INTERPRETASI | {i}' for i in trace.interpretations]

    trace.evidence_ids = used
    trace.approvals_needed = list(dict.fromkeys(trace.approvals_needed))
    rec = Recommendation(
        deal_id=deal.deal_id, action=' '.join(trace.proposals), owner_id=deal.owner_id or None,
        milestone=milestone, evidence_ids=used, precedent_ids=[a.decision_id for a in relevant],
        precedent_comparison=comparison, approvals_needed=trace.approvals_needed,
        unknowns=list(dict.fromkeys(trace.unknowns)), engine_mode=trace.engine_mode)
    return rec, trace


# --- Playbook per hambatan --------------------------------------------------------------

def _price(idx: ContextIndex, s: Signals, trace, use, outlets, latest, trust_accounts, diagnostic=None):
    deal = idx.deal
    if s.competitor and idx.deal_record():
        use(idx.deal_record().evidence_id)
    for eid, gap in s.competitor_gaps:
        use(eid)
        trace.facts.append(f'{idx.by_id[eid].source_id}: kompetitor disebut ~{gap}% lebih murah (klaim, belum diverifikasi).')
    for m in s.discount_mentions:
        use(m.evidence_id)
        if m.kind == 'request':
            trace.facts.append(f'{m.source_id} ({m.date}): PERMINTAAN diskon {m.pct}% (permintaan, bukan approval).')
        elif m.kind == 'approval_claim':
            trace.facts.append(f'{m.source_id} ({m.date}): pesan menyebut persetujuan diskon {m.pct}%.')
            trace.unknowns.append(f'{m.source_id}: klaim persetujuan di pesan tidak dianggap approval tanpa catatan decision_log oleh VP Sales.')
        else:
            trace.facts.append(f'{m.source_id} ({m.date}): pesan menyebut penolakan diskon {m.pct}%.')

    vp = s.vp_sales_ids
    for d in s.discount_decisions:
        rec = idx.find('decision_log.csv', d.decision_id)
        if rec:
            use(rec.evidence_id)
        emp = idx.find('employees.csv', d.decided_by)
        if emp:
            use(emp.evidence_id)
        nilai = f'{d.pct}%' if d.pct is not None else f'nilai tidak terbaca ({d.raw_value!r})'
        trace.facts.append(f'{d.decision_id} (deal_id {deal.deal_id} di decision_log): keputusan diskon {nilai} = '
                           f'{d.keputusan} oleh {d.decided_by} ({d.approver_title or "jabatan tidak ada di konteks"}).')
        if d.pct is None:
            trace.unknowns.append(f'{d.decision_id}: persentase diskon kosong/tidak terbaca ({d.raw_value!r}); '
                                  'tidak dianggap approval maupun penolakan untuk persentase mana pun.')
    for d, why in s.out_of_scope_decisions:
        rec = idx.find('decision_log.csv', d.get('decision_id', ''))
        if rec:
            use(rec.evidence_id)
        trace.facts.append(f'{d.get("decision_id")}: keputusan diskon {d.get("nilai") or "-"} {d.get("keputusan")} '
                           f'di akun {d.get("account_id")} {why}.')
        trace.interpretations.append(f'{d.get("decision_id")} tidak berlaku otomatis untuk {deal.deal_id}; '
                                     'hanya boleh menjadi preseden.')
    pending = []
    for pct in sorted({m.pct for m in s.discount_requests}):
        src = next(m for m in s.discount_requests if m.pct == pct)
        if outlets is not None:
            net = policy.annual_value_idr(outlets, pct)
            trace.calculations[f'discount_{pct}pct'] = {'annual_value_idr': net, 'reduction_idr': deal.annual_value - net}
            trace.facts.append(
                f'Hitungan: {outlets} outlet x {policy.rupiah(policy.PRICE_PER_OUTLET_MONTH_IDR)} x 12 = '
                f'{policy.rupiah(policy.annual_value_idr(outlets))}; diskon {pct}% -> {policy.rupiah(net)} '
                f'(berkurang {policy.rupiah(policy.annual_value_idr(outlets) - net)}).')
        known = [d for d in s.discount_decisions if d.pct is not None]  # R7: nilai kosong tidak pernah mencakup
        approved = [d for d in known if d.keputusan == 'Disetujui' and d.approver_title == 'VP Sales' and d.pct >= pct]
        rejected = [d for d in known if d.keputusan == 'Ditolak' and d.pct == pct]
        for d in known:
            if d.keputusan != 'Disetujui':
                continue
            if d.approver_title is None:
                trace.unknowns.append(f'Jabatan pemutus {d.decision_id} ({d.decided_by}) tidak dapat diverifikasi dari konteks.')
            elif d.approver_title != 'VP Sales':
                trace.interpretations.append(f'{d.decision_id} diputuskan {d.decided_by} ({d.approver_title}), bukan VP Sales; '
                                             f'tidak sah untuk diskon >{policy.DISCOUNT_APPROVAL_THRESHOLD_PCT}%.')
            elif d.pct < pct:
                trace.interpretations.append(f'{d.decision_id} menyetujui {d.pct}%, lebih kecil dari permintaan {pct}%; '
                                             f'tidak mencakup {pct}%.')
        if not policy.requires_vp_approval(pct):
            trace.interpretations.append(f'Diskon {pct}% tidak melebihi {policy.DISCOUNT_APPROVAL_THRESHOLD_PCT}%; aturan approval VP Sales tidak berlaku.')
        elif approved:
            trace.interpretations.append(f'Diskon {pct}% untuk {deal.deal_id} sudah disetujui VP Sales dan tercatat ({approved[0].decision_id}).')
        elif rejected:
            trace.interpretations.append(f'Diskon {pct}% untuk {deal.deal_id} sudah ditolak ({rejected[0].decision_id}); jangan ditawarkan.')
        else:
            pending.append(pct)
            who = ', '.join(sorted(vp)) or 'jabatan VP Sales tidak ada di konteks'
            trace.approvals_needed.append(
                f'{policy.DISCOUNT_APPROVER_ROLE} ({who}): putuskan dan catat di decision_log permintaan diskon {pct}% '
                f'({src.source_id}, {src.date}); >{policy.DISCOUNT_APPROVAL_THRESHOLD_PCT}% wajib approval. '
                f'Belum ada keputusan sah yang tercatat untuk {deal.deal_id}.')
    if vp:
        use(*(idx.find('employees.csv', e).evidence_id for e in sorted(vp)))
    if diagnostic is not None:
        for f in diagnostic.get('findings', []):
            look = f.get('decision_lookup')
            if not look:
                continue
            n_focus = len(look.get('focus_log_evidence_ids') or [])
            trace.facts.append(f'Verifikasi Bima {f.get("finding_id")}: pencarian {look.get("inspected_record_count")} record '
                               f'decision_log menemukan {n_focus} log untuk {look.get("account_id")}/{look.get("deal_id")}.')
            if n_focus and pending:
                trace.unknowns.append('Verifikasi Bima menemukan log keputusan fokus yang tidak dibaca sebagai approval sah; '
                                      'periksa nilai/pemutus log tersebut.')

    # Ringkasan keputusan diskon >10% pada candidate_decisions (konteks, bukan seluruh log).
    big = [d for d in idx.context.candidate_decisions
           if d.get('tipe') == 'diskon' and (parse_pct(d.get('nilai', '')) or 0) > policy.DISCOUNT_APPROVAL_THRESHOLD_PCT]
    if big:
        ok = sorted(d['decision_id'] for d in big if d.get('keputusan') == 'Disetujui')
        no = sorted(d['decision_id'] for d in big if d.get('keputusan') == 'Ditolak')
        trace.facts.append(f'Di candidate_decisions konteks ini ada {len(big)} keputusan diskon >10%: '
                           f'{len(ok)} disetujui ({", ".join(ok) or "-"}), {len(no)} ditolak ({", ".join(no) or "-"}).')

    text = []
    if pending:
        pcts = '/'.join(f'{p}%' for p in pending)
        text.append(f'USULAN: Jangan menawarkan atau menjanjikan diskon {pcts} ke {deal.account_name} sebelum '
                    f'{policy.DISCOUNT_APPROVER_ROLE} memutuskan dan mencatatnya. {deal.owner_id} membawa permintaan '
                    'tersebut ke VP Sales bersama pembanding preseden.')
    else:
        text.append(f'USULAN: {deal.owner_id} menanggapi keberatan harga {deal.account_name} hanya dengan opsi yang sesuai kebijakan.')
    if outlets is not None:
        text.append(f'Siapkan opsi tanpa diskon: {outlets} outlet paket {policy.smallest_package(outlets)} harga normal '
                    f'{policy.rupiah(policy.annual_value_idr(outlets))}/tahun; pilot sebagian outlet hanya sebagai skenario '
                    'usulan yang butuh persetujuan.')
    text.append('Tanggapi keberatan harga dengan nilai produk berdasar kebutuhan yang tercatat, bukan menyamai harga kompetitor.')
    trace.proposals.append(' '.join(text))
    return ('Keputusan VP Sales atas permintaan diskon tercatat di decision_log, lalu tanggapan tertulis '
            'pelanggan atas opsi harga yang disetujui.' if pending else
            'Tanggapan tertulis pelanggan atas opsi harga yang sesuai kebijakan.')


def _decision_maker(idx: ContextIndex, s: Signals, trace, use, outlets, latest, trust_accounts, diagnostic=None):
    deal = idx.deal
    msg = idx.by_id[latest.evidence_id]
    text = msg.text.lower()
    matches = [c for c in idx.contacts_at(deal.account_id)
               if c.get('jabatan_saat_ini') and c.get('jabatan_saat_ini').lower() in text]
    if len(matches) != 1:
        trace.unknowns.append(
            f'Identitas pengambil keputusan yang disebut di {msg.source_id} belum dapat dipastikan '
            f'({len(matches)} kontak CRM {deal.account_id} cocok dengan jabatan yang disebut).')
        trace.proposals.append(
            f'USULAN: {deal.owner_id} menanyakan langsung kepada kontak saat ini siapa pengambil keputusan pengadaan '
            'dan meminta pertemuan dengannya; jangan menebak dari jabatan tertinggi.')
        return 'Nama dan peran pengambil keputusan terkonfirmasi langsung oleh pelanggan.'
    c = matches[0]
    cid, name, title = c.get('contact_id'), c.get('nama'), c.get('jabatan_saat_ini')
    use(c.evidence_id)
    history = idx.employment(cid)
    current = [h for h in history if h.get('account_id') == deal.account_id and not h.get('selesai')]
    for h in history:
        use(h.evidence_id)
    dm = {'contact_id': cid, 'name': name, 'title': title, 'evidence_type': 'inferred',
          'basis': [msg.source_id, c.source_id] + [h.source_id for h in history]}
    trace.decision_maker = dm
    since = current[0].get('mulai') if current else '?'
    trace.interpretations.append(
        f'INFERENSI: {msg.source_id} menyebut "{title}" sebagai pemegang keputusan; satu-satunya kontak CRM '
        f'{deal.account_id} dengan jabatan itu adalah {cid} {name} (mulai {since}). Belum dikonfirmasi langsung.')
    for h in history:
        if h.get('account_id') != deal.account_id:
            org = h.get('organisasi') or h.get('account_id')
            trace.facts.append(f'{cid} sebelumnya {h.get("jabatan")} di {org} ({h.get("mulai")} s.d. {h.get("selesai") or "kini"}).')
            if h.get('account_id'):
                trust_accounts.add(h.get('account_id'))
    for d in idx.context.candidate_decisions:
        if d.get('account_id') in trust_accounts and is_open_commitment(d):
            trace.interpretations.append(
                f'Risiko kepercayaan: {d["decision_id"]} di {d["account_id"]} '
                f'({d.get("fitur_dijanjikan") or d.get("nilai")}; {d.get("status_janji") or d.get("keputusan")}). '
                f'{name} mungkin mengetahui pengalaman ini (inferensi dari riwayat kerja, belum dikonfirmasi).')
    trace.proposals.append(
        f'USULAN: {deal.owner_id} meminta kontak teknis memperkenalkan dan menjadwalkan pertemuan langsung dengan '
        f'{name} ({title}, identitas inferensi yang perlu dikonfirmasi); sesuaikan proposal dengan prioritas operasional. '
        'Jawab jujur status fitur yang belum rilis dan jangan menjanjikan tanggal fitur tanpa keputusan tercatat.')
    trace.unknowns.append(f'Sikap dan kriteria {name} terhadap proposal belum tercatat di interaksi.')
    if diagnostic is not None:
        auth = [f for f in diagnostic.get('findings', []) if 'authority_contact_id' in f]
        confirmed = [f for f in auth if f.get('authority_contact_id') == cid]
        if confirmed:
            trace.facts.append(f'Verifikasi kewenangan Bima ({confirmed[0].get("finding_id")}) menunjuk kandidat yang sama: {cid} '
                               '(tetap inferred).')
        elif auth:
            trace.unknowns.append(f'Verifikasi kewenangan Bima tidak menunjuk {cid} secara unik; identitas pengambil keputusan '
                                  'perlu dikonfirmasi sebelum dipakai.')
    return f'Pertemuan dengan {name} terlaksana, perannya terkonfirmasi, dan kriteria keputusan pengadaan tercatat.'


def _contact_label(idx: ContextIndex, cid: str) -> str:
    c = idx.find('crm_contacts.csv', cid)
    return f'{cid} {c.get("nama")} ({c.get("jabatan_saat_ini")})' if c else cid


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r'[a-z0-9&]+', (text or '').lower()) if len(w) >= 3}


def _latest_complete_month(snapshot_date: str) -> str:
    first = date.fromisoformat(snapshot_date).replace(day=1)
    return (first - timedelta(days=1)).strftime('%Y-%m')


def _context_usage(idx: ContextIndex, acc_id: str, reasons) -> list[dict]:
    """Usage bulan lengkap terakhir untuk fitur yang menautkan kandidat (relasi feature_usage).

    recorded / zero / missing dibedakan; nilai bulan lama tidak dipakai sebagai kondisi terbaru.
    """
    features = sorted({idx.by_id[e].get('feature_id') for kind, ids in reasons if kind == 'feature_usage'
                       for e in ids if e in idx.by_id and idx.by_id[e].file == 'feature_usage_monthly.csv'
                       and idx.by_id[e].get('account_id') == acc_id})
    month = _latest_complete_month(idx.context.snapshot_date)
    out = []
    for feature in features:
        rec = idx.find('feature_usage_monthly.csv', f'{month}|{acc_id}|{feature}')
        raw = rec.get('pengguna_aktif') if rec else ''
        value = int(raw) if raw.isdigit() else None
        status = 'missing' if value is None else 'zero' if value == 0 else 'recorded'
        out.append({'feature_id': feature, 'month': month, 'active_users': value, 'observation_status': status,
                    'evidence_ids': [rec.evidence_id] if rec else []})
    return out


def _usage_status(value) -> str:
    return 'missing' if value is None else 'zero' if value == 0 else 'recorded'


def _reference_candidates(idx: ContextIndex, diagnostic: dict | None) -> tuple[list[dict], list[str]]:
    """Kandidat dari related_account_* konteks; dicocokkan dengan verifikasi Bima bila diagnostic tersedia.

    Urutan = urutan pemeriksaan oleh account manager, bukan penilaian kelayakan atau izin.
    """
    deal = idx.deal
    focus = idx.account(deal.account_id)
    focus_words = _words(focus.get('industri')) if focus else set()
    related = idx.related_accounts()
    diag = {c.get('candidate_account_id'): c for c in (diagnostic or {}).get('reference_candidates', [])
            if c.get('candidate_account_id')}
    notes = []
    if diagnostic is not None and diagnostic.get('reference_candidates') is not None:
        customers = {a for a in related if idx.account(a) and idx.account(a).get('tipe') == 'pelanggan'}
        only_ctx, only_diag = sorted(customers - set(diag)), sorted(set(diag) - set(related))
        if only_ctx:
            notes.append(f'Kandidat related_account {", ".join(only_ctx)} tidak ada pada verifikasi referensi Bima; '
                         'diperlakukan sebagai belum diverifikasi.')
        if only_diag:
            notes.append(f'Verifikasi Bima memuat kandidat {", ".join(only_diag)} tanpa relasi related_account di konteks; '
                         'tidak dipakai.')
    out = []
    for acc_id, reasons in sorted(related.items()):
        acc = idx.account(acc_id)
        kinds = sorted({k for k, _ in reasons})
        ev_ids = {e for _, ids in reasons for e in ids} | ({acc.evidence_id} if acc else set())
        row = {'account_id': acc_id, 'name': acc.get('nama') if acc else acc_id,
               'owner_id': acc.get('account_owner_id') if acc else None, 'relations': kinds,
               'industry': acc.get('industri') if acc else None, 'outlets': acc.get('jumlah_outlet') if acc else None,
               'health_dashboard': acc.get('health_score_dashboard') if acc else None,
               'nps_last': acc.get('nps_terakhir') if acc else None,
               'material_cautions': [], 'minor_cautions': [], 'notes': [],
               'usage': _context_usage(idx, acc_id, reasons), 'overlap_paths': [],
               'verified_by_bima': acc_id in diag if diagnostic is not None else None,
               'suitability': None, 'reference_willingness': None, 'contact_consent': None}
        if not acc or acc.get('tipe') != 'pelanggan':
            row['material_cautions'].append('bukan akun pelanggan di CRM' if acc else 'baris akun tidak ada di konteks')
        else:
            health = acc.get('health_score_dashboard')
            if health and health != 'Hijau':
                row['minor_cautions'].append(f'health dashboard {health} (indikator CRM, bisa tidak mutakhir)')
            if focus_words and not (focus_words & _words(acc.get('industri'))):
                row['minor_cautions'].append(f'industri {acc.get("industri")} berbeda dari {focus.get("industri")}; '
                                             'kemiripan perlu dicek')
        tickets = [r for r in idx.rows('support_tickets.csv') if r.get('account_id') == acc_id and r.get('status') == 'Terbuka']
        if tickets:
            ev_ids |= {t.evidence_id for t in tickets}
            bugs = sum(t.get('kategori') == 'bug' for t in tickets)
            high = sum(t.get('prioritas') in ('Tinggi', 'Kritis') for t in tickets)
            titles = sorted({t.get('judul') for t in tickets if t.get('judul')})
            summary = (f'{len(tickets)} tiket terbuka ({bugs} bug, {high} prioritas Tinggi/Kritis; '
                       f'{", ".join(t.source_id for t in tickets)}; judul: {"/".join(titles)})')
            (row['material_cautions'] if bugs or high else row['minor_cautions']).append(summary)
        for d in idx.context.candidate_decisions:
            if d.get('account_id') != acc_id:
                continue
            if is_open_commitment(d):
                row['material_cautions'].append(
                    f'{d["decision_id"]} {d.get("tipe")} masih terbuka ({d.get("status_janji") or d.get("keputusan")})')
            elif d.get('tipe') == 'eskalasi':
                row['notes'].append(f'riwayat eskalasi {d["decision_id"]}: {d.get("alasan") or d.get("nilai")} ({d.get("keputusan")})')
            else:
                continue
            rec = idx.find('decision_log.csv', d.get('decision_id', ''))
            if rec:
                ev_ids.add(rec.evidence_id)
        dc = diag.get(acc_id)
        if dc:
            bima_usage = {(u.get('feature_id'), u.get('month')): u for u in dc.get('feature_usage', [])}
            for u in row['usage']:
                b = bima_usage.get((u['feature_id'], u['month']))
                if b is not None and b.get('active_users') != u['active_users']:
                    notes.append(f'Usage {acc_id} {u["feature_id"]} {u["month"]} berbeda dari verifikasi Bima; nilai Bima dipakai.')
                    u.update(active_users=b.get('active_users'), observation_status=_usage_status(b.get('active_users')),
                             evidence_ids=list(b.get('evidence_ids', [])))
            for path in dc.get('work_overlap_paths', []):
                row['overlap_paths'].append({
                    'focus_contact': (path.get('focus_contact') or {}).get('contact_id'),
                    'candidate_contact': (path.get('candidate_contact') or {}).get('contact_id'),
                    'organization': path.get('organization'), 'valid_from': path.get('valid_from'),
                    'valid_to': path.get('valid_to'), 'acquaintance_confirmed': path.get('acquaintance_confirmed'),
                    'evidence_ids': list(path.get('evidence_ids', []))})
            for key in ('suitability', 'reference_willingness', 'contact_consent'):
                row[key] = dc.get(key)
        for u in row['usage']:
            ev_ids |= set(u['evidence_ids'])
            if u['observation_status'] == 'zero':
                row['material_cautions'].append(f'0 pengguna aktif {u["feature_id"]} pada {u["month"]} (bulan lengkap terakhir)')
            elif u['observation_status'] == 'missing':
                row['minor_cautions'].append(f'usage {u["feature_id"]} {u["month"]} tidak tersedia (unknown, bukan nol)')
        if 'work_overlap' in kinds and not row['overlap_paths']:
            people = sorted({idx.by_id[e].get('contact_id') for e in ev_ids
                             if e in idx.by_id and idx.by_id[e].file == 'contact_employment_history.csv'})
            row['overlap_paths'].append({'focus_contact': None, 'candidate_contact': None, 'organization': None,
                                         'contacts': people, 'acquaintance_confirmed': None, 'evidence_ids': []})
        row['weight'] = sum(REASON_WEIGHT.get(k, 1) for k in kinds)
        row['evidence_ids'] = sorted(ev_ids)
        out.append(row)

    def nps(r):
        return int(r['nps_last']) if str(r['nps_last'] or '').isdigit() else -1

    out.sort(key=lambda r: (len(r['material_cautions']), len(r['minor_cautions']), -r['weight'], -nps(r), r['account_id']))
    first = {r['account_id'] for r in out if not r['material_cautions']}
    first = {a for a in [r['account_id'] for r in out if r['account_id'] in first][:MAX_REFERENCE_SHORTLIST]}
    for i, r in enumerate(out, 1):
        r['check_order'] = i
        r['status'] = ('cek_pertama' if r['account_id'] in first else
                       'cek_dengan_catatan' if r['material_cautions'] else 'cadangan')
    return out, notes


def _reference(idx: ContextIndex, s: Signals, trace, use, outlets, latest, trust_accounts, diagnostic=None):
    deal = idx.deal
    candidates, notes = _reference_candidates(idx, diagnostic)
    trace.unknowns.extend(notes)
    trace.reference_candidates = candidates
    req = idx.by_id[latest.evidence_id]
    use(req.evidence_id)
    if not candidates:
        trace.unknowns.append('Konteks tidak memuat related_account_* untuk deal ini; kandidat referensi belum tersedia.')
        trace.proposals.append(f'USULAN: {deal.owner_id} mengklarifikasi kriteria referensi pada {req.source_id} lalu mencari '
                               'pelanggan serupa yang bersedia; jangan menjanjikan referensi sebelum ada izin.')
        return 'Kriteria referensi tervalidasi dan satu pelanggan serupa menyatakan bersedia dihubungi.'
    for r in candidates:
        usage = '; '.join(f'{u["feature_id"]} {u["month"]}: '
                          + (f'{u["active_users"]} pengguna aktif' if u['observation_status'] != 'missing' else 'tidak tersedia')
                          for u in r['usage'])
        trace.facts.append(f'Kandidat {r["account_id"]} {r["name"]} (urutan cek {r["check_order"]}, {r["status"]}): '
                           f'relasi {", ".join(r["relations"])}; {r["industry"]}, {r["outlets"]} outlet; '
                           f'health dashboard {r["health_dashboard"] or "-"}, NPS {r["nps_last"] or "-"}'
                           + (f'; usage {usage}' if usage else '') + '.')
        use(*r['evidence_ids'])
        for c in r['material_cautions']:
            trace.interpretations.append(f'{r["account_id"]} dicek belakangan: {c}.')
        for c in r['minor_cautions']:
            trace.interpretations.append(f'{r["account_id"]} catatan: {c}.')
        for n in r['notes']:
            trace.interpretations.append(f'{r["account_id"]}: {n}.')
        for o in r['overlap_paths']:
            people = [o['focus_contact'], o['candidate_contact']] if o.get('focus_contact') else o.get('contacts', [])
            who = ' dan '.join(_contact_label(idx, c) for c in people if c)
            span = f' di {o["organization"]} ({o["valid_from"]} s.d. {o["valid_to"] or "kini"})' if o.get('organization') else ''
            trace.interpretations.append(f'{r["account_id"]}: overlap masa kerja {who}{span}; overlap tidak membuktikan saling '
                                         'kenal (acquaintance belum dikonfirmasi).')
            use(*o.get('evidence_ids', []))
    trace.interpretations.append('Kandidat related_account_* adalah hasil pencarian bersumber; urutan cek bukan penilaian kelayakan. '
                                 'Kesesuaian, kesediaan menjadi referensi dan izin kontak belum diketahui (null).')
    trace.unknowns.append(f'Kesesuaian, kesediaan dan izin kontak kandidat referensi '
                          f'{", ".join(r["account_id"] for r in candidates)} belum diketahui; kandidat bukan izin.')
    first = [r for r in candidates if r['status'] == 'cek_pertama']
    later = [r for r in candidates if r['status'] != 'cek_pertama']
    if first:
        who = ', '.join(f'{r["name"]} ({r["account_id"]}, AM {r["owner_id"] or "?"})' for r in first)
        text = (f'USULAN: {deal.owner_id} mengonfirmasi kriteria "pengguna serupa" atas permintaan {req.source_id}, lalu meminta '
                f'account manager memeriksa pengalaman terbaru dan menanyakan kesediaan serta izin kontak {who} sebelum '
                f'perkenalan ke {deal.account_name}.')
        if later:
            text += ' Kandidat lain dicek belakangan karena catatan: ' + '; '.join(
                f'{r["account_id"]} ({(r["material_cautions"] or r["minor_cautions"] or ["di luar urutan awal"])[0]})'
                for r in later) + '.'
        trace.proposals.append(text)
    else:
        trace.unknowns.append('Semua kandidat related_account memiliki catatan material; tidak ada yang didahulukan otomatis.')
        trace.proposals.append(f'USULAN: {deal.owner_id} meninjau catatan kandidat bersama account manager sebelum memilih '
                               'calon referensi; jangan memperkenalkan tanpa izin.')
    return 'Kriteria referensi tervalidasi dan minimal satu kandidat menyatakan bersedia serta mengizinkan kontak.'


_PLAYBOOKS = {'harga': _price, 'pengambil_keputusan': _decision_maker, 'referensi': _reference}


if __name__ == '__main__':  # pragma: no cover
    import sys
    if sys.argv[1].endswith('.json'):
        ctx = DealContext.model_validate(json.load(open(sys.argv[1], encoding='utf-8')))
    else:
        from backend.graph.context import build_deal_context
        ctx = build_deal_context(sys.argv[1])
    rec, tr = analyze_deal_trace(ctx)
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps({'recommendation': rec.model_dump(), 'trace': tr.to_dict()}, ensure_ascii=False, indent=2))
