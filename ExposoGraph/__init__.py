"""ExposoGraph.

Build, curate, and export carcinogen metabolism knowledge graphs
using LLM-powered extraction and manual entry.

Parts of this documentation and code were created with assistance
from ChatGPT Codex and Claude Code.
"""

from .branding import (
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    CONTACT_EMAIL,
    COPYRIGHT_HOLDER,
    DEVELOPED_BY,
)

__version__ = APP_VERSION

from .config import AppMode, get_app_mode, normalize_app_mode, persistence_enabled
from .engine import GraphEngine
from .exporter import (
    ensure_viewer_bundle,
    export_viewer_bundle,
    parse_graph_artifact,
    parse_graph_data_text,
    parse_graph_html,
    parse_graph_data_js,
    to_gexf,
    to_graph_data_js,
    to_interactive_html,
    to_interactive_html_string,
    to_json,
)
from .llm_extractor import extract_graph
from .models import (
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
from .reference_data import (
    ACTIVITY_SCORE_METADATA,
    ACTIVITY_SCORES,
    build_full_panel,
    build_tier1_panel,
    build_tier2_panel,
    get_activity_score_metadata,
    get_activity_score_references,
    get_activity_scores,
)
from .storage import GraphRepository, GraphRevision, GraphRevisionSummary

__all__ = [
    "ACTIVITY_SCORES",
    "ACTIVITY_SCORE_METADATA",
    "APP_NAME",
    "APP_TAGLINE",
    "APP_VERSION",
    "AppMode",
    "CONTACT_EMAIL",
    "COPYRIGHT_HOLDER",
    "CurationConfidence",
    "CurationRecord",
    "CurationStatus",
    "DEVELOPED_BY",
    "Edge",
    "EdgeType",
    "GraphEngine",
    "GraphRepository",
    "GraphRevision",
    "GraphRevisionSummary",
    "KnowledgeGraph",
    "Node",
    "NodeType",
    "ProvenanceRecord",
    "ensure_viewer_bundle",
    "export_viewer_bundle",
    "parse_graph_artifact",
    "parse_graph_data_text",
    "parse_graph_html",
    "build_full_panel",
    "build_tier1_panel",
    "build_tier2_panel",
    "extract_graph",
    "get_app_mode",
    "get_activity_score_metadata",
    "get_activity_score_references",
    "get_activity_scores",
    "normalize_app_mode",
    "persistence_enabled",
    "to_interactive_html",
    "to_interactive_html_string",
    "parse_graph_data_js",
    "to_gexf",
    "to_graph_data_js",
    "to_json",
]
