"""LLM-powered entity / relation extraction for the knowledge graph.

Supports OpenAI models via structured outputs. Falls back to JSON-mode
parsing when structured output is unavailable.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

from .models import KnowledgeGraph

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert biochemist and toxicologist. Your task is to extract a
structured knowledge graph from the user's natural-language description of
carcinogen metabolism, gene interactions, and DNA damage pathways.

Return **only** valid JSON matching the schema below. Do not include any
text outside the JSON block.

### Node types (use exactly these strings for "type"):
- Carcinogen  — chemical agents; include "group" (e.g. PAH, HCA, Aromatic_Amine,
  Nitrosamine, Mycotoxin, Estrogen, Androgen, Solvent, Alkylating) and "iarc"
  classification (Group 1 / 2A / 2B / 3).
- Enzyme      — include "phase" (I, II, III, when applicable) and "role"
  (Activation, Detoxification, Mixed, Transport, Repair). For DNA repair
  proteins, use "role": "Repair" and store the repair class in "group"
  (for example "DNA Repair (BER)" or "DNA Repair (NER)") instead of using
  "phase": "Repair".
- Gene        — a gene locus (use when distinguishing the gene from its encoded enzyme,
  e.g. for pharmacogenomic variants or tissue expression context).
- Metabolite  — include "reactivity" (High, Intermediate, Low).
- DNA_Adduct  — DNA lesion types.
- Pathway     — biological pathways; use KEGG IDs when possible.
- Tissue      — anatomical tissue or organ where expression/metabolism occurs.

### Edge types (use exactly these strings for "type"):
- ACTIVATES     — enzyme activates a procarcinogen → reactive metabolite
- DETOXIFIES    — enzyme conjugates / inactivates a metabolite
- TRANSPORTS    — efflux transporter moves a conjugate out of the cell
- FORMS_ADDUCT  — reactive metabolite covalently modifies DNA
- REPAIRS       — DNA repair enzyme removes a lesion
- PATHWAY       — node belongs to a biological pathway
- EXPRESSED_IN  — gene or enzyme is expressed in a tissue
- INDUCES       — substance or exposure induces enzyme expression/activity
- INHIBITS      — substance or exposure inhibits enzyme expression/activity
- ENCODES       — gene encodes an enzyme

### JSON Schema:
{
  "nodes": [
    {
      "id": "<short_unique_id>",
      "label": "<display name>",
      "type": "<NodeType>",
      "detail": "<one-line description>",
      "group": "<carcinogen class or repair class, or null>",
      "iarc": "<IARC group or null>",
      "phase": "<enzyme phase or null>",
      "role": "<enzyme role or null>",
      "reactivity": "<metabolite reactivity or null>",
      "source_db": "<supporting database(s) such as NCBI Gene, GTEx, ClinPGx, CTD, IARC, or KEGG, or null>",
      "evidence": "<brief evidence note or null>",
      "pmid": "<PubMed ID or null>",
      "tissue": "<relevant tissue context or null>",
      "variant": "<star allele or variant name or null>",
      "phenotype": "<functional phenotype such as poor metabolizer or null>",
      "activity_score": "<numeric activity score or null>",
      "tier": "<gene panel tier: 1, 2, or null>"
    }
  ],
  "edges": [
    {
      "source": "<source node id>",
      "target": "<target node id>",
      "type": "<EdgeType>",
      "label": "<short description of the reaction>",
      "carcinogen": "<id of the parent carcinogen, if applicable, or null>",
      "source_db": "<supporting database(s) such as NCBI Gene, CTD, IARC, or KEGG, or null>",
      "evidence": "<brief evidence note or null>",
      "pmid": "<PubMed ID or null>",
      "tissue": "<relevant tissue context or null>"
    }
  ]
}

Guidelines:
- Generate concise, uppercase-safe IDs (e.g. "BaP", "CYP1A1", "BPDE_dG").
- Every edge's source and target MUST reference an id that exists in the nodes list.
- Include the full metabolic chain: activation → metabolite → adduct → repair.
- Also include detoxification / conjugation branches when mentioned.
- If the user mentions KEGG pathway IDs, include Pathway nodes.
- Add annotation fields only when supported by the text; otherwise return null.
- Use `source_db` to reflect database-style provenance such as NCBI Gene, GTEx, ClinPGx, CTD, IARC, and KEGG.
- Capture tissue specificity, pharmacogenomic variants, and metabolizer phenotype when the text provides them.
"""


def extract_graph(
    text: str,
    *,
    model: str = "gpt-4o",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> KnowledgeGraph:
    """Send *text* to the LLM and return a validated KnowledgeGraph."""
    try:
        from openai import OpenAI
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "The 'openai' package is required for LLM extraction. "
            "Install project dependencies with `pip install -e .` or "
            "`pip install openai`."
        ) from exc

    client = OpenAI(
        api_key=api_key or os.environ.get("OPENAI_API_KEY"),
        base_url=base_url or os.environ.get("OPENAI_BASE_URL"),
    )

    try:
        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            response_format=KnowledgeGraph,
        )
        kg = response.choices[0].message.parsed
        if kg is not None:
            return kg
    except Exception as exc:
        logger.warning("Structured output failed, falling back to JSON mode: %s", exc)

    # Fallback: regular completion with JSON mode
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
    )
    raw = json.loads(response.choices[0].message.content)
    return KnowledgeGraph(**raw)


EXAMPLE_INPUT = """\
Benzo[a]pyrene (BaP) is a Group 1 PAH carcinogen found in tobacco smoke.
CYP1A1 and CYP1B1 epoxidize BaP to BaP-7,8-epoxide (high reactivity).
EPHX1 hydrolyzes the epoxide to BaP-7,8-diol (intermediate reactivity).
A second epoxidation by CYP1A1 produces the ultimate carcinogen BPDE
(high reactivity), which forms BPDE-N2-dG DNA adducts repaired by
nucleotide excision repair enzymes XPC and ERCC2/XPD.
Detoxification is handled by GSTM1 and GSTP1, which conjugate BPDE
with glutathione to form BPDE-GSH (low reactivity), effluxed by ABCB1
and ABCC2. BaP also generates 8-oxo-dG via ROS, repaired by OGG1.
BaP maps to KEGG pathways 05204 (Chemical Carcinogenesis — DNA adducts)
and 00980 (Xenobiotic metabolism by CYP450).
"""
