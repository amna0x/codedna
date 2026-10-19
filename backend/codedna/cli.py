"""Command-line interface for CodeDNA.

Usage:
    codedna analyze --repo PATH --base SHA --head SHA [--level file|method] [--output FILE]
    codedna graph   --repo PATH [--rev REV] [--no-members] [--output FILE]
    codedna impact  --repo PATH --base SHA --head SHA [--max-depth N] [--confirmed-only]
                    [--output FILE]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from codedna import __version__
from codedna.dependency_graph import build_graph
from codedna.git_analysis import CodeDNAGitError, extract_changes
from codedna.impact_analysis import compute_impact
from codedna.java_analysis import analyze_changes

EXIT_OK = 0
EXIT_ANALYSIS_ERROR = 1
# argparse itself exits with 2 on invalid command-line usage.


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codedna",
        description="Change-impact analysis and regression test selection for Java projects.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subcommands = parser.add_subparsers(dest="command", required=True)

    analyze = subcommands.add_parser(
        "analyze",
        help="Describe changes between two commits as JSON.",
        description=(
            "Describe changes between two commits as JSON: changed files and line ranges, "
            "plus the Java classes, methods, constructors and fields they touch."
        ),
    )
    analyze.add_argument("--repo", required=True, help="Path to a local Git repository.")
    analyze.add_argument("--base", required=True, help="Base commit (SHA, branch, tag, HEAD~1, ...).")
    analyze.add_argument("--head", required=True, help="Head/target commit to compare against base.")
    analyze.add_argument(
        "--level", choices=("file", "method"), default="method",
        help="'method' (default) maps Java changes to declarations; 'file' skips parsing.",
    )
    analyze.add_argument("--output", help="Write JSON to this file instead of standard output.")

    graph = subcommands.add_parser(
        "graph",
        help="Export the code dependency graph of one commit as JSON.",
        description=(
            "Export packages, files, types and members of one commit with typed edges "
            "(contains, extends, implements, uses, imports, static_access). Every dependency "
            "edge is labelled 'confirmed' or 'heuristic'; unresolved names are listed separately."
        ),
    )
    graph.add_argument("--repo", required=True, help="Path to a local Git repository.")
    graph.add_argument("--rev", default="HEAD", help="Commit to analyse (default: HEAD).")
    graph.add_argument("--no-members", action="store_true",
                       help="Leave out method/constructor/field nodes (smaller output).")
    graph.add_argument("--output", help="Write JSON to this file instead of standard output.")

    impact = subcommands.add_parser(
        "impact",
        help="List types potentially impacted by changes between two commits.",
        description=(
            "Map changes to declarations, then follow dependency edges backwards to find types "
            "that may be affected, each with an explanation path."
        ),
    )
    impact.add_argument("--repo", required=True, help="Path to a local Git repository.")
    impact.add_argument("--base", required=True, help="Base commit (SHA, branch, tag, HEAD~1, ...).")
    impact.add_argument("--head", required=True, help="Head/target commit to compare against base.")
    impact.add_argument("--max-depth", type=_non_negative_int, default=None,
                        help="Stop after this many dependency hops (default: no limit).")
    impact.add_argument("--confirmed-only", action="store_true",
                        help="Follow only confirmed edges, not heuristic ones.")
    impact.add_argument("--output", help="Write JSON to this file instead of standard output.")
    return parser


def _non_negative_int(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be 0 or greater")
    return number


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.command == "analyze":
            if args.level == "file":
                report = extract_changes(args.repo, args.base, args.head)
            else:
                report = analyze_changes(args.repo, args.base, args.head)
        elif args.command == "graph":
            report = build_graph(args.repo, args.rev, include_members=not args.no_members)
        else:
            report = compute_impact(args.repo, args.base, args.head, max_depth=args.max_depth,
                                    include_heuristic=not args.confirmed_only)
    except CodeDNAGitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ANALYSIS_ERROR
    return _write_json(report.to_dict(), args.output)


def _write_json(data: dict, output: str | None) -> int:
    text = json.dumps(data, indent=2)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
