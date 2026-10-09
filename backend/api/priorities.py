"""Validate ranking output without computing ranking or business readiness."""
from pydantic import ValidationError

from backend.api.phase3_models import PrioritiesResponse
from backend.api.provenance import collect_evidence_ids, validate_evidence_registry, validate_json
from backend.contracts import DealContext


_ERROR = 'Priority result is invalid or incomplete.'


def _require(condition: bool) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _validate_priorities(result: dict, contexts: list[DealContext], diagnostics: list[dict]) -> dict:
    validate_json(result)
    PrioritiesResponse.model_validate(result)
    _require(bool(contexts))
    context_by_id = {context.deal.deal_id: context for context in contexts}
    _require(len(context_by_id) == len(contexts))
    _require(len({context.deal.account_id for context in contexts}) == len(contexts))
    report_by_id = {report['deal_id']: report for report in diagnostics}
    _require(len(report_by_id) == len(diagnostics))
    _require(set(report_by_id) == set(context_by_id))
    items = result['items']
    _require(len(items) == len(contexts))
    _require({item['deal_id'] for item in items} == set(context_by_id))
    _require([item['rank'] for item in items] == list(range(1, len(contexts) + 1)))
    pipeline_evidence_ids = set()
    for item in items:
        context = context_by_id[item['deal_id']]
        report = report_by_id[item['deal_id']]
        _require(context.schema_version == 'v1')
        _require(context.snapshot_date == result['snapshot_date'] == report['snapshot_date'])
        _require(item['account_id'] == context.deal.account_id == report['account_id'])
        canonical = {}
        for record in [e.model_dump() for e in context.evidence] + report['evidence']:
            eid = record['id']
            _require(eid not in canonical or canonical[eid] == record)
            canonical[eid] = record
        validate_json(canonical)
        validate_evidence_registry(list(canonical.values()), canonical)
        registry = validate_evidence_registry(item['evidence'], canonical)
        pipeline_evidence_ids.update(registry)
        _require(collect_evidence_ids(item) <= set(registry))
        recommendation = item['recommendation']
        _require(recommendation['deal_id'] == context.deal.deal_id)
        candidates = {decision['decision_id'] for decision in context.candidate_decisions}
        _require(set(recommendation['precedent_ids']) <= candidates)
        nodes = {node.id for node in context.graph.nodes}
        edges = {edge.id: edge for edge in context.graph.edges}
        for path in item['evidence_paths']:
            path_nodes, path_edges = path['node_ids'], path['edge_ids']
            _require(len(path_nodes) == len(path_edges) + 1)
            _require(set(path_nodes) <= nodes)
            path_evidence = set(path['evidence_ids'])
            _require(path_evidence <= set(registry))
            for index, edge_id in enumerate(path_edges):
                _require(edge_id in edges)
                edge = edges[edge_id]
                _require(edge.source == path_nodes[index] and edge.target == path_nodes[index + 1])
                _require(set(edge.evidence_ids) <= path_evidence)
    _require(collect_evidence_ids(result) <= pipeline_evidence_ids)
    return result


def validate_priorities(result: dict, contexts: list[DealContext], diagnostics: list[dict]) -> dict:
    """Return the original full payload; reject invalid output with a safe message."""
    try:
        return _validate_priorities(result, contexts, diagnostics)
    except (ValueError, ValidationError, KeyError, TypeError, AttributeError, IndexError):
        raise ValueError(_ERROR) from None
