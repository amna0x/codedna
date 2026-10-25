"""Plugin install/remove: official catalogue only, checksum before pip (offline fakes)."""

from __future__ import annotations

import hashlib
import json
import subprocess

import pytest
from codedna.cli import EXIT_ANALYSIS_ERROR, main
from codedna.plugins import manager
from codedna.plugins.catalogue import OFFICIAL_RELEASES, CatalogueError

WHEEL = b"fake wheel bytes"
URL = OFFICIAL_RELEASES + "python-1.0.0/codedna_python-1.0.0-py3-none-any.whl"


WHEEL_SHA = hashlib.sha256(WHEEL).hexdigest()


def catalogue(sha=WHEEL_SHA, api="1.0"):
    return {"schema_version": 1, "plugins": [
        {"id": "java", "name": "Java", "description": "d", "licence": "l",
         "source": "https://example.org", "versions": [
             {"version": "0.1.0", "api_version": "1.0", "builtin": True, "url": None, "sha256": None}]},
        {"id": "python", "package": "codedna-python", "name": "Python", "description": "d",
         "licence": "MIT", "source": "https://example.org",
         "versions": [{"version": "1.0.0", "api_version": api, "url": URL, "sha256": sha}]}]}


class FakePip:
    def __init__(self, code=0, check=""):
        self.calls, self.code, self.check = [], code, check

    def __call__(self, args):
        self.calls.append(args)
        if args[0] == "check":  # pip check exits 1 for any broken package in the environment
            return subprocess.CompletedProcess(args, 1 if self.check else 0, self.check, "")
        return subprocess.CompletedProcess(args, self.code, "", "boom" if self.code else "")


def fetch(url):
    assert url == URL, url
    return WHEEL


def test_install_verifies_checksum_then_installs_one_wheel_without_index():
    pip = FakePip()
    result = manager.install(catalogue(), "python", "1.0.0", confirmed=True, download=fetch, pip=pip)
    assert result["status"] == "installed"
    args, check = pip.calls
    assert args[:4] == ["install", "--no-index", "--no-deps", "--disable-pip-version-check"]
    assert args[-1].endswith("codedna_python-1.0.0-py3-none-any.whl")
    assert check[0] == "check"


def test_install_is_rolled_back_when_the_plugin_dependencies_are_missing():
    pip = FakePip(check="codedna_python 1.0.0 requires tree-sitter, which is not installed.\n"
                        "otherpkg 2.0 requires zlib, which is not installed.\n")
    with pytest.raises(CatalogueError, match="removed again.*requires tree-sitter") as error:
        manager.install(catalogue(), "python", "1.0.0", confirmed=True, download=fetch, pip=pip)
    assert "otherpkg" not in str(error.value)  # other packages' problems are not reported
    assert pip.calls[-1] == ["uninstall", "--yes", "codedna-python"]


def test_unrelated_broken_packages_do_not_block_an_install():
    pip = FakePip(check="otherpkg 2.0 requires zlib, which is not installed.\n")
    assert manager.install(catalogue(), "python", "1.0.0", confirmed=True, download=fetch,
                           pip=pip)["status"] == "installed"


@pytest.mark.parametrize("kwargs, message", [
    ({"confirmed": False}, "confirm"),
])
def test_install_requires_confirmation(kwargs, message):
    pip = FakePip()
    with pytest.raises(CatalogueError, match=message):
        manager.install(catalogue(), "python", "1.0.0", download=fetch, pip=pip, **kwargs)
    assert pip.calls == []


def test_checksum_mismatch_never_reaches_pip():
    pip = FakePip()
    with pytest.raises(CatalogueError, match="checksum mismatch"):
        manager.install(catalogue(sha="0" * 64), "python", "1.0.0", confirmed=True,
                        download=fetch, pip=pip)
    assert pip.calls == []


def test_unknown_version_incompatible_api_and_builtin_are_handled():
    with pytest.raises(CatalogueError, match="not in the official catalogue"):
        manager.install(catalogue(), "python", "9.9.9", confirmed=True, download=fetch, pip=FakePip())
    with pytest.raises(CatalogueError, match="plugin API"):
        manager.install(catalogue(api="2.0"), "python", "1.0.0", confirmed=True,
                        download=fetch, pip=FakePip())
    assert "bundled" in manager.install(catalogue(), "java", "0.1.0", confirmed=True,
                                          download=fetch, pip=FakePip())["status"]


def test_remove_uses_the_catalogue_package_name_and_refuses_builtins():
    pip = FakePip()
    assert manager.remove(catalogue(), "python", confirmed=True, pip=pip)["status"] == "removed"
    assert pip.calls == [["show", "--quiet", "codedna-python"], ["uninstall", "--yes", "codedna-python"]]
    with pytest.raises(CatalogueError, match="bundled"):
        manager.remove(catalogue(), "java", confirmed=True, pip=pip)


def test_cli_install_without_yes_is_refused(monkeypatch, capsys):
    monkeypatch.setattr(manager, "_download",
                        lambda url: json.dumps(catalogue()).encode() if url == manager.OFFICIAL_CATALOGUE
                        else WHEEL)
    monkeypatch.setattr(manager, "_pip", FakePip())
    assert main(["plugins", "install", "python", "1.0.0"]) == EXIT_ANALYSIS_ERROR
    err = capsys.readouterr().err
    assert "confirm" in err and "licence MIT" in err and "source https://example.org" in err


def test_wheel_for_another_package_is_refused_before_download():
    data = catalogue()
    data["plugins"][1]["versions"][0]["url"] = OFFICIAL_RELEASES + "python-1.0.0/codedna-1.0.0-py3-none-any.whl"
    pip = FakePip()
    with pytest.raises(CatalogueError, match="is not package"):
        manager.install(data, "python", "1.0.0", confirmed=True,
                        download=lambda url: pytest.fail("downloaded"), pip=pip)
    assert pip.calls == []


def test_cli_catalogue_and_confirmed_install(monkeypatch, capsys):
    pip = FakePip()
    monkeypatch.setattr(manager, "_download",
                        lambda url: json.dumps(catalogue()).encode() if url == manager.OFFICIAL_CATALOGUE
                        else WHEEL)
    monkeypatch.setattr(manager, "_pip", pip)
    assert main(["plugins", "catalogue"]) == 0
    assert json.loads(capsys.readouterr().out)["schema_version"] == 1
    assert main(["plugins", "install", "python", "1.0.0", "--yes"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "installed"
    assert [call[0] for call in pip.calls] == ["install", "check"]


def make_wheel(path, requires=b""):
    """A minimal real wheel (no build tools needed) registering a codedna.languages entry point."""
    import base64
    import zipfile
    files = {
        "codedna_python/__init__.py": b"class PythonPlugin:\n    pass\n",
        "codedna_python-1.0.0.dist-info/METADATA":
            b"Metadata-Version: 2.1\nName: codedna-python\nVersion: 1.0.0\n" + requires,
        "codedna_python-1.0.0.dist-info/WHEEL":
            b"Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        "codedna_python-1.0.0.dist-info/entry_points.txt":
            b"[codedna.languages]\npython = codedna_python:PythonPlugin\n",
    }
    record = []
    with zipfile.ZipFile(path, "w") as wheel:
        for name, data in files.items():
            wheel.writestr(name, data)
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
            record.append(f"{name},sha256={digest},{len(data)}")
        record.append("codedna_python-1.0.0.dist-info/RECORD,,")
        wheel.writestr("codedna_python-1.0.0.dist-info/RECORD", "\n".join(record) + "\n")
    return path.read_bytes()


def test_real_pip_installs_and_removes_the_verified_wheel_offline(tmp_path):
    """Real pip in a throwaway virtual environment; no index, no network."""
    import sys
    import venv
    env = tmp_path / "env"
    venv.EnvBuilder(with_pip=True).create(env)
    python = env / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    pip = lambda args: subprocess.run([str(python), "-m", "pip", *args],
                                      capture_output=True, text=True, check=False)
    data = make_wheel(tmp_path / "codedna_python-1.0.0-py3-none-any.whl")
    index = catalogue(sha=hashlib.sha256(data).hexdigest())

    assert manager.install(index, "python", "1.0.0", confirmed=True,
                           download=lambda url: data, pip=pip)["status"] == "installed"
    probe = ("from importlib.metadata import entry_points;"
             "print([e.value for e in entry_points(group='codedna.languages')])")
    found = subprocess.run([str(python), "-c", probe],
                           capture_output=True, text=True, check=True).stdout
    assert "codedna_python:PythonPlugin" in found
    assert manager.remove(index, "python", confirmed=True, pip=pip)["status"] == "removed"
    with pytest.raises(CatalogueError, match="not installed"):
        manager.remove(index, "python", confirmed=True, pip=pip)
    assert "codedna_python" not in subprocess.run(
        [str(python), "-m", "pip", "list"], capture_output=True, text=True, check=True).stdout


def test_real_pip_rolls_back_a_plugin_whose_dependency_is_missing(tmp_path):
    import sys
    import venv
    env = tmp_path / "env"
    venv.EnvBuilder(with_pip=True).create(env)
    python = env / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    pip = lambda args: subprocess.run([str(python), "-m", "pip", *args],
                                      capture_output=True, text=True, check=False)
    data = make_wheel(tmp_path / "codedna_python-1.0.0-py3-none-any.whl",
                      requires=b"Requires-Dist: codedna-no-such-dependency>=1\n")
    index = catalogue(sha=hashlib.sha256(data).hexdigest())

    with pytest.raises(CatalogueError, match="codedna-no-such-dependency"):
        manager.install(index, "python", "1.0.0", confirmed=True, download=lambda url: data,
                        pip=pip)
    assert pip(["show", "codedna-python"]).returncode != 0  # nothing left behind


def test_wheel_of_another_version_is_refused_before_download():
    data = catalogue()
    data["plugins"][1]["versions"][0]["url"] = (
        OFFICIAL_RELEASES + "python-1.0.0/codedna_python-0.9.0-py3-none-any.whl")
    with pytest.raises(CatalogueError, match="is not version 1.0.0"):
        manager.install(data, "python", "1.0.0", confirmed=True,
                        download=lambda url: pytest.fail("downloaded"), pip=FakePip())


def test_unreachable_catalogue_is_a_catalogue_error():
    def offline(url):
        raise OSError("network is unreachable")
    with pytest.raises(CatalogueError, match="could not read the official catalogue"):
        manager.fetch_catalogue(download=offline)
    with pytest.raises(CatalogueError, match="could not read"):
        manager.fetch_catalogue(download=lambda url: b"<html>404</html>")


def test_api_lists_installs_and_removes_through_the_catalogue(monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from codedna.api.app import create_app

    pip = FakePip()
    monkeypatch.setattr(manager, "_download",
                        lambda url: json.dumps(catalogue()).encode() if url == manager.OFFICIAL_CATALOGUE
                        else WHEEL)
    monkeypatch.setattr(manager, "_pip", pip)
    token = "t" * 32
    client = TestClient(create_app(token), base_url="http://127.0.0.1:8765")
    headers = {"X-CodeDNA-Token": token}

    listing = client.get("/api/plugins/catalogue", headers=headers).json()
    assert [p["id"] for p in listing["catalogue"]["plugins"]] == ["java", "python"]
    assert listing["installed"]["plugins"][0]["name"] == "java"

    refused = client.post("/api/plugins/install", json={"plugin": "python", "version": "1.0.0"},
                          headers=headers)
    assert refused.status_code == 400 and "confirm" in refused.json()["error"]
    assert pip.calls == []
    assert client.post("/api/plugins/install", json={"plugin": "python", "version": "1.0",
                                                     "confirm": True},
                       headers=headers).status_code == 422  # versions are pinned
    installed = client.post("/api/plugins/install", json={"plugin": "python", "version": "1.0.0",
                                                          "confirm": True}, headers=headers)
    assert installed.status_code == 200 and installed.json()["status"] == "installed"
    removed = client.post("/api/plugins/remove", json={"plugin": "python", "confirm": True},
                          headers=headers)
    assert removed.status_code == 200 and removed.json()["status"] == "removed"
    assert client.post("/api/plugins/remove", json={"plugin": "java", "confirm": True},
                       headers=headers).json()["error"].endswith("cannot be removed here")
    assert client.get("/api/plugins/catalogue").status_code == 401


def test_api_reports_an_unreachable_catalogue_as_json(monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from codedna.api.app import create_app

    def offline(url):
        raise OSError("no route")
    monkeypatch.setattr(manager, "_download", offline)
    token = "t" * 32
    client = TestClient(create_app(token), base_url="http://127.0.0.1:8765")
    response = client.get("/api/plugins/catalogue", headers={"X-CodeDNA-Token": token})
    assert response.status_code == 400 and "no route" in response.json()["error"]
