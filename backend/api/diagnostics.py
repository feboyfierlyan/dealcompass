"""Validate factual diagnostic envelopes without response-model truncation."""
from datetime import date
import json

from backend.api.provenance import collect_evidence_ids, validate_evidence_registry, validate_json
from backend.contracts import DealContext, EvidenceRecord
from backend.graph.store import get_context_graph
from backend.ingestion.metrics import evidence_id, summarize_deal


def _canonical_evidence(records=()) -> dict[str, dict]:
    store = get_context_graph()
    canonical = {identifier: record.model_dump() for identifier, record in store.evidence.items()}
    # Resolve only requested direct rows outside graph scope, never scan daily usage.
    for record in records:
        identifier = record.get('id') if isinstance(record, dict) else None
        if not isinstance(identifier, str) or identifier in canonical or ':' not in identifier:
            continue
        filename, source_id = identifier.split(':', 1)
        row = store.dataset.by_id.get(filename, {}).get(source_id)
        if row is None:
            continue
        when = next((row.values.get(key) for key in ('tanggal', 'dibuat', 'mulai')
                     if isinstance(row.values.get(key), date)), None)
        canonical[identifier] = EvidenceRecord(
            id=identifier, source_file=row.source_file, source_id=row.source_id,
            date=when.isoformat() if when else None,
            excerpt=json.dumps(row.raw, ensure_ascii=False), evidence_type='direct',
        ).model_dump()
    return canonical


def _required(value, fields, kind=dict):
    if not isinstance(value, kind) or any(field not in value for field in fields):
        raise ValueError('Diagnostic report is incomplete or has an invalid schema.')


def _canonical_fields(value, expected):
    """Require all canonical metric fields, permitting arbitrary extra provenance."""
    if isinstance(expected, dict):
        _required(value, expected)
        for key, child in expected.items():
            _canonical_fields(value[key], child)
    elif type(value) is not type(expected) or value != expected:
        raise ValueError('Diagnostic metrics do not match the canonical scope or values.')


def _deal(report, context, canonical):
    _required(report, ('deal_id', 'account_id', 'snapshot_date', 'metrics', 'findings',
                       'reference_candidates', 'boundaries', 'evidence'))
    if ('schema_version' in report and report['schema_version'] != 'v1'):
        raise ValueError('Diagnostic schema version is invalid.')
    if (report['deal_id'] != context.deal.deal_id
            or report['account_id'] != context.deal.account_id
            or report['snapshot_date'] != context.snapshot_date):
        raise ValueError('Diagnostic deal, account or snapshot does not match its context.')
    _canonical_fields(report['metrics'], summarize_deal(context.deal.deal_id))
    if not isinstance(report['boundaries'], list) or any(not isinstance(item, str) for item in report['boundaries']):
        raise ValueError('Diagnostic boundaries must be an array of strings.')
    for field in ('findings', 'reference_candidates'):
        if not isinstance(report[field], list):
            raise ValueError('Diagnostic findings must be arrays.')
        for finding in report[field]:
            _required(finding, ('finding_id', 'category', 'fact', 'evidence_ids', 'interpretation',
                                'interpretation_type', 'missing_information', 'follow_up_implication'))
            for key in ('finding_id', 'category', 'fact', 'interpretation', 'interpretation_type'):
                if not isinstance(finding[key], str):
                    raise ValueError('Diagnostic finding text is invalid.')
            for key in ('missing_information', 'follow_up_implication'):
                if not isinstance(finding[key], list) or any(not isinstance(item, str) for item in finding[key]):
                    raise ValueError('Diagnostic finding details must be arrays of strings.')
            for key in ('decision_lookup', 'search_scope'):
                if key in finding:
                    scope = finding[key]
                    _required(scope, ('account_id', 'through'))
                    if scope['account_id'] != context.deal.account_id or scope['through'] != context.snapshot_date:
                        raise ValueError('Diagnostic lookup scope does not match its context.')
                    if 'deal_id' in scope and scope['deal_id'] != context.deal.deal_id:
                        raise ValueError('Diagnostic lookup deal does not match its context.')
    registry = validate_evidence_registry(report['evidence'], canonical)
    if not collect_evidence_ids(report) <= registry.keys():
        raise ValueError('Diagnostic references are missing from the evidence registry.')
    return report, registry


def validate_deal_diagnostic(report: dict, context: DealContext) -> dict:
    """Return the entire report unchanged, or a safe ValueError for malformed data."""
    validate_json(report)
    _required(report, ('evidence',))
    records = report['evidence'] if isinstance(report['evidence'], list) else []
    result, _ = _deal(report, context, _canonical_evidence(records))
    return result


def validate_pipeline_diagnostic(report: dict, contexts: list[DealContext]) -> dict:
    """Validate the complete five-context pipeline and statistical provenance."""
    validate_json(report)
    _required(report, ('snapshot_date', 'deals', 'statistical_assessment'))
    if 'schema_version' in report and report['schema_version'] != 'v1':
        raise ValueError('Diagnostic schema version is invalid.')
    from backend.ingestion.deals import list_deals
    expected = {d.deal_id for d in list_deals()}
    if len(contexts) != len(expected) or {c.deal.deal_id for c in contexts} != expected:
        raise ValueError('Pipeline requires every workspace deal exactly once.')
    if any(context.snapshot_date != report['snapshot_date'] for context in contexts):
        raise ValueError('Pipeline snapshot does not match its contexts.')
    if not isinstance(report['deals'], list) or len(report['deals']) != len(contexts):
        raise ValueError('Pipeline requires every deal exactly once.')
    context_map = {context.deal.deal_id: context for context in contexts}
    records = [record for deal in report['deals']
               if isinstance(deal, dict) and isinstance(deal.get('evidence'), list)
               for record in deal['evidence']]
    if isinstance(report.get('evidence'), list):
        records.extend(report['evidence'])
    canonical = _canonical_evidence(records)
    registry = {}
    seen = set()
    for deal in report['deals']:
        _required(deal, ('deal_id',))
        identifier = deal['deal_id']
        if not isinstance(identifier, str) or identifier not in context_map or identifier in seen:
            raise ValueError('Pipeline contains an unknown or duplicate deal.')
        seen.add(identifier)
        _, evidence = _deal(deal, context_map[identifier], canonical)
        registry.update(evidence)
    # Statistical IDs can also be registered by the canonical input contexts.
    for context in contexts:
        registry.update(validate_evidence_registry([record.model_dump() for record in context.evidence], canonical))
    if 'evidence' in report:
        registry.update(validate_evidence_registry(report['evidence'], canonical))
    assessment = report['statistical_assessment']
    _required(assessment, ('status', 'sample_size', 'stage_cohort_counts', 'method', 'threshold',
                           'outlier_deal_ids', 'evidence_ids', 'reason'))
    cohorts = {}
    for context in contexts:
        stage = context.deal.stage
        cohorts[stage] = cohorts.get(stage, 0) + 1
    _canonical_fields(assessment, dict(status='not_assessed', sample_size=len(contexts),
                                     stage_cohort_counts=cohorts, method=None,
                                     threshold=None, outlier_deal_ids=None))
    if not isinstance(assessment['reason'], str):
        raise ValueError('Statistical assessment reason must be text.')
    if not collect_evidence_ids(report) <= registry.keys():
        raise ValueError('Pipeline evidence references are not registered.')
    return report
