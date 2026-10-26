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
    assert some["verdict"] == "passed" and some["skipped_by_build"] == ["a.BTest"]


def test_check_needs_explicit_build_consent(project):
    repo, _ = project
    with pytest.raises(ValueError, match="allow_build"):
        brake.check(repo.path, maven_command=FAKE)


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
