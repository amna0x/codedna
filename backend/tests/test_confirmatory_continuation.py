"""One-time AFK continuation: verified source reuse, no network, fixed provenance."""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

from test_rtptorrent import PROJECT, dataset  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_partial_and_wrong_project_caches_are_not_ready(tmp_path):
    runner = load("continue_confirmatory")
    assert runner.read_cache(tmp_path) is None and not runner.ready(None)
    path = tmp_path / "rtptorrent-subset-manifest.json"
    path.write_text(json.dumps({"projects": runner.PROJECTS, "entries": {}}))
    assert not runner.ready(runner.read_cache(tmp_path))
    path.write_text(json.dumps({"projects": ["wrong@project"], "entries": {}}))
    with pytest.raises(ValueError, match="different project set"):
        runner.read_cache(tmp_path)


def test_freezing_provenance_preserves_an_existing_conflicting_record(tmp_path):
    runner = load("continue_confirmatory")
    file = tmp_path / "source.json"
    runner.freeze(file, {"source": "original"})
    first = file.read_bytes()
    runner.freeze(file, {"source": "original"})
    with pytest.raises(ValueError, match="Provenance changed"):
        runner.freeze(file, {"source": "different"})
    assert file.read_bytes() == first


def test_incomplete_cli_records_status_without_waiting_or_downloading(tmp_path, monkeypatch):
    runner = load("continue_confirmatory")
    monkeypatch.setattr(runner, "freeze_sources", lambda out: None)
    monkeypatch.setattr(runner.time, "sleep", lambda _: pytest.fail("must not wait without --wait"))
    out = tmp_path / "out"
    assert runner.main(["--source-raw", str(tmp_path / "missing"), "--out", str(out)]) == 2
    status = json.loads((out / "continuation-status.json").read_text())
    assert status["phase"] == "waiting_for_existing_download" and status["verified_files"] == 0


def cache_for_fixture(runner, source, raw, monkeypatch):
    shutil.copytree(source, raw / "rtp-torrent")
    fetcher = load("fetch_rtptorrent_subset")
    files = {p.relative_to(raw).as_posix(): {"sha256": runner.digest(p)}
             for p in raw.rglob("*") if p.is_file()}
    manifest = {"projects": [PROJECT], "entries": files,
                "url": fetcher.URL, "published_archive_md5": fetcher.ARCHIVE_MD5}
    (raw / "rtptorrent-subset-manifest.json").write_text(json.dumps(manifest))
    monkeypatch.setattr(runner, "PROJECTS", [PROJECT])
    monkeypatch.setattr(runner, "EXPECTED_ENTRIES", len(files))
    return manifest


def test_corrupt_source_file_is_rejected_before_preparation(dataset, tmp_path, monkeypatch):  # noqa: F811
    runner = load("continue_confirmatory")
    raw = tmp_path / "raw"
    source, _ = dataset
    manifest = cache_for_fixture(runner, source, raw, monkeypatch)
    (raw / runner.SHARED).write_text("changed")
    with pytest.raises(ValueError, match="Unverified raw cache"):
        runner.verify_cache(raw, manifest)


def test_end_to_end_reuses_cache_and_freezes_model_code(dataset, tmp_path, monkeypatch):  # noqa: F811
    import urllib.request
    runner = load("continue_confirmatory")
    source, _ = dataset
    raw = tmp_path / "raw"
    cache_for_fixture(runner, source, raw, monkeypatch)
    # Give provenance its own checkout copy so a changed source can be tested
    # without writing into the developer's real checkout.
    clone = tmp_path / "checkout"
    rolling = load("run_rolling_evidence")
    files = set(rolling.CODE) | {"scripts/continue_confirmatory.py",
        "scripts/prepare_confirmatory.py", "scripts/fetch_rtptorrent_subset.py",
        "backend/codedna/test_history/rtptorrent.py", "backend/codedna/test_history/store.py",
        "backend/codedna/test_history/mining.py", "backend/codedna/git_analysis/git.py",
        "backend/codedna/git_analysis/blobs.py", "backend/codedna/git_analysis/changes.py",
        "backend/codedna/test_mapping/results.py",
        "docs/CONFIRMATORY_PREPARATION_2026-10-25.md"}
    for relative in files:
        target = clone / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    monkeypatch.setattr(runner, "ROOT", clone)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: pytest.fail("no network allowed"))
    out = tmp_path / "prepared"
    out.mkdir()
    (out / "live-feature-equivalence.json").write_text('[{"offline_fixture": true}]')
    result = tmp_path / "results"
    summary = runner.continue_once(raw, out, result)
    assert summary["projects"]["shop"]["set"] == "confirmatory"
    assert summary["sets"]["confirmatory"]["verdict"] == "inconclusive"
    assert (out / "datasets/shop/dataset.csv").is_file()
    assert (result / "preparation-provenance.json").is_file()
    assert (result / "manifest.json").is_file()
    assert not (out / "raw").exists()
    assert runner.continue_once(raw, out, result) == summary
    (clone / "backend/codedna/test_history/features.py").write_text("changed source")
    with pytest.raises(ValueError, match="Provenance changed"):
        runner.continue_once(raw, out, result)



def test_output_lock_prevents_duplicate_workers_and_allows_restart(tmp_path):
    runner = load("continue_confirmatory")
    with runner.output_lock(tmp_path):
        with pytest.raises(ValueError, match="Another continuation"):
            with runner.output_lock(tmp_path):
                pytest.fail("duplicate worker must not enter")
    with runner.output_lock(tmp_path):
        pass  # the leftover lock file is reusable; OS ownership is released
