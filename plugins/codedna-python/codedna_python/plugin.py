"""The Python language plugin (ast, pytest).

Registered under the ``codedna.languages`` entry point (D-018, D-060). It
needs nothing beyond the standard library, and works next to the Java plugin
in one repository: each analyses its own files, and the core joins the
results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codedna.plugins.base import PLUGIN_API_VERSION

from codedna_python import __version__
from codedna_python.builder import build_graph_for_commit
from codedna_python.discovery import discover_tests_for_commit
from codedna_python.mapping import attach_python_declarations
from codedna_python.parser import TYPE_KINDS, parse_python
from codedna_python.runner import run_pytest


class PythonPlugin:
    name = "python"
    display_name = "Python (pytest)"
    version = __version__
    api_version = PLUGIN_API_VERSION
    file_suffixes = (".py",)
    type_kinds = TYPE_KINDS

    def handles(self, path: str) -> bool:
        return path.endswith(self.file_suffixes)

    def parse(self, source: bytes):
        return parse_python(source)

    def attach_declarations(self, report) -> None:
        attach_python_declarations(report)

    def build_graph(self, repo: Path, commit: str, *, include_members: bool = True,
                    cache: dict | None = None):
        return build_graph_for_commit(repo, commit, include_members=include_members, cache=cache)

    def discover_tests(self, repo: Path, commit: str, cache: dict | None = None):
        return discover_tests_for_commit(repo, commit, cache=cache)

    def run_tests(self, repo_path: str | Path, revision: str, output_dir: str | Path, *,
                  allow_build: bool, per_test_coverage: bool = False, **options: Any):
        # run_pytest ignores options meant for other plugins (maven_command, say).
        return run_pytest(repo_path, revision, output_dir, allow_build=allow_build,
                          per_test_coverage=per_test_coverage, **options)
