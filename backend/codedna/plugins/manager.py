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
import importlib
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
    try:
        data = json.loads((download or _download)(OFFICIAL_CATALOGUE).decode("utf-8"))
    except (OSError, ValueError) as exc:  # offline, not hosted yet, or not JSON
        raise CatalogueError(f"could not read the official catalogue {OFFICIAL_CATALOGUE}: "
                             f"{exc}") from exc
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
        return {"plugin": plugin, "version": version, "status": "bundled with CodeDNA; nothing to install"}
    if not entry.compatible:
        raise CatalogueError(f"{plugin} {version} needs plugin API {entry.api_version}")
    if not confirmed:
        raise CatalogueError("installing a plugin runs its code; confirm explicitly")
    name = PurePosixPath(entry.url).name
    if not name.endswith(".whl"):
        raise CatalogueError(f"{plugin} {version}: only wheel files are installed")
    parts = name.split("-")
    if _canonical(parts[0]) != _canonical(entry.package or ""):
        raise CatalogueError(f"{plugin} {version}: wheel {name} is not package {entry.package}")
    if len(parts) < 2 or parts[1] != version:
        raise CatalogueError(f"{plugin} {version}: wheel {name} is not version {version}")
    data = (download or _download)(entry.url)
    digest = hashlib.sha256(data).hexdigest()
    if digest != entry.sha256:
        raise CatalogueError(f"checksum mismatch for {plugin} {version}: got {digest}")
    run = pip or _pip
    previous = _installed_version(entry.package or "", run)
    with tempfile.TemporaryDirectory(prefix="codedna-plugin-") as tmp:
        wheel = Path(tmp) / name
        wheel.write_bytes(data)
        # Check the plugin's own dependencies first, changing nothing: with no
        # index, pip can satisfy them only from what is already installed. An
        # update therefore never replaces a working version with a broken one.
        dry = run(["install", "--dry-run", "--no-index", "--disable-pip-version-check",
                   str(wheel)])
        if dry.returncode != 0:
            raise CatalogueError(
                f"{plugin} {version} was not installed because its dependencies are not all "
                f"installed in CodeDNA's environment; nothing was changed. pip said: "
                f"{_last_line(dry.stderr)}")
        result = run(["install", "--no-index", "--no-deps", "--disable-pip-version-check",
                      str(wheel)])
    if result.returncode != 0:
        raise CatalogueError(f"pip could not install {plugin} {version}: {result.stderr.strip()}")
    missing = _unmet_requirements(entry.package or "", run)
    if missing:
        if previous is None:
            # A plugin whose dependencies are absent would fail to load; take
            # it out again rather than leave it broken.
            run(["uninstall", "--yes", entry.package])
            raise CatalogueError(
                f"{plugin} {version} was removed again because its dependencies are not "
                f"installed: {'; '.join(missing)}. Install them in CodeDNA's environment, "
                "then retry")
        raise CatalogueError(
            f"{plugin} {version} replaced version {previous} but its dependencies are not met: "
            f"{'; '.join(missing)}. Install them, or install {previous} again")
    importlib.invalidate_caches()  # a running server sees a newly added package
    return {"plugin": plugin, "version": version, "sha256": digest, "status": "installed",
            "previous_version": previous,
            # Python keeps an already imported plugin in memory: an update or
            # reinstall takes effect only after CodeDNA restarts.
            "restart_required": previous is not None}


def _installed_version(package: str, run: Runner) -> str | None:
    """Version of ``package`` in the environment pip manages, None if absent."""
    shown = run(["show", "--disable-pip-version-check", package])
    if shown.returncode != 0:
        return None
    return next((line.split(":", 1)[1].strip() for line in (shown.stdout or "").splitlines()
                 if line.startswith("Version:")), None)


def _last_line(text: str | None) -> str:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    return lines[-1] if lines else "(no output)"


def _unmet_requirements(package: str, run: Runner) -> list[str]:
    """``pip check`` lines about ``package`` (other packages' problems are not ours)."""
    result = run(["check", "--disable-pip-version-check"])
    return [line.strip() for line in (result.stdout or "").splitlines()
            if line.strip() and _canonical(line.split(" ", 1)[0]) == _canonical(package)]


def remove(catalogue: dict, plugin: str, *, confirmed: bool, pip: Runner | None = None) -> dict:
    entries = [e for e in validate_catalogue(catalogue) if e.plugin == plugin]
    if not entries:
        raise CatalogueError(f"{plugin} is not in the official catalogue")
    package = next((e.package for e in entries if e.package), None)
    if package is None:
        raise CatalogueError(f"{plugin} is bundled with CodeDNA and cannot be removed here")
    if not confirmed:
        raise CatalogueError("removing a plugin changes CodeDNA's environment; confirm explicitly")
    run = pip or _pip
    if run(["show", "--quiet", package]).returncode != 0:
        raise CatalogueError(f"{plugin} ({package}) is not installed")
    result = run(["uninstall", "--yes", package])
    if result.returncode != 0:
        raise CatalogueError(f"pip could not remove {package}: {result.stderr.strip()}")
    importlib.invalidate_caches()
    # A plugin already imported stays in memory until CodeDNA restarts.
    return {"plugin": plugin, "status": "removed", "restart_required": True}
