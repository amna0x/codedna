"""Shared code-graph schema: packages, files, types, members and typed edges.

Language plugins build graphs in this schema (D-018); the Java builder lives in
``codedna-java`` (D-054).
"""

from codedna.dependency_graph.cache import BoundedParseCache
from codedna.dependency_graph.model import (
    CONFIRMED,
    DEPENDENCY_KINDS,
    HEURISTIC,
    CodeGraph,
    Edge,
    Evidence,
    Node,
    UnresolvedReference,
    merge_graphs,
    union_graphs,
)

__all__ = [
    "CONFIRMED",
    "BoundedParseCache",
    "DEPENDENCY_KINDS",
    "HEURISTIC",
    "CodeGraph",
    "Edge",
    "Evidence",
    "Node",
    "UnresolvedReference",
    "merge_graphs",
    "union_graphs",
]
