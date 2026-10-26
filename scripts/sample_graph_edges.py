"""Sample dependency-graph edges for the manual precision check (M2).

Draws a seeded, stratified sample of non-``contains`` edges (equal numbers of
confirmed and heuristic edges where available) from ``codedna graph`` of one
commit, and writes a CSV a person labels:

* ``label``: ``correct`` (the evidence line in the source type really refers
  to the target type, by Java's name rules), ``incorrect`` (it refers to
  something else, e.g. a library type or a variable), or ``unclear``;
* ``note``: why, in a few words.

Each row carries one evidence ``file:line`` and that line's text, so it can
be checked against the source. ``scripts/score_graph_sample.py`` turns a
labelled file into precision per confidence label. No project code is run.

Usage (from the repository root):

    python scripts/sample_graph_edges.py REPO --rev REV --per-label 40 --out sample.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

from codedna_java.builder import build_graph
from codedna.git_analysis.git import resolve_commit, resolve_repository, run_git_bytes

FIELDS = ["row", "confidence", "kind", "source", "target", "evidence_file", "evidence_line",
          "evidence_note", "line_text", "evidence_count", "label", "note"]


def sample_edges(repo: Path, rev: str, per_label: int, seed: int) -> tuple[str, list[dict], dict]:
    commit = resolve_commit(repo, rev)
    graph = build_graph(repo, commit, include_members=False)
    edges = [e for e in graph.edges.values() if e.kind != "contains" and e.evidence]
    rng = random.Random(seed)
    picked = []
    for confidence in ("confirmed", "heuristic"):
        group = sorted((e for e in edges if e.confidence == confidence),
                       key=lambda e: (e.source, e.target, e.kind))
        picked += rng.sample(group, min(per_label, len(group)))
    lines: dict[str, list[str]] = {}
    rows = []
    for number, edge in enumerate(picked, 1):
        evidence = rng.choice(edge.evidence)
        if evidence.file not in lines:
            text = run_git_bytes(repo, "show", f"{commit}:{evidence.file}")
            lines[evidence.file] = text.decode("utf-8", "replace").splitlines()
        source_lines = lines[evidence.file]
        line = source_lines[evidence.line - 1].strip() if 0 < evidence.line <= len(source_lines) else ""
        rows.append({"row": number, "confidence": edge.confidence, "kind": edge.kind,
                     "source": edge.source, "target": edge.target,
                     "evidence_file": evidence.file, "evidence_line": evidence.line,
                     "evidence_note": evidence.note, "line_text": line,
                     "evidence_count": edge.evidence_count, "label": "", "note": ""})
    population = {c: sum(e.confidence == c for e in edges) for c in ("confirmed", "heuristic")}
    return commit, rows, population


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", type=Path)
    parser.add_argument("--rev", default="HEAD")
    parser.add_argument("--per-label", type=int, default=40)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"{args.out} exists; labels are never overwritten")
    repo = resolve_repository(args.repo)
    commit, rows, population = sample_edges(repo, args.rev, args.per_label, args.seed)
    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"commit {commit}; edges in graph (non-contains): {population}; "
          f"sampled {len(rows)} with seed {args.seed} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
