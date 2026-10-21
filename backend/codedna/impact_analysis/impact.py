"""Change-impact analysis: which types may be affected by a change?

1. ``analyze_changes`` maps the diff to changed Java declarations.
2. Every changed declaration becomes a *seed*: the type itself, or the type
   that owns a changed member. Comment/formatting-only changes are ignored.
3. The code graphs of BASE and HEAD are built and merged (so dependencies
   removed by the change are still followed).
4. A breadth-first search walks dependency edges *backwards* (from a type to
   the types that depend on it). Confirmed edges are explored first; only
   types not reachable through confirmed edges are then reached through
   heuristic ones. Every impacted type gets the shortest explanation path.

The result is a list of *potentially* impacted types, not a proof that they
behave differently.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path

from codedna.dependency_graph import (
    CONFIRMED,
    HEURISTIC,
    CodeGraph,
    Edge,
    merge_graphs,
)
from codedna.java_analysis import analyze_changes
from codedna.java_analysis.parser import TYPE_NODES
from codedna.plugins import load_plugins

_TYPE_KINDS = frozenset(TYPE_NODES.values())


@dataclass
class Seed:
    node: str
    file: str | None
    in_head: bool  # False for types deleted by the change
    reasons: list[str] = field(default_factory=list)


@dataclass
class PathStep:
    dependent: str
    depends_on: str
    kind: str
    confidence: str
    evidence: str  # "path:line" of the first piece of evidence


@dataclass
class ImpactedNode:
    node: str
    kind: str
    file: str | None
    role: str | None
    distance: int
    confidence: str  # "confirmed" only if every edge on the path is confirmed
    seed: str
    path: list[PathStep]


@dataclass
class ImpactReport:
    repository: str
    base_commit: str
    head_commit: str
    max_depth: int | None
    include_heuristic: bool
    seeds: list[Seed]
    impacted: list[ImpactedNode]
    impacted_files: list[dict]
    candidate_tests: list[dict]
    ignored_changes: list[dict]
    unanalysed_changes: list[dict]
    graph_stats: dict
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def compute_impact(repo_path: str | Path, base: str, head: str, *,
                   max_depth: int | None = None, include_heuristic: bool = True,
                   cache: dict | None = None) -> ImpactReport:
    changes = analyze_changes(repo_path, base, head)
    repo = Path(changes.repository)
    cache = {} if cache is None else cache  # parses keyed by blob SHA (may be shared)
    java = load_plugins().get("java")  # only language analysed so far (D-013)
    graph = merge_graphs(
        java.build_graph(repo, changes.base_commit, cache=cache),
        java.build_graph(repo, changes.head_commit, cache=cache),
    )

    seeds, ignored, unanalysed = _collect_seeds(changes, graph)
    warnings = list(changes.warnings) + list(graph.warnings)
    if unanalysed:
        warnings.append(
            f"{len(unanalysed)} changed non-Java file(s) not analysed; their impact is unknown "
            "and a broader test run may be needed")

    impacted = _traverse(graph, seeds, max_depth, include_heuristic)
    return ImpactReport(
        repository=changes.repository,
        base_commit=changes.base_commit,
        head_commit=changes.head_commit,
        max_depth=max_depth,
        include_heuristic=include_heuristic,
        seeds=sorted(seeds.values(), key=lambda s: s.node),
        impacted=impacted,
        impacted_files=_impacted_files(graph, seeds, impacted),
        candidate_tests=_candidate_tests(graph, seeds, impacted),
        ignored_changes=ignored,
        unanalysed_changes=unanalysed,
        graph_stats=graph.stats(),
        warnings=warnings,
    )


def _collect_seeds(changes, graph: CodeGraph) -> tuple[dict[str, Seed], list[dict], list[dict]]:
    seeds: dict[str, Seed] = {}
    ignored: list[dict] = []
    unanalysed: list[dict] = []

    def add(type_id: str, reason: str) -> None:
        node_id = f"type:{type_id}"
        node = graph.nodes.get(node_id)
        seed = seeds.setdefault(node_id, Seed(
            node_id, node.file if node else None, bool(node and "head" in node.versions)))
        if reason not in seed.reasons:
            seed.reasons.append(reason)

    for changed in changes.changed_files:
        if not changed.is_java:
            unanalysed.append({"path": changed.path, "status": changed.status,
                               "reason": "non-Java file; impact not analysed"})
            continue
        paths = {changed.path, changed.old_path} - {None}
        file_types = [n for n in graph.nodes.values() if n.kind in _TYPE_KINDS and n.file in paths]
        all_types = [n.id.removeprefix("type:") for n in file_types]
        top_types = [n.id.removeprefix("type:") for n in file_types
                     if n.parent and n.parent.startswith("file:")]
        java = changed.java
        if java is None:
            for type_id in all_types:
                add(type_id, f"file {changed.status} (declarations not mapped)")
            continue

        for declaration in java.declarations:
            if declaration.code_changed is False:
                ignored.append({"id": declaration.id, "file": changed.path,
                                "reason": "only comments or formatting changed"})
                continue
            owner = declaration.id if declaration.kind in _TYPE_KINDS else declaration.parent
            if owner is not None:
                add(owner, f"{declaration.kind} {declaration.id} {declaration.change}")
        for outside in java.outside_declarations:
            if outside.code_changed is False:
                ignored.append({"id": f"file:{changed.path}", "file": changed.path,
                                "reason": f"only comments or formatting changed ({outside.side} "
                                          f"lines {outside.lines})"})
                continue
            # Imports/package affect every top-level type of the file.
            for type_id in top_types:
                add(type_id, f"{'/'.join(outside.parts)} changed in {changed.path}")
        for unresolved in java.unresolved:
            for type_id in all_types:
                add(type_id, f"unresolved change ({unresolved.reason}); whole file treated as changed")
    return seeds, ignored, unanalysed


def _traverse(graph: CodeGraph, seeds: dict[str, Seed], max_depth: int | None,
              include_heuristic: bool) -> list[ImpactedNode]:
    dependents: dict[str, list[Edge]] = {}
    for edge in graph.dependency_edges():
        dependents.setdefault(edge.target, []).append(edge)

    found: dict[str, ImpactedNode] = {}
    passes = [{CONFIRMED}] + ([{CONFIRMED, HEURISTIC}] if include_heuristic else [])
    for allowed in passes:
        # BFS from all seeds at once; parent[n] = (previous node, edge used).
        parent: dict[str, tuple[str, Edge] | None] = {seed: None for seed in seeds}
        queue = deque((seed, 0) for seed in seeds)
        while queue:
            current, distance = queue.popleft()
            if max_depth is not None and distance >= max_depth:
                continue
            for edge in sorted(dependents.get(current, ()), key=lambda e: (e.source, e.kind)):
                if edge.confidence not in allowed or edge.source in parent:
                    continue
                parent[edge.source] = (current, edge)
                queue.append((edge.source, distance + 1))
                if edge.source not in found:
                    found[edge.source] = _impacted(graph, edge.source, parent, distance + 1)
    return sorted(found.values(), key=lambda n: (n.distance, n.node))


def _impacted(graph: CodeGraph, node_id: str, parent: dict, distance: int) -> ImpactedNode:
    steps: list[PathStep] = []
    current = node_id
    while parent[current] is not None:
        previous, edge = parent[current]
        first = edge.evidence[0] if edge.evidence else None
        steps.append(PathStep(edge.source, edge.target, edge.kind, edge.confidence,
                              f"{first.file}:{first.line}" if first else ""))
        current = previous
    # Steps read from the impacted type towards the seed: "A uses B", "B uses C".
    node = graph.nodes.get(node_id)
    confidence = CONFIRMED if all(s.confidence == CONFIRMED for s in steps) else HEURISTIC
    return ImpactedNode(
        node=node_id, kind=node.kind if node else "unknown", file=node.file if node else None,
        role=node.role if node else None, distance=distance, confidence=confidence,
        seed=current, path=steps,
    )


def _impacted_files(graph: CodeGraph, seeds: dict[str, Seed],
                    impacted: list[ImpactedNode]) -> list[dict]:
    files: dict[str, dict] = {}
    for seed in seeds.values():
        if seed.file:
            files[seed.file] = {"path": seed.file, "reason": "changed",
                                "role": graph.nodes[seed.node].role if seed.node in graph.nodes
                                else None}
    for node in impacted:
        if node.file and node.file not in files:
            files[node.file] = {"path": node.file, "reason": "impacted", "role": node.role,
                                "confidence": node.confidence}
    return sorted(files.values(), key=lambda f: f["path"])


def _candidate_tests(graph: CodeGraph, seeds: dict[str, Seed],
                     impacted: list[ImpactedNode]) -> list[dict]:
    """Top-level test classes among the changed/impacted types that still exist in HEAD.

    Dependency-only selection (baseline B4) at class level; tests are recognised
    by path convention only (see ``file_role``).
    """

    def is_runnable_test(node_id: str) -> bool:
        node = graph.nodes.get(node_id)
        return (node is not None and node.role == "test" and "head" in node.versions
                and bool(node.parent) and node.parent.startswith("file:"))

    tests = []
    for seed in seeds.values():
        if is_runnable_test(seed.node):
            tests.append({"type": seed.node, "file": seed.file, "reason": "test class changed",
                          "confidence": CONFIRMED})
    for item in impacted:
        if is_runnable_test(item.node):
            tests.append({"type": item.node, "file": item.file,
                          "reason": f"depends on changed {item.seed} (distance {item.distance})",
                          "confidence": item.confidence})
    return sorted(tests, key=lambda t: t["type"])
