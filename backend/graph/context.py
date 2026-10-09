"""Public v1 context interface; the dataset has one business snapshot."""
from backend.ingestion.dataset import SNAPSHOT_DATE
from backend.graph.store import get_context_graph

from backend.contracts import DealContext

def build_deal_context(deal_id: str, snapshot_date: str = '2026-10-01') -> DealContext:
    """Build a sourced context, not an analysis or reconstructed past snapshot."""
    if snapshot_date != SNAPSHOT_DATE.isoformat():
        raise ValueError('Hanya snapshot bisnis 2026-10-01 tersedia.')
    return get_context_graph().deal_context(deal_id)

