"""Command-line interface for CodeDNA.

Usage:
    codedna analyze --repo PATH --base SHA --head SHA [--level file|method] [--output FILE]
    codedna graph   --repo PATH [--rev REV] [--no-members] [--output FILE]
    codedna impact  --repo PATH --base SHA --head SHA [--max-depth N] [--confirmed-only]
                    [--output FILE]
    codedna tests   --repo PATH [--rev REV] [--output FILE]
    codedna run-tests --repo PATH [--rev REV] --output-dir DIR --allow-build
                    [--per-test-coverage] [--mvn PATH] [--gradle PATH] [--timeout SECONDS] [--keep-checkout]
    codedna select  --repo PATH --base SHA --head SHA --strategy all|dependency|coverage
                    [--coverage-map FILE] [--durations FILE] [--non-java retest-all|ignore]
    codedna risk-select --repo PATH --base SHA --head SHA [--history-csv FILE] [--risk-target F]
    codedna compare --repo PATH --base SHA --head SHA --ground-truth FILE
                    [--coverage-map FILE] [--non-java retest-all|ignore]
    codedna plugins
    codedna serve   [--host 127.0.0.1] [--port 8765] [--allow-build]
    codedna history mine     --repo PATH --db FILE [--rev REV] [--max-commits N]
    codedna history import   --db FILE RESULTS [RESULTS ...] [--source NAME]
    codedna history collect  --repo PATH --db FILE --output-dir DIR --allow-build
                             [--max-commits N] [--mvn PATH] [--timeout SECONDS]
    codedna history status   --db FILE
    codedna history import-rtptorrent --dataset DIR (--project NAME --db FILE | --list)
                             [--max-commits N]
    codedna history evaluate --db FILE [--repo PATH] [--rankers NAME ...]
                             [--no-structural] [--dataset-csv FILE] [--seed N] [--output FILE]
    codedna history experiment --db FILE [--repo PATH] [--model NAME] [--calibration METHOD]
                             [--budget F] [--risk-target F] [--no-structural] [--no-sweeps]
                             [--no-ablations] [--seed N] [--output FILE]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from codedna import __version__
from codedna.dependency_graph import build_graph
from codedna.git_analysis import CodeDNAGitError, extract_changes
from codedna.impact_analysis import compute_impact
from codedna.java_analysis import analyze_changes
from codedna.models.rankers import BASELINES, ML_MODELS
from codedna.plugins import load_plugins
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
        help="Run the Maven or Gradle test suite of one commit (executes project code; needs --allow-build).",
        description=(
            "Export the commit into OUTPUT_DIR/checkout with git archive, run 'mvn test' there and "
            "save results.json (Gradle projects: 'gradle test'). With --per-test-coverage, run each test class separately under "
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
    run_tests.add_argument("--gradle",
                           help="Path to the Gradle executable (default: gradle on PATH; "
                                "the repository's gradlew is never used).")
    run_tests.add_argument("--timeout", type=_non_negative_int, default=1800,
                           help="Timeout per build invocation in seconds (default: 1800).")
    run_tests.add_argument("--keep-checkout", action="store_true",
                           help="Keep OUTPUT_DIR/checkout after the run (for debugging).")

    run_tests.add_argument('--tests', nargs='*', default=None,
                           help='Only run these discovered test classes; empty list runs nothing.')
    risk_select = subcommands.add_parser('risk-select', help='Target-validated calibrated stopping or full-suite fallback.')
    _add_change_args(risk_select)
    risk_select.add_argument('--history-csv', help='Target history CSV; default REPO/.codedna/history.csv')
    risk_select.add_argument('--risk-target', type=float, default=.05)

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

    subcommands.add_parser("plugins", help="List installed language plugins.")

    serve = subcommands.add_parser(
        "serve",
        help="Start the local API for the CodeDNA IDE (loopback only).",
        description=(
            "Start the local HTTP API. Prints one JSON line with the URL and the session token "
            "(taken from CODEDNA_API_TOKEN if set). Requests need the X-CodeDNA-Token header. "
            "Needs the [api] extra."
        ),
    )
    serve.add_argument("--host", default="127.0.0.1",
                       help="Loopback address to listen on (default: 127.0.0.1).")
    serve.add_argument("--port", type=_non_negative_int, default=8765,
                       help="Port (default: 8765).")
    serve.add_argument("--allow-build", action="store_true",
                       help="Allow /api/run-tests (executes project code on request).")

    history = subcommands.add_parser(
        "history", help="Mine commit history, store test results, evaluate test ordering.")
    history_commands = history.add_subparsers(dest="history_command", required=True)

    mine = history_commands.add_parser("mine", help="Store the first-parent commit history.")
    mine.add_argument("--repo", required=True, help="Path to a local Git repository.")
    mine.add_argument("--db", required=True, help="SQLite history database (created if missing).")
    mine.add_argument("--rev", default="HEAD", help="Newest commit to mine (default: HEAD).")
    mine.add_argument("--max-commits", type=_non_negative_int,
                      help="Only the most recent N first-parent commits.")

    import_ = history_commands.add_parser("import", help="Store results.json files.")
    import_.add_argument("--db", required=True, help="SQLite history database.")
    import_.add_argument("results", nargs="+", help="results.json files or run directories.")
    import_.add_argument("--source", default="import", help="Label for where results came from.")

    collect = history_commands.add_parser(
        "collect",
        help="Run the full suite of every mined commit without results (needs --allow-build).",
        description="Runs each commit's Maven build: this EXECUTES project code, once per "
                    "commit, and may take hours. Only use it on projects you trust.")
    collect.add_argument("--repo", required=True, help="Path to a local Git repository.")
    collect.add_argument("--db", required=True, help="SQLite history database.")
    collect.add_argument("--output-dir", required=True, help="Directory for per-commit runs.")
    collect.add_argument("--allow-build", action="store_true",
                         help="Confirm that the project's code and build may be executed.")
    collect.add_argument("--max-commits", type=_non_negative_int,
                         help="Collect at most N commits in this invocation.")
    collect.add_argument("--mvn", help="Path to the Maven executable (default: mvn on PATH).")
    collect.add_argument("--timeout", type=_non_negative_int, default=1800,
                         help="Timeout per build invocation in seconds (default: 1800).")

    rtp = history_commands.add_parser(
        "import-rtptorrent",
        help="Import one RTPTorrent project (real CI test results; nothing is built).",
        description="Read an extracted RTPTorrent v1.1 folder (Mattis et al., MSR 2020, CC BY 4.0) "
                    "and store one project's tested commits, changed files and per-job test-class "
                    "results in a history database.")
    rtp.add_argument("--dataset", required=True,
                     help="The extracted rtp-torrent folder (or its parent).")
    rtp.add_argument("--project", help="Project folder name, e.g. brettwooldridge@HikariCP.")
    rtp.add_argument("--db", help="SQLite history database to create or replace.")
    rtp.add_argument("--max-commits", type=_non_negative_int,
                     help="Keep only the most recent N tested commits.")
    rtp.add_argument("--list", action="store_true", help="List the projects in the dataset.")

    status = history_commands.add_parser("status", help="Summarise a history database.")
    status.add_argument("--db", required=True, help="SQLite history database.")

    evaluate = history_commands.add_parser(
        "evaluate", help="Build features and compare orderings on a chronological split.")
    evaluate.add_argument("--db", help="SQLite history database (or use --from-dataset).")
    evaluate.add_argument("--from-dataset", help="Reuse a dataset CSV written by --dataset-csv "
                                                 "instead of rebuilding features.")
    evaluate.add_argument("--repo", help="Repository path (default: the one recorded by mine).")
    evaluate.add_argument("--rankers", nargs="+", choices=BASELINES + ML_MODELS,
                          help="Rankers to evaluate (default: all).")
    evaluate.add_argument("--no-structural", action="store_true",
                          help="Skip graph-based features (much faster).")
    evaluate.add_argument("--dataset-csv", help="Also write the feature dataset to this CSV file.")
    evaluate.add_argument("--seed", type=int, default=0, help="Random seed (default: 0).")
    evaluate.add_argument("--output", help="Write JSON to this file instead of standard output.")

    experiment = history_commands.add_parser(
        "experiment",
        help="Calibration, risk-aware selection and fallback experiment (Milestone 5).",
        description="Train on the oldest 60%% of commits, calibrate on the next 20%%, and "
                    "compare policies B0, B4, B6-B9 on the latest 20%%.")
    experiment.add_argument("--db", help="SQLite history database (or use --from-dataset).")
    experiment.add_argument("--from-dataset", help="Reuse a dataset CSV written by "
                                                   "'history evaluate --dataset-csv'.")
    experiment.add_argument("--repo", help="Repository path (default: the one recorded by mine).")
    experiment.add_argument("--model", choices=ML_MODELS, default="gradient_boosting",
                            help="Failure model (default: gradient_boosting).")
    experiment.add_argument("--calibration", choices=("none", "platt", "isotonic"),
                            default="isotonic", help="Calibration for B8/B9 (default: isotonic).")
    experiment.add_argument("--budget", type=_fraction, default=0.5,
                            help="Time budget as a fraction of estimated total (default: 0.5).")
    experiment.add_argument("--risk-target", type=_fraction, default=0.05,
                            help="Max estimated skip risk for B9 (default: 0.05).")
    experiment.add_argument("--no-structural", action="store_true",
                            help="Skip graph-based features (faster; B4 not evaluated).")
    experiment.add_argument("--no-sweeps", action="store_true", help="Skip risk-coverage sweeps.")
    experiment.add_argument("--no-ablations", action="store_true", help="Skip feature ablations.")
    experiment.add_argument("--seed", type=int, default=0, help="Random seed (default: 0).")
    experiment.add_argument("--output", help="Write JSON to this file instead of standard output.")
    return parser


def _fraction(value: str) -> float:
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return number


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
        elif args.command == 'risk-select':
            from codedna.selection.live import recommend
            return _write_json(recommend(args.repo,args.base,args.head,
                history_csv=args.history_csv,risk_target=args.risk_target),None)
        elif args.command == "run-tests":
            return _run_tests(args)
        elif args.command == "plugins":
            return _write_json(load_plugins().describe(), None)
        elif args.command == "serve":
            try:
                from codedna.api.server import serve
            except ImportError:
                print('error: the API needs extra packages: pip install -e ".[api]"',
                      file=sys.stderr)
                return EXIT_ANALYSIS_ERROR
            return serve(args.host, args.port, token=os.environ.get("CODEDNA_API_TOKEN"),
                         allow_build=args.allow_build)
        elif args.command == "history":
            return _run_history(args)
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
    except (CodeDNAGitError, SelectionError, ReportError, OSError, ValueError, KeyError,
            RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ANALYSIS_ERROR
    return _write_json(report.to_dict(), args.output)


def _run_tests(args: argparse.Namespace) -> int:
    if not args.allow_build:
        print("error: run-tests executes the project's code and build plugins; "
              "re-run with --allow-build if you trust this project", file=sys.stderr)
        return EXIT_ANALYSIS_ERROR
    print(f"warning: running the build of {args.repo} (project code will execute)",
          file=sys.stderr)
    run, coverage = run_maven_tests(
        args.repo, args.rev, args.output_dir, allow_build=True,
        per_test_coverage=args.per_test_coverage,
        maven_command=[args.mvn] if args.mvn else None,
        gradle_command=[args.gradle] if args.gradle else None, timeout=args.timeout,
        keep_checkout=args.keep_checkout, selected_tests=args.tests)
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


def _run_history(args: argparse.Namespace) -> int:
    from codedna.test_history.collection import collect_results, import_results
    from codedna.test_history.features import build_dataset
    from codedna.test_history.mining import mine_history
    from codedna.test_history.store import HistoryStore

    command = args.history_command
    if command == "import-rtptorrent":
        return _import_rtptorrent(args)
    if command == "collect" and not args.allow_build:
        print("error: history collect runs every commit's build (project code executes); "
              "re-run with --allow-build if you trust this project", file=sys.stderr)
        return EXIT_ANALYSIS_ERROR
    if command in ("evaluate", "experiment") and getattr(args, "from_dataset", None):
        from codedna.test_history.features import Dataset
        dataset = Dataset.from_csv(args.from_dataset)
        return _run_on_dataset(args, dataset)
    if command in ("evaluate", "experiment") and not args.db:
        print("error: give --db or --from-dataset", file=sys.stderr)
        return EXIT_ANALYSIS_ERROR
    if command in ("import", "status", "evaluate", "experiment") and not Path(args.db).is_file():
        print(f"error: history database not found: {args.db} (run 'history mine' first)",
              file=sys.stderr)
        return EXIT_ANALYSIS_ERROR

    with HistoryStore(args.db) as store:
        if command == "mine":
            commits = mine_history(args.repo, store, revision=args.rev,
                                   max_commits=args.max_commits)
            return _write_json({"mined_commits": len(commits), **store.summary()}, None)
        if command == "import":
            return _write_json({**import_results(store, args.results, args.source),
                                **store.summary()}, None)
        if command == "collect":
            print("warning: running the Maven build of each commit (project code will execute)",
                  file=sys.stderr)
            return _write_json(collect_results(
                args.repo, store, args.output_dir, allow_build=True,
                max_commits=args.max_commits, maven_command=[args.mvn] if args.mvn else None,
                timeout=args.timeout), None)
        if command == "status":
            return _write_json(store.summary(), None)
        dataset = build_dataset(store, args.repo, structural=not args.no_structural)
        return _run_on_dataset(args, dataset)


def _run_on_dataset(args: argparse.Namespace, dataset) -> int:
    from codedna.models.evaluate import evaluate
    from codedna.models.experiment import run_experiment

    if args.history_command == "experiment":
        return _write_json(run_experiment(
            dataset, model=args.model, calibration=args.calibration, budget=args.budget,
            risk_target=args.risk_target, seed=args.seed, sweeps=not args.no_sweeps,
            ablations=not args.no_ablations), args.output)
    if args.dataset_csv:
        dataset.to_csv(args.dataset_csv)
    return _write_json(evaluate(dataset, rankers=args.rankers, seed=args.seed), args.output)


def _import_rtptorrent(args: argparse.Namespace) -> int:
    from codedna.test_history.rtptorrent import import_rtptorrent, list_projects
    from codedna.test_history.store import HistoryStore

    if args.list:
        return _write_json({"projects": list_projects(args.dataset)}, None)
    if not args.project or not args.db:
        print("error: --project and --db are required (or use --list)", file=sys.stderr)
        return EXIT_ANALYSIS_ERROR
    with HistoryStore(args.db) as store:
        report = import_rtptorrent(args.dataset, args.project, store, max_commits=args.max_commits)
        return _write_json({**report.to_dict(), **store.summary()}, None)


def _write_json(data: dict, output: str | None) -> int:
    text = json.dumps(data, indent=2)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
