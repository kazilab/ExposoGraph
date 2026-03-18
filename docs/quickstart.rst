Quick Start
===========

Installation
------------

From PyPI (once published):

.. code-block:: bash

   pip install ExposoGraph

From source (development):

.. code-block:: bash

   git clone https://github.com/julhashkazi/kg-builder.git
   cd kg-builder
   pip install -e ".[all]"

Optional dependency groups:

- ``streamlit`` — Streamlit UI and agraph visualization
- ``notebook`` — Jupyter and pyvis
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

Jupyter Notebook
----------------

.. code-block:: bash

   pip install -e ".[notebook]"
   jupyter notebook ExposoGraph_notebook.ipynb

Python Library
--------------

.. code-block:: python

   from ExposoGraph import GraphEngine, extract_graph

   # LLM-powered extraction
   kg = extract_graph("Benzo[a]pyrene is activated by CYP1A1...")
   engine = GraphEngine()
   engine.merge(kg)

   print(engine.node_count, "nodes")
   print(engine.to_json())

Loading Reference Gene Panels
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from ExposoGraph import (
       GraphEngine,
       build_full_panel,
       get_activity_score_references,
       get_activity_scores,
   )

   # Load all 28 Tier 1 + Tier 2 genes
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

   from ExposoGraph import to_graph_data_js, to_interactive_html, to_json, to_gexf

   # Standalone interactive HTML
   to_interactive_html(engine, "knowledge-graph/index.html")

   # D3.js viewer format
   to_graph_data_js(engine, "knowledge-graph/graph-data.js")

   # Plain JSON
   to_json(engine, "output.json")

   # GEXF (Gephi)
   to_gexf(engine, "output.gexf")
