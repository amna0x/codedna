"""Offline checks for desktop build failures and artifact provenance."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


def load_builder():
    file = Path(__file__).resolve().parents[2] / "scripts" / "build_desktop_core.py"
    spec = importlib.util.spec_from_file_location("build_desktop_core", file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_manifest_tracks_nested_files_and_changes(tmp_path, monkeypatch):
    builder = load_builder()
    monkeypatch.setattr(builder.importlib.metadata, "version", lambda _: "test-version")
    (tmp_path / "_internal").mkdir()
    dll = tmp_path / "_internal" / "example.dll"
    dll.write_bytes(b"original")
    (tmp_path / "codedna-core.exe").write_bytes(b"executable")
    first = builder.write_manifest(tmp_path)
    assert first["files"]["_internal/example.dll"] == hashlib.sha256(b"original").hexdigest()
    assert "bundle-manifest.json" not in first["files"]
    assert builder.write_manifest(tmp_path) == first
    dll.write_bytes(b"changed")
    second = builder.write_manifest(tmp_path)
    assert second["files"] != first["files"]
    assert json.loads((tmp_path / "bundle-manifest.json").read_text()) == second


def test_windows_bundle_refuses_cross_platform_build(monkeypatch, capsys):
    builder = load_builder()
    monkeypatch.setattr(builder.sys, "platform", "linux")
    assert builder.main() == 1
    assert "Windows Python" in capsys.readouterr().err


def test_missing_freezer_gives_install_command(monkeypatch, capsys):
    builder = load_builder()
    monkeypatch.setattr(builder.sys, "platform", "win32")
    def missing(_):
        raise builder.importlib.metadata.PackageNotFoundError("pyinstaller")
    monkeypatch.setattr(builder.importlib.metadata, "version", missing)
    assert builder.main() == 1
    assert "[ml,api,desktop]" in capsys.readouterr().err


def test_failed_freezer_does_not_publish_a_manifest(monkeypatch, tmp_path):
    builder = load_builder()
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    monkeypatch.setattr(builder.sys, "platform", "win32")
    monkeypatch.setattr(builder.importlib.metadata, "version", lambda _: "test-version")
    def failed(*args, **kwargs):
        raise builder.subprocess.CalledProcessError(1, args[0])
    monkeypatch.setattr(builder.subprocess, "run", failed)
    with pytest.raises(builder.subprocess.CalledProcessError):
        builder.main()
    assert not list(tmp_path.rglob("bundle-manifest.json"))
