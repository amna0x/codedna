"""Full-suite runs recorded as project history (D-053), on temporary Git repositories."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from codedna.api.app import create_app
from codedna.cli import EXIT_ANALYSIS_ERROR, EXIT_OK, main
from codedna.git_analysis.git import run_git, snapshot_worktree
from codedna.test_history.features import Dataset
from codedna.test_history.recording import HISTORY_CSV, record_run
from codedna.test_mapping.reports import TestClassResult
from codedna.test_mapping.results import TestRunResult

FAKE = [sys.executable, str(Path(__file__).with_name("fake_mvn.py"))]
TOKEN = "t" * 32
AUTH = {"X-CodeDNA-Token": TOKEN}
CORE = "package a; public class Core { int value() { return 1; } }"


@pytest.fixture
def project(repo, tmp_path, monkeypatch):
    repo.write("pom.xml", "<project/>")
    repo.write("src/main/java/a/Core.java", CORE)
    for name in ["ATest", "BTest"]:
        repo.write(f"src/test/java/a/{name}.java",
                   f"package a; import org.junit.jupiter.api.Test; class {name} {{ @Test void x() {{}} }}")
    base = repo.commit("tests")
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"exit_code": 1, "tests": {
        "a.ATest": {"status": "passed", "time": 1.0, "cases": ["x"]},
        "a.BTest": {"status": "failed", "time": 2.0, "cases": ["x"]}}}))
    monkeypatch.setenv("CODEDNA_FAKE_MVN_SPEC", str(spec))
    return repo, base


def run_selection(repo, base, head, strategy="all"):
    api = TestClient(create_app(TOKEN, allow_build=True, maven_command=FAKE),
                     base_url="http://127.0.0.1")
    response = api.post("/api/run-selection", headers=AUTH, json={
        "repo": str(repo.path), "base": base, "head": head, "strategy": strategy,
        "allow_build": True})
    assert response.status_code == 200, response.text
    return response.json()


def fake_run(commit, tests=("a.ATest", "a.BTest")):
    return TestRunResult(repository="r", commit=commit, tool="maven", commands=[],
                         exit_codes=[0], duration_seconds=1.0, per_test_coverage=False,
                         tests={t: TestClassResult(t, "passed", 1.0, []) for t in tests})


def change(repo, value):
    repo.write("src/main/java/a/Core.java", CORE.replace("return 1", f"return {value}"))
    return repo.commit(f"value {value}")


def test_full_suite_runs_build_history_commit_by_commit(project):
    repo, base = project
    first = run_selection(repo, base, base)
    assert first["recording"]["recorded"] is True
    head = change(repo, 2)
    assert repo.git("status", "--porcelain") == ""  # outputs are ignored, not committed
    second = run_selection(repo, base, head, strategy="risk")
    assert second["recording"]["commits_with_results"] == 2
    dataset = Dataset.from_csv(repo.path / HISTORY_CSV)
    assert dataset.commits == [base, head]
    rows = {(r.commit, r.test_id): r.label for r in dataset.rows}
    assert rows[(head, "a.BTest")] == 1 and rows[(head, "a.ATest")] == 0
    # Past outcomes are history features of later rows only (no leakage).
    later = next(r for r in dataset.rows if r.commit == head and r.test_id == "a.BTest")
    assert later.features["past_failures"] == 1.0


def test_selected_runs_are_not_recorded(project):
    repo, base = project
    repo.write("src/test/java/a/ATest.java",
               "package a; import org.junit.jupiter.api.Test; class ATest { @Test void y() {} }")
    head = repo.commit("edit ATest")
    result = run_selection(repo, base, head, strategy="dependency")
    assert result["selection"]["skipped"]
    assert result["recording"]["recorded"] is False
    assert "complete outcomes" in result["recording"]["reason"]
    assert not (repo.path / HISTORY_CSV).exists()


def test_incomplete_or_off_branch_runs_are_refused(project):
    repo, base = project
    report = record_run(repo.path, fake_run(base, ["a.ATest"]),
                        expected_tests=["a.ATest", "a.BTest"])
    assert not report["recorded"] and "a.BTest" in report["reason"]
    repo.git("checkout", "--quiet", "-b", "side")
    side = change(repo, 5)
    repo.git("checkout", "--quiet", "-")
    report = record_run(repo.path, fake_run(side), expected_tests=["a.ATest", "a.BTest"])
    assert not report["recorded"] and "first-parent" in report["reason"]
    assert not (repo.path / ".codedna/history.db").exists()


def test_history_written_elsewhere_is_never_overwritten(project):
    repo, base = project
    csv = repo.path / HISTORY_CSV
    csv.parent.mkdir()
    csv.write_text("demo history\n")
    report = record_run(repo.path, fake_run(base), expected_tests=["a.ATest", "a.BTest"])
    assert not report["recorded"] and "left unchanged" in report["reason"]
    assert csv.read_text() == "demo history\n"
    # Also after CodeDNA once recorded: a hand-edited file stays untouched.
    csv.unlink()
    assert record_run(repo.path, fake_run(base), expected_tests=["a.ATest"])["recorded"]
    csv.write_text("edited\n")
    assert not record_run(repo.path, fake_run(base), expected_tests=["a.ATest"])["recorded"]
    assert csv.read_text() == "edited\n"


def test_snapshot_leaves_out_codedna_outputs_only(repo):
    repo.write("a.txt", "one\n")
    repo.commit("base")
    for name in [".codedna/runs/x/results.json", ".codedna/history.db", ".codedna/history.csv"]:
        repo.write(name, "output\n")
    repo.write(".codedna/policy.toml", "[[must_run]]\ntests = ['a.T']\n")
    repo.write("b.txt", "new\n")
    snapshot = snapshot_worktree(repo.path)
    names = run_git(repo.path, "diff", "--name-only", "HEAD", snapshot).split()
    assert names == [".codedna/policy.toml", "b.txt"]


def test_snapshot_and_ignore_file_list_the_same_outputs():
    from codedna.git_analysis import git
    from codedna.test_history import recording
    assert {p.removeprefix(".codedna/") for p in git._OUTPUTS} == \
        {name.rstrip("/") for name in recording.OUTPUTS}


def test_snapshot_works_once_outputs_are_ignored(repo):
    from codedna.test_history.recording import ignore_outputs
    repo.write("a.txt", "one\n")
    repo.commit("base")
    ignore_outputs(repo.path)
    repo.write(".codedna/runs/x/results.json", "output\n")
    repo.write("b.txt", "new\n")
    snapshot = snapshot_worktree(repo.path)  # used to fail: exclude pathspec on an ignored path
    assert run_git(repo.path, "diff", "--name-only", "HEAD", snapshot).split() == ["b.txt"]


def test_cli_records_a_saved_run(project, tmp_path, capsys):
    repo, base = project
    results = tmp_path / "results.json"
    results.write_text(json.dumps(fake_run(base).to_dict()))
    assert main(["history", "record", "--repo", str(repo.path), str(results)]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["recorded"] is True
    results.write_text(json.dumps(fake_run(base, ["a.ATest"]).to_dict()))
    assert main(["history", "record", "--repo", str(repo.path), str(results)]) == EXIT_ANALYSIS_ERROR
