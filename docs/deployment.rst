Deployment
==========

Streamlit Cloud
---------------

1. Push the repository to GitHub.

2. Connect the repo on `Streamlit Cloud <https://share.streamlit.io>`_.

3. Set the **main file path** to ``ExposoGraph/app.py``.

4. Add your OpenAI API key in **Secrets management**:

   .. code-block:: toml

      OPENAI_API_KEY = "sk-..."

5. Deploy. The app reads secrets via ``st.secrets`` and falls back to
   environment variables for local development.

6. For privacy-safe public deployment, keep the default stateless mode or
   set:

   .. code-block:: toml

      ExposoGraph_MODE = "stateless"

   In stateless mode the app does not write user graphs, revisions, or HTML
   snapshots to server-side storage. Users must download the interactive HTML
   output to keep their work.

Local Development
-----------------

.. code-block:: bash

   export OPENAI_API_KEY="sk-..."
   export ExposoGraph_MODE=local
   pip install -e ".[streamlit]"
   streamlit run ExposoGraph/app.py

Or copy the example secrets file:

.. code-block:: bash

   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # Edit .streamlit/secrets.toml with your key

PyPI Publishing
---------------

The project uses `hatch <https://hatch.pypa.io/>`_ as its build backend.
A GitHub Actions workflow publishes to PyPI automatically on each GitHub
Release using `trusted publishers <https://docs.pypi.org/trusted-publishers/>`_.

To build locally:

.. code-block:: bash

   pip install build
   python -m build
   # Outputs dist/exposograph-0.0.1-py3-none-any.whl
