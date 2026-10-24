"""End-to-end test with real Maven, JUnit 5 and JaCoCo on the sample project.

Skipped unless pytest runs with ``--run-maven``: it needs Maven, a JDK and
internet access (Maven downloads plugins), so it runs in CI, not by default.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from codedna.selection import compare_strategies
from codedna.test_mapping.maven import run_maven_tests

pytestmark = pytest.mark.maven

SAMPLE = Path(__file__).resolve().parents[2] / "examples" / "sample-java-project"
CALCULATOR = "src/main/java/example/PriceCalculator.java"


def test_coverage_mapping_and_strategy_comparison_with_real_maven(repo, tmp_path):
    shutil.copytree(SAMPLE, repo.path, dirs_exist_ok=True, ignore=shutil.ignore_patterns("target"))
    base = repo.commit("sample project")
    source = (repo.path / CALCULATOR).read_text(encoding="utf-8")
    repo.write(CALCULATOR, source.replace("return amount * (1.0 - discountRate);",
                                          "return amount;  // bug: discount ignored"))
    head = repo.commit("introduce a regression")

    base_run, coverage = run_maven_tests(repo.path, base, tmp_path / "base", allow_build=True,
                                         per_test_coverage=True)
    assert base_run.failing_tests == [], base_run.warnings
    assert "example.PriceCalculator#applyDiscount(double)" in \
        coverage.tests["example.PriceCalculatorTest"].members
    assert "example.OrderService#total()" in coverage.tests["example.OrderServiceTest"].members

    head_run, _ = run_maven_tests(repo.path, head, tmp_path / "head", allow_build=True)
    assert head_run.failing_tests == ["example.OrderServiceTest", "example.PriceCalculatorTest"]

    selected_run, _ = run_maven_tests(repo.path, head, tmp_path / "selected", allow_build=True,
        selected_tests=["example.PriceCalculatorTest"])
    assert set(selected_run.tests) == {"example.PriceCalculatorTest"}
    assert selected_run.failing_tests == ["example.PriceCalculatorTest"]

    comparison = compare_strategies(repo.path, base, head, head_run, coverage_map=coverage)
    rows = {row["strategy"]: row for row in comparison["strategies"]}
    for strategy in ("all", "dependency", "coverage"):
        assert rows[strategy]["safe"], rows[strategy]
