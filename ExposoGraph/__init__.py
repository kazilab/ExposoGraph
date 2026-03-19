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

from .config import AppMode, LLMProvider, get_app_mode, normalize_app_mode, persistence_enabled
from .engine import GraphEngine
from .exporter import (
    ensure_viewer_bundle,
    export_viewer_bundle,
    parse_graph_artifact,
    parse_graph_data_js,
    parse_graph_data_text,
    parse_graph_html,
    to_gexf,
    to_graph_data_js,
    to_interactive_html,
    to_interactive_html_string,
    to_json,
)
from .llm_backend import LLMBackend, OllamaBackend, OpenAIBackend, UsageRecord
from .llm_extractor import extract_graph, extract_graph_with_usage
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
from .graph_analysis import (
    MetabolismChain,
    VariantImpact,
    all_shortest_paths,
    centrality,
    metabolism_chain,
    pathway_subgraph,
    shortest_path,
    variant_impact_score,
)
from .db_clients import CTDClient, IARCClassifier, IARCGroup, KEGGClient
from .seeder import seed_from_ctd, seed_from_kegg_pathway, seed_iarc_classification
from .storage import GraphRepository, GraphRevision, GraphRevisionSummary

__all__ = [
    "ACTIVITY_SCORE_METADATA",
    "ACTIVITY_SCORES",
    "APP_NAME",
    "CTDClient",
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
    "IARCClassifier",
    "IARCGroup",
    "GraphRevision",
    "GraphRevisionSummary",
    "KEGGClient",
    "KnowledgeGraph",
    "LLMBackend",
    "LLMProvider",
    "MetabolismChain",
    "Node",
    "NodeType",
    "OllamaBackend",
    "OpenAIBackend",
    "ProvenanceRecord",
    "VariantImpact",
    "build_full_panel",
    "build_tier1_panel",
    "build_tier2_panel",
    "ensure_viewer_bundle",
    "export_viewer_bundle",
    "all_shortest_paths",
    "centrality",
    "UsageRecord",
    "extract_graph",
    "extract_graph_with_usage",
    "get_activity_score_metadata",
    "get_activity_score_references",
    "get_activity_scores",
    "get_app_mode",
    "metabolism_chain",
    "normalize_app_mode",
    "pathway_subgraph",
    "parse_graph_artifact",
    "parse_graph_data_js",
    "parse_graph_data_text",
    "parse_graph_html",
    "persistence_enabled",
    "seed_from_ctd",
    "seed_from_kegg_pathway",
    "seed_iarc_classification",
    "shortest_path",
    "to_gexf",
    "to_graph_data_js",
    "to_interactive_html",
    "to_interactive_html_string",
    "to_json",
    "variant_impact_score",
]
