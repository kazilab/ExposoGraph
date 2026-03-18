# ExposoGraph

Build, curate, and export carcinogen metabolism knowledge graphs using LLM-powered extraction and manual entry.

Part of the **CarcinoGenomic Platform** — a 5-layer computational pipeline for individualized carcinogen metabolism risk assessment from germline DNA.

Version: **0.0.1**
Developed by: **Data analysis team @ KaziLab**
Contact: **exposograph@kazilab.se**
Copyright: **KaziLab**

## Acknowledgement

Parts of this documentation and code were created with assistance from ChatGPT Codex and Claude Code.

## Features

- **LLM Extraction** — Describe a carcinogen metabolism pathway in plain English; GPT-4o extracts structured nodes and edges automatically
- **Manual Entry** — Add and annotate nodes (Carcinogen, Enzyme, Metabolite, DNA_Adduct, Pathway) and edges with full provenance tracking
- **Interactive Preview** — Color-coded graph visualization with drag-to-rearrange and zoom
- **Rich Annotations** — Source databases (IARC, KEGG, CTD, PharmVar, CPIC, GTEx), PubMed IDs, tissue context, pharmacogenomic variants, activity scores
- **Multiple Export Formats** — standalone interactive HTML, JSON, D3.js viewer (`graph-data.js`), GEXF (Gephi)
- **Validation** — Checks for dangling edges, missing carcinogen context nodes

## Quick Start

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
from ExposoGraph import GraphEngine, extract_graph

# LLM extraction
kg = extract_graph("Benzo[a]pyrene is activated by CYP1A1...")
engine = GraphEngine()
engine.merge(kg)

# Serialize
print(engine.to_json())
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
├── __init__.py        # Public API exports
├── app.py             # Streamlit UI
├── engine.py          # NetworkX-backed graph engine
├── exporter.py        # JSON, D3.js, GEXF export
├── llm_extractor.py   # OpenAI LLM extraction
└── models.py          # Pydantic data models
```

## Node & Edge Types

**Nodes:** Carcinogen, Enzyme, Metabolite, DNA_Adduct, Pathway

**Edges:** ACTIVATES, DETOXIFIES, TRANSPORTS, FORMS_ADDUCT, REPAIRS, PATHWAY

## Development

```bash
pip install -e ".[all]"
pytest
ruff check .
```

## License

MIT
