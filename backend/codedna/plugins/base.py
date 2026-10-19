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

# Major version of the plugin API. Plugins declaring another major version are
# refused; bump it only for incompatible interface changes.
PLUGIN_API_VERSION = "1.0"


@runtime_checkable
class LanguagePlugin(Protocol):
    name: str  # e.g. "java"
    display_name: str  # e.g. "Java (Maven, JUnit)"
    version: str  # plugin version
    api_version: str  # plugin API version it was written for, e.g. "1.0"
    file_suffixes: tuple[str, ...]  # e.g. (".java",)

    def handles(self, path: str) -> bool:
        """True if this plugin analyses the file at ``path``."""

    def parse(self, source: bytes) -> Any:
        """Declarations with line ranges for one source file."""

    def build_graph(self, repo: Path, commit: str, *, include_members: bool = True,
                    cache: dict | None = None) -> Any:
        """``CodeGraph`` (shared schema) for all files of ``commit`` this plugin handles."""

    def discover_tests(self, repo: Path, commit: str) -> Any:
        """Statically discovered test classes of ``commit`` (``DiscoveryReport``)."""

    def run_tests(self, repo_path: str | Path, revision: str, output_dir: str | Path, *,
                  allow_build: bool, per_test_coverage: bool = False, **options: Any) -> Any:
        """Run tests (executes project code; only with ``allow_build``, D-014)."""
