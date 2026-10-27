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
    optional = []
    paths = set()
    import sys
    from pathlib import Path
    if getattr(sys, "frozen", False):
        from codedna.plugins import desktop_store
        try:
            optional = desktop_store.entry_points()
            paths = {path.resolve() for path in desktop_store.activate()}
        except Exception as exc:
            registry.problems.append(f"desktop plugin store: {exc}")

    def load(point, expected_site=None):
        try:
            factory = point.load()
            if expected_site is not None:
                import inspect
                if not Path(inspect.getfile(factory)).resolve().is_relative_to(expected_site):
                    raise ValueError("optional plugin did not load from its installed wheel; using bundled copy")
            registry.register(factory(), f"entry point {point.name}")
        except Exception as exc:  # a broken plugin must not break the core
            registry.problems.append(f"entry point {point.name}: failed to load ({exc})")

    for point in sorted(optional, key=lambda e: e.name):
        load(point, Path(point.dist.locate_file("")).resolve())
    overrides = set(registry.plugins)
    optional_names = {point.name for point in optional}
    if paths:
        from importlib.metadata import distributions
        # Default metadata lookup deduplicates distribution names; an optional
        # update would otherwise hide its bundled distribution completely.
        bundled_paths = [item for item in sys.path if Path(item).resolve() not in paths]
        available = [point for dist in distributions(path=bundled_paths)
                     for point in dist.entry_points if point.group == ENTRY_POINT_GROUP]
    else:
        available = entry_points(group=ENTRY_POINT_GROUP)
    for point in sorted(available, key=lambda e: e.name):
        # An optional copy is loaded once above. If it breaks after installation,
        # leave its error visible and let a bundled copy provide the language.
        if paths and Path(point.dist.locate_file("")).resolve() in paths:
            continue
        if point.name not in overrides:
            if point.name not in optional_names:
                load(point)
                continue
            # Import the bundled fallback without the failed optional namespace.
            # Keep any already-loaded bundled fallback stable on repeated calls.
            prefix = point.module.split(".")[0]
            original = sys.path[:]
            try:
                sys.path[:] = [item for item in sys.path if Path(item).resolve() not in paths]
                for name, module in list(sys.modules.items()):
                    file = getattr(module, "__file__", None)
                    if (name == prefix or name.startswith(prefix + ".")) and file:
                        if any(Path(file).resolve().is_relative_to(path) for path in paths):
                            del sys.modules[name]
                load(point)
            finally:
                sys.path[:] = original
    return registry
