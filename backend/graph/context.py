"""Public v1 context interface; the dataset has one business snapshot."""
from backend.ingestion.scope import snapshot_date as active_snapshot
from backend.graph.store import get_context_graph

from backend.contracts import DealContext

def build_deal_context(deal_id: str, snapshot_date: str | None = None) -> DealContext:
    """Build a sourced context, not an analysis or reconstructed past snapshot."""
    snapshot_date = active_snapshot().isoformat() if snapshot_date is None else snapshot_date
    if snapshot_date != active_snapshot().isoformat():
        raise ValueError('Requested snapshot does not match this workspace.')
    return get_context_graph().deal_context(deal_id)

