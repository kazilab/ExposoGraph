# Changelog

All notable changes to ExposoGraph will be documented in this file.

## [0.0.3] - 2026-03-21

### Changed

- Version bump to `0.0.3` for the current release candidate and synchronized
  package, app, and documentation metadata ahead of PyPI/GitHub publication

## [0.0.2] - 2026-03-19

### Added

- **Graph analysis module** (`graph_analysis.py`) — shortest path, all shortest paths,
  degree/betweenness centrality, metabolism chain traversal, pathway subgraph extraction,
  and variant impact scoring with activity-score integration
- **Multi-LLM support** — pluggable backend architecture (`llm_backend.py`) with OpenAI
  (structured output + JSON-mode fallback, exponential backoff retry) and Ollama
  (`/api/chat`) backends; `LLMProvider` enum in `config.py`; token/cost tracking via
  `UsageRecord` dataclass
- **Public database clients** (`db_clients/`) — KEGG REST API client (pathway + gene
  lookups), CTD batch query client (chemical-gene interactions with organism filtering),
  bundled IARC carcinogen classification data with monograph volume references
- **Seeder module** (`seeder.py`) — converts KEGG pathways and CTD interactions directly
  into `KnowledgeGraph` objects with provenance tracking and heuristic edge-type inference
- **Streamlit UI updates** — LLM provider selector (OpenAI/Ollama) in extraction tab with
  Ollama-specific URL and model inputs; token usage display on successful extraction
- **Pre-built example** — `examples/bap_graph.json` (20 nodes, 20 edges covering full
  BaP activation, detoxification, adduct formation, and repair pathways) and
  `examples/build_bap_graph.py` demo script
- **GEXF export** (`exporter.py`) — Gephi-compatible graph export with automatic
  JSON-serialization of complex node/edge attributes
- **Comprehensive test suite** — 226 tests across 14 test modules; `test_integration.py`
  for end-to-end pipeline validation; `test_llm_backend.py`, `test_db_clients.py`,
  `test_seeder.py`, `test_graph_analysis.py` for new modules
- **CI/CD** — GitHub Actions workflow with pytest-cov (85% coverage gate, currently 96%),
  ruff linting, mypy strict type checking
- **Sphinx documentation** scaffolding with ReadTheDocs configuration

### Fixed

- **Fabricated PMID** — replaced non-existent PMID 41024270 (OGG1) with verified
  PMID 25588927 (Zhou et al. meta-analysis)
- **PMID-title mismatches** — corrected titles for PMID 29194389 (CYP2A6, Tanner &
  Tyndale 2017) and PMID 23665933 (CYP3A4, Okubo et al. 2013)
- **ClinPGx URL pattern** — `clinpgx.org/gene/{symbol}` does not resolve; replaced with
  PharmGKB accession ID lookup (`clinpgx.org/gene/{accession_id}`) for all 28 gene panels
- **IARC references** — added specific IARC Monograph volume numbers and years to all
  30 classification entries (previously generic "Group N" only)
- **Missing PubMed references** — added literature citations to 5 activity score metadata
  entries (CYP2D6, CYP2C9, CYP2C19, UGT1A1, XPC) that previously had none
- **GEXF export crash** — NetworkX GEXF writer failed on list/dict node attributes
  (provenance, curation); fixed by JSON-serializing non-scalar values before write

### Changed

- `extract_graph()` now delegates to pluggable `LLMBackend` protocol; new
  `extract_graph_with_usage()` returns both the graph and a `UsageRecord`
- `__init__.py` public API expanded with all new module exports
- `pyproject.toml` — added `[ollama]`, `[db]`, and `[docs]` optional dependency groups;
  pytest-cov configuration; mypy overrides for new dependencies

## [0.0.1] - 2026-03-17

### Added

- Initial release: Pydantic v2 models, NetworkX graph engine, LLM extraction (OpenAI),
  JSON/D3.js/HTML export, Streamlit UI, reference gene panels and activity scores
