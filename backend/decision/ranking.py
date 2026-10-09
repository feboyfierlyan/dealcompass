"""ICAL-03: rank_deals(contexts, diagnostics) -> dict sesuai docs/coordination/PHASE3_CONTRACT.md.

Metode `deal-priority-heuristic-v1`: rules deterministik pilihan desain, bukan model terlatih
dan bukan probabilitas closing. Rank = urutan perhatian/tindakan sales pada snapshot.

Ringkas:
1. Tier: analysis_status `ready` -> acceleration; `insufficient_evidence` -> discovery.
   Semua acceleration diurutkan sebelum discovery; discovery tidak diberi skor karena
   faktor pembandingnya belum diketahui (unknown bukan nol, bukan peluang buruk).
2. Skor acceleration 0-10 = tahap (0-4) + nilai potensi (0-3) + hambatan dinyatakan
   pelanggan (0-2) + preseden relevan (0-1). Bobot di WEIGHTS.
3. Tie-break: hambatan dinyatakan pelanggan, tahap, nilai, lalu deal_id (determinisme saja).
4. Umur tahap, interaksi terakhir dan gate approval/izin = konteks, tidak dihitung.

Tidak membaca dataset, tidak melakukan HTTP, tidak memanggil Jev, tidak mengubah input.
Approval/izin berasal dari analyze_deal_trace(mode='rules') dan tidak diubah oleh skor.
"""
import copy
import json
import math
import re
from collections import defaultdict, deque

from backend.contracts import DealContext, EvidenceRecord
from backend.decision import policy
from backend.decision.analyze import NON_BLOCKING, analyze_deal_trace
from backend.decision.records import ContextIndex

METHOD_ID = 'deal-priority-heuristic-v1'
SCHEMA_VERSION = 'v1'
SUPPORTED_SNAPSHOT = '2026-10-01'
# dataset_kasirnusa/README.md, crm_deals.stage: urutan tahap terbuka.
STAGE_ORDER = ('Lead', 'Discovery', 'Demo', 'Proposal', 'Negosiasi')
# Potensi tahunan IDR (crm_deals.nilai_tahunan = outlet x harga acuan x 12).
VALUE_BINS = ((200_000_000, 3), (100_000_000, 2), (50_000_000, 1))
HOLD_RE = re.compile(r'\b(?:tunda|menunda|ditunda|tertunda|sampai ada|sebelum tanda tangan|menunggu|syarat)\b', re.I)
NEGATED_HOLD_RE = re.compile(r'\b(?:tidak|bukan|belum)\s+(?:perlu\s+)?(?:menunda|tunda|ditunda|menunggu)\b', re.I)
SCORED = ('tahap_deal', 'nilai_potensi_tahunan', 'hambatan_dinyatakan_pelanggan', 'preseden_relevan')
WEIGHTS = {
    'tahap_deal': {'max_points': 4, 'rule': 'Lead 0, Discovery 1, Demo 2, Proposal 3, Negosiasi 4 (crm_deals.stage)',
                   'reason': 'Tahap lebih lanjut berarti tindakan berikutnya lebih dekat ke keputusan pembelian.'},
    'nilai_potensi_tahunan': {'max_points': 3, 'rule': '>= Rp200.000.000: 3; >= Rp100.000.000: 2; >= Rp50.000.000: 1; lainnya 0',
                              'reason': 'Potensi yang dipertaruhkan; dibin agar nominal tidak mendominasi.'},
    'hambatan_dinyatakan_pelanggan': {'max_points': 2,
                                      'rule': 'pesan pelanggan menyatakan penundaan/syarat: 2; pesan pelanggan menyatakan hambatan: 1; '
                                              'hambatan hanya dari pesan internal: 0',
                                      'reason': 'Hambatan yang dinyatakan pelanggan memberi tindakan pembuka yang jelas.'},
    'preseden_relevan': {'max_points': 1, 'rule': '>= 1 preseden decision_log dengan fit cocok/sebagian: 1; lainnya 0',
                         'reason': 'Tindakan punya pembanding historis yang dapat dijelaskan.'},
}
MAX_SCORE = sum(w['max_points'] for w in WEIGHTS.values())
LABELS = {'tahap_deal': 'tahap', 'nilai_potensi_tahunan': 'nilai', 'hambatan_dinyatakan_pelanggan': 'hambatan pelanggan',
          'preseden_relevan': 'preseden'}
MAX_PATH_TARGETS = 3


# --- validasi input -------------------------------------------------------------------------

def _as_context(obj) -> DealContext:
    if isinstance(obj, DealContext):
        return obj.model_copy(deep=True)
    if isinstance(obj, dict):
        return DealContext.model_validate(copy.deepcopy(obj))
    raise ValueError(f'context harus DealContext atau dict, bukan {type(obj).__name__}')


def _pair_inputs(contexts, diagnostics) -> list[tuple[DealContext, dict]]:
    if not isinstance(contexts, (list, tuple)) or not isinstance(diagnostics, (list, tuple)):
        raise ValueError('contexts dan diagnostics harus list.')
    if not contexts:
        raise ValueError('contexts kosong; tidak ada deal untuk diranking.')
    ctxs = [_as_context(c) for c in contexts]
    diags = []
    for d in diagnostics:
        if not isinstance(d, dict):
            raise ValueError(f'diagnostic harus dict, bukan {type(d).__name__}')
        diags.append(copy.deepcopy(d))
    by_ctx, by_diag = {}, {}
    for c in ctxs:
        if c.deal.deal_id in by_ctx:
            raise ValueError(f'deal_id duplikat pada contexts: {c.deal.deal_id}')
        by_ctx[c.deal.deal_id] = c
    for d in diags:
        did = d.get('deal_id')
        if not isinstance(did, str) or not did:
            raise ValueError('diagnostic tanpa deal_id.')
        if did in by_diag:
            raise ValueError(f'deal_id duplikat pada diagnostics: {did}')
        by_diag[did] = d
    if set(by_ctx) != set(by_diag):
        raise ValueError(f'Set deal berbeda: hanya di contexts {sorted(set(by_ctx) - set(by_diag))}, '
                         f'hanya di diagnostics {sorted(set(by_diag) - set(by_ctx))}.')
    snapshots = {c.snapshot_date for c in ctxs} | {d.get('snapshot_date') for d in diags}
    if snapshots != {SUPPORTED_SNAPSHOT}:
        raise ValueError(f'Snapshot campuran/tidak didukung: {sorted(map(str, snapshots))}; hanya {SUPPORTED_SNAPSHOT}.')
    for did, c in by_ctx.items():
        if c.schema_version != SCHEMA_VERSION:
            raise ValueError(f'{did}: schema_version konteks {c.schema_version!r} bukan v1.')
        d = by_diag[did]
        if d.get('account_id') != c.deal.account_id:
            raise ValueError(f'{did}: account_id diagnostic {d.get("account_id")!r} tidak sama dengan konteks {c.deal.account_id!r}.')
    return [(by_ctx[k], by_diag[k]) for k in sorted(by_ctx)]


def _registry(pairs) -> dict[str, dict]:
    """Union bukti context + diagnostic. ID sama dengan isi berbeda adalah kesalahan."""
    reg: dict[str, dict] = {}

    def add(record: dict, where: str):
        rid = record['id']
        if rid in reg and reg[rid] != record:
            raise ValueError(f'Evidence {rid} memiliki isi berbeda antar-sumber ({where}).')
        reg[rid] = record

    for c, d in pairs:
        for e in c.evidence:
            add(e.model_dump(), f'context {c.deal.deal_id}')
        for raw in d.get('evidence', []) or []:
            try:
                rec = EvidenceRecord.model_validate(raw).model_dump()
            except Exception as exc:
                raise ValueError(f'Evidence diagnostic {c.deal.deal_id} tidak valid: {exc}') from exc
            add(rec, f'diagnostic {c.deal.deal_id}')
    return reg


# --- graph path -----------------------------------------------------------------------------

def _adjacency(graph):
    adj = defaultdict(list)
    for e in graph.edges:
        adj[e.source].append((e.target, e))
        if e.target != e.source:
            adj[e.target].append((e.source, e))
    for k in adj:
        adj[k].sort(key=lambda x: (x[1].relation, x[1].id))
    return adj


def _allowed(relation: str, allowed: tuple[str, ...]) -> bool:
    return any(relation.startswith(a[:-1]) if a.endswith('*') else relation == a for a in allowed)


def _segment(adj, start, goal, allowed, max_hops=4):
    """Jalur terpendek deterministik memakai edge asli (boleh dilalui berlawanan arah; edge tidak diubah)."""
    if start == goal:
        return [start], []
    prev = {start: None}
    depth = {start: 0}
    q = deque([start])
    while q:
        u = q.popleft()
        if depth[u] >= max_hops:
            continue
        for v, e in adj.get(u, []):
            if v in prev or not _allowed(e.relation, allowed):
                continue
            prev[v], depth[v] = (u, e), depth[u] + 1
            if v == goal:
                q.clear()
                break
            q.append(v)
    if goal not in prev:
        return None
    nodes, edges, cur = [goal], [], goal
    while prev[cur] is not None:
        u, e = prev[cur]
        nodes.append(u)
        edges.append(e)
        cur = u
    return nodes[::-1], edges[::-1]


def _path(adj, waypoints, allowed, purpose):
    nodes, edges = [waypoints[0]], []
    for a, b in zip(waypoints, waypoints[1:]):
        seg = _segment(adj, a, b, allowed)
        if seg is None:
            return None
        nodes += seg[0][1:]
        edges += seg[1]
    if not edges:
        return None
    return {'node_ids': nodes, 'edge_ids': [e.id for e in edges],
            'evidence_ids': sorted({i for e in edges for i in e.evidence_ids}), '_purpose': purpose}


def path_is_valid(graph, path) -> bool:
    """Setiap pasangan node berurutan dihubungkan edge asli yang disebut; bukti = bukti edge."""
    edges = {e.id: e for e in graph.edges}
    nodes = {n.id for n in graph.nodes}
    ns, es = path['node_ids'], path['edge_ids']
    if len(ns) < 2 or len(es) != len(ns) - 1 or not set(ns) <= nodes:
        return False
    used = set()
    for (a, b), eid in zip(zip(ns, ns[1:]), es):
        e = edges.get(eid)
        if e is None or {e.source, e.target} != {a, b}:
            return False
        used |= set(e.evidence_ids)
    return set(path['evidence_ids']) <= used


# --- faktor --------------------------------------------------------------------------------

def _voice(idx: ContextIndex, rec) -> str:
    """customer | internal | unknown, dari tipe interaksi dan pengirim/peserta (bukan dari subjek)."""
    tipe = rec.get('tipe')
    if tipe == 'email_internal':
        return 'internal'
    if tipe == 'catatan_meeting':
        people = {p.strip() for p in rec.get('peserta').split(';') if p.strip()}
        focus = {c.get('contact_id') for c in idx.contacts_at(idx.deal.account_id)}
        employees = {r.get('employee_id') for r in idx.rows('employees.csv')}
        if people & focus:
            return 'customer'
        return 'internal' if people and people <= employees else 'unknown'
    if tipe == 'email':
        sender = rec.get('dari').strip().lower()
        domains = {r.get('email').split('@')[-1].lower() for r in idx.rows('employees.csv') if '@' in r.get('email')}
        if not sender or not domains:
            return 'unknown'
        return 'internal' if sender.split('@')[-1] in domains else 'customer'
    return 'unknown'


def _factor(name, value, effect, evidence_ids):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f'faktor {name} tidak finite')
    return {'name': name, 'value': value, 'effect': effect, 'evidence_ids': sorted(set(evidence_ids))}


def _profile(ctx: DealContext, diag: dict):
    """Analisis rules satu deal + faktor. Tidak mengubah ctx/diag (keduanya salinan)."""
    rec, trace = analyze_deal_trace(ctx, mode='rules', diagnostic=diag)
    idx = ContextIndex(ctx)
    deal = ctx.deal
    drec = idx.deal_record()
    deal_ev = [drec.evidence_id] if drec else []
    points, unknown = {}, []

    stage_known = deal.stage in STAGE_ORDER
    points['tahap_deal'] = STAGE_ORDER.index(deal.stage) if stage_known else 0
    if not stage_known:
        unknown.append('tahap_deal')
    points['nilai_potensi_tahunan'] = next((p for lim, p in VALUE_BINS if deal.annual_value >= lim), 0)

    main = trace.main_obstacle
    blocking = [o for o in trace.obstacles if o['category'] == main and main not in NON_BLOCKING]
    voices = []
    for o in blocking:
        r = idx.by_id.get(o['evidence_id'])
        v = _voice(idx, r) if r else 'unknown'
        hold = bool(r and v == 'customer' and HOLD_RE.search(r.text) and not NEGATED_HOLD_RE.search(r.text))
        voices.append((o['evidence_id'], o['source_id'], v, hold))
    if any(h for *_, h in voices):
        points['hambatan_dinyatakan_pelanggan'], blocker_label = 2, 'pelanggan menyatakan penundaan/syarat'
    elif any(v == 'customer' for _, _, v, _ in voices):
        points['hambatan_dinyatakan_pelanggan'], blocker_label = 1, 'pelanggan menyatakan hambatan'
    elif voices and all(v == 'internal' for _, _, v, _ in voices):
        points['hambatan_dinyatakan_pelanggan'], blocker_label = 0, 'hambatan hanya dari pesan internal'
    else:
        points['hambatan_dinyatakan_pelanggan'], blocker_label = 0, None
        unknown.append('hambatan_dinyatakan_pelanggan')

    relevant = [p for p in trace.precedents if p['fit'] != 'tidak_cocok']
    points['preseden_relevan'] = 1 if relevant else 0
    prec_ev = sorted({e for p in relevant for e in p['evidence_ids']})

    kind = 'acceleration' if trace.analysis_status == 'ready' else 'discovery'
    gap_ev = sorted({e for f in diag.get('findings', []) if f.get('category') == 'data_gap' for e in f.get('evidence_ids', [])})
    score = sum(points[f] for f in SCORED)
    score_max = score + sum(WEIGHTS[f]['max_points'] - points[f] for f in unknown)

    pts = lambda f: f'{points[f]}/{WEIGHTS[f]["max_points"]} poin'
    tier_note = '' if kind == 'acceleration' else ' Tier discovery: tidak dipakai menghitung skor.'
    factors = [
        _factor('status_bukti', trace.analysis_status,
                'Menentukan tier: ready -> acceleration (diskor); insufficient_evidence -> discovery (setelah acceleration, '
                'tanpa skor; unknown bukan peluang buruk).',
                [o['evidence_id'] for o in blocking] if kind == 'acceleration' else deal_ev + gap_ev),
        _factor('tahap_deal', deal.stage if stage_known else None,
                (f'Tahap {deal.stage} = {pts("tahap_deal")} ({WEIGHTS["tahap_deal"]["rule"]}).' if stage_known else
                 'Tahap tidak dikenal: 0 poin dan dicatat unknown (bukan bukti negatif).') + tier_note, deal_ev),
        _factor('nilai_potensi_tahunan', deal.annual_value,
                f'{policy.rupiah(deal.annual_value)} = {pts("nilai_potensi_tahunan")} ({WEIGHTS["nilai_potensi_tahunan"]["rule"]}); '
                'potensi CRM, bukan pendapatan.' + tier_note
                + (' Dalam tier discovery dipakai sebagai urutan jadwal discovery.' if kind == 'discovery' else ''), deal_ev),
        _factor('hambatan_dinyatakan_pelanggan', blocker_label,
                (f'{blocker_label} ({", ".join(f"{s}:{v}" for _, s, v, _ in voices)}) = {pts("hambatan_dinyatakan_pelanggan")}.'
                 if blocker_label else 'Belum ada hambatan bersumber dari akun fokus: unknown, 0 poin, bukan bukti negatif.')
                + tier_note, [e for e, *_ in voices]),
        _factor('preseden_relevan', len(relevant),
                (f'{len(relevant)} preseden decision_log relevan ({", ".join(p["decision_id"] for p in relevant)}) = '
                 f'{pts("preseden_relevan")}; preseden bukan izin otomatis.' if relevant else
                 f'Tidak ada preseden relevan di candidate_decisions = {pts("preseden_relevan")}.') + tier_note, prec_ev),
        _factor('skor_prioritas', score if kind == 'acceleration' else None,
                (f'Jumlah poin {score}/{MAX_SCORE}; dipakai untuk urutan dalam tier acceleration. Bukan probabilitas closing.'
                 if kind == 'acceleration' else 'Tidak dihitung: bukti percakapan belum cukup untuk dibandingkan.'), deal_ev),
    ]
    # Konteks, tidak dihitung.
    gates, gate_ev = [], []
    if trace.approvals_needed:
        gates.append('approval VP Sales tertunda')
        gate_ev += [m['evidence_id'] for m in trace.discount_mentions] + [
            r.evidence_id for r in idx.rows('employees.csv') if r.get('jabatan') == 'VP Sales']
    refs = [c for c in trace.reference_candidates if c.get('status') == 'cek_pertama']
    if trace.reference_candidates:
        gates.append('kesediaan/izin kandidat referensi belum ada')
        gate_ev += [e for c in refs for e in c['evidence_ids'] if e.startswith('crm_accounts.csv:')]
    if trace.decision_maker:
        gates.append('identitas pengambil keputusan masih inferred')
        gate_ev += [r.evidence_id for r in idx.rows('crm_contacts.csv') if r.get('contact_id') == trace.decision_maker['contact_id']]
    if kind == 'discovery':
        gates.append('discovery belum dilakukan')
    factors.append(_factor('gate_approval_izin', '; '.join(gates) or 'tidak ada gate tercatat',
                           'Gate wajib sebelum tindakan; tidak menaikkan/menurunkan skor dan tidak dihapus oleh nilai atau preseden.',
                           gate_ev))
    metrics = diag.get('metrics') or {}
    stage_age = metrics.get('stage_age_days', deal.stage_age_days)
    factors.append(_factor('umur_tahap_hari', stage_age if isinstance(stage_age, int) else None,
                           'Konteks saja: umur tahap tidak dibandingkan lintas tahap (bukan SLA/outlier; statistik not_assessed).',
                           metrics.get('age_evidence_ids') or deal_ev))
    cust = ((metrics.get('interactions') or {}).get('customer') or {})
    factors.append(_factor('interaksi_eksternal_terakhir', cust.get('last_date'),
                           'Konteks saja: tanggal interaksi eksternal terakhir (termasuk outbound sales, bukan bukti balasan '
                           'pembeli); null = tidak ada dalam cakupan sumber.' if metrics else
                           'Metrics diagnostic tidak tersedia: unknown.', cust.get('last_evidence_ids') or []))
    if metrics and isinstance(stage_age, int) and stage_age != deal.stage_age_days:
        unknown.append('umur_tahap_berbeda')
    return {'ctx': ctx, 'diag': diag, 'idx': idx, 'rec': rec, 'trace': trace, 'kind': kind, 'points': points,
            'score': score, 'score_max': score_max, 'unknown': unknown, 'factors': factors, 'voices': voices,
            'blocking': blocking, 'relevant': relevant}


# --- urutan ---------------------------------------------------------------------------------

def _order(profiles, weights=None):
    w = weights or {f: 1 for f in SCORED}

    def key(p):
        d = p['ctx'].deal
        if p['kind'] == 'discovery':
            return (1, 0, -d.annual_value, -p['points']['tahap_deal'], 0, d.deal_id)
        s = sum(p['points'][f] * w[f] for f in SCORED)
        return (0, -s, -p['points']['hambatan_dinyatakan_pelanggan'], -p['points']['tahap_deal'], -d.annual_value, d.deal_id)

    return sorted(profiles, key=key)


def _tie_reason(a, b) -> str:
    pa, pb = a['points'], b['points']
    da, db = a['ctx'].deal, b['ctx'].deal
    if pa['hambatan_dinyatakan_pelanggan'] != pb['hambatan_dinyatakan_pelanggan']:
        return (f'tie-break 1 hambatan dinyatakan pelanggan ({pa["hambatan_dinyatakan_pelanggan"]} vs '
                f'{pb["hambatan_dinyatakan_pelanggan"]})')
    if pa['tahap_deal'] != pb['tahap_deal']:
        return f'tie-break 2 tahap ({da.stage} vs {db.stage})'
    if da.annual_value != db.annual_value:
        return f'tie-break 3 nilai ({policy.rupiah(da.annual_value)} vs {policy.rupiah(db.annual_value)})'
    return 'tie-break 4 deal_id (determinisme saja, bukan prioritas bisnis)'


def _diff(a, b) -> str:
    parts = [f'{LABELS[f]} {a["points"][f]} vs {b["points"][f]}' for f in SCORED if a['points'][f] != b['points'][f]]
    return ', '.join(parts) or 'faktor sama'


def _rationale(p, ordered, rank, n_acc):
    deal = p['ctx'].deal
    out = []
    if p['kind'] == 'acceleration':
        bd = ' + '.join(f'{LABELS[f]} {p["points"][f]}/{WEIGHTS[f]["max_points"]}' for f in SCORED)
        out.append(f'Tier acceleration (status ready): hambatan "{p["trace"].main_obstacle}" bersumber dari percakapan akun fokus. '
                   f'Skor {p["score"]}/{MAX_SCORE} = {bd}.')
        if rank > 1:
            a = ordered[rank - 2]
            if a['kind'] == 'acceleration':
                out.append(f'Di bawah {a["ctx"].deal.deal_id} (skor {a["score"]}): ' +
                           (f'skor sama; diputus {_tie_reason(a, p)}.' if a['score'] == p['score'] else
                            f'selisih {a["score"] - p["score"]} poin ({_diff(a, p)}).'))
        if rank < len(ordered):
            b = ordered[rank]
            if b['kind'] == 'acceleration':
                out.append(f'Di atas {b["ctx"].deal.deal_id} (skor {b["score"]}): ' +
                           (f'skor sama; diputus {_tie_reason(p, b)}.' if b['score'] == p['score'] else
                            f'selisih {p["score"] - b["score"]} poin ({_diff(p, b)}).'))
            else:
                out.append(f'Di atas deal discovery {b["ctx"].deal.deal_id} karena hambatan deal ini sudah bersumber; '
                           'bukan karena deal discovery dinilai buruk.')
    else:
        out.append(f'Tier discovery (status insufficient_evidence): percakapan akun fokus belum cukup untuk menilai hambatan, '
                   f'sehingga ditempatkan setelah {n_acc} deal acceleration tanpa skor. Ini bukan bukti peluang buruk, '
                   'kalah, atau risiko rendah.')
        out.append(f'Nilai CRM {policy.rupiah(deal.annual_value)} belum divalidasi percakapan; dipakai hanya untuk urutan jadwal '
                   'discovery antar-deal discovery.')
    first = p['rec'].action.split('. ')[0].removeprefix('USULAN: ').rstrip('.')
    out.append(f'Tindakan berikutnya (owner {p["rec"].owner_id or "belum tercatat"}): {first}.')
    if p['rec'].approvals_needed:
        out.append('Gate tetap berlaku terlepas dari rank: ' + ' | '.join(p['rec'].approvals_needed))
    return out


# --- jalur bukti -----------------------------------------------------------------------------

def _evidence_paths(p) -> tuple[list[dict], list[str]]:
    ctx, idx, trace = p['ctx'], p['idx'], p['trace']
    deal = ctx.deal
    adj = _adjacency(ctx.graph)
    nodes = {n.id for n in ctx.graph.nodes}
    paths, missing = [], []

    def add(waypoints, allowed, purpose):
        if not all(w in nodes for w in waypoints):
            missing.append(f'Jalur {purpose}: node {[w for w in waypoints if w not in nodes]} tidak ada di graph konteks.')
            return
        path = _path(adj, waypoints, allowed, purpose)
        if path is None:
            missing.append(f'Jalur {purpose} tidak ditemukan di graph konteks; record ditampilkan tanpa jalur.')
        elif all(path['edge_ids'] != q['edge_ids'] for q in paths):
            paths.append(path)

    if p['kind'] == 'discovery' or not p['blocking']:
        add([deal.deal_id, deal.account_id], ('deal_for',), 'deal-akun')
    for o in p['blocking'][:MAX_PATH_TARGETS]:
        add([deal.deal_id, deal.account_id, o['source_id']], ('deal_for', 'interaction_for'), f'hambatan {o["source_id"]}')
    if trace.approvals_needed:
        vps = [r.get('employee_id') for r in idx.rows('employees.csv') if r.get('jabatan') == 'VP Sales']
        for m in [m for m in trace.discount_mentions if m['kind'] == 'request'][:MAX_PATH_TARGETS]:
            for vp in vps:
                add([m['source_id'], vp], ('sent_to', 'current_email_identity'), f'permintaan {m["source_id"]} ke VP Sales {vp}')
    for prec in sorted(p['relevant'], key=lambda x: (-x['score'], x['decision_id']))[:MAX_PATH_TARGETS]:
        did = prec['decision_id']
        d = next((x for x in ctx.candidate_decisions if x.get('decision_id') == did), {})
        way = [deal.deal_id, did] + ([d['deal_id']] if d.get('deal_id') in nodes else [])
        add(way, ('candidate_precedent_*', 'decision_on_deal'), f'preseden {did}')
    dm = trace.decision_maker
    if dm:
        add([deal.deal_id, deal.account_id, dm['contact_id']], ('deal_for', 'employed_at', 'current_crm_account'),
            f'pengambil keputusan {dm["contact_id"]} (inferred)')
        for prec in p['relevant'][:MAX_PATH_TARGETS]:
            d = next((x for x in ctx.candidate_decisions if x.get('decision_id') == prec['decision_id']), {})
            if d.get('account_id') and d.get('account_id') != deal.account_id:
                way = [dm['contact_id'], d['account_id'], prec['decision_id']]
                if d.get('fitur_dijanjikan') in nodes:
                    way.append(d['fitur_dijanjikan'])
                add(way, ('employed_at', 'decision_for', 'promises_feature'), f'riwayat {dm["contact_id"]} ke {prec["decision_id"]}')
    req_ids = [o['source_id'] for o in p['blocking']]
    for c in [c for c in trace.reference_candidates if c.get('status') == 'cek_pertama'][:MAX_PATH_TARGETS]:
        add([deal.deal_id, c['account_id']], ('related_account_*',), f'kandidat referensi {c["account_id"]}')
        for u in c.get('usage', []):
            usage_node = f'feature-usage:{u["month"]}|{c["account_id"]}|{u["feature_id"]}'
            for rid in req_ids[:1]:
                add([rid, u['feature_id'], usage_node, c['account_id']],
                    ('possibly_mentions_feature', 'mentions', 'measures_feature', 'feature_usage_for'),
                    f'usage {u["feature_id"]} {u["month"]} {c["account_id"]}')
        for o in c.get('overlap_paths', []):
            if o.get('focus_contact') and o.get('candidate_contact'):
                add([deal.account_id, o['focus_contact'], o['candidate_contact'], c['account_id']],
                    ('employed_at', 'overlapping_employment', 'current_crm_account'),
                    f'overlap {o["focus_contact"]}-{o["candidate_contact"]} (bukan bukti saling kenal)')
    for q in paths:
        q.pop('_purpose', None)
    return paths, missing


# --- API utama ------------------------------------------------------------------------------

def _methodology() -> dict:
    return {
        'id': METHOD_ID,
        'label': 'Prioritas tindakan deal (heuristik rules v1)',
        'description': (
            'Rules deterministik pilihan desain, bukan model terlatih. Tier acceleration (status ready) diurutkan sebelum '
            'tier discovery (insufficient_evidence). Skor acceleration = tahap_deal (0-4) + nilai_potensi_tahunan (0-3) + '
            'hambatan_dinyatakan_pelanggan (0-2) + preseden_relevan (0-1), maksimum '
            f'{MAX_SCORE}; bobot dan aturan bin ada di field weights. Approval/izin adalah gate dari analisis rules dan '
            'tidak memengaruhi skor. Rank = urutan perhatian/tindakan sales pada snapshot, bukan probabilitas closing.'),
        'ordered_rules': [
            'Validasi input: pasangkan context dan diagnostic per deal_id; tolak duplikasi, set deal berbeda, akun berbeda, '
            'snapshot campuran dan evidence ID sama dengan isi berbeda.',
            "Analisis bisnis per deal: analyze_deal_trace(context, mode='rules', diagnostic) menghasilkan Recommendation v1, "
            'status bukti, hambatan, approval/izin dan preseden. Jev tidak dipakai.',
            'Tier: ready -> acceleration; insufficient_evidence -> discovery. Semua acceleration sebelum discovery.',
            'Skor acceleration = jumlah poin empat faktor terhitung (lihat weights); urut skor menurun.',
            'Faktor unknown = 0 poin dan dicatat; limitations menyebut rank yang dapat berubah bila unknown terisi.',
            'Konteks tidak dihitung: umur tahap, interaksi eksternal terakhir, gate approval/izin.',
            'Discovery diurutkan nilai potensi menurun lalu tahap, sebagai urutan jadwal discovery tanpa skor.',
        ],
        'tie_breakers': [
            'Poin hambatan dinyatakan pelanggan lebih tinggi (deal yang ditahan pelanggan dengan syarat jelas ditangani dulu).',
            'Tahap lebih lanjut.',
            'Nilai potensi tahunan lebih besar.',
            'deal_id leksikografis; hanya agar hasil deterministik, bukan prioritas bisnis.',
        ],
        'limitations': [
            'Bobot dan bin adalah pilihan desain yang dapat diperdebatkan; belum divalidasi terhadap hasil closing historis.',
            'Hambatan dinyatakan pelanggan dideteksi dengan aturan leksikal pada isi pesan; parafrase dapat terlewat.',
            'Nilai deal adalah potensi CRM (outlet x harga acuan), bukan pendapatan.',
        ],
        'weights': copy.deepcopy(WEIGHTS),
    }


def rank_deals(contexts: list[DealContext], diagnostics: list[dict]) -> dict:
    """Ranking prioritas seluruh deal input (kontrak fase 3). Input tidak diubah."""
    pairs = _pair_inputs(contexts, diagnostics)
    registry = _registry(pairs)
    profiles = [_profile(c, d) for c, d in pairs]
    ordered = _order(profiles)
    n_acc = sum(p['kind'] == 'acceleration' for p in ordered)
    items = []
    for rank, p in enumerate(ordered, 1):
        deal = p['ctx'].deal
        paths, missing = _evidence_paths(p)
        rec = p['rec'].model_dump()
        limitations = [f'Rank {rank} adalah urutan perhatian sales pada snapshot {SUPPORTED_SNAPSHOT}, bukan probabilitas closing.']
        limitations += [f'Faktor {f} unknown; tidak diberi poin dan bukan bukti negatif.' for f in p['unknown']
                        if f in SCORED]
        if 'umur_tahap_berbeda' in p['unknown']:
            limitations.append('Umur tahap diagnostic berbeda dari DealSummary; dipakai sebagai konteks saja.')
        if p['kind'] == 'acceleration' and p['score_max'] > p['score']:
            above = [q for q in ordered[:rank - 1] if q['kind'] == 'acceleration' and q['score'] <= p['score_max']]
            if above:
                limitations.append(f'Bila faktor unknown terisi maksimum (skor {p["score_max"]}), deal ini dapat naik melewati '
                                   f'{", ".join(q["ctx"].deal.deal_id for q in above)}.')
        if p['kind'] == 'discovery':
            limitations.append('Tidak ada percakapan akun fokus yang cukup dalam sumber; aktivitas di luar dataset tidak diketahui.')
        if p['rec'].approvals_needed:
            limitations.append('Approval VP Sales masih tertunda; rank tidak mengesahkan diskon atau penawaran.')
        if p['trace'].reference_candidates:
            limitations.append('Kandidat referensi adalah hasil pencarian bersumber, bukan izin; kesesuaian, kesediaan dan izin '
                               'kontak masih null. Overlap kerja tidak membuktikan saling kenal.')
        if p['trace'].decision_maker:
            limitations.append(f'Identitas pengambil keputusan {p["trace"].decision_maker["contact_id"]} masih inferred dan '
                               'perlu dikonfirmasi langsung.')
        diag_cats = {f.get('category') for f in p['diag'].get('findings', [])}
        if p['trace'].analysis_status == 'ready' and diag_cats and diag_cats <= {'data_gap'}:
            limitations.append('Diagnostic Bima hanya mencatat data_gap untuk deal ini; status ready berasal dari rules Ical.')
        limitations += missing
        limitations.append('Bukti terbatas pada konteks dan diagnostic snapshot; ketiadaan record bukan bukti tidak ada aktivitas.')
        ref_ids = set(rec['evidence_ids'])
        for f in p['factors']:
            ref_ids |= set(f['evidence_ids'])
        for q in paths:
            ref_ids |= set(q['evidence_ids'])
        unresolved = sorted(i for i in ref_ids if i not in registry)
        if unresolved:
            raise ValueError(f'{deal.deal_id}: evidence ID tidak dapat di-resolve: {unresolved[:5]}')
        items.append({
            'deal_id': deal.deal_id, 'account_id': deal.account_id, 'rank': rank, 'priority_kind': p['kind'],
            'analysis_status': p['trace'].analysis_status,
            'rationale': _rationale(p, ordered, rank, n_acc),
            'factors': p['factors'], 'recommendation': rec,
            'evidence_ids': sorted(ref_ids), 'evidence': [registry[i] for i in sorted(ref_ids)],
            'evidence_paths': paths, 'limitations': list(dict.fromkeys(limitations)),
        })
    result = {
        'schema_version': SCHEMA_VERSION, 'snapshot_date': SUPPORTED_SNAPSHOT, 'engine_mode': 'rules',
        'methodology': _methodology(), 'items': items,
        'limitations': [
            'Ranking heuristik rules; belum tervalidasi terhadap hasil closing historis dan bukan probabilitas closing.',
            'Rank adalah urutan perhatian/tindakan sales, bukan prediksi urutan closing atau penilaian kualitas pelanggan.',
            'Deal discovery ditempatkan setelah acceleration karena bukti belum cukup untuk dibandingkan; bukan peluang buruk.',
            'Approval/izin adalah gate dari analisis rules; nilai besar atau preseden sukses tidak menghapus gate.',
            'Umur tahap tidak dibandingkan lintas tahap; outlier statistik tidak dinilai.',
            'Jev tidak dipakai untuk ranking (engine_mode rules).',
            *_sensitivity(profiles),
        ],
    }
    json.dumps(result, allow_nan=False)  # JSON strict: gagal keras bila ada NaN/Infinity/objek non-JSON
    return result


def _sensitivity(profiles) -> list[str]:
    base = [p['ctx'].deal.deal_id for p in _order(profiles) if p['kind'] == 'acceleration']
    if len(base) < 2:
        return []
    out = []
    for f in SCORED:
        w = {g: (0 if g == f else 1) for g in SCORED}
        alt = [p['ctx'].deal.deal_id for p in _order(profiles, w) if p['kind'] == 'acceleration']
        out.append(f'Sensitivitas tanpa faktor {f}: urutan acceleration {" > ".join(alt)}'
                   + (' (sama).' if alt == base else f' (berubah dari {" > ".join(base)}).'))
    w = {g: (2 if g == 'nilai_potensi_tahunan' else 1) for g in SCORED}
    alt = [p['ctx'].deal.deal_id for p in _order(profiles, w) if p['kind'] == 'acceleration']
    out.append(f'Sensitivitas bobot nilai x2: urutan acceleration {" > ".join(alt)}'
               + (' (sama).' if alt == base else f' (berubah dari {" > ".join(base)}).'))
    return out
