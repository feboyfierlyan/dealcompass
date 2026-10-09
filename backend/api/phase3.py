"""HTTP adapters for sourced diagnostics and Ical-owned rules priorities."""
from copy import deepcopy
import importlib
import logging

from fastapi import HTTPException

from backend.api.diagnostics import validate_deal_diagnostic, validate_pipeline_diagnostic
from backend.api.priorities import validate_priorities
from backend.graph.analysis import analyze_deal_initial, analyze_pipeline_initial
from backend.graph.context import build_deal_context
from backend.ingestion.deals import list_deals


logger = logging.getLogger(__name__)


class PrioritiesNotImplemented(NotImplementedError):
    """The optional Ical ranking module/function has not been supplied."""


def load_rank_deals():
    """Missing ranking is optional; missing dependencies inside it are failures."""
    try:
        module = importlib.import_module('backend.decision.ranking')
    except ModuleNotFoundError as exc:
        if exc.name == 'backend.decision.ranking':
            raise PrioritiesNotImplemented from None
        raise
    engine = getattr(module, 'rank_deals', None)
    if engine is None:
        raise PrioritiesNotImplemented
    if not callable(engine):
        raise TypeError('Ranking entry point is not callable.')
    return engine


def _unavailable(operation, exc, code):
    # Exception text/tracebacks may contain payloads or provider credentials.
    logger.error('%s failed (%s); exception details withheld.', operation, type(exc).__name__)
    message = ('Ranking tidak tersedia atau gagal validasi kelengkapan, snapshot, sumber dan jalur graph.'
               if code == 'PRIORITIES_UNAVAILABLE' else
               'Diagnostic tidak tersedia atau gagal validasi kelengkapan, snapshot dan sumber.')
    return HTTPException(503, detail={'code': code, 'message': message})


def _not_implemented():
    return HTTPException(501, detail={'code': 'PRIORITIES_NOT_IMPLEMENTED',
                                    'message': 'Fungsi ranking rules Ical belum tersedia.'})


def deal_initial_analysis(deal_id):
    try:
        context = build_deal_context(deal_id)
        result = {'schema_version': 'v1', **analyze_deal_initial(context)}
        return validate_deal_diagnostic(result, context)
    except Exception as exc:
        raise _unavailable('Deal diagnostic', exc, 'DIAGNOSTICS_UNAVAILABLE') from None


def _pipeline_inputs():
    contexts = [build_deal_context(deal.deal_id) for deal in list_deals()]
    result = {'schema_version': 'v1', **analyze_pipeline_initial()}
    validated = validate_pipeline_diagnostic(result, contexts)
    return contexts, validated


def pipeline_initial_analysis():
    try:
        _, result = _pipeline_inputs()
        return result
    except Exception as exc:
        raise _unavailable('Pipeline diagnostic', exc, 'DIAGNOSTICS_UNAVAILABLE') from None


def pipeline_priorities():
    try:
        engine = load_rank_deals()
    except PrioritiesNotImplemented:
        raise _not_implemented() from None
    except Exception as exc:
        raise _unavailable('Ranking dependency', exc, 'PRIORITIES_UNAVAILABLE') from None
    try:
        contexts, diagnostic = _pipeline_inputs()
    except Exception as exc:
        raise _unavailable('Ranking inputs', exc, 'PRIORITIES_UNAVAILABLE') from None
    try:
        # Validate against the original graph, even if an engine mutates its inputs.
        result = engine(deepcopy(contexts), deepcopy(diagnostic['deals']))
    except NotImplementedError:
        raise _not_implemented() from None
    except Exception as exc:
        raise _unavailable('Ranking engine', exc, 'PRIORITIES_UNAVAILABLE') from None
    try:
        return validate_priorities(result, contexts, diagnostic['deals'])
    except Exception as exc:
        raise _unavailable('Ranking output', exc, 'PRIORITIES_UNAVAILABLE') from None
