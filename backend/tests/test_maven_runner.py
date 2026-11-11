"""Tests for the Maven runner using a fake ``mvn`` (no Maven or Java needed)."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

from codedna.cli import EXIT_ANALYSIS_ERROR, main
from codedna.git_analysis.blobs import export_commit
from codedna_java.maven import BuildError, run_maven_tests
from codedna.test_mapping.results import load_coverage_map, load_results

FAKE_MVN = [sys.executable, str(Path(__file__).with_name("fake_mvn.py"))]
JUNIT5 = "import org.junit.jupiter.api.Test;\n"

PROJECT = {
    "pom.xml": "<project/>\n",
    "src/main/java/a/Price.java":
        "package a;\n\npublic class Price {\n    int twice(int v) {\n        return 2 * v;\n    }\n"
        "    int half(int v) {\n        return v / 2;\n    }\n}\n",
    "src/test/java/a/PriceTest.java":
        "package a;\n" + JUNIT5 + "class PriceTest {\n    @Test void twice() {}\n}\n",
    "src/test/java/a/HalfTest.java":
        "package a;\n" + JUNIT5 + "class HalfTest {\n    @Test void half() {}\n}\n",
}
SPEC = {"tests": {
    "a.PriceTest": {"status": "passed", "time": 0.5, "cases": ["twice"],
                    "classes": ["a/Price"], "lines": {"a/Price.java": [5]}},
    "a.HalfTest": {"status": "failed", "time": 0.25, "cases": ["half"],
                   "classes": ["a/Price"], "lines": {"a/Price.java": [8]}},
}}


@pytest.mark.parametrize('platform,tool,expected', [
    ('win32', 'maven', 'mvn.cmd'), ('linux', 'maven', 'mvn'),
    ('win32', 'gradle', 'gradle.bat'), ('linux', 'gradle', 'gradle'),
])
def test_discovery_prefers_platform_launcher_when_both_scripts_exist(repo, monkeypatch, platform, tool, expected):
    from codedna_java import maven
    names = ('mvn', 'mvn.cmd') if tool == 'maven' else ('gradle', 'gradle.bat')
    for name in names:
        repo.write(f'bin/{name}', 'launcher fixture\n')
    repo.commit('both platform launchers')
    monkeypatch.setattr(maven, 'sys', SimpleNamespace(platform=platform))
    monkeypatch.setattr(maven.shutil, 'which', lambda name: str(repo.path / 'bin' / name) if name in names else None)
    discover = maven.find_maven if tool == 'maven' else maven.find_gradle
    assert discover() == [str(repo.path / 'bin' / expected)]


@pytest.fixture
def project(repo, tmp_path, monkeypatch):
    for path, content in PROJECT.items():
        repo.write(path, content)
    repo.commit("project")
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(SPEC), encoding="utf-8")
    monkeypatch.setenv("CODEDNA_FAKE_MVN_SPEC", str(spec))
    return repo


def test_build_requires_explicit_permission(project, tmp_path):
    with pytest.raises(BuildError, match="--allow-build"):
        run_maven_tests(project.path, "HEAD", tmp_path / "out", allow_build=False,
                        maven_command=FAKE_MVN)
    assert not (tmp_path / "out").exists()


def test_cli_refuses_without_allow_build(project, tmp_path, capsys):
    code = main(["run-tests", "--repo", str(project.path), "--output-dir", str(tmp_path / "o")])

    assert code == EXIT_ANALYSIS_ERROR
    assert "--allow-build" in capsys.readouterr().err
    assert not (tmp_path / "o").exists()


def test_full_suite_run_writes_results_and_keeps_worktree_clean(project, tmp_path):
    out = tmp_path / "out"
    run, coverage = run_maven_tests(project.path, "HEAD", out, allow_build=True,
                                    maven_command=FAKE_MVN)

    assert coverage is None
    assert run.failing_tests == ["a.HalfTest"]
    assert run.tests["a.PriceTest"].time == 0.5
    assert run.commands[0][-2:] == ["test", "-Dmaven.test.failure.ignore=true"]
    saved = load_results(out / "results.json")
    assert saved.commit == run.commit and saved.failing_tests == ["a.HalfTest"]
    assert (out / "reports" / "full-suite" / "TEST-a.PriceTest.xml").is_file()
    assert not (out / "checkout").exists()  # removed after the run
    assert not (project.path / "target").exists()  # user's working tree untouched
    assert project.git("status", "--porcelain") == ""


def test_per_test_coverage_maps_lines_to_members(project, tmp_path):
    out = tmp_path / "out"
    run, coverage = run_maven_tests(project.path, "HEAD", out, allow_build=True,
                                    per_test_coverage=True, maven_command=FAKE_MVN,
                                    keep_checkout=True)

    assert len(run.commands) == 2
    assert any("-Dtest=a.PriceTest,a.PriceTest$*" in command for command in run.commands)
    price = coverage.tests["a.PriceTest"]
    assert price.members == ["a.Price#twice(int)"]
    assert price.types == ["a.Price"]
    assert price.files == {"src/main/java/a/Price.java": [[5, 5]]}
    assert coverage.tests["a.HalfTest"].members == ["a.Price#half(int)"]
    assert load_coverage_map(out / "coverage-map.json").tests["a.HalfTest"].members == [
        "a.Price#half(int)"]
    assert (out / "checkout" / "pom.xml").is_file()


def test_build_failure_is_reported_as_warning(project, tmp_path, monkeypatch):
    spec = tmp_path / "failing.json"
    spec.write_text(json.dumps({"exit_code": 1, "tests": {}}), encoding="utf-8")
    monkeypatch.setenv("CODEDNA_FAKE_MVN_SPEC", str(spec))

    run, _ = run_maven_tests(project.path, "HEAD", tmp_path / "out", allow_build=True,
                             maven_command=FAKE_MVN)

    assert run.exit_codes == [1]
    assert any("Maven exited with 1" in w for w in run.warnings)


def test_output_directory_must_be_empty(project, tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "old.txt").write_text("x", encoding="utf-8")
    with pytest.raises(BuildError, match="not empty"):
        run_maven_tests(project.path, "HEAD", out, allow_build=True, maven_command=FAKE_MVN)


def test_project_without_root_pom_is_rejected(repo, tmp_path):
    repo.write("src/main/java/A.java", "class A {}\n")
    repo.commit("no pom")
    with pytest.raises(BuildError, match="no pom.xml"):
        run_maven_tests(repo.path, "HEAD", tmp_path / "out", allow_build=True,
                        maven_command=FAKE_MVN)


def test_missing_maven_is_reported(project, tmp_path, monkeypatch):
    monkeypatch.setattr("codedna_java.maven.shutil.which", lambda name: None)
    with pytest.raises(BuildError, match="Maven"):
        run_maven_tests(project.path, "HEAD", tmp_path / "out", allow_build=True)


def test_export_commit_writes_files_of_that_commit(repo, tmp_path):
    repo.write("a.txt", "one\n")
    first = repo.commit("one")
    repo.write("a.txt", "two\n")
    repo.commit("two")

    export_commit(repo.path, first, tmp_path / "export")

    assert (tmp_path / "export" / "a.txt").read_text(encoding="utf-8") == "one\n"
