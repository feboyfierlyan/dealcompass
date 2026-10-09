"""Transport mocks only: passing these tests is NOT evidence of provider access."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import httpx

from backend.decision.analyze import analyze_deal_trace
from backend.integrations import jev_live as live
from backend.integrations.jev import JevClient, JevError
from evaluation.cases import mock_client, real


KEY = 'test-secret-never-print'


def response_for(body):
    answers = {}
    for name, q in body['questions'].items():
        if q['type'] == 'choice':
            answers[name] = {'type': 'choice', 'choice': 'harga', 'confidence': .9,
                             'probabilities': {'harga': .96, 'referensi': .02, 'bukti_kurang': .02}}
        elif q['type'] == 'noul':
            answers[name] = {'type': 'noul', 'noul': .02}
        else:
            answers[name] = {'type': 'score', 'score': 1.9, 'confidence': .9,
                             'legend': {str(i): v for i, v in enumerate(q['criteria'])},
                             'probabilities': {'0': 0, '1': .1, '2': .9}}
    return {'model': 'jev-test', 'answers': answers, 'usage': {'input_tokens': 12, 'output_tokens': 6}}


class LiveSetupTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def run_cli(self, args):
        out = io.StringIO()
        with redirect_stdout(out):
            code = live.main(args)
        self.assertNotIn(KEY, out.getvalue())
        return code, json.loads(out.getvalue())

    def test_missing_key_never_constructs_client(self):
        with patch.object(live, 'JevClient') as factory:
            for action in ('check', 'smoke', 'analyze', 'serve'):
                code, result = self.run_cli([action])
                self.assertEqual((code, result['error'], result['request_count']), (1, 'missing_key', 0))
            factory.assert_not_called()

    def test_preflight_is_not_live_success_and_clamps_budget(self):
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': KEY, 'DEALCOMPASS_ANALYSIS_BUDGET_S': '60'}), \
                patch.object(live, 'JevClient') as factory:
            code, result = self.run_cli(['check'])
            factory.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'CONFIGURED_NOT_TESTED')
        self.assertEqual(result['analysis_budget_s'], 15)
        self.assertEqual(result['request_count'], 0)

    def test_env_file_literal_and_process_env_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / '.env'
            f.write_text('# local\nTYPESAFE_API_KEY="$(do-not-run)"\nTYPESAFE_MODEL=jev-latest\nVITE_KEY=ignored\n')
            live.load_env_file(f)
            self.assertEqual(os.environ['TYPESAFE_API_KEY'], '$(do-not-run)')
            self.assertNotIn('VITE_KEY', os.environ)
            os.environ['TYPESAFE_API_KEY'] = KEY
            live.load_env_file(f)
            self.assertEqual(os.environ['TYPESAFE_API_KEY'], KEY)

    def test_malformed_env_does_not_leak_or_partially_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / '.env'
            f.write_text(f'TYPESAFE_API_KEY={KEY}\nTYPESAFE_MODEL="broken\n')
            code, result = self.run_cli(['--env-file', str(f), 'check'])
        self.assertEqual((code, result['error']), (1, 'invalid_env_file'))
        self.assertNotIn('TYPESAFE_API_KEY', os.environ)

    def test_unofficial_endpoints_rejected_before_network(self):
        os.environ['TYPESAFE_API_KEY'] = KEY
        with patch.object(live, 'JevClient') as factory:
            for url in ('http://api.typesafe.ai/v1', 'https://api.typesafe.ai.evil.test/v1',
                        'https://api.typesafe.ai@evil.test/v1', 'https://api.typesafe.ai/v1?x=1'):
                os.environ['TYPESAFE_BASE_URL'] = url
                code, result = self.run_cli(['smoke'])
                self.assertEqual((code, result['error']), (1, 'untrusted_endpoint'))
            factory.assert_not_called()

    def test_invalid_numeric_limits_rejected(self):
        os.environ['TYPESAFE_API_KEY'] = KEY
        for name in ('TYPESAFE_TIMEOUT_S', 'DEALCOMPASS_ANALYSIS_BUDGET_S'):
            for value in ('nan', 'inf', '0', '-1', '61', 'oops'):
                with patch.dict(os.environ, {name: value}):
                    with self.assertRaises(JevError) as err:
                        live.configuration()
                    self.assertEqual(err.exception.code, 'invalid_timeout')

    def test_serve_loopback_normalizes_key_and_disables_recording(self):
        os.environ.update(TYPESAFE_API_KEY='  ' + KEY + '  ', DEALCOMPASS_RECORD_DIR='unsafe')
        with patch('uvicorn.run') as run, redirect_stdout(io.StringIO()):
            self.assertEqual(live.main(['serve', '--port', '8001']), 0)
            run.assert_called_once_with('backend.main:app', host='127.0.0.1', port=8001, log_level='info')
        self.assertEqual(os.environ['TYPESAFE_API_KEY'], KEY)
        self.assertNotIn('DEALCOMPASS_RECORD_DIR', os.environ)
        code, result = self.run_cli(['serve', '--port', '65536'])
        self.assertEqual((code, result['error']), (1, 'invalid_port'))


class LiveProofTests(unittest.TestCase):
    def make_client(self, mutate=None, status=200):
        self.requests = []
        def handler(request):
            self.requests.append(request)
            result = response_for(json.loads(request.content))
            if mutate:
                mutate(result)
            return httpx.Response(status, json=result)
        return JevClient(KEY, transport=httpx.MockTransport(handler))

    def test_smoke_one_request_three_types_actual_fictional_sources(self):
        c = self.make_client()
        result = live.smoke(c)
        self.assertEqual((result['status'], result['request_count']), ('PASS', 1))
        request = self.requests[0]
        self.assertEqual(str(request.url), 'https://api.typesafe.ai/v1/systemone')
        self.assertEqual(request.headers['authorization'], 'Bearer ' + KEY)
        body = json.loads(request.content)
        self.assertEqual(set(body['state']), {'I0296', 'I0348'})
        self.assertEqual({q['type'] for q in body['questions'].values()}, {'choice', 'score', 'noul'})
        self.assertIn('20%', body['state']['I0348'])
        self.assertNotIn(KEY, json.dumps(result))

    def test_shape_complete_but_semantics_wrong_requires_review(self):
        c = self.make_client(lambda r: r['answers']['approval'].update(noul=.98))
        result = live.smoke(c)
        self.assertEqual(result['status'], 'REVIEW_REQUIRED')
        self.assertTrue(result['live_response_validated'])
        self.assertFalse(result['semantic_check_passed'])

    def test_http200_incomplete_distribution_is_not_proof(self):
        for mutate in (lambda r: r['answers']['hambatan'].pop('confidence'),
                       lambda r: r['answers']['hambatan'].update(probabilities={'harga': .96}),
                       lambda r: r['answers']['kejelasan'].update(legend={'0': 'wrong'}),
                       lambda r: r.pop('model'),
                       lambda r: r.update(model=123),
                       lambda r: r.pop('usage')):
            with self.assertRaises(JevError) as err:
                live.smoke(self.make_client(mutate))
            self.assertEqual(err.exception.code, 'incomplete_live_response')

    def test_http_failure_cli_nonzero_with_safe_receipt(self):
        c = self.make_client(status=401)
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': KEY}), patch.object(live, 'JevClient', return_value=c):
            out = io.StringIO()
            with redirect_stdout(out):
                code = live.main(['smoke'])
        result = json.loads(out.getvalue())
        self.assertEqual((code, result['status'], result['error'], result['request_count']), (1, 'FAIL', 'unauthorized', 1))
        self.assertNotIn(KEY, out.getvalue())

    def test_receipt_only_known_metadata(self):
        c = self.make_client()
        live.smoke(c)
        c.calls[0].usage.update(secret=KEY, output_tokens=KEY)
        c.calls[0].model = 'jev-' + KEY + '\n'
        encoded = json.dumps(live.receipt(c))
        self.assertNotIn(KEY, encoded)
        self.assertIsNone(live.receipt(c)['calls'][0]['model'])
        self.assertEqual(live.receipt(c)['calls'][0]['usage'], {'input_tokens': 12})

    def test_mock_analysis_proves_policy_and_fallback_distinction(self):
        result = live.analyze(mock_client(), 'DL-002')
        self.assertEqual(result['status'], 'PASS')  # MOCK; not a real provider claim.
        self.assertTrue(result['checks']['vp_sales_pending'])
        self.assertGreater(result['request_count'], 0)
        failed = live.analyze(mock_client(mode='unauthorized'), 'DL-002')
        self.assertEqual((failed['status'], failed['engine_mode']), ('NOT_LIVE_SUCCESS', 'rules'))
        self.assertTrue(failed['checks']['vp_sales_pending'])

    def test_p05_never_labelled_jev_without_new_calls_even_with_reused_client(self):
        c = mock_client()
        analyze_deal_trace(real('DL-002'), client=c)
        previous = len(c.calls)
        rec, trace = analyze_deal_trace(real('DL-005'), client=c)
        self.assertEqual(len(c.calls), previous)
        self.assertEqual(rec.engine_mode, 'rules')
        self.assertEqual(trace.jev_calls, [])
        self.assertEqual(trace.analysis_status, 'insufficient_evidence')
        self.assertTrue(any('no_eligible_questions' in u for u in rec.unknowns))
        proof = live.analyze(mock_client(), 'DL-005')
        self.assertEqual((proof['status'], proof['request_count']), ('NOT_LIVE_SUCCESS', 0))


if __name__ == '__main__':
    unittest.main()
