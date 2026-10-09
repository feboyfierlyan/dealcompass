"""Durable single-host team ledger. No credentials, prompts or answers are stored.

All team requests must use this same SQLite file/backend. Reservations are deliberately
conservative, not a provider tokenizer guarantee. Unknown usage locks further spending.
"""
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

MAX_INPUT_TOKENS = 100_000_000
RESERVATION = 1_000_000
MAX_REQUEST_BYTES = 65_536
MAX_QUESTIONS = 16


class UsageError(Exception):
    pass


class UsageLedger:
    def __init__(self, path=None):
        self.path = Path(path or os.environ.get('TYPESAFE_USAGE_DB') or
                         Path.home() / '.local/share/dealcompass/typesafe-usage.sqlite3').expanduser().resolve()

    @contextmanager
    def connect(self):
        if not self.path.is_file():
            raise UsageError('usage_not_initialized')
        try:
            db = sqlite3.connect(str(self.path), timeout=10)
            db.row_factory = sqlite3.Row
            try:
                db.execute('BEGIN IMMEDIATE')
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise
            finally:
                db.close()
        except sqlite3.Error:
            raise UsageError('usage_storage_error') from None

    def initialize(self, prior_input_tokens, limit=MAX_INPUT_TOKENS):
        if (type(prior_input_tokens) is not int or type(limit) is not int or
                not 0 <= prior_input_tokens <= limit <= MAX_INPUT_TOKENS):
            raise UsageError('invalid_usage_budget')
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Exclusive creation: never reset an existing team's usage counter.
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        except FileExistsError:
            raise UsageError('usage_already_initialized') from None
        with self.connect() as db:
            db.execute('CREATE TABLE budget (id INTEGER PRIMARY KEY CHECK(id=1), prior INTEGER NOT NULL, cap INTEGER NOT NULL)')
            db.execute('INSERT INTO budget VALUES (1, ?, ?)', (prior_input_tokens, limit))
            db.execute('''CREATE TABLE requests (
                id TEXT PRIMARY KEY, created_utc TEXT NOT NULL, completed_utc TEXT,
                status TEXT NOT NULL, reserved INTEGER NOT NULL, input_tokens INTEGER,
                output_tokens INTEGER, usage_json TEXT, http_status INTEGER)''')

    def _summary(self, db):
        budget = db.execute('SELECT prior, cap FROM budget WHERE id=1').fetchone()
        if not budget:
            raise UsageError('usage_storage_error')
        rows = db.execute('SELECT * FROM requests').fetchall()
        actual = sum(r['input_tokens'] or 0 for r in rows)
        held = sum(r['reserved'] for r in rows if r['input_tokens'] is None)
        blocked = any(r['status'] in ('pending', 'unknown_usage', 'reservation_exceeded') for r in rows)
        charged = budget['prior'] + actual + held
        return dict(limit_input_tokens=budget['cap'], prior_input_tokens=budget['prior'],
                    recorded_input_tokens=actual, recorded_output_tokens=sum(r['output_tokens'] or 0 for r in rows),
                    reserved_input_tokens=held, accounted_input_tokens=charged,
                    remaining_input_tokens=max(0, budget['cap'] - charged), request_count=len(rows),
                    pending_requests=sum(r['status'] == 'pending' for r in rows),
                    blocked=blocked or charged + RESERVATION > budget['cap'])

    def summary(self):
        with self.connect() as db:
            return self._summary(db)

    def reserve(self, payload):
        if len(json.dumps(payload, ensure_ascii=False).encode('utf-8')) > MAX_REQUEST_BYTES or not 1 <= len(payload['questions']) <= MAX_QUESTIONS:
            raise UsageError('usage_request_too_large')
        with self.connect() as db:
            if self._summary(db)['blocked']:
                raise UsageError('usage_budget_blocked')
            request_id = uuid.uuid4().hex
            db.execute('INSERT INTO requests(id,created_utc,status,reserved) VALUES (?,?,?,?)',
                       (request_id, datetime.now(timezone.utc).isoformat(), 'pending', RESERVATION))
            return request_id

    def finish(self, request_id, usage, http_status=None):
        valid = isinstance(usage, dict) and all(type(usage.get(k)) is int and usage[k] >= 0 for k in ('input_tokens', 'output_tokens'))
        clean = {k: usage[k] for k in ('input_tokens', 'output_tokens')} if valid else None
        status = ('reservation_exceeded' if clean['input_tokens'] > RESERVATION else 'recorded') if valid else 'unknown_usage'
        with self.connect() as db:
            changed = db.execute('''UPDATE requests SET completed_utc=?, status=?, input_tokens=?, output_tokens=?, usage_json=?, http_status=?
                WHERE id=? AND status='pending' ''', (datetime.now(timezone.utc).isoformat(), status,
                clean['input_tokens'] if clean else None, clean['output_tokens'] if clean else None,
                json.dumps(clean) if clean else None, http_status, request_id)).rowcount
            if changed != 1:
                raise UsageError('usage_receipt_conflict')
        if status != 'recorded':
            raise UsageError(status)
