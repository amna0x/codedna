"""The language-plugin interface (docs/DECISIONS.md D-018).

A plugin supplies everything that depends on one programming language; the
core (Git changes, graph model, impact, selection, history, ML) stays
language-neutral. Every plugin must produce the shared schema: declaration
IDs, ``CodeGraph`` nodes/edges with confirmed/heuristic labels, unresolved
references, and discovered test classes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

# Plugin API version. Plugins declaring another major version are refused;
# bump the major only for incompatible interface changes. 1.1 (D-054) adds two
# optional members, ``type_kinds`` and ``attach_declarations``: the core reads
# them with ``getattr``, so 1.0 plugins keep loading (their changes then stay at
# file level). Optional members are not part of the Protocol below, because
# ``isinstance`` would reject plugins that lack them.
PLUGIN_API_VERSION = "1.1"


@runtime_checkable
class LanguagePlugin(Protocol):
    name: str  # e.g. "java"
    display_name: str  # e.g. "Java (Maven, JUnit)"
    version: str  # plugin version
    api_version: str  # plugin API version it was written for, e.g. "1.0"
    file_suffixes: tuple[str, ...]  # e.g. (".java",)
    # Optional since 1.1: type_kinds: frozenset[str], graph node kinds that are
    # types (e.g. {"class", "enum"}); default: none.

    def handles(self, path: str) -> bool:
        """True if this plugin analyses the file at ``path``."""

    def parse(self, source: bytes) -> Any:
        """Declarations with line ranges for one source file."""

    # Optional since 1.1: attach_declarations(report) fills the declaration
    # mapping of the files it handles in a ``ChangeReport`` (in place).

    def build_graph(self, repo: Path, commit: str, *, include_members: bool = True,
                    cache: dict | None = None) -> Any:
        """``CodeGraph`` (shared schema) for all files of ``commit`` this plugin handles."""

    def discover_tests(self, repo: Path, commit: str) -> Any:
        """Statically discovered test classes of ``commit`` (``DiscoveryReport``)."""

    def run_tests(self, repo_path: str | Path, revision: str, output_dir: str | Path, *,
                  allow_build: bool, per_test_coverage: bool = False, **options: Any) -> Any:
        """Run tests (executes project code; only with ``allow_build``, D-014).

        ``options`` may hold options for other plugins (``maven_command``,
        ``python_command``...), because the core passes the same options to
        every plugin of a mixed repository: ignore the ones you do not know.
        """


def api_compatible(version: str) -> bool:
    """Same major as the core, and no newer minor (it could rely on members the core lacks)."""
    try:
        major, minor = (int(part) for part in str(version).split(".")[:2])
        core_major, core_minor = (int(part) for part in PLUGIN_API_VERSION.split("."))
    except ValueError:
        return False
    return major == core_major and minor <= core_minor
