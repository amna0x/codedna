"""Tests for the local API used by the CodeDNA IDE."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from codedna.api.app import _hostname, create_app  # noqa: E402
from codedna.api.server import is_loopback, serve  # noqa: E402

TOKEN = "t" * 32
AUTH = {"X-CodeDNA-Token": TOKEN}
FAKE_MVN = [sys.executable, str(Path(__file__).with_name("fake_mvn.py"))]
JUNIT5 = "import org.junit.jupiter.api.Test;\n"


def client(**options) -> TestClient:
    return TestClient(create_app(TOKEN, **options), base_url="http://127.0.0.1:8765")


@pytest.fixture
def project(repo):
    repo.write("pom.xml", "<project/>\n")
    repo.write("src/main/java/a/Core.java", "package a;\npublic class Core { int v() { return 1; } }\n")
    repo.write("src/test/java/a/CoreTest.java",
               "package a;\n" + JUNIT5 + "class CoreTest { Core c; @Test void t() {} }\n")
    base = repo.commit("base")
    repo.write("src/main/java/a/Core.java", "package a;\npublic class Core { int v() { return 2; } }\n")
    head = repo.commit("head")
    return repo, base, head


# --- access control ----------------------------------------------------------------------


def test_health_is_open_but_everything_else_needs_the_token():
    api = client()
    assert api.get("/api/health").json() == {"status": "ok", "version": "0.1.0"}
    assert api.get("/api/plugins").status_code == 401
    assert api.get("/api/plugins", headers={"X-CodeDNA-Token": "wrong"}).status_code == 401
    assert api.get("/api/plugins", headers=AUTH).json()["plugins"][0]["name"] == "java"


@pytest.mark.parametrize("host", ["evil.example", "localhost.evil.example", "192.168.1.5:8765"])
def test_non_loopback_host_headers_are_rejected(host):
    response = client().get("/api/health", headers={"Host": host})
    assert response.status_code == 403


def test_no_cors_headers_are_sent():
    response = client().get("/api/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("header,host", [("127.0.0.1:8765", "127.0.0.1"), ("localhost", "localhost"),
                                         ("[::1]:8765", "[::1]"), ("evil:1", "evil")])
def test_hostname_parsing(header, host):
    assert _hostname(header) == host


def test_token_and_host_policies():
    with pytest.raises(ValueError, match="at least 16"):
        create_app("short")
    assert is_loopback("127.0.0.1") and is_loopback("::1") and is_loopback("localhost")
    assert not is_loopback("0.0.0.0") and not is_loopback("192.168.1.5")
    assert serve("0.0.0.0", 8765) == 1


# --- analysis endpoints ---------------------------------------------------------------------


def test_analysis_endpoints_return_cli_json(project):
    repo, base, head = project
    api, body = client(), {"repo": str(repo.path), "base": base, "head": head}

    analyzed = api.post("/api/analyze", headers=AUTH, json=body).json()
    assert analyzed["changed_files"][0]["java"]["declarations"][0]["id"] == "a.Core#v()"

    graph = api.post("/api/graph", headers=AUTH,
                     json={"repo": str(repo.path), "include_members": False}).json()
    assert any(e["kind"] == "uses" for e in graph["edges"])

    impact = api.post("/api/impact", headers=AUTH, json=body).json()
    assert [n["node"] for n in impact["impacted"]] == ["type:a.CoreTest"]

    tests = api.post("/api/tests", headers=AUTH, json={"repo": str(repo.path)}).json()
    assert tests["tests"][0]["id"] == "a.CoreTest"

    selected = api.post("/api/select", headers=AUTH, json={**body, "strategy": "dependency"}).json()
    assert [s["test"] for s in selected["selected"]] == ["a.CoreTest"]

    capabilities = api.get("/api/capabilities", headers=AUTH).json()
    assert capabilities["allow_build"] is False


def test_errors_are_json_with_useful_status(project, tmp_path):
    repo, base, head = project
    api = client()

    missing = api.post("/api/analyze", headers=AUTH,
                       json={"repo": str(tmp_path / "nope"), "base": "a", "head": "b"})
    assert missing.status_code == 400 and "does not exist" in missing.json()["error"]

    bad_strategy = api.post("/api/select", headers=AUTH, json={
        "repo": str(repo.path), "base": base, "head": head, "strategy": "magic"})
    assert bad_strategy.status_code == 422

    no_map = api.post("/api/select", headers=AUTH, json={
        "repo": str(repo.path), "base": base, "head": head, "strategy": "coverage"})
    assert no_map.status_code == 400 and "coverage map" in no_map.json()["error"]

    no_truth = api.post("/api/compare", headers=AUTH, json={
        "repo": str(repo.path), "base": base, "head": head,
        "ground_truth": str(tmp_path / "missing.json")})
    assert no_truth.status_code == 400


# --- running tests ------------------------------------------------------------------------------


def test_run_tests_needs_server_and_request_opt_in(project, tmp_path, monkeypatch):
    repo, _, head = project
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"tests": {"a.CoreTest": {"status": "failed", "time": 0.5}}}),
                    encoding="utf-8")
    monkeypatch.setenv("CODEDNA_FAKE_MVN_SPEC", str(spec))
    body = {"repo": str(repo.path), "rev": head, "output_dir": str(tmp_path / "run")}

    locked = client().post("/api/run-tests", headers=AUTH, json={**body, "allow_build": True})
    assert locked.status_code == 403

    enabled = client(allow_build=True, maven_command=FAKE_MVN)
    unconfirmed = enabled.post("/api/run-tests", headers=AUTH, json=body)
    assert unconfirmed.status_code == 400 and "allow_build" in unconfirmed.json()["detail"]
    assert not (tmp_path / "run").exists()

    ran = enabled.post("/api/run-tests", headers=AUTH, json={**body, "allow_build": True}).json()
    assert ran["results"]["failing_tests"] == ["a.CoreTest"]
    assert ran["coverage_map"] is None
