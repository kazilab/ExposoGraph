Changelog
=========

0.0.4 (2026-04-15)
------------------

Current release.

- Preserved parallel edges in the NetworkX ``MultiDiGraph`` engine so distinct
  evidence edges with the same source, predicate, and target are no longer overwritten
- Corrected KEGG fixed-width record parsing for multi-line ``GENE`` and
  ``PATHWAY`` sections used by the seeding workflow
- Tightened ``metabolism_chain()`` traversal so carcinogen-specific chains do
  not absorb unrelated unlabeled branches through shared enzymes
- ``filter_knowledge_graph()`` now returns detached model copies rather than
  aliasing the source graph objects
- Restored a clean strict ``mypy`` pass for the shipped source tree

0.0.3 (2026-03-21)
------------------

Release metadata synchronized for the current PyPI/GitHub publication.

- Updated package and app version identifiers to ``0.0.3``

0.0.2 (2026-03-19)
------------------

Current development release.

- Added graph ingestion modes: ``exploratory`` and ``strict``
- Added canonical grounding metadata, record origin tracking, and custom predicates
- Added validated/exploratory graph visibility filtering for preview, data, export, and persistence
- Added visibility-aware JSON, HTML, JS, and GEXF export helpers
- Added revision visibility tracking and SQLite schema migration support
- Added clean repository shutdown via context-manager support and fixed prior SQLite resource warnings
- Added Ollama/OpenAI backend abstraction and mode-aware seeded graph preparation

0.0.1 (2026-03-17)
------------------

Initial release.

- Pydantic v2 data models for 7 node types and 10 edge types
- NetworkX MultiDiGraph engine with load/merge/validate
- LLM-powered extraction via OpenAI structured outputs
- Streamlit app with manual entry, LLM extraction, and gene panel loading
- D3.js force-directed graph viewer with dark theme
- Export to JSON, ``graph-data.js`` (D3 viewer), and GEXF (Gephi)
- Curated Tier 1 (13 genes) and Tier 2 (23 genes) reference panels
- Referenced activity-score tables for 18 genes, including evidence metadata
- Test coverage across models, engine, exporter, storage, and reference data
- CI/CD: ruff linting, pytest matrix (3.10–3.12), PyPI publish workflow
