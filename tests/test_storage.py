"""Tests for ExposoGraph.storage."""

from ExposoGraph.engine import GraphEngine
from ExposoGraph.models import Edge, EdgeType, KnowledgeGraph, Node, NodeType
from ExposoGraph.storage import GraphRepository


def _sample_engine() -> GraphEngine:
    engine = GraphEngine()
    kg = KnowledgeGraph(
        nodes=[
            Node(id="BaP", label="Benzo[a]pyrene", type=NodeType.CARCINOGEN),
            Node(id="CYP1A1", label="CYP1A1", type=NodeType.ENZYME),
        ],
        edges=[
            Edge(source="CYP1A1", target="BaP", type=EdgeType.ACTIVATES),
        ],
    )
    engine.load(kg)
    return engine


def _template_path(tmp_path):
    template = tmp_path / "template.html"
    template.write_text(
        '<html><head><script src="./graph-data.js"></script></head><body></body></html>',
        encoding="utf-8",
    )
    return template


class TestGraphRepository:
    def test_save_and_load_latest_revision(self, tmp_path):
        repo = GraphRepository(tmp_path / "graphs.sqlite3")
        engine = _sample_engine()

        saved = repo.save_engine(
            graph_key="bap_demo",
            graph_name="BaP Demo",
            engine=engine,
            template_path=_template_path(tmp_path),
            note="initial",
        )

        assert saved.revision_number == 1
        latest = repo.get_latest_revision("bap_demo")
        assert latest is not None
        assert latest.revision_number == 1
        assert "GRAPH_DATA" in latest.html
        assert len(latest.to_knowledge_graph().nodes) == 2

    def test_save_creates_incrementing_revisions(self, tmp_path):
        repo = GraphRepository(tmp_path / "graphs.sqlite3")
        engine = _sample_engine()
        template = _template_path(tmp_path)

        first = repo.save_engine(
            graph_key="bap_demo",
            graph_name="BaP Demo",
            engine=engine,
            template_path=template,
            note="initial",
        )
        engine.add_node(Node(id="EPHX1", label="EPHX1", type=NodeType.ENZYME))
        second = repo.save_engine(
            graph_key="bap_demo",
            graph_name="BaP Demo",
            engine=engine,
            template_path=template,
            note="added EPHX1",
        )

        assert first.revision_number == 1
        assert second.revision_number == 2

        revisions = repo.list_revisions("bap_demo")
        assert [rev.revision_number for rev in revisions] == [2, 1]
        assert revisions[0].node_count == 3

    def test_list_graphs_returns_latest_revision_per_graph(self, tmp_path):
        repo = GraphRepository(tmp_path / "graphs.sqlite3")
        template = _template_path(tmp_path)

        engine = _sample_engine()
        repo.save_engine(
            graph_key="graph_a",
            graph_name="Graph A",
            engine=engine,
            template_path=template,
        )
        engine.add_node(Node(id="XPC", label="XPC", type=NodeType.ENZYME))
        repo.save_engine(
            graph_key="graph_a",
            graph_name="Graph A",
            engine=engine,
            template_path=template,
        )
        repo.save_engine(
            graph_key="graph_b",
            graph_name="Graph B",
            engine=_sample_engine(),
            template_path=template,
        )

        graphs = repo.list_graphs()
        keys = {graph.graph_key for graph in graphs}
        assert keys == {"graph_a", "graph_b"}
        graph_a = next(graph for graph in graphs if graph.graph_key == "graph_a")
        assert graph_a.revision_number == 2
