"""ICAL-01 decision engine: analyze_deal(context) -> Recommendation.

Pemisahan keluaran (kontrak v1 tidak punya field terpisah):
- action diawali "USULAN:" (rekomendasi, bukan fakta);
- precedent_comparison berisi baris "FAKTA | ...", "INTERPRETASI | ...", "SKENARIO | ...";
- unknowns berisi celah bukti dan kegagalan mesin.
Struktur lengkap tersedia lewat analyze_deal_trace() untuk evaluasi/UI.

Mode mesin (DEALCOMPASS_ENGINE_MODE): auto (default; jev bila TYPESAFE_API_KEY
ada, selain itu rules) | rules | jev | replay. Jev hanya mengklasifikasi
hambatan (Choice), menilai kecocokan preseden (Score) dan memeriksa klaim
persetujuan eksplisit (Noul). Policy gate diskon selalu deterministik.
Kegagalan Jev -> fallback rules dan engine_mode='rules', dicatat di unknowns.
"""
import json
import os
from dataclasses import asdict, dataclass, field

from backend.contracts import DealContext, Recommendation
from backend.decision import policy
from backend.decision.precedents import PrecedentAssessment, assess
from backend.decision.signals import OBSTACLES, MessageObstacle, Signals, extract, is_interaction
from backend.integrations import jev

NON_BLOCKING = {'tanpa_hambatan', 'bukti_kurang', 'kebutuhan_produk'}
FIT_LEVELS = ['tidak relevan', 'relevan sebagian', 'sangat relevan']


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
    precedents: list[dict] = field(default_factory=list)
    calculations: dict = field(default_factory=dict)
    approvals_needed: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    validation_issues: list[str] = field(default_factory=list)
    jev_calls: list[dict] = field(default_factory=list)

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


def validate_context(context: DealContext) -> list[str]:
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
    return issues


def _ev(context: DealContext, eid: str):
    return next((e for e in context.evidence if e.id == eid), None)


def _cite(context: DealContext, eid: str) -> str:
    e = _ev(context, eid)
    return f'{e.source_id} ({e.date or "tanpa tanggal"})' if e else eid


def _run_jev(context: DealContext, signals: Signals, client, trace: DecisionTrace) -> dict:
    """Memanggil Jev. Melempar JevError bila ada panggilan gagal."""
    out = {'obstacles': {}, 'fit': {}, 'explicit_approval': {}}
    for ev in context.evidence:
        if not is_interaction(ev):
            continue
        a = client.ask(ev.excerpt, {'hambatan': jev.choice(
            'Klasifikasikan hambatan penjualan utama yang dinyatakan pesan ini. '
            'Pilih bukti_kurang bila pesan tidak cukup jelas.', OBSTACLES)})
        out['obstacles'][ev.id] = a['hambatan']['choice']
    for r in signals.discount_requests:
        a = client.ask(_ev(context, r.evidence_id).excerpt, {'persetujuan_eksplisit': jev.noul(
            'Apakah pesan ini menyatakan secara eksplisit bahwa diskon SUDAH disetujui oleh pihak berwenang?')})
        out['explicit_approval'][r.evidence_id] = a['persetujuan_eksplisit']['noul']
    for d in context.candidate_decisions:
        if not d.get('decision_id'):
            continue
        state = {'deal': context.deal.model_dump(), 'hambatan_pesan': [
            {'evidence_id': o.evidence_id, 'excerpt': _ev(context, o.evidence_id).excerpt}
            for o in signals.obstacles if o.category not in NON_BLOCKING], 'preseden': d}
        a = client.ask(state, {'kecocokan': jev.score(
            'Seberapa cocok keputusan preseden ini sebagai pembanding untuk hambatan deal saat ini? '
            'Preseden bukan izin otomatis.', FIT_LEVELS)})['kecocokan']
        level = a.get('legend', {}).get(str(a['score'])) if isinstance(a.get('legend'), dict) else None
        if level is None:
            idx = int(round(float(a['score'])))
            level = FIT_LEVELS[idx] if 0 <= idx < len(FIT_LEVELS) else f'skor {a["score"]}'
        out['fit'][d['decision_id']] = level
    return out


def analyze_deal_trace(context: DealContext, mode: str | None = None, client=None) -> tuple[Recommendation, DecisionTrace]:
    deal = context.deal
    mode = client.mode if client is not None else resolve_mode(mode)
    trace = DecisionTrace(deal_id=deal.deal_id, engine_mode=mode)
    valid_ev = {e.id for e in context.evidence}
    trace.validation_issues = validate_context(context)
    trace.unknowns.extend(context.unknowns)
    trace.unknowns.extend(f'Validasi konteks: {i}' for i in trace.validation_issues)
    signals = extract(context)
    used: list[str] = []

    def use(*eids):
        for eid in eids:
            if eid in valid_ev and eid not in used:
                used.append(eid)

    # --- Jev (opsional) -------------------------------------------------------
    jev_out = None
    if mode in ('jev', 'replay'):
        try:
            if client is None:
                client = jev.client_from_env(mode)
            jev_out = _run_jev(context, signals, client, trace)
        except jev.JevError as e:
            trace.unknowns.append(f'Jev ({mode}) gagal: {e.code}. Hasil memakai rules deterministik; '
                                  'integrasi Jev untuk analisis ini tidak berhasil.')
            trace.engine_mode = 'rules'
        finally:
            if client is not None:
                trace.jev_calls = [asdict(c) for c in getattr(client, 'calls', [])]
    if jev_out:
        for o in signals.obstacles:
            j = jev_out['obstacles'].get(o.evidence_id)
            if j and j != o.category:
                trace.interpretations.append(
                    f'Jev mengklasifikasi {_cite(context, o.evidence_id)} sebagai {j}; rules: {o.category}. Label Jev dipakai.')
                o.category, o.source = j, trace.engine_mode
            elif j:
                o.source = trace.engine_mode
        for eid, p in jev_out['explicit_approval'].items():
            if p >= 0.5:
                trace.unknowns.append(
                    f'Jev menilai {_cite(context, eid)} menyiratkan persetujuan (noul={p:.2f}), tetapi persetujuan '
                    'hanya diakui dari decision_log; tidak dianggap approval.')

    trace.obstacles = [asdict(o) for o in signals.obstacles]

    # --- Fakta dasar & hitungan ----------------------------------------------
    deal_ev = [e.id for e in context.evidence if e.source_id == deal.deal_id]
    use(*deal_ev)
    trace.facts.append(
        f'{deal.deal_id} {deal.account_name}: stage {deal.stage} sejak '
        f'{policy.stage_start(context.snapshot_date, deal.stage_age_days)} ({deal.stage_age_days} hari per '
        f'{context.snapshot_date}); nilai potensi tahunan {policy.rupiah(deal.annual_value)} (bukan pendapatan).')
    per_year = policy.PRICE_PER_OUTLET_MONTH_IDR * 12
    outlets, rem = divmod(deal.annual_value, per_year)
    if rem:
        outlets = None
        trace.unknowns.append('annual_value tidak habis dibagi harga per outlet; jumlah outlet tidak dihitung.')
    else:
        trace.calculations['outlets'] = outlets
        trace.calculations['list_annual_value_idr'] = policy.annual_value_idr(outlets)
        trace.calculations['smallest_package'] = policy.smallest_package(outlets)

    blocking = [o for o in signals.obstacles if o.category not in NON_BLOCKING]
    for o in signals.obstacles:
        e = _ev(context, o.evidence_id)
        if o.category not in ('bukti_kurang', 'tanpa_hambatan'):
            use(o.evidence_id)
            trace.facts.append(f'{e.source_id} ({e.date}): "{e.excerpt}"')
    if not blocking:
        trace.analysis_status = 'insufficient_evidence'
        trace.main_obstacle = 'bukti_kurang'
        trace.unknowns.append('Bukti interaksi tidak cukup untuk menyimpulkan hambatan; bukan berarti tidak ada risiko.')
        trace.proposals.append(
            f'USULAN: {deal.owner_id} menjadwalkan discovery dengan {deal.account_name} untuk mengidentifikasi '
            'pengambil keputusan, kebutuhan, jumlah outlet dan anggaran sebelum menawarkan harga atau paket.')
        milestone = 'Catatan discovery pertama berisi pengambil keputusan, kebutuhan dan jadwal pengadaan.'
    else:
        latest = max(blocking, key=lambda o: (_ev(context, o.evidence_id).date or ''))
        trace.main_obstacle = latest.category
        milestone = _PLAYBOOKS[latest.category](context, signals, trace, use, outlets)

    # --- Preseden --------------------------------------------------------------
    assessments: list[PrecedentAssessment] = [assess(context, d, signals)
                                              for d in context.candidate_decisions if d.get('decision_id')]
    precedent_ids = []
    comparison = []
    for a in assessments:
        if jev_out and a.decision_id in jev_out['fit']:
            a.interpretations.append(f'Jev Score kecocokan {a.decision_id}: {jev_out["fit"][a.decision_id]} '
                                     '(penilaian relevansi, bukan probabilitas closing).')
        trace.precedents.append(asdict(a))
        if a.fit == 'tidak_cocok':
            trace.interpretations.append(f'{a.decision_id} diperiksa tetapi tidak cocok untuk hambatan deal ini.')
            continue
        precedent_ids.append(a.decision_id)
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
    if not precedent_ids:
        trace.unknowns.append('Tidak ada preseden relevan di candidate_decisions; perbandingan historis terbatas.')
    comparison = [f'FAKTA | {f}' for f in trace.facts] + comparison + \
                 [f'INTERPRETASI | {i}' for i in trace.interpretations]

    trace.evidence_ids = used
    rec = Recommendation(
        deal_id=deal.deal_id,
        action=' '.join(trace.proposals),
        owner_id=deal.owner_id or None,
        milestone=milestone,
        evidence_ids=used,
        precedent_ids=precedent_ids,
        precedent_comparison=comparison,
        approvals_needed=trace.approvals_needed,
        unknowns=list(dict.fromkeys(trace.unknowns)),
        engine_mode=trace.engine_mode,
    )
    return rec, trace


# --- Playbook per hambatan -------------------------------------------------------

def _price(context, signals, trace, use, outlets):
    deal = context.deal
    for eid, gap in signals.competitor_gaps:
        use(eid)
        trace.facts.append(f'{_cite(context, eid)}: kompetitor disebut ~{gap}% lebih murah (klaim pelanggan, belum diverifikasi).')
    pending = []
    for r in signals.discount_requests:
        use(r.evidence_id)
        trace.facts.append(f'{_cite(context, r.evidence_id)}: PERMINTAAN diskon {r.pct}% (permintaan, bukan approval).')
        if outlets is not None:
            net = policy.annual_value_idr(outlets, r.pct)
            trace.calculations[f'discount_{r.pct}pct'] = {
                'annual_value_idr': net, 'reduction_idr': deal.annual_value - net}
            trace.facts.append(
                f'Hitungan: {outlets} outlet x {policy.rupiah(policy.PRICE_PER_OUTLET_MONTH_IDR)} x 12 = '
                f'{policy.rupiah(deal.annual_value)}; diskon {r.pct}% -> {policy.rupiah(net)} '
                f'(berkurang {policy.rupiah(deal.annual_value - net)}).')
        valid = [d for d in signals.discount_decisions
                 if d.keputusan == 'Disetujui' and d.approver_is_vp and d.pct is not None and d.pct >= r.pct]
        rejected = [d for d in signals.discount_decisions if d.keputusan == 'Ditolak']
        for d in signals.discount_decisions:
            use(*[e.id for e in context.evidence if e.source_id == d.decision_id])
            trace.facts.append(f'{d.decision_id}: keputusan diskon {d.pct}% untuk deal ini = {d.keputusan} oleh {d.decided_by}.')
            if d.keputusan == 'Disetujui' and d.approver_is_vp is None:
                trace.unknowns.append(f'Jabatan pemutus {d.decision_id} ({d.decided_by}) tidak dapat diverifikasi dari konteks.')
            elif d.keputusan == 'Disetujui' and not d.approver_is_vp:
                trace.interpretations.append(f'{d.decision_id} diputuskan {d.decided_by} yang bukan VP Sales; tidak sah untuk diskon >{policy.DISCOUNT_APPROVAL_THRESHOLD_PCT}%.')
        if not policy.requires_vp_approval(r.pct):
            trace.interpretations.append(f'Diskon {r.pct}% tidak melebihi {policy.DISCOUNT_APPROVAL_THRESHOLD_PCT}%; aturan approval VP Sales tidak berlaku.')
        elif valid:
            trace.interpretations.append(f'Diskon {r.pct}% sudah disetujui VP Sales dan tercatat ({valid[0].decision_id}).')
        elif rejected:
            trace.interpretations.append(f'Diskon untuk deal ini sudah ditolak ({rejected[0].decision_id}); jangan ditawarkan.')
        else:
            pending.append(r)
            trace.approvals_needed.append(
                f'{policy.DISCOUNT_APPROVER_ROLE}: putuskan dan catat di decision_log permintaan diskon {r.pct}% '
                f'({_cite(context, r.evidence_id)}); >{policy.DISCOUNT_APPROVAL_THRESHOLD_PCT}% wajib approval. '
                f'Belum ada keputusan tercatat untuk {deal.deal_id}.')
    text = []
    if pending:
        pcts = '/'.join(f'{r.pct}%' for r in pending)
        text.append(f'USULAN: Jangan menawarkan atau menjanjikan diskon {pcts} ke {deal.account_name} sebelum '
                    f'{policy.DISCOUNT_APPROVER_ROLE} memutuskan dan mencatatnya. {deal.owner_id} membawa permintaan '
                    'tersebut ke VP Sales bersama pembanding preseden di bawah.')
    if outlets is not None:
        pkg = policy.smallest_package(outlets)
        text.append(f'Siapkan opsi tanpa diskon untuk dibahas: {outlets} outlet paket {pkg} harga normal '
                    f'{policy.rupiah(policy.annual_value_idr(outlets))}/tahun; bila preseden pilot relevan, '
                    'pilot sebagian outlet hanya sebagai skenario usulan yang butuh persetujuan.')
    text.append('Tanggapi keberatan harga dengan nilai produk berdasar kebutuhan yang tercatat, bukan menyamai harga kompetitor.')
    trace.proposals.append(' '.join(text))
    return ('Keputusan VP Sales atas permintaan diskon tercatat di decision_log, lalu tanggapan tertulis '
            'pelanggan atas opsi harga yang disetujui.' if pending else
            'Tanggapan tertulis pelanggan atas opsi harga yang sesuai kebijakan.')


def _decision_maker(context, signals, trace, use, outlets):
    deal = context.deal
    nodes = {n.id: n for n in context.graph.nodes}
    makers = [e for e in context.graph.edges if e.relation == 'pengambil_keputusan']
    names = []
    for e in makers:
        use(*e.evidence_ids)
        names.append(nodes[e.source].label if e.source in nodes else e.source)
        for prev in (x for x in context.graph.edges if x.source == e.source and x.relation == 'pernah_bekerja_di'):
            use(*prev.evidence_ids)
            org = nodes[prev.target].label if prev.target in nodes else prev.target
            trace.facts.append(f'{names[-1]} sebelumnya di {org} ({prev.valid_from} s.d. {prev.valid_to}).')
            acc = prev.target.split(':', 1)[-1]
            for d in context.candidate_decisions:
                if d.get('account_id') == acc and (d.get('status_janji', '').startswith('Belum') or d.get('keputusan') == 'Menunggu'):
                    trace.interpretations.append(
                        f'Risiko kepercayaan: di {org} ada {d["decision_id"]} '
                        f'({d.get("fitur_dijanjikan") or d.get("nilai")}; {d.get("status_janji") or d.get("keputusan")}). '
                        'Pengambil keputusan baru kemungkinan mengetahui pengalaman ini (inferensi, belum dikonfirmasi).')
    who = ', '.join(names) or 'pengambil keputusan yang baru'
    trace.proposals.append(
        f'USULAN: {deal.owner_id} meminta kontak teknis memperkenalkan dan menjadwalkan pertemuan langsung dengan '
        f'{who}; sesuaikan proposal dengan prioritas operasional. Jawab jujur status fitur yang belum rilis dan '
        'jangan menjanjikan tanggal fitur tanpa keputusan tercatat.')
    trace.unknowns.append(f'Sikap dan kriteria {who} terhadap proposal belum tercatat.')
    return f'Pertemuan dengan {who} terlaksana dan kriteria keputusan pengadaan tercatat.'


def _reference(context, signals, trace, use, outlets):
    deal = context.deal
    nodes = {n.id: n for n in context.graph.nodes}
    cands = [e for e in context.graph.edges if e.relation == 'kandidat_referensi']
    labels = []
    for e in cands:
        use(*e.evidence_ids)
        labels.append(nodes[e.source].label if e.source in nodes else e.source)
        for eid in e.evidence_ids:
            ev = _ev(context, eid)
            if ev and ev.source_file.endswith('crm_accounts.csv'):
                trace.facts.append(f'Kandidat referensi {ev.source_id}: {ev.excerpt}')
    for e in context.graph.edges:
        if e.relation == 'overlap_kerja':
            use(*e.evidence_ids)
            a, b = (nodes[x].label if x in nodes else x for x in (e.source, e.target))
            trace.interpretations.append(
                f'{a} dan {b} pernah bekerja di organisasi yang sama ({e.valid_from} s.d. {e.valid_to}); '
                'overlap kerja tidak membuktikan saling kenal.')
    if labels:
        trace.interpretations.append('Kandidat referensi adalah inferensi kemiripan; kesediaan menjadi referensi belum dikonfirmasi.')
        trace.proposals.append(
            f'USULAN: {deal.owner_id} meminta izin pemilik akun pelanggan untuk menghubungkan {", ".join(labels)} '
            f'sebagai referensi bagi {deal.account_name}, lalu jadwalkan panggilan referensi.')
    else:
        trace.unknowns.append('Konteks belum menyediakan kandidat referensi pelanggan serupa.')
        trace.proposals.append(f'USULAN: {deal.owner_id} mencari pelanggan serupa yang bersedia menjadi referensi.')
    return 'Panggilan referensi terjadwal dengan pelanggan serupa yang menyatakan bersedia.'


_PLAYBOOKS = {'harga': _price, 'pengambil_keputusan': _decision_maker, 'referensi': _reference}


if __name__ == '__main__':  # pragma: no cover
    import sys
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    rec, tr = analyze_deal_trace(DealContext.model_validate(data))
    print(json.dumps({'recommendation': rec.model_dump(), 'trace': tr.to_dict()}, ensure_ascii=False, indent=2))
