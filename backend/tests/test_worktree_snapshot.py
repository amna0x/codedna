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


def test_staged_and_deleted_files_are_snapshotted_from_the_working_tree(repo):
    repo.write("a/Core.java", CORE)
    repo.write("a/User.java", USER)
    repo.commit("base")
    repo.write("a/Core.java", CORE.replace("return 1", "return 3"))
    repo.git("add", "a/Core.java")  # staged ...
    repo.write("a/Core.java", CORE.replace("return 1", "return 4"))  # ... then edited again
    (repo.path / "a/User.java").unlink()

    snapshot = resolve_commit(repo.path, WORKTREE)

    assert "return 4" in repo.git("show", f"{snapshot}:a/Core.java")
    assert "a/User.java" not in repo.git("ls-tree", "-r", "--name-only", snapshot)
    assert "return 3" in repo.git("show", ":a/Core.java")  # the real index is unchanged


def test_sparse_checkout_files_are_not_reported_as_deleted(repo):
    repo.write("a/Core.java", CORE)
    repo.write("b/Other.java", "package b;\nclass Other {}\n")
    repo.commit("base")
    repo.git("sparse-checkout", "set", "a")
    assert not (repo.path / "b/Other.java").exists()

    changes = extract_changes(repo.path, "HEAD", WORKTREE)

    assert changes.changed_files == []


def test_edits_inside_a_submodule_are_refused_not_lost(repo, tmp_path):
    import subprocess
    inner = tmp_path / "inner"
    inner.mkdir()
    git = lambda *a, cwd=inner: subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)
    git("init", "-q")
    (inner / "Lib.java").write_text("class Lib {}\n")
    git("add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "lib")
    repo.write("a/Core.java", CORE)
    repo.commit("base")
    git("-c", "protocol.file.allow=always", "submodule", "add", "-q", str(inner), "lib", cwd=repo.path)
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "sub", cwd=repo.path)
    assert resolve_commit(repo.path, WORKTREE)  # clean submodule: fine

    (repo.path / "lib/Lib.java").write_text("class Lib { int x; }\n")

    with pytest.raises(InvalidCommitError, match="inside submodules.*lib"):
        resolve_commit(repo.path, WORKTREE)
