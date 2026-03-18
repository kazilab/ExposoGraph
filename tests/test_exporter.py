"""Tests for ExposoGraph.exporter."""

import json
import tempfile
from pathlib import Path

from ExposoGraph.engine import GraphEngine
from ExposoGraph.exporter import (
    export_viewer_bundle,
    parse_graph_artifact,
    parse_graph_html,
    parse_graph_data_js,
    to_graph_data_js,
    to_interactive_html,
    to_interactive_html_string,
    to_json,
)
from ExposoGraph.models import Edge, EdgeType, KnowledgeGraph, Node, NodeType


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


class TestGraphDataJs:
    def test_roundtrip(self, tmp_path):
        engine = _sample_engine()
        out = to_graph_data_js(engine, tmp_path / "graph-data.js")
        assert out.exists()

        content = out.read_text()
        assert "GRAPH_DATA" in content
        assert "Auto-generated" in content

        restored = parse_graph_data_js(out)
        assert len(restored.nodes) == 2
        assert len(restored.edges) == 1

    def test_parse_handles_js_syntax(self, tmp_path):
        js_content = """\
const GRAPH_DATA = {
  nodes: [
    { id: "A", label: "A", type: "Enzyme", detail: "test" },
    { id: "B", label: "B", type: "Metabolite", detail: "test" },
  ],
  edges: [
    { source: "A", target: "B", type: "ACTIVATES" },
  ],
};
"""
        p = tmp_path / "test.js"
        p.write_text(js_content)
        kg = parse_graph_data_js(p)
        assert len(kg.nodes) == 2
        assert len(kg.edges) == 1

    def test_parse_strips_comments(self, tmp_path):
        js_content = """\
// This is a comment
const GRAPH_DATA = {
  nodes: [
    // inline comment
    { id: "X", label: "X", type: "Pathway", detail: "test" },
  ],
  edges: [],
};
"""
        p = tmp_path / "commented.js"
        p.write_text(js_content)
        kg = parse_graph_data_js(p)
        assert len(kg.nodes) == 1

    def test_parse_preserves_urls_inside_strings(self, tmp_path):
        js_content = """\
const GRAPH_DATA = {
  nodes: [
    { id: "X", label: "X", type: "Pathway", detail: "https://example.org/pathway" },
  ],
  edges: [],
};
"""
        p = tmp_path / "url.js"
        p.write_text(js_content)
        kg = parse_graph_data_js(p)
        assert kg.nodes[0].detail == "https://example.org/pathway"


class TestJsonExport:
    def test_export_valid_json(self, tmp_path):
        engine = _sample_engine()
        out = to_json(engine, tmp_path / "kg.json")
        data = json.loads(out.read_text())
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1


class TestNoneCleanup:
    def test_none_values_stripped(self, tmp_path):
        engine = _sample_engine()
        out = to_json(engine, tmp_path / "kg.json")
        data = json.loads(out.read_text())
        for node in data["nodes"]:
            assert None not in node.values()


class TestViewerBundle:
    def test_export_viewer_bundle_copies_index_template(self, tmp_path):
        engine = _sample_engine()
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        (template_dir / "index.html").write_text("<html>viewer</html>")

        out_dir = export_viewer_bundle(
            engine,
            tmp_path / "bundle",
            template_dir=template_dir,
        )

        assert out_dir.exists()
        assert (out_dir / "index.html").read_text() == "<html>viewer</html>"
        assert (out_dir / "graph-data.js").exists()


class TestInteractiveHtml:
    def test_html_export_inlines_graph_data(self, tmp_path):
        engine = _sample_engine()
        template = tmp_path / "template.html"
        template.write_text(
            '<html><head><script src="./graph-data.js"></script></head><body></body></html>'
        )

        html = to_interactive_html_string(engine, template_path=template)

        assert "GRAPH_DATA" in html
        assert './graph-data.js' not in html

    def test_html_roundtrip(self, tmp_path):
        engine = _sample_engine()
        template = tmp_path / "template.html"
        template.write_text(
            '<html><head><script src="./graph-data.js"></script></head><body></body></html>'
        )

        out = to_interactive_html(engine, tmp_path / "graph.html", template_path=template)

        restored = parse_graph_html(out)
        assert len(restored.nodes) == 2
        assert len(restored.edges) == 1

    def test_parse_graph_artifact_supports_html(self, tmp_path):
        engine = _sample_engine()
        template = tmp_path / "template.html"
        template.write_text(
            '<html><head><script src="./graph-data.js"></script></head><body></body></html>'
        )
        out = to_interactive_html(engine, tmp_path / "graph.html", template_path=template)

        restored = parse_graph_artifact(out)
        assert len(restored.nodes) == 2
        assert len(restored.edges) == 1
