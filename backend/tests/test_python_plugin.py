"""The Python language plugin (codedna-python, D-060) on its own and next to Java."""

from __future__ import annotations

import json
import sys
from importlib.metadata import entry_points as real_entry_points

import pytest

from codedna.cli import EXIT_ANALYSIS_ERROR, EXIT_OK, main
from codedna.impact_analysis import compute_impact
from codedna.plugins import load_plugins
from codedna.plugins.languages import (
    TestRunError,
    analyze_changes,
    build_graph,
    discover_tests,
    run_tests,
)
from codedna.plugins.registry import PluginRegistry
from codedna.selection import select_tests
from codedna.test_mapping.results import RESULTS_FILE, TestClassResult, TestRunResult
from codedna_python.discovery import read_config
from codedna_python.parser import module_name, parse_python

pytest.importorskip("codedna_java")

MODELS = '''"""Shop models."""


class Base:
    def describe(self):
        return "base"


class Order(Base):
    @property
    def total(self):
        return 3  # three

    @total.setter
    def total(self, value):
        pass


def make():
    return Order()
'''

PROJECT = {
    "src/shop/__init__.py": "",
    "src/shop/models.py": MODELS,
    "src/shop/report.py": "from .models import Order\n\n\ndef render(order):\n"
                          "    return str(order.total)\n",
    "src/shop/util.py": "import json\n\n\ndef dump(value):\n    return json.dumps(value)\n",
    "tests/test_models.py": "from shop.models import Order\n\n\ndef test_total():\n"
                            "    assert Order().total == 3\n",
    "tests/test_report.py": "from shop import report\nfrom shop.models import Order\n\n\n"
                            "class TestRender:\n    def test_render(self):\n"
                            "        assert report.render(Order()) == '3'\n",
    "tests/test_util.py": "from shop.util import dump\n\n\ndef test_dump():\n"
                          "    assert dump(1) == '1'\n",
    "pyproject.toml": '[tool.pytest.ini_options]\ntestpaths = ["tests"]\npythonpath = ["src"]\n',
    # Java side of the same repository
    "src/main/java/shop/Price.java": "package shop;\npublic class Price {\n"
                                     "    public int cents() { return 100; }\n}\n",
    "src/test/java/shop/PriceTest.java": "package shop;\nimport org.junit.jupiter.api.Test;\n"
                                         "class PriceTest {\n"
                                         "    @Test void cents() { new Price().cents(); }\n}\n",
}


def commit(repo, files: dict[str, str], message: str) -> str:
    for path, content in files.items():
        repo.write(path, content)
    return repo.commit(message)


@pytest.fixture
def mixed(repo):
    return repo, commit(repo, PROJECT, "base")


@pytest.fixture
def java_only_plugins(monkeypatch):
    """Pretend only the Java plugin is installed."""
    monkeypatch.setattr("codedna.plugins.registry.entry_points",
                        lambda group: [ep for ep in real_entry_points(group=group)
                                       if ep.name == "java"])


# --- parsing ------------------------------------------------------------------------


def test_module_names_come_from_paths():
    assert module_name("src/shop/models.py") == "shop.models"
    assert module_name("shop/__init__.py") == "shop"
    assert module_name("tests/test_x.py") == "tests.test_x"
    assert module_name("__init__.py") == "__init__"


def test_declarations_have_prefixed_ids_and_decorators_belong_to_them():
    result = parse_python(MODELS.encode(), "src/shop/models.py")

    ids = [(d.id, d.kind, d.start_line, d.end_line) for d in result.declarations]
    assert ids == [
        ("py:shop.models.Base", "class", 4, 6),
        ("py:shop.models.Base#describe()", "method", 5, 6),
        ("py:shop.models.Order", "class", 9, 16),
        ("py:shop.models.Order#total()", "method", 10, 12),  # getter, from its decorator
        ("py:shop.models.Order#total()", "method", 14, 16),  # setter: same declaration
        ("py:shop.models#make()", "function", 19, 20),
    ]
    assert [(b.class_id, b.name) for b in result.bases] == [("py:shop.models.Order", "Base")]


def test_relative_imports_resolve_against_the_package():
    source = b"from . import a\nfrom ..core import b\nfrom ... import c\nimport os.path as p\n"
    result = parse_python(source, "pkg/sub/mod.py")

    assert [(i.module, i.names, i.alias) for i in result.imports] == [
        ("pkg.sub", ["a"], None), ("pkg.core", ["b"], None), (None, ["c"], None),
        ("os.path", [], "p")]


def test_syntax_errors_are_reported_not_guessed():
    result = parse_python(b"def broken(:\n    pass\n", "x.py")

    assert result.has_syntax_errors and result.declarations == []
    assert result.error == "Python syntax error near line 1"


# --- change mapping -----------------------------------------------------------------


def test_comment_only_change_is_not_a_code_change(mixed):
    repo, base = mixed
    head = commit(repo, {"src/shop/models.py": MODELS.replace("# three", "# three!")}, "comment")

    report = analyze_changes(repo.path, base, head)

    changed = report.changed_files[0]
    assert changed.language == "python" and changed.java is None
    assert [(d.id, d.change, d.code_changed) for d in changed.analysis.declarations] == [
        ("py:shop.models.Order#total()", "modified", False)]
    impact = compute_impact(repo.path, base, head)
    assert impact.seeds == [] and impact.ignored_changes[0]["id"] == "py:shop.models.Order#total()"


def test_function_and_module_level_changes_are_mapped(mixed):
    repo, base = mixed
    head = commit(repo, {"src/shop/util.py": "import json\nimport os\n\n\ndef dump(value):\n"
                                             "    return json.dumps(value, indent=1)\n"}, "edit")

    analysis = analyze_changes(repo.path, base, head).changed_files[0].analysis

    assert analysis.package == "shop.util"
    assert [(d.id, d.kind, d.parent, d.code_changed) for d in analysis.declarations] == [
        ("py:shop.util#dump()", "function", "py:shop.util", True)]
    assert [(o.side, o.parts, o.code_changed) for o in analysis.outside_declarations] == [
        ("head", ["import"], True)]


def test_a_syntax_error_leaves_the_file_unresolved(mixed):
    repo, base = mixed
    head = commit(repo, {"src/shop/util.py": "def dump(:\n"}, "broken")

    report = analyze_changes(repo.path, base, head)

    analysis = report.changed_files[0].analysis
    assert analysis.declarations == []
    assert analysis.unresolved[0].reason == "Python syntax error in head version near line 1"
    assert any("src/shop/util.py: Python syntax error" in w for w in report.warnings)
    seeds = compute_impact(repo.path, base, head).seeds
    assert [s.node for s in seeds] == ["type:py:shop.util"]  # whole file treated as changed


# --- graph --------------------------------------------------------------------------


def edges(graph, kind=None):
    return {(e.source, e.target, e.kind, e.confidence) for e in graph.edges.values()
            if e.kind != "contains" and (kind is None or e.kind == kind)}


def test_import_and_inheritance_edges_are_labelled(mixed):
    repo, head = mixed

    graph = build_graph(repo.path, head)

    python = {e for e in edges(graph) if "py:" in e[0]}
    assert python == {
        ("type:py:shop.models", "type:py:shop.models.Base", "uses", "confirmed"),
        ("type:py:shop.models", "type:py:shop.models.Order", "uses", "confirmed"),
        ("type:py:shop.models.Order", "type:py:shop.models.Base", "extends", "confirmed"),
        ("type:py:shop.report", "type:py:shop.models", "imports", "confirmed"),
        ("type:py:shop.report", "type:py:shop.models.Order", "uses", "confirmed"),
        ("type:py:tests.test_models", "type:py:shop.models", "imports", "confirmed"),
        ("type:py:tests.test_models", "type:py:shop.models.Order", "uses", "confirmed"),
        ("type:py:tests.test_report", "type:py:shop", "imports", "confirmed"),
        ("type:py:tests.test_report", "type:py:shop.report", "imports", "confirmed"),
        ("type:py:tests.test_report", "type:py:shop.models", "imports", "confirmed"),
        ("type:py:tests.test_report", "type:py:shop.models.Order", "uses", "confirmed"),
        ("type:py:tests.test_report", "type:py:tests.test_report.TestRender", "uses",
         "confirmed"),
        ("type:py:tests.test_util", "type:py:shop.util", "imports", "confirmed"),
    }
    # Java's graph is joined in, and no edge crosses the languages.
    assert ("type:shop.PriceTest", "type:shop.Price", "uses", "confirmed") in edges(graph)
    assert not [e for e in edges(graph) if ("py:" in e[0]) != ("py:" in e[1])]
    assert graph.external_reference_count >= 1  # import json
    assert graph.nodes["type:py:tests.test_models"].role == "test"
    assert graph.nodes["type:py:shop.models"].parent == "file:src/shop/models.py"


def test_suffix_matches_and_name_matches_are_heuristic(repo):
    head = commit(repo, {
        "app/lib/shop/models.py": "class Base:\n    pass\n",
        "app/lib/shop/orders.py": "class Order(Missing):\n    pass\n\n\n"
                                  "class Special(Base):\n    pass\n",
        "tests/test_orders.py": "from shop.models import Base\nfrom .... import nothing\n",
    }, "base")

    graph = build_graph(repo.path, head, language="python")

    assert edges(graph) >= {
        ("type:py:tests.test_orders", "type:py:app.lib.shop.models", "imports", "heuristic"),
        ("type:py:tests.test_orders", "type:py:app.lib.shop.models.Base", "uses", "heuristic"),
        ("type:py:app.lib.shop.orders.Special", "type:py:app.lib.shop.models.Base", "extends",
         "heuristic"),
    }
    unresolved = {(r.source, r.name, r.reason) for r in graph.unresolved.values()}
    assert ("type:py:app.lib.shop.orders.Order", "Missing", "not found in the repository") \
        in unresolved
    assert ("type:py:tests.test_orders", "....", "relative import above the top-level package") \
        in unresolved


def test_a_shared_cache_keeps_java_and_python_parses_apart(repo):
    # Empty files have the same blob SHA in both languages.
    head = commit(repo, {"a/Empty.java": "", "a/empty.py": "", "a/B.java": "class B {}\n"}, "base")
    registry = load_plugins()
    cache: dict = {}
    from codedna.plugins.languages import commit_graph

    first = commit_graph(repo.path, head, registry=registry, cache=cache)
    again = commit_graph(repo.path, head, registry=registry, cache=cache)

    assert "type:py:a.empty" in first.nodes and "type:B" in first.nodes
    assert first.nodes.keys() == again.nodes.keys()


# --- discovery ----------------------------------------------------------------------


def test_pytest_tests_are_discovered_with_java_tests(mixed):
    repo, head = mixed

    report = discover_tests(repo.path, head).to_dict()

    assert [(t["id"], t["language"], t["methods"]) for t in report["tests"]] == [
        ("shop.PriceTest", "java", ["cents"]),
        ("py:tests.test_models", "python", ["test_total"]),
        ("py:tests.test_report", "python", ["TestRender.test_render"]),
        ("py:tests.test_util", "python", ["test_dump"]),
    ]
    assert report["languages"]["python"] == {"build_tool": "pytest", "test_count": 3}


def test_pytest_settings_change_what_is_discovered(repo):
    head = commit(repo, {
        "setup.cfg": "[tool:pytest]\npython_files = check_*.py\ntestpaths = suite\n",
        "suite/check_a.py": "def test_a():\n    pass\n",
        "other/check_b.py": "import unittest\n\n\nclass Case(unittest.TestCase):\n"
                            "    def test_b(self):\n        pass\n",
        "suite/test_ignored.py": "def test_c():\n    pass\n",
        "suite/check_init.py": "class TestHasInit:\n    def __init__(self):\n        pass\n\n"
                               "    def test_d(self):\n        pass\n",
        "build/check_built.py": "def test_e():\n    pass\n",
    }, "base")

    config = read_config(repo.path, head)
    report = discover_tests(repo.path, head, language="python")

    assert config.source == "setup.cfg" and config.testpaths == ("suite",)
    assert [(t.id, t.methods, t.runs_by_default) for t in report.tests] == [
        ("py:other.check_b", ["Case.test_b"], False),  # outside testpaths
        ("py:suite.check_a", ["test_a"], True),
    ]


def test_a_dot_pytest_ini_is_read_like_pytest_ini(repo):
    head = commit(repo, {".pytest.ini": "[pytest]\npython_functions = check_\n",
                         "pyproject.toml": "[tool.pytest.ini_options]\npython_functions = 'x'\n",
                         "tests/test_a.py": "def check_a():\n    pass\n\n\ndef test_b():\n"
                                            "    pass\n"}, "base")

    report = discover_tests(repo.path, head, language="python")

    assert read_config(repo.path, head).source == ".pytest.ini"
    assert [(t.id, t.methods) for t in report.tests] == [("py:tests.test_a", ["check_a"])]


# --- selection and impact in a mixed repository -------------------------------------


def test_a_python_change_selects_only_the_python_tests_that_depend_on_it(mixed):
    repo, base = mixed
    head = commit(repo, {"src/shop/models.py": MODELS.replace('"base"', '"BASE"')}, "edit")

    impact = compute_impact(repo.path, base, head)
    report = select_tests(repo.path, base, head, "dependency")

    assert [s.node for s in impact.seeds] == ["type:py:shop.models.Base"]
    assert [t["type"] for t in impact.candidate_tests] == [
        "type:py:tests.test_models", "type:py:tests.test_report"]
    assert [s.test for s in report.selected] == ["py:tests.test_models", "py:tests.test_report"]
    assert [s.file for s in report.selected] == ["tests/test_models.py", "tests/test_report.py"]
    assert report.skipped == ["py:tests.test_util", "shop.PriceTest"]
    assert report.total_tests == 4


def test_a_java_change_selects_only_java_tests(mixed):
    repo, base = mixed
    head = commit(repo, {"src/main/java/shop/Price.java":
                         PROJECT["src/main/java/shop/Price.java"].replace("100", "101")}, "edit")

    report = select_tests(repo.path, base, head, "dependency")

    assert [s.test for s in report.selected] == ["shop.PriceTest"]


def test_python_changes_without_python_tests_fall_back_to_retest_all(repo):
    base = commit(repo, {k: v for k, v in PROJECT.items() if k.endswith(".java")}
                  | {"scripts/release.py": "VERSION = 1\n"}, "base")
    head = commit(repo, {"scripts/release.py": "VERSION = 2\n"}, "head")

    report = select_tests(repo.path, base, head, "dependency")

    assert [s.test for s in report.selected] == ["shop.PriceTest"]
    assert "unanalysed file changed (scripts/release.py)" in report.selected[0].reasons[0]
    assert any("1 changed python file(s) count as unanalysed: no python tests" in w
               for w in report.warnings)


def test_without_the_python_plugin_python_files_are_not_analysed(java_only_plugins, mixed):
    repo, base = mixed
    head = commit(repo, {"src/shop/util.py": "VALUE = 1\n"}, "edit")

    report = analyze_changes(repo.path, base, head)
    impact = compute_impact(repo.path, base, head)

    assert report.changed_files[0].language is None
    assert any("1 changed .py file(s) not analysed: the python plugin (codedna-python)" in w
               for w in report.warnings)
    assert impact.unanalysed_changes[0]["path"] == "src/shop/util.py"
    assert [t.id for t in discover_tests(repo.path, head).tests] == ["shop.PriceTest"]


# --- running tests ------------------------------------------------------------------


def test_running_needs_allow_build(mixed, tmp_path):
    repo, head = mixed
    with pytest.raises(TestRunError, match="allow-build"):
        run_tests(repo.path, head, tmp_path / "out", allow_build=False)
    with pytest.raises(TestRunError, match="not discovered"):
        run_tests(repo.path, head, tmp_path / "out", allow_build=True,
                  selected_tests=["py:tests.nope"])
    assert not (tmp_path / "out").exists()


def test_selected_python_tests_run_with_pytest(mixed, tmp_path, capsys):
    repo, head = mixed
    output = tmp_path / "out"

    code = main(["run-tests", "--repo", str(repo.path), "--rev", head, "--output-dir",
                 str(output), "--allow-build", "--python", sys.executable,
                 "--tests", "py:tests.test_models", "py:tests.test_report"])

    assert code == EXIT_OK, capsys.readouterr().err
    saved = json.loads((output / RESULTS_FILE).read_text(encoding="utf-8"))
    assert saved["tool"] == "pytest" and saved["exit_codes"] == [0]
    assert [(t["id"], t["status"], [c["name"] for c in t["cases"]]) for t in saved["tests"]] == [
        ("py:tests.test_models", "passed", ["test_total"]),
        ("py:tests.test_report", "passed", ["TestRender.test_render"]),
    ]
    assert not (output / "checkout").exists()


def test_a_failing_python_test_is_reported(mixed, tmp_path):
    repo, _ = mixed
    head = commit(repo, {"tests/test_util.py": "def test_dump():\n    assert False, 'boom'\n"},
                  "break")

    run, coverage = run_tests(repo.path, head, tmp_path / "out", allow_build=True,
                              selected_tests=["py:tests.test_util"],
                              python_command=[sys.executable], per_test_coverage=True)

    assert coverage is None and run.failing_tests == ["py:tests.test_util"]
    assert run.tests["py:tests.test_util"].cases[0].message.startswith("AssertionError: boom")
    assert "per-test coverage is not supported for Python" in run.warnings[0]


class FakeJava:
    """Stands in for Maven: records what it was asked to run."""

    name, display_name, version, api_version = "java", "Fake Java", "0", "1.1"
    file_suffixes = (".java",)

    def __init__(self, real):
        self.real, self.calls = real, []

    def handles(self, path):
        return path.endswith(".java")

    def parse(self, source):
        return None

    def build_graph(self, *args, **kwargs):
        return self.real.build_graph(*args, **kwargs)

    def discover_tests(self, repo, commit):
        return self.real.discover_tests(repo, commit)

    def run_tests(self, repo_path, revision, output_dir, *, allow_build,
                  per_test_coverage=False, **options):
        self.calls.append((str(output_dir), options))
        run = TestRunResult(str(repo_path), revision, "maven", [["mvn", "test"]], [0], 0.5, False)
        for test in options.get("selected_tests") or ["shop.PriceTest"]:
            run.tests[test] = TestClassResult(test, "passed", 0.5)
        return run, None


def test_a_mixed_run_splits_tests_by_language_and_joins_results(mixed, tmp_path):
    repo, head = mixed
    real = load_plugins()
    fake = FakeJava(real.plugins["java"])
    registry = PluginRegistry(plugins={"java": fake, "python": real.plugins["python"]})
    output = tmp_path / "out"

    run, _ = run_tests(repo.path, head, output, allow_build=True, registry=registry,
                       selected_tests=["shop.PriceTest", "py:tests.test_util"],
                       python_command=[sys.executable], maven_command=["mvn"])

    assert fake.calls == [(str(output.resolve() / "java"),
                           {"selected_tests": ["shop.PriceTest"],
                            "python_command": [sys.executable], "maven_command": ["mvn"]})]
    assert run.tool == "maven+pytest"
    assert sorted(run.tests) == ["py:tests.test_util", "shop.PriceTest"]
    saved = json.loads((output / RESULTS_FILE).read_text(encoding="utf-8"))
    assert [t["id"] for t in saved["tests"]] == ["py:tests.test_util", "shop.PriceTest"]
    assert (output / "python" / RESULTS_FILE).is_file()


def test_the_java_plugin_ignores_python_options(mixed, tmp_path):
    from codedna_java.maven import BuildError

    repo, head = mixed
    with pytest.raises(BuildError, match="allow-build"):  # not a TypeError
        load_plugins().plugins["java"].run_tests(repo.path, head, tmp_path, allow_build=False,
                                                 python_command=["python"])


def test_run_tests_cli_reports_a_missing_interpreter(mixed, tmp_path, capsys):
    repo, head = mixed

    code = main(["run-tests", "--repo", str(repo.path), "--rev", head, "--output-dir",
                 str(tmp_path / "out"), "--allow-build", "--python", str(tmp_path / "nope"),
                 "--tests", "py:tests.test_util"])

    assert code == EXIT_ANALYSIS_ERROR
    assert "Python interpreter not found" in capsys.readouterr().err


def test_discovery_reuses_graph_parse_cache_and_supports_legacy_plugins(mixed, monkeypatch):
    from codedna.plugins.languages import commit_graph, commit_tests
    import codedna_python.builder as builder
    repo, head = mixed
    original = builder.parse_python
    calls = []
    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(builder, "parse_python", counted)
    registry = load_plugins()
    cache = {}
    commit_graph(repo.path, head, registry=registry, cache=cache)
    parsed = len(calls)
    assert parsed > 0
    first = commit_tests(repo.path, head, registry=registry, cache=cache)
    again = commit_tests(repo.path, head, registry=registry, cache=cache)
    assert first.to_dict() == again.to_dict()
    assert len(calls) == parsed
    class LegacyDiscovery:
        name = "legacy"
        def discover_tests(self, repo, commit):
            return first.reports["python"]
    legacy = PluginRegistry(plugins={"legacy": LegacyDiscovery()})
    assert commit_tests(repo.path, head, registry=legacy, cache=cache).tests


def test_runner_prefers_original_project_environment_without_executing_it(repo, monkeypatch):
    import os
    import codedna_python.runner as runner
    relative = "Scripts/python.exe" if os.name == "nt" else "bin/python"
    candidate = repo.path / ".venv" / relative
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(b"test interpreter placeholder; never executed")
    monkeypatch.setattr(runner.shutil, "which", lambda _: "/unrelated/python")
    assert runner.find_python(repo.path) == [str(candidate)]


def test_frozen_core_cannot_masquerade_as_project_python(repo, monkeypatch):
    import codedna_python.runner as runner
    monkeypatch.setattr(runner.shutil, "which", lambda _: None)
    monkeypatch.setattr(runner.sys, "frozen", True, raising=False)
    with pytest.raises(runner.PytestRunError, match="not a project Python interpreter"):
        runner.find_python(repo.path)


def test_source_runner_keeps_interpreter_fallback(repo, monkeypatch):
    import codedna_python.runner as runner
    monkeypatch.setattr(runner.shutil, "which", lambda _: None)
    monkeypatch.delattr(runner.sys, "frozen", raising=False)
    assert runner.find_python(repo.path) == [sys.executable]
