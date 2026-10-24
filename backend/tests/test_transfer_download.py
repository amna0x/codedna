"""Selective dataset download preserves needed job links and validates outputs."""

import csv
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest


spec = importlib.util.spec_from_file_location(
    "fetch_subset", Path(__file__).resolve().parents[2] / "scripts/fetch_rtptorrent_subset.py")
fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)


def test_subset_download_filters_shared_map_and_verifies_restart(repo, monkeypatch):
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        handle.writestr("rtp-torrent/a@A/a@A.csv", "travisJobId,testName\n10,TestA\n")
        handle.writestr("rtp-torrent/b@B/b@B.csv", "travisJobId,testName\n20,TestB\n")
        handle.writestr("rtp-torrent/repo/a@A/HEAD", "ref: refs/heads/main\n")
        handle.writestr("rtp-torrent/repo/a@A/refs/", "")
        handle.writestr("rtp-torrent/repo/a@A/hooks/pre-commit", "must not extract")
        handle.writestr("rtp-torrent/tr_all_built_commits.csv",
                        "tr_job_id,git_commit_id\n10,aaa\n20,bbb\n30,ccc\n")

    class LocalRemote(io.BytesIO):
        def __init__(self):
            super().__init__(archive.getvalue())
            self.length = len(archive.getvalue())
            self.downloaded = 0

    monkeypatch.setattr(fetcher, "RemoteZip", LocalRemote)
    monkeypatch.setattr(fetcher.shutil, "disk_usage", lambda path: SimpleNamespace(free=2 * 1024**3))
    out = repo.path / "raw"
    first = fetcher.fetch(out, ["a@A"])
    with (out / "rtp-torrent/tr_all_built_commits.csv").open(newline="") as handle:
        assert list(csv.DictReader(handle)) == [{"tr_job_id": "10", "git_commit_id": "aaa"}]
    assert not (out / "rtp-torrent/b@B").exists()
    assert not (out / "rtp-torrent/repo/a@A/hooks").exists()
    assert (out / "rtp-torrent/repo/a@A/refs").is_dir()
    assert first["whole_archive_md5_verified"] is False
    assert fetcher.fetch(out, ["a@A"]) == first
    (out / "rtp-torrent/repo/a@A/HEAD").write_text("changed")
    with pytest.raises(RuntimeError, match="not verified"):
        fetcher.fetch(out, ["a@A"])


@pytest.mark.parametrize("name", ["../escape", "/escape", "rtp-torrent/C:/escape", "a\\b"])
def test_archive_paths_cannot_escape_output(repo, name):
    with pytest.raises(ValueError, match="Unsafe ZIP path"):
        fetcher.safe_target(repo.path, name)
