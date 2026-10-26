"""Mine the first-parent commit history of a repository into the history store."""

from __future__ import annotations

from pathlib import Path

from codedna.git_analysis.git import resolve_commit, resolve_repository, run_git
from codedna.test_history.store import CommitRecord, FileChange, HistoryStore

_MARKER = "\x1ecommit "


def mine_history(repo_path: str | Path, store: HistoryStore, *, revision: str = "HEAD",
                 max_commits: int | None = None) -> list[CommitRecord]:
    """Store the first-parent history ending at ``revision`` (oldest first).

    First-parent history is the sequence of states the main branch actually
    went through, which is what CI tested. Merge commits are diffed against
    their first parent; renames are recorded as delete + add.
    """
    repo = resolve_repository(repo_path)
    tip = resolve_commit(repo, revision)
    args = ["log", "--first-parent", "--reverse", "--no-renames", "--numstat",
            "--diff-merges=first-parent", f"--format={_MARKER}%H %P%x09%ct"]
    if max_commits is not None:
        args.append(f"--max-count={max_commits}")
    output = run_git(repo, *args, tip)

    mined: list[tuple[CommitRecord, list[FileChange]]] = []
    for seq, block in enumerate(output.split(_MARKER)[1:]):
        header, *lines = block.split("\n")
        ids, committed_at = header.split("\t")
        sha, *parents = ids.split()
        files = []
        for line in lines:
            if not line.strip():
                continue
            added, deleted, path = line.split("\t", 2)
            files.append(FileChange(path, _count(added), _count(deleted)))
        mined.append((CommitRecord(sha, seq, parents[0] if parents else None,
                                   int(committed_at)), files))

    store.replace_commits(mined)
    store.set_meta("repository", str(repo))
    store.set_meta("mined_tip", tip)
    return [commit for commit, _ in mined]


def _count(value: str) -> int | None:
    return None if value == "-" else int(value)  # "-" = binary file
