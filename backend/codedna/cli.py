"""Command-line interface for CodeDNA.

Usage:
    codedna analyze --repo PATH --base SHA --head SHA [--output FILE]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from codedna import __version__
from codedna.git_analysis import CodeDNAGitError, extract_changes

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
        help="List files changed between two commits as JSON.",
        description="List files changed between two commits as JSON (file-level analysis).",
    )
    analyze.add_argument("--repo", required=True, help="Path to a local Git repository.")
    analyze.add_argument("--base", required=True, help="Base commit (SHA, branch, tag, HEAD~1, ...).")
    analyze.add_argument("--head", required=True, help="Head/target commit to compare against base.")
    analyze.add_argument("--output", help="Write JSON to this file instead of standard output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "analyze":
        return _run_analyze(args)
    return EXIT_ANALYSIS_ERROR  # unreachable: subcommand is required


def _run_analyze(args: argparse.Namespace) -> int:
    try:
        report = extract_changes(args.repo, args.base, args.head)
    except CodeDNAGitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ANALYSIS_ERROR

    text = json.dumps(report.to_dict(), indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
