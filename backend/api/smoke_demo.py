"""GET-only demo checks against HTTP and the canonical local business snapshot.

Never runs a recommendation/ranking engine locally. A PASS is an observed response,
not a benchmark, approval, or proof of a new server process (see DEMO_RUNBOOK.md).
"""
import argparse
import json
import math
import sys
from time import perf_counter
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from backend.api.diagnostics import validate_deal_diagnostic, validate_pipeline_diagnostic
from backend.api.priorities import validate_priorities
from backend.api.provenance import collect_evidence_ids, validate_evidence_registry, validate_json
from backend.contracts import DealContext, DealSummary
from backend.graph.context import build_deal_context
from backend.graph.store import get_context_graph
from backend.ingestion.deals import list_deals


SNAPSHOT = '2026-10-01'
DEFAULT_TIMEOUT = 15.0
MAX_TIMEOUT = 60.0


def _require(condition):
    if not condition:
        raise ValueError('Validation failed.')


def _base_url(value):
    _require(isinstance(value, str) and bool(value))
    _require(not any(character.isspace() or ord(character) < 32 or ord(character) == 127
                     for character in value))
    _require(not any(character in value for character in ('?', '#', '\\')))
    parsed = urlsplit(value)
    _require(parsed.scheme in ('http', 'https') and bool(parsed.hostname))
    _require(parsed.username is None and parsed.password is None)
    _require(parsed.port is None or 0 < parsed.port <= 65535)
    return value.rstrip('/')


def _timeout(value):
    result = float(value)
    _require(math.isfinite(result) and 0 < result <= MAX_TIMEOUT)
    return result


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # A redirect must not hide a failing endpoint or change the checked server.
        return None


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's usual error can echo supplied URLs/credentials or other secrets.
        self.exit(2, 'FAIL category=arguments endpoint=configuration status=none\n')


def _version(payload):
    _require(payload['schema_version'] == 'v1' and payload['snapshot_date'] == SNAPSHOT)


def _sources(records, store):
    """Resolve records to original rows, including diagnostic-only direct records."""
    for record in records:
        try:
            rows = store.lookup_evidence(record['id'])
        except KeyError:
            filename, source_id = record['id'].split(':', 1)
            row = store.dataset.by_id.get(filename, {}).get(source_id)
            rows = [] if row is None else [row]
        _require(bool(rows))
        if record['evidence_type'] == 'direct':
            _require(len(rows) == 1)
            row = rows[0]
            _require(record['source_file'] == row.source_file and record['source_id'] == row.source_id)
            _require(json.loads(record['excerpt']) == row.raw)
        else:
            _require(record['id'] in store.evidence)
            expected = store.evidence[record['id']].model_dump()
            validate_evidence_registry([record], {record['id']: expected})


def _detail(payload, context, store):
    DealContext.model_validate(payload, strict=True)
    # Compare the complete raw payload: do not trust an HTTP-provided graph as the
    # ground truth for paths, and do not let model defaults mask omitted fields.
    _require(payload == context.model_dump())
    registry = validate_evidence_registry(payload['evidence'],
                                          {record.id: record.model_dump() for record in context.evidence})
    _require(collect_evidence_ids(payload) <= registry.keys())
    _sources(payload['evidence'], store)


def _diagnostic(payload, context, store):
    _version(payload)
    validate_deal_diagnostic(payload, context)
    _sources(payload['evidence'], store)
    if context.deal.account_id == 'P02':
        requests = [finding for finding in payload['findings']
                    if finding.get('requested_discount_pct') == '20'
                    and 'interactions.jsonl:I0348' in finding['evidence_ids']]
        _require(bool(requests))
        _require(all(finding['decision_lookup']['focus_log_evidence_ids'] == [] for finding in requests))
    elif context.deal.account_id == 'P05':
        _require(any(finding['category'] == 'data_gap' and finding['missing_information']
                     for finding in payload['findings']))


def _priorities(payload, contexts, reports, store):
    validate_priorities(payload, contexts, reports)
    for item in payload['items']:
        _require(bool(item['evidence_paths']) and bool(item['rationale']) and bool(item['factors']))
        _require(bool(item['recommendation']['action']) and bool(item['recommendation']['milestone']))
        _sources(item['evidence'], store)
    items = {item['account_id']: item for item in payload['items']}
    p02 = items['P02']
    _require(any('VP Sales' in approval for approval in p02['recommendation']['approvals_needed']))
    _require('interactions.jsonl:I0348' in p02['recommendation']['evidence_ids'])
    gates = [factor for factor in p02['factors'] if factor['name'] == 'gate_approval_izin']
    _require(any(isinstance(gate['value'], str) and 'VP Sales' in gate['value']
                 and 'tertunda' in gate['value'] and 'interactions.jsonl:I0348' in gate['evidence_ids']
                 for gate in gates))
    p05 = items['P05']
    _require(p05['priority_kind'] == 'discovery' and p05['analysis_status'] == 'insufficient_evidence')
    _require('discovery' in p05['recommendation']['action'].lower())
    _require(bool(p05['recommendation']['unknowns']))
    scores = [factor for factor in p05['factors'] if factor['name'] == 'skor_prioritas']
    _require(bool(scores) and all(factor['value'] is None for factor in scores))


def run_checks(base_url, timeout=DEFAULT_TIMEOUT, *, opener=None, output=None):
    """Return 0 only when all 15 GETs and canonical gates pass; otherwise return 1.

    ``opener`` is an optional urllib-compatible callable for isolated transport
    tests, not a fallback. Each invocation always requests every endpoint afresh.
    Timeout is the urllib socket timeout per request, bounded to (0, 60] seconds.
    """
    output = sys.stdout if output is None else output
    started = perf_counter()
    endpoint, status, category = 'configuration', None, 'configuration'
    request_started = None
    passed = 0

    def check(path, validator, expected_status=200):
        nonlocal endpoint, status, category, request_started, passed
        endpoint, status, category = path, None, 'transport'
        request_started = perf_counter()
        request = Request(base_url + path, method='GET', headers={
            'Accept': 'application/json', 'Cache-Control': 'no-cache, no-store', 'Pragma': 'no-cache',
        })
        try:
            response = opener(request, timeout=timeout)
        except HTTPError as error:
            status = error.code
            if status != expected_status:
                error.close()
                category = 'http'
                raise ValueError('Unexpected HTTP status.') from None
            response = error
        with response:
            status = response.getcode()
            category = 'http'
            _require(type(status) is int and status == expected_status)
            category = 'json'
            payload = json.loads(response.read())
        validate_json(payload)
        category = 'validation'
        validator(payload)
        duration = perf_counter() - request_started
        print(f'PASS {path} status={status} duration={duration:.3f}s', file=output)
        passed += 1
        return payload

    try:
        base_url = _base_url(base_url)
        timeout = _timeout(timeout)
        if opener is None:
            opener = build_opener(_NoRedirect()).open
        endpoint, category = 'canonical', 'canonical'
        deals = list_deals()
        _require(len(deals) == 5)
        _require({(deal.deal_id, deal.account_id) for deal in deals}
                 == {(f'DL-{index:03d}', f'P{index:02d}') for index in range(1, 6)})
        contexts = [build_deal_context(deal.deal_id) for deal in deals]
        _require(all(context.schema_version == 'v1' and context.snapshot_date == SNAPSHOT
                     and context.deal == deal for context, deal in zip(contexts, deals)))
        store = get_context_graph()

        def health(payload):
            _version(payload)
            _require(payload['status'] == 'ok')

        def listing(payload):
            _version(payload)
            items = payload['items']
            _require(isinstance(items, list) and len(items) == len(deals))
            for item in items:
                DealSummary.model_validate(item, strict=True)
            _require(len({item['deal_id'] for item in items}) == len(deals))
            _require({item['deal_id']: item for item in items}
                     == {deal.deal_id: deal.model_dump() for deal in deals})

        check('/health', health)
        check('/api/deals', listing)
        reports = []
        for context in contexts:
            identifier = context.deal.deal_id
            check(f'/api/deals/{identifier}', lambda payload: _detail(payload, context, store))
            reports.append(check(f'/api/deals/{identifier}/initial-analysis',
                                 lambda payload: _diagnostic(payload, context, store)))

        def pipeline(payload):
            _version(payload)
            validate_pipeline_diagnostic(payload, contexts)
            single = {report['deal_id']: {key: value for key, value in report.items()
                                         if key != 'schema_version'} for report in reports}
            combined = {report['deal_id']: {key: value for key, value in report.items()
                                           if key != 'schema_version'} for report in payload['deals']}
            _require(single == combined)
            if 'evidence' in payload:
                _sources(payload['evidence'], store)

        check('/api/pipeline/initial-analysis', pipeline)
        check('/api/pipeline/priorities', lambda payload: _priorities(payload, contexts, reports, store))

        def unknown(payload):
            _require(payload['detail']['code'] == 'DEAL_NOT_FOUND')

        check('/api/deals/DL-999/initial-analysis', unknown, 404)
    except Exception:
        # No exception messages, bodies, supplied URLs, or headers reach output.
        observed = 'none' if type(status) is not int else str(status)
        elapsed = '' if request_started is None else f' duration={perf_counter() - request_started:.3f}s'
        print(f'FAIL category={category} endpoint={endpoint} status={observed}{elapsed}', file=output)
        print(f'FAIL total_duration={perf_counter() - started:.3f}s passed={passed}', file=output)
        return 1
    print(f'PASS total_duration={perf_counter() - started:.3f}s endpoints={passed}', file=output)
    return 0


def main(argv=None):
    parser = _SafeArgumentParser(description='Check the rules demo via GETs; never invokes Jev or local ranking.')
    parser.add_argument('--base-url', required=True, help='HTTP(S) server URL, optionally with a path prefix.')
    parser.add_argument('--timeout', type=_timeout, default=DEFAULT_TIMEOUT,
                        help='Per-request socket timeout in seconds: positive, at most 60 (default: 15).')
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:
        return int(exit_request.code)
    return run_checks(args.base_url, args.timeout)


if __name__ == '__main__':
    raise SystemExit(main())
