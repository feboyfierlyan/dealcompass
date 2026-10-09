"""Kontrak bersama v1. Perubahan dikoordinasikan Main."""
from typing import Literal
from pydantic import BaseModel, Field

class DealSummary(BaseModel):
    deal_id: str
    account_id: str
    account_name: str
    stage: str
    stage_age_days: int
    annual_value: int
    owner_id: str
    rank: int | None = None
    analysis_status: Literal['not_analyzed', 'ready', 'insufficient_evidence'] = 'not_analyzed'

class EvidenceRecord(BaseModel):
    id: str
    source_file: str
    source_id: str
    date: str | None = None
    excerpt: str
    evidence_type: Literal['direct', 'inferred']

class GraphNode(BaseModel):
    id: str
    label: str
    type: str

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: str
    evidence_ids: list[str]
    evidence_type: Literal['direct', 'inferred']
    valid_from: str | None = None
    valid_to: str | None = None

class EvidenceGraph(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)

class DealContext(BaseModel):
    schema_version: Literal['v1'] = 'v1'
    snapshot_date: str = '2026-10-01'
    deal: DealSummary
    evidence: list[EvidenceRecord]
    graph: EvidenceGraph
    candidate_decisions: list[dict] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)

class Recommendation(BaseModel):
    schema_version: Literal['v1'] = 'v1'
    deal_id: str
    action: str
    owner_id: str | None = None
    milestone: str
    evidence_ids: list[str]
    precedent_ids: list[str]
    precedent_comparison: list[str] = Field(default_factory=list)
    approvals_needed: list[str]
    unknowns: list[str]
    engine_mode: Literal['jev', 'rules', 'replay']

