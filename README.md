# ExposoGraph

[![CI](https://github.com/kazilab/ExposoGraph/actions/workflows/ci.yml/badge.svg)](https://github.com/kazilab/ExposoGraph/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Build, curate, and export carcinogen metabolism knowledge graphs using LLM-powered extraction and manual entry.

Part of the **CarcinoGenomic Platform** — a 5-layer computational pipeline for individualized carcinogen metabolism risk assessment from germline DNA.

Version: **0.0.3**
Developed by: **Data analysis team @ KaziLab**
Contact: **exposograph@kazilab.se**
Copyright: **KaziLab**

## Acknowledgement

Parts of this documentation and code were created with assistance from ChatGPT Codex and Claude Code.

## Features

- **Multi-LLM Extraction** — Describe a carcinogen metabolism pathway in plain English; OpenAI (GPT-4o) or local Ollama models extract structured nodes and edges automatically
- **Mode-Aware Ingestion** — Use `exploratory` mode to keep provisional entities or `strict` mode to keep only canonically grounded content
- **Manual Entry** — Add and annotate nodes and edges with full provenance and curation tracking
- **Graph Analysis** — Shortest path, centrality, metabolism chain traversal, pathway subgraph, variant impact scoring
- **Public DB Integration** — KEGG pathway lookups, CTD chemical-gene interactions, IARC carcinogen classifications
- **Interactive Preview** — Color-coded Streamlit AGraph visualization with hover metadata, search/filter controls, zoom, and downloadable Plotly HTML exports
- **Advanced Graph Viewer** — Dash Cytoscape viewer with sidebar search, legends, carcinogen filters, detail panel, image export, and saved layout JSON
- **Validated vs Exploratory Views** — Filter the current graph to `all`, `validated only`, or `exploratory only` in the UI and export pipeline
- **Rich Annotations** — Structured provenance records, source manifests, curated KEGG pathway coverage, PubMed IDs, tissue context, pharmacogenomic variants, activity scores
- **Multiple Export Formats** — Standalone Plotly HTML, parseable app HTML, JSON, D3.js viewer (`graph-data.js`), GEXF (Gephi)
- **Viewer Data Contract** — Export a Cytoscape-ready JSON bundle and saved preset layout for richer web-style exploration without maintaining custom JavaScript
- **Validation** — Referential integrity checks at model level, dangling edge detection, carcinogen context validation
- **Persistent Storage** — SQLite-backed revision history with explicit export visibility tracking and atomic operations

## Quick Start

### Try Without an API Key

A pre-built Benzo[a]pyrene metabolism graph is included:

```bash
pip install -e .
python examples/build_bap_graph.py
```

This loads `examples/bap_graph.json` (20 nodes, 20 edges covering the full BaP → BPDE → DNA adduct pathway), runs graph analysis, and exports to HTML and JSON.

For a no-API-key demonstration of strict vs exploratory handling and
validated-only exports:

```bash
python examples/mode_visibility_demo.py
```

<details>
<summary>Sample output</summary>

```
Loaded graph: 20 nodes, 20 edges

Shortest path CYP1A1 → BPDE-dG: CYP1A1 → BPDE → BPDE_dG

Top-5 nodes by degree centrality:
  CYP1A1        0.263
  BPDE          0.211
  CYP1B1        0.158
  BPDE_dG       0.158
  BPDE_GSH      0.158

BaP metabolism chain: 16 nodes, 13 edges
  Activation edges:    4
  Detoxification edges: 3
  Adduct edges:        1
  Repair edges:        3

Variant impact score for CYP1A1:
  Activity score:        1.0
  Downstream adducts:    1
  Impact score:          1.00
```

</details>

### Sample JSON

```json
{
  "nodes": [
    {"id": "BaP", "label": "Benzo[a]pyrene", "type": "Carcinogen", "group": "PAH", "iarc": "Group 1"},
    {"id": "CYP1A1", "label": "CYP1A1", "type": "Enzyme", "phase": "I", "role": "Activation"},
    {"id": "BPDE", "label": "BPDE", "type": "Metabolite", "reactivity": "High"},
    {"id": "BPDE_dG", "label": "BPDE-N2-dG", "type": "DNA_Adduct"}
  ],
  "edges": [
    {"source": "CYP1A1", "target": "BPDE", "type": "ACTIVATES", "carcinogen": "BaP"},
    {"source": "BPDE", "target": "BPDE_dG", "type": "FORMS_ADDUCT", "carcinogen": "BaP"}
  ]
}
```

### Streamlit App

```bash
pip install -e ".[streamlit]"
streamlit run ExposoGraph/app.py
```

App mode defaults to `stateless`, which disables server-side saves and
is appropriate for public web deployment. To enable local revision history
and file saves on your own machine:

```bash
export ExposoGraph_MODE=local
streamlit run ExposoGraph/app.py
```

### Jupyter

```bash
pip install -e ".[notebook]"
jupyter lab
```

No notebook file is currently bundled in this repository. Use the installed
package from your own notebook, or start from the runnable examples in
`examples/`.

### Advanced Viewer

```bash
pip install -e ".[viewer]"
```

```python
from ExposoGraph import (
    GraphVisibility,
    ViewerLayoutMode,
    launch_dash_viewer,
    write_cytoscape_bundle,
)

write_cytoscape_bundle(
    engine,
    "exports/graph_cytoscape.json",
    visibility=GraphVisibility.ALL,
    layout_mode=ViewerLayoutMode.COSE,
)

launch_dash_viewer(
    engine,
    visibility=GraphVisibility.ALL,
    layout_mode=ViewerLayoutMode.COSE,
    port=8050,
)
```

### Python Library

```bash
pip install -e .
```

```python
from ExposoGraph import (
    GraphEngine,
    GraphMode,
    GraphVisibility,
    centrality,
    extract_graph,
    metabolism_chain,
    to_json,
)

# LLM extraction (requires OpenAI API key)
# exploratory: keep unmatched or custom content
kg = extract_graph(
    "Benzo[a]pyrene is activated by CYP1A1...",
    mode=GraphMode.EXPLORATORY,
)
engine = GraphEngine()
engine.merge(kg, mode=GraphMode.EXPLORATORY)

# Analysis
scores = centrality(engine, method="degree")
chain = metabolism_chain(engine, "BaP")

# Visibility-aware export
to_json(engine, "graph_validated.json", visibility=GraphVisibility.VALIDATED_ONLY)
```

#### Using Ollama (Local LLM)

```python
from ExposoGraph import GraphMode, extract_graph
from ExposoGraph.llm_backend import OllamaBackend

backend = OllamaBackend(base_url="http://localhost:11434")
kg = extract_graph(
    "BaP is activated by CYP1A1...",
    backend=backend,
    model="llama3.1",
    mode=GraphMode.EXPLORATORY,
)
```

#### Public Database Integration

```python
from ExposoGraph import GraphMode
from ExposoGraph.db_clients import IARCClassifier
from ExposoGraph.seeder import seed_from_ctd, seed_from_kegg_pathway

# Seed from KEGG pathway
kg = seed_from_kegg_pathway("hsa05204", mode=GraphMode.STRICT)

# Seed from CTD
kg = seed_from_ctd("Benzo(a)pyrene", mode=GraphMode.EXPLORATORY)

# IARC classification lookup
clf = IARCClassifier()
clf.classify("Benzo[a]pyrene")  # → IARCGroup.GROUP_1
```

#### Reference Curation Metadata

```python
from ExposoGraph import CURATION_SOURCE_MANIFEST, REFERENCE_KEGG_PATHWAYS

primary_sources = CURATION_SOURCE_MANIFEST["primary_sources"]
kegg_ids = [entry["pathway_id"] for entry in REFERENCE_KEGG_PATHWAYS]
```

#### Manuscript-Aligned Showcase Summary

```python
from ExposoGraph import build_full_legends_architecture_summary

summary = build_full_legends_architecture_summary()

summary.node_count          # 96
summary.edge_count          # 102
summary.node_type_counts    # {'Carcinogen': 15, 'Enzyme': 36, ...}
summary.edge_type_counts    # {'ACTIVATES': 30, 'DETOXIFIES': 23, ...}
summary.carcinogen_classes  # grouped class inventories for section 2.2 rewrites
```

#### Optional Androgen Module

```python
from ExposoGraph import build_androgen_module_graph, build_full_legends_graph

androgen_only = build_androgen_module_graph()
showcase_with_androgen = build_full_legends_graph(include_androgen_module=True)
```

## Configuration

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY="sk-..."
```

Or enter it in the Streamlit sidebar when running the app.

For Streamlit Cloud deployment, add the key to `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "sk-..."
```

## Graph Modes and Visibility

Two separate controls now shape how data moves through the system:

- **Graph mode** controls ingestion behavior:
  - `exploratory` keeps unmatched or custom entities and marks them as provisional
  - `strict` keeps only canonically grounded nodes and edges
- **Graph visibility** controls viewing and export behavior:
  - `all`
  - `validated_only`
  - `exploratory_only`

Typical pattern:

```python
from ExposoGraph import (
    GraphEngine,
    GraphMode,
    GraphRepository,
    GraphVisibility,
    ViewerLayoutMode,
    launch_dash_viewer,
    write_cytoscape_bundle,
    extract_graph,
    to_interactive_html,
    to_plotly_html,
)

engine = GraphEngine()
kg = extract_graph(
    "BaP induces CYP1A1 and forms BPDE adducts",
    mode=GraphMode.STRICT,
)
engine.merge(kg, mode=GraphMode.STRICT)

to_interactive_html(
    engine,
    "validated_graph.html",
    visibility=GraphVisibility.VALIDATED_ONLY,
)

to_plotly_html(
    engine,
    "validated_graph_plotly.html",
    visibility=GraphVisibility.VALIDATED_ONLY,
)

write_cytoscape_bundle(
    engine,
    "validated_graph_cytoscape.json",
    visibility=GraphVisibility.VALIDATED_ONLY,
    layout_mode=ViewerLayoutMode.PRESET,
)

with GraphRepository("data/ExposoGraph.sqlite3") as repo:
    repo.save_engine(
        graph_key="bap_validated",
        graph_name="BaP Validated",
        engine=engine,
        visibility=GraphVisibility.VALIDATED_ONLY,
    )
```

## Project Structure

```
ExposoGraph/
├── __init__.py          # Public API exports
├── app.py               # Streamlit UI orchestrator
├── branding.py          # Version and metadata
├── config.py            # App modes, graph modes, and visibility enums
├── engine.py            # NetworkX-backed graph engine
├── exporter.py          # JSON, D3.js, HTML, GEXF export
├── graph_filters.py     # Validated/exploratory graph filtering helpers
├── graph_analysis.py    # Shortest path, centrality, metabolism chains
├── grounding.py         # Canonical grounding and strict-mode preparation
├── llm_backend.py       # Pluggable LLM backends (OpenAI, Ollama)
├── llm_extractor.py     # LLM prompt + extraction pipeline
├── models.py            # Pydantic data models (Node, Edge, KnowledgeGraph)
├── reference_data.py    # Gene panels and activity scores
├── seeder.py            # DB-to-KnowledgeGraph conversion
├── storage.py           # SQLite revision history
├── db_clients/
│   ├── kegg.py          # KEGG REST API client
│   ├── ctd.py           # CTD chemical-gene interaction client
│   └── iarc.py          # Bundled IARC classification data
├── ui_extract.py        # Tab: LLM extraction
├── ui_manual.py         # Tab: manual node/edge entry
├── ui_preview.py        # Tab: interactive graph preview
└── ui_data.py           # Tab: raw data view
examples/
├── bap_graph.json       # Pre-built BaP metabolism graph (no API key needed)
├── build_bap_graph.py   # Demo script: load → analyze → export
└── mode_visibility_demo.py  # Demo script: strict ingestion + filtered export/save
tests/
├── test_integration.py  # End-to-end pipeline test
├── test_engine.py
├── test_models.py
├── test_exporter.py
├── test_graph_analysis.py
├── test_llm_backend.py
├── test_llm_extractor.py
├── test_db_clients.py
├── test_seeder.py
├── test_reference_data.py
├── test_config.py
└── test_storage.py
```

## Node & Edge Types

**Nodes:** Carcinogen, Enzyme, Gene, Metabolite, DNA_Adduct, Pathway, Tissue

**Edges:** ACTIVATES, DETOXIFIES, TRANSPORTS, FORMS_ADDUCT, REPAIRS, PATHWAY, EXPRESSED_IN, INDUCES, INHIBITS, ENCODES, CUSTOM

## Development

```bash
pip install -e ".[all]"
pytest                           # runs with --cov, 85% threshold gate
ruff check .
mypy ExposoGraph/
```

### Optional dependency groups

| Group | Install | Provides |
|-------|---------|----------|
| `llm` | `pip install -e ".[llm]"` | OpenAI API support |
| `ollama` | `pip install -e ".[ollama]"` | Ollama local LLM support |
| `db` | `pip install -e ".[db]"` | KEGG/CTD HTTP clients |
| `streamlit` | `pip install -e ".[streamlit]"` | Streamlit web app |
| `notebook` | `pip install -e ".[notebook]"` | Jupyter + Plotly/Matplotlib |
| `dev` | `pip install -e ".[dev]"` | pytest, ruff, mypy |
| `docs` | `pip install -e ".[docs]"` | Sphinx + Furo |
| `all` | `pip install -e ".[all]"` | Everything |

## License

MIT
