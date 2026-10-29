"""Test brake for AI coding agents and its MCP server (D-059), on temporary Git repositories."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from codedna.agent import brake
from codedna.agent.mcp_server import BrakeServer
from codedna.test_history.recording import HISTORY_CSV

FAKE = [sys.executable, str(Path(__file__).with_name("fake_mvn.py"))]
CORE = "package a; public class Core { int value() { return 1; } }"


def test_failure_outside_requested_selection_still_blocks():
    from types import SimpleNamespace
    run = SimpleNamespace(tests={
        'a.ATest': SimpleNamespace(failed=False, status='passed'),
        'a.ExtraTest': SimpleNamespace(failed=True, status='failed')},
        exit_codes=[1], warnings=[])
    result = brake._run_verdict(['a.ATest'], run)
    assert result['verdict'] == 'blocked'
    assert result['failed'] == ['a.ExtraTest']


def junit_class(name):
    return f"package a; import org.junit.jupiter.api.Test; class {name} {{ @Test void x() {{}} }}"


@pytest.fixture
def project(repo, tmp_path, monkeypatch):
    repo.write("pom.xml", "<project/>")
    repo.write("src/main/java/a/Core.java", CORE)
    for name in ["ATest", "BTest"]:
        repo.write(f"src/test/java/a/{name}.java", junit_class(name))
    repo.commit("base")
    spec = tmp_path / "spec.json"

    def outcomes(exit_code=0, **tests):
        spec.write_text(json.dumps({"exit_code": exit_code, "tests": {
            t: {"status": status, "time": 1.0, "cases": ["x"]} for t, status in tests.items()}}))

    outcomes(**{"a.ATest": "passed", "a.BTest": "passed"})
    monkeypatch.setenv("CODEDNA_FAKE_MVN_SPEC", str(spec))
    repo.write("src/main/java/a/Core.java", CORE.replace("return 1", "return 2"))  # agent's edit
    return repo, outcomes


def test_plan_lists_every_test_without_validated_history(project):
    repo, _ = project
    planned = brake.plan(repo.path)
    assert planned["must_run"] == ["a.ATest", "a.BTest"] and planned["skipped"] == []
    assert planned["risk"]["status"] == "unvalidated"
    assert planned["summary"].startswith("Run all 2 test classes")
    assert planned["head_commit"] != planned["base_commit"]  # the uncommitted edit


def test_plan_keeps_must_run_patterns(project):
    repo, _ = project
    planned = brake.plan(repo.path, must_run=["a.BTest"])
    assert "must-run: pinned by request" in planned["reasons"]["a.BTest"]


def test_check_verdicts(project):
    repo, outcomes = project
    passed = brake.check(repo.path, maven_command=FAKE, allow_build=True)
    assert passed["verdict"] == "passed" and passed["results"]["tests"]
    assert passed["recording"]["recorded"] is False  # uncommitted states are never history

    outcomes(**{"a.ATest": "passed", "a.BTest": "failed"})
    blocked = brake.check(repo.path, maven_command=FAKE, allow_build=True)
    assert blocked["verdict"] == "blocked" and blocked["failed"] == ["a.BTest"]

    outcomes(**{"a.ATest": "passed"})  # BTest produced no report (e.g. did not compile)
    incomplete = brake.check(repo.path, maven_command=FAKE, allow_build=True)
    assert incomplete["verdict"] == "incomplete" and incomplete["missing"] == ["a.BTest"]
    assert repo.git("status", "--porcelain") == "M src/main/java/a/Core.java"


def test_build_errors_and_all_skipped_runs_are_incomplete(project):
    repo, outcomes = project
    outcomes(exit_code=1, **{"a.ATest": "passed", "a.BTest": "passed"})  # e.g. another module failed
    errored = brake.check(repo.path, maven_command=FAKE, allow_build=True)
    assert errored["verdict"] == "incomplete" and "exit codes [1]" in errored["message"]

    outcomes(**{"a.ATest": "skipped", "a.BTest": "skipped"})
    skipped = brake.check(repo.path, maven_command=FAKE, allow_build=True)
    assert skipped["verdict"] == "incomplete" and skipped["skipped_by_build"] == ["a.ATest", "a.BTest"]

    outcomes(**{"a.ATest": "passed", "a.BTest": "skipped"})
    some = brake.check(repo.path, maven_command=FAKE, allow_build=True)
    assert some["verdict"] == "incomplete" and some["skipped_by_build"] == ["a.BTest"]
    assert "remain unverified" in some["message"]


def test_check_needs_explicit_build_consent(project):
    repo, _ = project
    with pytest.raises(ValueError, match="allow_build"):
        brake.check(repo.path, maven_command=FAKE)


@pytest.mark.parametrize("outcome,verdict", [("failed", "blocked"), ("skipped", "incomplete"), ("passed", "passed")])
def test_shadow_executes_skipped_recommendations_and_preserves_plan(project, monkeypatch, outcome, verdict):
    repo, outcomes = project
    original = brake.plan(repo.path)
    selected = {**original, "must_run": ["a.ATest"], "skipped": ["a.BTest"]}
    monkeypatch.setattr(brake, "plan", lambda *a, **k: selected)
    outcomes(**{"a.ATest": "passed", "a.BTest": outcome})
    result = brake.check(repo.path, maven_command=FAKE, allow_build=True, shadow=True)
    assert result["verdict"] == verdict
    assert result["plan"] == selected
    evidence = result["shadow"]
    assert evidence["expected_tests"] == ["a.ATest", "a.BTest"]
    assert evidence["skipping_authorized"] is False
    assert evidence["observed_failures_outside_recommendation"] == (["a.BTest"] if outcome == "failed" else [])
    assert evidence["skipped_by_build"] == (["a.BTest"] if outcome == "skipped" else [])
    assert evidence["total_seconds"] >= evidence["analysis_seconds"] + evidence["execution_seconds"] >= 0
    assert result["recording"]["recorded"] is False  # WORKTREE is not training history


def test_shadow_runs_even_when_recommendation_is_empty(project, monkeypatch):
    repo, outcomes = project
    original = brake.plan(repo.path)
    monkeypatch.setattr(brake, "plan", lambda *a, **k: {
        **original, "must_run": [], "skipped": ["a.ATest", "a.BTest"]})
    outcomes(**{"a.ATest": "passed", "a.BTest": "failed"})
    result = brake.check(repo.path, maven_command=FAKE, allow_build=True, shadow=True)
    assert result["verdict"] == "blocked"
    assert result["shadow"]["observed_failures_outside_recommendation"] == ["a.BTest"]


def test_shadow_missing_results_remain_incomplete(project):
    repo, outcomes = project
    outcomes(**{"a.ATest": "passed"})
    result = brake.check(repo.path, maven_command=FAKE, allow_build=True, shadow=True)
    assert result["verdict"] == "incomplete"
    assert result["shadow"]["missing_results"] == ["a.BTest"]


def test_shadow_mcp_validates_type_and_execution_consent(project):
    repo, _ = project
    hidden = rpc(BrakeServer(repo=repo.path), "tools/call", {
        "name": "codedna_check", "arguments": {"shadow": True}})
    assert hidden["error"]["code"] == -32602
    server = BrakeServer(repo=repo.path, allow_build=True, build_options={"maven_command": FAKE})
    bad = rpc(server, "tools/call", {"name": "codedna_check", "arguments": {"shadow": "true"}})
    assert bad["result"]["isError"] is True
    good = rpc(server, "tools/call", {"name": "codedna_check", "arguments": {"shadow": True}})
    assert good["result"]["structuredContent"]["shadow"]["mode"] == "full_suite_observation"


@pytest.mark.parametrize('first,second', [('failed','passed'), ('passed','failed')])
def test_repeated_failure_is_never_erased_or_recorded_as_stable_history(project, monkeypatch, first, second):
    from codedna.plugins import languages
    repo, outcomes = project
    original = languages.run_tests
    statuses = iter([first, second])
    def execute(*args, **kwargs):
        outcomes(**{'a.ATest': 'passed', 'a.BTest': next(statuses)})
        return original(*args, **kwargs)
    monkeypatch.setattr(languages, 'run_tests', execute)
    result = brake.check(repo.path, maven_command=FAKE, allow_build=True, shadow=True, attempts=2)
    assert result['verdict'] == 'blocked' and result['failed'] == ['a.BTest']
    assert result['repeat_evidence']['unstable_observed'] is True
    assert len(result['repeat_evidence']['attempts']) == 2
    assert result['recording']['recorded'] is False
    assert result['shadow']['observed_failures_outside_recommendation'] == []  # both were recommended


def test_repeated_build_error_cannot_turn_into_a_pass(project, monkeypatch):
    from codedna.plugins import languages
    repo, outcomes = project
    original = languages.run_tests
    codes = iter([1, 0])
    def execute(*args, **kwargs):
        outcomes(exit_code=next(codes), **{'a.ATest': 'passed', 'a.BTest': 'passed'})
        return original(*args, **kwargs)
    monkeypatch.setattr(languages, 'run_tests', execute)
    result = brake.check(repo.path, maven_command=FAKE, allow_build=True, attempts=2)
    assert result['verdict'] == 'incomplete'
    assert result['repeat_evidence']['unstable_observed'] is True
    assert result['recording']['recorded'] is False
    assert [a['verdict']['verdict'] for a in result['repeat_evidence']['attempts']] == ['incomplete', 'passed']


@pytest.mark.parametrize('initial,expected', [('failed', 'blocked'), ('passed', 'incomplete')])
def test_repeat_runner_failure_preserves_earlier_evidence(project, monkeypatch, initial, expected):
    from codedna.plugins import languages
    repo, outcomes = project
    original = languages.run_tests
    calls = []
    def execute(*args, **kwargs):
        calls.append(True)
        if len(calls) > 1:
            raise RuntimeError('Injected failure while starting the repeat')
        outcomes(**{'a.ATest': 'passed', 'a.BTest': initial})
        return original(*args, **kwargs)
    monkeypatch.setattr(languages, 'run_tests', execute)
    result = brake.check(repo.path, maven_command=FAKE, allow_build=True, attempts=2)
    assert result['verdict'] == expected
    assert result['repeat_evidence']['completed'] == 1
    assert 'Injected failure' in result['repeat_evidence']['error']
    assert result['recording']['recorded'] is False
    if initial == 'failed':
        assert result['failed'] == ['a.BTest']


def test_validated_plan_without_tests_is_nothing_to_run(project, monkeypatch):
    repo, _ = project
    planned = brake.plan(repo.path)
    monkeypatch.setattr(brake, "plan", lambda *a, **k: {
        **planned, "must_run": [], "skipped": ["a.ATest", "a.BTest"]})
    result = brake.check(repo.path, maven_command=["nonexistent-command"], allow_build=True)
    assert result["verdict"] == "nothing_to_run" and result["results"] is None


def test_check_of_a_commit_is_recorded_as_history(project):
    repo, _ = project
    repo.commit("change")
    result = brake.check(repo.path, base="HEAD~1", head="HEAD", maven_command=FAKE,
                         allow_build=True)
    assert result["verdict"] == "passed" and result["recording"]["recorded"] is True
    assert (repo.path / HISTORY_CSV).is_file()


def test_project_without_tests_checks_nothing(repo):
    repo.write("pom.xml", "<project/>")
    repo.write("src/main/java/a/Core.java", CORE)
    repo.commit("base")
    result = brake.check(repo.path, maven_command=["nonexistent-command"], allow_build=True)
    assert result["verdict"] == "no_tests" and result["results"] is None


# --- MCP server -----------------------------------------------------------------


def rpc(server, method, params=None, ident=1):
    message = {"jsonrpc": "2.0", "id": ident, "method": method}
    if params is not None:
        message["params"] = params
    return server.handle(message)


def tool_names(server):
    return [t["name"] for t in rpc(server, "tools/list")["result"]["tools"]]


def test_initialize_negotiates_the_protocol_version(repo):
    server = BrakeServer()
    assert rpc(server, "initialize", {"protocolVersion": "2024-11-05"})["result"][
        "protocolVersion"] == "2024-11-05"
    answer = rpc(server, "initialize", {"protocolVersion": "1999-01-01"})["result"]
    assert answer["protocolVersion"] == "2025-06-18"
    assert answer["capabilities"] == {"tools": {"listChanged": False}}
    assert server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    assert rpc(server, "ping")["result"] == {}
    assert rpc(server, "resources/list")["error"]["code"] == -32601


def test_check_is_offered_only_with_build_consent_for_one_repository(project):
    repo, _ = project
    assert tool_names(BrakeServer()) == ["codedna_plan_tests", "codedna_impact"]
    with pytest.raises(ValueError, match="needs --repo"):
        BrakeServer(allow_build=True)
    server = BrakeServer(repo=repo.path, allow_build=True, build_options={"maven_command": FAKE})
    assert "codedna_check" in tool_names(server)
    answer = rpc(server, "tools/call", {"name": "codedna_check", "arguments": {}})["result"]
    assert answer["isError"] is False and answer["structuredContent"]["verdict"] == "passed"
    hidden = rpc(BrakeServer(), "tools/call", {"name": "codedna_check", "arguments": {}})
    assert hidden["error"]["code"] == -32602
    odd = rpc(BrakeServer(), "tools/call", {"name": ["codedna_plan_tests"], "arguments": {}})
    assert odd["error"]["code"] == -32602  # an unhashable name must not crash the server


def test_tool_calls_validate_arguments_and_repository(project, tmp_path):
    repo, _ = project
    server = BrakeServer(repo=repo.path)
    planned = rpc(server, "tools/call", {"name": "codedna_plan_tests", "arguments": {}})["result"]
    assert planned["isError"] is False
    assert json.loads(planned["content"][0]["text"])["must_run"] == ["a.ATest", "a.BTest"]

    impact = rpc(server, "tools/call", {"name": "codedna_impact", "arguments": {}})["result"]
    assert impact["structuredContent"]["seeds"][0]["node"] == "type:a.Core"

    unknown = rpc(server, "tools/call", {"name": "codedna_plan_tests", "arguments": {"x": 1}})
    assert "unknown arguments" in unknown["error"]["message"]
    for arguments in ({"risk_target": 1.5}, {"must_run": [""]}, {"head": 3}):
        bad = rpc(server, "tools/call", {"name": "codedna_plan_tests", "arguments": arguments})
        assert bad["result"]["isError"] is True

    other = tmp_path / "other"
    other.mkdir()
    import subprocess
    subprocess.run(["git", "init", "--quiet", str(other)], check=True)
    elsewhere = rpc(server, "tools/call", {"name": "codedna_plan_tests",
                                           "arguments": {"repo": str(other)}})["result"]
    assert elsewhere["isError"] is True and "serves" in elsewhere["structuredContent"]["error"]
    no_repo = rpc(BrakeServer(), "tools/call", {"name": "codedna_plan_tests", "arguments": {}})
    assert "give 'repo'" in no_repo["result"]["structuredContent"]["error"]


def test_stdio_loop_answers_requests_and_parse_errors(project):
    repo, _ = project
    lines = [json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
             json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
             "not json", "",
             json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})]
    out = io.StringIO()
    assert BrakeServer(repo=repo.path).serve(io.StringIO("\n".join(lines) + "\n"), out) == 0
    answers = [json.loads(line) for line in out.getvalue().splitlines()]
    assert [a.get("id") for a in answers] == [1, None, 2]
    assert answers[1]["error"]["code"] == -32700


@pytest.fixture
def validated(repo, tmp_path, monkeypatch):
    """240 recorded commits in the project's own history, then a change of Core (D-068)."""
    from test_live_risk import validated_change
    base, head, path = validated_change(repo, tmp_path)
    history = repo.path / HISTORY_CSV
    history.parent.mkdir(parents=True, exist_ok=True)
    history.write_bytes(path.read_bytes())
    spec = tmp_path / "spec.json"

    def outcomes(**tests):
        spec.write_text(json.dumps({"exit_code": int("failed" in tests.values()), "tests": {
            t: {"status": status, "time": 1.0, "cases": ["x"]} for t, status in tests.items()}}))

    monkeypatch.setenv("CODEDNA_FAKE_MVN_SPEC", str(spec))
    return repo, base, head, outcomes


@pytest.mark.parametrize("method", ["b10", "crc"])
def test_brake_plans_part_of_the_suite_on_validated_history(validated, method):
    repo, base, head, _ = validated
    planned = brake.plan(repo.path, base=base, head=head, method=method)
    assert planned["risk"]["status"] == "validated_history", planned["risk"]
    assert planned["risk"]["method"] == method
    assert planned["risk"]["objective"] == "omit_any_failing_test"
    assert planned["risk"]["audit"]["future_guarantee"] is False
    assert planned["risk"]["audit"]["sample_size"] > 0
    assert planned["risk"]["audit"]["denominator"] == (
        "failing_audit_commits" if method == "crc" else "all_audit_commits")
    assert "not a guarantee" in planned["risk"]["note"]
    assert planned["must_run"] == ["a.CoreTest"] and planned["skipped"] == ["a.OtherTest"]
    assert planned["summary"].startswith("Run 1 of 2 test classes")
    if method == "crc":
        assert planned["risk"]["conformal"]["failing_audit_commits"] >= 19
        assert "Conformal stop" in planned["summary"]


def test_brake_check_on_validated_history_gives_a_verdict(validated):
    repo, base, head, outcomes = validated
    outcomes(**{"a.CoreTest": "failed"})
    blocked = brake.check(repo.path, base=base, head=head, method="crc",
                          maven_command=FAKE, allow_build=True)
    assert blocked["verdict"] == "blocked" and blocked["failed"] == ["a.CoreTest"]
    assert blocked["recording"] is None  # a partial run is never history
    outcomes(**{"a.CoreTest": "passed"})
    passed = brake.check(repo.path, base=base, head=head, method="crc",
                         maven_command=FAKE, allow_build=True)
    assert passed["verdict"] == "passed" and passed["plan"]["skipped"] == ["a.OtherTest"]


def test_mcp_plan_accepts_the_conformal_method(validated):
    repo, base, head, _ = validated
    server = BrakeServer(repo=repo.path)
    answer = rpc(server, "tools/call", {"name": "codedna_plan_tests", "arguments": {
        "base": base, "head": head, "method": "crc"}})["result"]
    assert answer["isError"] is False
    risk = answer["structuredContent"]["risk"]
    assert risk["method"] == "crc" and risk["conformal"]["threshold"] is not None
    bad = rpc(server, "tools/call", {"name": "codedna_plan_tests", "arguments": {"method": "x"}})
    assert bad["result"]["isError"] is True


def test_unvalidated_brake_has_no_invented_audit(project):
    repo, _ = project
    risk = brake.plan(repo.path)["risk"]
    assert risk["audit"] is None
    assert risk["estimated_skip_risk"] is None
    assert risk["objective"] == "omit_any_failing_test"
