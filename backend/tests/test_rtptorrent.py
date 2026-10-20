"""Tests for the RTPTorrent importer, on a small dataset laid out like RTPTorrent v1.1."""

from __future__ import annotations

import csv
import json
import subprocess

import pytest

from codedna.cli import EXIT_ANALYSIS_ERROR, EXIT_OK, main
from codedna.git_analysis.git import resolve_repository
from codedna.test_history.features import build_dataset
from codedna.test_history.rtptorrent import RtpTorrentError, import_rtptorrent, list_projects
from codedna.test_history.store import HistoryStore

PROJECT = "acme@shop"
JUNIT = "import org.junit.jupiter.api.Test;\n"


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


@pytest.fixture
def dataset(repo, tmp_path):
    """c0 -> c1 -> c2 -> c3 on master, plus a side commit s1 off c1."""
    repo.write("src/main/java/a/Core.java", "package a;\npublic class Core { int v() { return 0; } }\n")
    repo.write("src/test/java/a/CoreTest.java",
               "package a;\n" + JUNIT + "class CoreTest { Core c; @Test void t() {} }\n")
    repo.write("src/test/java/a/OtherTest.java", "package a;\n" + JUNIT + "class OtherTest { @Test void t() {} }\n")
    c0 = repo.commit("c0")
    repo.write("src/main/java/a/Core.java", "package a;\npublic class Core { int v() { return 1; } }\n")
    c1 = repo.commit("c1")
    repo.git("checkout", "-q", "-b", "side")
    repo.write("side.txt", "x\n")
    s1 = repo.commit("s1")
    repo.git("checkout", "-q", "-")
    repo.write("src/main/java/a/Extra.java", "package a;\npublic class Extra {}\n")
    c2 = repo.commit("c2")
    repo.write("src/main/java/a/Core.java", "package a;\npublic class Core { int v() { return 3; } }\n")
    c3 = repo.commit("c3")

    root = tmp_path / "data" / "rtp-torrent"
    subprocess.run(["git", "clone", "-q", "--bare", str(repo.path), str(root / "repo" / PROJECT)],
                   check=True, capture_output=True)
    write_csv(root / "tr_all_built_commits.csv", ["tr_job_id", "git_commit_id"], [
        (100, c1), (101, c1),            # two jobs (platforms) on the same commit
        (102, c2), (102, c3),            # one push of two commits
        (103, "f" * 40),                 # commit missing from the repository
        (104, c3), (104, s1),            # two unrelated tips
        (999, c0),                       # another project's job: ignored
    ])
    header = ["travisJobId", "testName", "index", "duration", "count", "failures", "errors", "skipped"]
    write_csv(root / PROJECT / f"{PROJECT}.csv", header, [
        (100, "a.CoreTest", 0, 1.5, 3, 0, 0, 0),
        (100, "a.OtherTest", 1, -0.2, 2, 0, 0, 0),
        (101, "a.CoreTest", 0, 1.4, 3, 1, 0, 0),     # fails on the second platform
        (101, "a.OtherTest", 1, 0.3, 2, 0, 0, 2),    # all skipped
        (102, "a.CoreTest", 0, 1.6, 3, 0, 2, 0),     # errors
        (102, "a.OtherTest", 1, 0.3, 2, 0, 0, 0),
        (103, "a.CoreTest", 0, 1.0, 3, 0, 0, 0),
        (104, "a.CoreTest", 0, 1.0, 3, 0, 0, 0),
        (105, "a.CoreTest", 0, 1.0, 3, 0, 0, 0),     # no built-commits row
    ])
    (root / "other@thing").mkdir()  # not a project: no results file
    return root, {"c0": c0, "c1": c1, "c2": c2, "c3": c3, "s1": s1}


def test_bare_repositories_are_accepted(dataset):
    root, _ = dataset
    bare = root / "repo" / PROJECT
    assert resolve_repository(bare) == bare.resolve()


def test_import_maps_jobs_to_tested_commits_in_ci_order(dataset, tmp_path):
    root, c = dataset
    with HistoryStore(tmp_path / "h.db") as store:
        report = import_rtptorrent(root.parent, PROJECT, store)

        assert [commit.sha for commit in store.commits()] == [c["c1"], c["c3"]]
        first, second = store.commits()
        assert first.parent == c["c0"]
        assert second.parent == c["c1"]  # base before the whole push (c2 + c3)
        assert {f.path for f in store.changed_files(c["c3"])} == {
            "src/main/java/a/Core.java", "src/main/java/a/Extra.java"}

        results = {r.test_id: r for r in store.results(c["c1"])}
        assert results["a.CoreTest"].failed  # failure on job 101 wins over pass on 100
        assert not results["a.OtherTest"].failed
        assert {r.test_id: r.status for r in store.results(c["c3"])} == {
            "a.CoreTest": "failed", "a.OtherTest": "passed"}
        assert store.get_meta("source") == "rtptorrent"

    assert (report.jobs, report.jobs_imported, report.tested_commits) == (6, 3, 2)
    assert (report.jobs_without_commits, report.jobs_with_missing_commits,
            report.jobs_with_several_tips) == (1, 1, 1)
    assert report.result_rows == 6 and report.failing_rows == 2
    assert report.negative_durations == 1
    assert any("3 of 6 jobs skipped" in w for w in report.warnings)


def test_skipped_status_and_negative_duration(dataset, tmp_path):
    root, c = dataset
    with HistoryStore(tmp_path / "h.db") as store:
        import_rtptorrent(root, PROJECT, store)
        rows = store.db.execute(
            "SELECT source, test_id, status, time FROM test_results WHERE sha = ? ORDER BY source, test_id",
            (c["c1"],)).fetchall()
    assert ("travis:100", "a.OtherTest", "passed", 0.0) in rows
    assert ("travis:101", "a.OtherTest", "skipped", 0.3) in rows


def test_repeated_runs_in_one_job_are_merged_and_failure_wins(dataset, tmp_path):
    root, c = dataset
    results = root / PROJECT / f"{PROJECT}.csv"
    with open(results, "a", newline="", encoding="utf-8") as handle:
        # Job 102 runs OtherTest a second time (e.g. another module) and it fails there.
        csv.writer(handle).writerow((102, "a.OtherTest", 2, 0.7, 2, 1, 0, 0))

    with HistoryStore(tmp_path / "h.db") as store:
        report = import_rtptorrent(root, PROJECT, store)
        row = store.db.execute(
            "SELECT status, time FROM test_results WHERE sha = ? AND test_id = 'a.OtherTest'",
            (c["c3"],)).fetchone()

    assert row[0] == "failed"
    assert row[1] == pytest.approx(0.3 + 0.7)
    assert report.merged_runs == 1
    assert report.result_rows == 6  # still one row per (job, class)
    assert any("were merged" in w for w in report.warnings)


def test_max_commits_keeps_the_most_recent_window(dataset, tmp_path):
    root, c = dataset
    with HistoryStore(tmp_path / "h.db") as store:
        report = import_rtptorrent(root, PROJECT, store, max_commits=1)
        assert [commit.sha for commit in store.commits()] == [c["c3"]]
    assert report.jobs_imported == 1


def test_imported_history_feeds_the_feature_builder(dataset, tmp_path):
    root, c = dataset
    with HistoryStore(tmp_path / "h.db") as store:
        import_rtptorrent(root, PROJECT, store)
        data = build_dataset(store, structural=True)  # repository path comes from the store
    rows = {(row.commit, row.test_id): row for row in data.rows}
    later = rows[(c["c3"], "a.CoreTest")]
    assert later.label == 1
    assert later.features["past_failures"] == 1.0  # c1's failure, not its own
    assert later.features["dep_reachable"] == 1.0  # CoreTest uses the changed Core
    assert rows[(c["c3"], "a.OtherTest")].features["dep_reachable"] == 0.0


def test_list_projects_and_layout_errors(dataset, tmp_path):
    root, _ = dataset
    assert list_projects(root) == [PROJECT]
    with HistoryStore(tmp_path / "h.db") as store:
        with pytest.raises(RtpTorrentError, match="no results file"):
            import_rtptorrent(root, "nobody@nothing", store)
    with pytest.raises(RtpTorrentError, match="not an RTPTorrent folder"):
        list_projects(tmp_path)


def test_cli_import_and_list(dataset, tmp_path, capsys):
    root, _ = dataset
    assert main(["history", "import-rtptorrent", "--dataset", str(root), "--list"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["projects"] == [PROJECT]

    db = tmp_path / "h.db"
    assert main(["history", "import-rtptorrent", "--dataset", str(root), "--project", PROJECT,
                 "--db", str(db)]) == EXIT_OK
    summary = json.loads(capsys.readouterr().out)
    assert summary["tested_commits"] == 2 and summary["commits_with_failures"] == 2

    assert main(["history", "import-rtptorrent", "--dataset", str(root)]) == EXIT_ANALYSIS_ERROR
    assert "--project and --db" in capsys.readouterr().err
