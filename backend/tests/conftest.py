"""Shared pytest fixtures: throwaway Git repositories built inside tmp_path."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption("--run-maven", action="store_true",
                     help="also run tests marked 'maven' (need Maven, a JDK and internet)")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-maven"):
        return
    skip = pytest.mark.skip(reason="needs real Maven; run with --run-maven")
    for item in items:
        if "maven" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def isolated_git_config(monkeypatch, tmp_path_factory):
    """Ignore the developer's global/system Git config so tests are reproducible.

    Settings such as ``core.autocrlf`` or ``commit.gpgsign`` on a laptop would
    otherwise change line endings or make commits fail.
    """
    empty_config = tmp_path_factory.mktemp("gitconfig") / "config"
    empty_config.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty_config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for name, value in {
        "GIT_AUTHOR_NAME": "CodeDNA Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "CodeDNA Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }.items():
        monkeypatch.setenv(name, value)


class GitRepo:
    """Tiny helper for building commit histories in tests."""

    def __init__(self, path: Path):
        self.path = path

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=self.path, capture_output=True, text=True, check=True,
            env=os.environ.copy(),
        )
        return result.stdout.strip()

    def write(self, relative: str, content: str) -> None:
        target = self.path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        # newline="\n" keeps line counts identical on Windows and Linux.
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)

    def write_bytes(self, relative: str, content: bytes) -> None:
        target = self.path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    def commit(self, message: str) -> str:
        self.git("add", "--all")
        self.git("commit", "--allow-empty", "--quiet", "-m", message)
        return self.git("rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path) -> GitRepo:
    path = tmp_path / "repo"
    path.mkdir()
    git_repo = GitRepo(path)
    git_repo.git("init", "--quiet")
    return git_repo


def numbered_lines(count: int, prefix: str = "line") -> str:
    return "".join(f"{prefix} {number}\n" for number in range(1, count + 1))
