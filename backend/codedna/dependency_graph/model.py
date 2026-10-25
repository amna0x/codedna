"""Data model of the code graph: nodes, typed edges and unresolved references.

Node IDs are stable strings derived from names and paths, so the same code
gets the same ID in every commit:

* ``package:<name>``      (``package:`` for the default package)
* ``file:<repo-relative path>``
* ``type:<declaration id>``   e.g. ``type:example.OrderService``
* ``member:<declaration id>`` e.g. ``member:example.OrderService#total()``

Declaration IDs are the ones the language plugin's change mapping produces
(Java: D-009), which lets method-level change reports point straight into the
graph.

Every edge carries a ``confidence``:

* ``confirmed`` — follows from the source text and Java's name-resolution
  rules for the cases we implement (e.g. an exact single-type import).
* ``heuristic`` — plausible but not proven (e.g. ``Foo.bar()`` where ``Foo``
  is assumed to be a class, not a variable).

References that could not be resolved are kept in ``unresolved`` and never
turned into edges.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

CONFIRMED = "confirmed"
HEURISTIC = "heuristic"

# Edge kinds that express "source depends on target" (used for impact).
DEPENDENCY_KINDS = frozenset({"extends", "implements", "uses", "imports", "static_access"})

MAX_EVIDENCE = 10


@dataclass
class Node:
    id: str
    kind: str  # package | file | class | interface | enum | record | annotation_type | method ...
    label: str
    file: str | None = None
    lines: list[int] | None = None  # [start, end] in the file
    package: str | None = None
    parent: str | None = None  # containing node ID
    role: str | None = None  # files/types: "test" or "main" (by path convention)
    has_syntax_errors: bool = False
    versions: list[str] = field(default_factory=list)  # "base"/"head" in a merged graph


@dataclass
class Evidence:
    file: str
    line: int
    confidence: str
    note: str = ""


@dataclass
class Edge:
    source: str
    target: str
    kind: str  # contains | extends | implements | uses | imports | static_access
    confidence: str
    evidence: list[Evidence] = field(default_factory=list)
    evidence_count: int = 0
    versions: list[str] = field(default_factory=list)

    def add_evidence(self, evidence: Evidence) -> None:
        self.evidence_count += 1
        if len(self.evidence) < MAX_EVIDENCE and evidence not in self.evidence:
            self.evidence.append(evidence)
        if evidence.confidence == CONFIRMED:
            self.confidence = CONFIRMED


@dataclass
class UnresolvedReference:
    source: str  # node ID of the referring type
    name: str  # the name as written
    file: str
    line: int
    reason: str
    count: int = 1


@dataclass
class CodeGraph:
    repository: str
    commit: str  # SHA, or "BASE..HEAD" for a merged graph
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: dict[tuple[str, str, str], Edge] = field(default_factory=dict)
    unresolved: dict[tuple[str, str], UnresolvedReference] = field(default_factory=dict)
    external_reference_count: int = 0
    warnings: list[str] = field(default_factory=list)

    def add_node(self, node: Node) -> Node:
        return self.nodes.setdefault(node.id, node)

    def add_edge(self, source: str, target: str, kind: str, evidence: Evidence | None = None,
                 confidence: str = CONFIRMED) -> Edge:
        key = (source, target, kind)
        edge = self.edges.get(key)
        if edge is None:
            initial = evidence.confidence if evidence else confidence
            edge = self.edges[key] = Edge(source, target, kind, initial)
        if evidence is not None:
            edge.add_evidence(evidence)
        return edge

    def add_unresolved(self, reference: UnresolvedReference) -> None:
        key = (reference.source, reference.name)
        existing = self.unresolved.get(key)
        if existing is None:
            self.unresolved[key] = reference
        else:
            existing.count += 1

    def dependency_edges(self) -> list[Edge]:
        return [edge for edge in self.edges.values() if edge.kind in DEPENDENCY_KINDS]

    def stats(self) -> dict:
        node_kinds: dict[str, int] = {}
        for node in self.nodes.values():
            node_kinds[node.kind] = node_kinds.get(node.kind, 0) + 1
        edge_kinds: dict[str, dict[str, int]] = {}
        for edge in self.edges.values():
            counts = edge_kinds.setdefault(edge.kind, {CONFIRMED: 0, HEURISTIC: 0})
            counts[edge.confidence] += 1
        dependency_refs = sum(edge.evidence_count for edge in self.dependency_edges())
        unresolved_refs = sum(ref.count for ref in self.unresolved.values())
        total = dependency_refs + unresolved_refs
        return {
            "nodes": dict(sorted(node_kinds.items())),
            "edges": dict(sorted(edge_kinds.items())),
            "resolved_references": dependency_refs,
            "unresolved_references": unresolved_refs,
            "external_references": self.external_reference_count,
            # Share of in-repository-candidate references we could not resolve.
            "unresolved_rate": round(unresolved_refs / total, 4) if total else 0.0,
        }

    def to_dict(self) -> dict:
        return {
            "repository": self.repository,
            "commit": self.commit,
            "stats": self.stats(),
            "nodes": [asdict(node) for node in sorted(self.nodes.values(), key=lambda n: n.id)],
            "edges": [
                asdict(edge)
                for edge in sorted(self.edges.values(), key=lambda e: (e.kind, e.source, e.target))
            ],
            "unresolved": [
                asdict(ref)
                for ref in sorted(self.unresolved.values(), key=lambda r: (r.source, r.name))
            ],
            "warnings": list(self.warnings),
        }


def merge_graphs(base: CodeGraph, head: CodeGraph) -> CodeGraph:
    """Union of two graphs; every node and edge records which versions contain it.

    Impact analysis uses the union so that relationships removed by the change
    (only in base) are still followed — a conservative choice for test
    selection.
    """
    merged = CodeGraph(base.repository, f"{base.commit}..{head.commit}")
    for version, graph in (("base", base), ("head", head)):
        for node in graph.nodes.values():
            # Head attributes win because head is processed last.
            versions = merged.nodes[node.id].versions if node.id in merged.nodes else []
            merged.nodes[node.id] = Node(**{**asdict(node), "versions": [*versions, version]})
        for key, edge in graph.edges.items():
            target = merged.edges.get(key)
            if target is None:
                target = merged.edges[key] = Edge(edge.source, edge.target, edge.kind,
                                                  edge.confidence)
            for evidence in edge.evidence:
                if len(target.evidence) < MAX_EVIDENCE and evidence not in target.evidence:
                    target.evidence.append(Evidence(**asdict(evidence)))
            # Unchanged files contribute the same references to both versions,
            # so take the larger count rather than the sum.
            target.evidence_count = max(target.evidence_count, edge.evidence_count)
            if edge.confidence == CONFIRMED:
                target.confidence = CONFIRMED
            target.versions.append(version)
        for key, ref in graph.unresolved.items():
            merged.unresolved.setdefault(key, ref)
        merged.warnings.extend(f"{version}: {warning}" for warning in graph.warnings)
    merged.external_reference_count = max(base.external_reference_count,
                                          head.external_reference_count)
    return merged
