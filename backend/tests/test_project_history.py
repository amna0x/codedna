"""Saved runs browsed and added to the recorded project history (D-057), on temporary Git repositories."""

from __future__ import annotations

import json
import os

import pytest
from fastapi.testclient import TestClient

from codedna.api.app import create_app
from codedna.git_analysis.git import CodeDNAGitError
from codedna.test_history.features import Dataset
from codedna.test_history.project import (ProjectHistoryError, import_run, list_runs,
                                          record_saved_runs, run_detail)
from codedna.test_history.recording import HISTORY_CSV, record_run
from codedna.test_mapping.results import TestClassResult, TestRunResult

TOKEN = "t" * 32
AUTH = {"X-CodeDNA-Token": TOKEN}
CORE = "package a; public class Core { int value() { return 1; } }"
TESTS = ("a.ATest", "a.BTest")


@pytest.fixture
def project(repo):
    repo.write("pom.xml", "<project/>")
    repo.write("src/main/java/a/Core.java", CORE)
    for name in ["ATest", "BTest"]:
        repo.write(f"src/test/java/a/{name}.java",
                   f"package a; import org.junit.jupiter.api.Test; class {name} {{ @Test void x() {{}} }}")
    first = repo.commit("tests")
    repo.write("src/main/java/a/Core.java", CORE.replace("return 1", "return 2"))
    second = repo.commit("value 2")
    return repo, first, second


def run_of(repo, commit, tests=TESTS, failing=(), exit_codes=(0,)):
    return TestRunResult(
        repository=str(repo.path.resolve()), commit=commit, tool="maven", commands=[],
        exit_codes=list(exit_codes), duration_seconds=2.0, per_test_coverage=False,
        tests={t: TestClassResult(t, "failed" if t in failing else "passed", 1.0, [])
               for t in tests})


_order = [0]


def save(repo, run_id, run_or_text):
    folder = repo.path / ".codedna/runs" / run_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "results.json"
    text = run_or_text if isinstance(run_or_text, str) else json.dumps(run_or_text.to_dict())
    path.write_text(text, encoding="utf-8")
    _order[0] += 1  # distinct modification times give a fixed oldest-first order
    os.utime(path, ns=(10**18 + _order[0] * 10**9,) * 2)
    return folder


def test_failing_runs_are_evidence_and_partial_ones_are_not(project):
    repo, first, second = project
    # A test failure makes Maven exit non-zero; that run is still complete evidence.
    save(repo, "complete", run_of(repo, first))
    save(repo, "failing", run_of(repo, second, failing=["a.BTest"], exit_codes=[1]))
    save(repo, "partial", run_of(repo, second, tests=["a.ATest"]))
    save(repo, "broken", "{not json")
    runs = {r["id"]: r for r in list_runs(repo.path)["runs"]}
    assert runs["complete"]["candidate"] and runs["failing"]["candidate"]
    assert not runs["partial"]["candidate"] and "a.BTest" in runs["partial"]["reason"]
    assert not runs["broken"]["candidate"] and "unreadable" in runs["broken"]["reason"]


def test_saved_runs_join_the_one_recorded_history(project):
    repo, first, second = project
    # The IDE recorded the first commit already (D-053) ...
    assert record_run(repo.path, run_of(repo, first), expected_tests=list(TESTS))["recorded"]
    # ... and a later failing run was only saved (e.g. before recording existed).
    save(repo, "later", run_of(repo, second, failing=["a.BTest"], exit_codes=[1]))
    report = record_saved_runs(repo.path)
    assert report["recorded_runs"] == 1 and report["commits_with_results"] == 2
    dataset = Dataset.from_csv(repo.path / HISTORY_CSV)
    assert dataset.commits == [first, second]
    labels = {(r.commit, r.test_id): r.label for r in dataset.rows}
    assert labels[(second, "a.BTest")] == 1 and labels[(first, "a.BTest")] == 0
    # Recording again is idempotent and the CSV stays CodeDNA's own, so D-053 keeps working.
    assert record_saved_runs(repo.path)["commits_with_results"] == 2
    assert record_run(repo.path, run_of(repo, first), expected_tests=list(TESTS))["recorded"]
    assert repo.git("status", "--porcelain") == ""
    assert not (repo.path / ".git/info/exclude").read_text().count(".codedna")


def test_history_written_elsewhere_is_left_alone(project):
    repo, first, _ = project
    csv = repo.path / HISTORY_CSV
    csv.parent.mkdir()
    csv.write_text("demo history\n")
    save(repo, "run", run_of(repo, first))
    report = record_saved_runs(repo.path)
    assert report["recorded_runs"] == 0
    assert any("left unchanged" in s["reason"] for s in report["skipped"])
    assert csv.read_text() == "demo history\n"


def test_other_repositories_and_branches_are_refused(project, tmp_path):
    repo, first, _ = project
    repo.git("checkout", "--quiet", "-b", "side")
    repo.write("src/main/java/a/Core.java", CORE.replace("return 1", "return 9"))
    side = repo.commit("side")
    repo.git("checkout", "--quiet", "-")
    save(repo, "side", run_of(repo, side))
    foreign = run_of(repo, first)
    foreign.repository = str(tmp_path / "elsewhere")
    save(repo, "foreign", foreign)
    runs = {r["id"]: r for r in list_runs(repo.path)["runs"]}
    assert "another repository" in runs["foreign"]["reason"]
    assert "first-parent" in runs["side"]["reason"]
    assert record_saved_runs(repo.path)["recorded_runs"] == 0
    assert not (repo.path / HISTORY_CSV).exists()


def test_import_binds_a_clones_run_but_not_another_project(project, tmp_path):
    repo, first, _ = project
    clone_run = run_of(repo, first)
    clone_run.repository = str(tmp_path / "clone")
    source = tmp_path / "clone-results.json"
    source.write_text(json.dumps(clone_run.to_dict()))
    imported = import_run(repo.path, source)
    detail = run_detail(repo.path, imported["id"])
    assert detail["results"]["repository"] == str(repo.path.resolve())
    record = json.loads((repo.path / ".codedna/runs" / imported["id"] / "record.json").read_text())
    assert record["source_repository"] == str(tmp_path / "clone")
    assert record_saved_runs(repo.path)["recorded_runs"] == 1
    clone_run.commit = "f" * 40  # a commit this repository does not have
    source.write_text(json.dumps(clone_run.to_dict()))
    with pytest.raises(CodeDNAGitError):
        import_run(repo.path, source)


def test_run_detail_rejects_bad_identifiers(project):
    repo, _, _ = project
    for bad in ["../x", "a/b", ""]:
        with pytest.raises(ProjectHistoryError):
            run_detail(repo.path, bad)


def test_api_lists_and_records(project):
    repo, first, _ = project
    save(repo, "run", run_of(repo, first))
    api = TestClient(create_app(TOKEN), base_url="http://127.0.0.1")
    listed = api.post("/api/project-history", headers=AUTH, json={"repo": str(repo.path)})
    assert listed.status_code == 200 and listed.json()["candidate_runs"] == 1
    recorded = api.post("/api/project-history/record", headers=AUTH, json={"repo": str(repo.path)})
    assert recorded.status_code == 200 and recorded.json()["recorded_runs"] == 1
    bad = api.post("/api/project-history/run", headers=AUTH,
                   json={"repo": str(repo.path), "run_id": "../x"})
    assert bad.status_code == 400
    assert api.post("/api/project-history", json={"repo": str(repo.path)}).status_code in (401, 403)


def test_cli_records_saved_runs(project, capsys):
    from codedna.cli import EXIT_ANALYSIS_ERROR, EXIT_OK, main
    repo, first, _ = project
    assert main(["history", "record", "--repo", str(repo.path), "--saved"]) == EXIT_ANALYSIS_ERROR
    capsys.readouterr()
    save(repo, "run", run_of(repo, first))
    assert main(["history", "record", "--repo", str(repo.path), "--saved"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["recorded_runs"] == 1
