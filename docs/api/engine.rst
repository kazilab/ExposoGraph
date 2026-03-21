``ExposoGraph.engine``
======================

NetworkX-backed graph engine for building and querying the knowledge graph.

``GraphEngine.load(...)`` and ``GraphEngine.merge(...)`` both accept a
``mode`` argument:

- ``exploratory`` keeps provisional content after grounding
- ``strict`` merges only canonically grounded content and returns warnings for dropped items

.. autoclass:: ExposoGraph.engine.GraphEngine
   :members:
   :undoc-members:
   :show-inheritance:
