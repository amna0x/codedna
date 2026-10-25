"""Tests for features (no leakage), metrics, rankers, ML models and evaluation."""

from __future__ import annotations

import json

import pytest

from codedna.cli import EXIT_OK, main
from codedna.models.evaluate import chronological_split, evaluate
from codedna.models.metrics import apfd, apfdc, recall_at_budget, time_to_first_failure
from codedna.models.rankers import MLRanker, order_by_baseline
from codedna.plugins import ENTRY_POINT_GROUP, load_plugins
from codedna.test_history.features import NEVER, Dataset, Row, build_dataset
from codedna.test_history.mining import mine_history
from codedna.test_history.store import HistoryStore

JUNIT5 = "import org.junit.jupiter.api.Test;\n"


# --- metrics -----------------------------------------------------------------------


def test_apfd_matches_the_textbook_formula():
    order = ["a", "b", "c", "d"]
    assert apfd(order, {"a"}) == pytest.approx(1 - 1 / 4 + 1 / 8)
    assert apfd(order, {"b", "d"}) == pytest.approx(1 - 6 / 8 + 1 / 8)
    assert apfd(order, set()) is None


def test_apfdc_weighs_test_cost():
    order = ["slow", "fail"]
    times = {"slow": 9.0, "fail": 1.0}
    assert apfdc(order, {"fail"}, times) == pytest.approx((1 - 0.5) / 10)
    assert apfdc(["fail", "slow"], {"fail"}, times) == pytest.approx((10 - 0.5) / 10)
    assert apfdc(order, {"fail"}, {"slow": 0, "fail": 0}) is None


def test_recall_at_budget_and_time_to_first_failure():
    order = ["a", "b", "c"]
    times = {"a": 1.0, "b": 1.0, "c": 2.0}
    assert recall_at_budget(order, {"b", "c"}, times, 0.5) == 0.5
    assert recall_at_budget(order, {"c"}, times, 0.25) == 0.0
    assert recall_at_budget(order, set(), times, 0.5) is None
    assert time_to_first_failure(order, {"c"}, times) == 1.0


# --- baselines and ML ----------------------------------------------------------------


def row(test, label=0, commit="c", **features):
    base = {"mean_duration": 1.0, "recent_failures": 0.0, "failure_rate": 0.0,
            "past_failures": 0.0}
    return Row(commit, 0, test, label, 1.0, {**base, **features})


def test_baseline_orderings():
    rows = [row("a", mean_duration=3.0, failure_rate=0.5, past_failures=2),
            row("b", mean_duration=1.0, recent_failures=2),
            row("c", mean_duration=2.0)]
    assert order_by_baseline("shortest_first", rows) == ["b", "c", "a"]
    assert order_by_baseline("recent_failures", rows) == ["b", "c", "a"]
    assert order_by_baseline("failure_history", rows) == ["a", "b", "c"]
    shuffled = order_by_baseline("random", rows)
    assert sorted(shuffled) == ["a", "b", "c"] and shuffled == order_by_baseline("random", rows)
    with pytest.raises(ValueError):
        order_by_baseline("nope", rows)


@pytest.mark.parametrize("name", ["logistic_regression", "gradient_boosting"])
def test_ml_rankers_learn_a_simple_signal(name):
    train = [Row(f"c{i}", i, f"t{j}", int(j == 0), 1.0, {"signal": float(j == 0), "noise": float(i % 3)})
             for i in range(30) for j in range(4)]
    model = MLRanker(name, ["signal", "noise"], seed=0)
    model.fit(train)
    test_rows = [Row("x", 99, f"t{j}", int(j == 2), 1.0, {"signal": float(j == 2), "noise": 1.0})
                 for j in range(4)]
    assert model.order(test_rows)[0] == "t2"
    probabilities = model.predict_proba(test_rows)
    assert all(0.0 <= p <= 1.0 for p in probabilities)


def test_ml_ranker_refuses_single_class_training_data():
    model = MLRanker("logistic_regression", ["f"])
    with pytest.raises(ValueError, match="both failing and passing"):
        model.fit([Row("c", 0, "t", 0, 1.0, {"f": 1.0})])


# --- features from a real (temporary) history ------------------------------------------


@pytest.fixture
def history(repo, tmp_path):
    """Five commits; a.CoreTest fails at commits 2 and 4, which change Core."""
    repo.write("src/main/java/a/Core.java", "package a;\npublic class Core { int v() { return 1; } }\n")
    repo.write("src/main/java/a/Other.java", "package a;\npublic class Other {}\n")
    repo.write("src/test/java/a/CoreTest.java",
               "package a;\n" + JUNIT5 + "class CoreTest { Core c; @Test void t() {} }\n")
    repo.write("src/test/java/a/OtherTest.java",
               "package a;\n" + JUNIT5 + "class OtherTest { Other o; @Test void t() {} }\n")
    shas = [repo.commit("c0")]
    for i in range(1, 5):
        target = "Core" if i % 2 == 0 else "Other"
        if target == "Core":
            repo.write("src/main/java/a/Core.java",
                       f"package a;\npublic class Core {{ int v() {{ return {i}; }} }}\n")
        else:
            repo.write("src/main/java/a/Other.java", f"package a;\npublic class Other {{ int x = {i}; }}\n")
        shas.append(repo.commit(f"c{i}"))

    store = HistoryStore(tmp_path / "h.db")
    mine_history(repo.path, store)
    for i, sha in enumerate(shas):
        store.add_result(sha, "a.CoreTest", "failed" if i in (2, 4) else "passed", 1.0 + i, "test")
        store.add_result(sha, "a.OtherTest", "passed", 0.5, "test")
    yield repo, store, shas
    store.close()


def features_of(dataset, sha, test):
    return next(r for r in dataset.rows if r.commit == sha and r.test_id == test)


def test_history_features_use_only_earlier_commits(history):
    repo, store, shas = history
    dataset = build_dataset(store, repo.path, structural=False)

    first_failure = features_of(dataset, shas[2], "a.CoreTest")
    assert first_failure.label == 1
    assert first_failure.features["past_failures"] == 0.0  # its own failure is not visible
    assert first_failure.features["commits_since_failure"] == NEVER
    assert first_failure.features["past_runs"] == 2.0
    assert first_failure.duration == 3.0  # cost only, not a feature

    after = features_of(dataset, shas[3], "a.CoreTest")
    assert after.features["past_failures"] == 1.0
    assert after.features["failed_last_run"] == 1.0
    assert after.features["commits_since_failure"] == 1.0
    assert after.features["mean_duration"] == pytest.approx((1 + 2 + 3) / 3)

    second_failure = features_of(dataset, shas[4], "a.CoreTest")
    assert second_failure.features["co_failures"] == 1.0  # Core.java changed when it failed before
    assert features_of(dataset, shas[4], "a.OtherTest").features["co_failures"] == 0.0


def test_structural_features_follow_the_dependency_graph(history):
    repo, store, shas = history
    dataset = build_dataset(store, repo.path, structural=True)

    core = features_of(dataset, shas[2], "a.CoreTest").features
    other = features_of(dataset, shas[2], "a.OtherTest").features
    assert (core["dep_reachable"], core["dep_distance"], core["dep_confirmed"]) == (1.0, 1.0, 1.0)
    assert (other["dep_reachable"], other["dep_distance"]) == (0.0, -1.0)
    assert features_of(dataset, shas[0], "a.CoreTest").features["dep_reachable"] == 0.0  # no parent


def test_too_few_failures_are_warned_about(history):
    repo, store, _ = history
    dataset = build_dataset(store, repo.path, structural=False)
    assert any("only 2 commit(s) with failing tests" in w for w in dataset.warnings)


def test_chronological_split_keeps_time_order():
    dataset = Dataset(rows=[], feature_names=[], commits=[f"c{i}" for i in range(10)])
    splits = chronological_split(dataset)
    assert splits == {"train": [f"c{i}" for i in range(6)], "validation": ["c6", "c7"],
                      "test": ["c8", "c9"]}


def test_evaluate_reports_baselines_and_untrainable_models(history):
    repo, store, _ = history
    dataset = build_dataset(store, repo.path, structural=False)

    report = evaluate(dataset, rankers=["shortest_first", "failure_history", "logistic_regression"])

    assert report["protocol"]["splits"] == {"train": 3, "validation": 1, "test": 1}
    test_split = report["results"]["test"]
    assert test_split["commits_with_failures"] == 1
    assert test_split["rankers"]["failure_history"]["mean_apfd"] == pytest.approx(0.75)
    assert test_split["rankers"]["shortest_first"]["mean_apfd"] == pytest.approx(0.25)
    assert "logistic_regression" in report["results"]["test"]["rankers"]  # train has 1 failure
    with pytest.raises(ValueError, match="unknown rankers"):
        evaluate(dataset, rankers=["magic"])


def test_history_evaluate_command(history, tmp_path, capsys):
    repo, store, _ = history
    csv_path = tmp_path / "dataset.csv"

    code = main(["history", "evaluate", "--db", str(store.path), "--repo", str(repo.path),
                 "--no-structural", "--rankers", "random", "recent_failures",
                 "--dataset-csv", str(csv_path)])

    assert code == EXIT_OK
    report = json.loads(capsys.readouterr().out)
    assert set(report["results"]["test"]["rankers"]) == {"random", "recent_failures"}
    assert csv_path.read_text(encoding="utf-8").splitlines()[0].startswith("commit,seq,test_id,label")


# --- plugins -----------------------------------------------------------------------------


def test_java_plugin_is_found_through_its_entry_point():
    registry = load_plugins()
    java = registry.get("java")
    assert java.handles("src/A.java") and not java.handles("README.md")
    assert registry.for_path("x/B.java") is java
    assert registry.describe()["plugins"][0]["name"] == "java"
    assert "class" in java.type_kinds and "method" not in java.type_kinds


def test_incompatible_and_broken_plugins_are_rejected(monkeypatch):
    class Old:
        name, display_name, version, api_version, file_suffixes = "old", "Old", "1", "0.9", (".old",)
        type_kinds = frozenset({"class"})

        def handles(self, path): return path.endswith(".old")
        def parse(self, source): ...
        def attach_declarations(self, report): ...
        def build_graph(self, repo, commit, **kw): ...
        def discover_tests(self, repo, commit): ...
        def run_tests(self, *a, **kw): ...

    class EntryPoint:
        def __init__(self, name, factory):
            self.name, self._factory = name, factory

        def load(self):
            if self._factory is None:
                raise ImportError("missing module")
            return self._factory

    class Newer(Old):
        name, api_version = "newer", "1.9"  # needs members a 1.1 core may not have

    class Current(Old):
        name, api_version = "current", "1.0"  # older minor: still compatible

    fake = [EntryPoint("old", Old), EntryPoint("broken", None), EntryPoint("junk", object),
            EntryPoint("newer", Newer), EntryPoint("current", Current)]
    monkeypatch.setattr("codedna.plugins.registry.entry_points",
                        lambda group: fake if group == ENTRY_POINT_GROUP else [])

    registry = load_plugins()

    assert list(registry.plugins) == ["current"]
    problems = " ".join(registry.problems)
    assert "newer: plugin API 1.9 is incompatible" in problems
    assert "incompatible" in problems and "failed to load" in problems and "does not implement" in problems


def test_plugins_command(capsys):
    assert main(["plugins"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["plugins"][0]["name"] == "java"
