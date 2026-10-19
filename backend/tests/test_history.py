"""Tests for history mining, the result store, import and collection (Milestone 4)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from codedna.cli import EXIT_ANALYSIS_ERROR, EXIT_OK, main
from codedna.git_analysis import CodeDNAGitError
from codedna.test_history.collection import collect_results, import_results
from codedna.test_history.mining import mine_history
from codedna.test_history.store import HistoryStore
from codedna.test_mapping.reports import TestCaseResult, TestClassResult
from codedna.test_mapping.results import TestRunResult, save_json

FAKE_MVN = [sys.executable, str(Path(__file__).with_name("fake_mvn.py"))]


@pytest.fixture
def store(tmp_path):
    with HistoryStore(tmp_path / "history.db") as db:
        yield db


def run_result(sha, outcomes):
    run = TestRunResult(repository="r", commit=sha, tool="maven", commands=[], exit_codes=[0],
                        duration_seconds=1.0, per_test_coverage=False)
    for test_id, status in outcomes.items():
        result = TestClassResult(test_id)
        result.add(TestCaseResult("t", status, 0.5))
        run.tests[test_id] = result
    return run


def test_mine_first_parent_history_in_order(repo, store):
    repo.write("a.txt", "1\n")
    first = repo.commit("one")
    repo.git("checkout", "-q", "-b", "feature")
    repo.write("b.txt", "feature\n")
    repo.commit("feature work")
    repo.git("checkout", "-q", "-")
    repo.write("a.txt", "1\n2\n")
    second = repo.commit("two")
    repo.git("merge", "-q", "--no-ff", "-m", "merge feature", "feature")
    merge = repo.git("rev-parse", "HEAD")

    commits = mine_history(repo.path, store)

    assert [c.sha for c in commits] == [first, second, merge]  # feature commit not first-parent
    assert [c.seq for c in store.commits()] == [0, 1, 2]
    assert store.commits()[2].parent == second
    assert [(f.path, f.added, f.deleted) for f in store.changed_files(second)] == [("a.txt", 1, 0)]
    assert [f.path for f in store.changed_files(merge)] == ["b.txt"]  # diff vs first parent
    assert store.get_meta("mined_tip") == merge


def test_mine_limits_and_binary_files(repo, store):
    repo.write("a.txt", "1\n")
    repo.commit("one")
    repo.write_bytes("img.bin", b"\x00\x01")
    two = repo.commit("two")
    repo.write("a.txt", "2\n")
    three = repo.commit("three")

    commits = mine_history(repo.path, store, max_commits=2)

    assert [c.sha for c in commits] == [two, three]
    assert store.changed_files(two)[0].added is None  # binary


def test_failure_from_any_source_wins(store):
    store.add_result("c1", "a.T", "passed", 1.0, "ci")
    store.add_result("c1", "a.T", "failed", 1.0, "rerun")
    store.add_result("c1", "a.U", "passed", 2.0, "ci")

    results = {r.test_id: r for r in store.results("c1")}
    assert results["a.T"].failed and not results["a.U"].failed


def test_import_results_and_warn_about_unknown_commits(repo, store, tmp_path):
    repo.write("a.txt", "1\n")
    sha = repo.commit("one")
    mine_history(repo.path, store)
    save_json(run_result(sha, {"a.T": "failed", "a.U": "passed"}).to_dict(), tmp_path / "r1" / "results.json")
    save_json(run_result("f" * 40, {"a.T": "passed"}).to_dict(), tmp_path / "r2.json")

    summary = import_results(store, [tmp_path / "r1", tmp_path / "r2.json"])

    assert summary["rows"] == 3
    assert any("not in the mined history" in w for w in summary["warnings"])
    assert store.summary()["commits_with_failures"] == 1


def test_collect_requires_allow_build(repo, store, tmp_path):
    with pytest.raises(CodeDNAGitError, match="--allow-build"):
        collect_results(repo.path, store, tmp_path / "runs", allow_build=False)


def test_collect_runs_each_commit_once(repo, store, tmp_path, monkeypatch):
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"tests": {"a.T": {"status": "passed", "time": 0.5}}}), encoding="utf-8")
    monkeypatch.setenv("CODEDNA_FAKE_MVN_SPEC", str(spec))
    repo.write("pom.xml", "<project/>\n")
    repo.commit("one")
    repo.write("a.txt", "x\n")
    repo.commit("two")
    mine_history(repo.path, store)

    first = collect_results(repo.path, store, tmp_path / "runs", allow_build=True,
                            max_commits=1, maven_command=FAKE_MVN)
    second = collect_results(repo.path, store, tmp_path / "runs", allow_build=True,
                             maven_command=FAKE_MVN)

    assert (first["collected"], first["remaining"]) == (1, 1)
    assert (second["collected"], second["remaining"]) == (1, 0)
    assert len(store.commits_with_results()) == 2


def test_history_cli_mine_import_status(repo, tmp_path, capsys):
    repo.write("a.txt", "1\n")
    sha = repo.commit("one")
    db = tmp_path / "h.db"
    save_json(run_result(sha, {"a.T": "passed"}).to_dict(), tmp_path / "run" / "results.json")

    assert main(["history", "mine", "--repo", str(repo.path), "--db", str(db)]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["mined_commits"] == 1
    assert main(["history", "import", "--db", str(db), str(tmp_path / "run")]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["rows"] == 1
    assert main(["history", "status", "--db", str(db)]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["commits_with_results"] == 1

    assert main(["history", "collect", "--repo", str(repo.path), "--db", str(db),
                 "--output-dir", str(tmp_path / "runs")]) == EXIT_ANALYSIS_ERROR
    assert "--allow-build" in capsys.readouterr().err
    assert main(["history", "status", "--db", str(tmp_path / "missing.db")]) == EXIT_ANALYSIS_ERROR
