"""Pydantic data models for the Carcinogen-Gene Knowledge Graph."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


# ── Enums ────────────────────────────────────────────────────────────────

class NodeType(str, Enum):
    CARCINOGEN = "Carcinogen"
    ENZYME = "Enzyme"
    GENE = "Gene"
    METABOLITE = "Metabolite"
    DNA_ADDUCT = "DNA_Adduct"
    PATHWAY = "Pathway"
    TISSUE = "Tissue"


class EdgeType(str, Enum):
    ACTIVATES = "ACTIVATES"
    DETOXIFIES = "DETOXIFIES"
    TRANSPORTS = "TRANSPORTS"
    FORMS_ADDUCT = "FORMS_ADDUCT"
    REPAIRS = "REPAIRS"
    PATHWAY = "PATHWAY"
    EXPRESSED_IN = "EXPRESSED_IN"
    INDUCES = "INDUCES"
    INHIBITS = "INHIBITS"
    ENCODES = "ENCODES"


class CurationStatus(str, Enum):
    DRAFT = "Draft"
    IN_REVIEW = "In Review"
    REVIEWED = "Reviewed"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class CurationConfidence(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ProvenanceRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_db: Optional[str] = None
    record_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("record_id", "accession"),
    )
    evidence: Optional[str] = None
    pmid: Optional[str] = None
    tissue: Optional[str] = None
    citation: Optional[str] = None
    url: Optional[str] = None


class CurationRecord(BaseModel):
    status: CurationStatus = CurationStatus.DRAFT
    confidence: Optional[CurationConfidence] = None
    curator: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    notes: Optional[str] = None


def _join_unique(values: list[str]) -> str | None:
    seen: list[str] = []
    for value in values:
        cleaned = value.strip()
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    if not seen:
        return None
    return "; ".join(seen)


def _first_nonempty(values: list[str]) -> str | None:
    for value in values:
        cleaned = value.strip()
        if cleaned:
            return cleaned
    return None


def _normalize_provenance_fields(owner: BaseModel, *, summary_only_fields: tuple[str, ...]) -> None:
    provenance = list(getattr(owner, "provenance", []))
    if not provenance:
        legacy = ProvenanceRecord(
            source_db=getattr(owner, "source_db", None),
            evidence=getattr(owner, "evidence", None),
            pmid=getattr(owner, "pmid", None),
            tissue=getattr(owner, "tissue", None),
        )
        if any(legacy.model_dump(exclude_none=True).values()):
            provenance = [legacy]
            setattr(owner, "provenance", provenance)

    if not provenance:
        return

    for field in ("source_db", "pmid", "tissue"):
        if getattr(owner, field, None) is None:
            joined = _join_unique(
                [getattr(item, field) for item in provenance if getattr(item, field)]
            )
            setattr(owner, field, joined)

    for field in summary_only_fields:
        if getattr(owner, field, None) is None:
            first_value = _first_nonempty(
                [getattr(item, field) for item in provenance if getattr(item, field)]
            )
            setattr(owner, field, first_value)


# ── Node ─────────────────────────────────────────────────────────────────

class Node(BaseModel):
    id: str
    label: str
    type: NodeType
    detail: str = ""
    group: Optional[str] = None
    iarc: Optional[str] = None
    phase: Optional[str] = None
    role: Optional[str] = None
    reactivity: Optional[str] = None
    source_db: Optional[str] = None
    evidence: Optional[str] = None
    pmid: Optional[str] = None
    tissue: Optional[str] = None
    variant: Optional[str] = None
    phenotype: Optional[str] = None
    activity_score: Optional[float] = None
    tier: Optional[int] = None
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    curation: Optional[CurationRecord] = None

    @model_validator(mode="after")
    def _normalize(self) -> "Node":
        if not self.id:
            self.id = self.label.replace(" ", "_").replace(",", "")
        _normalize_provenance_fields(self, summary_only_fields=("evidence",))
        return self


# ── Edge ─────────────────────────────────────────────────────────────────

class Edge(BaseModel):
    source: str
    target: str
    type: EdgeType
    label: Optional[str] = None
    carcinogen: Optional[str] = None
    source_db: Optional[str] = None
    evidence: Optional[str] = None
    pmid: Optional[str] = None
    tissue: Optional[str] = None
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    curation: Optional[CurationRecord] = None

    @model_validator(mode="after")
    def _normalize(self) -> "Edge":
        _normalize_provenance_fields(self, summary_only_fields=("evidence",))
        return self


# ── Top-level graph container ────────────────────────────────────────────

class KnowledgeGraph(BaseModel):
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
