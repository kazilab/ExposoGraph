# ExposoGraph

[![CI](https://github.com/kazilab/ExposoGraph/actions/workflows/ci.yml/badge.svg)](https://github.com/kazilab/ExposoGraph/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Build, curate, and export carcinogen metabolism knowledge graphs using LLM-powered extraction and manual entry.

Part of the **CarcinoGenomic Platform** — a 5-layer computational pipeline for individualized carcinogen metabolism risk assessment from germline DNA.

Version: **0.0.2**
Developed by: **Data analysis team @ KaziLab**
Contact: **exposograph@kazilab.se**
Copyright: **KaziLab**

## Acknowledgement

Parts of this documentation and code were created with assistance from ChatGPT Codex and Claude Code.

## Features

- **Multi-LLM Extraction** — Describe a carcinogen metabolism pathway in plain English; OpenAI (GPT-4o) or local Ollama models extract structured nodes and edges automatically
- **Manual Entry** — Add and annotate nodes and edges with full provenance and curation tracking
- **Graph Analysis** — Shortest path, centrality, metabolism chain traversal, pathway subgraph, variant impact scoring
- **Public DB Integration** — KEGG pathway lookups, CTD chemical-gene interactions, IARC carcinogen classifications
- **Interactive Preview** — Color-coded graph visualization with drag-to-rearrange and zoom
- **Rich Annotations** — Source databases (IARC, KEGG, CTD, PharmVar, CPIC, GTEx), PubMed IDs, tissue context, pharmacogenomic variants, activity scores
- **Multiple Export Formats** — Standalone interactive HTML, JSON, D3.js viewer (`graph-data.js`), GEXF (Gephi)
- **Validation** — Referential integrity checks at model level, dangling edge detection, carcinogen context validation
- **Persistent Storage** — SQLite-backed revision history with atomic operations

## Quick Start

### Try Without an API Key

A pre-built Benzo[a]pyrene metabolism graph is included:

```bash
pip install -e .
python examples/build_bap_graph.py
```

This loads `examples/bap_graph.json` (20 nodes, 21 edges covering the full BaP → BPDE → DNA adduct pathway), runs graph analysis, and exports to HTML and JSON.

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

### Jupyter Notebook

```bash
pip install -e ".[notebook]"
jupyter notebook ExposoGraph_notebook.ipynb
```

### Python Library

```bash
pip install -e .
```

```python
from ExposoGraph import GraphEngine, extract_graph, centrality, metabolism_chain

# LLM extraction (requires OpenAI API key)
kg = extract_graph("Benzo[a]pyrene is activated by CYP1A1...")
engine = GraphEngine()
engine.merge(kg)

# Analysis
scores = centrality(engine, method="degree")
chain = metabolism_chain(engine, "BaP")

# Serialize
print(engine.to_json())
```

#### Using Ollama (Local LLM)

```python
from ExposoGraph import extract_graph
from ExposoGraph.llm_backend import OllamaBackend

backend = OllamaBackend(base_url="http://localhost:11434")
kg = extract_graph("BaP is activated by CYP1A1...", backend=backend, model="llama3.1")
```

#### Public Database Integration

```python
from ExposoGraph.db_clients import KEGGClient, CTDClient, IARCClassifier
from ExposoGraph.seeder import seed_from_kegg_pathway, seed_from_ctd

# Seed from KEGG pathway
kg = seed_from_kegg_pathway("hsa05204")

# Seed from CTD
kg = seed_from_ctd("Benzo(a)pyrene")

# IARC classification lookup
clf = IARCClassifier()
clf.classify("Benzo[a]pyrene")  # → IARCGroup.GROUP_1
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

## Project Structure

```
ExposoGraph/
├── __init__.py          # Public API exports
├── app.py               # Streamlit UI orchestrator
├── branding.py          # Version and metadata
├── config.py            # App modes and LLM provider enum
├── engine.py            # NetworkX-backed graph engine
├── exporter.py          # JSON, D3.js, HTML, GEXF export
├── graph_analysis.py    # Shortest path, centrality, metabolism chains
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
└── build_bap_graph.py   # Demo script: load → analyze → export
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

**Edges:** ACTIVATES, DETOXIFIES, TRANSPORTS, FORMS_ADDUCT, REPAIRS, PATHWAY, EXPRESSED_IN, INDUCES, INHIBITS, ENCODES

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
| `notebook` | `pip install -e ".[notebook]"` | Jupyter + PyVis |
| `dev` | `pip install -e ".[dev]"` | pytest, ruff, mypy |
| `docs` | `pip install -e ".[docs]"` | Sphinx + Furo |
| `all` | `pip install -e ".[all]"` | Everything |

## License

MIT
