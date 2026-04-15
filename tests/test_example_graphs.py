"""Tests for reusable seeded showcase graphs."""

from collections import Counter

from ExposoGraph import (
    build_androgen_module_engine,
    build_androgen_module_graph,
    build_full_legends_architecture_summary,
    build_full_legends_engine,
    build_full_legends_graph,
    pathway_subgraph,
)


def test_full_legends_graph_matches_phase2_target_counts():
    kg = build_full_legends_graph()
    node_types = Counter(node.type.value for node in kg.nodes)
    edge_types = Counter(edge.type.value for edge in kg.edges)

    assert len(kg.nodes) == 98
    assert len(kg.edges) == 110
    assert node_types == {
        "Carcinogen": 15,
        "Enzyme": 38,
        "Metabolite": 28,
        "DNA_Adduct": 11,
        "Pathway": 6,
    }
    assert edge_types == {
        "ACTIVATES": 30,
        "DETOXIFIES": 23,
        "FORMS_ADDUCT": 14,
        "PATHWAY": 19,
        "REPAIRS": 17,
        "TRANSPORTS": 7,
    }


def test_full_legends_engine_loads_and_validates():
    engine = build_full_legends_engine()

    assert engine.node_count == 98
    assert engine.edge_count == 110
    assert engine.validate() == []


def test_full_legends_graph_keeps_key_manuscript_entities():
    engine = build_full_legends_engine()

    for node_id in (
        "DMBA",
        "MeIQx",
        "Benzidine",
        "NDMA",
        "E2",
        "DHT",
        "Benzene",
        "VinylChloride",
        "EthyleneOxide",
        "CYP17A1",
        "SRD5A1",
        "SRD5A2",
        "CYP19A1",
        "AKR1C3",
        "UGT2B17",
        "UGT2B15",
        "AKR1C2",
        "HSD3B2",
        "CYP3A5",
        "COMT",
    ):
        assert engine.get_node(node_id) is not None


def test_full_legends_graph_exposes_curated_kegg_pathways():
    engine = build_full_legends_engine()

    members = pathway_subgraph(engine, "hsa00140")
    assert "CYP17A1" in members
    assert "Testosterone" in members

    members = pathway_subgraph(engine, "hsa05204")
    assert "AFB1" in members
    assert "NNK" in members


def test_full_legends_architecture_summary_matches_seeded_graph():
    summary = build_full_legends_architecture_summary()

    assert summary.node_count == 98
    assert summary.edge_count == 110
    assert summary.node_type_count == 5
    assert summary.edge_type_count == 6
    assert summary.node_type_counts == {
        "Carcinogen": 15,
        "Enzyme": 38,
        "Metabolite": 28,
        "DNA_Adduct": 11,
        "Pathway": 6,
    }
    assert summary.edge_type_counts == {
        "ACTIVATES": 30,
        "DETOXIFIES": 23,
        "TRANSPORTS": 7,
        "FORMS_ADDUCT": 14,
        "REPAIRS": 17,
        "PATHWAY": 19,
    }


def test_full_legends_architecture_summary_keeps_manuscript_inventories():
    summary = build_full_legends_architecture_summary()
    carcinogen_classes = {group.name: group.count for group in summary.carcinogen_classes}
    enzyme_categories = {group.name: group.count for group in summary.enzyme_categories}

    assert carcinogen_classes == {
        "PAH": 2,
        "HCA": 2,
        "Aromatic Amines": 2,
        "Nitrosamines": 2,
        "Mycotoxins": 1,
        "Estrogens": 1,
        "Androgens": 2,
        "Solvents": 2,
        "Alkylating Agents": 1,
    }
    assert enzyme_categories == {
        "Phase I": 14,
        "Phase II": 14,
        "Phase III": 3,
        "DNA Repair": 7,
    }
    assert "DMBA" in summary.carcinogens
    assert "5a-DHT" in summary.carcinogens
    assert "CYP19A1" in summary.enzymes
    assert "UGT2B15" in summary.enzymes
    assert "Chemical carcinogenesis - DNA adducts" in summary.pathway_labels


def test_androgen_module_graph_has_receptor_variant_and_tissue_context():
    kg = build_androgen_module_graph()
    node_types = Counter(node.type.value for node in kg.nodes)
    edge_types = Counter(edge.type.value for edge in kg.edges)
    edge_index = {
        (edge.source, edge.target, edge.type.value, edge.custom_predicate)
        for edge in kg.edges
    }

    assert len(kg.nodes) == 31
    assert len(kg.edges) == 41
    assert node_types == {
        "Carcinogen": 3,
        "Enzyme": 9,
        "Gene": 5,
        "Metabolite": 6,
        "DNA_Adduct": 2,
        "Pathway": 3,
        "Tissue": 3,
    }
    assert edge_types == {
        "ACTIVATES": 3,
        "CUSTOM": 7,
        "DETOXIFIES": 3,
        "FORMS_ADDUCT": 2,
        "PATHWAY": 15,
        "EXPRESSED_IN": 7,
        "ENCODES": 4,
    }
    assert ("SRD5A2", "DHT", "CUSTOM", "CONVERTS_TO_DHT") in edge_index
    assert ("CYP19A1", "E2", "CUSTOM", "AROMATIZES_TO_ESTRADIOL") in edge_index
    assert ("DHT", "AR", "CUSTOM", "BINDS_RECEPTOR") in edge_index
    assert ("AR", "AR_signal_program", "CUSTOM", "ACTIVATES_TRANSCRIPTION") in edge_index
    assert ("AR", "Prostate", "EXPRESSED_IN", None) in edge_index
    assert ("SRD5A2_V89L", "SRD5A2", "ENCODES", None) in edge_index


def test_androgen_module_engine_loads_and_exposes_variant_annotations():
    engine = build_androgen_module_engine()
    ar_node = engine.get_node("AR")
    srd5a2_v89l = engine.get_node("SRD5A2_V89L")
    ugt2b17_deletion = engine.get_node("UGT2B17_copy_number_deletion")

    assert engine.node_count == 31
    assert engine.edge_count == 41
    assert engine.validate() == []
    assert engine.get_node("CYP3A5") is not None
    assert ar_node["type"] == "Gene"
    assert srd5a2_v89l["variant"] == "V89L"
    assert ugt2b17_deletion["phenotype"].startswith("Absent")


def test_full_legends_graph_can_merge_optional_androgen_module():
    kg = build_full_legends_graph(include_androgen_module=True)
    node_types = Counter(node.type.value for node in kg.nodes)
    edge_types = Counter(edge.type.value for edge in kg.edges)

    assert len(kg.nodes) == 109
    assert len(kg.edges) == 143
    assert node_types == {
        "Carcinogen": 15,
        "Enzyme": 38,
        "Gene": 5,
        "Metabolite": 28,
        "DNA_Adduct": 13,
        "Pathway": 7,
        "Tissue": 3,
    }
    assert edge_types == {
        "ACTIVATES": 32,
        "CUSTOM": 7,
        "DETOXIFIES": 24,
        "TRANSPORTS": 7,
        "FORMS_ADDUCT": 16,
        "REPAIRS": 17,
        "PATHWAY": 29,
        "EXPRESSED_IN": 7,
        "ENCODES": 4,
    }


def test_full_legends_architecture_summary_can_include_androgen_module():
    summary = build_full_legends_architecture_summary(include_androgen_module=True)
    enzyme_categories = {group.name: group.count for group in summary.enzyme_categories}

    assert summary.node_count == 109
    assert summary.edge_count == 143
    assert summary.node_type_count == 7
    assert summary.edge_type_count == 9
    assert summary.node_type_counts == {
        "Carcinogen": 15,
        "Enzyme": 38,
        "Gene": 5,
        "Metabolite": 28,
        "DNA_Adduct": 13,
        "Pathway": 7,
        "Tissue": 3,
    }
    assert summary.edge_type_counts == {
        "ACTIVATES": 32,
        "DETOXIFIES": 24,
        "TRANSPORTS": 7,
        "FORMS_ADDUCT": 16,
        "REPAIRS": 17,
        "PATHWAY": 29,
        "EXPRESSED_IN": 7,
        "ENCODES": 4,
        "CUSTOM": 7,
    }
    assert enzyme_categories == {
        "Phase I": 14,
        "Phase II": 14,
        "Phase III": 3,
        "DNA Repair": 7,
    }
    assert "AR proliferative transcriptional program" in summary.pathway_labels
    assert "CYP3A5" in summary.enzymes
