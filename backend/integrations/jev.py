"""Adapter Jev (TypeSafe) untuk backend.

Diverifikasi terhadap dokumentasi resmi 2026-10-09:
- https://docs.typesafe.ai/introduction/quickstart
- https://docs.typesafe.ai/api.md
POST {base}/systemone, header Authorization: Bearer <key>, body
{state, model, questions}. Jawaban: noul -> {noul}, choice -> {choice,
probabilities, confidence}, score -> {score, legend, probabilities, confidence}.
Status error terdokumentasi: 401, 422, 429, 529.

Secret hanya dibaca dari env backend dan tidak pernah dicatat.
Integrasi live BELUM diuji: tidak ada TYPESAFE_API_KEY saat implementasi.
"""
import hashlib
import json
import math
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

DEFAULT_BASE_URL = 'https://api.typesafe.ai/v1'
DEFAULT_MODEL = 'jev-latest'
DEFAULT_TIMEOUT_S = 20.0
_STATUS_CODES = {401: 'unauthorized', 422: 'invalid_request', 429: 'rate_limited', 529: 'overloaded'}


class JevError(Exception):
    def __init__(self, code: str, message: str = ''):
        super().__init__(f'{code}: {message}' if message else code)
        self.code = code


@dataclass
class JevCall:
    """Log satu panggilan tanpa secret. Latensi diukur, bukan diperkirakan."""
    question_keys: list[str]
    mode: str  # jev | replay
    model: str | None = None
    latency_ms: int | None = None
    error: str | None = None
    usage: dict = field(default_factory=dict)


def choice(instructions: str, criteria: dict[str, str]) -> dict:
    return {'type': 'choice', 'instructions': instructions, 'criteria': criteria}


def score(instructions: str, criteria: list[str]) -> dict:
    if not 2 <= len(criteria) <= 10:
        raise ValueError('Score criteria wajib 2-10 level (docs api.md).')
    return {'type': 'score', 'instructions': instructions, 'criteria': criteria}


def noul(instructions: str) -> dict:
    return {'type': 'noul', 'instructions': instructions}


def request_key(state, questions: dict) -> str:
    raw = json.dumps({'state': state, 'questions': questions}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]


def _finite(value, lo=None, hi=None) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return False
    return (lo is None or value >= lo) and (hi is None or value <= hi)


def _bad(key: str, why: str):
    raise JevError('invalid_response', f'{key}: {why}')


def _validate_answers(questions: dict, data) -> dict:
    """Validasi ketat bentuk respons (docs api.md). Gagal -> JevError('invalid_response')."""
    if not isinstance(data, dict):
        _bad('body', 'bukan object')
    answers = data.get('answers')
    if not isinstance(answers, dict):
        _bad('answers', 'tidak ada / bukan object')
    for key, q in questions.items():
        a = answers.get(key)
        if not isinstance(a, dict) or a.get('type') != q['type']:
            _bad(key, f'tipe bukan {q["type"]}')
        if q['type'] == 'noul':
            if not _finite(a.get('noul'), 0, 1):
                _bad(key, 'noul harus angka finite 0..1')
        elif q['type'] == 'choice':
            if not isinstance(a.get('choice'), str) or a['choice'] not in q['criteria']:
                _bad(key, 'choice di luar criteria')
        elif q['type'] == 'score':
            if not _finite(a.get('score'), 0, len(q['criteria']) - 1):
                _bad(key, f'score harus angka finite 0..{len(q["criteria"]) - 1}')
            if 'legend' in a and not isinstance(a['legend'], dict):
                _bad(key, 'legend bukan object')
        if 'confidence' in a and not _finite(a['confidence'], 0, 1):
            _bad(key, 'confidence harus angka finite 0..1')
        probs = a.get('probabilities')
        if probs is not None and (not isinstance(probs, dict) or not all(_finite(v, 0, 1) for v in probs.values())):
            _bad(key, 'probabilities tidak valid')
    return answers


class JevClient:
    mode = 'jev'

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, base_url: str = DEFAULT_BASE_URL,
                 timeout_s: float = DEFAULT_TIMEOUT_S, transport: httpx.BaseTransport | None = None,
                 record_dir: str | None = None):
        if not api_key:
            raise JevError('missing_key')
        self._key = api_key
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.timeout_s = timeout_s
        self._transport = transport
        self.record_dir = Path(record_dir) if record_dir else None
        self.calls: list[JevCall] = []

    def __repr__(self):
        return f'JevClient(model={self.model!r}, base_url={self.base_url!r})'

    def ask(self, state, questions: dict, timeout_s: float | None = None) -> dict:
        call = JevCall(list(questions), self.mode)
        self.calls.append(call)
        start = time.perf_counter()
        timeout = self.timeout_s if timeout_s is None else min(self.timeout_s, timeout_s)
        try:
            with httpx.Client(transport=self._transport, timeout=timeout) as client:
                r = client.post(f'{self.base_url}/systemone',
                                headers={'Authorization': f'Bearer {self._key}', 'Content-Type': 'application/json'},
                                json={'state': state, 'model': self.model, 'questions': questions})
        except httpx.TimeoutException as e:
            call.error = 'timeout'
            raise JevError('timeout') from e
        except httpx.HTTPError as e:
            call.error = 'network_error'
            raise JevError('network_error', type(e).__name__) from e
        finally:
            call.latency_ms = round((time.perf_counter() - start) * 1000)
        if r.status_code != 200:
            call.error = _STATUS_CODES.get(r.status_code, f'http_{r.status_code}')
            raise JevError(call.error)
        try:
            data = r.json()
        except ValueError as e:
            call.error = 'invalid_response'
            raise JevError('invalid_response', 'bukan JSON') from e
        try:
            answers = _validate_answers(questions, data)
        except JevError as e:
            call.error = e.code
            raise
        call.model = data.get('model')
        call.usage = data.get('usage') or {}
        if self.record_dir:
            self.record_dir.mkdir(parents=True, exist_ok=True)
            rec = {'request': {'state': state, 'model': self.model, 'questions': questions},
                   'response': {'model': call.model, 'answers': answers, 'usage': call.usage},
                   'latency_ms': call.latency_ms}
            (self.record_dir / f'{request_key(state, questions)}.json').write_text(
                json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
        return answers


class ReplayClient:
    """Memutar ulang respons Jev yang direkam oleh JevClient(record_dir=...)."""
    mode = 'replay'

    def __init__(self, replay_dir: str):
        self.dir = Path(replay_dir)
        if not self.dir.is_dir():
            raise JevError('replay_missing', 'direktori replay tidak ada')
        self.model = None
        self.calls: list[JevCall] = []

    def ask(self, state, questions: dict, timeout_s: float | None = None) -> dict:
        call = JevCall(list(questions), self.mode)
        self.calls.append(call)
        path = self.dir / f'{request_key(state, questions)}.json'
        if not path.is_file():
            call.error = 'replay_missing'
            raise JevError('replay_missing', path.name)
        try:
            data = json.loads(path.read_text(encoding='utf-8'))['response']
            answers = _validate_answers(questions, data)
        except (ValueError, KeyError, TypeError) as e:
            call.error = 'invalid_replay'
            raise JevError('invalid_replay', path.name) from e
        except JevError as e:
            call.error = 'invalid_replay'
            raise JevError('invalid_replay', str(e)) from e
        call.model = self.model = data.get('model')
        call.usage = data.get('usage') or {}
        call.latency_ms = 0
        return answers


def client_from_env(mode: str):
    """mode: jev | replay. Mengembalikan klien atau melempar JevError."""
    if mode == 'replay':
        return ReplayClient(os.environ.get('DEALCOMPASS_REPLAY_DIR', 'evaluation/replay'))
    return JevClient(
        api_key=os.environ.get('TYPESAFE_API_KEY', ''),
        model=os.environ.get('TYPESAFE_MODEL') or DEFAULT_MODEL,
        base_url=os.environ.get('TYPESAFE_BASE_URL') or DEFAULT_BASE_URL,
        timeout_s=float(os.environ.get('TYPESAFE_TIMEOUT_S') or DEFAULT_TIMEOUT_S),
        record_dir=os.environ.get('DEALCOMPASS_RECORD_DIR') or None,
    )
