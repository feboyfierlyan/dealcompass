"""Analisis default rules + Jev: cache, single-flight, fallback dan gate. MockTransport/replay saja, nol token berbayar."""
import json
import os
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import httpx

from backend.decision import hybrid
from backend.decision.hybrid import AnalysisCache, AnalysisEnvelope, AnalysisService
from backend.decision.ranking import path_is_valid
from backend.graph.analysis import analyze_deal_initial
from backend.integrations.jev import JevClient, ReplayClient
from backend.integrations.usage import MAX_INPUT_TOKENS, RESERVATION, UsageLedger
from evaluation.cases import add_interaction, mock_transport, real

JEV_ENV = {'DEALCOMPASS_ENGINE_MODE': 'jev', 'TYPESAFE_API_KEY': '', 'TYPESAFE_MODEL': '', 'TYPESAFE_BASE_URL': ''}


class Counter:
    """MockTransport yang menghitung request provider tiruan."""

    def __init__(self, mode='ok', delay_s=0.0, **kw):
        inner = mock_transport(mode, delay_s=delay_s, **kw).handler
        self.requests = 0
        self._lock = threading.Lock()

        def handler(request):
            with self._lock:
                self.requests += 1
            return inner(request)
        self.transport = httpx.MockTransport(handler)
        self.clients = 0

    def factory(self, ledger=None, record_dir=None):
        def make(mode):
            self.clients += 1
            return JevClient('test-key-not-a-cache-key', transport=self.transport, timeout_s=5,
                             usage_ledger=ledger, record_dir=record_dir)
        return make


def inputs(deal_id):
    ctx = real(deal_id)
    return ctx, analyze_deal_initial(ctx)


class HybridAnalysisTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        env = patch.dict(os.environ, JEV_ENV)
        env.start()
        self.addCleanup(env.stop)

    def service(self, counter, ledger=None, path='cache.sqlite3'):
        return AnalysisService(AnalysisCache(self.tmp / path if path else None), client_factory=counter.factory(ledger))

    def run_deal(self, service, deal_id='DL-002', refresh=False, ctx=None):
        ctx_, diag = inputs(deal_id) if ctx is None else (ctx, analyze_deal_initial(ctx))
        out = service.analyze(deal_id, refresh=refresh, context=ctx_, diagnostic=diag)
        AnalysisEnvelope.model_validate(out)
        return out

    def test_rules_mode_is_rules_only_without_provider(self):
        counter = Counter()
        with patch.dict(os.environ, {'DEALCOMPASS_ENGINE_MODE': 'rules'}):
            out = self.run_deal(self.service(counter))
        meta = out['analysis']
        self.assertEqual((meta['outcome'], meta['engine_mode'], meta['cache'], meta['provider_requests']),
                         ('rules_only', 'rules', 'none', 0))
        self.assertEqual((counter.clients, counter.requests), (0, 0))
        self.assertTrue(any(a.startswith('VP Sales (E01)') for a in out['recommendation']['approvals_needed']))

    def test_jev_success_becomes_active_hybrid_with_gates_and_real_paths(self):
        counter = Counter()
        out = self.run_deal(self.service(counter))
        rec, meta = out['recommendation'], out['analysis']
        self.assertEqual((meta['outcome'], meta['engine_mode'], rec['engine_mode'], meta['cache']), ('jev_applied', 'jev', 'jev', 'fresh'))
        self.assertEqual(meta['provider_requests'], counter.requests)
        self.assertGreater(counter.requests, 1, 'one workflow may contain several provider requests')
        self.assertEqual(meta['model'], 'jev-mock')
        self.assertIsNone(meta['fallback_reason'])
        self.assertTrue(any(a.startswith('VP Sales (E01)') for a in rec['approvals_needed']))
        self.assertTrue(rec['action'].startswith('USULAN:'))
        ctx = real('DL-002')
        self.assertTrue(set(rec['evidence_ids']) <= {e.id for e in ctx.evidence})
        self.assertTrue(meta['evidence_paths'])
        self.assertEqual(meta['gate'], 'approval VP Sales tertunda')
        for p in meta['evidence_paths']:
            self.assertTrue(path_is_valid(ctx.graph, p))
        self.assertNotIn('test-key-not-a-cache-key', json.dumps(out))

    def test_cache_hit_adds_no_provider_request_and_keeps_provenance(self):
        counter = Counter()
        service = self.service(counter)
        first = self.run_deal(service)
        before = counter.requests
        second = self.run_deal(service)
        self.assertEqual(counter.requests, before)
        self.assertEqual(service.workflows, 1)
        self.assertEqual(second['analysis']['cache'], 'hit')
        for k in ('analysis_id', 'generated_at', 'provider_requests', 'model', 'analysis_version', 'context_fingerprint'):
            self.assertEqual(second['analysis'][k], first['analysis'][k], k)
        self.assertEqual(second['recommendation'], first['recommendation'])

    def test_persistent_cache_survives_restart_and_is_separate_from_ledger(self):
        counter = Counter()
        ledger = UsageLedger(self.tmp / 'usage.sqlite3')
        ledger.initialize(0)
        first = self.run_deal(self.service(counter, ledger))
        self.assertEqual(ledger.summary()['request_count'], first['analysis']['provider_requests'])
        restarted = self.service(Counter(), ledger)
        again = self.run_deal(restarted)
        self.assertEqual((again['analysis']['cache'], restarted.workflows), ('hit', 0))
        self.assertEqual(ledger.summary()['request_count'], first['analysis']['provider_requests'], 'cache hit is not billed')
        self.assertNotEqual(ledger.path, self.tmp / 'cache.sqlite3')
        self.assertNotIn(b'test-key', (self.tmp / 'cache.sqlite3').read_bytes())

    def test_context_change_on_same_snapshot_invalidates_cache(self):
        counter = Counter()
        service = self.service(counter)
        first = self.run_deal(service)
        ctx = add_interaction(real('DL-002'), 'IXSYN1', 'P02', '2026-09-30', 'Kami masih menimbang harga paket.')
        self.assertEqual(ctx.snapshot_date, '2026-10-01')
        changed = self.run_deal(service, ctx=ctx)
        self.assertEqual(changed['analysis']['cache'], 'fresh')
        self.assertNotEqual(changed['analysis']['context_fingerprint'], first['analysis']['context_fingerprint'])
        self.assertEqual(service.workflows, 2)

    def test_analysis_version_or_model_change_invalidates_cache(self):
        counter = Counter()
        service = self.service(counter)
        self.run_deal(service)
        with patch.object(hybrid, 'analysis_version', return_value='rules+jev/1+other'):
            self.assertEqual(self.run_deal(service)['analysis']['cache'], 'fresh')
        with patch.dict(os.environ, {'TYPESAFE_MODEL': 'jev-other'}):
            self.assertEqual(self.run_deal(service)['analysis']['cache'], 'fresh')
        self.assertEqual(service.workflows, 3)

    def test_api_key_is_not_part_of_cache_key(self):
        counter = Counter()
        service = self.service(counter)
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'key-one'}):
            first = self.run_deal(service)
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'key-two'}):
            second = self.run_deal(service)
        self.assertEqual((second['analysis']['cache'], service.workflows), ('hit', 1))
        self.assertEqual(first['analysis']['analysis_id'], second['analysis']['analysis_id'])

    def test_concurrent_requests_share_one_workflow(self):
        counter = Counter(delay_s=0.05)
        service = self.service(counter)
        ctx, diag = inputs('DL-002')
        with ThreadPoolExecutor(4) as pool:
            outs = list(pool.map(lambda _: service.analyze('DL-002', context=ctx, diagnostic=diag), range(4)))
        self.assertEqual(service.workflows, 1)
        self.assertEqual(counter.clients, 1)
        self.assertEqual(sorted(o['analysis']['cache'] for o in outs).count('fresh'), 1)
        self.assertEqual({o['analysis']['analysis_id'] for o in outs}, {outs[0]['analysis']['analysis_id']})
        self.assertEqual(counter.requests, outs[0]['analysis']['provider_requests'])

    def test_failure_falls_back_honestly_and_is_not_retried_by_navigation(self):
        for mode, reason in (('timeout', 'timeout'), ('unauthorized', 'unauthorized'), ('bad_choice', 'invalid_response')):
            with self.subTest(mode=mode):
                counter = Counter(mode)
                service = self.service(counter, path=None)
                out = self.run_deal(service)
                rec, meta = out['recommendation'], out['analysis']
                self.assertEqual((meta['outcome'], meta['engine_mode'], rec['engine_mode']), ('jev_unavailable', 'rules', 'rules'))
                self.assertEqual(meta['fallback_reason'], reason)
                self.assertTrue(any(a.startswith('VP Sales (E01)') for a in rec['approvals_needed']))
                self.assertTrue(any(f'gagal: {reason}' in u for u in rec['unknowns']))
                before = counter.requests
                again = self.run_deal(service)
                self.assertEqual((again['analysis']['cache'], again['analysis']['outcome'], counter.requests),
                                 ('hit', 'jev_unavailable', before))
                self.run_deal(service, refresh=True)
                self.assertEqual(service.workflows, 2, 'only a deliberate refresh retries')

    def test_failure_retry_window_expires(self):
        clock = [1000.0]
        counter = Counter('timeout')
        service = AnalysisService(AnalysisCache(None), client_factory=counter.factory(), monotonic=lambda: clock[0])
        self.run_deal(service)
        clock[0] += hybrid.DEFAULT_RETRY_AFTER_S + 1
        self.run_deal(service)
        self.assertEqual(service.workflows, 2)

    def test_usage_blocked_ledger_falls_back_without_transport(self):
        counter = Counter()
        ledger = UsageLedger(self.tmp / 'full.sqlite3')
        ledger.initialize(MAX_INPUT_TOKENS - RESERVATION + 1)
        out = self.run_deal(self.service(counter, ledger))
        self.assertEqual((out['analysis']['outcome'], out['analysis']['fallback_reason']), ('jev_unavailable', 'usage_budget_blocked'))
        self.assertEqual(counter.requests, 0)
        self.assertEqual(ledger.summary()['request_count'], 0)

    def test_insufficient_evidence_p05_never_creates_a_client(self):
        def forbidden(mode):
            raise AssertionError('P05 must not call the provider')
        service = AnalysisService(AnalysisCache(None), client_factory=forbidden)
        out = self.run_deal(service, 'DL-005')
        meta = out['analysis']
        self.assertEqual((meta['outcome'], meta['analysis_status'], meta['provider_requests'], meta['engine_mode']),
                         ('not_eligible', 'insufficient_evidence', 0, 'rules'))
        self.assertTrue(any('bukan berarti tidak ada risiko' in u for u in out['recommendation']['unknowns']))

    def test_jev_result_that_drops_a_rules_gate_is_rejected(self):
        counter = Counter(choice_fn=lambda state: 'tanpa_hambatan')
        out = self.run_deal(self.service(counter, path=None))
        meta, rec = out['analysis'], out['recommendation']
        self.assertEqual((meta['outcome'], meta['fallback_reason'], rec['engine_mode']),
                         ('jev_unavailable', 'approval_gate_dropped', 'rules'))
        self.assertGreater(meta['provider_requests'], 0, 'tokens were spent and are reported')
        self.assertTrue(any(a.startswith('VP Sales (E01)') for a in rec['approvals_needed']))

    def test_reference_consent_survives_hybrid_for_reference_deals(self):
        for deal_id in ('DL-003', 'DL-004'):
            with self.subTest(deal=deal_id):
                out = self.run_deal(self.service(Counter(), path=None), deal_id)
                self.assertEqual(out['analysis']['outcome'], 'jev_applied')
                self.assertTrue(any('kandidat bukan izin' in u for u in out['recommendation']['unknowns']))

    def test_replay_is_labelled_replay_not_live(self):
        record = self.tmp / 'replay'
        counter = Counter()
        recorder = AnalysisService(AnalysisCache(None), client_factory=counter.factory(record_dir=str(record)))
        self.run_deal(recorder)
        with patch.dict(os.environ, {'DEALCOMPASS_ENGINE_MODE': 'replay', 'DEALCOMPASS_REPLAY_DIR': str(record)}):
            service = AnalysisService(AnalysisCache(None), client_factory=lambda mode: ReplayClient(str(record)))
            out = self.run_deal(service)
        self.assertEqual((out['analysis']['outcome'], out['analysis']['engine_mode'], out['recommendation']['engine_mode']),
                         ('jev_applied', 'replay', 'replay'))

    def test_gate_matches_ranking_factor_for_rules_results(self):
        from backend.api.phase3 import pipeline_priorities
        with patch.dict(os.environ, {'DEALCOMPASS_ENGINE_MODE': 'rules'}):
            ranking = {i['deal_id']: i for i in pipeline_priorities()['items']}
            service = AnalysisService(AnalysisCache(None))
            for deal_id, item in ranking.items():
                with self.subTest(deal=deal_id):
                    out = self.run_deal(service, deal_id)
                    gate = next(f['value'] for f in item['factors'] if f['name'] == 'gate_approval_izin')
                    self.assertEqual(out['analysis']['gate'], gate)
                    self.assertEqual(out['recommendation'], item['recommendation'])

    def test_deals_are_isolated_by_key(self):
        service = self.service(Counter(), path=None)
        a, b = self.run_deal(service, 'DL-002'), self.run_deal(service, 'DL-004')
        self.assertEqual((a['deal_id'], a['recommendation']['deal_id']), ('DL-002', 'DL-002'))
        self.assertEqual((b['deal_id'], b['recommendation']['deal_id']), ('DL-004', 'DL-004'))
        self.assertNotEqual(a['analysis']['analysis_id'], b['analysis']['analysis_id'])


if __name__ == '__main__':
    unittest.main()
