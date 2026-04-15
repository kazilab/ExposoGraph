"""Advanced Dash Cytoscape viewer for ExposoGraph."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, TypeVar, cast

from .branding import APP_NAME
from .config import GraphVisibility
from .cytoscape_adapter import (
    CytoscapeBundle,
    ViewerLayoutMode,
    build_cytoscape_bundle,
    load_cytoscape_bundle,
    normalize_viewer_layout_mode,
    viewer_layout,
)
from .engine import GraphEngine
from .models import KnowledgeGraph

cyto: Any
ALL: Any
DashApp: Any
DashInput: Any
DashOutput: Any
DashState: Any
ctx: Any
dcc: Any
html: Any
no_update: Any
_DASH_IMPORT_ERROR: ImportError | None
_CallbackFunc = TypeVar("_CallbackFunc", bound=Callable[..., Any])

try:  # pragma: no cover - exercised through runtime integration
    import dash_cytoscape as _cyto
    from dash import (
        ALL as _ALL,
        Dash as _DashApp,
        Input as _DashInput,
        Output as _DashOutput,
        State as _DashState,
        ctx as _ctx,
        dcc as _dcc,
        html as _html,
        no_update as _no_update,
    )
except ImportError as exc:  # pragma: no cover - tested via helper raising
    cyto = cast(Any, None)
    ALL = cast(Any, None)
    DashApp = cast(Any, None)
    DashInput = cast(Any, None)
    DashOutput = cast(Any, None)
    DashState = cast(Any, None)
    ctx = cast(Any, None)
    dcc = cast(Any, None)
    html = cast(Any, None)
    no_update = cast(Any, None)
    _DASH_IMPORT_ERROR = exc
else:
    cyto = _cyto
    ALL = _ALL
    DashApp = _DashApp
    DashInput = _DashInput
    DashOutput = _DashOutput
    DashState = _DashState
    ctx = _ctx
    dcc = _dcc
    html = _html
    no_update = _no_update
    _DASH_IMPORT_ERROR = None


@dataclass(frozen=True)
class ViewerState:
    elements: list[dict[str, Any]]
    layout: dict[str, Any]
    visible_node_count: int
    visible_edge_count: int
    node_type_counts: dict[str, int]
    edge_type_counts: dict[str, int]


_SIDEBAR_STYLE = {
    "background": "#121a27",
    "border": "1px solid rgba(124, 154, 185, 0.22)",
    "borderRadius": "18px",
    "padding": "18px",
    "display": "flex",
    "flexDirection": "column",
    "gap": "16px",
    "minWidth": "320px",
}

_CARD_STYLE = {
    "background": "rgba(18, 26, 39, 0.84)",
    "border": "1px solid rgba(124, 154, 185, 0.18)",
    "borderRadius": "14px",
    "padding": "12px 14px",
}

_PANEL_TITLE_STYLE = {
    "fontSize": "0.76rem",
    "fontWeight": 700,
    "letterSpacing": "0.08em",
    "textTransform": "uppercase",
    "color": "#8da3bc",
    "marginBottom": "8px",
}

_INPUT_STYLE = {
    "width": "100%",
    "padding": "10px 12px",
    "borderRadius": "10px",
    "border": "1px solid rgba(124, 154, 185, 0.25)",
    "background": "#0a121f",
    "color": "#e6edf7",
}

_ACTION_BUTTON_STYLE = {
    "border": "1px solid rgba(124, 154, 185, 0.22)",
    "background": "linear-gradient(180deg, rgba(15, 25, 41, 0.96), rgba(9, 15, 27, 0.98))",
    "color": "#e6edf7",
    "borderRadius": "10px",
    "padding": "9px 12px",
    "fontSize": "0.84rem",
    "fontWeight": 600,
    "cursor": "pointer",
    "boxShadow": "inset 0 1px 0 rgba(255,255,255,0.04)",
}

_HOVER_TOOLTIP_STYLE = {
    "position": "absolute",
    "top": "18px",
    "left": "18px",
    "zIndex": 60,
    "maxWidth": "320px",
    "padding": "12px 14px",
    "borderRadius": "14px",
    "border": "1px solid rgba(124, 154, 185, 0.18)",
    "background": "linear-gradient(180deg, rgba(13, 21, 34, 0.96), rgba(8, 14, 24, 0.98))",
    "boxShadow": "0 18px 34px rgba(0, 0, 0, 0.24)",
    "pointerEvents": "none",
}


_GENOTYPE_PROFILES: dict[str, dict[str, float]] = {
    "normal": {},
    "bap_high_risk": {"CYP1A1": 1.3, "GSTM1": 0.0},
    "nat2_slow": {"NAT2": 0.5},
    "cyp2e1_high": {"CYP2E1": 1.3},
}

_GENOTYPE_MESSAGES: dict[str, str] = {
    "normal": "Baseline profile: no genotype overrides applied.",
    "bap_high_risk": (
        "BaP high-risk: CYP1A1 activation edges become bolder and GSTM1 detoxification "
        "edges fade toward an absent-function state."
    ),
    "nat2_slow": (
        "NAT2 slow acetylator: NAT2-linked activation and detoxification edges are "
        "dimmed to reflect reduced catalytic capacity."
    ),
    "cyp2e1_high": (
        "CYP2E1 high activity: CYP2E1-driven activation edges become bolder to show "
        "stronger bioactivation context."
    ),
}

_ACTIVITY_EDGE_TYPES = {"ACTIVATES", "DETOXIFIES", "REPAIRS"}


def _genotype_node_background_opacity(score: float) -> float:
    if score == 0.0:
        return 0.18
    if score > 1.0:
        return 1.0
    if score < 1.0:
        return 0.5
    return 0.94


def _genotype_edge_visual_style(
    score: float | None,
    edge_type: str,
    default_color: str,
) -> dict[str, Any]:
    if score is None or edge_type not in _ACTIVITY_EDGE_TYPES:
        return {
            "color": default_color,
            "opacity": 0.72,
            "target_arrow_shape": "triangle",
        }

    base_width = 3
    if score == 0.0:
        return {
            "color": "#b9c1cb",
            "width": 1,
            "opacity": 0.16,
            "target_arrow_shape": "none",
        }
    if score > 1.0:
        return {
            "color": default_color,
            "width": max(4, min(8, round(base_width * (1 + (score - 1.0) * 4)))),
            "opacity": 0.96,
            "target_arrow_shape": "triangle",
        }
    return {
        "color": default_color,
        "width": max(1, min(8, round(base_width * score))),
        "opacity": 0.22,
        "target_arrow_shape": "triangle",
    }


def _apply_genotype_profile(
    elements: list[dict[str, Any]],
    profile_key: str,
) -> list[dict[str, Any]]:
    """Apply genotype-aware borders, opacity, and edge emphasis to Cytoscape elements."""
    overrides = _GENOTYPE_PROFILES.get(profile_key or "normal", {})
    if not overrides:
        return elements

    from .cytoscape_adapter import _activity_indicator

    updated: list[dict[str, Any]] = []
    # Build a lookup of source node activity overrides
    node_activity: dict[str, float] = {}
    for element in elements:
        data = element.get("data", {})
        node_id = data.get("id")
        if data.get("kind") == "node" and node_id and node_id in overrides:
            node_activity[node_id] = overrides[node_id]

    for element in elements:
        data = element.get("data", {})
        el = copy.deepcopy(element)
        el_data = el["data"]

        if el_data.get("kind") == "node" and el_data.get("id") in overrides:
            score = overrides[el_data["id"]]
            indicator_color, indicator_width = _activity_indicator(score)
            el_data["activity_border_color"] = indicator_color
            el_data["activity_border_width"] = indicator_width
            el_data["background_opacity"] = _genotype_node_background_opacity(score)

        if el_data.get("kind") == "edge":
            source_id = el_data.get("source")
            edge_type = el_data.get("type", "")
            if source_id in node_activity:
                style = _genotype_edge_visual_style(
                    node_activity[source_id],
                    edge_type,
                    str(el_data.get("color", "#8ea4bb")),
                )
                el_data["color"] = style["color"]
                el_data["opacity"] = style["opacity"]
                el_data["target_arrow_shape"] = style["target_arrow_shape"]
                if "width" in style:
                    el_data["width"] = style["width"]

        updated.append(el)
    return updated


def _require_dash() -> None:
    if _DASH_IMPORT_ERROR is not None:
        raise ImportError(
            "Dash viewer support requires `dash` and `dash-cytoscape`. "
            "Install `ExposoGraph[viewer]` or `pip install dash dash-cytoscape`."
        ) from _DASH_IMPORT_ERROR


def _typed_dash_callback(
    app: Any,
) -> Callable[..., Callable[[_CallbackFunc], _CallbackFunc]]:
    return cast(Callable[..., Callable[[_CallbackFunc], _CallbackFunc]], app.callback)


def _slug(value: str | None) -> str:
    if not value:
        return "unknown"
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower())
    return slug.strip("-") or "unknown"


def _coerce_bundle(
    source: GraphEngine | KnowledgeGraph | CytoscapeBundle | Mapping[str, Any] | str | Path,
    *,
    visibility: GraphVisibility | str = GraphVisibility.ALL,
    layout_mode: ViewerLayoutMode | str = ViewerLayoutMode.COSE,
    positions: Mapping[str, Mapping[str, float]] | None = None,
) -> CytoscapeBundle:
    if isinstance(source, CytoscapeBundle):
        return source
    if isinstance(source, Mapping):
        return CytoscapeBundle.from_dict(source)
    if isinstance(source, (str, Path)):
        return load_cytoscape_bundle(source)
    return build_cytoscape_bundle(
        source,
        visibility=visibility,
        positions=positions,
        layout_mode=layout_mode,
    )


def _split_elements(elements: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for element in elements:
        data = element.get("data", {})
        if data.get("source") and data.get("target"):
            edges.append(copy.deepcopy(element))
        else:
            nodes.append(copy.deepcopy(element))
    return nodes, edges


def _is_edge_element(element: Mapping[str, Any]) -> bool:
    data = dict(element.get("data", {}))
    return bool(data.get("source") and data.get("target"))


def _element_id(element: Mapping[str, Any]) -> str | None:
    data = dict(element.get("data", {}))
    element_id = data.get("id")
    return str(element_id) if element_id is not None else None


def _extract_positions(elements: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, float]]:
    positions: dict[str, dict[str, float]] = {}
    for element in elements:
        if _is_edge_element(element):
            continue
        element_id = _element_id(element)
        position = element.get("position")
        if (
            element_id is None
            or not isinstance(position, Mapping)
            or "x" not in position
            or "y" not in position
        ):
            continue
        positions[element_id] = {
            "x": float(position["x"]),
            "y": float(position["y"]),
        }
    return positions


def _node_classes(element: dict[str, Any]) -> set[str]:
    classes = element.get("classes", "")
    return {part for part in str(classes).split() if part}


def _set_classes(element: dict[str, Any], classes: set[str]) -> dict[str, Any]:
    element["classes"] = " ".join(sorted(classes))
    return element


def _search_blob(data: Mapping[str, Any]) -> str:
    fields = [
        "id",
        "label",
        "type",
        "detail",
        "group",
        "iarc",
        "phase",
        "role",
        "reactivity",
        "source_db",
        "evidence",
        "pmid",
        "tissue",
        "variant",
        "phenotype",
        "origin",
        "match_status",
        "canonical_label",
        "canonical_id",
        "canonical_predicate",
        "custom_type",
        "custom_predicate",
        "label",
    ]
    values = [str(data.get(field, "")) for field in fields if data.get(field)]
    return " ".join(values).lower()


def _toggle_filter_values(
    current_values: Iterable[str] | None,
    clicked_value: str,
    *,
    available_values: Iterable[str],
) -> list[str]:
    ordered = [str(value) for value in available_values]
    current = [str(value) for value in current_values or [] if str(value) in ordered]
    if clicked_value not in ordered:
        return current
    if clicked_value in current:
        return [value for value in current if value != clicked_value]
    next_values = [value for value in ordered if value in current]
    next_values.append(clicked_value)
    return next_values


def _merge_bundle_positions(
    bundle_data: Mapping[str, Any],
    graph_elements: Iterable[Mapping[str, Any]],
) -> dict[str, Any] | None:
    latest_positions = _extract_positions(graph_elements)
    if not latest_positions:
        return None

    existing_positions = {
        str(node_id): {
            "x": float(coords["x"]),
            "y": float(coords["y"]),
        }
        for node_id, coords in dict(bundle_data.get("positions", {})).items()
        if isinstance(coords, Mapping) and "x" in coords and "y" in coords
    }
    changed = False
    merged_positions = dict(existing_positions)
    for node_id, coords in latest_positions.items():
        previous = existing_positions.get(node_id)
        if previous != coords:
            merged_positions[node_id] = coords
            changed = True

    if not changed:
        return None

    merged_bundle = copy.deepcopy(dict(bundle_data))
    merged_bundle["positions"] = merged_positions
    merged_elements = []
    for element in merged_bundle.get("elements", []):
        element_node_id = _element_id(element)
        if _is_edge_element(element) or element_node_id not in merged_positions:
            merged_elements.append(element)
            continue
        updated_element = copy.deepcopy(element)
        updated_element["position"] = merged_positions[element_node_id]
        merged_elements.append(updated_element)
    merged_bundle["elements"] = merged_elements
    return merged_bundle


def _relevant_group_scope(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    carcinogen_group: str | None,
) -> tuple[set[str], set[str]]:
    all_node_ids = {str(node["data"]["id"]) for node in nodes}
    all_edge_ids = {str(edge["data"]["id"]) for edge in edges}
    if not carcinogen_group:
        return all_node_ids, all_edge_ids

    carcinogen_ids = {
        str(node["data"]["id"])
        for node in nodes
        if node["data"].get("type") == "Carcinogen"
        and node["data"].get("group") == carcinogen_group
    }
    if not carcinogen_ids:
        return set(), set()

    relevant_node_ids = set(carcinogen_ids)
    relevant_edge_ids: set[str] = set()
    for edge in edges:
        data = edge["data"]
        source = str(data.get("source", ""))
        target = str(data.get("target", ""))
        if (
            source in carcinogen_ids
            or target in carcinogen_ids
            or data.get("carcinogen") in carcinogen_ids
        ):
            relevant_edge_ids.add(str(data["id"]))
            relevant_node_ids.update({source, target})

    for edge in edges:
        data = edge["data"]
        if data.get("type") not in {"FORMS_ADDUCT", "REPAIRS"}:
            continue
        source = str(data.get("source", ""))
        target = str(data.get("target", ""))
        if source in relevant_node_ids or target in relevant_node_ids:
            relevant_edge_ids.add(str(data["id"]))
            relevant_node_ids.update({source, target})

    return relevant_node_ids, relevant_edge_ids


def _counts_by_type(elements: Iterable[dict[str, Any]], *, edge: bool) -> dict[str, int]:
    counts: dict[str, int] = {}
    for element in elements:
        data = element.get("data", {})
        key = str(data.get("type", "Edge" if edge else "Node"))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def apply_viewer_filters(
    bundle: CytoscapeBundle | Mapping[str, Any],
    *,
    search_query: str = "",
    node_types: Iterable[str] | None = None,
    edge_types: Iterable[str] | None = None,
    carcinogen_group: str | None = None,
    layout_mode: ViewerLayoutMode | str | None = None,
    focus_node_id: str | None = None,
    focus_edge_id: str | None = None,
) -> ViewerState:
    resolved_bundle = bundle if isinstance(bundle, CytoscapeBundle) else CytoscapeBundle.from_dict(bundle)
    nodes, edges = _split_elements(resolved_bundle.elements)

    allowed_node_types = (
        {str(node["data"].get("type", "")) for node in nodes}
        if node_types is None
        else set(node_types)
    )
    allowed_edge_types = (
        {str(edge["data"].get("type", "")) for edge in edges}
        if edge_types is None
        else set(edge_types)
    )
    group_node_ids, group_edge_ids = _relevant_group_scope(nodes, edges, carcinogen_group)

    visible_nodes = [
        node
        for node in nodes
        if str(node["data"].get("type", "")) in allowed_node_types
        and str(node["data"].get("id", "")) in group_node_ids
    ]
    visible_node_ids = {str(node["data"]["id"]) for node in visible_nodes}

    visible_edges = [
        edge
        for edge in edges
        if str(edge["data"].get("type", "")) in allowed_edge_types
        and str(edge["data"].get("id", "")) in group_edge_ids
        and str(edge["data"].get("source", "")) in visible_node_ids
        and str(edge["data"].get("target", "")) in visible_node_ids
    ]

    neighbor_map: dict[str, set[str]] = {node_id: set() for node_id in visible_node_ids}
    edge_by_id: dict[str, dict[str, Any]] = {}
    for edge in visible_edges:
        data = edge["data"]
        edge_id = str(data["id"])
        source = str(data["source"])
        target = str(data["target"])
        edge_by_id[edge_id] = edge
        neighbor_map.setdefault(source, set()).add(target)
        neighbor_map.setdefault(target, set()).add(source)

    active_node_ids: set[str] = set()
    active_edge_ids: set[str] = set()

    query = search_query.strip().lower()
    if query:
        matching_nodes = {
            str(node["data"]["id"])
            for node in visible_nodes
            if query in _search_blob(node["data"])
        }
        matching_edges = {
            str(edge["data"]["id"])
            for edge in visible_edges
            if query in _search_blob(edge["data"])
        }
        active_node_ids.update(matching_nodes)
        for edge_id in matching_edges:
            edge = edge_by_id[edge_id]
            active_edge_ids.add(edge_id)
            active_node_ids.update(
                {
                    str(edge["data"]["source"]),
                    str(edge["data"]["target"]),
                }
            )
        for node_id in list(active_node_ids):
            active_node_ids.update(neighbor_map.get(node_id, set()))

    if focus_edge_id and focus_edge_id in edge_by_id:
        edge = edge_by_id[focus_edge_id]
        active_edge_ids.add(focus_edge_id)
        active_node_ids.update(
            {
                str(edge["data"]["source"]),
                str(edge["data"]["target"]),
            }
        )

    if focus_node_id and focus_node_id in visible_node_ids:
        active_node_ids.add(focus_node_id)
        active_node_ids.update(neighbor_map.get(focus_node_id, set()))

    should_dim = bool(query or focus_node_id or focus_edge_id)
    if should_dim and not active_node_ids and not active_edge_ids:
        active_node_ids = set()
        active_edge_ids = set()

    filtered_elements: list[dict[str, Any]] = []
    for node in visible_nodes:
        node_id = str(node["data"]["id"])
        classes = _node_classes(node)
        classes.discard("dimmed")
        classes.discard("connected")
        classes.discard("selected")
        if should_dim and node_id not in active_node_ids:
            classes.add("dimmed")
        else:
            if focus_node_id and node_id in active_node_ids:
                classes.add("connected")
            if focus_edge_id and node_id in active_node_ids:
                classes.add("connected")
            if focus_node_id and node_id == focus_node_id:
                classes.add("selected")
        filtered_elements.append(_set_classes(node, classes))

    for edge in visible_edges:
        edge_id = str(edge["data"]["id"])
        source = str(edge["data"]["source"])
        target = str(edge["data"]["target"])
        classes = _node_classes(edge)
        classes.discard("dimmed")
        classes.discard("connected")
        classes.discard("selected")
        connected = (
            edge_id in active_edge_ids
            or source in active_node_ids
            or target in active_node_ids
        )
        if should_dim and not connected:
            classes.add("dimmed")
        elif connected and should_dim:
            classes.add("connected")
        if focus_edge_id and edge_id == focus_edge_id:
            classes.add("selected")
        filtered_elements.append(_set_classes(edge, classes))

    return ViewerState(
        elements=filtered_elements,
        layout=viewer_layout(layout_mode or resolved_bundle.metadata.get("layout_mode", "cose")),
        visible_node_count=len(visible_nodes),
        visible_edge_count=len(visible_edges),
        node_type_counts=_counts_by_type(visible_nodes, edge=False),
        edge_type_counts=_counts_by_type(visible_edges, edge=True),
    )


def build_detail_payload(
    bundle: CytoscapeBundle | Mapping[str, Any],
    selection: Mapping[str, Any] | None,
) -> dict[str, Any]:
    resolved_bundle = bundle if isinstance(bundle, CytoscapeBundle) else CytoscapeBundle.from_dict(bundle)
    nodes, edges = _split_elements(resolved_bundle.elements)
    node_by_id = {str(node["data"]["id"]): node["data"] for node in nodes}
    edge_by_id = {str(edge["data"]["id"]): edge["data"] for edge in edges}

    if not selection:
        return {
            "title": "Graph Overview",
            "subtitle": "Advanced Cytoscape viewer",
            "summary": (
                f"{resolved_bundle.metadata.get('node_count', 0)} nodes · "
                f"{resolved_bundle.metadata.get('edge_count', 0)} edges"
            ),
            "fields": [],
            "connections": [],
        }

    kind = str(selection.get("kind", "node"))
    selected_id = str(selection.get("id", ""))
    if kind == "edge" and selected_id in edge_by_id:
        edge = edge_by_id[selected_id]
        return {
            "title": edge.get("label") or edge.get("type") or "Edge",
            "subtitle": f"{edge.get('source')} → {edge.get('target')}",
            "summary": edge.get("type", "Edge"),
            "fields": [
                ("Type", edge.get("type")),
                ("Source", edge.get("source")),
                ("Target", edge.get("target")),
                ("Origin", edge.get("origin")),
                ("Match", edge.get("match_status")),
                ("Canonical", edge.get("canonical_predicate")),
                ("Custom", edge.get("custom_predicate")),
                ("Carcinogen", edge.get("carcinogen")),
                ("Source DB", edge.get("source_db")),
                ("Evidence", edge.get("evidence")),
                ("PMID", edge.get("pmid")),
            ],
            "connections": [],
        }

    node = node_by_id.get(selected_id)
    if node is None:
        return {
            "title": "Selection cleared",
            "subtitle": "",
            "summary": "Choose a node or edge to inspect it.",
            "fields": [],
            "connections": [],
        }

    outgoing: list[str] = []
    incoming: list[str] = []
    for edge in edge_by_id.values():
        if edge.get("source") == selected_id:
            target_label = node_by_id.get(str(edge.get("target")), {}).get("label", edge.get("target"))
            outgoing.append(f"{edge.get('type')} → {target_label}")
        if edge.get("target") == selected_id:
            source_label = node_by_id.get(str(edge.get("source")), {}).get("label", edge.get("source"))
            incoming.append(f"{edge.get('type')} ← {source_label}")

    connections = []
    if outgoing:
        connections.append(("Outgoing", outgoing))
    if incoming:
        connections.append(("Incoming", incoming))
    return {
        "title": node.get("label") or selected_id,
        "subtitle": node.get("type", "Node"),
        "summary": node.get("detail") or "No detail available.",
        "fields": [
            ("ID", node.get("id")),
            ("Origin", node.get("origin")),
            ("Match", node.get("match_status")),
            ("Canonical", node.get("canonical_label") or node.get("canonical_id")),
            ("Group", node.get("group")),
            ("IARC", node.get("iarc")),
            ("Phase", node.get("phase")),
            ("Role", node.get("role")),
            ("Reactivity", node.get("reactivity")),
            ("Tissue", node.get("tissue")),
            ("Variant", node.get("variant")),
            ("Phenotype", node.get("phenotype")),
            ("Source DB", node.get("source_db")),
            ("Evidence", node.get("evidence")),
            ("PMID", node.get("pmid")),
        ],
        "connections": connections,
    }


def create_dash_viewer_app(
    source: GraphEngine | KnowledgeGraph | CytoscapeBundle | Mapping[str, Any] | str | Path,
    *,
    visibility: GraphVisibility | str = GraphVisibility.ALL,
    positions: Mapping[str, Mapping[str, float]] | None = None,
    layout_mode: ViewerLayoutMode | str = ViewerLayoutMode.PRESET,
    title: str | None = None,
) -> Any:
    _require_dash()
    assert (
        cyto is not None
        and DashApp is not None
        and dcc is not None
        and html is not None
        and ALL is not None
    )
    cyto.load_extra_layouts()

    bundle = _coerce_bundle(
        source,
        visibility=visibility,
        layout_mode=layout_mode,
        positions=positions,
    )

    app = DashApp(__name__)
    viewer_title = title or f"{APP_NAME} Advanced Viewer"
    typed_callback = _typed_dash_callback(app)
    node_type_options = list(bundle.metadata.get("node_type_counts", {}).keys())
    edge_type_options = list(bundle.metadata.get("edge_type_counts", {}).keys())
    carcinogen_groups = list(bundle.metadata.get("carcinogen_groups", {}).keys())

    app.layout = html.Div(
        style={
            "minHeight": "100vh",
            "background": (
                "radial-gradient(circle at top, rgba(56, 108, 160, 0.28), transparent 38%), "
                "linear-gradient(180deg, #09111d 0%, #060c15 100%)"
            ),
            "color": "#e6edf7",
            "fontFamily": "Inter, system-ui, sans-serif",
            "padding": "24px",
        },
        children=[
            dcc.Store(id="viewer-bundle-store", data=bundle.to_dict()),
            dcc.Store(id="viewer-selection-store"),
            dcc.Download(id="viewer-layout-download"),
            html.Div(
                style={"maxWidth": "1700px", "margin": "0 auto"},
                children=[
                    html.Div(
                        style={
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "flex-start",
                            "gap": "22px",
                            "marginBottom": "18px",
                            "padding": "18px 20px",
                            "borderRadius": "18px",
                            "border": "1px solid rgba(124, 154, 185, 0.18)",
                            "background": "linear-gradient(180deg, rgba(18, 26, 39, 0.82), rgba(9, 15, 27, 0.92))",
                        },
                        children=[
                            html.Div(
                                children=[
                                    html.H1(
                                        viewer_title,
                                        style={"margin": "0", "fontSize": "2rem", "letterSpacing": "-0.02em"},
                                    ),
                                    html.P(
                                        "Advanced Dash Cytoscape viewer for exploratory and validated ExposoGraph outputs.",
                                        style={"margin": "8px 0 0", "color": "#9fb1c8", "maxWidth": "48rem", "lineHeight": 1.5},
                                    ),
                                ]
                            ),
                            html.Div(
                                id="viewer-stats",
                                style={
                                    "flex": "1 1 auto",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "330px minmax(0, 1fr)",
                            "gap": "18px",
                            "alignItems": "start",
                        },
                        children=[
                            html.Aside(
                                style=_SIDEBAR_STYLE,
                                children=[
                                    html.Div(
                                        style=_CARD_STYLE,
                                        children=[
                                            html.Div("Search", style=_PANEL_TITLE_STYLE),
                                            dcc.Input(
                                                id="viewer-search",
                                                type="text",
                                                placeholder="label, id, detail, PMID, tissue...",
                                                value="",
                                                debounce=True,
                                                style=_INPUT_STYLE,
                                            ),
                                            html.Div(
                                                "Matches expand to immediate neighbors, similar to the manuscript viewer.",
                                                style={"marginTop": "8px", "color": "#8da3bc", "fontSize": "0.8rem", "lineHeight": 1.45},
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        style=_CARD_STYLE,
                                        children=[
                                            html.Div("Filters", style=_PANEL_TITLE_STYLE),
                                            html.Div("Node types", style={"fontSize": "0.82rem", "color": "#9fb1c8", "marginBottom": "6px"}),
                                            dcc.Dropdown(
                                                id="viewer-node-types",
                                                options=[{"label": value, "value": value} for value in node_type_options],
                                                value=node_type_options,
                                                multi=True,
                                                clearable=False,
                                                style={"borderRadius": "10px"},
                                            ),
                                            html.Div("Edge types", style={"fontSize": "0.82rem", "color": "#9fb1c8", "marginTop": "12px", "marginBottom": "6px"}),
                                            dcc.Dropdown(
                                                id="viewer-edge-types",
                                                options=[{"label": value, "value": value} for value in edge_type_options],
                                                value=edge_type_options,
                                                multi=True,
                                                clearable=False,
                                                style={"borderRadius": "10px"},
                                            ),
                                            html.Div("Carcinogen class", style={"fontSize": "0.82rem", "color": "#9fb1c8", "marginTop": "12px", "marginBottom": "6px"}),
                                            dcc.Dropdown(
                                                id="viewer-carcinogen-group",
                                                options=[{"label": "All", "value": ""}] + [
                                                    {"label": value.replace("_", " "), "value": value}
                                                    for value in carcinogen_groups
                                                ],
                                                value="",
                                                clearable=False,
                                                style={"borderRadius": "10px"},
                                            ),
                                            html.Div("Layout", style={"fontSize": "0.82rem", "color": "#9fb1c8", "marginTop": "12px", "marginBottom": "6px"}),
                                            dcc.Dropdown(
                                                id="viewer-layout-mode",
                                                options=[
                                                    {"label": "Force", "value": ViewerLayoutMode.COSE.value},
                                                    {"label": "Hierarchy", "value": ViewerLayoutMode.BREADTHFIRST.value},
                                                    {"label": "Circle", "value": ViewerLayoutMode.CIRCLE.value},
                                                    {"label": "Saved Preset", "value": ViewerLayoutMode.PRESET.value},
                                                ],
                                                value=normalize_viewer_layout_mode(layout_mode).value,
                                                clearable=False,
                                                style={"borderRadius": "10px"},
                                            ),
                                            html.Div("Genotype profile", style={"fontSize": "0.82rem", "color": "#9fb1c8", "marginTop": "12px", "marginBottom": "6px"}),
                                            dcc.Dropdown(
                                                id="viewer-genotype-profile",
                                                options=[
                                                    {"label": "Normal (all activity = 1.0)", "value": "normal"},
                                                    {"label": "CYP1A1*2B / GSTM1-null", "value": "bap_high_risk"},
                                                    {"label": "NAT2 slow acetylator", "value": "nat2_slow"},
                                                    {"label": "CYP2E1 c2/c2 high activity", "value": "cyp2e1_high"},
                                                ],
                                                value="normal",
                                                clearable=False,
                                                style={"borderRadius": "10px"},
                                            ),
                                            html.Div(
                                                _GENOTYPE_MESSAGES["normal"],
                                                id="viewer-genotype-feedback",
                                                style={
                                                    "fontSize": "0.78rem",
                                                    "color": "#9fb1c8",
                                                    "marginTop": "6px",
                                                    "lineHeight": "1.35",
                                                },
                                            ),
                                        ],
                                    ),
                                    html.Div(id="viewer-node-legend", style=_CARD_STYLE),
                                    html.Div(id="viewer-edge-legend", style=_CARD_STYLE),
                                    html.Div(id="viewer-detail", style=_CARD_STYLE),
                                ],
                            ),
                            html.Div(
                                style={
                                    "position": "relative",
                                    "background": "rgba(18, 26, 39, 0.84)",
                                    "border": "1px solid rgba(124, 154, 185, 0.18)",
                                    "borderRadius": "18px",
                                    "padding": "12px",
                                    "boxShadow": "0 18px 44px rgba(0, 0, 0, 0.22)",
                                },
                                children=[
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "justifyContent": "space-between",
                                            "gap": "10px",
                                            "alignItems": "center",
                                            "marginBottom": "8px",
                                            "flexWrap": "wrap",
                                        },
                                        children=[
                                            html.Div(
                                                [
                                                    html.Div("Interactive Graph", style=_PANEL_TITLE_STYLE),
                                                    html.Div(
                                                        "Hover to inspect neighborhoods. Click a node or edge to pin details.",
                                                        style={"color": "#9fb1c8", "fontSize": "0.92rem"},
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                style={"display": "flex", "gap": "8px", "flexWrap": "wrap"},
                                                children=[
                                                    html.Button("Reset Focus", id="viewer-reset-focus", n_clicks=0, style=_ACTION_BUTTON_STYLE),
                                                    html.Button("+", id="viewer-zoom-in", n_clicks=0, style=_ACTION_BUTTON_STYLE),
                                                    html.Button("−", id="viewer-zoom-out", n_clicks=0, style=_ACTION_BUTTON_STYLE),
                                                    html.Button("Reset View", id="viewer-zoom-reset", n_clicks=0, style=_ACTION_BUTTON_STYLE),
                                                    html.Button("PNG", id="viewer-export-png", n_clicks=0, style=_ACTION_BUTTON_STYLE),
                                                    html.Button("SVG", id="viewer-export-svg", n_clicks=0, style=_ACTION_BUTTON_STYLE),
                                                    html.Button("Layout JSON", id="viewer-export-layout", n_clicks=0, style=_ACTION_BUTTON_STYLE),
                                                ],
                                            ),
                                        ],
                                    ),
                                    html.Div(id="viewer-hover-tooltip", style={**_HOVER_TOOLTIP_STYLE, "display": "none"}),
                                    cyto.Cytoscape(
                                        id="advanced-viewer-graph",
                                        elements=bundle.elements,
                                        stylesheet=bundle.stylesheet,
                                        layout=bundle.layout,
                                        style={
                                            "width": "100%",
                                            "height": "78vh",
                                            "background": (
                                                "radial-gradient(circle at center, rgba(90, 160, 222, 0.06), transparent 45%), "
                                                "linear-gradient(180deg, rgba(9, 17, 29, 0.84), rgba(6, 12, 21, 0.96))"
                                            ),
                                            "borderRadius": "12px",
                                            "border": "1px solid rgba(124, 154, 185, 0.12)",
                                        },
                                        userPanningEnabled=True,
                                        userZoomingEnabled=True,
                                        autoRefreshLayout=False,
                                        clearOnUnhover=True,
                                        responsive=True,
                                        minZoom=0.15,
                                        maxZoom=3.5,
                                        wheelSensitivity=0.2,
                                        boxSelectionEnabled=False,
                                    ),
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "justifyContent": "space-between",
                                            "gap": "10px",
                                            "alignItems": "center",
                                            "marginTop": "8px",
                                            "fontSize": "0.82rem",
                                            "color": "#8da3bc",
                                            "flexWrap": "wrap",
                                        },
                                        children=[
                                            html.Div("Search and hover dim non-relevant neighborhoods, mirroring the old manuscript viewer."),
                                            html.Div("Dash Cytoscape viewer"),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

    @typed_callback(
        DashOutput("viewer-node-types", "value"),
        DashOutput("viewer-edge-types", "value"),
        DashInput({"type": "viewer-legend-toggle", "kind": "node", "value": ALL}, "n_clicks"),
        DashInput({"type": "viewer-legend-toggle", "kind": "edge", "value": ALL}, "n_clicks"),
        DashState("viewer-node-types", "value"),
        DashState("viewer-edge-types", "value"),
        DashState("viewer-bundle-store", "data"),
        prevent_initial_call=True,
    )
    def _toggle_legend_filters(
        _node_clicks: list[int],
        _edge_clicks: list[int],
        node_type_values: list[str],
        edge_type_values: list[str],
        bundle_data: dict[str, Any],
    ) -> tuple[Any, Any]:
        triggered = getattr(ctx, "triggered_id", None)
        if not isinstance(triggered, dict):
            return no_update, no_update

        metadata = bundle_data.get("metadata", {})
        if triggered.get("kind") == "node":
            next_node_values = _toggle_filter_values(
                node_type_values,
                str(triggered.get("value", "")),
                available_values=metadata.get("node_type_counts", {}).keys(),
            )
            return next_node_values, no_update
        if triggered.get("kind") == "edge":
            next_edge_values = _toggle_filter_values(
                edge_type_values,
                str(triggered.get("value", "")),
                available_values=metadata.get("edge_type_counts", {}).keys(),
            )
            return no_update, next_edge_values
        return no_update, no_update

    @typed_callback(
        DashOutput("viewer-bundle-store", "data"),
        DashInput("advanced-viewer-graph", "elements"),
        DashState("viewer-bundle-store", "data"),
        prevent_initial_call=True,
    )
    def _persist_positions(
        graph_elements: list[dict[str, Any]],
        bundle_data: dict[str, Any],
    ) -> Any:
        merged = _merge_bundle_positions(bundle_data, graph_elements)
        return merged if merged is not None else no_update

    @typed_callback(
        DashOutput("advanced-viewer-graph", "elements"),
        DashOutput("advanced-viewer-graph", "stylesheet"),
        DashOutput("advanced-viewer-graph", "layout"),
        DashOutput("viewer-stats", "children"),
        DashOutput("viewer-node-legend", "children"),
        DashOutput("viewer-edge-legend", "children"),
        DashOutput("viewer-genotype-feedback", "children"),
        DashInput("viewer-bundle-store", "data"),
        DashInput("viewer-search", "value"),
        DashInput("viewer-node-types", "value"),
        DashInput("viewer-edge-types", "value"),
        DashInput("viewer-carcinogen-group", "value"),
        DashInput("viewer-layout-mode", "value"),
        DashInput("viewer-genotype-profile", "value"),
        DashInput("advanced-viewer-graph", "mouseoverNodeData"),
        DashInput("advanced-viewer-graph", "mouseoverEdgeData"),
        DashInput("viewer-selection-store", "data"),
    )
    def _update_graph(
        bundle_data: dict[str, Any],
        search_value: str,
        node_type_values: list[str],
        edge_type_values: list[str],
        carcinogen_group_value: str,
        layout_value: str,
        genotype_profile: str,
        hovered_node: dict[str, Any] | None,
        hovered_edge: dict[str, Any] | None,
        selection: dict[str, Any] | None,
    ) -> tuple[Any, Any, Any, Any, Any, Any, Any]:
        selected_node_id = None
        selected_edge_id = None
        if selection:
            if selection.get("kind") == "node":
                selected_node_id = str(selection.get("id", ""))
            elif selection.get("kind") == "edge":
                selected_edge_id = str(selection.get("id", ""))

        focus_node_id = selected_node_id or (str(hovered_node.get("id")) if hovered_node else None)
        focus_edge_id = selected_edge_id or (str(hovered_edge.get("id")) if hovered_edge else None)
        state = apply_viewer_filters(
            bundle_data,
            search_query=search_value or "",
            node_types=node_type_values,
            edge_types=edge_type_values,
            carcinogen_group=carcinogen_group_value or None,
            layout_mode=layout_value,
            focus_node_id=focus_node_id,
            focus_edge_id=focus_edge_id,
        )

        stats = _stats_children(
            bundle_data.get("metadata", {}),
            state,
            layout_value=layout_value or bundle_data.get("metadata", {}).get("layout_mode", "cose"),
            search_value=search_value or "",
            carcinogen_group_value=carcinogen_group_value or "",
        )
        node_legend = _legend_children(
            "Node Types",
            state.node_type_counts,
            {
                "Carcinogen": "#e05565",
                "Enzyme": "#4f98a3",
                "Gene": "#3d8b8b",
                "Metabolite": "#e8945a",
                "DNA_Adduct": "#a86fdf",
                "Pathway": "#5591c7",
                "Tissue": "#c2855a",
            },
            kind="node",
            active_values=node_type_values,
        )
        edge_legend = _legend_children(
            "Edge Types",
            state.edge_type_counts,
            {
                "ACTIVATES": "#e05565",
                "DETOXIFIES": "#6daa45",
                "TRANSPORTS": "#5591c7",
                "FORMS_ADDUCT": "#a86fdf",
                "REPAIRS": "#e8af34",
                "PATHWAY": "#707a8a",
                "EXPRESSED_IN": "#c2855a",
                "INDUCES": "#d4a843",
                "INHIBITS": "#8b4a6b",
                "ENCODES": "#3d8b8b",
                "CUSTOM": "#9ea9bd",
            },
            kind="edge",
            active_values=edge_type_values,
        )
        final_elements = _apply_genotype_profile(state.elements, genotype_profile)
        genotype_feedback = _GENOTYPE_MESSAGES.get(genotype_profile or "normal", _GENOTYPE_MESSAGES["normal"])
        return (
            final_elements,
            bundle_data["stylesheet"],
            state.layout,
            stats,
            node_legend,
            edge_legend,
            genotype_feedback,
        )

    @typed_callback(
        DashOutput("viewer-selection-store", "data"),
        DashInput("advanced-viewer-graph", "tapNodeData"),
        DashInput("advanced-viewer-graph", "tapEdgeData"),
        DashInput("viewer-reset-focus", "n_clicks"),
    )
    def _update_selection(
        tap_node: dict[str, Any] | None,
        tap_edge: dict[str, Any] | None,
        _reset_clicks: int,
    ) -> Any:
        prop_id = ""
        if getattr(ctx, "triggered", None):
            prop_id = str(ctx.triggered[0].get("prop_id", ""))
        selection: dict[str, Any] | None
        if prop_id == "viewer-reset-focus.n_clicks":
            selection = None
        elif prop_id == "advanced-viewer-graph.tapNodeData" and tap_node is not None:
            selection = {"kind": "node", "id": tap_node.get("id"), "data": tap_node}
        elif prop_id == "advanced-viewer-graph.tapEdgeData" and tap_edge is not None:
            selection = {"kind": "edge", "id": tap_edge.get("id"), "data": tap_edge}
        else:
            if tap_node is not None:
                selection = {"kind": "node", "id": tap_node.get("id"), "data": tap_node}
            elif tap_edge is not None:
                selection = {"kind": "edge", "id": tap_edge.get("id"), "data": tap_edge}
            else:
                selection = None
        return selection

    @typed_callback(
        DashOutput("viewer-detail", "children"),
        DashInput("viewer-bundle-store", "data"),
        DashInput("viewer-selection-store", "data"),
        DashInput("advanced-viewer-graph", "mouseoverNodeData"),
        DashInput("advanced-viewer-graph", "mouseoverEdgeData"),
    )
    def _render_detail(
        bundle_data: dict[str, Any],
        selection: dict[str, Any] | None,
        hovered_node: dict[str, Any] | None,
        hovered_edge: dict[str, Any] | None,
    ) -> Any:
        context_label = "Overview"
        focus = selection
        if selection:
            context_label = "Pinned Selection"
        elif hovered_node is not None:
            focus = {"kind": "node", "id": hovered_node.get("id"), "data": hovered_node}
            context_label = "Hover Node"
        elif hovered_edge is not None:
            focus = {"kind": "edge", "id": hovered_edge.get("id"), "data": hovered_edge}
            context_label = "Hover Edge"
        detail_payload = build_detail_payload(bundle_data, focus)
        return _detail_children(detail_payload, context_label=context_label)

    @typed_callback(
        DashOutput("viewer-hover-tooltip", "children"),
        DashOutput("viewer-hover-tooltip", "style"),
        DashInput("viewer-bundle-store", "data"),
        DashInput("advanced-viewer-graph", "mouseoverNodeData"),
        DashInput("advanced-viewer-graph", "mouseoverEdgeData"),
    )
    def _render_hover_tooltip(
        bundle_data: dict[str, Any],
        hovered_node: dict[str, Any] | None,
        hovered_edge: dict[str, Any] | None,
    ) -> tuple[Any, Any]:
        if hovered_node is not None:
            payload = build_detail_payload(
                bundle_data,
                {"kind": "node", "id": hovered_node.get("id"), "data": hovered_node},
            )
            return _hover_tooltip_children(payload, "Hover Node"), {**_HOVER_TOOLTIP_STYLE, "display": "block"}
        if hovered_edge is not None:
            payload = build_detail_payload(
                bundle_data,
                {"kind": "edge", "id": hovered_edge.get("id"), "data": hovered_edge},
            )
            return _hover_tooltip_children(payload, "Hover Edge"), {**_HOVER_TOOLTIP_STYLE, "display": "block"}
        return [], {**_HOVER_TOOLTIP_STYLE, "display": "none"}

    @typed_callback(
        DashOutput("advanced-viewer-graph", "zoom"),
        DashOutput("advanced-viewer-graph", "pan"),
        DashInput("viewer-zoom-in", "n_clicks"),
        DashInput("viewer-zoom-out", "n_clicks"),
        DashInput("viewer-zoom-reset", "n_clicks"),
        DashState("advanced-viewer-graph", "zoom"),
        DashState("advanced-viewer-graph", "pan"),
        prevent_initial_call=True,
    )
    def _update_zoom(
        _zoom_in: int,
        _zoom_out: int,
        _zoom_reset: int,
        zoom: float | None,
        pan: dict[str, float] | None,
    ) -> tuple[Any, Any]:
        triggered = getattr(ctx, "triggered_id", None)
        current_zoom = float(zoom or 1.0)
        if triggered == "viewer-zoom-in":
            return min(current_zoom * 1.18, 3.5), pan or {"x": 0, "y": 0}
        if triggered == "viewer-zoom-out":
            return max(current_zoom / 1.18, 0.15), pan or {"x": 0, "y": 0}
        if triggered == "viewer-zoom-reset":
            return 1.0, {"x": 0, "y": 0}
        return no_update, no_update

    @typed_callback(
        DashOutput("advanced-viewer-graph", "generateImage"),
        DashInput("viewer-export-png", "n_clicks"),
        DashInput("viewer-export-svg", "n_clicks"),
        prevent_initial_call=True,
    )
    def _export_image(_png_clicks: int, _svg_clicks: int) -> Any:
        triggered = getattr(ctx, "triggered_id", None)
        if triggered == "viewer-export-png":
            return {"type": "png", "action": "download", "filename": _slug(viewer_title)}
        if triggered == "viewer-export-svg":
            return {"type": "svg", "action": "download", "filename": _slug(viewer_title)}
        return no_update

    @typed_callback(
        DashOutput("viewer-layout-download", "data"),
        DashInput("viewer-export-layout", "n_clicks"),
        DashState("viewer-bundle-store", "data"),
        prevent_initial_call=True,
    )
    def _export_layout(_clicks: int, bundle_data: dict[str, Any]) -> Any:
        positions = bundle_data.get("positions", {})
        return cast(Any, dcc).send_string(
            json.dumps(positions, indent=2),
            f"{_slug(viewer_title)}_layout.json",
        )

    return app


def launch_dash_viewer(
    source: GraphEngine | KnowledgeGraph | CytoscapeBundle | Mapping[str, Any] | str | Path,
    *,
    visibility: GraphVisibility | str = GraphVisibility.ALL,
    positions: Mapping[str, Mapping[str, float]] | None = None,
    layout_mode: ViewerLayoutMode | str = ViewerLayoutMode.PRESET,
    title: str | None = None,
    host: str = "127.0.0.1",
    port: int = 8050,
    debug: bool = False,
    jupyter_mode: str | None = None,
) -> Any:
    app = create_dash_viewer_app(
        source,
        visibility=visibility,
        positions=positions,
        layout_mode=layout_mode,
        title=title,
    )
    run_kwargs: dict[str, Any] = {"host": host, "port": port, "debug": debug}
    if jupyter_mode is not None:
        run_kwargs["jupyter_mode"] = jupyter_mode
    app.run(**run_kwargs)
    return app


def _stats_children(
    metadata: Mapping[str, Any],
    state: ViewerState,
    *,
    layout_value: str,
    search_value: str,
    carcinogen_group_value: str,
) -> Any:
    _require_dash()
    assert html is not None
    total_nodes = int(metadata.get("node_count", state.visible_node_count))
    total_edges = int(metadata.get("edge_count", state.visible_edge_count))
    node_types = len(metadata.get("node_type_counts", {}))
    edge_types = len(metadata.get("edge_type_counts", {}))
    chips = [
        _pill(f"layout: {layout_value}", accent="#76c3ff"),
        _pill(f"view: {metadata.get('visibility', 'all')}", accent="#7de3a0"),
    ]
    if carcinogen_group_value:
        chips.append(_pill(f"group: {carcinogen_group_value.replace('_', ' ')}", accent="#e8af34"))
    if search_value.strip():
        chips.append(_pill(f"search: {search_value.strip()}", accent="#a86fdf"))

    return html.Div(
        [
            html.Div(
                style={"display": "flex", "gap": "10px", "justifyContent": "flex-end", "flexWrap": "wrap"},
                children=[
                    _stat_card("Nodes", str(state.visible_node_count), f"of {total_nodes}"),
                    _stat_card("Edges", str(state.visible_edge_count), f"of {total_edges}"),
                    _stat_card("Node Types", str(node_types), "classes"),
                    _stat_card("Edge Types", str(edge_types), "relations"),
                ],
            ),
            html.Div(
                style={"display": "flex", "gap": "8px", "justifyContent": "flex-end", "flexWrap": "wrap", "marginTop": "10px"},
                children=chips,
            ),
        ]
    )


def _stat_card(label: str, value: str, hint: str) -> Any:
    _require_dash()
    assert html is not None
    return html.Div(
        style={
            "minWidth": "96px",
            "padding": "10px 12px",
            "borderRadius": "12px",
            "border": "1px solid rgba(124, 154, 185, 0.2)",
            "background": "linear-gradient(180deg, rgba(18, 26, 39, 0.88), rgba(10, 16, 28, 0.94))",
            "textAlign": "left",
        },
        children=[
            html.Div(label, style={"fontSize": "0.72rem", "color": "#8da3bc", "textTransform": "uppercase", "letterSpacing": "0.08em"}),
            html.Div(value, style={"fontSize": "1.25rem", "fontWeight": 700, "marginTop": "4px"}),
            html.Div(hint, style={"fontSize": "0.75rem", "color": "#9fb1c8", "marginTop": "2px"}),
        ],
    )


def _pill(label: str, *, accent: str) -> Any:
    _require_dash()
    assert html is not None
    return html.Span(
        [
            html.Span(
                style={
                    "display": "inline-block",
                    "width": "8px",
                    "height": "8px",
                    "borderRadius": "999px",
                    "background": accent,
                    "marginRight": "7px",
                }
            ),
            label,
        ],
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "padding": "6px 10px",
            "borderRadius": "999px",
            "border": "1px solid rgba(124, 154, 185, 0.16)",
            "background": "rgba(13, 21, 34, 0.8)",
            "color": "#b8c7d8",
            "fontSize": "0.8rem",
        },
    )


def _legend_children(
    title: str,
    counts: Mapping[str, int],
    colors: Mapping[str, str],
    *,
    kind: str,
    active_values: Iterable[str] | None,
) -> Any:
    _require_dash()
    assert html is not None
    if not counts:
        return html.Div(
            [html.Div(title, style=_PANEL_TITLE_STYLE), html.Div("No items", style={"color": "#9fb1c8"})]
        )
    active = {str(value) for value in active_values or []}
    return html.Div(
        [
            html.Div(
                [
                    html.Div(title, style=_PANEL_TITLE_STYLE),
                    html.Div(
                        "Click rows to toggle filters",
                        style={"fontSize": "0.76rem", "color": "#7c92ab", "marginBottom": "8px"},
                    ),
                ]
            ),
            html.Div(
                [
                    html.Button(
                        id={"type": "viewer-legend-toggle", "kind": kind, "value": name},
                        n_clicks=0,
                        style={
                            "display": "flex",
                            "width": "100%",
                            "justifyContent": "space-between",
                            "alignItems": "center",
                            "gap": "12px",
                            "padding": "8px 10px",
                            "marginBottom": "6px",
                            "borderRadius": "10px",
                            "border": (
                                f"1px solid {colors.get(name, '#8ea4bb')}"
                                if name in active
                                else "1px solid rgba(124, 154, 185, 0.08)"
                            ),
                            "background": (
                                "rgba(85, 145, 199, 0.14)"
                                if name in active
                                else "rgba(8, 14, 24, 0.42)"
                            ),
                            "color": "#e6edf7" if name in active else "#cbd7e6",
                            "cursor": "pointer",
                            "textAlign": "left",
                        },
                        children=[
                            html.Span(
                                [
                                    html.Span(
                                        style={
                                            "display": "inline-block",
                                            "width": "10px",
                                            "height": "10px",
                                            "borderRadius": "999px",
                                            "background": colors.get(name, "#8ea4bb"),
                                            "marginRight": "8px",
                                        }
                                    ),
                                    html.Span(name, style={"fontWeight": 600 if name in active else 500}),
                                ]
                            ),
                            html.Span(str(count), style={"color": "#9fb1c8", "fontFamily": "monospace"}),
                        ],
                    )
                    for name, count in counts.items()
                ]
            ),
        ]
    )


def _hover_tooltip_children(payload: Mapping[str, Any], context_label: str) -> Any:
    _require_dash()
    assert html is not None
    subtitle = payload.get("subtitle", "")
    summary = payload.get("summary", "")
    field_rows = [
        html.Div(
            [
                html.Span(f"{label}: ", style={"color": "#93a8bf"}),
                html.Span(str(value)),
            ],
            style={"marginTop": "4px", "fontSize": "0.82rem"},
        )
        for label, value in list(payload.get("fields", []))[:4]
        if value not in (None, "")
    ]
    return html.Div(
        [
            html.Div(context_label, style={**_PANEL_TITLE_STYLE, "marginBottom": "6px"}),
            html.Div(payload.get("title", ""), style={"fontWeight": 700, "fontSize": "1rem", "lineHeight": 1.25}),
            html.Div(subtitle, style={"marginTop": "3px", "color": "#7fc4ff", "fontSize": "0.84rem"}),
            html.Div(summary, style={"marginTop": "8px", "color": "#d4dfeb", "fontSize": "0.82rem", "lineHeight": 1.45}),
            html.Div(field_rows, style={"marginTop": "6px"}),
        ]
    )


def _detail_children(payload: Mapping[str, Any], *, context_label: str = "Overview") -> Any:
    _require_dash()
    assert html is not None
    field_rows = [
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "96px minmax(0, 1fr)",
                "gap": "8px",
                "marginBottom": "6px",
                "fontSize": "0.9rem",
            },
            children=[
                html.Div(label, style={"color": "#9fb1c8"}),
                html.Div(str(value)),
            ],
        )
        for label, value in payload.get("fields", [])
        if value not in (None, "")
    ]
    connection_rows = []
    for heading, items in payload.get("connections", []):
        connection_rows.append(
            html.Div(
                [
                    html.Div(heading, style={"fontWeight": 600, "marginTop": "10px", "marginBottom": "6px"}),
                    html.Ul(
                        [html.Li(item, style={"marginBottom": "4px"}) for item in items],
                        style={"paddingLeft": "18px", "margin": "0"},
                    ),
                ]
            )
        )
    return html.Div(
        [
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "gap": "8px", "alignItems": "center", "marginBottom": "10px"},
                children=[
                    html.Div("Inspector", style=_PANEL_TITLE_STYLE),
                    html.Div(
                        context_label,
                        style={
                            "padding": "4px 8px",
                            "borderRadius": "999px",
                            "background": "rgba(75, 119, 161, 0.16)",
                            "border": "1px solid rgba(118, 195, 255, 0.18)",
                            "fontSize": "0.76rem",
                            "color": "#b7dfff",
                        },
                    ),
                ],
            ),
            html.Div(payload.get("title", ""), style={"fontSize": "1.08rem", "fontWeight": 700, "lineHeight": 1.25}),
            html.Div(payload.get("subtitle", ""), style={"color": "#7fc4ff", "marginTop": "4px", "fontSize": "0.88rem"}),
            html.P(payload.get("summary", ""), style={"color": "#c9d5e5", "lineHeight": 1.55, "marginTop": "10px"}),
            html.Div(field_rows),
            html.Div(connection_rows),
        ]
    )
