"""Immutable validation reuse must never turn mutable state into stale evidence."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock

import pytest

from codedna.git_analysis import git
from codedna.selection import select_tests


def seed(repo):
    repo.write('A.java', 'class A {}')
    return repo.commit('initial')


def counted(monkeypatch):
    original = git._run
    calls = []
    lock = Lock()
    def run(repo, args, *other, **options):
        with lock:
            calls.append(tuple(args))
        return original(repo, args, *other, **options)
    monkeypatch.setattr(git, '_run', run)
    return calls


def test_successful_immutable_validation_is_reused_only_inside_one_scope(repo, monkeypatch):
    sha = seed(repo); calls = counted(monkeypatch)
    for _ in range(2):
        with git.git_validation_scope():
            for _ in range(3):
                assert git.resolve_repository(repo.path) == repo.path.resolve()
                assert git.resolve_commit(repo.path, sha) == sha
    assert len(calls) == 4  # once per kind in each independent scope
    git.resolve_repository(repo.path)
    git.resolve_commit(repo.path, sha)
    assert len(calls) == 6


def test_head_and_worktree_are_fresh_even_in_one_scope(repo):
    original = seed(repo)
    with git.git_validation_scope():
        assert git.resolve_commit(repo.path, 'HEAD') == original
        repo.write('A.java', 'class A { int value = 1; }')
        changed = repo.commit('change HEAD')
        assert git.resolve_commit(repo.path, 'HEAD') == changed
        assert git.resolve_commit(repo.path, original) == original
        repo.write('A.java', 'class A { int value = 2; }')
        first = git.resolve_commit(repo.path, git.WORKTREE)
        repo.write('A.java', 'class A { int value = 3; }')
        second = git.resolve_commit(repo.path, git.WORKTREE)
        assert first != second
    assert repo.git('rev-parse', 'HEAD') == changed


def test_nested_scope_reuses_but_exception_clears_scope(repo, monkeypatch):
    sha = seed(repo); calls = counted(monkeypatch)
    with pytest.raises(RuntimeError):
        with git.git_validation_scope():
            git.resolve_commit(repo.path, sha)
            with git.git_validation_scope():
                git.resolve_commit(repo.path, sha)
            raise RuntimeError('caller interrupted')
    git.resolve_commit(repo.path, sha)
    assert len(calls) == 2


def test_invalid_commits_are_not_remembered(repo, monkeypatch):
    seed(repo); calls = counted(monkeypatch)
    with git.git_validation_scope():
        for _ in range(2):
            with pytest.raises(git.InvalidCommitError):
                git.resolve_commit(repo.path, 'f'*40)
    assert len(calls) == 2


def test_git_environment_changes_invalidate_reuse(repo, monkeypatch):
    sha = seed(repo); calls = counted(monkeypatch)
    with git.git_validation_scope():
        git.resolve_commit(repo.path, sha)
        monkeypatch.setenv('GIT_NO_REPLACE_OBJECTS', '1')
        git.resolve_commit(repo.path, sha)
    assert len(calls) == 2


def test_concurrent_analyses_do_not_share_validation(repo, monkeypatch):
    sha = seed(repo); calls = counted(monkeypatch); barrier = Barrier(2)
    def resolve():
        with git.git_validation_scope():
            barrier.wait(timeout=10)
            for _ in range(2):
                assert git.resolve_commit(repo.path, sha) == sha
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: resolve(), range(2)))
    assert len(calls) == 2


def test_selection_reuses_validation_without_changing_result(repo, monkeypatch):
    repo.write('src/main/java/example/Price.java', 'package example; public class Price {}')
    repo.write('src/test/java/example/PriceTest.java',
               'package example; public class PriceTest { @org.junit.jupiter.api.Test void checksPrice() {} }')
    base = repo.commit('tests')
    repo.write('src/main/java/example/Price.java', 'package example; public class Price { int value; }')
    head = repo.commit('change')
    calls = counted(monkeypatch)
    reference = select_tests.__wrapped__(repo.path, base, head, 'all').to_dict()
    before = len(calls)
    actual = select_tests(repo.path, base, head, 'all').to_dict()
    after = len(calls)-before
    assert actual == reference
    assert after < before


def test_same_immutable_name_is_validated_in_each_repository(repo, tmp_path, monkeypatch):
    sha = seed(repo)
    other = tmp_path/'other'; other.mkdir()
    repo.git('init', '--quiet', str(other))
    calls = counted(monkeypatch)
    with git.git_validation_scope():
        assert git.resolve_commit(repo.path, sha) == sha
        with pytest.raises(git.InvalidCommitError):
            git.resolve_commit(other, sha)
    assert len(calls) == 2


def test_hexadecimal_branch_name_is_not_mistaken_for_an_immutable_object(repo):
    first = seed(repo)
    name = 'a'*64  # valid branch name in a SHA-1 repository, not a SHA-256 object
    repo.git('update-ref', 'refs/heads/'+name, first)
    with git.git_validation_scope():
        assert git.resolve_commit(repo.path, name) == first
        repo.write('A.java', 'class A { int updated; }')
        second = repo.commit('move branch')
        repo.git('update-ref', 'refs/heads/'+name, second)
        assert git.resolve_commit(repo.path, name) == second
