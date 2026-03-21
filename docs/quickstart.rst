Quick Start
===========

Installation
------------

From PyPI (once published):

.. code-block:: bash

   pip install ExposoGraph

From source (development):

.. code-block:: bash

   git clone https://github.com/kazilab/ExposoGraph.git
   cd ExposoGraph
   pip install -e ".[all]"

Optional dependency groups:

- ``streamlit`` — Streamlit UI and agraph visualization
- ``viewer`` — Dash Cytoscape advanced graph viewer
- ``notebook`` — Jupyter, Plotly, and Matplotlib
- ``dev`` — pytest, ruff, mypy
- ``docs`` — Sphinx, MyST, and Furo for documentation builds
- ``all`` — everything above

Streamlit App
-------------

.. code-block:: bash

   pip install -e ".[streamlit]"
   streamlit run ExposoGraph/app.py

App mode defaults to ``stateless``. To set it explicitly:

.. code-block:: bash

   export ExposoGraph_MODE=stateless

Set your OpenAI API key in the sidebar, or via environment variable:

.. code-block:: bash

   export OPENAI_API_KEY="sk-..."

For local persistence and revision history, switch to local mode:

.. code-block:: bash

   export ExposoGraph_MODE=local
   streamlit run ExposoGraph/app.py

Jupyter
-------

.. code-block:: bash

   pip install -e ".[notebook]"
   jupyter lab

No notebook file is currently bundled in the repository. Use the installed
package from your own notebook, or start from the runnable examples in
``examples/``.

Advanced Viewer
---------------

.. code-block:: bash

   pip install -e ".[viewer]"

.. code-block:: python

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

Python Library
--------------

.. code-block:: python

   from ExposoGraph import (
       GraphEngine,
       GraphMode,
       GraphVisibility,
       extract_graph,
       to_json,
   )

   # LLM-powered extraction
   # exploratory keeps provisional nodes and edges
   kg = extract_graph(
       "Benzo[a]pyrene is activated by CYP1A1...",
       mode=GraphMode.EXPLORATORY,
   )
   engine = GraphEngine()
   engine.merge(kg, mode=GraphMode.EXPLORATORY)

   print(engine.node_count, "nodes")
   to_json(engine, "validated_only.json", visibility=GraphVisibility.VALIDATED_ONLY)

Graph Modes
^^^^^^^^^^^

ExposoGraph uses two ingestion modes:

- ``exploratory`` keeps unmatched and custom content, annotated as provisional
- ``strict`` keeps only canonically grounded nodes and edges

.. code-block:: python

   from ExposoGraph import GraphEngine, GraphMode, extract_graph

   strict_kg = extract_graph(
       "BaP activates CYP1A1 and forms BPDE adducts",
       mode=GraphMode.STRICT,
   )

   engine = GraphEngine()
   warnings = engine.merge(strict_kg, mode=GraphMode.STRICT)
   print(warnings)

Loading Reference Gene Panels
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from ExposoGraph import (
       GraphEngine,
       build_full_panel,
       get_activity_score_references,
       get_activity_scores,
   )

   # Load all 36 Tier 1 + Tier 2 genes
   kg = build_full_panel()
   engine = GraphEngine()
   engine.load(kg)

   # Look up activity scores for a gene
   scores = get_activity_scores("CYP2D6")
   for s in scores:
       print(f"  {s['allele']}: {s['value']} — {s['phenotype']}")

   refs = get_activity_score_references("CYP2D6")
   for ref in refs or []:
       print(f"  {ref['source_db']}: {ref.get('pmid') or ref.get('record_id')}")

Exporting
^^^^^^^^^

.. code-block:: python

   from ExposoGraph import (
       GraphVisibility,
       ViewerLayoutMode,
       to_gexf,
       to_graph_data_js,
       to_interactive_html,
       to_json,
       to_plotly_html,
       write_cytoscape_bundle,
   )

   # Standalone parseable app HTML
   to_interactive_html(
       engine,
       "exports/graph.html",
       visibility=GraphVisibility.ALL,
   )

   # Standalone Plotly HTML
   to_plotly_html(
       engine,
       "exports/graph_plotly.html",
       visibility=GraphVisibility.ALL,
   )

   # Validated-only HTML
   to_interactive_html(
       engine,
       "exports/graph_validated.html",
       visibility=GraphVisibility.VALIDATED_ONLY,
   )

   # Cytoscape-ready JSON bundle
   write_cytoscape_bundle(
       engine,
       "exports/graph_cytoscape.json",
       visibility=GraphVisibility.ALL,
       layout_mode=ViewerLayoutMode.COSE,
   )

   # D3.js viewer format
   to_graph_data_js(
       engine,
       "exports/graph-data.js",
       visibility=GraphVisibility.ALL,
   )

   # Plain JSON
   to_json(
       engine,
       "output.json",
       visibility=GraphVisibility.EXPLORATORY_ONLY,
   )

   # GEXF (Gephi)
   to_gexf(
       engine,
       "output.gexf",
       visibility=GraphVisibility.VALIDATED_ONLY,
   )

Filtered Revisions
^^^^^^^^^^^^^^^^^^

In ``local`` app mode, SQLite revision saves can persist either the full graph
or the current visibility slice.

.. code-block:: python

   from ExposoGraph import GraphRepository, GraphVisibility

   with GraphRepository("data/ExposoGraph.sqlite3") as repo:
       repo.save_engine(
           graph_key="bap_demo",
           graph_name="BaP Demo",
           engine=engine,
           visibility=GraphVisibility.VALIDATED_ONLY,
           note="Validated subset only",
       )

See also ``examples/mode_visibility_demo.py`` for a runnable no-API-key
example that demonstrates strict vs exploratory merge behavior and
visibility-aware export.
