"""Saved results of a test run and the per-test coverage map (JSON files).

``results.json`` — outcome and duration of every test class in one run.
``coverage-map.json`` — for every test class, the files/lines, types and
members it executed, mapped onto the code graph's IDs.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

RESULTS_FILE = "results.json"
COVERAGE_MAP_FILE = "coverage-map.json"

PASSED, FAILED, ERROR, SKIPPED = "passed", "failed", "error", "skipped"
# Worst status wins when combining test cases into a class result.
_SEVERITY = {SKIPPED: 0, PASSED: 1, FAILED: 2, ERROR: 3}


class ReportError(Exception):
    """A test or coverage report written by a build tool could not be read."""


@dataclass
class TestCaseResult:
    __test__ = False  # not a pytest test class

    name: str  # method name; "Nested.method" for @Nested classes
    status: str
    time: float
    message: str | None = None


@dataclass
class TestClassResult:
    __test__ = False  # not a pytest test class

    id: str  # top-level class, e.g. "example.PriceCalculatorTest"
    status: str = SKIPPED
    time: float = 0.0
    cases: list[TestCaseResult] = field(default_factory=list)

    def add(self, case: TestCaseResult) -> None:
        self.cases.append(case)
        self.time = round(self.time + case.time, 6)
        if _SEVERITY[case.status] > _SEVERITY[self.status]:
            self.status = case.status

    @property
    def failed(self) -> bool:
        return self.status in (FAILED, ERROR)


@dataclass
class TestRunResult:
    __test__ = False  # not a pytest test class

    repository: str
    commit: str
    tool: str  # e.g. "maven"
    commands: list[list[str]]
    exit_codes: list[int]
    duration_seconds: float
    per_test_coverage: bool
    tests: dict[str, TestClassResult] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def failing_tests(self) -> list[str]:
        return sorted(test_id for test_id, result in self.tests.items() if result.failed)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["tests"] = [asdict(result) for _, result in sorted(self.tests.items())]
        data["failing_tests"] = self.failing_tests
        return data

    @classmethod
    def from_dict(cls, data: dict) -> TestRunResult:
        tests = {}
        for entry in data.get("tests", []):
            result = TestClassResult(entry["id"], entry["status"], entry["time"],
                                     [TestCaseResult(**case) for case in entry.get("cases", [])])
            tests[result.id] = result
        return cls(
            repository=data["repository"], commit=data["commit"], tool=data["tool"],
            commands=data.get("commands", []), exit_codes=data.get("exit_codes", []),
            duration_seconds=data.get("duration_seconds", 0.0),
            per_test_coverage=data.get("per_test_coverage", False),
            tests=tests, warnings=data.get("warnings", []),
        )


@dataclass
class TestCoverage:
    __test__ = False  # not a pytest test class

    files: dict[str, list[list[int]]] = field(default_factory=dict)  # path -> line ranges
    types: list[str] = field(default_factory=list)
    members: list[str] = field(default_factory=list)


@dataclass
class CoverageMap:
    repository: str
    commit: str
    tool: str  # "jacoco"
    tests: dict[str, TestCoverage] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "repository": self.repository, "commit": self.commit, "tool": self.tool,
            "tests": {test_id: asdict(cov) for test_id, cov in sorted(self.tests.items())},
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CoverageMap:
        return cls(
            repository=data["repository"], commit=data["commit"], tool=data["tool"],
            tests={test_id: TestCoverage(**cov) for test_id, cov in data.get("tests", {}).items()},
            warnings=data.get("warnings", []),
        )


def save_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_results(path: Path) -> TestRunResult:
    return TestRunResult.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def load_coverage_map(path: Path) -> CoverageMap:
    return CoverageMap.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
