"""Confirmatory-set preparation, offline: fake fetch and a local ZIP instead of Zenodo."""

from __future__ import annotations

import importlib.util
import shutil
import zipfile
from pathlib import Path

from codedna.test_history.features import Dataset
from test_rtptorrent import PROJECT, dataset  # noqa: F401 (fixture)

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_only_projects_outside_study11_are_confirmatory():
    prepare = load("prepare_confirmatory")
    available = ["brettwooldridge@HikariCP", "doanduyhai@Achilles", "apache@sling", "acme@Shop"]
    assert prepare.new_projects(available, {"hikaricp", "achilles"}) == ["apache@sling", "acme@Shop"]
    assert prepare.short_name("Graylog2@graylog2-server") == "graylog2-server"


def test_remote_listing_reads_only_project_result_files(tmp_path, monkeypatch):
    fetcher = load("fetch_rtptorrent_subset")
    archive = tmp_path / "rtp.zip"
    with zipfile.ZipFile(archive, "w") as z:
        for name in ["rtp-torrent/readme.md", "rtp-torrent/a@x/a@x.csv", "rtp-torrent/b@y/b@y.csv",
                     "rtp-torrent/repo/a@x/HEAD", "rtp-torrent/b@y/other.csv"]:
            z.writestr(name, "x")
    monkeypatch.setattr(fetcher, "RemoteZip", lambda: open(archive, "rb"))
    assert fetcher.remote_projects() == ["a@x", "b@y"]


def test_prepare_imports_builds_features_and_resumes(dataset, tmp_path):  # noqa: F811
    prepare = load("prepare_confirmatory")
    source, _ = dataset
    calls = []

    def fake_fetch(raw, projects):
        calls.append(list(projects))
        if not (raw / "rtp-torrent").exists():
            shutil.copytree(source, raw / "rtp-torrent")

    out = tmp_path / "confirm"
    [folder] = prepare.prepare(out, [PROJECT], fake_fetch)

    assert folder == out / "datasets" / "shop"
    data = Dataset.from_csv(folder / "dataset.csv")
    assert data.rows and (out / "db" / "shop.db").is_file()
    assert (out / "db" / "shop-import.json").is_file()
    stamp = (folder / "dataset.csv").stat().st_mtime_ns
    prepare.prepare(out, [PROJECT], fake_fetch)  # resumed: nothing rebuilt
    assert (folder / "dataset.csv").stat().st_mtime_ns == stamp
    assert calls == [[PROJECT], [PROJECT]]
    assert not list(out.rglob("*.partial"))
