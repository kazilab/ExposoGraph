"""Streamlit UI for ExposoGraph.

Run with:  streamlit run ExposoGraph/app.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import streamlit as st
from streamlit_agraph import Config, Edge as AEdge, Node as ANode, agraph

# Ensure the package is importable when run via `streamlit run ExposoGraph/app.py`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from .branding import (  # noqa: E402
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    CONTACT_EMAIL,
    COPYRIGHT_HOLDER,
    DEVELOPED_BY,
)
from .config import AppMode, get_app_mode, persistence_enabled  # noqa: E402
from .engine import GraphEngine  # noqa: E402
from .exporter import (  # noqa: E402
    parse_graph_artifact,
    parse_graph_data_text,
    to_interactive_html,
    to_interactive_html_string,
)
from .llm_extractor import EXAMPLE_INPUT, extract_graph  # noqa: E402
from .models import (  # noqa: E402
    CurationConfidence,
    CurationRecord,
    CurationStatus,
    Edge,
    EdgeType,
    KnowledgeGraph,
    Node,
    NodeType,
    ProvenanceRecord,
)  # noqa: E402
from .reference_data import (  # noqa: E402
    ACTIVITY_SCORES,
    build_full_panel,
    build_tier1_panel,
    build_tier2_panel,
    get_activity_score_metadata,
    get_activity_score_references,
    get_activity_scores,
)
from .storage import GraphRepository  # noqa: E402


def _get_secret(key: str, default: str = "") -> str:
    """Read a secret from Streamlit secrets (Cloud) or env vars (local)."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.environ.get(key, default)

# ── Constants ────────────────────────────────────────────────────────────

REFERENCE_VIEWER_DIR = PROJECT_ROOT / "references" / "knowledge-graph"
DEPLOY_VIEWER_DIR = PROJECT_ROOT / "knowledge-graph"
DATA_DIR = PROJECT_ROOT / "data"
REPOSITORY_PATH = DATA_DIR / "ExposoGraph.sqlite3"
PROJECTS_DIR = PROJECT_ROOT / "saved_graphs"
APP_MODE = get_app_mode()
PERSISTENCE_ENABLED = persistence_enabled(APP_MODE)
if PERSISTENCE_ENABLED:
    DATA_DIR.mkdir(exist_ok=True)
    PROJECTS_DIR.mkdir(exist_ok=True)
NODE_COLORS = {
    "Carcinogen": "#e05565",
    "Enzyme": "#4f98a3",
    "Gene": "#3d8b8b",
    "Metabolite": "#e8945a",
    "DNA_Adduct": "#a86fdf",
    "Pathway": "#5591c7",
    "Tissue": "#c2855a",
}
EDGE_COLORS = {
    "ACTIVATES": "#e05565",
    "DETOXIFIES": "#6daa45",
    "TRANSPORTS": "#5591c7",
    "FORMS_ADDUCT": "#a86fdf",
    "REPAIRS": "#e8af34",
    "PATHWAY": "#888888",
    "EXPRESSED_IN": "#c2855a",
    "INDUCES": "#d4a843",
    "INHIBITS": "#8b4a6b",
    "ENCODES": "#3d8b8b",
}
NODE_SEARCH_FIELDS = (
    "id",
    "label",
    "type",
    "detail",
    "group",
    "iarc",
    "phase",
    "role",
    "source_db",
    "evidence",
    "pmid",
    "tissue",
    "variant",
    "phenotype",
    "provenance",
    "curation",
)
EDGE_SEARCH_FIELDS = (
    "source",
    "target",
    "type",
    "label",
    "carcinogen",
    "source_db",
    "evidence",
    "pmid",
    "tissue",
    "provenance",
    "curation",
)

# ── Session state bootstrap ──────────────────────────────────────────────


def _get_engine() -> GraphEngine:
    if "engine" not in st.session_state:
        st.session_state.engine = GraphEngine()
    return st.session_state.engine


@st.cache_resource
def _get_repository() -> GraphRepository | None:
    if not PERSISTENCE_ENABLED:
        return None
    return GraphRepository(REPOSITORY_PATH)


def _get_pending_extraction() -> KnowledgeGraph | None:
    raw = st.session_state.get("pending_extraction")
    if raw is None:
        return None
    return KnowledgeGraph(**raw)


def _load_example_text() -> None:
    st.session_state["extract_text"] = EXAMPLE_INPUT


def _matches_query(data: dict, query: str, fields: tuple[str, ...]) -> bool:
    if not query:
        return True

    def _flatten(value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, dict):
            values: list[str] = []
            for nested in value.values():
                values.extend(_flatten(nested))
            return values
        if isinstance(value, list):
            values: list[str] = []
            for nested in value:
                values.extend(_flatten(nested))
            return values
        return [str(value)]

    values: list[str] = []
    for field in fields:
        values.extend(_flatten(data.get(field)))
    haystack = " ".join(values)
    return query.lower() in haystack.lower()


def _existing_viewer_data_path() -> Path | None:
    for candidate in (
        DEPLOY_VIEWER_DIR / "index.html",
        DEPLOY_VIEWER_DIR / "graph-data.js",
        REFERENCE_VIEWER_DIR / "graph-data.js",
    ):
        if candidate.exists():
            return candidate
    return None


def _viewer_template_dir() -> Path | None:
    for candidate in (REFERENCE_VIEWER_DIR, DEPLOY_VIEWER_DIR):
        if (candidate / "index.html").exists():
            return candidate
    return None


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _load_into_engine(engine: GraphEngine, kg: KnowledgeGraph, *, replace: bool) -> list[str]:
    if replace:
        engine.clear()
        return engine.load(kg)
    return engine.merge(kg)


def _slugify_project_name(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    slug = slug.strip("._")
    return slug or "knowledge_graph"


def _saved_project_paths() -> list[Path]:
    return sorted(
        list(PROJECTS_DIR.glob("*.html")) + list(PROJECTS_DIR.glob("*.json"))
    )


def _revision_label(revision_id: int, revisions_by_id: dict[int, object]) -> str:
    revision = revisions_by_id[revision_id]
    note = f" - {revision.note}" if getattr(revision, "note", None) else ""
    return (
        f"r{revision.revision_number} | {revision.node_count}n/{revision.edge_count}e | "
        f"{revision.created_at[:19]}{note}"
    )


def _parse_uploaded_graph(name: str, raw_text: str) -> KnowledgeGraph:
    suffix = Path(name).suffix.lower()
    if suffix == ".json":
        return KnowledgeGraph(**json.loads(raw_text))
    if suffix in {".html", ".js"}:
        return parse_graph_data_text(raw_text)
    raise ValueError(f"Unsupported upload type: {suffix}")


def _build_provenance_record(
    *,
    source_db: str,
    record_id: str,
    evidence: str,
    pmid: str,
    tissue: str,
    citation: str,
    url: str,
) -> list[ProvenanceRecord]:
    record = ProvenanceRecord(
        source_db=source_db or None,
        record_id=record_id or None,
        evidence=evidence or None,
        pmid=pmid or None,
        tissue=tissue or None,
        citation=citation or None,
        url=url or None,
    )
    if not record.model_dump(exclude_none=True):
        return []
    return [record]


def _build_curation_record(
    *,
    status: str,
    confidence: str,
    curator: str,
    reviewed_by: str,
    reviewed_at: str,
    notes: str,
) -> CurationRecord | None:
    if not any([status, confidence, curator, reviewed_by, reviewed_at, notes]):
        return None
    return CurationRecord(
        status=CurationStatus(status) if status else CurationStatus.DRAFT,
        confidence=CurationConfidence(confidence) if confidence else None,
        curator=curator or None,
        reviewed_by=reviewed_by or None,
        reviewed_at=reviewed_at or None,
        notes=notes or None,
    )


def _annotation_lines(data: dict) -> list[str]:
    lines: list[str] = []
    for label, key in [
        ("Source", "source_db"),
        ("Evidence", "evidence"),
        ("PMID", "pmid"),
        ("Tissue", "tissue"),
        ("Variant", "variant"),
        ("Phenotype", "phenotype"),
    ]:
        value = data.get(key)
        if value:
            lines.append(f"{label}: {value}")
    provenance = data.get("provenance") or []
    if provenance:
        record_ids = []
        for record in provenance:
            record_id = record.get("record_id")
            if record_id and record_id not in record_ids:
                record_ids.append(record_id)
        if record_ids:
            lines.append(f"Record IDs: {'; '.join(record_ids)}")
        lines.append(f"Provenance records: {len(provenance)}")
    curation = data.get("curation") or {}
    for label, key in [
        ("Status", "status"),
        ("Confidence", "confidence"),
        ("Curator", "curator"),
        ("Reviewed by", "reviewed_by"),
    ]:
        value = curation.get(key)
        if value:
            lines.append(f"{label}: {value}")
    if data.get("activity_score") is not None:
        lines.append(f"Activity score: {data['activity_score']}")
    return lines


def _node_tooltip(data: dict) -> str:
    parts = [data.get("detail", "")]
    parts.extend(_annotation_lines(data))
    return "\n".join(part for part in parts if part)


def _edge_tooltip(data: dict) -> str:
    parts = [data.get("label", data.get("type", ""))]
    parts.extend(_annotation_lines(data))
    return "\n".join(part for part in parts if part)


# ── Page config ──────────────────────────────────────────────────────────

st.set_page_config(
    page_title=f"{APP_NAME} v{APP_VERSION}",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { min-width: 340px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ──────────────────────────────────────────────────────────────

engine = _get_engine()
repository = _get_repository()
if "extract_text" not in st.session_state:
    st.session_state.extract_text = ""
if "project_name" not in st.session_state:
    st.session_state.project_name = "knowledge_graph"
if "revision_note" not in st.session_state:
    st.session_state.revision_note = ""

with st.sidebar:
    st.markdown(f"### {APP_NAME}")
    st.caption(APP_TAGLINE)
    st.caption(f"Version {APP_VERSION} · {DEVELOPED_BY}")
    st.caption(f"Contact: {CONTACT_EMAIL} · Copyright {COPYRIGHT_HOLDER}")
    st.caption(
        f"**{engine.node_count}** nodes · **{engine.edge_count}** edges"
    )
    if APP_MODE == AppMode.STATELESS:
        st.info(
            "Mode: stateless. User graphs are not saved on the server. "
            "Download the interactive HTML file to keep your work."
        )
    else:
        st.caption(f"Mode: local persistence (`{_relative_path(REPOSITORY_PATH)}`)")

    st.divider()

    # -- Import existing graph-data.js --
    st.markdown("##### Import Existing Data")
    replace_import = st.checkbox(
        "Replace current graph on import",
        value=engine.node_count == 0,
        help="When enabled, imported data clears the current graph first.",
    )
    viewer_data_path = _existing_viewer_data_path()
    if viewer_data_path is not None:
        st.caption(f"Viewer data source: `{_relative_path(viewer_data_path)}`")
    else:
        st.caption("Viewer data source: none found yet")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Load current viewer data", use_container_width=True):
            if viewer_data_path is not None:
                kg = parse_graph_artifact(viewer_data_path)
                warnings = _load_into_engine(engine, kg, replace=replace_import)
                message = f"Loaded {len(kg.nodes)} nodes, {len(kg.edges)} edges"
                if warnings:
                    message += f" with {len(warnings)} warning(s)"
                st.success(message)
                st.rerun()
            else:
                st.error("graph-data.js not found")
    with col_b:
        uploaded = st.file_uploader(
            "Upload graph",
            type=["json", "html", "js"],
            label_visibility="collapsed",
        )
        if uploaded is not None:
            try:
                kg = _parse_uploaded_graph(uploaded.name, uploaded.read().decode("utf-8"))
                warnings = _load_into_engine(engine, kg, replace=replace_import)
                message = f"Loaded {len(kg.nodes)} nodes, {len(kg.edges)} edges"
                if warnings:
                    message += f" with {len(warnings)} warning(s)"
                st.success(message)
                st.rerun()
            except Exception as exc:
                st.error(f"Upload failed: {exc}")

    st.divider()

    st.text_input(
        "Project name",
        key="project_name",
        help="Used as the human-readable project name and the base name for exports.",
    )
    if PERSISTENCE_ENABLED and repository is not None:
        st.text_input(
            "Revision note",
            key="revision_note",
            help="Optional note describing what changed in this revision.",
        )

        st.divider()

        # -- Database-backed revision history --
        st.markdown("##### Revision History")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("Save revision", use_container_width=True):
                if engine.node_count == 0:
                    st.error("Graph is empty")
                else:
                    try:
                        saved = repository.save_engine(
                            graph_key=_slugify_project_name(st.session_state.project_name),
                            graph_name=st.session_state.project_name.strip() or "knowledge_graph",
                            engine=engine,
                            template_path=_viewer_template_dir(),
                            note=st.session_state.revision_note.strip() or None,
                        )
                        st.success(f"Saved revision r{saved.revision_number} to `{REPOSITORY_PATH.name}`")
                        st.session_state.revision_note = ""
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Revision save failed: {exc}")
        with col_r2:
            db_graphs = repository.list_graphs()
            selected_db_graph = st.selectbox(
                "Stored project",
                options=[""] + [graph.graph_key for graph in db_graphs],
                format_func=lambda key: next(
                    (
                        f"{graph.graph_name} (r{graph.revision_number})"
                        for graph in db_graphs
                        if graph.graph_key == key
                    ),
                    "Select project",
                ),
                label_visibility="collapsed",
            )
            if st.button("Load latest", use_container_width=True):
                if not selected_db_graph:
                    st.error("Select a stored project first")
                else:
                    revision = repository.get_latest_revision(selected_db_graph)
                    if revision is None:
                        st.error("No revisions found for that project")
                    else:
                        warnings = _load_into_engine(
                            engine,
                            revision.to_knowledge_graph(),
                            replace=replace_import,
                        )
                        message = f"Loaded {revision.graph_name} r{revision.revision_number}"
                        if warnings:
                            message += f" with {len(warnings)} warning(s)"
                        st.success(message)
                        st.rerun()

        if db_graphs:
            selected_history_graph = st.selectbox(
                "Revision history",
                options=[""] + [graph.graph_key for graph in db_graphs],
                format_func=lambda key: next(
                    (graph.graph_name for graph in db_graphs if graph.graph_key == key),
                    "Select project",
                ),
            )
            if selected_history_graph:
                revisions = repository.list_revisions(selected_history_graph)
                revisions_by_id = {revision.revision_id: revision for revision in revisions}
                selected_revision_id = st.selectbox(
                    "Revision",
                    options=[revision.revision_id for revision in revisions],
                    format_func=lambda revision_id: _revision_label(revision_id, revisions_by_id),
                )
                selected_revision = repository.get_revision(selected_revision_id)
                if selected_revision is not None:
                    st.caption(f"Database: `{_relative_path(REPOSITORY_PATH)}`")
                    col_db1, col_db2 = st.columns(2)
                    with col_db1:
                        if st.button("Load selected revision", use_container_width=True):
                            warnings = _load_into_engine(
                                engine,
                                selected_revision.to_knowledge_graph(),
                                replace=replace_import,
                            )
                            message = (
                                f"Loaded {selected_revision.graph_name} "
                                f"r{selected_revision.revision_number}"
                            )
                            if warnings:
                                message += f" with {len(warnings)} warning(s)"
                            st.success(message)
                            st.rerun()
                    with col_db2:
                        st.download_button(
                            "Download revision HTML",
                            data=selected_revision.html,
                            file_name=(
                                f"{selected_revision.graph_key}_r"
                                f"{selected_revision.revision_number}.html"
                            ),
                            mime="text/html",
                            use_container_width=True,
                        )

        st.divider()

        # -- File-based HTML snapshots --
        st.markdown("##### HTML Files")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("Save HTML snapshot", use_container_width=True):
                if engine.node_count == 0:
                    st.error("Graph is empty")
                else:
                    project_path = PROJECTS_DIR / f"{_slugify_project_name(st.session_state.project_name)}.html"
                    to_interactive_html(engine, project_path, template_path=_viewer_template_dir())
                    st.success(f"Saved `{project_path.name}`")
        with col_s2:
            saved_projects = _saved_project_paths()
            selected_project = st.selectbox(
                "Saved",
                options=[""] + [path.name for path in saved_projects],
                label_visibility="collapsed",
            )
            if st.button("Load HTML snapshot", use_container_width=True):
                if not selected_project:
                    st.error("Select a saved project first")
                else:
                    project_path = PROJECTS_DIR / selected_project
                    kg = parse_graph_artifact(project_path)
                    warnings = _load_into_engine(engine, kg, replace=replace_import)
                    message = f"Loaded `{project_path.name}`"
                    if warnings:
                        message += f" with {len(warnings)} warning(s)"
                    st.success(message)
                    st.rerun()

        st.divider()

    # -- Load reference gene panels --
    st.markdown("##### Reference Gene Panels")
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        if st.button("Tier 1 (13)", use_container_width=True, help="Core CYP/GST/NAT/UGT enzymes"):
            kg = build_tier1_panel()
            engine.merge(kg)
            st.success(f"Loaded {len(kg.nodes)} Tier 1 genes")
            st.rerun()
    with col_p2:
        if st.button("Tier 2 (15)", use_container_width=True, help="Extended Phase II/III and DNA-repair panel"):
            kg = build_tier2_panel()
            engine.merge(kg)
            st.success(f"Loaded {len(kg.nodes)} Tier 2 genes")
            st.rerun()
    with col_p3:
        if st.button("All (28)", use_container_width=True, help="Full Tier 1 + Tier 2 panel"):
            kg = build_full_panel()
            engine.merge(kg)
            st.success(f"Loaded {len(kg.nodes)} genes")
            st.rerun()

    st.divider()

    # -- Activity scores --
    st.markdown("##### Activity Score Lookup")
    activity_gene = st.selectbox("Gene", [""] + sorted(ACTIVITY_SCORES.keys()))
    if activity_gene:
        st.dataframe(get_activity_scores(activity_gene), use_container_width=True, hide_index=True)
        activity_meta = get_activity_score_metadata(activity_gene) or {}
        if activity_meta:
            st.caption(
                f"Evidence basis: {activity_meta.get('evidence_basis', 'Unspecified')}. "
                f"{activity_meta.get('note', '')}"
            )
        activity_refs = get_activity_score_references(activity_gene) or []
        if activity_refs:
            with st.expander("Activity score references", expanded=False):
                ref_rows = [
                    {
                        "source_db": ref.get("source_db", ""),
                        "record_id": ref.get("record_id", ""),
                        "pmid": ref.get("pmid", ""),
                        "citation": ref.get("citation", ""),
                        "url": ref.get("url", ""),
                    }
                    for ref in activity_refs
                ]
                st.dataframe(ref_rows, use_container_width=True, hide_index=True)

    st.divider()

    # -- Export --
    st.markdown("##### Export")
    html_export = ""
    html_export_error = ""
    if engine.node_count > 0:
        try:
            html_export = to_interactive_html_string(engine, template_path=_viewer_template_dir())
        except Exception as exc:
            html_export_error = str(exc)
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        if PERSISTENCE_ENABLED:
            if st.button("Export HTML locally", use_container_width=True):
                if engine.node_count == 0:
                    st.error("Graph is empty")
                elif html_export_error:
                    st.error(f"Export failed: {html_export_error}")
                else:
                    out = to_interactive_html(
                        engine,
                        DEPLOY_VIEWER_DIR / "index.html",
                        template_path=_viewer_template_dir(),
                    )
                    st.success(f"Written to `{_relative_path(out)}`")
        else:
            st.caption("Server-side file export disabled in stateless mode.")
    with col_e2:
        if engine.node_count > 0 and not html_export_error:
            st.download_button(
                "Download HTML",
                data=html_export,
                file_name=f"{_slugify_project_name(st.session_state.project_name)}.html",
                mime="text/html",
                use_container_width=True,
            )
        elif html_export_error:
            st.caption(f"HTML export unavailable: {html_export_error}")
    if _viewer_template_dir() is not None:
        if PERSISTENCE_ENABLED:
            st.caption(
                "Local export and download both produce a standalone interactive HTML "
                f"file using the `{_relative_path(_viewer_template_dir())}` viewer template."
            )
        else:
            st.caption(
                "Downloads produce a standalone interactive HTML file using the "
                f"`{_relative_path(_viewer_template_dir())}` viewer template."
            )

    st.divider()

    # -- Validation --
    errors = engine.validate()
    if errors:
        st.warning(f"{len(errors)} validation issue(s)")
        for e in errors:
            st.caption(f"⚠ {e}")
    elif engine.node_count > 0:
        st.success("Graph valid")

    st.divider()
    if st.button("Clear graph", type="secondary", use_container_width=True):
        engine.clear()
        st.rerun()


# ── Main area tabs ───────────────────────────────────────────────────────

st.markdown(f"## {APP_NAME}")
st.caption(f"{APP_TAGLINE} · Version {APP_VERSION}")
st.caption(f"{DEVELOPED_BY} · {CONTACT_EMAIL} · Copyright {COPYRIGHT_HOLDER}")

tab_extract, tab_manual, tab_preview, tab_data = st.tabs(
    ["LLM Extract", "Manual Entry", "Graph Preview", "Raw Data"]
)

# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  TAB 1: LLM-Assisted Extraction                                     ║
# ╚═══════════════════════════════════════════════════════════════════════╝

with tab_extract:
    st.markdown("#### Extract Knowledge Graph from Text")
    st.caption(
        "Describe a carcinogen metabolism pathway in plain English. "
        "The LLM will extract nodes and edges automatically."
    )

    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Leave blank to use the OPENAI_API_KEY env var.",
        )
    with col_cfg2:
        model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"], index=0)

    user_text = st.text_area(
        "Pathway description",
        key="extract_text",
        height=220,
        placeholder=EXAMPLE_INPUT,
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        run_extract = st.button("Extract", type="primary", use_container_width=True)
    with col2:
        st.button(
            "Load example text",
            use_container_width=True,
            on_click=_load_example_text,
        )

    if run_extract and user_text.strip():
        resolved_key = api_key or _get_secret("OPENAI_API_KEY")
        if not resolved_key:
            st.error("Provide an OpenAI API key or set OPENAI_API_KEY before extracting.")
            st.stop()
        with st.spinner("Calling LLM…"):
            try:
                kg = extract_graph(
                    user_text,
                    model=model,
                    api_key=resolved_key or None,
                )
                st.success(
                    f"Extracted **{len(kg.nodes)}** nodes and "
                    f"**{len(kg.edges)}** edges"
                )
                st.session_state.pending_extraction = kg.model_dump(mode="json")
                st.rerun()

            except Exception as exc:
                st.error(f"Extraction failed: {exc}")

    pending_kg = _get_pending_extraction()
    if pending_kg is not None:
        with st.expander("Preview extracted data", expanded=True):
            st.json(pending_kg.model_dump(mode="json"))

        col_merge, col_discard = st.columns(2)
        with col_merge:
            if st.button("Merge into graph", type="primary", use_container_width=True):
                try:
                    engine.merge(pending_kg)
                    st.session_state.pop("pending_extraction", None)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Merge failed: {exc}")
        with col_discard:
            if st.button("Discard extraction", use_container_width=True):
                st.session_state.pop("pending_extraction", None)
                st.rerun()

# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  TAB 2: Manual Entry                                                 ║
# ╚═══════════════════════════════════════════════════════════════════════╝

with tab_manual:
    st.markdown("#### Add Nodes & Edges Manually")

    node_tab, edge_tab = st.tabs(["Add Node", "Add Edge"])

    with node_tab:
        with st.form("add_node", clear_on_submit=True):
            st.markdown("**New Node**")
            c1, c2 = st.columns(2)
            with c1:
                n_label = st.text_input("Label *", placeholder="e.g. CYP1A1")
                n_type = st.selectbox("Type *", [t.value for t in NodeType])
            with c2:
                n_id = st.text_input("ID (auto from label)", placeholder="CYP1A1")
                n_detail = st.text_input("Detail", placeholder="Short description")

            c3, c4, c5 = st.columns(3)
            with c3:
                n_group = st.text_input("Group / Class", placeholder="PAH, DNA Repair (BER), …")
                n_iarc = st.selectbox("IARC", [None, "Group 1", "Group 2A", "Group 2B", "Group 3"])
            with c4:
                n_phase = st.selectbox("Phase", [None, "I", "II", "III"])
                n_role = st.selectbox(
                    "Role",
                    [None, "Activation", "Detoxification", "Mixed", "Transport", "Repair"],
                )
            with c5:
                n_reactivity = st.selectbox("Reactivity", [None, "High", "Intermediate", "Low"])

            with st.expander("Provenance & Curation", expanded=False):
                a1, a2 = st.columns(2)
                with a1:
                    n_source_db = st.text_input("Source DB", placeholder="NCBI Gene; GTEx; ClinPGx")
                    n_record_id = st.text_input("Record ID / Accession", placeholder="e.g. 1543 or CYP1A1")
                    n_pmid = st.text_input("PMID", placeholder="e.g. 29134625")
                    n_citation = st.text_input("Citation", placeholder="Short citation or paper title")
                    n_variant = st.text_input("Variant", placeholder="e.g. CYP1A1*2C")
                with a2:
                    n_tissue = st.text_input("Tissue", placeholder="e.g. lung, liver, bladder")
                    n_url = st.text_input("URL", placeholder="https://...")
                    n_phenotype = st.text_input("Phenotype", placeholder="e.g. poor metabolizer")
                    n_activity_score = st.text_input("Activity score", placeholder="e.g. 1.5")
                n_evidence = st.text_area("Evidence", placeholder="Short provenance or evidence note", height=80)

                curation_col1, curation_col2 = st.columns(2)
                with curation_col1:
                    n_status = st.selectbox(
                        "Status",
                        [status.value for status in CurationStatus],
                        index=0,
                    )
                    n_confidence = st.selectbox(
                        "Confidence",
                        [""] + [confidence.value for confidence in CurationConfidence],
                    )
                    n_curator = st.text_input("Curator", placeholder="Name or initials")
                with curation_col2:
                    n_reviewed_by = st.text_input("Reviewed by", placeholder="Reviewer name")
                    n_reviewed_at = st.text_input("Reviewed at", placeholder="YYYY-MM-DD")
                    n_curation_notes = st.text_area(
                        "Curation notes",
                        placeholder="Why this record is draft/reviewed/approved",
                        height=80,
                    )

            if st.form_submit_button("Add Node", type="primary"):
                if not n_label:
                    st.error("Label is required")
                elif n_activity_score:
                    try:
                        activity_score = float(n_activity_score)
                    except ValueError:
                        st.error("Activity score must be numeric")
                        activity_score = None
                else:
                    activity_score = None
                if n_label and (not n_activity_score or activity_score is not None):
                    provenance = _build_provenance_record(
                        source_db=n_source_db,
                        record_id=n_record_id,
                        evidence=n_evidence,
                        pmid=n_pmid,
                        tissue=n_tissue,
                        citation=n_citation,
                        url=n_url,
                    )
                    curation = _build_curation_record(
                        status=n_status,
                        confidence=n_confidence,
                        curator=n_curator,
                        reviewed_by=n_reviewed_by,
                        reviewed_at=n_reviewed_at,
                        notes=n_curation_notes,
                    )
                    node = Node(
                        id=n_id or n_label.replace(" ", "_"),
                        label=n_label,
                        type=NodeType(n_type),
                        detail=n_detail,
                        group=n_group or None,
                        iarc=n_iarc,
                        phase=n_phase,
                        role=n_role,
                        reactivity=n_reactivity,
                        source_db=n_source_db or None,
                        evidence=n_evidence or None,
                        pmid=n_pmid or None,
                        tissue=n_tissue or None,
                        variant=n_variant or None,
                        phenotype=n_phenotype or None,
                        activity_score=activity_score,
                        provenance=provenance,
                        curation=curation,
                    )
                    engine.add_node(node)
                    st.success(f"Added node **{node.label}** ({node.type.value})")
                    st.rerun()

    with edge_tab:
        node_ids = sorted(engine.G.nodes) if engine.node_count > 0 else []

        with st.form("add_edge", clear_on_submit=True):
            st.markdown("**New Edge**")
            if not node_ids:
                st.info("Add at least two nodes first.")

            c1, c2, c3 = st.columns(3)
            with c1:
                e_source = st.selectbox("Source *", node_ids or [""])
            with c2:
                e_target = st.selectbox("Target *", node_ids or [""])
            with c3:
                e_type = st.selectbox("Type *", [t.value for t in EdgeType])

            c4, c5 = st.columns(2)
            with c4:
                e_label = st.text_input("Label", placeholder="e.g. epoxidation")
            with c5:
                carcinogen_ids = [
                    n for n in node_ids
                    if engine.get_node(n) and engine.get_node(n).get("type") == "Carcinogen"
                ]
                e_carcin = st.selectbox("Carcinogen (context)", [""] + carcinogen_ids)

            with st.expander("Provenance & Curation", expanded=False):
                e_source_db = st.text_input("Source DB", placeholder="NCBI Gene; CTD; ClinPGx")
                e_record_id = st.text_input("Record ID / Accession", placeholder="e.g. rs2228001 or pathway accession")
                e_pmid = st.text_input("PMID", placeholder="e.g. 25786862")
                e_tissue = st.text_input("Tissue", placeholder="e.g. liver, lung")
                e_citation = st.text_input("Citation", placeholder="Short citation or paper title")
                e_url = st.text_input("URL", placeholder="https://...")
                e_evidence = st.text_area("Evidence", placeholder="Short provenance or evidence note", height=80)
                curation_col1, curation_col2 = st.columns(2)
                with curation_col1:
                    e_status = st.selectbox(
                        "Status",
                        [status.value for status in CurationStatus],
                        index=0,
                    )
                    e_confidence = st.selectbox(
                        "Confidence",
                        [""] + [confidence.value for confidence in CurationConfidence],
                    )
                    e_curator = st.text_input("Curator", placeholder="Name or initials")
                with curation_col2:
                    e_reviewed_by = st.text_input("Reviewed by", placeholder="Reviewer name")
                    e_reviewed_at = st.text_input("Reviewed at", placeholder="YYYY-MM-DD")
                    e_curation_notes = st.text_area(
                        "Curation notes",
                        placeholder="Why this edge is draft/reviewed/approved",
                        height=80,
                    )

            if st.form_submit_button("Add Edge", type="primary"):
                if not e_source or not e_target:
                    st.error("Source and target are required")
                else:
                    provenance = _build_provenance_record(
                        source_db=e_source_db,
                        record_id=e_record_id,
                        evidence=e_evidence,
                        pmid=e_pmid,
                        tissue=e_tissue,
                        citation=e_citation,
                        url=e_url,
                    )
                    curation = _build_curation_record(
                        status=e_status,
                        confidence=e_confidence,
                        curator=e_curator,
                        reviewed_by=e_reviewed_by,
                        reviewed_at=e_reviewed_at,
                        notes=e_curation_notes,
                    )
                    edge = Edge(
                        source=e_source,
                        target=e_target,
                        type=EdgeType(e_type),
                        label=e_label or None,
                        carcinogen=e_carcin or None,
                        source_db=e_source_db or None,
                        evidence=e_evidence or None,
                        pmid=e_pmid or None,
                        tissue=e_tissue or None,
                        provenance=provenance,
                        curation=curation,
                    )
                    try:
                        engine.add_edge(edge)
                        st.success(f"Added edge **{e_source}** → **{e_target}** ({e_type})")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  TAB 3: Interactive Graph Preview                                    ║
# ╚═══════════════════════════════════════════════════════════════════════╝

with tab_preview:
    st.markdown("#### Graph Preview")

    if engine.node_count == 0:
        st.info("No data yet — use LLM Extract or Manual Entry to add nodes.")
    else:
        all_nodes = list(engine.G.nodes(data=True))
        all_edges = list(engine.G.edges(keys=True, data=True))
        node_type_options = sorted({data.get("type", "?") for _, data in all_nodes})
        edge_type_options = sorted({data.get("type", "?") for _, _, _, data in all_edges})

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            preview_query = st.text_input(
                "Search graph",
                key="preview_query",
                placeholder="label, id, detail, PMID, tissue, evidence...",
            ).strip()
        with col_f2:
            preview_node_types = st.multiselect(
                "Node types",
                node_type_options,
                default=node_type_options,
                key="preview_node_types",
            )
        with col_f3:
            preview_edge_types = st.multiselect(
                "Edge types",
                edge_type_options,
                default=edge_type_options,
                key="preview_edge_types",
            )

        allowed_node_ids = {
            node_id
            for node_id, data in all_nodes
            if data.get("type", "?") in preview_node_types
        }
        edge_match_node_ids: set[str] = set()
        if preview_query:
            for u, v, _, data in all_edges:
                if (
                    data.get("type", "?") in preview_edge_types
                    and u in allowed_node_ids
                    and v in allowed_node_ids
                    and _matches_query(data, preview_query, EDGE_SEARCH_FIELDS)
                ):
                    edge_match_node_ids.update((u, v))

        if preview_query:
            visible_node_ids = {
                node_id
                for node_id, data in all_nodes
                if node_id in allowed_node_ids
                and (
                    _matches_query(data, preview_query, NODE_SEARCH_FIELDS)
                    or node_id in edge_match_node_ids
                )
            }
        else:
            visible_node_ids = allowed_node_ids

        filtered_nodes = [
            (node_id, data)
            for node_id, data in all_nodes
            if node_id in visible_node_ids
        ]
        filtered_edges = [
            (u, v, edge_key, data)
            for u, v, edge_key, data in all_edges
            if data.get("type", "?") in preview_edge_types
            and u in visible_node_ids
            and v in visible_node_ids
        ]

        st.caption(
            f"Showing {len(filtered_nodes)} of {engine.node_count} nodes and "
            f"{len(filtered_edges)} of {engine.edge_count} edges"
        )

        if not filtered_nodes:
            st.info("No nodes match the current preview filters.")
        else:
            agraph_nodes = []
            agraph_edges = []

            for _, data in filtered_nodes:
                ntype = data.get("type", "Enzyme")
                color = NODE_COLORS.get(ntype, "#888")
                agraph_nodes.append(
                    ANode(
                        id=data["id"],
                        label=data.get("label", data["id"]),
                        color=color,
                        size=25 if ntype == "Carcinogen" else 18,
                        title=_node_tooltip(data),
                    )
                )

            for u, v, _, data in filtered_edges:
                etype = data.get("type", "ACTIVATES")
                color = EDGE_COLORS.get(etype, "#555")
                agraph_edges.append(
                    AEdge(
                        source=u,
                        target=v,
                        label=data.get("label", etype),
                        color=color,
                        title=_edge_tooltip(data),
                        width=2,
                    )
                )

            config = Config(
                width=1200,
                height=700,
                directed=True,
                physics=True,
                hierarchical=False,
                nodeHighlightBehavior=True,
                highlightColor="#5cc6d0",
                collapsible=False,
                node={"labelProperty": "label"},
                link={"labelProperty": "label", "renderLabel": False},
            )

            agraph(nodes=agraph_nodes, edges=agraph_edges, config=config)

            st.caption(
                f"{len(filtered_nodes)} nodes · {len(filtered_edges)} edges · "
                "Drag to rearrange, scroll to zoom"
            )

# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  TAB 4: Raw Data View                                               ║
# ╚═══════════════════════════════════════════════════════════════════════╝

with tab_data:
    st.markdown("#### Current Graph Data")

    if engine.node_count == 0:
        st.info("Graph is empty.")
    else:
        all_nodes = list(engine.G.nodes(data=True))
        all_edges = list(engine.G.edges(keys=True, data=True))
        node_type_options = sorted({data.get("type", "?") for _, data in all_nodes})
        edge_type_options = sorted({data.get("type", "?") for _, _, _, data in all_edges})

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            data_query = st.text_input(
                "Search raw data",
                key="data_query",
                placeholder="Search nodes, edges, evidence, PMIDs...",
            ).strip()
        with col_f2:
            data_node_types = st.multiselect(
                "Node types",
                node_type_options,
                default=node_type_options,
                key="data_node_types",
            )
        with col_f3:
            data_edge_types = st.multiselect(
                "Edge types",
                edge_type_options,
                default=edge_type_options,
                key="data_edge_types",
            )

        filtered_nodes = [
            (node_id, data)
            for node_id, data in all_nodes
            if data.get("type", "?") in data_node_types
            and _matches_query(data, data_query, NODE_SEARCH_FIELDS)
        ]
        filtered_edges = [
            (u, v, edge_key, data)
            for u, v, edge_key, data in all_edges
            if data.get("type", "?") in data_edge_types
            and _matches_query(data, data_query, EDGE_SEARCH_FIELDS)
        ]

        node_rows = [
            {
                "id": data.get("id"),
                "label": data.get("label"),
                "type": data.get("type"),
                "detail": data.get("detail", ""),
                "status": (data.get("curation") or {}).get("status", ""),
                "confidence": (data.get("curation") or {}).get("confidence", ""),
                "provenance_count": len(data.get("provenance") or []),
                "source_db": data.get("source_db", ""),
                "tissue": data.get("tissue", ""),
            }
            for _, data in filtered_nodes
        ]
        edge_rows = [
            {
                "source": u,
                "target": v,
                "type": data.get("type"),
                "label": data.get("label", ""),
                "status": (data.get("curation") or {}).get("status", ""),
                "confidence": (data.get("curation") or {}).get("confidence", ""),
                "provenance_count": len(data.get("provenance") or []),
                "carcinogen": data.get("carcinogen", ""),
                "pmid": data.get("pmid", ""),
            }
            for u, v, _, data in filtered_edges
        ]

        st.caption(
            f"Filtered to {len(filtered_nodes)} nodes and {len(filtered_edges)} edges"
        )
        col_n, col_e = st.columns(2)
        with col_n:
            st.markdown(f"**Nodes ({len(filtered_nodes)})**")
            if node_rows:
                st.dataframe(node_rows, use_container_width=True, hide_index=True)
            for _, data in filtered_nodes:
                ntype = data.get("type", "?")
                color = NODE_COLORS.get(ntype, "#888")
                with st.expander(f":{color[1:]}[●] {data.get('label', data.get('id'))} — {ntype}"):
                    st.json(data)
                    if st.button("Delete", key=f"del_node_{data['id']}"):
                        engine.remove_node(data["id"])
                        st.rerun()

        with col_e:
            st.markdown(f"**Edges ({len(filtered_edges)})**")
            if edge_rows:
                st.dataframe(edge_rows, use_container_width=True, hide_index=True)
            for i, (u, v, edge_key, data) in enumerate(filtered_edges):
                etype = data.get("type", "?")
                color = EDGE_COLORS.get(etype, "#555")
                lbl = data.get("label", etype)
                with st.expander(f":{color[1:]}[→] {u} → {v}  ({lbl})"):
                    st.json(data)
                    if st.button("Delete", key=f"del_edge_{i}_{edge_key}"):
                        engine.remove_edge(u, v, edge_key)
                        st.rerun()
