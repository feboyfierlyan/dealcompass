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
import time
from dataclasses import asdict, dataclass, field

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


def analyze_deal_trace(context: DealContext, mode: str | None = None, client=None) -> tuple[Recommendation, DecisionTrace]:
    started = time.monotonic()
    mode = client.mode if client is not None else resolve_mode(mode)
    idx = ContextIndex(context)
    if mode == 'rules':
        rec, trace = _analyze(context, idx, 'rules', None, None)
    else:
        deadline = started + budget_s()
        failure = None
        try:
            if client is None:
                client = jev.client_from_env(mode)
            rec, trace = _analyze(context, idx, mode, client, deadline)
        except jev.JevError as e:
            failure = e.code
        except Exception as e:  # respons tak terduga tidak boleh menjatuhkan endpoint
            failure = f'internal_error:{type(e).__name__}'
        calls = [asdict(c) for c in getattr(client, 'calls', [])] if client is not None else []
        if failure:
            rec, trace = _analyze(context, idx, 'rules', None, None, extra_unknowns=[
                f'Jev ({mode}) gagal: {failure}. Seluruh analisis memakai rules deterministik; '
                'tidak ada label Jev yang dipakai.'])
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


def _analyze(context, idx: ContextIndex, mode, client, deadline, extra_unknowns=()):
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
        milestone = _PLAYBOOKS[latest.category](idx, signals, trace, use, outlets, latest, trust_accounts)

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

def _price(idx: ContextIndex, s: Signals, trace, use, outlets, latest, trust_accounts):
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


def _decision_maker(idx: ContextIndex, s: Signals, trace, use, outlets, latest, trust_accounts):
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
    return f'Pertemuan dengan {name} terlaksana, perannya terkonfirmasi, dan kriteria keputusan pengadaan tercatat.'


def _contact_label(idx: ContextIndex, cid: str) -> str:
    c = idx.find('crm_contacts.csv', cid)
    return f'{cid} {c.get("nama")} ({c.get("jabatan_saat_ini")})' if c else cid


def _reference(idx: ContextIndex, s: Signals, trace, use, outlets, latest, trust_accounts):
    deal = idx.deal
    related = idx.related_accounts()
    shortlist, rejected = [], []
    for acc_id, reasons in sorted(related.items()):
        acc = idx.account(acc_id)
        kinds = sorted({k for k, _ in reasons})
        ev_ids = sorted({e for _, ids in reasons for e in ids})
        row = {'account_id': acc_id, 'name': acc.get('nama') if acc else acc_id, 'reasons': kinds,
               'evidence_ids': ev_ids, 'health': acc.get('health_score_dashboard') if acc else '',
               'nps': acc.get('nps_terakhir') if acc else '', 'cautions': [], 'notes': []}
        if not acc:
            row['cautions'].append('baris akun tidak ada di konteks')
        elif acc.get('tipe') != 'pelanggan':
            row['cautions'].append(f'tipe {acc.get("tipe")}, bukan pelanggan')
        elif acc.get('health_score_dashboard') != 'Hijau':
            row['cautions'].append(f'health dashboard {acc.get("health_score_dashboard") or "kosong"}')
        for d in idx.context.candidate_decisions:
            if d.get('account_id') == acc_id and (is_open_commitment(d) or d.get('tipe') == 'eskalasi'):
                row['cautions'].append(f'{d["decision_id"]} {d.get("tipe")}: {d.get("nilai") or d.get("alasan")} ({d.get("status_janji") or d.get("keputusan")})')
        if 'work_overlap' in kinds:
            people = sorted({idx.by_id[e].get('contact_id') for e in ev_ids
                             if e in idx.by_id and idx.by_id[e].file == 'contact_employment_history.csv'})
            row['notes'].append('overlap masa kerja ' + ', '.join(_contact_label(idx, p) for p in people)
                                + '; overlap tidak membuktikan saling kenal')
        row['weight'] = sum(REASON_WEIGHT.get(k, 1) for k in kinds)
        (shortlist if not row['cautions'] else rejected).append(row)
    shortlist.sort(key=lambda r: (-r['weight'], -(int(r['nps']) if str(r['nps']).isdigit() else -1), r['account_id']))
    trace.reference_candidates = [{**r, 'status': 'shortlist'} for r in shortlist] + [{**r, 'status': 'ditolak'} for r in rejected]
    if not related:
        trace.unknowns.append('Konteks tidak memuat related_account_* untuk deal ini; kandidat referensi belum tersedia.')
        trace.proposals.append(f'USULAN: {deal.owner_id} mencari pelanggan serupa yang bersedia menjadi referensi.')
        return 'Panggilan referensi terjadwal dengan pelanggan serupa yang menyatakan bersedia.'
    picked = shortlist[:MAX_REFERENCE_SHORTLIST]
    for r in picked:
        use(*r['evidence_ids'])
        trace.facts.append(f'Kandidat {r["account_id"]} {r["name"]}: alasan {", ".join(r["reasons"])}; '
                           f'health {r["health"] or "-"}, NPS {r["nps"] or "-"}.')
        trace.interpretations.extend(f'{r["account_id"]}: {n}.' for n in r['notes'])
    for r in shortlist[MAX_REFERENCE_SHORTLIST:]:
        trace.interpretations.append(f'{r["account_id"]} {r["name"]} juga memenuhi syarat dasar tetapi di luar {MAX_REFERENCE_SHORTLIST} teratas.')
    for r in rejected:
        trace.interpretations.append(f'Kandidat {r["account_id"]} {r["name"]} ({", ".join(r["reasons"])}) tidak diusulkan: '
                                     f'{"; ".join(r["cautions"])}.')
        trace.interpretations.extend(f'{r["account_id"]}: {n}.' for n in r['notes'])
    trace.interpretations.append('related_account_* adalah kandidat pencarian bersumber; kelayakan dan kesediaan menjadi referensi belum dikonfirmasi.')
    if picked:
        names = ', '.join(f'{r["name"]} ({r["account_id"]})' for r in picked)
        trace.proposals.append(
            f'USULAN: {deal.owner_id} meminta izin pemilik akun untuk menghubungi {names} sebagai calon referensi '
            f'bagi {deal.account_name}; verifikasi kepuasan dan kesediaan sebelum mengenalkan.')
    else:
        trace.unknowns.append('Semua kandidat related_account memiliki catatan kehati-hatian; tidak ada yang diusulkan otomatis.')
        trace.proposals.append(f'USULAN: {deal.owner_id} meninjau kandidat yang ditolak bersama pemilik akun sebelum memilih referensi.')
    return 'Panggilan referensi terjadwal dengan pelanggan serupa yang menyatakan bersedia.'


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
