"""Strict, provenance-preserving phase-three ranking wire models."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictFloat, StrictInt, StrictStr


class PriorityWireModel(BaseModel):
    model_config = ConfigDict(extra='allow', strict=True, allow_inf_nan=False)


class PriorityMethodology(PriorityWireModel):
    id: str
    label: str
    description: str
    ordered_rules: list[str]
    tie_breakers: list[str]
    limitations: list[str]


class PriorityFactor(PriorityWireModel):
    name: str
    value: StrictInt | StrictFloat | StrictStr | None
    effect: str
    evidence_ids: list[str]


class PriorityRecommendation(PriorityWireModel):
    schema_version: Literal['v1']
    deal_id: str
    action: str
    owner_id: str | None
    milestone: str
    evidence_ids: list[str]
    precedent_ids: list[str]
    precedent_comparison: list[str]
    approvals_needed: list[str]
    unknowns: list[str]
    engine_mode: Literal['rules']


class PriorityEvidence(PriorityWireModel):
    id: str
    source_file: str
    source_id: str
    date: str | None
    excerpt: str
    evidence_type: Literal['direct', 'inferred']


class PriorityEvidencePath(PriorityWireModel):
    node_ids: list[str]
    edge_ids: list[str]
    evidence_ids: list[str]


class PriorityItem(PriorityWireModel):
    deal_id: str
    account_id: str
    rank: StrictInt
    priority_kind: Literal['acceleration', 'discovery']
    analysis_status: Literal['ready', 'insufficient_evidence']
    rationale: list[str]
    factors: list[PriorityFactor]
    recommendation: PriorityRecommendation
    evidence_ids: list[str]
    evidence: list[PriorityEvidence]
    evidence_paths: list[PriorityEvidencePath]
    limitations: list[str]


class PrioritiesResponse(PriorityWireModel):
    schema_version: Literal['v1']
    snapshot_date: str
    engine_mode: Literal['rules']
    methodology: PriorityMethodology
    items: list[PriorityItem]
    limitations: list[str]
