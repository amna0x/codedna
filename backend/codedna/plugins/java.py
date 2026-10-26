"""The built-in Java plugin (Maven, JUnit 4/5, JaCoCo).

Step 1 of the plugin refactor (D-018): the Java implementation still lives
in ``java_analysis``, ``dependency_graph``, ``test_mapping``; this class is the
single entry point the core uses to reach it. Moving the code into a
separately installable ``codedna-java`` package is planned for Milestone 7.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codedna import __version__
from codedna.dependency_graph.builder import build_graph_for_commit
from codedna.java_analysis.parser import parse_java
from codedna.plugins.base import PLUGIN_API_VERSION
from codedna.test_mapping.discovery import discover_tests_for_commit
from codedna.test_mapping.maven import run_maven_tests


class JavaPlugin:
    name = "java"
    display_name = "Java (Maven, JUnit 4/5, JaCoCo)"
    version = __version__
    api_version = PLUGIN_API_VERSION
    file_suffixes = (".java",)

    def handles(self, path: str) -> bool:
        return path.endswith(self.file_suffixes)

    def parse(self, source: bytes):
        return parse_java(source)

    def build_graph(self, repo: Path, commit: str, *, include_members: bool = True,
                    cache: dict | None = None):
        return build_graph_for_commit(repo, commit, include_members=include_members, cache=cache)

    def discover_tests(self, repo: Path, commit: str, *, cache: dict | None = None):
        return discover_tests_for_commit(repo, commit, cache=cache)

    def run_tests(self, repo_path: str | Path, revision: str, output_dir: str | Path, *,
                  allow_build: bool, per_test_coverage: bool = False, **options: Any):
        return run_maven_tests(repo_path, revision, output_dir, allow_build=allow_build,
                               per_test_coverage=per_test_coverage, **options)


    def risk_select(self, repo_path, base, head, **options):
        """Optional additive capability; Java live-feature construction stays here."""
        from codedna.plugins.java_live import recommend
        return recommend(repo_path,base,head,**options)
