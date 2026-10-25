"""Tests for the selection baselines (all / dependency / coverage) and compare."""

from __future__ import annotations

import json

import pytest

from codedna.cli import EXIT_ANALYSIS_ERROR, EXIT_OK, main
from codedna.selection import SelectionError, compare_strategies, select_tests
from codedna.test_mapping.results import TestCaseResult, TestClassResult
from codedna.test_mapping.results import (
    CoverageMap,
    TestCoverage,
    TestRunResult,
    save_json,
)

JUNIT5 = "import org.junit.jupiter.api.Test;\n"
CORE = ("package a;\n\npublic class Core {\n    int one() {\n        return 1;\n    }\n"
        "    int two() {\n        return 2;\n    }\n}\n")
FILES = {
    "src/main/java/a/Core.java": CORE,
    "src/main/java/a/Service.java": "package a;\n\npublic class Service {\n    Core core;\n}\n",
    "src/main/java/a/Other.java": "package a;\n\npublic class Other {\n}\n",
    "src/test/java/a/OneTest.java": "package a;\n" + JUNIT5 + "class OneTest {\n    Core c;\n    @Test void t() {}\n}\n",
    "src/test/java/a/TwoTest.java": "package a;\n" + JUNIT5 + "class TwoTest {\n    Service s;\n    @Test void t() {}\n}\n",
    "src/test/java/a/OtherTest.java": "package a;\n" + JUNIT5 + "class OtherTest {\n    Other o;\n    @Test void t() {}\n}\n",
}


def commit(repo, files, message):
    for path, content in files.items():
        repo.write(path, content)
    return repo.commit(message)


def coverage_map(base_sha, tests):
    return CoverageMap(repository="r", commit=base_sha, tool="jacoco",
                       tests={k: TestCoverage(**v) for k, v in tests.items()})


def results(commit_sha, outcomes):
    run = TestRunResult(repository="r", commit=commit_sha, tool="maven", commands=[],
                        exit_codes=[0], duration_seconds=1.0, per_test_coverage=False)
    for test_id, (status, seconds) in outcomes.items():
        result = TestClassResult(test_id)
        result.add(TestCaseResult("t", status, seconds))
        run.tests[test_id] = result
    return run


@pytest.fixture
def history(repo):
    base = commit(repo, FILES, "base")
    head = commit(repo, {"src/main/java/a/Core.java": CORE.replace("return 1;", "return 11;")},
                  "change Core#one")
    cov = coverage_map(base, {
        "a.OneTest": {"members": ["a.Core#one()"], "types": ["a.Core"],
                      "files": {"src/main/java/a/Core.java": [[4, 6]]}},
        "a.TwoTest": {"members": ["a.Core#two()"], "types": ["a.Core", "a.Service"],
                      "files": {"src/main/java/a/Core.java": [[7, 9]]}},
        "a.OtherTest": {"members": [], "types": ["a.Other"], "files": {}},
    })
    return repo, base, head, cov


def selected(report):
    return sorted(report.selected_ids)


def test_retest_all_selects_everything(history):
    repo, base, head, _ = history
    report = select_tests(repo.path, base, head, "all")
    assert selected(report) == ["a.OneTest", "a.OtherTest", "a.TwoTest"]
    assert report.selection_ratio == 1.0


def test_dependency_strategy_follows_static_graph(history):
    repo, base, head, _ = history
    report = select_tests(repo.path, base, head, "dependency")
    assert selected(report) == ["a.OneTest", "a.TwoTest"]
    assert report.skipped == ["a.OtherTest"]
    assert report.selection_ratio == pytest.approx(2 / 3, abs=1e-4)


def test_coverage_strategy_is_method_precise(history):
    repo, base, head, cov = history
    report = select_tests(repo.path, base, head, "coverage", coverage_map=cov)
    assert selected(report) == ["a.OneTest"]
    assert report.selected[0].reasons == ["covers modified method a.Core#one()"]


def test_coverage_strategy_requires_map(history):
    repo, base, head, _ = history
    with pytest.raises(SelectionError, match="coverage map"):
        select_tests(repo.path, base, head, "coverage")


def test_tests_without_coverage_data_are_selected(history):
    repo, base, head, cov = history
    del cov.tests["a.OtherTest"]
    report = select_tests(repo.path, base, head, "coverage", coverage_map=cov)
    assert selected(report) == ["a.OneTest", "a.OtherTest"]
    assert "no coverage data" in next(s for s in report.selected if s.test == "a.OtherTest").reasons[0]


def test_added_member_selects_tests_covering_its_class(repo):
    base = commit(repo, FILES, "base")
    head = commit(repo, {"src/main/java/a/Core.java": CORE.replace(
        "    int two()", "    int three() {\n        return 3;\n    }\n    int two()")}, "add method")
    cov = coverage_map(base, {
        "a.OneTest": {"members": ["a.Core#one()"], "types": ["a.Core"], "files": {}},
        "a.TwoTest": {"members": [], "types": ["a.Service"], "files": {}},
        "a.OtherTest": {"members": [], "types": ["a.Other"], "files": {}},
    })

    report = select_tests(repo.path, base, head, "coverage", coverage_map=cov)

    assert selected(report) == ["a.OneTest"]
    assert "gained a.Core#three()" in report.selected[0].reasons[0]


def test_comment_only_change_selects_nothing(repo):
    base = commit(repo, FILES, "base")
    head = commit(repo, {"src/main/java/a/Core.java": CORE.replace(
        "    int one()", "    // first\n    int one()")}, "comment")
    cov = coverage_map(base, {t: {"members": [], "types": ["a.Core"], "files": {}}
                              for t in ("a.OneTest", "a.TwoTest", "a.OtherTest")})

    assert select_tests(repo.path, base, head, "coverage", coverage_map=cov).selected == []
    assert select_tests(repo.path, base, head, "dependency").selected == []


def test_changed_test_class_is_always_selected(history):
    repo, _, head, cov = history
    newer = commit(repo, {"src/test/java/a/OtherTest.java": FILES["src/test/java/a/OtherTest.java"]
                          .replace("void t()", "void t2()")}, "edit test")
    report = select_tests(repo.path, head, newer, "coverage", coverage_map=cov)
    assert selected(report) == ["a.OtherTest"]
    assert report.selected[0].reasons[0] == "test class changed"


def test_non_java_change_falls_back_to_retest_all_unless_ignored(history):
    repo, _, head, cov = history
    newer = commit(repo, {"pom.xml": "<project/>\n"}, "build change")

    fallback = select_tests(repo.path, head, newer, "dependency")
    assert len(fallback.selected) == 3
    assert "falling back to retest-all" in fallback.selected[0].reasons[0]

    ignored = select_tests(repo.path, head, newer, "dependency", non_java="ignore")
    assert ignored.selected == []
    assert any("ignored by request" in w for w in ignored.warnings)


def test_stale_coverage_map_is_warned_about(history):
    repo, base, head, cov = history
    cov.commit = head
    report = select_tests(repo.path, base, head, "coverage", coverage_map=cov)
    assert any("not BASE" in w for w in report.warnings)


def test_estimated_time_uses_recorded_durations(history):
    repo, base, head, cov = history
    durations = results(base, {"a.OneTest": ("passed", 2.0), "a.TwoTest": ("passed", 6.0)})

    report = select_tests(repo.path, base, head, "coverage", coverage_map=cov, durations=durations)

    assert report.estimated_time["selected_seconds"] == 2.0
    assert report.estimated_time["all_seconds"] == 8.0
    assert report.estimated_time["saved_ratio"] == 0.75
    assert report.estimated_time["tests_without_duration"] == ["a.OtherTest"]


def test_compare_counts_caught_and_missed_failures(history):
    repo, base, head, cov = history
    truth = results(head, {"a.OneTest": ("passed", 1.0), "a.TwoTest": ("failed", 1.0),
                           "a.OtherTest": ("passed", 1.0)})

    comparison = compare_strategies(repo.path, base, head, truth, coverage_map=cov)

    rows = {row["strategy"]: row for row in comparison["strategies"]}
    assert rows["all"]["safe"] and rows["all"]["caught"] == ["a.TwoTest"]
    assert rows["dependency"]["safe"] and rows["dependency"]["selected"] == 2
    # TwoTest did not cover the changed method, so coverage-based selection misses it.
    assert rows["coverage"]["missed"] == ["a.TwoTest"] and not rows["coverage"]["safe"]
    assert comparison["warnings"] == []


def test_compare_warns_when_ground_truth_is_not_head(history):
    repo, base, head, _ = history
    comparison = compare_strategies(repo.path, base, head, results(base, {}))
    assert any("not HEAD" in w for w in comparison["warnings"])
    assert any("coverage strategy was not evaluated" in w for w in comparison["warnings"])


def test_select_and_compare_commands(history, tmp_path, capsys):
    repo, base, head, cov = history
    run_dir = tmp_path / "base-run"
    save_json(cov.to_dict(), run_dir / "coverage-map.json")
    save_json(results(head, {"a.OneTest": ("failed", 1.0)}).to_dict(), tmp_path / "truth.json")

    assert main(["select", "--repo", str(repo.path), "--base", base, "--head", head,
                 "--strategy", "coverage", "--coverage-map", str(run_dir)]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["selected_count"] == 1

    assert main(["compare", "--repo", str(repo.path), "--base", base, "--head", head,
                 "--ground-truth", str(tmp_path / "truth.json"),
                 "--coverage-map", str(run_dir)]) == EXIT_OK
    rows = json.loads(capsys.readouterr().out)["strategies"]
    assert [r["strategy"] for r in rows] == ["all", "dependency", "coverage"]
    assert all(r["safe"] for r in rows)

    assert main(["select", "--repo", str(repo.path), "--base", base, "--head", head,
                 "--strategy", "coverage"]) == EXIT_ANALYSIS_ERROR
    assert "coverage map" in capsys.readouterr().err
