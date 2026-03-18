Changelog
=========

0.0.1 (2026-03-18)
------------------

Initial release.

- Pydantic v2 data models for 7 node types and 10 edge types
- NetworkX MultiDiGraph engine with load/merge/validate
- LLM-powered extraction via OpenAI structured outputs
- Streamlit app with manual entry, LLM extraction, and gene panel loading
- D3.js force-directed graph viewer with dark theme
- Export to JSON, ``graph-data.js`` (D3 viewer), and GEXF (Gephi)
- Curated Tier 1 (13 genes) and Tier 2 (15 genes) reference panels
- Referenced activity-score tables for 18 genes, including evidence metadata
- Test coverage across models, engine, exporter, storage, and reference data
- CI/CD: ruff linting, pytest matrix (3.10–3.12), PyPI publish workflow
