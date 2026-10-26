"""Find installed language plugins.

Plugins are ordinary Python packages that register a factory under the
entry-point group ``codedna.languages`` in their ``pyproject.toml``::

    [project.entry-points."codedna.languages"]
    python = "codedna_python:PythonPlugin"

Java is a plugin too (``codedna-java``, D-054): the core has no built-in
language. Plugins with an incompatible API version, or that fail to load, are
skipped and reported, never silently half-loaded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.metadata import entry_points

from codedna.plugins.base import PLUGIN_API_VERSION, LanguagePlugin, api_compatible

ENTRY_POINT_GROUP = "codedna.languages"


@dataclass
class PluginRegistry:
    plugins: dict[str, LanguagePlugin] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)

    def register(self, plugin: object, source: str) -> None:
        if not isinstance(plugin, LanguagePlugin):
            self.problems.append(f"{source}: does not implement the LanguagePlugin interface")
            return
        if not api_compatible(plugin.api_version):
            self.problems.append(
                f"{source}: plugin API {plugin.api_version} is incompatible with "
                f"core API {PLUGIN_API_VERSION}")
            return
        if plugin.name in self.plugins:
            self.problems.append(f"{source}: language {plugin.name!r} is already provided; skipped")
            return
        self.plugins[plugin.name] = plugin

    def get(self, name: str) -> LanguagePlugin | None:
        return self.plugins.get(name)

    def for_path(self, path: str) -> LanguagePlugin | None:
        return next((p for p in self.plugins.values() if p.handles(path)), None)

    def describe(self) -> dict:
        return {
            "api_version": PLUGIN_API_VERSION,
            "plugins": [
                {"name": p.name, "display_name": p.display_name, "version": p.version,
                 "api_version": p.api_version, "file_suffixes": list(p.file_suffixes)}
                for p in self.plugins.values()
            ],
            "problems": self.problems,
        }


def load_plugins() -> PluginRegistry:
    registry = PluginRegistry()
    for entry_point in sorted(entry_points(group=ENTRY_POINT_GROUP), key=lambda e: e.name):
        try:
            factory = entry_point.load()
            registry.register(factory(), f"entry point {entry_point.name}")
        except Exception as exc:  # a broken plugin must not break the core
            registry.problems.append(f"entry point {entry_point.name}: failed to load ({exc})")
    return registry
