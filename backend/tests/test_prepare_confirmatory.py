"""Confirmatory-set preparation, offline: fake fetch and a local ZIP instead of Zenodo."""

from __future__ import annotations

import importlib.util
import json
from types import SimpleNamespace

import pytest
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


@pytest.mark.parametrize("projects, message", [
    (["brettwooldridge@HikariCP"], "Inspected projects"),
    (["one@Shop", "two@shop"], "unique"),
    (["invalid"], "qualified"),
])
def test_explicit_project_selection_cannot_relabel_inspected_or_colliding_data(monkeypatch, capsys,
                                                                             projects, message):
    prepare = load("prepare_confirmatory")
    runner = SimpleNamespace(STUDY11={"hikaricp"})
    monkeypatch.setattr(prepare, "_script", lambda name: runner if name == "run_rolling_evidence"
                        else SimpleNamespace())
    monkeypatch.setattr(prepare, "prepare", lambda *a, **k: pytest.fail("must reject before fetching"))
    assert prepare.main(["--projects", *projects]) == 1
    assert message in capsys.readouterr().err


def test_nonstructural_preparation_preserves_live_inputs_and_refuses_mixed_resume(dataset, tmp_path):
    from codedna.plugins.java_live import LIVE_FEATURES
    from codedna.test_history.features import STRUCTURAL_FEATURES

    prepare = load("prepare_confirmatory")
    source, _ = dataset
    calls = []
    def fetch(raw, projects):
        calls.append(list(projects))
        if not (raw / "rtp-torrent").exists():
            shutil.copytree(source, raw / "rtp-torrent")
    [full] = prepare.prepare(tmp_path / "full", [PROJECT], fetch)
    [fast] = prepare.prepare(tmp_path / "fast", [PROJECT], fetch, structural=False)
    old, new = Dataset.from_csv(full / "dataset.csv"), Dataset.from_csv(fast / "dataset.csv")
    assert not set(STRUCTURAL_FEATURES) & set(new.feature_names)
    assert len(old.rows) == len(new.rows)
    for before, after in zip(old.rows, new.rows):
        assert (before.commit, before.test_id, before.label, before.duration) == \
            (after.commit, after.test_id, after.label, after.duration)
        assert {f: before.features[f] for f in LIVE_FEATURES} == \
            {f: after.features[f] for f in LIVE_FEATURES}
    assert prepare.prepare(tmp_path / "fast", [PROJECT], fetch, structural=False) == [fast]
    count = len(calls)
    with pytest.raises(ValueError, match="configuration changed"):
        prepare.prepare(tmp_path / "fast", [PROJECT], fetch, structural=True)
    assert len(calls) == count
    config_path = tmp_path / "fast" / "preparation.json"
    config = json.loads(config_path.read_text())
    config["extractor_sha256"] = "changed"
    config_path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="configuration changed"):
        prepare.prepare(tmp_path / "fast", [PROJECT], fetch, structural=False)


def test_unfingerprinted_existing_datasets_are_not_adopted(tmp_path):
    prepare = load("prepare_confirmatory")
    folder = tmp_path / "datasets" / "shop"
    folder.mkdir(parents=True)
    (folder / "dataset.csv").write_text("old data")
    with pytest.raises(ValueError, match="no configuration"):
        prepare.prepare(tmp_path, [PROJECT], lambda *a: pytest.fail("must not fetch"))



def test_preparation_reuses_external_raw_without_copy_or_download(dataset, tmp_path):
    prepare = load("prepare_confirmatory")
    source, _ = dataset
    raw = tmp_path / "shared" / "raw"
    shutil.copytree(source, raw / "rtp-torrent")
    out = tmp_path / "fast-preparation"
    seen = []
    [folder] = prepare.prepare(out, [PROJECT], lambda path, projects: seen.append(path),
                               structural=False, raw_dir=raw)
    assert seen == [raw.resolve()]
    assert Dataset.from_csv(folder / "dataset.csv").rows
    assert not (out / "raw").exists()
    assert json.loads((out / "preparation.json").read_text())["raw_dir"] == str(raw.resolve())
