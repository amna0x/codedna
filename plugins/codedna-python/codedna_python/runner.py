"""Run a project's pytest tests and save ``results.json``.

**Running tests executes the analysed project's code** (its test modules,
``conftest.py`` files and pytest plugins). Nothing here runs unless the
caller passes ``allow_build=True`` (the CLI's ``--allow-build``, D-014). The
commit is exported with ``git archive`` into ``OUTPUT_DIR/checkout``, so the
user's working tree is never touched, and pytest runs there with the
interpreter the user names (``--python``) or ``python3``/``python`` on PATH;
that interpreter needs pytest and the project's own dependencies. CodeDNA
installs nothing into it.

Results come from pytest's JUnit XML report and are kept per test module
(``py:<module>``), CodeDNA's unit of selection for Python. Per-test coverage
is not supported for Python.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ElementTree
from pathlib import Path, PurePosixPath

from codedna.git_analysis.blobs import export_commit
from codedna.git_analysis.git import CodeDNAGitError, resolve_commit, resolve_repository
from codedna.test_mapping.results import (
    ERROR,
    FAILED,
    PASSED,
    RESULTS_FILE,
    SKIPPED,
    TestCaseResult,
    TestClassResult,
    TestRunResult,
    save_json,
)
from codedna_python.discovery import discover_tests_for_commit

# pytest exit codes that still mean "the tests ran" (0 passed, 1 some failed,
# 5 nothing collected).
_RAN = {0, 1, 5}


class PytestRunError(CodeDNAGitError):
    """pytest could not be started or its report could not be read."""


def find_python() -> list[str]:
    # On Windows "python3" is often the Microsoft Store stub, so try "python" first.
    names = ("python", "python3") if os.name == "nt" else ("python3", "python")
    for name in names:
        executable = shutil.which(name)
        if executable:
            return [executable]
    return [sys.executable]


def run_pytest(repo_path: str | Path, revision: str, output_dir: str | Path, *,
               allow_build: bool, per_test_coverage: bool = False,
               python_command: list[str] | None = None, timeout: int = 1800,
               keep_checkout: bool = False, selected_tests: list[str] | None = None,
               **_other_plugins_options) -> tuple[TestRunResult, None]:
    """Run pytest on ``revision`` (all tests, or only ``selected_tests`` modules)."""
    if not allow_build:
        raise PytestRunError("running tests executes project code; pass --allow-build to confirm")
    repo = resolve_repository(repo_path)
    commit = resolve_commit(repo, revision)
    output = Path(output_dir).resolve()
    if output.exists() and any(output.iterdir()):
        raise PytestRunError(f"output directory is not empty: {output}")

    discovery = discover_tests_for_commit(repo, commit)
    files = {t.id: t.file for t in discovery.tests}
    if selected_tests is not None:
        runnable = {t.id for t in discovery.tests if t.runs_by_default}
        if len(set(selected_tests)) != len(selected_tests) or any(
                t not in runnable for t in selected_tests):
            raise PytestRunError("selected tests must be distinct pytest modules that run by default")

    run = TestRunResult(repository=str(repo), commit=commit, tool="pytest", commands=[],
                        exit_codes=[], duration_seconds=0.0, per_test_coverage=False)
    if per_test_coverage:
        run.warnings.append("per-test coverage is not supported for Python; tests ran without it")
    checkout = output / "checkout"
    export_commit(repo, commit, checkout)
    report = output / "reports" / "pytest-junit.xml"
    started = time.monotonic()
    try:
        if selected_tests == []:
            run.warnings.append("no tests selected; pytest was not invoked")
        else:
            report.parent.mkdir(parents=True, exist_ok=True)
            # File paths, never "-k" expressions or node IDs built from repository text.
            targets = [files[t] for t in sorted(selected_tests)] if selected_tests else []
            command = [*(python_command or find_python()), "-m", "pytest", "-q",
                       "-p", "no:cacheprovider", "-o", "junit_family=xunit2",
                       f"--junitxml={report}", *(["--", *targets] if targets else [])]
            _run(command, checkout, output / "logs" / "pytest.log", run, timeout)
            if report.is_file():
                _collect(report, discovery.tests, run)
            else:
                run.warnings.append("pytest wrote no report; is pytest installed for "
                                    f"{command[0]}? See logs/pytest.log")
        if selected_tests:
            missing = set(selected_tests) - set(run.tests)
            if missing:
                run.warnings.append("selected tests missing from reports: " + ", ".join(sorted(missing)))
    finally:
        run.duration_seconds = round(time.monotonic() - started, 3)
        if not keep_checkout:
            shutil.rmtree(checkout, ignore_errors=True)
    save_json(run.to_dict(), output / RESULTS_FILE)
    return run, None


def _run(command: list[str], checkout: Path, log: Path, run: TestRunResult, timeout: int) -> None:
    run.commands.append(command)
    log.parent.mkdir(parents=True, exist_ok=True)
    # No bytecode files in the checkout; nothing else of the user's environment changes.
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        with log.open("wb") as handle:
            completed = subprocess.run(command, cwd=checkout, stdout=handle,
                                       stderr=subprocess.STDOUT, timeout=timeout or None,
                                       env=env, check=False)
    except FileNotFoundError as exc:
        raise PytestRunError(f"Python interpreter not found: {command[0]}") from exc
    except subprocess.TimeoutExpired:
        run.exit_codes.append(-1)
        run.warnings.append(f"pytest timed out after {timeout} s; results may be incomplete")
        return
    run.exit_codes.append(completed.returncode)
    if completed.returncode not in _RAN:
        run.warnings.append(f"pytest exited with code {completed.returncode} (interrupted, "
                            "internal or usage error); see logs/pytest.log")


def _collect(report: Path, tests, run: TestRunResult) -> None:
    """Fold JUnit test cases into one result per test module."""
    try:
        root = ElementTree.parse(report).getroot()  # no external entities or DTDs are fetched
    except (ElementTree.ParseError, OSError) as exc:
        run.warnings.append(f"{report.name} could not be read: {exc}")
        return
    # "tests/test_x.py" -> classname prefix "tests.test_x"; longest prefix wins.
    prefixes = sorted(((".".join(PurePosixPath(t.file).with_suffix("").parts), t.id) for t in tests),
                      key=lambda item: -len(item[0]))
    unknown: set[str] = set()
    for case in root.iter("testcase"):
        classname = case.get("classname") or ""
        name = case.get("name") or ""
        match = next(((prefix, test_id) for prefix, test_id in prefixes
                      if classname == prefix or classname.startswith(prefix + ".")), None)
        if match is None:
            unknown.add(classname or name)
            continue
        prefix, test_id = match
        inner = classname[len(prefix) + 1:]
        result = run.tests.setdefault(test_id, TestClassResult(test_id))
        result.add(TestCaseResult(f"{inner}.{name}" if inner else name, _status(case),
                                  _float(case.get("time")), _message(case)))
    if unknown:
        run.warnings.append(f"results for {len(unknown)} unknown test location(s) ignored: "
                            f"{sorted(unknown)[:5]}")


def _status(case: ElementTree.Element) -> str:
    if case.find("error") is not None:
        return ERROR
    if case.find("failure") is not None:
        return FAILED
    if case.find("skipped") is not None:
        return SKIPPED
    return PASSED


def _message(case: ElementTree.Element) -> str | None:
    for tag in ("error", "failure", "skipped"):
        element = case.find(tag)
        if element is not None:
            return (element.get("message") or "")[:500] or None
    return None


def _float(value: str | None) -> float:
    try:
        return round(float(value or 0), 6)
    except ValueError:
        return 0.0
