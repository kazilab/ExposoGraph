"""Export the knowledge graph to various formats.

Primary target: the D3.js viewer at knowledge-graph/index.html, which reads
a GRAPH_DATA constant from graph-data.js.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from .branding import APP_NAME, APP_VERSION
from .engine import GraphEngine
from .models import KnowledgeGraph


def _extract_graph_data_object(raw: str) -> str:
    """Extract the object assigned to ``GRAPH_DATA`` from JS or HTML text."""
    marker = "GRAPH_DATA"
    marker_pos = raw.find(marker)
    if marker_pos == -1:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or start >= end:
            raise ValueError("Could not locate graph data object")
        return raw[start:end + 1]

    start = raw.find("{", marker_pos)
    if start == -1:
        raise ValueError("Could not locate start of GRAPH_DATA object")

    depth = 0
    in_string = False
    string_char = ""
    escape = False

    for idx in range(start, len(raw)):
        ch = raw[idx]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == string_char:
                in_string = False
        else:
            if ch in ('"', "'", "`"):
                in_string = True
                string_char = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return raw[start:idx + 1]

    raise ValueError("Could not find the end of the GRAPH_DATA object")


def _strip_js_comments(raw: str) -> str:
    """Remove JS comments without damaging quoted strings."""
    result: list[str] = []
    in_string = False
    string_char = ""
    escape = False
    in_line_comment = False
    in_block_comment = False
    idx = 0

    while idx < len(raw):
        ch = raw[idx]
        nxt = raw[idx + 1] if idx + 1 < len(raw) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                result.append(ch)
            idx += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                idx += 2
            else:
                idx += 1
            continue

        if in_string:
            result.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == string_char:
                in_string = False
            idx += 1
            continue

        if ch in ('"', "'", "`"):
            in_string = True
            string_char = ch
            result.append(ch)
            idx += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            idx += 2
            continue

        if ch == "/" and nxt == "*":
            in_block_comment = True
            idx += 2
            continue

        result.append(ch)
        idx += 1

    return "".join(result)


def parse_graph_data_text(raw: str) -> KnowledgeGraph:
    """Parse JS/HTML text that contains a ``GRAPH_DATA`` object assignment.

    Handles unquoted keys, single-line comments, and trailing commas
    that are valid in JavaScript but not in JSON.
    """
    js_obj = _extract_graph_data_object(raw)

    # Strip JS comments
    js_obj = _strip_js_comments(js_obj)

    # Quote unquoted object keys:  key: → "key":
    js_obj = re.sub(r"(?<=[{,\n])\s*(\w+)\s*:", r' "\1":', js_obj)

    # Remove trailing commas before } or ]
    js_obj = re.sub(r",\s*([}\]])", r"\1", js_obj)

    data = json.loads(js_obj)
    return KnowledgeGraph(**data)


def parse_graph_data_js(path: str | Path) -> KnowledgeGraph:
    """Parse a ``graph-data.js`` file."""
    raw = Path(path).read_text(encoding="utf-8")
    return parse_graph_data_text(raw)


def parse_graph_html(path: str | Path) -> KnowledgeGraph:
    """Parse a standalone HTML graph export with embedded ``GRAPH_DATA``."""
    raw = Path(path).read_text(encoding="utf-8")
    return parse_graph_data_text(raw)


def parse_graph_artifact(path: str | Path) -> KnowledgeGraph:
    """Parse JSON, JS, or HTML graph artifacts."""
    path = Path(path)
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return KnowledgeGraph(**json.loads(raw))
    return parse_graph_data_text(raw)


def _clean_for_js(obj: Any) -> Any:
    """Strip None values so the JS side sees clean objects."""
    if isinstance(obj, dict):
        return {k: _clean_for_js(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_clean_for_js(i) for i in obj]
    return obj


def _graph_data_script(engine: GraphEngine) -> str:
    data = _clean_for_js(engine.to_dict())
    return f"const GRAPH_DATA = {json.dumps(data, indent=2)};"


def _default_template_candidates() -> list[Path]:
    repo_root = Path(__file__).resolve().parent.parent
    return [
        repo_root / "references" / "knowledge-graph" / "index.html",
        repo_root / "knowledge-graph" / "index.html",
    ]


def _load_viewer_template(template_path: str | Path | None = None) -> str:
    candidates: list[Path] = []
    if template_path is not None:
        template_path = Path(template_path)
        if template_path.is_dir():
            candidates.append(template_path / "index.html")
        else:
            candidates.append(template_path)
    candidates.extend(_default_template_candidates())

    for candidate in candidates:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")

    raise FileNotFoundError("No viewer HTML template was found")


def to_graph_data_js(engine: GraphEngine, path: str | Path) -> Path:
    """Write a ``graph-data.js`` file consumable by the D3 viewer."""
    path = Path(path)
    header = (
        "// ═══════════════════════════════════════════════════════════════\n"
        f"// Auto-generated by {APP_NAME} v{APP_VERSION}\n"
        "// ═══════════════════════════════════════════════════════════════\n\n"
    )

    js = header + _graph_data_script(engine) + "\n"
    path.write_text(js, encoding="utf-8")
    return path


def to_interactive_html_string(
    engine: GraphEngine,
    *,
    template_path: str | Path | None = None,
) -> str:
    """Render a self-contained interactive HTML document."""
    template = _load_viewer_template(template_path)
    data_script = _graph_data_script(engine)
    script_tag = f"<script>\n{data_script}\n</script>"
    external_tag = '<script src="./graph-data.js"></script>'

    if external_tag in template:
        return template.replace(external_tag, script_tag, 1)

    head_close = "</head>"
    if head_close in template:
        return template.replace(head_close, f"{script_tag}\n{head_close}", 1)

    return f"{script_tag}\n{template}"


def to_interactive_html(
    engine: GraphEngine,
    path: str | Path,
    *,
    template_path: str | Path | None = None,
) -> Path:
    """Write a standalone interactive HTML file with embedded graph data."""
    path = Path(path)
    html = to_interactive_html_string(engine, template_path=template_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def ensure_viewer_bundle(
    output_dir: str | Path,
    *,
    template_dir: str | Path | None = None,
) -> Path:
    """Ensure *output_dir* is a usable D3 viewer bundle directory.

    When *template_dir* contains an ``index.html`` file, it is copied into the
    output directory if missing so the generated ``graph-data.js`` has a viewer
    to pair with.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if template_dir is not None:
        template_dir = Path(template_dir)
        template_index = template_dir / "index.html"
        target_index = output_dir / "index.html"
        if template_index.exists() and template_index != target_index and not target_index.exists():
            shutil.copy2(template_index, target_index)

    return output_dir


def export_viewer_bundle(
    engine: GraphEngine,
    output_dir: str | Path,
    *,
    template_dir: str | Path | None = None,
) -> Path:
    """Write a complete viewer bundle directory.

    The resulting folder contains ``graph-data.js`` and, when a template is
    available, ``index.html``.
    """
    output_dir = ensure_viewer_bundle(output_dir, template_dir=template_dir)
    to_graph_data_js(engine, output_dir / "graph-data.js")
    return output_dir


def to_json(engine: GraphEngine, path: str | Path) -> Path:
    """Write a plain JSON export."""
    path = Path(path)
    data = _clean_for_js(engine.to_dict())
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def to_gexf(engine: GraphEngine, path: str | Path) -> Path:
    """Write GEXF (Gephi) format."""
    import networkx as nx

    path = Path(path)
    nx.write_gexf(engine.G, str(path))
    return path
