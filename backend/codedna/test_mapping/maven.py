"""Run a project's JUnit tests with Maven, optionally with per-test JaCoCo coverage.

**Running tests executes the analysed project's code and build plugins.**
Nothing here runs unless the caller passes ``allow_build=True`` (the CLI's
``--allow-build``). The commit is exported with ``git archive`` into
``OUTPUT_DIR/checkout`` so the user's working tree is never modified, and
JaCoCo is attached from the command line, so the project's ``pom.xml`` is not
edited. Maven may still download plugins and dependencies from the internet.

Per-test coverage runs Maven once per test class (``-Dtest=<class>``) with a
fresh JaCoCo data file each time — simple and exact at class granularity, but
slow: total time is roughly ``number of test classes × build start-up``.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import time
from pathlib import Path

from codedna.git_analysis.blobs import export_commit, list_files, read_blobs
from codedna.git_analysis.git import CodeDNAGitError, resolve_commit, resolve_repository
from codedna.java_analysis.parser import TYPE_NODES, JavaParseResult, parse_java
from codedna.test_mapping.build import detect_build
from codedna.test_mapping.discovery import discover_tests_for_commit
from codedna.test_mapping.reports import (
    JacocoCoverage,
    ReportError,
    parse_jacoco_report,
    parse_surefire_reports,
)
from codedna.test_mapping.results import (
    COVERAGE_MAP_FILE,
    RESULTS_FILE,
    CoverageMap,
    TestCoverage,
    TestRunResult,
    save_json,
)

JACOCO_PLUGIN = "org.jacoco:jacoco-maven-plugin:0.8.12"
MAVEN_REPORTS = "**/target/surefire-reports"
GRADLE_REPORTS = "**/build/test-results/test"
GRADLE_INIT = """allprojects {
    tasks.withType(Test).configureEach {
        ignoreFailures = true
        filter.failOnNoMatchingTests = false
    }
}
"""
_TYPE_KINDS = frozenset(TYPE_NODES.values())
_JAVA_NAME = re.compile(r"^[A-Za-z_$][\w$]*(\.[A-Za-z_$][\w$]*)*$")


class BuildError(CodeDNAGitError):
    """The build could not be started or its output could not be read."""


def find_maven() -> list[str]:
    executable = shutil.which("mvn") or shutil.which("mvn.cmd")
    if executable is None:
        raise BuildError("Maven (mvn) not found on PATH; install Maven 3.9+ or pass --mvn")
    return [executable]


def find_gradle() -> list[str]:
    # The system Gradle, never the repository's own wrapper script.
    executable = shutil.which("gradle") or shutil.which("gradle.bat")
    if executable is None:
        raise BuildError("Gradle not found on PATH; install Gradle 8+ or pass --gradle")
    return [executable]


def run_maven_tests(repo_path: str | Path, revision: str, output_dir: str | Path, *,
                    allow_build: bool, per_test_coverage: bool = False,
                    maven_command: list[str] | None = None, timeout: int = 1800,
                    keep_checkout: bool = False,
                    selected_tests: list[str] | None = None,
                    gradle_command: list[str] | None = None) -> tuple[TestRunResult, CoverageMap | None]:
    """Run the tests of ``revision`` and write ``results.json`` (+ ``coverage-map.json``).

    Maven (single or multi-module, run from the root reactor) or Gradle,
    chosen from the committed build files (``build.py``).
    """
    if not allow_build:
        raise BuildError("running tests executes project code; pass --allow-build to confirm")
    repo = resolve_repository(repo_path)
    commit = resolve_commit(repo, revision)
    output = Path(output_dir).resolve()
    if output.exists() and any(output.iterdir()):
        raise BuildError(f"output directory is not empty: {output}")
    layout = detect_build(repo, commit)
    if layout.tool is None:
        raise BuildError("no pom.xml or Gradle build file at the repository root")
    if per_test_coverage and (layout.tool != "maven" or len(layout.modules) > 1):
        raise BuildError("per-test coverage supports single-module Maven projects only")
    if selected_tests == []:
        tool = []
    elif layout.tool == "gradle":
        tool = gradle_command or find_gradle()
    else:
        tool = maven_command or find_maven()

    if selected_tests is not None:
        if per_test_coverage:
            raise BuildError("selected tests and per-test coverage cannot be combined")
        available = {t.id for t in discover_tests_for_commit(repo, commit).tests if t.runs_by_default}
        if len(set(selected_tests)) != len(selected_tests) or any(
                not _JAVA_NAME.fullmatch(t) or t not in available for t in selected_tests):
            raise BuildError("selected tests must be distinct test classes the build runs by default")
    checkout = output / "checkout"
    export_commit(repo, commit, checkout)

    run = TestRunResult(repository=str(repo), commit=commit, tool=layout.tool, commands=[],
                        exit_codes=[], duration_seconds=0.0, per_test_coverage=per_test_coverage)
    coverage_map = None
    started = time.monotonic()
    try:
        if per_test_coverage:
            coverage_map = _run_per_test(repo, commit, tool, checkout, output, run, timeout)
        elif selected_tests == []:
            run.warnings.append("no tests selected; the build tool was not invoked")
        elif layout.tool == "gradle":
            _run_gradle(tool, selected_tests, checkout, output, run, timeout)
            _collect_results(checkout, output / "reports" / "full-suite", run, GRADLE_REPORTS)
        else:
            goals = ["test"]
            if selected_tests is not None:
                patterns = [pattern for t in selected_tests for pattern in (t, t + "$*")]
                # In a reactor most modules match none of the selected classes.
                strict = "true" if len(layout.modules) == 1 else "false"
                goals += ["-Dtest=" + ",".join(patterns), f"-Dsurefire.failIfNoSpecifiedTests={strict}"]
            _run_maven(tool, goals, checkout, output / "logs" / "full-suite.log", run, timeout)
            _collect_results(checkout, output / "reports" / "full-suite", run)
        if selected_tests:
            missing = set(selected_tests) - set(run.tests)
            if missing:
                run.warnings.append("selected tests missing from reports: " + ", ".join(sorted(missing)))
    finally:
        run.duration_seconds = round(time.monotonic() - started, 3)
        if not keep_checkout:
            shutil.rmtree(checkout, ignore_errors=True)

    save_json(run.to_dict(), output / RESULTS_FILE)
    if coverage_map is not None:
        save_json(coverage_map.to_dict(), output / COVERAGE_MAP_FILE)
    return run, coverage_map


def _run_per_test(repo: Path, commit: str, maven: list[str], checkout: Path, output: Path,
                  run: TestRunResult, timeout: int) -> CoverageMap:
    discovery = discover_tests_for_commit(repo, commit)
    run.warnings.extend(discovery.warnings)
    code = _CodeIndex(repo, commit)
    coverage_map = CoverageMap(repository=str(repo), commit=commit, tool="jacoco")
    target = checkout / "target"

    for test in discovery.tests:
        if not test.runs_by_default:
            continue
        if not _JAVA_NAME.match(test.id):
            run.warnings.append(f"skipped test with unexpected name: {test.id!r}")
            continue
        # JaCoCo appends to an existing data file, so start every run clean.
        (target / "jacoco.exec").unlink(missing_ok=True)
        shutil.rmtree(target / "surefire-reports", ignore_errors=True)
        shutil.rmtree(target / "site" / "jacoco", ignore_errors=True)
        _run_maven(maven, [
            f"{JACOCO_PLUGIN}:prepare-agent", "test", f"{JACOCO_PLUGIN}:report",
            f"-Dtest={test.id},{test.id}$*",
            "-Dsurefire.failIfNoSpecifiedTests=false",
        ], checkout, output / "logs" / f"{test.id}.log", run, timeout)
        _collect_results(checkout, output / "reports" / test.id, run)

        report = target / "site" / "jacoco" / "jacoco.xml"
        if not report.is_file():
            run.warnings.append(f"{test.id}: no JaCoCo report produced; coverage unknown")
            continue
        try:
            coverage = parse_jacoco_report(report)
        except ReportError as exc:
            run.warnings.append(str(exc))
            continue
        shutil.copy2(report, output / "reports" / test.id / "jacoco.xml")
        coverage_map.tests[test.id] = code.map_coverage(coverage, coverage_map.warnings)
    return coverage_map


def _run_maven(maven: list[str], goals: list[str], checkout: Path, log: Path,
               run: TestRunResult, timeout: int) -> None:
    _run_tool("Maven", [*maven, "-B", "--no-transfer-progress", *goals,
                        "-Dmaven.test.failure.ignore=true"], checkout, log, run, timeout)


def _run_tool(name: str, command: list[str], checkout: Path, log: Path,
              run: TestRunResult, timeout: int) -> None:
    run.commands.append(command)
    log.parent.mkdir(parents=True, exist_ok=True)
    try:
        completed = subprocess.run(command, cwd=checkout, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=timeout,
                                   check=False)
    except FileNotFoundError as exc:
        raise BuildError(f"cannot run {name}: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        run.exit_codes.append(-1)
        run.warnings.append(f"{name} timed out after {timeout}s: {' '.join(command[1:])}")
        log.write_text(str(exc.stdout or ""), encoding="utf-8")
        return
    log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    run.exit_codes.append(completed.returncode)
    if completed.returncode != 0:
        # Test failures are ignored, so a non-zero exit means the build itself
        # failed, e.g. a compilation error.
        run.warnings.append(f"{name} exited with {completed.returncode} (build failure?); "
                            f"see {log}")


def _run_gradle(gradle: list[str], selected: list[str] | None, checkout: Path, output: Path,
                run: TestRunResult, timeout: int) -> None:
    # An init script of ours (not the project's) makes failing tests not fail
    # the build, like -Dmaven.test.failure.ignore, and lets modules without
    # selected tests pass.
    init = output / "codedna-init.gradle"
    init.write_text(GRADLE_INIT, encoding="utf-8")
    filters = [arg for t in selected or [] for arg in ("--tests", t, "--tests", t + "$*")]
    _run_tool("Gradle", [*gradle, "--no-daemon", "--console=plain", "--init-script", str(init),
                         "test", "--continue", *filters],
              checkout, output / "logs" / "full-suite.log", run, timeout)


def _collect_results(checkout: Path, destination: Path, run: TestRunResult,
                     pattern: str = MAVEN_REPORTS) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    directories = sorted(p for p in checkout.glob(pattern) if p.is_dir())
    if not directories:
        run.warnings.append(f"no test reports matching {pattern} in {checkout}")
        return
    for reports in directories:
        try:
            results = parse_surefire_reports(reports)
        except ReportError as exc:
            run.warnings.append(str(exc))
            continue
        module = reports.relative_to(checkout).parts[:-len(Path(pattern).parts) + 1]
        target = destination.joinpath(*module) if module else destination
        target.mkdir(parents=True, exist_ok=True)
        for report in reports.glob("TEST-*.xml"):
            shutil.copy2(report, target / report.name)
        for test_id, result in results.items():
            existing = run.tests.get(test_id)
            if existing is None:
                run.tests[test_id] = result
            else:
                for case in result.cases:
                    existing.add(case)


class _CodeIndex:
    """Declarations of every Java file of a commit, for mapping covered lines."""

    def __init__(self, repo: Path, commit: str):
        files = list_files(repo, commit, ".java")
        contents = read_blobs(repo, sorted({blob for _, blob in files}))
        self.parsed: dict[str, JavaParseResult] = {
            path: parse_java(contents[blob]) for path, blob in files}

    def map_coverage(self, coverage: JacocoCoverage, warnings: list[str]) -> TestCoverage:
        result = TestCoverage()
        types: set[str] = set(coverage.covered_types)
        members: set[str] = set()
        for (package, source_name), lines in sorted(coverage.covered_lines.items()):
            paths = self._source_paths(package, source_name)
            if not paths:
                message = f"covered source {package}/{source_name} not found in commit"
                if message not in warnings:
                    warnings.append(message)
                continue
            if len(paths) > 1:
                message = f"covered source {package}/{source_name} matches {paths}; all used"
                if message not in warnings:
                    warnings.append(message)
            for path in paths:
                result.files[path] = _to_ranges(lines)
                for line in lines:
                    declaration = self._innermost(path, line)
                    if declaration is None:
                        continue
                    if declaration.kind in _TYPE_KINDS:
                        types.add(declaration.id)
                    else:
                        members.add(declaration.id)
                        if declaration.parent:
                            types.add(declaration.parent)
        result.types = sorted(types)
        result.members = sorted(members)
        return result

    def _source_paths(self, package: str, source_name: str) -> list[str]:
        suffix = f"{package}/{source_name}" if package else source_name
        paths = [p for p in self.parsed if p == suffix or p.endswith(f"/{suffix}")]
        main = [p for p in paths if "/src/main/" in f"/{p}"]
        return main or paths

    def _innermost(self, path: str, line: int):
        containing = [d for d in self.parsed[path].declarations
                      if d.start_line <= line <= d.end_line]
        # Innermost = narrowest extent (members are nested inside their types).
        return min(containing, key=lambda d: d.end_line - d.start_line, default=None)


def _to_ranges(lines: set[int]) -> list[list[int]]:
    ranges: list[list[int]] = []
    for line in sorted(lines):
        if ranges and line == ranges[-1][1] + 1:
            ranges[-1][1] = line
        else:
            ranges.append([line, line])
    return ranges
