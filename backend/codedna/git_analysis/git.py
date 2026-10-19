"""Safe, minimal wrapper around the Git command-line tool.

Design rules (see docs/DECISIONS.md, D-003):

* Git is always called with an argument list, never through a shell
  (no ``shell=True``), so paths and SHAs cannot inject shell commands.
* User-supplied revisions are validated before use and passed after
  ``--end-of-options`` so a value like ``--output=x`` is never read as an
  option.
* Features that could run code configured inside the analysed repository
  (external diff drivers, textconv filters, fsmonitor hooks) are disabled.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

# Options prepended to every git invocation. They stop repository-local
# configuration from launching helper programs during read-only analysis.
_SAFE_CONFIG = (
    "-c", "core.fsmonitor=false",
    "-c", "core.quotePath=false",
)


class CodeDNAGitError(Exception):
    """Base class for errors raised while analysing a Git repository."""


class InvalidRepositoryError(CodeDNAGitError):
    """The given path does not exist or is not a Git working tree."""


class InvalidCommitError(CodeDNAGitError):
    """A revision could not be resolved to a commit."""


class GitCommandError(CodeDNAGitError):
    """Git could not be run, or exited with an unexpected error."""


def run_git(repo: Path, *args: str) -> str:
    """Run ``git <args>`` inside ``repo`` and return its standard output.

    Raises GitCommandError if git is missing or exits with a non-zero code.
    """
    command = ["git", *_SAFE_CONFIG, *args]
    try:
        completed = subprocess.run(
            command,
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as exc:
        raise GitCommandError("git executable not found on PATH") from exc
    except OSError as exc:
        raise GitCommandError(f"could not run git: {exc}") from exc

    if completed.returncode != 0:
        message = completed.stderr.strip() or f"exit code {completed.returncode}"
        raise GitCommandError(f"git {' '.join(args)} failed: {message}")
    return completed.stdout


def resolve_repository(path: str | Path) -> Path:
    """Return the absolute top-level directory of the repository at ``path``."""
    candidate = Path(path).expanduser()
    if not candidate.exists():
        raise InvalidRepositoryError(f"repository path does not exist: {candidate}")
    if not candidate.is_dir():
        raise InvalidRepositoryError(f"repository path is not a directory: {candidate}")

    try:
        top_level = run_git(candidate, "rev-parse", "--show-toplevel").strip()
    except GitCommandError as exc:
        raise InvalidRepositoryError(f"not a Git repository: {candidate}") from exc
    return Path(top_level).resolve()


def resolve_commit(repo: Path, revision: str) -> str:
    """Resolve ``revision`` (SHA, branch, tag, ``HEAD~1``...) to a full commit SHA."""
    if not revision or not revision.strip():
        raise InvalidCommitError("commit revision must not be empty")
    if revision.startswith("-"):
        raise InvalidCommitError(f"invalid commit revision: {revision!r}")

    try:
        sha = run_git(
            repo, "rev-parse", "--verify", "--quiet", "--end-of-options",
            f"{revision}^{{commit}}",
        ).strip()
    except GitCommandError as exc:
        raise InvalidCommitError(f"unknown commit: {revision!r}") from exc
    if not sha:
        raise InvalidCommitError(f"unknown commit: {revision!r}")
    return sha
