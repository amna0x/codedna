"""Target-validation gate for calibrated stopping (D-041)."""

from __future__ import annotations

import json

import pytest

from codedna.cli import EXIT_OK, main
from codedna.selection.gate import GateConfig, assess_change, gated_decision, validate
from codedna.test_history.features import build_dataset, change_rows
from codedna.test_history.mining import mine_history
from codedna.test_history.store import HistoryStore
from test_history import run_result
from test_risk_calibration import synthetic_dataset

pytest.importorskip("sklearn")


def test_enough_clean_evidence_validates():
    gate = validate(synthetic_dataset(commits=200))
    assert gate.validated, gate.report.reasons
    evidence = gate.report.evidence["validation"]
    assert evidence["observed_miss_rate"] <= 0.05
    assert evidence["observed_miss_rate_95ci"][1] <= 0.10
    assert gate.report.validated_through == "c199"


def test_too_little_evidence_is_unvalidated_with_reasons():
    gate = validate(synthetic_dataset(commits=30))
    assert not gate.validated
    assert any("validation slice has" in r for r in gate.report.reasons)
    assert gate.ranker is None


def test_weak_evidence_fails_on_the_upper_bound():
    # Enough failing commits but too few validation commits for a tight interval.
    gate = validate(synthetic_dataset(commits=120), GateConfig(min_validation_commits=10))
    assert not gate.validated
    assert any("upper bound" in r for r in gate.report.reasons)


def test_no_failures_at_all_is_unvalidated():
    gate = validate(synthetic_dataset(commits=200, failures=False))
    assert not gate.validated
    assert "no failing commits in the training history" in gate.report.reasons


def rows_for(commit_index=199):
    dataset = synthetic_dataset(commits=200)
    return [r for r in dataset.rows if r.commit == f"c{commit_index}"]


def test_gated_decision_runs_everything_unless_validated_and_fresh():
    validated = validate(synthetic_dataset(commits=200))
    rows = rows_for()
    decision, probabilities = gated_decision(validated, rows, commits_since_full_run=1)
    assert not decision.fallback and len(decision.selected) < len(rows)
    assert decision.reasons[0] == "risk validated on this project's earlier history"
    assert len(probabilities) == len(rows)

    stale, _ = gated_decision(validated, rows, commits_since_full_run=51)
    assert stale.fallback and len(stale.selected) == len(rows)
    assert "evidence stale" in stale.reasons[0]

    unknown, _ = gated_decision(validated, rows, commits_since_full_run=None)
    assert unknown.fallback

    unvalidated = validate(synthetic_dataset(commits=30))
    full, probabilities = gated_decision(unvalidated, rows, commits_since_full_run=0)
    assert full.fallback and "risk unvalidated" in full.reasons[0]
    assert probabilities is None


def test_non_java_change_runs_everything():
    gate = validate(synthetic_dataset(commits=200))
    rows = rows_for()
    for r in rows:
        r.features["non_java_files_changed"] = 1.0
    decision, _ = gated_decision(gate, rows, commits_since_full_run=0)
    assert decision.fallback and "non-Java" in decision.reasons[0]


def small_history(repo, tmp_path, commits=6):
    shas = []
    for i in range(commits):
        repo.write("src/main/java/a/A.java", f"package a; class A {{ int v = {i}; }}\n")
        shas.append(repo.commit(f"c{i}"))
    store = HistoryStore(tmp_path / "h.db")
    mine_history(repo.path, store)
    for i, sha in enumerate(shas):
        store.add_run(run_result(sha, {"a.ATest": "failed" if i % 2 else "passed",
                                       "a.BTest": "passed"}), "test")
    return store, shas


def test_change_rows_use_all_history_and_no_labels(repo, tmp_path):
    store, shas = small_history(repo, tmp_path)
    repo.write("src/main/java/a/A.java", "package a; class A { int v = 99; }\n")
    head = repo.commit("new change")
    rows = change_rows(store, shas[-1], head, structural=False)
    by_test = {r.test_id: r for r in rows}
    assert set(by_test) == {"a.ATest", "a.BTest"}
    assert by_test["a.ATest"].features["past_runs"] == 6
    assert by_test["a.ATest"].features["past_failures"] == 3
    assert by_test["a.ATest"].features["java_files_changed"] == 1
    assert all(r.label == 0 for r in rows)
    # Same history features as the dataset would give the next commit.
    dataset = build_dataset(store, structural=False)
    assert len(dataset.rows) == 12
    store.close()


def test_assess_change_and_cli_report_unvalidated_history(repo, tmp_path, capsys):
    store, shas = small_history(repo, tmp_path)
    report = assess_change(store, shas[-2], shas[-1], structural=False)
    store.close()
    assert report["gate"]["status"] == "unvalidated"
    assert report["decision"]["mode"] == "full_suite"
    assert report["decision"]["estimated_skip_risk"] is None
    assert sorted(report["decision"]["selected"]) == ["a.ATest", "a.BTest"]
    assert report["commits_since_full_run"] == 1  # evidence ends at the base

    code = main(["history", "risk", "--db", str(tmp_path / "h.db"), "--base", shas[-2],
                 "--head", shas[-1], "--no-structural"])
    assert code == EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["decision"]["mode"] == "full_suite"
    assert "risk unvalidated" in out["decision"]["reasons"][0]


def test_evidence_age_counts_commits_after_the_newest_result(repo, tmp_path):
    store, shas = small_history(repo, tmp_path)
    repo.write("src/main/java/a/A.java", "package a; class A { int v = 7; }\n")
    repo.commit("untested 1")
    repo.write("src/main/java/a/A.java", "package a; class A { int v = 8; }\n")
    head = repo.commit("untested 2")
    report = assess_change(store, shas[-1], head, structural=False)
    store.close()
    assert report["gate"]["validated_through"] == shas[-1]
    assert report["commits_since_full_run"] == 2


def test_only_the_base_and_its_ancestors_are_used(repo, tmp_path):
    store, shas = small_history(repo, tmp_path)
    report = assess_change(store, shas[2], shas[3], structural=False)
    rows = change_rows(store, shas[2], shas[3], structural=False,
                       only={s for s in shas[:3]})
    store.close()
    # Results stored for shas[3] (the change) and later must not be history.
    assert report["gate"]["validated_through"] == shas[2]
    assert report["gate"]["evidence"]["history_commits"] == 3
    assert {r.test_id: r.features["past_runs"] for r in rows} == {"a.ATest": 3, "a.BTest": 3}


def test_candidates_are_the_tests_at_head_including_new_ones(repo, tmp_path):
    store, shas = small_history(repo, tmp_path)
    repo.write("src/test/java/a/NewTest.java",
               "package a;\nimport org.junit.jupiter.api.Test;\nclass NewTest { @Test void t() {} }\n")
    head = repo.commit("add a test")
    report = assess_change(store, shas[-1], head, structural=False)
    store.close()
    assert [t["test"] for t in report["tests"]] == ["a.NewTest"]  # only tests present at head
    assert report["decision"]["selected"] == ["a.NewTest"]


def test_tests_without_history_always_run_when_validated():
    gate = validate(synthetic_dataset(commits=200))
    rows = rows_for()
    for r in rows:
        if r.test_id == "t5":
            r.features["past_runs"] = 0.0
            r.features["recent_failures"] = 0.0
    decision, _ = gated_decision(gate, rows, commits_since_full_run=0)
    assert not decision.fallback
    assert "t5" in decision.selected
    assert any("without history always run" in r for r in decision.reasons)
