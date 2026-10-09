"""Local ledger + MockTransport; never consumes paid provider tokens."""
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from backend.integrations.usage import UsageLedger, UsageError, RESERVATION, MAX_INPUT_TOKENS
from backend.integrations.jev import JevClient, JevError, noul


class UsageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger = UsageLedger(Path(self.tmp.name) / 'usage.sqlite3')
        self.ledger.initialize(0)
        self.payload = {'state': 'MOCK state', 'model': 'jev-test', 'questions': {'q': noul('Test?')}}

    def test_restart_exact_usage_whitelist_and_no_secrets(self):
        ident = self.ledger.reserve(self.payload)
        self.ledger.finish(ident, {'input_tokens': 123, 'output_tokens': 4, 'secret': 'do-not-store'})
        restarted = UsageLedger(self.ledger.path).summary()
        self.assertEqual(restarted['recorded_input_tokens'], 123)
        self.assertEqual(restarted['recorded_output_tokens'], 4)
        self.assertFalse(restarted['blocked'])
        self.assertNotIn(b'do-not-store', self.ledger.path.read_bytes())
        self.assertNotIn(b'MOCK state', self.ledger.path.read_bytes())

    def test_cap_checked_before_transport(self):
        other = UsageLedger(Path(self.tmp.name) / 'full.sqlite3')
        other.initialize(MAX_INPUT_TOKENS - RESERVATION + 1)
        calls = []
        client = JevClient('MOCK', usage_ledger=other, transport=httpx.MockTransport(lambda r: calls.append(r)))
        with self.assertRaisesRegex(JevError, 'usage_budget_blocked'):
            client.ask('Test', self.payload['questions'])
        self.assertEqual(calls, [])

    def test_parallel_workers_cannot_spend_through_pending_reservation(self):
        def reserve(_):
            try:
                return UsageLedger(self.ledger.path).reserve(self.payload)
            except UsageError:
                return None
        with ThreadPoolExecutor(max_workers=8) as pool:
            ids = list(pool.map(reserve, range(8)))
        self.assertEqual(sum(x is not None for x in ids), 1)
        self.assertEqual(self.ledger.summary()['reserved_input_tokens'], RESERVATION)
        self.assertTrue(UsageLedger(self.ledger.path).summary()['blocked'])

    def test_missing_or_invalid_usage_freezes_future_requests(self):
        for usage in (None, {}, {'input_tokens': True, 'output_tokens': 1}, {'input_tokens': -1, 'output_tokens': 0}):
            with self.subTest(usage=usage):
                ledger = UsageLedger(Path(self.tmp.name) / f'case-{len(list(Path(self.tmp.name).iterdir()))}.sqlite3')
                ledger.initialize(0)
                with self.assertRaisesRegex(UsageError, 'unknown_usage'):
                    ledger.finish(ledger.reserve(self.payload), usage)
                self.assertTrue(ledger.summary()['blocked'])
                with self.assertRaisesRegex(UsageError, 'usage_budget_blocked'):
                    ledger.reserve(self.payload)

    def test_account_usage_even_when_answers_invalid(self):
        client = JevClient('MOCK', usage_ledger=self.ledger, transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={'answers': {}, 'usage': {'input_tokens': 77, 'output_tokens': 3}})))
        with self.assertRaisesRegex(JevError, 'invalid_response'):
            client.ask('Test', self.payload['questions'])
        self.assertEqual(self.ledger.summary()['recorded_input_tokens'], 77)

    def test_timeout_and_http_error_remain_accounted(self):
        def timeout(r):
            raise httpx.ReadTimeout('MOCK timeout')
        client = JevClient('MOCK', usage_ledger=self.ledger, transport=httpx.MockTransport(timeout))
        with self.assertRaisesRegex(JevError, 'timeout'):
            client.ask('Test', self.payload['questions'])
        self.assertTrue(self.ledger.summary()['blocked'])
        self.assertEqual(self.ledger.summary()['reserved_input_tokens'], RESERVATION)

    def test_http429_without_usage_blocks_next_request(self):
        client = JevClient('MOCK', usage_ledger=self.ledger, transport=httpx.MockTransport(
            lambda r: httpx.Response(429, json={'error': 'MOCK'})))
        with self.assertRaisesRegex(JevError, 'rate_limited'):
            client.ask('Test', self.payload['questions'])
        self.assertTrue(self.ledger.summary()['blocked'])

    def test_limit_cannot_raise_or_reset_existing_ledger(self):
        with self.assertRaisesRegex(UsageError, 'usage_already_initialized'):
            self.ledger.initialize(0)
        with self.assertRaisesRegex(UsageError, 'invalid_usage_budget'):
            self.ledger.initialize(0, MAX_INPUT_TOKENS + 1)

    def test_oversized_request_never_reserved(self):
        with self.assertRaisesRegex(UsageError, 'usage_request_too_large'):
            self.ledger.reserve({**self.payload, 'state': 'x' * 65537})
        self.assertEqual(self.ledger.summary()['request_count'], 0)

    def test_provider_over_reservation_preserved_and_halts(self):
        with self.assertRaisesRegex(UsageError, 'reservation_exceeded'):
            self.ledger.finish(self.ledger.reserve(self.payload), {'input_tokens': RESERVATION + 1, 'output_tokens': 0})
        self.assertEqual(self.ledger.summary()['recorded_input_tokens'], RESERVATION + 1)
        self.assertTrue(self.ledger.summary()['blocked'])

    def test_missing_and_corrupt_database_never_allows_request(self):
        missing = UsageLedger(Path(self.tmp.name) / 'missing.sqlite3')
        with self.assertRaisesRegex(UsageError, 'usage_not_initialized'):
            missing.reserve(self.payload)
        missing.path.write_text('corrupt')
        with self.assertRaisesRegex(UsageError, 'usage_storage_error'):
            missing.reserve(self.payload)

    def test_duplicate_receipt_does_not_double_count(self):
        ident = self.ledger.reserve(self.payload)
        usage = {'input_tokens': 42, 'output_tokens': 1}
        self.ledger.finish(ident, usage)
        with self.assertRaisesRegex(UsageError, 'usage_receipt_conflict'):
            self.ledger.finish(ident, usage)
        self.assertEqual(self.ledger.summary()['recorded_input_tokens'], 42)


if __name__ == '__main__':
    unittest.main()
