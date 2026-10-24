"""Uncommitted changes are analysed through a snapshot commit (WORKTREE)."""

from __future__ import annotations

import pytest

from codedna.git_analysis import extract_changes
from codedna.git_analysis.git import WORKTREE, InvalidCommitError, resolve_commit
from codedna.impact_analysis import compute_impact

CORE = "package a;\npublic class Core {\n    int value() { return 1; }\n}\n"
USER = "package a;\npublic class User {\n    Core core;\n}\n"


def test_worktree_changes_are_analysed_without_touching_refs_or_index(repo):
    repo.write(".gitignore", "build/\n")
    repo.write("a/Core.java", CORE)
    repo.write("a/User.java", USER)
    head = repo.commit("base")
    repo.git("tag", "base")
    repo.write("a/Core.java", CORE.replace("return 1", "return 2"))  # unstaged edit
    repo.write("a/New.java", "package a;\nclass New {}\n")  # untracked
    repo.write("build/Out.java", "class Out {}\n")  # ignored
    status_before = repo.git("status", "--porcelain")

    changes = extract_changes(repo.path, "HEAD", WORKTREE)

    assert {f.path for f in changes.changed_files} == {"a/Core.java", "a/New.java"}
    assert changes.base_commit == head and changes.head_commit != head
    assert repo.git("rev-parse", "HEAD") == head
    assert repo.git("status", "--porcelain") == status_before  # index untouched
    assert resolve_commit(repo.path, WORKTREE) == changes.head_commit  # reproducible
    impacted = {n.node for n in compute_impact(repo.path, "HEAD", WORKTREE).impacted}
    assert "type:a.User" in impacted


def test_filter_drivers_are_refused_rather_than_run(repo):
    repo.write(".gitattributes", "*.bin filter=lfs\n")
    repo.write("a/Core.java", CORE)
    repo.commit("base")
    repo.write("data.bin", "x")

    with pytest.raises(InvalidCommitError, match="filter drivers"):
        resolve_commit(repo.path, WORKTREE)
