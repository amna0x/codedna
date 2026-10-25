"""Tests for static JUnit test discovery (Milestone 3)."""

from __future__ import annotations

import json

from codedna.cli import EXIT_OK, main
from codedna_java.discovery import discover_tests


def discover(repo, files):
    for path, content in files.items():
        repo.write(path, content)
    repo.commit("snapshot")
    report = discover_tests(repo.path, "HEAD")
    return {t.id: t for t in report.tests}, report


JUNIT5 = "import org.junit.jupiter.api.Test;\n"


def test_junit5_test_class_with_methods(repo):
    tests, report = discover(repo, {
        "src/test/java/a/PriceTest.java":
            "package a;\n" + JUNIT5 + "import org.junit.jupiter.params.ParameterizedTest;\n"
            "class PriceTest {\n    @Test void one() {}\n    @ParameterizedTest void two(int x) {}\n"
            "    void helper() {}\n}\n",
        "src/main/java/a/Price.java": "package a;\npublic class Price {}\n",
    })

    assert list(tests) == ["a.PriceTest"]
    test = tests["a.PriceTest"]
    assert test.framework == "junit5"
    assert test.methods == ["one", "two"]
    assert test.runs_by_default is True
    assert report.warnings == []


def test_junit4_framework_detected(repo):
    tests, _ = discover(repo, {
        "src/test/java/a/OldTest.java":
            "package a;\nimport org.junit.Test;\npublic class OldTest {\n    @Test public void t() {}\n}\n",
    })

    assert tests["a.OldTest"].framework == "junit4"


def test_abstract_base_tests_are_inherited(repo):
    tests, _ = discover(repo, {
        "src/test/java/a/BaseContractTest.java":
            "package a;\n" + JUNIT5 + "abstract class BaseContractTest {\n    @Test void contract() {}\n}\n",
        "src/test/java/a/ListContractTest.java":
            "package a;\nclass ListContractTest extends BaseContractTest {}\n",
    })

    assert list(tests) == ["a.ListContractTest"]  # the abstract base is not runnable
    assert tests["a.ListContractTest"].inherited_from == ["a.BaseContractTest"]
    assert tests["a.ListContractTest"].methods == ["a.BaseContractTest#contract"]


def test_nested_test_classes_belong_to_top_level_class(repo):
    tests, _ = discover(repo, {
        "src/test/java/a/CartTest.java":
            "package a;\n" + JUNIT5 + "import org.junit.jupiter.api.Nested;\n"
            "class CartTest {\n    @Test void empty() {}\n"
            "    @Nested class WhenFull {\n        @Test void total() {}\n    }\n}\n",
    })

    assert list(tests) == ["a.CartTest"]
    assert tests["a.CartTest"].methods == ["empty", "WhenFull.total"]


def test_tests_outside_surefire_defaults_are_flagged(repo):
    tests, report = discover(repo, {
        "src/test/java/a/Checks.java": "package a;\n" + JUNIT5 + "class Checks { @Test void t() {} }\n",
        "src/main/java/a/InMainTest.java": "package a;\n" + JUNIT5 + "class InMainTest { @Test void t() {} }\n",
    })

    assert tests["a.Checks"].in_test_sources and not tests["a.Checks"].matches_surefire_defaults
    assert not tests["a.InMainTest"].in_test_sources
    assert not any(t.runs_by_default for t in tests.values())
    assert len(report.warnings) == 2


def test_testng_is_reported_as_unsupported(repo):
    tests, report = discover(repo, {
        "src/test/java/a/NgTest.java":
            "package a;\nimport org.testng.annotations.Test;\nclass NgTest { @Test void t() {} }\n",
    })

    assert tests == {}
    assert "TestNG is not supported" in report.warnings[0]


def test_tests_command_outputs_json(repo, capsys):
    repo.write("src/test/java/a/ATest.java", "package a;\n" + JUNIT5 + "class ATest { @Test void t() {} }\n")
    repo.commit("one")

    assert main(["tests", "--repo", str(repo.path)]) == EXIT_OK
    data = json.loads(capsys.readouterr().out)
    assert data["test_count"] == 1
    assert data["tests"][0]["id"] == "a.ATest" and data["tests"][0]["runs_by_default"] is True
