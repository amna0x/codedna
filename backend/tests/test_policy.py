"""Must-run (pinned) tests policy (D-050), on temporary Git repositories."""

from __future__ import annotations

import json

import pytest

import codedna.selection.policy as policy
from codedna.cli import EXIT_OK, main
from codedna.selection import compare_strategies, select_tests
from codedna.selection.policy import POLICY_FILE, apply_policy
from codedna.selection.risk import RiskPolicy, decide
from codedna.test_history.features import Row
from test_selection import CORE, FILES, commit, results

PIN_OTHER = '[[must_run]]\ntests = ["a.OtherTest"]\nreason = "release checks"\n'


def change(repo, policy_text=None, head_files=None):
    files = dict(FILES)
    if policy_text is not None:
        files[POLICY_FILE] = policy_text
    base = commit(repo, files, "base")
    edits = {"src/main/java/a/Core.java": CORE.replace("return 1;", "return 11;")}
    head = commit(repo, {**edits, **(head_files or {})}, "change Core#one")
    return base, head


def reasons(report, test):
    return next(item.reasons for item in report.selected if item.test == test)


def test_without_policy_selection_is_unchanged(repo):
    base, head = change(repo)
    report = select_tests(repo.path, base, head, "dependency")
    assert sorted(report.selected_ids) == ["a.OneTest", "a.TwoTest"]
    assert report.policy == {"pinned": [], "source": None}


def test_base_policy_pins_tests_the_strategy_would_skip(repo):
    base, head = change(repo, PIN_OTHER)
    report = select_tests(repo.path, base, head, "dependency")
    assert sorted(report.selected_ids) == ["a.OneTest", "a.OtherTest", "a.TwoTest"]
    assert reasons(report, "a.OtherTest") == ["must-run: release checks"]
    assert report.policy["pinned"] == ["a.OtherTest"]
    assert report.policy["source"].startswith(POLICY_FILE)


def test_patterns_match_and_unmatched_patterns_warn(repo):
    base, head = change(repo, '[[must_run]]\ntests = ["a.O*Test", "a.Missing*"]\n')
    report = select_tests(repo.path, base, head, "dependency")
    assert report.policy["pinned"] == ["a.OneTest", "a.OtherTest"]
    assert reasons(report, "a.OtherTest") == ["must-run: listed in the project policy"]
    assert any("'a.Missing*' matches no test" in w for w in report.warnings)


def test_a_change_cannot_loosen_or_tighten_its_own_policy(repo):
    base, head = change(repo, PIN_OTHER, {POLICY_FILE: '[[must_run]]\ntests = ["a.TwoTest"]\n'})
    report = select_tests(repo.path, base, head, "dependency")
    assert report.policy["pinned"] == ["a.OtherTest"]
    assert any("BASE policy is used" in w for w in report.warnings)


def test_policy_removed_in_the_change_still_applies(repo):
    base, _ = change(repo, PIN_OTHER)
    repo.git("rm", "--quiet", POLICY_FILE)
    head = repo.commit("drop policy")
    report = select_tests(repo.path, base, head, "dependency")
    assert "a.OtherTest" in report.selected_ids
    assert any("edits .codedna/policy.toml" in w for w in report.warnings)


@pytest.mark.parametrize("text", [
    "[[must_run]\ntests = [",                          # not TOML
    '[must_run]\ntests = ["a.OtherTest"]\n',            # table instead of [[...]]
    '[[must_run]]\ntests = []\n',                       # empty list
    '[[must_run]]\ntests = ["a.OtherTest"]\nskip = 1\n',  # unknown key
    '[ignore]\ntests = ["a.OtherTest"]\n',              # unknown section
])
def test_unreadable_policy_pins_every_test(repo, text):
    base, head = change(repo, text)
    report = select_tests(repo.path, base, head, "dependency")
    assert report.skipped == []
    assert all("nothing may be skipped" in " ".join(item.reasons) for item in report.selected)
    assert any("every test is pinned" in w for w in report.warnings)


def test_request_patterns_add_to_the_project_policy(repo, capsys):
    base, head = change(repo)
    assert main(["select", "--repo", str(repo.path), "--base", base, "--head", head,
                 "--strategy", "dependency", "--must-run", "a.OtherTest"]) == EXIT_OK
    out = json.loads(capsys.readouterr().out)
    other = next(i for i in out["selected"] if i["test"] == "a.OtherTest")
    assert other["reasons"] == ["must-run: pinned by request"]


def test_compare_measures_baselines_without_the_policy(repo):
    base, head = change(repo, PIN_OTHER)
    truth = results(head, {"a.OneTest": ("passed", 1.0), "a.TwoTest": ("passed", 1.0),
                           "a.OtherTest": ("failed", 1.0)})
    rows = {r["strategy"]: r for r in compare_strategies(repo.path, base, head, truth)["strategies"]}
    assert rows["dependency"]["missed"] == ["a.OtherTest"]


def test_installed_rules_add_pins_and_fail_safe(repo, monkeypatch):
    base, head = change(repo)

    class Rule:
        name = "security"

        def pinned(self, context):
            assert "src/main/java/a/Core.java" in context.changed_paths
            return {"a.OtherTest": "touches payment code", "a.Unknown": "ignored"}

    class Entry:
        def __init__(self, name, factory):
            self.name, self.load = name, lambda: factory

    def broken():
        raise RuntimeError("bad add-on")

    monkeypatch.setattr(policy, "installed_rules", lambda: [Entry("security", Rule)])
    report = select_tests(repo.path, base, head, "dependency")
    assert reasons(report, "a.OtherTest") == ["security: touches payment code"]
    assert report.policy["pinned"] == ["a.OtherTest"]

    class NotADict:
        name = "odd"

        def pinned(self, context):
            return None

    for name, factory in [("broken", broken), ("odd", NotADict)]:
        monkeypatch.setattr(policy, "installed_rules", lambda: [Entry(name, factory)])
        result = apply_policy(repo.path, base, head, ["a.OneTest", "a.OtherTest"], set())
        assert sorted(result.pinned) == ["a.OneTest", "a.OtherTest"]
        assert any(f"'{name}' failed" in w for w in result.warnings)


def test_decide_counts_pinned_tests_as_run():
    rows = [Row("c", 0, t, 0, 0.0, {"mean_duration": 1.0}) for t in ("a", "b", "c")]
    probabilities = [0.5, 0.01, 0.01]
    plain = decide(rows, probabilities, RiskPolicy(budget=None, risk_target=0.05), order=["b", "c", "a"])
    assert plain.selected == ["a", "b", "c"]  # 'a' is last in order but carries the risk
    pinned = decide(rows, probabilities, RiskPolicy(budget=None, risk_target=0.05),
                    order=["b", "c", "a"], always={"a"})
    assert pinned.selected == ["a"] and pinned.estimated_skip_risk < 0.05
    assert "1 must-run test class(es) always run" in pinned.reasons


def test_api_select_accepts_must_run_patterns(repo):
    from fastapi.testclient import TestClient

    from codedna.api.app import create_app
    base, head = change(repo)
    api = TestClient(create_app("t" * 32), base_url="http://127.0.0.1")
    body = {"repo": str(repo.path), "base": base, "head": head, "strategy": "dependency",
            "must_run": ["a.OtherTest"]}
    response = api.post("/api/select", json=body, headers={"X-CodeDNA-Token": "t" * 32})
    assert response.status_code == 200
    assert response.json()["policy"]["pinned"] == ["a.OtherTest"]
