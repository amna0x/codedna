"""Windows-sized Git requests: real commit DAGs and honest launch errors."""

import csv
import errno
import subprocess

import pytest

from codedna.git_analysis import git
from codedna.test_history import rtptorrent as rtp
from codedna.test_history.store import HistoryStore


def large_push(repo, count=1000):
    """Create many actual commits through stdin, without slow per-commit processes."""
    records = []
    for index in range(1, count + 1):
        record = (f"commit refs/heads/large\nmark :{index}\n"
                  f"committer CodeDNA Test <test@example.invalid> {1700000000 + index} +0000\n"
                  "data 1\nx\n")
        if index > 1:
            record += f"from :{index - 1}\n"
        records.append(record + "\n")
    git.run_git_bytes(repo.path, "fast-import", "--quiet", stdin="".join(records).encode())
    return git.run_git(repo.path, "rev-list", "--reverse", "large").splitlines()


def test_import_large_push_keeps_the_correct_tip_with_bounded_git_arguments(repo, tmp_path, monkeypatch):
    shas = large_push(repo)
    assert len(subprocess.list2cmdline(["git", "merge-base", "--independent", *shas])) > 32767
    root = tmp_path / "rtp-torrent"
    project = "acme@large"
    target = root / "repo" / project
    # The dataset format uses bare repositories. Clone our temporary history.
    git.run_git(repo.path, "clone", "--quiet", "--bare", str(repo.path), str(target))
    (root / project).mkdir()
    with (root / rtp.BUILT_COMMITS_FILE).open("w", newline="") as stream:
        writer = csv.writer(stream); writer.writerow(["tr_job_id", "git_commit_id"])
        writer.writerows((1, sha) for sha in shas)
    with (root / project / f"{project}.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["travisJobId", "testName", "index", "duration", "count", "failures", "errors", "skipped"])
        writer.writerow([1, "a.ExampleTest", 0, 1., 1, 1, 0, 0])
    original_text, original_bytes = rtp.run_git, rtp.run_git_bytes
    def bounded_text(repository, *args):
        assert len(subprocess.list2cmdline(["git", *args])) < 30000
        return original_text(repository, *args)
    def bounded_bytes(repository, *args, **kwargs):
        assert len(subprocess.list2cmdline(["git", *args])) < 30000
        return original_bytes(repository, *args, **kwargs)
    monkeypatch.setattr(rtp, "run_git", bounded_text)
    monkeypatch.setattr(rtp, "run_git_bytes", bounded_bytes)
    with HistoryStore(tmp_path / "history.db") as store:
        report = rtp.import_rtptorrent(root, project, store)
        assert [commit.sha for commit in store.commits()] == [shas[-1]]
        assert store.commits()[0].parent is None
        assert store.results(shas[-1])[0].failed
    assert report.jobs_imported == 1 and report.jobs_with_several_tips == 0


@pytest.mark.parametrize("merged", [False, True])
def test_stdin_tip_detection_matches_git_for_branches_merges_and_gaps(repo, monkeypatch, merged):
    repo.write("base.txt", "base"); base = repo.commit("base")
    repo.git("checkout", "--quiet", "-b", "side")
    repo.write("side.txt", "side"); side = repo.commit("side")
    repo.git("checkout", "--quiet", "-")
    repo.write("main.txt", "main"); middle = repo.commit("middle")
    repo.write("main.txt", "later"); tip = repo.commit("tip")
    if merged:
        repo.git("merge", "--quiet", "--no-ff", "side", "-m", "merge")
        tip = repo.git("rev-parse", "HEAD")
    # 'middle' is deliberately absent: transitive ancestry must still be found.
    inputs = [base, side, tip, base]
    expected = set(git.run_git(repo.path, "merge-base", "--independent", *inputs).split())
    monkeypatch.setattr(rtp, "_CHUNK", 1)
    assert set(rtp._tips(repo.path, inputs)) == expected
    assert len(rtp._tips(repo.path, inputs)) == len(expected)
    assert (len(expected) == 1) is merged


def test_empty_tip_set_does_not_launch_git(repo, monkeypatch):
    monkeypatch.setattr(rtp, "run_git", lambda *a: pytest.fail("no Git call needed"))
    assert rtp._tips(repo.path, []) == []


@pytest.mark.parametrize("kind", ["windows_length", "posix_length", "missing_git", "permission"])
def test_launch_errors_keep_the_real_cause(repo, monkeypatch, kind):
    if kind == "windows_length":
        error = FileNotFoundError("The filename or extension is too long")
        error.winerror = 206
        expected = "command line or path is too long"
    elif kind == "posix_length":
        error = OSError(errno.E2BIG, "Argument list too long")
        expected = "command line or path is too long"
    elif kind == "missing_git":
        error = FileNotFoundError(errno.ENOENT, "No such file")
        expected = "git executable not found on PATH"
    else:
        error = PermissionError(errno.EACCES, "Access denied")
        expected = "Access denied"
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(git.subprocess, "run", fail)
    with pytest.raises(git.GitCommandError, match=expected) as raised:
        git.run_git(repo.path, "status")
    assert raised.value.__cause__ is error
    if kind.endswith("length"):
        assert "not found on PATH" not in str(raised.value)


def test_missing_working_directory_is_not_reported_as_missing_git(repo, monkeypatch):
    missing = repo.path / "missing"
    def fail(*args, **kwargs):
        raise FileNotFoundError(errno.ENOENT, "Missing working directory")
    monkeypatch.setattr(git.subprocess, "run", fail)
    with pytest.raises(git.GitCommandError, match="working directory does not exist"):
        git.run_git(missing, "status")
