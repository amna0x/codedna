"""The Java language plugin (Maven/Gradle, JUnit 4/5, JaCoCo).

Registered under the ``codedna.languages`` entry point (D-018, D-054). The
core reaches Java only through this class, so CodeDNA starts and analyses Git
changes without it; Java files are then reported as not analysed.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

from codedna.plugins.base import PLUGIN_API_VERSION

from codedna_java import __version__
from codedna_java.builder import build_graph_for_commit
from codedna_java.discovery import discover_tests_for_commit
from codedna_java.mapping import attach_java_declarations
from codedna_java.maven import run_maven_tests
from codedna_java.parser import TYPE_NODES, parse_java


class JavaPlugin:
    name = "java"
    display_name = "Java (Maven, Gradle, JUnit 4/5, JaCoCo)"
    version = __version__
    api_version = PLUGIN_API_VERSION
    file_suffixes = (".java",)
    type_kinds = frozenset(TYPE_NODES.values())

    def handles(self, path: str) -> bool:
        return path.endswith(self.file_suffixes)

    def parse(self, source: bytes):
        return parse_java(source)

    def attach_declarations(self, report) -> None:
        attach_java_declarations(report)

    def build_graph(self, repo: Path, commit: str, *, include_members: bool = True,
                    cache: dict | None = None):
        return build_graph_for_commit(repo, commit, include_members=include_members, cache=cache)

    def discover_tests(self, repo: Path, commit: str, *, cache: dict | None = None):
        return discover_tests_for_commit(repo, commit, cache=cache)

    def run_tests(self, repo_path: str | Path, revision: str, output_dir: str | Path, *,
                  allow_build: bool, per_test_coverage: bool = False, **options: Any):
        # Options meant for other plugins (python_command, say) are ignored.
        known = inspect.signature(run_maven_tests).parameters
        return run_maven_tests(repo_path, revision, output_dir, allow_build=allow_build,
                               per_test_coverage=per_test_coverage,
                               **{k: v for k, v in options.items() if k in known})

    def risk_select(self, repo_path, base, head, **options):
        """Optional capability: live risk-based selection (D-041)."""
        from codedna_java.live import recommend
        return recommend(repo_path, base, head, **options)


    def find_witness(self, request):
        """Optional experimental capability; only the consented worker invokes it."""
        from codedna_java.witness import find_witness
        return find_witness(request)
