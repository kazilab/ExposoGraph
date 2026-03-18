"""NetworkX-backed graph engine for building and querying the knowledge graph."""

from __future__ import annotations

import json
import logging
from typing import Any

import networkx as nx

from .models import Edge, KnowledgeGraph, Node

logger = logging.getLogger(__name__)


class GraphEngine:
    """Thin wrapper around a NetworkX MultiDiGraph that speaks our domain model."""

    def __init__(self) -> None:
        self.G: nx.MultiDiGraph = nx.MultiDiGraph()

    # ── Mutations ────────────────────────────────────────────────────────

    def add_node(self, node: Node) -> None:
        self.G.add_node(node.id, **node.model_dump(exclude_none=True, mode="json"))

    def add_edge(self, edge: Edge) -> None:
        if edge.source not in self.G:
            raise ValueError(f"Missing source node: {edge.source}")
        if edge.target not in self.G:
            raise ValueError(f"Missing target node: {edge.target}")
        if edge.carcinogen and edge.carcinogen not in self.G:
            raise ValueError(f"Missing carcinogen context node: {edge.carcinogen}")

        self.G.add_edge(
            edge.source,
            edge.target,
            key=f"{edge.source}-{edge.type.value}-{edge.target}",
            **edge.model_dump(exclude_none=True, mode="json"),
        )

    def remove_node(self, node_id: str) -> None:
        if node_id in self.G:
            self.G.remove_node(node_id)

    def remove_edge(self, source: str, target: str, key: str | None = None) -> None:
        if key is not None and self.G.has_edge(source, target, key):
            self.G.remove_edge(source, target, key)
        elif self.G.has_edge(source, target):
            self.G.remove_edge(source, target)

    # ── Bulk operations ──────────────────────────────────────────────────

    def load(self, kg: KnowledgeGraph) -> list[str]:
        """Load a KnowledgeGraph, skipping edges with missing node references.

        Returns a list of warning messages for any skipped edges.
        """
        warnings: list[str] = []
        for node in kg.nodes:
            self.add_node(node)
        for edge in kg.edges:
            try:
                self.add_edge(edge)
            except ValueError as exc:
                warnings.append(str(exc))
                logger.warning("Skipped edge during load: %s", exc)
        return warnings

    def merge(self, kg: KnowledgeGraph) -> list[str]:
        """Additive merge — new nodes/edges are added, existing ones updated.

        Returns a list of warning messages for any skipped edges.
        """
        warnings: list[str] = []
        for node in kg.nodes:
            self.add_node(node)
        for edge in kg.edges:
            try:
                self.add_edge(edge)
            except ValueError as exc:
                warnings.append(str(exc))
                logger.warning("Skipped edge during merge: %s", exc)
        return warnings

    def clear(self) -> None:
        self.G.clear()

    # ── Queries ──────────────────────────────────────────────────────────

    @property
    def node_count(self) -> int:
        return self.G.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self.G.number_of_edges()

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        if node_id in self.G:
            return dict(self.G.nodes[node_id])
        return None

    def neighbors(self, node_id: str) -> list[str]:
        if node_id not in self.G:
            return []
        return list(self.G.successors(node_id)) + list(self.G.predecessors(node_id))

    def nodes_by_type(self, node_type: str) -> list[dict[str, Any]]:
        return [
            data
            for _, data in self.G.nodes(data=True)
            if data.get("type") == node_type
        ]

    # ── Serialization ────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, list]:
        nodes = [dict(data) for _, data in self.G.nodes(data=True)]
        edges = [dict(data) for _, _, _, data in self.G.edges(keys=True, data=True)]
        return {"nodes": nodes, "edges": edges}

    def to_knowledge_graph(self) -> KnowledgeGraph:
        data = self.to_dict()
        return KnowledgeGraph(
            nodes=[Node(**n) for n in data["nodes"]],
            edges=[Edge(**e) for e in data["edges"]],
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    # ── Validation ───────────────────────────────────────────────────────

    def validate(self) -> list[str]:
        errors: list[str] = []
        node_ids = set(self.G.nodes)
        for u, v, data in self.G.edges(data=True):
            if u not in node_ids:
                errors.append(f"Edge references missing source node: {u}")
            if v not in node_ids:
                errors.append(f"Edge references missing target node: {v}")
            if data.get("carcinogen") and data["carcinogen"] not in node_ids:
                errors.append(
                    f"Edge '{u}→{v}' references carcinogen '{data['carcinogen']}' "
                    f"which is not in the graph"
                )
        return errors
