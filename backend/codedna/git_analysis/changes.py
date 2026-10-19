"""File-level change extraction between two commits.

This is the first stage of the CodeDNA pipeline. It answers: *which files
changed between BASE and HEAD, how, and on which lines?* Class- and
method-level mapping is added later by ``java_analysis``.

Line-range conventions:

* ``changed_lines``: inclusive ``[start, end]`` ranges in the **head**
  version of the file covering added or modified lines.
* ``removed_lines``: inclusive ``[start, end]`` ranges in the **base**
  version of the file covering deleted or replaced lines.

A pure deletion inside a file therefore shows up only in ``removed_lines``.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from codedna.git_analysis.git import (
    GitCommandError,
    resolve_commit,
    resolve_repository,
    run_git,
)

# Diff flags shared by every diff call: detect renames, never run external
# diff drivers or textconv filters configured in the analysed repository.
_DIFF_FLAGS = ("--no-color", "--no-ext-diff", "--no-textconv", "-M")

_STATUS_NAMES = {
    "A": "added",
    "C": "copied",
    "D": "deleted",
    "M": "modified",
    "R": "renamed",
    "T": "type_changed",
}

_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

LineRange = list[int]  # [start, end], inclusive, 1-based


@dataclass
class ChangedFile:
    """One file that differs between the base and head commits."""

    path: str
    status: str
    old_path: str | None = None
    similarity: int | None = None
    is_java: bool = False
    is_binary: bool = False
    changed_lines: list[LineRange] = field(default_factory=list)
    removed_lines: list[LineRange] = field(default_factory=list)


@dataclass
class ChangeReport:
    """Result of comparing two commits; serialised as the CLI's JSON output."""

    repository: str
    base_commit: str
    head_commit: str
    analysis_level: str
    changed_files: list[ChangedFile]
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def extract_changes(repo_path: str | Path, base: str, head: str) -> ChangeReport:
    """Compare ``base`` and ``head`` in ``repo_path`` and describe every changed file."""
    repo = resolve_repository(repo_path)
    base_sha = resolve_commit(repo, base)
    head_sha = resolve_commit(repo, head)

    warnings: list[str] = []
    changed_files: list[ChangedFile] = []
    for entry in _list_changed_paths(repo, base_sha, head_sha):
        status_code = entry[0]
        status = _STATUS_NAMES.get(status_code[0])
        if status is None:
            warnings.append(f"unrecognised git status {status_code!r} for {entry[-1]}; skipped")
            continue

        changed = ChangedFile(path=entry[-1], status=status)
        if status in ("renamed", "copied"):
            changed.old_path = entry[1]
            changed.similarity = int(status_code[1:]) if status_code[1:].isdigit() else None
        changed.is_java = changed.path.endswith(".java") or (
            changed.old_path is not None and changed.old_path.endswith(".java")
        )

        _attach_line_ranges(repo, base_sha, head_sha, changed)
        if changed.is_binary:
            warnings.append(f"binary file, line ranges unavailable: {changed.path}")
        changed_files.append(changed)

    return ChangeReport(
        repository=str(repo),
        base_commit=base_sha,
        head_commit=head_sha,
        analysis_level="file",
        changed_files=changed_files,
        warnings=warnings,
    )


def _list_changed_paths(repo: Path, base: str, head: str) -> list[tuple[str, ...]]:
    """Return ``(status, path)`` or ``(status, old_path, new_path)`` tuples.

    ``-z`` makes git separate fields with NUL bytes, so paths containing
    spaces, tabs or quotes are returned verbatim without escaping.
    """
    output = run_git(repo, "diff", "--name-status", "-z", *_DIFF_FLAGS, base, head)
    tokens = output.split("\0")
    if tokens and tokens[-1] == "":
        tokens.pop()

    entries: list[tuple[str, ...]] = []
    index = 0
    while index < len(tokens):
        status = tokens[index]
        path_count = 2 if status[:1] in ("R", "C") else 1
        paths = tokens[index + 1 : index + 1 + path_count]
        if len(paths) != path_count:
            raise GitCommandError(f"unexpected git diff --name-status output near {status!r}")
        entries.append((status, *paths))
        index += 1 + path_count
    return entries


def _attach_line_ranges(repo: Path, base: str, head: str, changed: ChangedFile) -> None:
    """Fill ``changed_lines``/``removed_lines`` from a zero-context diff of one file."""
    paths = [changed.path] if changed.old_path is None else [changed.old_path, changed.path]
    patch = run_git(repo, "diff", "--unified=0", *_DIFF_FLAGS, base, head, "--", *paths)

    for line in patch.splitlines():
        if line.startswith("Binary files ") or line == "GIT binary patch":
            changed.is_binary = True
            continue
        match = _HUNK_HEADER.match(line)
        if not match:
            continue
        old_start, old_count, new_start, new_count = match.groups()
        old_range = _to_range(int(old_start), old_count)
        new_range = _to_range(int(new_start), new_count)
        if old_range:
            changed.removed_lines.append(old_range)
        if new_range:
            changed.changed_lines.append(new_range)


def _to_range(start: int, count: str | None) -> LineRange | None:
    """Convert a hunk ``start,count`` pair to an inclusive range (None if empty)."""
    length = 1 if count is None else int(count)
    if length == 0:
        return None
    return [start, start + length - 1]
