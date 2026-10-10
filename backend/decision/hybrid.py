"""Analisis default halaman deal: rules dulu, Jev memperkaya, rules memeriksa hasil akhir.

Satu workflow per (deal, fingerprint konteks, versi analisis, konfigurasi model):
1. Rules deterministik selalu dihitung (cepat, tanpa provider).
2. Mode rules atau bukti tidak cukup (P05) -> hasil rules, nol request provider.
3. Hasil hybrid tervalidasi dicari di cache (memori lalu SQLite terpisah dari ledger billing).
4. Belum ada -> satu workflow analyze_deal_trace(mode jev/replay); permintaan bersamaan untuk
   key yang sama menunggu workflow yang sama (single-flight), bukan memanggil provider lagi.
5. Hasil Jev hanya dipakai bila semua request sukses, invariant bukti lolos dan gate rules
   (approval, izin referensi) tidak hilang. Selain itu rules ditampilkan dengan alasan fallback.
6. Kegagalan disimpan sebentar (negative cache) agar navigasi tidak memicu retry otomatis.

Satu workflow dapat berisi beberapa request Jev (per pesan/preseden); semuanya melewati
UsageLedger tim yang sama lewat JevClient. Cache key tidak memuat API key. Hasil cache
membawa metadata asal (generated_at, provider_requests, model) dan tidak disebut baru.
"""
from functools import lru_cache
import hashlib
import json
import logging
import os
import re
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from backend.contracts import DealContext, Recommendation
from backend.decision.analyze import NON_BLOCKING, analyze_deal_trace, resolve_mode
from backend.integrations.jev import DEFAULT_BASE_URL, DEFAULT_MODEL

logger = logging.getLogger(__name__)

ANALYSIS_SCHEMA = 'rules+jev/1'
DEFAULT_RETRY_AFTER_S = 300.0
SHARED_WAIT_S = 60.0
_DECISION_FILES = ('analyze.py', 'signals.py', 'precedents.py', 'policy.py', 'records.py', 'hybrid.py')
_CODE = re.compile(r'[A-Za-z0-9_:.\-]{1,64}')

Outcome = Literal['jev_applied', 'rules_only', 'jev_unavailable', 'not_eligible']
CacheState = Literal['fresh', 'hit', 'shared', 'none']


class EvidencePathOut(BaseModel):
    node_ids: list[str]
    edge_ids: list[str]
    evidence_ids: list[str]


class AnalysisMeta(BaseModel):
    """Metadata tambahan (bukan bagian Recommendation v1). Lihat docs/handoffs/ICAL.md."""
    analysis_id: str
    analysis_version: str
    context_fingerprint: str
    engine_mode: Literal['jev', 'rules', 'replay']
    outcome: Outcome
    analysis_status: Literal['ready', 'insufficient_evidence']
    fallback_reason: str | None = None
    cache: CacheState
    generated_at: str
    provider_requests: int = Field(ge=0)
    model: str | None = None
    gate: str
    evidence_paths: list[EvidencePathOut] = Field(default_factory=list)
    path_limitations: list[str] = Field(default_factory=list)


class AnalysisEnvelope(BaseModel):
    schema_version: Literal['v1'] = 'v1'
    deal_id: str
    snapshot_date: str
    recommendation: Recommendation
    analysis: AnalysisMeta


def _sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def analysis_version() -> str:
    """Skema + hash kode keputusan (termasuk teks pertanyaan Jev). Kode berubah -> cache lama tidak dipakai."""
    here = Path(__file__).resolve().parent
    digest = hashlib.sha256(ANALYSIS_SCHEMA.encode())
    for name in _DECISION_FILES:
        digest.update(name.encode())
        digest.update((here / name).read_bytes().replace(b'\r\n', b'\n'))
    return f'{ANALYSIS_SCHEMA}+{digest.hexdigest()[:12]}'


def context_fingerprint(context: DealContext, diagnostic: dict | None) -> str:
    return _sha({'context': context.model_dump(mode='json'), 'diagnostic': diagnostic})[:16]


def model_config(mode: str) -> dict:
    """Konfigurasi yang memengaruhi jawaban provider. Tidak memuat API key."""
    if mode == 'replay':
        return {'mode': 'replay', 'replay_dir': os.environ.get('DEALCOMPASS_REPLAY_DIR', 'evaluation/replay')}
    return {'mode': mode, 'model': os.environ.get('TYPESAFE_MODEL') or DEFAULT_MODEL,
            'base_url': (os.environ.get('TYPESAFE_BASE_URL') or DEFAULT_BASE_URL).rstrip('/')}


def cache_key(deal_id: str, fingerprint: str, version: str, config: dict) -> str:
    return _sha({'deal_id': deal_id, 'context': fingerprint, 'version': version, 'config': config})


def _code(value) -> str | None:
    if value is None:
        return None
    value = str(value).split(':', 1)[0] if str(value).startswith('internal_error') else str(value)
    return value if _CODE.fullmatch(value) else 'unrecognized_error'


def _model(calls: list[dict]) -> str | None:
    for c in calls:
        m = c.get('model')
        if isinstance(m, str) and m.startswith('jev-') and len(m) <= 80 and all(ch.isalnum() or ch in '.-_' for ch in m):
            return m
    return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def gate_summary(trace) -> str:
    """Gate sebelum tindakan dari trace aktif; teks sama dengan faktor ranking gate_approval_izin."""
    gates = []
    if trace.approvals_needed:
        gates.append('approval VP Sales tertunda')
    if trace.reference_candidates:
        gates.append('kesediaan/izin kandidat referensi belum ada')
    if trace.decision_maker:
        gates.append('identitas pengambil keputusan masih inferred')
    if trace.analysis_status != 'ready':
        gates.append('discovery belum dilakukan')
    return '; '.join(gates) or 'tidak ada gate tercatat'


def evidence_paths(context: DealContext, trace) -> tuple[list[dict], list[str]]:
    """Jalur graph dari trace analisis aktif, memakai pencari jalur ranking atas edge asli konteks."""
    from backend.decision.ranking import _evidence_paths, path_is_valid
    from backend.decision.records import ContextIndex
    profile = {
        'ctx': context, 'idx': ContextIndex(context), 'trace': trace,
        'kind': 'acceleration' if trace.analysis_status == 'ready' else 'discovery',
        'blocking': [o for o in trace.obstacles if o['category'] == trace.main_obstacle and trace.main_obstacle not in NON_BLOCKING],
        'relevant': [p for p in trace.precedents if p['fit'] != 'tidak_cocok'],
    }
    paths, missing = _evidence_paths(profile)
    valid = [p for p in paths if path_is_valid(context.graph, p)]
    if len(valid) != len(paths):
        missing.append('Sebagian jalur tidak lolos validasi edge konteks dan tidak ditampilkan.')
    return valid, missing


# --- cache -----------------------------------------------------------------------------------

class AnalysisCache:
    """Hasil hybrid tervalidasi. File SQLite sendiri, tidak berbagi tabel/berkas dengan UsageLedger."""

    def __init__(self, path: str | Path | None):
        self.path = Path(path).expanduser().resolve() if path else None
        self._memory: dict[str, dict] = {}
        self._lock = threading.Lock()

    def _db(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(str(self.path), timeout=5)
        db.execute('CREATE TABLE IF NOT EXISTS analyses (key TEXT PRIMARY KEY, deal_id TEXT NOT NULL, '
                   'created_utc TEXT NOT NULL, payload TEXT NOT NULL)')
        return db

    def get(self, key: str) -> dict | None:
        with self._lock:
            if key in self._memory:
                return self._memory[key]
        if not self.path or not self.path.is_file():
            return None
        try:
            db = self._db()
            try:
                row = db.execute('SELECT payload FROM analyses WHERE key=?', (key,)).fetchone()
            finally:
                db.close()
            if not row:
                return None
            payload = json.loads(row[0])
            Recommendation.model_validate(payload['recommendation'])
            AnalysisMeta.model_validate(payload['analysis'])
        except (sqlite3.Error, ValueError, KeyError, TypeError):
            logger.warning('Analysis cache entry unreadable; ignored.')
            return None
        with self._lock:
            self._memory[key] = payload
        return payload

    def put(self, key: str, deal_id: str, payload: dict) -> None:
        with self._lock:
            self._memory[key] = payload
        if not self.path:
            return
        try:
            db = self._db()
            try:
                with db:
                    db.execute('INSERT OR REPLACE INTO analyses VALUES (?,?,?,?)',
                               (key, deal_id, payload['analysis']['generated_at'], json.dumps(payload, ensure_ascii=False)))
            finally:
                db.close()
        except sqlite3.Error:
            logger.warning('Analysis cache write failed; result kept in memory only.')


def default_cache_path() -> Path:
    explicit = os.environ.get('DEALCOMPASS_ANALYSIS_CACHE_DB')
    if explicit:
        return Path(explicit)
    from backend.integrations.usage import UsageLedger
    return UsageLedger().path.parent / 'analysis-cache.sqlite3'


def retry_after_s() -> float:
    try:
        value = float(os.environ.get('DEALCOMPASS_JEV_RETRY_AFTER_S') or DEFAULT_RETRY_AFTER_S)
        return value if 0 <= value <= 86_400 else DEFAULT_RETRY_AFTER_S
    except ValueError:
        return DEFAULT_RETRY_AFTER_S


@dataclass
class _Flight:
    done: threading.Event
    result: dict | None = None
    error: BaseException | None = None


class AnalysisService:
    def __init__(self, cache: AnalysisCache | None = None, client_factory=None, monotonic=time.monotonic):
        self.cache = cache if cache is not None else AnalysisCache(default_cache_path())
        self.client_factory = client_factory  # tests: mode -> client; default jev.client_from_env (ledger tim)
        self._monotonic = monotonic
        self._lock = threading.Lock()
        self._inflight: dict[str, _Flight] = {}
        self._failures: dict[str, tuple[float, dict]] = {}
        self._failure_lock = threading.Lock()  # separate: _stored() also runs while _lock is held
        self.workflows = 0  # jumlah workflow provider yang benar-benar dijalankan (observasi tes)

    def analyze(self, deal_id: str, refresh: bool = False, context: DealContext | None = None,
                diagnostic: dict | None = None) -> dict:
        if context is None:
            from backend.graph.context import build_deal_context
            context = build_deal_context(deal_id)
        if diagnostic is None:
            from backend.graph.analysis import analyze_deal_initial
            diagnostic = analyze_deal_initial(context)
        rules_rec, rules_trace = analyze_deal_trace(context, mode='rules', diagnostic=diagnostic)
        mode = resolve_mode()
        fingerprint = context_fingerprint(context, diagnostic)
        version = analysis_version()
        key = cache_key(context.deal.deal_id, fingerprint, version, model_config(mode))
        base = {'analysis_id': key[:16], 'analysis_version': version, 'context_fingerprint': fingerprint}

        if mode == 'rules' or rules_trace.analysis_status == 'insufficient_evidence':
            outcome = 'rules_only' if mode == 'rules' else 'not_eligible'
            return self._envelope(context, rules_rec, rules_trace, {
                **base, 'engine_mode': 'rules', 'outcome': outcome, 'cache': 'none', 'generated_at': _now(),
                'provider_requests': 0, 'fallback_reason': None if mode == 'rules' else 'insufficient_evidence'})

        if not refresh:
            stored = self._stored(key)  # fast path without the service lock
            if stored is not None:
                return self._served(stored, 'hit')

        # Leader election and the cache recheck are one atomic step: a workflow that completed between the
        # fast-path miss and this lock is served from its stored result, never run again.
        with self._lock:
            flight = self._inflight.get(key)
            stored = None if refresh or flight is not None else self._stored(key)
            leader = flight is None and stored is None
            if leader:
                flight = self._inflight[key] = _Flight(threading.Event())
        if stored is not None:
            return self._served(stored, 'hit')
        if not leader:
            if not flight.done.wait(SHARED_WAIT_S):
                return self._envelope(context, rules_rec, rules_trace, {
                    **base, 'engine_mode': 'rules', 'outcome': 'jev_unavailable', 'cache': 'none',
                    'generated_at': _now(), 'provider_requests': 0, 'fallback_reason': 'shared_wait_timeout'})
            if flight.error is not None:
                raise flight.error
            return self._served(flight.result, 'shared')
        try:
            flight.result = self._run(context, diagnostic, mode, key, base, rules_rec, rules_trace)
            return flight.result
        except BaseException as e:
            flight.error = e
            raise
        finally:
            flight.done.set()
            with self._lock:
                self._inflight.pop(key, None)

    def _stored(self, key: str) -> dict | None:
        """Validated result or a still-valid failure for this key. Leaders write both before leaving in-flight."""
        hit = self.cache.get(key)
        if hit is not None:
            return hit
        with self._failure_lock:
            failed = self._failures.get(key)
        return failed[1] if failed and failed[0] > self._monotonic() else None

    def _run(self, context, diagnostic, mode, key, base, rules_rec, rules_trace) -> dict:
        self.workflows += 1
        client = self.client_factory(mode) if self.client_factory else None
        rec, trace = analyze_deal_trace(context, mode=mode, client=client, diagnostic=diagnostic)
        calls = trace.jev_calls
        reason = _code(trace.fallback_reason)
        if reason is None:
            reason = self._policy_check(context, rec, trace, rules_rec, rules_trace)
            if reason:
                note = (f'Hasil Jev ({mode}) ditolak pemeriksaan rules: {reason}. Rekomendasi rules ditampilkan; '
                        'tidak ada label Jev yang dipakai.')
                rec = rules_rec.model_copy(update={'unknowns': list(dict.fromkeys([*rules_rec.unknowns, note]))})
                trace = rules_trace
        meta = {**base, 'cache': 'fresh', 'generated_at': _now(), 'provider_requests': len(calls),
                'model': _model(calls)}
        if reason is None:
            result = self._envelope(context, rec, trace, {**meta, 'engine_mode': rec.engine_mode,
                                                           'outcome': 'jev_applied', 'fallback_reason': None})
            self.cache.put(key, context.deal.deal_id, result)
        else:
            result = self._envelope(context, rec, trace, {**meta, 'engine_mode': 'rules',
                                                           'outcome': 'jev_unavailable', 'fallback_reason': reason})
            with self._failure_lock:
                self._failures[key] = (self._monotonic() + retry_after_s(), result)
        return result

    @staticmethod
    def _policy_check(context, rec, trace, rules_rec, rules_trace) -> str | None:
        """Rules memeriksa hasil Jev: bukti valid, gate tidak hilang. Kode alasan, bukan teks provider."""
        calls = trace.jev_calls
        if not calls or any(c.get('error') for c in calls) or rec.engine_mode not in ('jev', 'replay'):
            return 'no_successful_requests'
        evidence = {e.id for e in context.evidence}
        decisions = {d.get('decision_id') for d in context.candidate_decisions}
        if not set(rec.evidence_ids) <= evidence or not set(rec.precedent_ids) <= decisions:
            return 'unresolvable_sources'
        if not rec.action.startswith('USULAN:'):
            return 'proposal_label_missing'
        if not set(rules_rec.approvals_needed) <= set(rec.approvals_needed):
            return 'approval_gate_dropped'
        if rules_trace.reference_candidates and not trace.reference_candidates:
            return 'reference_consent_gate_dropped'
        if rules_trace.decision_maker and not trace.decision_maker:
            return 'decision_maker_gate_dropped'
        return None

    def _envelope(self, context, rec, trace, meta) -> dict:
        paths, missing = evidence_paths(context, trace)
        meta = {**meta, 'analysis_status': trace.analysis_status, 'gate': gate_summary(trace),
                'evidence_paths': paths, 'path_limitations': missing}
        meta.setdefault('model', None)
        envelope = AnalysisEnvelope(deal_id=context.deal.deal_id, snapshot_date=context.snapshot_date,
                                    recommendation=rec, analysis=AnalysisMeta.model_validate(meta))
        return envelope.model_dump(mode='json')

    @staticmethod
    def _served(payload: dict, cache: CacheState) -> dict:
        """Salinan hasil tersimpan; asal (generated_at, provider_requests) tidak diubah."""
        out = json.loads(json.dumps(payload))
        out['analysis']['cache'] = cache
        return out


_service: AnalysisService | None = None
_service_lock = threading.Lock()


@lru_cache(maxsize=8)
def _workspace_service(path: str) -> AnalysisService:
    return AnalysisService(cache=AnalysisCache(Path(path) / 'analysis-cache.sqlite3'))


def default_service() -> AnalysisService:
    from backend.ingestion.scope import workspace
    selected = workspace.get()
    if selected:
        return _workspace_service(selected['path'])
    global _service
    with _service_lock:
        if _service is None:
            _service = AnalysisService()
        return _service


def analyze_deal_envelope(deal_id: str, refresh: bool = False, context: DealContext | None = None) -> dict:
    """Entry point route: AnalysisEnvelope sebagai dict JSON. context opsional dari produsen Bima di route."""
    return default_service().analyze(deal_id, refresh=refresh, context=context)
