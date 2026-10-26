"""The core's only way into language-specific analysis (D-018, D-054, D-060).

Every command that needs declarations, a code graph, test discovery or a test
run goes through these helpers, which ask the installed language plugins.
Several plugins can work on one repository at once (a Java + Python project,
say): each analyses the files it handles, their graphs are joined, their tests
form one universe and a test run is split between them. No dependency between
two languages is analysed, so a change in one language never reaches the
other's tests through the graph (D-060).

Without a plugin, change listing still works and the files it would have
analysed are reported as not analysed; commands that cannot work at all raise
``PluginMissingError`` with the install command.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from codedna.dependency_graph.model import CodeGraph, union_graphs
from codedna.git_analysis.blobs import list_files
from codedna.git_analysis.changes import ChangedFile, ChangeReport, extract_changes
from codedna.git_analysis.git import CodeDNAGitError, resolve_commit, resolve_repository
from codedna.plugins.base import LanguagePlugin
from codedna.plugins.registry import PluginRegistry, load_plugins
from codedna.test_mapping.results import (
    COVERAGE_MAP_FILE,
    RESULTS_FILE,
    CoverageMap,
    TestRunResult,
    save_json,
)

# Languages the core knows by name, so it can say what to install. Analysis
# itself never looks at this table.
KNOWN = {
    "java": ("codedna-java", ".java", "python -m pip install -e plugins/codedna-java"),
    "python": ("codedna-python", ".py", "python -m pip install -e plugins/codedna-python"),
}


class PluginMissingError(RuntimeError):
    """The language plugin a command needs is not installed (or failed to load)."""


class TestRunError(CodeDNAGitError):
    """A test run across plugins cannot start (shown like a build error)."""

    __test__ = False  # not a pytest test class


def require(language: str = "java", registry: PluginRegistry | None = None) -> LanguagePlugin:
    registry = registry or load_plugins()
    plugin = registry.get(language)
    if plugin is not None:
        return plugin
    package, _, command = KNOWN.get(language, (f"a {language} plugin", "", ""))
    message = f"the {language} language plugin ({package}) is not installed"
    if command:
        message += f"; install it with: {command}"
    problems = [p for p in registry.problems if p.startswith(f"entry point {language}:")]
    if problems:
        message += f" (load problems: {'; '.join(problems)})"
    raise PluginMissingError(message)


def installed(registry: PluginRegistry | None = None) -> list[LanguagePlugin]:
    """Every installed plugin, by name; raises ``PluginMissingError`` if there is none.

    With no plugin at all the message names the Java plugin, the one CodeDNA
    bundles and installs by default.
    """
    registry = registry or load_plugins()
    if not registry.plugins:
        require("java", registry)
    return [registry.plugins[name] for name in sorted(registry.plugins)]


def plugin_for(path: str | None, registry: PluginRegistry) -> LanguagePlugin | None:
    """The installed plugin that handles ``path`` (first by name), or None."""
    if not path:
        return None
    return next((registry.plugins[name] for name in sorted(registry.plugins)
                 if registry.plugins[name].handles(path)), None)


def file_language(changed: ChangedFile, registry: PluginRegistry) -> str | None:
    plugin = plugin_for(changed.path, registry) or plugin_for(changed.old_path, registry)
    return plugin.name if plugin else None


def type_kinds(registry: PluginRegistry | None = None) -> frozenset[str]:
    """Graph node kinds that are types, over all installed plugins."""
    registry = registry or load_plugins()
    return frozenset().union(*(plugin_type_kinds(p) for p in registry.plugins.values()))


def plugin_type_kinds(plugin: LanguagePlugin) -> frozenset[str]:
    """Optional since plugin API 1.1; a 1.0 plugin reports no type kinds."""
    return frozenset(getattr(plugin, "type_kinds", ()))


def analyze_changes(repo_path: str | Path, base: str, head: str, *,
                    registry: PluginRegistry | None = None) -> ChangeReport:
    """File-level changes plus each installed plugin's declaration mapping."""
    registry = registry or load_plugins()
    report = extract_changes(repo_path, base, head)
    for name in sorted(registry.plugins):
        attach = getattr(registry.plugins[name], "attach_declarations", None)  # optional since 1.1
        if attach is not None:
            attach(report)
    for changed in report.changed_files:
        changed.language = file_language(changed, registry)
    for name in sorted(registry.plugins):
        plugin = registry.plugins[name]
        handled = [c for c in report.changed_files if c.language == name]
        if handled and getattr(plugin, "attach_declarations", None) is None:
            report.warnings.append(
                f"the {name} plugin (API {plugin.api_version}) does not map changes to "
                f"declarations; {len(handled)} changed file(s) stay at file level")
    for language, (package, suffix, command) in KNOWN.items():
        missed = [c.path for c in report.changed_files
                  if c.path.endswith(suffix) or (c.old_path or "").endswith(suffix)]
        if missed and registry.get(language) is None:
            report.warnings.append(
                f"{len(missed)} changed {suffix} file(s) not analysed: the {language} plugin "
                f"({package}) is not installed; install it with: {command}")
    return report


def build_graph(repo_path: str | Path, revision: str, *, include_members: bool = True,
                language: str | None = None, registry: PluginRegistry | None = None) -> CodeGraph:
    """The code graph of ``revision``: one plugin's, or all installed plugins' joined."""
    registry = registry or load_plugins()
    repo = resolve_repository(repo_path)
    commit = resolve_commit(repo, revision)
    if language is not None:
        return require(language, registry).build_graph(repo, commit,
                                                       include_members=include_members)
    return commit_graph(repo, commit, registry=registry, include_members=include_members)


def commit_graph(repo: Path, commit: str, *, registry: PluginRegistry,
                 include_members: bool = True, cache: dict | None = None) -> CodeGraph:
    """All installed plugins' graphs of one commit, joined (``union_graphs``).

    ``cache`` is shared by the plugins: each keys its parses so they cannot
    collide with another plugin's (Java by blob SHA, Python by ``("py", sha)``).
    """
    return union_graphs([plugin.build_graph(repo, commit, include_members=include_members,
                                            cache=cache)
                         for plugin in installed(registry)])


@dataclass
class CombinedDiscovery:
    """The discovered tests of every installed plugin, as one universe.

    Test IDs of different plugins never collide (Python's start with ``py:``).
    ``tests`` holds the plugins' own test objects, which all have ``id``,
    ``file`` and ``runs_by_default``.
    """

    repository: str
    commit: str
    reports: dict[str, Any] = field(default_factory=dict)  # plugin name -> DiscoveryReport
    _languages: dict[str, str] | None = field(default=None, init=False, repr=False,
                                              compare=False)

    @property
    def tests(self) -> list:
        return [test for name in sorted(self.reports) for test in self.reports[name].tests]

    @property
    def warnings(self) -> list[str]:
        return [warning for name in sorted(self.reports) for warning in self.reports[name].warnings]

    @property
    def build_tool(self) -> str | None:
        return next((r.build_tool for _, r in sorted(self.reports.items())
                     if getattr(r, "build_tool", None)), None)

    def language_of(self, test_id: str) -> str | None:
        """The plugin that discovered ``test_id`` (None if none did)."""
        if self._languages is None:
            self._languages = {}
            for name in sorted(self.reports, reverse=True):  # first plugin wins on a clash
                self._languages.update((t.id, name) for t in self.reports[name].tests)
        return self._languages.get(test_id)

    def to_dict(self) -> dict:
        tests, languages = [], {}
        for name in sorted(self.reports):
            data = self.reports[name].to_dict()
            tests.extend({**entry, "language": name} for entry in data["tests"])
            languages[name] = {"build_tool": data.get("build_tool"),
                               "test_count": data["test_count"]}
        return {"repository": self.repository, "commit": self.commit,
                "build_tool": self.build_tool, "test_count": len(tests), "tests": tests,
                "warnings": self.warnings, "languages": languages}


def discover_tests(repo_path: str | Path, revision: str = "HEAD", *,
                   language: str | None = None, registry: PluginRegistry | None = None):
    """Statically discovered tests: one plugin's report, or every plugin's combined."""
    registry = registry or load_plugins()
    repo = resolve_repository(repo_path)
    commit = resolve_commit(repo, revision)
    if language is not None:
        return require(language, registry).discover_tests(repo, commit)
    return commit_tests(repo, commit, registry=registry)


def commit_tests(repo: Path, commit: str, *, registry: PluginRegistry,
                 cache: dict | None = None) -> CombinedDiscovery:
    """Every installed plugin's tests at ``commit``; ``cache`` (parses by blob SHA) goes to Java."""
    def discover(plugin: Any):
        if cache is not None and plugin.name == "java":
            return plugin.discover_tests(repo, commit, cache=cache)
        return plugin.discover_tests(repo, commit)
    return CombinedDiscovery(str(repo), commit, {
        plugin.name: discover(plugin) for plugin in installed(registry)})


def run_tests(repo_path: str | Path, revision: str, output_dir: str | Path, *, allow_build: bool,
              per_test_coverage: bool = False, selected_tests: list[str] | None = None,
              registry: PluginRegistry | None = None,
              **options: Any) -> tuple[TestRunResult, CoverageMap | None]:
    """Run tests with the plugin(s) whose tests the commit has (executes project code, D-014).

    One language: that plugin runs into ``output_dir`` exactly as on its own.
    Several: each runs its own tests into ``output_dir/<plugin>`` and the
    results are joined into ``output_dir/results.json``. ``selected_tests``
    is split by the plugin that discovered each test. Options a plugin does
    not know (``maven_command`` for Python, say) are ignored by it.
    """
    registry = registry or load_plugins()
    plugins = installed(registry)
    if not allow_build:
        # Each plugin refuses too; checking here means discovery never starts.
        raise TestRunError("running tests executes project code; pass --allow-build to confirm")
    repo = resolve_repository(repo_path)
    commit = resolve_commit(repo, revision)
    discovery = commit_tests(repo, commit, registry=registry)

    if selected_tests is None:
        chosen = {p.name: None for p in plugins if discovery.reports[p.name].tests}
        if not chosen:  # no test found statically: let the plugins that have files try
            chosen = {p.name: None for p in plugins if _has_files(repo, commit, p)} \
                or {p.name: None for p in plugins[:1]}
    else:
        chosen = {}
        for test_id in selected_tests:
            language = discovery.language_of(test_id)
            if language is None:
                raise TestRunError(f"selected test {test_id!r} was not discovered in {commit[:12]}")
            chosen.setdefault(language, []).append(test_id)
        if not chosen:  # nothing selected: the plugin still writes an empty result
            chosen = {plugins[0].name: []}

    if len(chosen) == 1:
        (name, tests), = chosen.items()
        return registry.plugins[name].run_tests(
            repo, commit, output_dir, allow_build=True, per_test_coverage=per_test_coverage,
            **({"selected_tests": tests} if tests is not None else {}), **options)

    output = Path(output_dir).resolve()
    if output.exists() and any(output.iterdir()):
        raise TestRunError(f"output directory is not empty: {output}")
    started = time.monotonic()
    joined = TestRunResult(repository=str(repo), commit=commit, tool="", commands=[],
                           exit_codes=[], duration_seconds=0.0,
                           per_test_coverage=per_test_coverage)
    coverage: CoverageMap | None = None
    tools = []
    for name, tests in sorted(chosen.items()):
        run, plugin_coverage = registry.plugins[name].run_tests(
            repo, commit, output / name, allow_build=True, per_test_coverage=per_test_coverage,
            **({"selected_tests": tests} if tests is not None else {}), **options)
        tools.append(run.tool)
        joined.commands.extend(run.commands)
        joined.exit_codes.extend(run.exit_codes)
        joined.tests.update(run.tests)
        joined.warnings.extend(f"{name}: {warning}" for warning in run.warnings)
        if plugin_coverage is not None:
            coverage = plugin_coverage  # only one plugin (Java) records coverage
    joined.tool = "+".join(tools)
    joined.duration_seconds = round(time.monotonic() - started, 3)
    save_json(joined.to_dict(), output / RESULTS_FILE)
    if coverage is not None:
        save_json(coverage.to_dict(), output / COVERAGE_MAP_FILE)
    return joined, coverage


def _has_files(repo: Path, commit: str, plugin: LanguagePlugin) -> bool:
    return any(plugin.handles(path) for path, _ in list_files(repo, commit))


__all__ = [
    "KNOWN", "CombinedDiscovery", "PluginMissingError", "TestRunError", "analyze_changes",
    "build_graph", "commit_graph", "commit_tests", "discover_tests", "file_language",
    "installed", "plugin_for", "plugin_type_kinds", "require", "run_tests", "type_kinds",
]
