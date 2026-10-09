"""Explicit TypeSafe live setup/proof; never called by dashboard GETs.

python -m backend.integrations.jev_live --env-file /path/to/.env check|smoke|analyze|serve
No key argument, no shell expansion, no retries, no automatic provider signup.
"""
import argparse
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from backend.integrations.usage import UsageLedger, UsageError

from backend.integrations.jev import DEFAULT_BASE_URL, DEFAULT_MODEL, JevClient, JevError, choice, noul, score

KEYS = {'TYPESAFE_API_KEY', 'TYPESAFE_MODEL', 'TYPESAFE_BASE_URL', 'TYPESAFE_TIMEOUT_S',
        'DEALCOMPASS_ENGINE_MODE', 'DEALCOMPASS_ANALYSIS_BUDGET_S', 'TYPESAFE_USAGE_DB',
        'DEALCOMPASS_ANALYSIS_CACHE_DB', 'DEALCOMPASS_JEV_RETRY_AFTER_S'}


def load_env_file(path):
    """Small literal KEY=value loader, opt-in; existing nonempty env wins."""
    if path is None:
        return
    try:
        text = Path(path).read_text(encoding='utf-8-sig')
        values = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            name, sep, value = line.partition('=')
            name, value = name.strip(), value.strip()
            if not sep:
                raise ValueError
            if name not in KEYS:
                continue
            if value.startswith(('"', "'")):
                if len(value) < 2 or value[-1] != value[0]:
                    raise ValueError
                value = value[1:-1]
            values[name] = value
    except (OSError, ValueError, UnicodeError):
        raise JevError('invalid_env_file') from None
    for name, value in values.items():
        if not os.environ.get(name):
            os.environ[name] = value


def configuration():
    key = os.environ.get('TYPESAFE_API_KEY', '').strip()
    if not key:
        raise JevError('missing_key')
    base = (os.environ.get('TYPESAFE_BASE_URL') or DEFAULT_BASE_URL).rstrip('/')
    # A TypeSafe key must only go to the official endpoint verified in docs.
    if base != DEFAULT_BASE_URL:
        raise JevError('untrusted_endpoint')
    model = os.environ.get('TYPESAFE_MODEL') or DEFAULT_MODEL
    if not model.startswith('jev-') or len(model) > 80 or not all(c.isalnum() or c in '.-_' for c in model):
        raise JevError('invalid_model')
    try:
        timeout = float(os.environ.get('TYPESAFE_TIMEOUT_S') or 20)
        budget = float(os.environ.get('DEALCOMPASS_ANALYSIS_BUDGET_S') or 15)
        if not all(math.isfinite(x) and 0 < x <= 60 for x in (timeout, budget)):
            raise ValueError
    except ValueError:
        raise JevError('invalid_timeout') from None
    # Keep analysis under the existing frontend 20s request timeout.
    budget = min(budget, 15.0)
    return {'api_key': key, 'base_url': base, 'model': model, 'timeout_s': timeout}, budget


def smoke_input():
    """Only two fictional source texts, no whole dataset/contact graph upload."""
    from backend.ingestion.dataset import get_dataset
    ds = get_dataset()
    ids = ['I0296', 'I0348']
    state = {i: ds.by_id['interactions.jsonl'][i].raw['isi'] for i in ids}
    questions = {
        'hambatan': choice('Apa hambatan utama pada pesan I0296? Pilih bukti_kurang bila tidak jelas.', {
            'harga': 'Keberatan harga atau biaya dibanding penawaran pesaing.',
            'referensi': 'Meminta pengalaman pengguna lain.',
            'bukti_kurang': 'Tidak cukup bukti untuk kedua hambatan tersebut.'}),
        'approval': noul('Apakah I0348 menyatakan diskon SUDAH disetujui, bukan sekadar meminta keputusan?'),
        'kejelasan': score('Seberapa eksplisit keberatan harga pada I0296?', [
            'Tidak ada keberatan harga.', 'Harga disebut tetapi keberatannya ambigu.',
            'Keberatan harga dinyatakan jelas.']),
    }
    return state, questions


def receipt(client):
    """Whitelist operational metadata; no raw headers/state/provider error text."""
    calls = []
    for c in client.calls:
        usage = {k: v for k, v in c.usage.items()
                 if k in ('input_tokens', 'output_tokens') and type(v) is int and v >= 0} if isinstance(c.usage, dict) else {}
        model = c.model if (isinstance(c.model, str) and c.model.startswith('jev-')
                            and len(c.model) <= 80 and all(ch.isalnum() or ch in '.-_' for ch in c.model)
                            and (not getattr(client, '_key', '') or client._key not in c.model)) else None
        calls.append({'mode': c.mode, 'model': model, 'latency_ms': c.latency_ms,
                      'error': c.error, 'usage': usage, 'question_keys': c.question_keys})
    return {'request_count': len(calls), 'calls': calls}


def smoke(client):
    state, questions = smoke_input()
    answers = client.ask(state, questions)
    # Live proof requires complete documented distributions, not merely HTTP200.
    for name, q in questions.items():
        answer = answers[name]
        if q['type'] == 'noul':
            continue
        expected = set(q['criteria']) if q['type'] == 'choice' else {str(i) for i in range(len(q['criteria']))}
        probs = answer.get('probabilities')
        if (not isinstance(probs, dict) or set(probs) != expected
                or abs(sum(probs.values()) - 1) > .01 or 'confidence' not in answer):
            raise JevError('incomplete_live_response')
        if q['type'] == 'score' and answer.get('legend') != {str(i): s for i, s in enumerate(q['criteria'])}:
            raise JevError('incomplete_live_response')
    metadata = receipt(client)['calls'][-1]
    if metadata['model'] is None or set(metadata['usage']) != {'input_tokens', 'output_tokens'}:
        raise JevError('incomplete_live_response')
    # Closed output schema, not the complete provider response.
    observed = {'hambatan': answers['hambatan']['choice'], 'approval_noul': answers['approval']['noul'],
                'kejelasan_score': answers['kejelasan']['score']}
    semantic = observed['hambatan'] == 'harga' and observed['approval_noul'] < .5
    return {'status': 'PASS' if semantic else 'REVIEW_REQUIRED', 'live_response_validated': True,
            'source_ids': ['interactions.jsonl:I0296', 'interactions.jsonl:I0348'],
            'observed': observed, 'semantic_check_passed': semantic,
            'note': 'Score/Noul bukan peluang closing; approval tetap dari decision_log.', **receipt(client)}


def analyze(client, deal_id):
    from backend.decision.analyze import analyze_deal_trace
    from backend.graph.context import build_deal_context
    from backend.graph.analysis import analyze_deal_initial
    from evaluation.cases import invariant_checks
    context = build_deal_context(deal_id)
    rec, trace = analyze_deal_trace(context, client=client, diagnostic=analyze_deal_initial(context))
    checks = invariant_checks(rec, trace, context)
    if deal_id == 'DL-002':
        checks['vp_sales_pending'] = any('VP Sales' in a for a in rec.approvals_needed)
    if deal_id == 'DL-005':
        checks['insufficient_evidence'] = trace.analysis_status == 'insufficient_evidence'
    passed = rec.engine_mode == 'jev' and bool(client.calls) and all(c.error is None for c in client.calls) and all(checks.values())
    return {'status': 'PASS' if passed else 'NOT_LIVE_SUCCESS', 'deal_id': deal_id,
            'engine_mode': rec.engine_mode, 'analysis_status': trace.analysis_status,
            'checks': checks, 'note': 'Fallback rules tidak dihitung sebagai sukses Jev.', **receipt(client)}


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'FAIL invalid_arguments (jangan kirim key melalui argumen CLI)\n')


def main(argv=None):
    parser = SafeParser(description=__doc__)
    parser.add_argument('--env-file')
    parser.add_argument('action', choices=['check', 'smoke', 'analyze', 'serve', 'usage', 'init-budget'])
    parser.add_argument('--prior-input-tokens', type=int)
    parser.add_argument('--deal', choices=[f'DL-{i:03}' for i in range(1, 6)], default='DL-002')
    parser.add_argument('--port', type=int, default=8001)
    args = parser.parse_args(argv)
    client = None
    result = {'status': 'BLOCKED', 'request_count': 0}
    try:
        load_env_file(args.env_file)
        if args.action in ('usage', 'init-budget'):
            ledger = UsageLedger()
            if args.action == 'init-budget':
                ledger.initialize(args.prior_input_tokens)
            print(json.dumps({'status': 'USAGE', **ledger.summary()}))
            return 0
        config, budget = configuration()
        os.environ['TYPESAFE_API_KEY'] = config['api_key']
        os.environ['DEALCOMPASS_ENGINE_MODE'] = 'jev'
        os.environ['DEALCOMPASS_ANALYSIS_BUDGET_S'] = str(budget)
        # No recording of provider bodies by this explicit live-proof command.
        os.environ.pop('DEALCOMPASS_RECORD_DIR', None)
        if args.action == 'check':
            result = {'status': 'CONFIGURED_NOT_TESTED', 'key_present': True, 'request_count': 0,
                      'endpoint': DEFAULT_BASE_URL + '/systemone', 'analysis_budget_s': budget}
        elif args.action == 'serve':
            if not 1 <= args.port <= 65535:
                raise JevError('invalid_port')
            import uvicorn
            print('Backend Jev configured; live success requires an actual successful analysis.', flush=True)
            uvicorn.run('backend.main:app', host='127.0.0.1', port=args.port, log_level='info')
            return 0
        else:
            client = JevClient(**config)
            result = smoke(client) if args.action == 'smoke' else analyze(client, args.deal)
    except UsageError as e:
        result = {'status': 'BLOCKED', 'error': str(e), 'request_count': 0}
    except JevError as e:
        result = {'status': 'BLOCKED' if client is None else 'FAIL', 'error': e.code,
                  **(receipt(client) if client else {'request_count': 0})}
    except Exception:
        result = {'status': 'FAIL', 'error': 'unexpected_error',
                  **(receipt(client) if client else {'request_count': 0})}
    result['checked_utc'] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] in ('PASS', 'CONFIGURED_NOT_TESTED') else 1


if __name__ == '__main__':
    raise SystemExit(main())
