"""Command-line interface for CodeDNA.

Usage:
    codedna analyze --repo PATH --base SHA --head SHA [--level file|method] [--output FILE]
    codedna graph   --repo PATH [--rev REV] [--no-members] [--output FILE]
    codedna impact  --repo PATH --base SHA --head SHA [--max-depth N] [--confirmed-only]
                    [--output FILE]
    codedna tests   --repo PATH [--rev REV] [--output FILE]
    codedna run-tests --repo PATH [--rev REV] --output-dir DIR --allow-build
                    [--per-test-coverage] [--mvn PATH] [--timeout SECONDS] [--keep-checkout]
    codedna select  --repo PATH --base SHA --head SHA --strategy all|dependency|coverage
                    [--coverage-map FILE] [--durations FILE] [--non-java retest-all|ignore]
    codedna compare --repo PATH --base SHA --head SHA --ground-truth FILE
                    [--coverage-map FILE] [--non-java retest-all|ignore]
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
from codedna.selection import STRATEGIES, SelectionError, compare_strategies, select_tests
from codedna.test_mapping.discovery import discover_tests
from codedna.test_mapping.maven import run_maven_tests
from codedna.test_mapping.reports import ReportError
from codedna.test_mapping.results import (
    COVERAGE_MAP_FILE,
    RESULTS_FILE,
    load_coverage_map,
    load_results,
)

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

    tests = subcommands.add_parser(
        "tests",
        help="List JUnit test classes of one commit (static discovery, nothing is run).",
    )
    tests.add_argument("--repo", required=True, help="Path to a local Git repository.")
    tests.add_argument("--rev", default="HEAD", help="Commit to analyse (default: HEAD).")
    tests.add_argument("--output", help="Write JSON to this file instead of standard output.")

    run_tests = subcommands.add_parser(
        "run-tests",
        help="Run the Maven test suite of one commit (executes project code; needs --allow-build).",
        description=(
            "Export the commit into OUTPUT_DIR/checkout with git archive, run 'mvn test' there and "
            "save results.json. With --per-test-coverage, run each test class separately under "
            "JaCoCo and also save coverage-map.json. This EXECUTES the project's code and build "
            "plugins, and Maven may download dependencies: only use it on projects you trust."
        ),
    )
    run_tests.add_argument("--repo", required=True, help="Path to a local Git repository.")
    run_tests.add_argument("--rev", default="HEAD", help="Commit to test (default: HEAD).")
    run_tests.add_argument("--output-dir", required=True,
                           help="New or empty directory for the checkout, logs and results.")
    run_tests.add_argument("--allow-build", action="store_true",
                           help="Confirm that the project's code and build may be executed.")
    run_tests.add_argument("--per-test-coverage", action="store_true",
                           help="Run each test class separately with JaCoCo (slow).")
    run_tests.add_argument("--mvn", help="Path to the Maven executable (default: mvn on PATH).")
    run_tests.add_argument("--timeout", type=_non_negative_int, default=1800,
                           help="Timeout per Maven invocation in seconds (default: 1800).")
    run_tests.add_argument("--keep-checkout", action="store_true",
                           help="Keep OUTPUT_DIR/checkout after the run (for debugging).")

    select = subcommands.add_parser(
        "select", help="Select regression tests for a change with a baseline strategy.")
    _add_change_args(select)
    select.add_argument("--strategy", choices=STRATEGIES, required=True,
                        help="all = retest-all (B0); dependency = static graph (B4); "
                             "coverage = JaCoCo coverage recorded at BASE.")
    select.add_argument("--coverage-map",
                        help="coverage-map.json (or its run directory) recorded at BASE.")
    select.add_argument("--durations",
                        help="results.json (or its run directory) used to estimate test time.")
    _add_non_java_arg(select)
    select.add_argument("--output", help="Write JSON to this file instead of standard output.")

    compare = subcommands.add_parser(
        "compare",
        help="Compare selection strategies against a full-suite run of HEAD.")
    _add_change_args(compare)
    compare.add_argument("--ground-truth", required=True,
                         help="results.json (or its run directory) of a full run of HEAD.")
    compare.add_argument("--coverage-map",
                         help="coverage-map.json (or its run directory) recorded at BASE.")
    _add_non_java_arg(compare)
    compare.add_argument("--output", help="Write JSON to this file instead of standard output.")
    return parser


def _add_change_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", required=True, help="Path to a local Git repository.")
    parser.add_argument("--base", required=True, help="Base commit (SHA, branch, tag, HEAD~1, ...).")
    parser.add_argument("--head", required=True, help="Head/target commit to compare against base.")


def _add_non_java_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--non-java", choices=("retest-all", "ignore"), default="retest-all",
                        help="What to do when non-Java files changed (default: retest-all).")


def _json_file(path: str | None, default_name: str) -> Path | None:
    """Accept either a JSON file or the run directory that contains it."""
    if path is None:
        return None
    candidate = Path(path)
    return candidate / default_name if candidate.is_dir() else candidate


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
        elif args.command == "impact":
            report = compute_impact(args.repo, args.base, args.head, max_depth=args.max_depth,
                                    include_heuristic=not args.confirmed_only)
        elif args.command == "tests":
            report = discover_tests(args.repo, args.rev)
        elif args.command == "run-tests":
            return _run_tests(args)
        elif args.command == "select":
            coverage = _json_file(args.coverage_map, COVERAGE_MAP_FILE)
            durations = _json_file(args.durations, RESULTS_FILE)
            report = select_tests(
                args.repo, args.base, args.head, args.strategy,
                coverage_map=load_coverage_map(coverage) if coverage else None,
                durations=load_results(durations) if durations else None,
                non_java=args.non_java)
        else:
            coverage = _json_file(args.coverage_map, COVERAGE_MAP_FILE)
            return _write_json(compare_strategies(
                args.repo, args.base, args.head,
                load_results(_json_file(args.ground_truth, RESULTS_FILE)),
                coverage_map=load_coverage_map(coverage) if coverage else None,
                non_java=args.non_java), args.output)
    except (CodeDNAGitError, SelectionError, ReportError, OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ANALYSIS_ERROR
    return _write_json(report.to_dict(), args.output)


def _run_tests(args: argparse.Namespace) -> int:
    if not args.allow_build:
        print("error: run-tests executes the project's code and build plugins; "
              "re-run with --allow-build if you trust this project", file=sys.stderr)
        return EXIT_ANALYSIS_ERROR
    print(f"warning: running the Maven build of {args.repo} (project code will execute)",
          file=sys.stderr)
    run, coverage = run_maven_tests(
        args.repo, args.rev, args.output_dir, allow_build=True,
        per_test_coverage=args.per_test_coverage,
        maven_command=[args.mvn] if args.mvn else None, timeout=args.timeout,
        keep_checkout=args.keep_checkout)
    summary = {
        "results": str(Path(args.output_dir) / RESULTS_FILE),
        "coverage_map": str(Path(args.output_dir) / COVERAGE_MAP_FILE) if coverage else None,
        "commit": run.commit,
        "test_classes": len(run.tests),
        "failing_tests": run.failing_tests,
        "duration_seconds": run.duration_seconds,
        "warnings": run.warnings,
    }
    return _write_json(summary, None)


def _write_json(data: dict, output: str | None) -> int:
    text = json.dumps(data, indent=2)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
