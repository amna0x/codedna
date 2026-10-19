"""Code graph of a Java repository: packages, files, types, members and typed edges."""

from codedna.dependency_graph.builder import build_graph, build_graph_for_commit, file_role
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
)

__all__ = [
    "CONFIRMED",
    "DEPENDENCY_KINDS",
    "HEURISTIC",
    "CodeGraph",
    "Edge",
    "Evidence",
    "Node",
    "UnresolvedReference",
    "build_graph",
    "build_graph_for_commit",
    "file_role",
    "merge_graphs",
]
