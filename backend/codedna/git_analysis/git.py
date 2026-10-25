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

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

#: Pseudo-revision for uncommitted changes (tracked edits and untracked,
#: non-ignored files). Resolved to a snapshot commit; see snapshot_worktree.
WORKTREE = "WORKTREE"

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
    return _run(repo, args).decode("utf-8", errors="replace").replace("\r\n", "\n")


def run_git_bytes(repo: Path, *args: str, stdin: bytes | None = None) -> bytes:
    """Like :func:`run_git` but return raw bytes (e.g. file contents from ``git show``).

    Raw bytes keep line endings exactly as stored, so line numbers match the
    ones Git reports in diffs. ``stdin`` is fed to commands that read input,
    such as ``git cat-file --batch``.
    """
    return _run(repo, args, stdin)


def _run(repo: Path, args: tuple[str, ...], stdin: bytes | None = None,
         env: dict[str, str] | None = None) -> bytes:
    command = ["git", *_SAFE_CONFIG, *args]
    try:
        completed = subprocess.run(
            command,
            cwd=repo,
            input=stdin,
            capture_output=True,
            check=False,
            env={**os.environ, **env} if env else None,
        )
    except FileNotFoundError as exc:
        raise GitCommandError("git executable not found on PATH") from exc
    except OSError as exc:
        raise GitCommandError(f"could not run git: {exc}") from exc

    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        message = stderr or f"exit code {completed.returncode}"
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
        # Bare repositories (no working tree, e.g. the ones shipped with
        # RTPTorrent) are fine: all analysis reads Git objects, never files.
        try:
            bare = run_git(candidate, "rev-parse", "--is-bare-repository").strip() == "true"
        except GitCommandError:
            bare = False
        if bare:
            return candidate.resolve()
        raise InvalidRepositoryError(f"not a Git repository: {candidate}") from exc
    return Path(top_level).resolve()


def resolve_commit(repo: Path, revision: str) -> str:
    """Resolve ``revision`` (SHA, branch, tag, ``HEAD~1``, ``WORKTREE``...) to a full commit SHA."""
    if revision == WORKTREE:
        return snapshot_worktree(repo)
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


# Fixed identity and dates make the snapshot of an unchanged tree reproducible.
_SNAPSHOT_ENV = {
    "GIT_AUTHOR_NAME": "CodeDNA", "GIT_AUTHOR_EMAIL": "codedna@localhost",
    "GIT_COMMITTER_NAME": "CodeDNA", "GIT_COMMITTER_EMAIL": "codedna@localhost",
    "GIT_AUTHOR_DATE": "1970-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "1970-01-01T00:00:00Z",
}


# CodeDNA's own outputs are not part of the user's change, even in folders
# created before .codedna/.gitignore existed (D-053).
_OUTPUT_EXCLUDES = tuple(f":(exclude){path}" for path in (
    ".codedna/runs", ".codedna/history.db", ".codedna/history.csv",
    ".codedna/history.csv.partial"))


def snapshot_worktree(repo: Path) -> str:
    """Commit object for the working tree on top of HEAD, without touching refs or the index.

    A copy of the real index (its file stat cache means unchanged files are
    not hashed again; HEAD's tree if there is no index) receives
    ``git add -A`` (so ``.gitignore`` applies; CodeDNA's own run folders and
    history files are left out). The tree and an unreferenced
    commit are written to the object store, where ``git gc`` eventually
    removes them. The real index and every ref stay untouched. Repositories whose attributes name a
    filter driver (e.g. Git LFS) are refused: ``git add`` would run that
    driver's configured program.
    """
    head = resolve_commit(repo, "HEAD")
    listed = run_git_bytes(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    attributes = run_git_bytes(repo, "check-attr", "-z", "--stdin", "filter", stdin=listed)
    fields = attributes.split(b"\0")
    filtered = sorted({fields[i].decode("utf-8", "replace") for i in range(0, len(fields) - 2, 3)
                       if fields[i + 2] not in (b"unspecified", b"unset")})
    if filtered:
        raise InvalidCommitError(
            "uncommitted changes cannot be analysed: Git filter drivers apply to "
            f"{len(filtered)} file(s), e.g. {filtered[0]}; commit the changes instead")
    dirty = _dirty_submodules(repo)
    if dirty:
        # The parent only records each submodule's commit, so edits inside one
        # would silently vanish from the snapshot.
        raise InvalidCommitError(
            "uncommitted changes inside submodules cannot be analysed "
            f"({', '.join(dirty)}); commit them in the submodule first")
    with tempfile.TemporaryDirectory(prefix="codedna-index-") as tmp:
        index = Path(tmp) / "index"
        env = {"GIT_INDEX_FILE": str(index), **_SNAPSHOT_ENV}
        real = repo / run_git(repo, "rev-parse", "--git-path", "index").strip()
        try:
            shutil.copyfile(real, index)
        except OSError:  # no index yet (or unreadable): start from HEAD's tree
            _run(repo, ("read-tree", head), env=env)
        _run(repo, ("add", "-A", "--", ".", *_OUTPUT_EXCLUDES), env=env)
        tree = _run(repo, ("write-tree",), env=env).decode().strip()
        return _run(repo, ("commit-tree", tree, "-p", head, "-m", "CodeDNA working-tree snapshot"),
                    env=env).decode().strip()


def _dirty_submodules(repo: Path) -> list[str]:
    """Submodules with modified or untracked content but an unchanged commit."""
    status = run_git_bytes(repo, "status", "--porcelain=v2", "-z", "--ignore-submodules=none")
    dirty = []
    for entry in status.split(b"\0"):
        parts = entry.split(b" ", 8)
        # "1 XY S<c><m><u> ..." (or "2 ..." for renames): S = submodule.
        if parts[0] in (b"1", b"2") and len(parts) > 8 and parts[2].startswith(b"S") \
                and parts[2][1:2] != b"C" and (parts[2][2:3] == b"M" or parts[2][3:4] == b"U"):
            dirty.append(parts[-1].decode("utf-8", "replace"))
    return sorted(dirty)

