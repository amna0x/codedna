"""Real wheel installation and restart tests; no network or external build tools."""
import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from codedna.plugins import desktop_store as store, manager
from codedna.plugins.catalogue import CatalogueError, OFFICIAL_RELEASES


def make_wheel(folder, version="1.0.0", *, fail=False, requires="", extra=None,
               tag="py3-none-any", factory_extra=""):
    name = f"codedna_python-{version}-{tag}.whl"
    dist = f"codedna_python-{version}.dist-info"
    code = f'''class PythonPlugin:
    name = "python"
    display_name = "Desktop fixture"
    version = "{version}"
    api_version = "1.1"
    file_suffixes = (".fixture",)
    def __init__(self):
        {"raise RuntimeError('broken update')" if fail else "pass"}
{factory_extra}
    def handles(self, path): return path.endswith('.fixture')
    def parse(self, source): return None
    def build_graph(self, *args, **kwargs): return None
    def discover_tests(self, *args, **kwargs): return None
    def run_tests(self, *args, **kwargs): return None
'''
    files = {"codedna_python/__init__.py": code.encode(),
             f"{dist}/METADATA": (f"Metadata-Version: 2.1\nName: codedna-python\nVersion: {version}\n"
                                   + requires).encode(),
             f"{dist}/WHEEL": f"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: {tag}\n".encode(),
             f"{dist}/entry_points.txt": b"[codedna.languages]\npython = codedna_python:PythonPlugin\n"}
    files.update(extra or {})
    rows = []
    wheel = Path(folder) / name
    with zipfile.ZipFile(wheel, "w") as archive:
        for path, content in files.items():
            archive.writestr(path, content)
            digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip("=")
            rows.append((path, "sha256=" + digest, str(len(content))))
        rows.append((f"{dist}/RECORD", "", ""))
        record = io.StringIO(newline="")
        csv.writer(record).writerows(rows)
        archive.writestr(f"{dist}/RECORD", record.getvalue())
    return wheel


def catalogue(wheel):
    version = wheel.name.split("-")[1]
    return {"schema_version": 1, "plugins": [{"id": "python", "package": "codedna-python",
        "name": "Python", "description": "test", "licence": "MIT", "source": "https://example.org",
        "versions": [{"version": version, "api_version": "1.1",
                      "url": OFFICIAL_RELEASES + "test/" + wheel.name,
                      "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest()}]}]}


def install(wheel):
    index = catalogue(wheel)
    entry = manager.find_version(index, "python", wheel.name.split("-")[1])
    return store.install(wheel, entry, entry.sha256)


def source_probe(site, entry):
    result = subprocess.run([sys.executable, "-m", "codedna.plugins.desktop_store", "--probe",
                             str(site), entry.plugin, entry.package, entry.version],
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise CatalogueError(result.stderr)


def restarted_plugins():
    code = "import sys,json;sys.frozen=True;from codedna.plugins import load_plugins;print(json.dumps(load_plugins().describe()))"
    return json.loads(subprocess.run([sys.executable, "-c", code], capture_output=True,
                                    text=True, check=True, timeout=60).stdout)


@pytest.fixture
def home(tmp_path, monkeypatch):
    home = tmp_path / "CodeDNA user plugins with spaces"
    monkeypatch.setenv("CODEDNA_PLUGIN_HOME", str(home))
    monkeypatch.setattr(store, "_BOOT", None)
    monkeypatch.setattr(sys, "path", sys.path.copy())
    return home


def test_real_install_upgrade_restart_and_remove_restore_bundled_plugin(home, tmp_path):
    first = make_wheel(tmp_path)
    result = install(first)
    assert result["status"] == "installed" and result["restart_required"]
    before = store.activate()
    assert len(before) == 1
    assert next(p for p in restarted_plugins()["plugins"] if p["name"] == "python")["version"] == "1.0.0"
    second = make_wheel(tmp_path, "1.1.0")
    assert install(second)["previous_version"] == "1.0.0"
    assert store.activate() == before  # loaded session never silently switches code
    assert next(p for p in restarted_plugins()["plugins"] if p["name"] == "python")["version"] == "1.1.0"
    assert store.remove("python")["restart_required"]
    after = restarted_plugins()
    assert not after["problems"]
    assert next(p for p in after["plugins"] if p["name"] == "python")["version"] == "0.1.0"
    assert before[0].exists()  # loaded Windows files remain as inactive rollback cache


@pytest.mark.parametrize("problem", ["missing", "incompatible", "broken", "unsafe", "namespace", "pth", "native"])
def test_bad_update_never_replaces_working_manifest(home, tmp_path, problem):
    install(make_wheel(tmp_path))
    before = (home / "active.json").read_bytes()
    kwargs = {
        "missing": {"requires": "Requires-Dist: codedna-never-installed>=9\n"},
        "incompatible": {"requires": "Requires-Dist: codedna>=99\n"},
        "broken": {"fail": True},
        "unsafe": {"extra": {"../escaped.py": b"bad"}},
        "namespace": {"extra": {"codedna/__init__.py": b"bad"}},
        "pth": {"extra": {"codedna_python/evil.pth": b"import os"}},
        "native": {"tag": "cp27-cp27m-macosx_10_9_x86_64"},
    }[problem]
    with pytest.raises(CatalogueError):
        install(make_wheel(tmp_path, "1.1.0", **kwargs))
    assert (home / "active.json").read_bytes() == before
    assert not list(home.glob(".stage-*"))
    assert not (home / "escaped.py").exists()


def test_frozen_manager_never_calls_pip_and_checks_digest_and_consent(home, tmp_path, monkeypatch):
    wheel = make_wheel(tmp_path)
    index = catalogue(wheel)
    monkeypatch.setattr(store, "_probe", source_probe)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(manager, "_pip", lambda args: pytest.fail("frozen core launched pip"))
    with pytest.raises(CatalogueError, match="confirm"):
        manager.install(index, "python", "1.0.0", confirmed=False)
    with pytest.raises(CatalogueError, match="checksum"):
        manager.install(index, "python", "1.0.0", confirmed=True, download=lambda _: b"corrupt")
    assert not home.exists()
    result = manager.install(index, "python", "1.0.0", confirmed=True, download=lambda _: wheel.read_bytes())
    assert result["status"] == "installed" and result["restart_required"]
    assert manager.remove(index, "python", confirmed=True)["status"] == "removed"
    with pytest.raises(CatalogueError, match="bundled"):
        manager.remove(index, "python", confirmed=True)


def test_atomic_activation_failure_preserves_old_version(home, tmp_path, monkeypatch):
    install(make_wheel(tmp_path))
    before = (home / "active.json").read_bytes()
    replace = os.replace
    def fail(source, target):
        if Path(target).name == "active.json":
            raise OSError("simulated write failure")
        return replace(source, target)
    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(CatalogueError, match="unchanged"):
        install(make_wheel(tmp_path, "1.1.0"))
    assert (home / "active.json").read_bytes() == before


def test_concurrent_change_is_refused_without_touching_state(home):
    with store._locked(home):
        with pytest.raises(CatalogueError, match="in progress"):
            store.remove("python")
    assert not (home / "active.json").exists()


def test_corrupt_store_does_not_hide_bundled_languages(home):
    home.mkdir()
    (home / "active.json").write_text('{"schema_version":1,"plugins":{"python":{"directory":"../outside"}}}')
    result = restarted_plugins()
    assert {p["name"] for p in result["plugins"]} >= {"java", "python"}
    assert any("desktop plugin store" in problem for problem in result["problems"])


def test_broken_optional_copy_falls_back_to_bundled_language(home, tmp_path):
    install(make_wheel(tmp_path))
    item = json.loads((home / "active.json").read_text())["plugins"]["python"]
    source = store._path(home, item) / "site/codedna_python/__init__.py"
    source.write_text("raise RuntimeError('damaged optional copy')\n")
    result = restarted_plugins()
    assert next((p for p in result["plugins"] if p["name"] == "python"), {}).get("version") == "0.1.0", result
    assert any("damaged optional copy" in problem for problem in result["problems"])
