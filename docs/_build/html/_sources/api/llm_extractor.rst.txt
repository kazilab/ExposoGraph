``ExposoGraph.llm_extractor``
=============================

LLM-powered entity and relation extraction using OpenAI structured outputs.

.. autofunction:: ExposoGraph.llm_extractor.extract_graph

.. data:: ExposoGraph.llm_extractor.SYSTEM_PROMPT

   The system prompt sent to the LLM, containing the full schema specification
   and extraction guidelines.

.. data:: ExposoGraph.llm_extractor.EXAMPLE_INPUT

   Example input text describing the Benzo[a]pyrene metabolism pathway,
   useful for testing and demonstration.
