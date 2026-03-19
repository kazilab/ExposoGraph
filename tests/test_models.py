"""Tests for ExposoGraph.models."""

import pytest
from pydantic import ValidationError

from ExposoGraph.models import (
    CurationConfidence,
    CurationRecord,
    CurationStatus,
    Edge,
    EdgeType,
    KnowledgeGraph,
    Node,
    NodeType,
    ProvenanceRecord,
)


class TestNode:
    def test_basic_creation(self):
        node = Node(id="CYP1A1", label="CYP1A1", type=NodeType.ENZYME)
        assert node.id == "CYP1A1"
        assert node.type == NodeType.ENZYME

    def test_auto_id_from_label(self):
        node = Node(id="", label="Benzo a pyrene", type=NodeType.CARCINOGEN)
        assert node.id.startswith("Benzo_a_pyrene_")
        assert len(node.id) == len("Benzo_a_pyrene_") + 6  # 6-char hash suffix

    def test_auto_id_simple_label_no_hash(self):
        node = Node(id="", label="CYP1A1", type=NodeType.ENZYME)
        assert node.id == "CYP1A1"

    def test_auto_id_special_chars_get_hash(self):
        n1 = Node(id="", label="Benzo[a]pyrene", type=NodeType.CARCINOGEN)
        n2 = Node(id="", label="Benzo(a)pyrene", type=NodeType.CARCINOGEN)
        # Both sanitize to Benzo_a_pyrene but get different hash suffixes
        assert n1.id != n2.id
        assert n1.id.startswith("Benzo_a_pyrene_")
        assert n2.id.startswith("Benzo_a_pyrene_")

    def test_auto_id_stable_for_same_label(self):
        n1 = Node(id="", label="BaP-7,8-diol", type=NodeType.METABOLITE)
        n2 = Node(id="", label="BaP-7,8-diol", type=NodeType.METABOLITE)
        assert n1.id == n2.id

    def test_explicit_id_preserved(self):
        node = Node(id="custom_id", label="Benzo[a]pyrene", type=NodeType.CARCINOGEN)
        assert node.id == "custom_id"

    def test_generate_id_classmethod(self):
        assert Node.generate_id("CYP1A1") == "CYP1A1"
        assert Node.generate_id("Benzo[a]pyrene").startswith("Benzo_a_pyrene_")

    def test_optional_fields_default_none(self):
        node = Node(id="BaP", label="BaP", type=NodeType.CARCINOGEN)
        assert node.group is None
        assert node.iarc is None
        assert node.activity_score is None

    def test_all_annotation_fields(self):
        node = Node(
            id="CYP1A1",
            label="CYP1A1",
            type=NodeType.ENZYME,
            phase="I",
            role="Activation",
            source_db="KEGG",
            evidence="Well-characterized",
            pmid="12345678",
            tissue="lung",
            variant="CYP1A1*2C",
            phenotype="increased activity",
            activity_score=1.5,
        )
        assert node.activity_score == 1.5
        assert node.variant == "CYP1A1*2C"
        assert len(node.provenance) == 1
        assert node.provenance[0].pmid == "12345678"

    def test_provenance_backfills_legacy_summary_fields(self):
        node = Node(
            id="CYP1A1",
            label="CYP1A1",
            type=NodeType.ENZYME,
            provenance=[
                ProvenanceRecord(
                    source_db="KEGG",
                    record_id="hsa:1543",
                    pmid="12345678",
                    tissue="lung",
                    evidence="Strong literature support",
                )
            ],
        )
        assert node.source_db == "KEGG"
        assert node.pmid == "12345678"
        assert node.tissue == "lung"
        assert node.evidence == "Strong literature support"

    def test_provenance_record_accepts_accession_alias(self):
        record = ProvenanceRecord(accession="1543", source_db="NCBI Gene")
        assert record.record_id == "1543"

    def test_curation_record_supported(self):
        node = Node(
            id="CYP1A1",
            label="CYP1A1",
            type=NodeType.ENZYME,
            curation=CurationRecord(
                status=CurationStatus.REVIEWED,
                confidence=CurationConfidence.HIGH,
                curator="JK",
                reviewed_by="KP",
            ),
        )
        assert node.curation is not None
        assert node.curation.status == CurationStatus.REVIEWED
        assert node.curation.confidence == CurationConfidence.HIGH

    def test_curation_reviewed_at_accepts_valid_dates(self):
        for date_str in ("2026-03-19", "2026-03-19T14:30:00"):
            record = CurationRecord(reviewed_at=date_str)
            assert record.reviewed_at == date_str

    def test_curation_reviewed_at_rejects_invalid_format(self):
        with pytest.raises(ValidationError, match="reviewed_at"):
            CurationRecord(reviewed_at="March 19, 2026")


class TestEdge:
    def test_basic_creation(self):
        edge = Edge(source="CYP1A1", target="BPDE", type=EdgeType.ACTIVATES)
        assert edge.source == "CYP1A1"
        assert edge.type == EdgeType.ACTIVATES

    def test_optional_fields(self):
        edge = Edge(source="A", target="B", type=EdgeType.PATHWAY)
        assert edge.carcinogen is None
        assert edge.tissue is None

    def test_edge_legacy_fields_normalize_to_provenance(self):
        edge = Edge(
            source="A",
            target="B",
            type=EdgeType.PATHWAY,
            source_db="KEGG",
            pmid="12345678",
            evidence="Mapped from pathway reference",
        )
        assert len(edge.provenance) == 1
        assert edge.provenance[0].source_db == "KEGG"
        assert edge.provenance[0].pmid == "12345678"


class TestKnowledgeGraph:
    def test_empty(self):
        kg = KnowledgeGraph()
        assert kg.nodes == []
        assert kg.edges == []

    def test_from_dict(self):
        data = {
            "nodes": [
                {"id": "BaP", "label": "BaP", "type": "Carcinogen"},
                {"id": "CYP1A1", "label": "CYP1A1", "type": "Enzyme"},
            ],
            "edges": [
                {"source": "CYP1A1", "target": "BaP", "type": "ACTIVATES"},
            ],
        }
        kg = KnowledgeGraph(**data)
        assert len(kg.nodes) == 2
        assert len(kg.edges) == 1
        assert kg.nodes[0].type == NodeType.CARCINOGEN

    def test_rejects_edge_with_missing_source(self):
        with pytest.raises(ValidationError, match="missing source node"):
            KnowledgeGraph(
                nodes=[Node(id="A", label="A", type=NodeType.ENZYME)],
                edges=[Edge(source="MISSING", target="A", type=EdgeType.ACTIVATES)],
            )

    def test_rejects_edge_with_missing_target(self):
        with pytest.raises(ValidationError, match="missing target node"):
            KnowledgeGraph(
                nodes=[Node(id="A", label="A", type=NodeType.ENZYME)],
                edges=[Edge(source="A", target="MISSING", type=EdgeType.ACTIVATES)],
            )

    def test_rejects_edge_with_missing_carcinogen(self):
        with pytest.raises(ValidationError, match="missing carcinogen node"):
            KnowledgeGraph(
                nodes=[
                    Node(id="A", label="A", type=NodeType.ENZYME),
                    Node(id="B", label="B", type=NodeType.METABOLITE),
                ],
                edges=[Edge(source="A", target="B", type=EdgeType.ACTIVATES, carcinogen="MISSING")],
            )

    def test_roundtrip_json(self):
        kg = KnowledgeGraph(
            nodes=[
                Node(
                    id="X",
                    label="X",
                    type=NodeType.PATHWAY,
                    provenance=[ProvenanceRecord(source_db="KEGG", url="https://example.org")],
                    curation=CurationRecord(status=CurationStatus.DRAFT, curator="JK"),
                )
            ],
            edges=[],
        )
        dumped = kg.model_dump(mode="json")
        restored = KnowledgeGraph(**dumped)
        assert restored.nodes[0].id == "X"
        assert restored.nodes[0].provenance[0].url == "https://example.org"
        assert restored.nodes[0].curation is not None


class TestNodeTypes:
    @pytest.mark.parametrize("nt", list(NodeType))
    def test_all_node_types_have_string_values(self, nt):
        assert isinstance(nt.value, str)

    @pytest.mark.parametrize("et", list(EdgeType))
    def test_all_edge_types_have_string_values(self, et):
        assert isinstance(et.value, str)
