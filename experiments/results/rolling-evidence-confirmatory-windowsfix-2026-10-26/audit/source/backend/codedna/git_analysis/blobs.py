"""Read files of a commit straight from Git's object store.

Nothing is checked out: ``git ls-tree`` lists the files and one
``git cat-file --batch`` call returns their contents. ``export_commit``
writes a commit's files into a separate directory (for running builds)
without touching the user's working tree.
"""

from __future__ import annotations

import io
import tarfile
from pathlib import Path

from codedna.git_analysis.git import GitCommandError, run_git, run_git_bytes


def list_files(repo: Path, commit: str, suffix: str = "") -> list[tuple[str, str]]:
    """Return sorted ``(path, blob_sha)`` for regular files in ``commit`` ending in ``suffix``."""
    output = run_git(repo, "ls-tree", "-r", "-z", "--full-tree", commit)
    files = []
    for entry in output.split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        mode, object_type, blob = meta.split()
        # Skip symlinks (120000) and submodules (commit objects).
        if object_type == "blob" and mode != "120000" and path.endswith(suffix):
            files.append((path, blob))
    return sorted(files)


def read_blobs(repo: Path, blobs: list[str]) -> dict[str, bytes]:
    """Read many blobs with a single ``git cat-file --batch`` call."""
    if not blobs:
        return {}
    output = run_git_bytes(repo, "cat-file", "--batch",
                           stdin="".join(f"{blob}\n" for blob in blobs).encode("ascii"))
    contents: dict[str, bytes] = {}
    position = 0
    for blob in blobs:
        header_end = output.index(b"\n", position)
        header = output[position:header_end].decode("ascii", errors="replace").split()
        if len(header) != 3 or header[0] != blob:
            raise GitCommandError(f"unexpected git cat-file output for {blob}: {header}")
        size = int(header[2])
        start = header_end + 1
        contents[blob] = output[start:start + size]
        position = start + size + 1  # content is followed by a newline
    return contents


def export_commit(repo: Path, commit: str, destination: Path) -> None:
    """Write the files of ``commit`` into ``destination`` (which must be empty or missing).

    Uses ``git archive``; extraction uses tarfile's ``data`` filter, which
    rejects absolute paths, ``..`` components and links leaving the directory.
    """
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise ValueError(f"export destination is not empty: {destination}")
    archive = run_git_bytes(repo, "archive", "--format=tar", commit)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        if hasattr(tarfile, "data_filter"):
            tar.extractall(destination, filter="data")
        else:  # Python < 3.11.4
            for member in tar.getmembers():
                target = (destination / member.name).resolve()
                if not target.is_relative_to(destination.resolve()) or member.issym() or member.islnk():
                    raise ValueError(f"unsafe path in archive: {member.name}")
            tar.extractall(destination)
