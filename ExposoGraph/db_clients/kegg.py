"""KEGG REST API client for pathway and enzyme lookups.

Uses the public KEGG REST API (https://rest.kegg.jp/) to retrieve
pathway membership, enzyme annotations, and gene-pathway mappings.
No API key is required for the public endpoints.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_BASE_URL = "https://rest.kegg.jp"


@dataclass
class KEGGPathway:
    """Minimal representation of a KEGG pathway."""

    pathway_id: str
    name: str
    genes: list[str] = field(default_factory=list)


@dataclass
class KEGGGene:
    """Minimal representation of a KEGG gene entry."""

    gene_id: str
    symbol: str
    name: str = ""
    pathways: list[str] = field(default_factory=list)


class KEGGClient:
    """Lightweight client for the KEGG REST API.

    Parameters
    ----------
    base_url:
        Override the KEGG REST base URL (useful for testing).
    timeout:
        HTTP request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str = _BASE_URL,
        timeout: int = 30,
    ) -> None:
        try:
            import requests as _requests  # noqa: F401
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError(
                "The 'requests' package is required for KEGG lookups. "
                "Install with: pip install ExposoGraph[db]"
            ) from exc
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str) -> str:
        """Perform a GET request and return the response text."""
        import requests

        url = f"{self.base_url}/{path}"
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return str(resp.text)

    @staticmethod
    def _field_body(line: str) -> str:
        """Return the content area of a KEGG fixed-width record line."""
        return line[12:].strip() if len(line) > 12 else ""

    @staticmethod
    def _parse_pathway_gene(body: str) -> str | None:
        """Extract the gene symbol from a KEGG pathway GENE line."""
        if not body:
            return None
        parts = body.split(None, 2)
        if not parts:
            return None
        if parts[0].isdigit():
            return parts[1].rstrip(";") if len(parts) > 1 else None
        return parts[0].rstrip(";")

    def get_pathway(self, pathway_id: str) -> KEGGPathway:
        """Fetch pathway details including member genes.

        Parameters
        ----------
        pathway_id:
            KEGG pathway identifier, e.g. ``"hsa05204"`` or ``"path:hsa05204"``.
        """
        clean_id = pathway_id.replace("path:", "")
        text = self._get(f"get/{clean_id}")
        name = ""
        genes: list[str] = []
        in_gene_section = False

        for line in text.splitlines():
            if line.startswith("NAME"):
                name = self._field_body(line)
            elif line.startswith("GENE"):
                in_gene_section = True
                gene_symbol = self._parse_pathway_gene(self._field_body(line))
                if gene_symbol:
                    genes.append(gene_symbol)
            elif in_gene_section and line.startswith("            "):
                gene_symbol = self._parse_pathway_gene(self._field_body(line))
                if gene_symbol:
                    genes.append(gene_symbol)
            elif in_gene_section and not line.startswith(" "):
                in_gene_section = False

        return KEGGPathway(pathway_id=clean_id, name=name, genes=genes)

    def get_gene(self, gene_id: str) -> KEGGGene:
        """Fetch a KEGG gene entry.

        Parameters
        ----------
        gene_id:
            KEGG gene identifier, e.g. ``"hsa:1543"`` for CYP1A1.
        """
        text = self._get(f"get/{gene_id}")
        symbol = ""
        name = ""
        pathways: list[str] = []
        in_pathway_section = False

        for line in text.splitlines():
            if line.startswith("SYMBOL"):
                symbol = self._field_body(line)
            elif line.startswith("NAME"):
                name = self._field_body(line)
            elif line.startswith("PATHWAY"):
                in_pathway_section = True
                body = self._field_body(line)
                if body:
                    pathways.append(body.split(None, 1)[0])
            elif in_pathway_section and line.startswith("            "):
                body = self._field_body(line)
                if body:
                    pathways.append(body.split(None, 1)[0])
            elif in_pathway_section and not line.startswith(" "):
                in_pathway_section = False

        return KEGGGene(gene_id=gene_id, symbol=symbol, name=name, pathways=pathways)

    def find_genes(self, query: str, organism: str = "hsa") -> list[dict[str, str]]:
        """Search KEGG for genes matching a query string.

        Returns a list of ``{"gene_id": ..., "description": ...}`` dicts.
        """
        text = self._get(f"find/{organism}/{query}")
        results: list[dict[str, str]] = []
        for line in text.strip().splitlines():
            if not line.strip():
                continue
            parts = line.split("\t", 1)
            results.append({
                "gene_id": parts[0].strip(),
                "description": parts[1].strip() if len(parts) > 1 else "",
            })
        return results

    def list_pathway_genes(self, pathway_id: str) -> list[str]:
        """Return gene IDs belonging to a pathway via the ``/link`` endpoint.

        Parameters
        ----------
        pathway_id:
            KEGG pathway identifier, e.g. ``"hsa05204"``.
        """
        clean_id = pathway_id.replace("path:", "")
        text = self._get(f"link/genes/{clean_id}")
        genes: list[str] = []
        for line in text.strip().splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                genes.append(parts[1].strip())
        return genes
