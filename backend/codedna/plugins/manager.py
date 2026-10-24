"""Install and remove language plugins from the official catalogue only (D-020).

Installing a plugin runs its code later, so every step is explicit: the
caller names an exact catalogue version and confirms; the wheel is
downloaded from the URL the validated catalogue gives, its SHA-256 checked
before pip sees it, and pip installs that one file into CodeDNA's own
environment (``sys.executable``) with no index and no dependency resolution.
Nothing here accepts a URL or file from the caller.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from collections.abc import Callable
from pathlib import Path, PurePosixPath

from codedna.plugins.catalogue import CatalogueError, PluginVersion, validate_catalogue

OFFICIAL_CATALOGUE = "https://mohibk0004-del.github.io/codedna/catalogue/index.json"
_MAX_BYTES = 50 * 1024 * 1024

Download = Callable[[str], bytes]
Runner = Callable[[list[str]], subprocess.CompletedProcess]


def _download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read(_MAX_BYTES + 1)
    if len(data) > _MAX_BYTES:
        raise CatalogueError(f"download from {url} exceeds {_MAX_BYTES} bytes")
    return data


def _pip(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "pip", *args], capture_output=True, text=True,
                          check=False)


def _canonical(name: str) -> str:
    """PEP 503 name normalisation, so codedna_python and codedna-python match."""
    return re.sub(r"[-_.]+", "-", name).lower()


def fetch_catalogue(download: Download | None = None) -> dict:
    data = json.loads((download or _download)(OFFICIAL_CATALOGUE).decode("utf-8"))
    validate_catalogue(data)
    return data


def find_version(catalogue: dict, plugin: str, version: str) -> PluginVersion:
    for entry in validate_catalogue(catalogue):
        if entry.plugin == plugin and entry.version == version:
            return entry
    raise CatalogueError(f"{plugin} {version} is not in the official catalogue")


def install(catalogue: dict, plugin: str, version: str, *, confirmed: bool,
            download: Download | None = None, pip: Runner | None = None) -> dict:
    entry = find_version(catalogue, plugin, version)
    if entry.builtin:
        return {"plugin": plugin, "version": version, "status": "built-in; nothing to install"}
    if not entry.compatible:
        raise CatalogueError(f"{plugin} {version} needs plugin API {entry.api_version}")
    if not confirmed:
        raise CatalogueError("installing a plugin runs its code; confirm explicitly")
    name = PurePosixPath(entry.url).name
    if not name.endswith(".whl"):
        raise CatalogueError(f"{plugin} {version}: only wheel files are installed")
    if _canonical(name.split("-", 1)[0]) != _canonical(entry.package or ""):
        raise CatalogueError(f"{plugin} {version}: wheel {name} is not package {entry.package}")
    data = (download or _download)(entry.url)
    digest = hashlib.sha256(data).hexdigest()
    if digest != entry.sha256:
        raise CatalogueError(f"checksum mismatch for {plugin} {version}: got {digest}")
    with tempfile.TemporaryDirectory(prefix="codedna-plugin-") as tmp:
        wheel = Path(tmp) / name
        wheel.write_bytes(data)
        result = (pip or _pip)(["install", "--no-index", "--no-deps", "--disable-pip-version-check",
                      str(wheel)])
    if result.returncode != 0:
        raise CatalogueError(f"pip could not install {plugin} {version}: {result.stderr.strip()}")
    return {"plugin": plugin, "version": version, "sha256": digest, "status": "installed"}


def remove(catalogue: dict, plugin: str, *, confirmed: bool, pip: Runner | None = None) -> dict:
    entries = [e for e in validate_catalogue(catalogue) if e.plugin == plugin]
    if not entries:
        raise CatalogueError(f"{plugin} is not in the official catalogue")
    package = next((e.package for e in entries if e.package), None)
    if package is None:
        raise CatalogueError(f"{plugin} is built in and cannot be removed")
    if not confirmed:
        raise CatalogueError("removing a plugin changes CodeDNA's environment; confirm explicitly")
    run = pip or _pip
    if run(["show", "--quiet", package]).returncode != 0:
        raise CatalogueError(f"{plugin} ({package}) is not installed")
    result = run(["uninstall", "--yes", package])
    if result.returncode != 0:
        raise CatalogueError(f"pip could not remove {package}: {result.stderr.strip()}")
    return {"plugin": plugin, "status": "removed"}
