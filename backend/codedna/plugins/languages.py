"""The core's only way into language-specific analysis (D-018, D-054).

Every command that needs declarations, a code graph or test discovery goes
through these helpers, which ask the installed language plugins. Without a
plugin, change listing still works and the files it would have analysed are
reported as not analysed; commands that cannot work at all raise
``PluginMissingError`` with the install command.
"""

from __future__ import annotations

from pathlib import Path

from codedna.git_analysis.changes import ChangeReport, extract_changes
from codedna.git_analysis.git import resolve_commit, resolve_repository
from codedna.plugins.base import LanguagePlugin
from codedna.plugins.registry import PluginRegistry, load_plugins

# Languages the core knows by name, so it can say what to install. Analysis
# itself never looks at this table.
KNOWN = {"java": ("codedna-java", ".java", "python -m pip install -e plugins/codedna-java")}


class PluginMissingError(RuntimeError):
    """The language plugin a command needs is not installed (or failed to load)."""


def require(language: str = "java", registry: PluginRegistry | None = None) -> LanguagePlugin:
    registry = registry or load_plugins()
    plugin = registry.get(language)
    if plugin is not None:
        return plugin
    package, _, command = KNOWN.get(language, (f"a {language} plugin", "", ""))
    message = f"the {language} language plugin ({package}) is not installed"
    if command:
        message += f"; install it with: {command}"
    problems = [p for p in registry.problems if language in p]
    if problems:
        message += f" (load problems: {'; '.join(problems)})"
    raise PluginMissingError(message)


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
    for plugin in registry.plugins.values():
        attach = getattr(plugin, "attach_declarations", None)  # optional since API 1.1
        if attach is not None:
            attach(report)
    for language, (package, suffix, command) in KNOWN.items():
        missed = [c.path for c in report.changed_files
                  if c.path.endswith(suffix) or (c.old_path or "").endswith(suffix)]
        if missed and registry.get(language) is None:
            report.warnings.append(
                f"{len(missed)} changed {suffix} file(s) not analysed: the {language} plugin "
                f"({package}) is not installed; install it with: {command}")
    return report


def build_graph(repo_path: str | Path, revision: str, *, include_members: bool = True,
                language: str = "java", registry: PluginRegistry | None = None):
    plugin = require(language, registry)
    repo = resolve_repository(repo_path)
    return plugin.build_graph(repo, resolve_commit(repo, revision),
                              include_members=include_members)


def discover_tests(repo_path: str | Path, revision: str = "HEAD", *, language: str = "java",
                   registry: PluginRegistry | None = None):
    plugin = require(language, registry)
    repo = resolve_repository(repo_path)
    return plugin.discover_tests(repo, resolve_commit(repo, revision))
