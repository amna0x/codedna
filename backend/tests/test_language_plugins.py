"""The core without its Java plugin (D-054): it must start, list changes and say what to install."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from codedna.cli import EXIT_ANALYSIS_ERROR, EXIT_OK, main
from codedna.plugins import load_plugins
from codedna.plugins.languages import (
    PluginMissingError,
    analyze_changes,
    build_graph,
    require,
    type_kinds,
)

FILES = {
    "src/main/java/a/Core.java": "package a;\npublic class Core {\n    int value() { return 1; }\n}\n",
    "src/test/java/a/CoreTest.java": "package a;\nclass CoreTest {\n    @org.junit.jupiter.api.Test void t() {}\n}\n",
    "README.md": "demo\n",
}


@pytest.fixture
def no_plugins(monkeypatch):
    """Pretend no language plugin is installed."""
    monkeypatch.setattr("codedna.plugins.registry.entry_points", lambda group: [])


@pytest.fixture
def change(repo):
    for path, content in FILES.items():
        repo.write(path, content)
    base = repo.commit("base")
    repo.write("src/main/java/a/Core.java", FILES["src/main/java/a/Core.java"].replace("1", "2"))
    repo.write("README.md", "demo, changed\n")
    return repo, base, repo.commit("head")


def test_changes_are_listed_and_java_files_reported_as_not_analysed(no_plugins, change):
    repo, base, head = change

    report = analyze_changes(repo.path, base, head)

    assert report.analysis_level == "file"
    assert {c.path for c in report.changed_files} == {"src/main/java/a/Core.java", "README.md"}
    assert all(c.java is None for c in report.changed_files)
    assert any("1 changed .java file(s) not analysed" in w and "codedna-java" in w
               for w in report.warnings)


def test_the_installed_java_plugin_maps_the_same_change(change):
    repo, base, head = change

    report = analyze_changes(repo.path, base, head)

    assert report.analysis_level == "method"
    java = next(c for c in report.changed_files if c.path.endswith("Core.java")).java
    assert [d.id for d in java.declarations] == ["a.Core#value()"]
    assert not any("not analysed" in w for w in report.warnings)


def test_commands_that_need_java_name_the_plugin_to_install(no_plugins, change, capsys):
    repo, base, head = change
    with pytest.raises(PluginMissingError, match="pip install -e plugins/codedna-java"):
        require("java")
    with pytest.raises(PluginMissingError):
        build_graph(repo.path, head)
    assert type_kinds() == frozenset()

    for argv in (["impact", "--repo", str(repo.path), "--base", base, "--head", head],
                 ["select", "--repo", str(repo.path), "--base", base, "--head", head,
                  "--strategy", "dependency"],
                 ["graph", "--repo", str(repo.path), "--rev", head],
                 ["tests", "--repo", str(repo.path), "--rev", head]):
        assert main(argv) == EXIT_ANALYSIS_ERROR, argv
        assert "codedna-java" in capsys.readouterr().err

    assert main(["analyze", "--repo", str(repo.path), "--base", base, "--head", head]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["analysis_level"] == "file"
    assert main(["plugins"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["plugins"] == []


def test_load_problems_are_part_of_the_message(monkeypatch):
    class Broken:
        name = "java"

        def load(self):
            raise ImportError("No module named 'tree_sitter'")

    monkeypatch.setattr("codedna.plugins.registry.entry_points", lambda group: [Broken()])

    with pytest.raises(PluginMissingError, match="tree_sitter"):
        require("java", load_plugins())


def test_api_reports_a_missing_plugin_as_a_json_error(no_plugins, change):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from codedna.api.app import create_app

    repo, base, head = change
    token = "t" * 32
    client = TestClient(create_app(token), base_url="http://127.0.0.1:8765")
    headers = {"X-CodeDNA-Token": token}

    response = client.post("/api/impact", json={"repo": str(repo.path), "base": base,
                                                "head": head}, headers=headers)
    assert response.status_code == 400
    assert "codedna-java" in response.json()["error"]
    response = client.post("/api/analyze", json={"repo": str(repo.path), "base": base,
                                                 "head": head}, headers=headers)
    assert response.status_code == 200 and response.json()["analysis_level"] == "file"


def test_the_core_never_imports_the_java_plugin():
    """Importing every core module with ``codedna_java`` blocked must work."""
    probe = (
        "import sys, pkgutil, importlib\n"
        "sys.modules['codedna_java'] = sys.modules['tree_sitter'] = None\n"  # imports now fail
        "import codedna\n"
        "for m in pkgutil.walk_packages(codedna.__path__, 'codedna.'):\n"
        "    if not m.name.endswith('__main__'): importlib.import_module(m.name)\n"
        "print('ok')\n")
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True,
                            check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
