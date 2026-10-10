"""Production boundary tests; all provider calls are disabled or mocked."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.deployment import create_app, validate_live_storage
from backend.integrations.usage import UsageLedger, UsageError


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dist = self.root / 'dist'
        (self.dist / 'assets').mkdir(parents=True)
        (self.dist / 'index.html').write_text('<html>DealCompass bundle</html>')
        (self.dist / 'assets' / 'app.js').write_text('console.log("test")')
        self.env = patch.dict(os.environ, {
            'DEALCOMPASS_ENGINE_MODE': 'rules',
            'DEALCOMPASS_DEMO_USER': 'team',
            'DEALCOMPASS_DEMO_PASSWORD': 'test-password-123456',
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = TestClient(create_app(self.dist), base_url='https://demo.test')
        self.auth = ('team', 'test-password-123456')

    def test_health_is_public_but_every_other_surface_requires_login(self):
        self.assertEqual(self.client.get('/health').status_code, 200)
        for path in ('/', '/assets/app.js', '/api/deals', '/docs', '/openapi.json'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 401)
                self.assertIn('Basic', response.headers['www-authenticate'])
        self.assertEqual(self.client.post('/api/deals/DL-001/analysis').status_code, 401)

    def test_wrong_and_malformed_credentials_are_rejected(self):
        self.assertEqual(self.client.get('/', auth=('team', 'wrong')).status_code, 401)
        for header in ('Basic !!!!', 'Basic /w==', 'Bearer anything', 'Basic dGVhbQ=='):
            self.assertEqual(self.client.get('/', headers={'Authorization': header}).status_code, 401)

    def test_bundle_assets_and_api_share_one_origin(self):
        for path, text in (('/', 'DealCompass bundle'), ('/assets/app.js', 'console.log')):
            response = self.client.get(path, auth=self.auth)
            self.assertEqual(response.status_code, 200)
            self.assertIn(text, response.text)
            self.assertEqual(response.headers['cache-control'], 'no-store')
        response = self.client.get('/api/deals', auth=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['items']), 5)

    def test_missing_api_and_files_are_not_disguised_as_spa_html(self):
        for path in ('/api/missing', '/api/deals/DL-999', '/assets/missing.js',
                     '/.env', '/dataset_kasirnusa/accounts.csv', '/unknown'):
            response = self.client.get(path, auth=self.auth)
            self.assertEqual(response.status_code, 404)
            self.assertNotIn('<html>', response.text)

    def test_cross_origin_posts_do_not_reach_paid_analysis(self):
        with patch('backend.main.analyze_deal_envelope') as analyze:
            for headers in ({'Origin': 'https://evil.test'}, {'Origin': 'null'},
                            {'Sec-Fetch-Site': 'cross-site'}):
                response = self.client.post('/api/deals/DL-001/analysis', auth=self.auth, headers=headers)
                self.assertEqual(response.status_code, 403)
            analyze.assert_not_called()

    def test_same_origin_and_authenticated_cli_posts_work(self):
        with patch('backend.main.analyze_deal_envelope', return_value={'test': 'ok'}) as analyze:
            for headers in ({'Origin': 'https://demo.test'}, {}):
                response = self.client.post('/api/deals/DL-001/analysis', auth=self.auth, headers=headers)
                self.assertEqual(response.status_code, 200)
            self.assertEqual(analyze.call_count, 2)

    def test_no_password_no_build_or_ambiguous_mode_fails_startup(self):
        for value in ('', 'short'):
            with patch.dict(os.environ, {'DEALCOMPASS_DEMO_PASSWORD': value}):
                with self.assertRaises(RuntimeError):
                    create_app(self.dist)
        with patch.dict(os.environ, {'DEALCOMPASS_ENGINE_MODE': 'auto'}):
            with self.assertRaises(RuntimeError):
                create_app(self.dist)
        with self.assertRaises(RuntimeError):
            create_app(self.root / 'missing')

    def test_public_mode_needs_no_credentials_and_keeps_cross_origin_guard(self):
        with patch.dict(os.environ, {'DEALCOMPASS_PUBLIC_ACCESS':'1','DEALCOMPASS_DEMO_PASSWORD':''}):
            client = TestClient(create_app(self.dist), base_url='https://demo.test')
            for path in ('/', '/api/deals', '/assets/app.js'):
                self.assertEqual(client.get(path).status_code,200)
            with patch('backend.main.analyze_deal_envelope', return_value={'ok':True}) as analyze:
                self.assertEqual(client.post('/api/deals/DL-001/analysis',headers={'Origin':'https://other.test'}).status_code,403)
                analyze.assert_not_called()
                self.assertEqual(client.post('/api/deals/DL-001/analysis?refresh=true').status_code,200)
                self.assertFalse(analyze.call_args.kwargs['refresh'])

    def test_public_write_rate_is_bounded(self):
        with patch.dict(os.environ, {'DEALCOMPASS_PUBLIC_ACCESS':'1'}):
            client = TestClient(create_app(self.dist),base_url='https://demo.test')
            with patch('backend.main.analyze_deal_envelope', return_value={'ok':True}):
                for _ in range(60): self.assertEqual(client.post('/api/deals/DL-001/analysis').status_code,200)
                self.assertEqual(client.post('/api/deals/DL-001/analysis').status_code,429)

    def live_env(self):
        return patch.dict(os.environ, {
            'DEALCOMPASS_ENGINE_MODE': 'jev',
            'TYPESAFE_USAGE_DB': str(self.root / 'usage.sqlite3'),
            'DEALCOMPASS_ANALYSIS_CACHE_DB': str(self.root / 'cache.sqlite3'),
            'RAILWAY_PROJECT_ID': 'test-project',
            'RAILWAY_VOLUME_MOUNT_PATH': str(self.root),
        })

    def test_live_requires_existing_ledger_never_initializes_or_resets(self):
        with self.live_env(), patch('backend.deployment.configuration'):
            with self.assertRaises(UsageError):
                create_app(self.dist)
            ledger = UsageLedger()
            self.assertFalse(ledger.path.exists())
            ledger.initialize(46540)
            create_app(self.dist)
            self.assertEqual(ledger.summary()['accounted_input_tokens'], 46540)

    def test_pending_receipts_block_live_startup(self):
        with self.live_env(), patch('backend.deployment.configuration'):
            ledger = UsageLedger()
            ledger.initialize(123)
            ledger.reserve({'questions': ['test']})
            with self.assertRaises(RuntimeError):
                create_app(self.dist)
            self.assertEqual(ledger.summary()['pending_requests'], 1)

    def test_cloud_live_requires_volume_and_paths_inside_it(self):
        with self.live_env(), patch('backend.deployment.configuration'):
            for overrides in ({'RAILWAY_VOLUME_MOUNT_PATH': ''},
                              {'TYPESAFE_USAGE_DB': '/tmp/ephemeral.sqlite3'},
                              {'DEALCOMPASS_ANALYSIS_CACHE_DB': 'relative.sqlite3'},
                              {'DEALCOMPASS_ANALYSIS_CACHE_DB': str(self.root / 'usage.sqlite3')}):
                with patch.dict(os.environ, overrides), self.assertRaises(RuntimeError):
                    validate_live_storage()


if __name__ == '__main__':
    unittest.main()
