"""The official plugin catalogue index (D-020): load and validate, never install.

The index is one versioned JSON file (``website/catalogue/index.json``),
rendered by the website and read by the IDE's future plugin manager. Every
downloadable version must be pinned, carry a SHA-256 checksum and point at a
GitHub Release asset of the official repository; anything else is rejected
here so no caller can be handed an arbitrary URL.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from codedna.plugins.base import PLUGIN_API_VERSION

SCHEMA_VERSION = 1
OFFICIAL_RELEASES = "https://github.com/mohibk0004-del/codedna/releases/download/"
_ID = re.compile(r"^[a-z][a-z0-9-]{1,40}$")
_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
# <tag>/<asset file name>: no further path, query, fragment or escapes.
_ASSET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*/[A-Za-z0-9][A-Za-z0-9._+-]*$")


class CatalogueError(ValueError):
    """The catalogue index is malformed or breaks a distribution rule."""


@dataclass(frozen=True)
class PluginVersion:
    plugin: str
    version: str
    api_version: str
    builtin: bool
    url: str | None
    sha256: str | None

    @property
    def compatible(self) -> bool:
        return self.api_version.split(".")[0] == PLUGIN_API_VERSION.split(".")[0]


def load_catalogue(path: str | Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogueError(f"cannot read catalogue {path}: {exc}") from exc
    validate_catalogue(data)
    return data


def validate_catalogue(data: dict) -> list[PluginVersion]:
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise CatalogueError(f"catalogue schema_version must be {SCHEMA_VERSION}")
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        raise CatalogueError("catalogue needs a 'plugins' list")
    versions, seen = [], set()
    for plugin in plugins:
        if not isinstance(plugin, dict):
            raise CatalogueError("every catalogue plugin must be an object")
        pid = plugin.get("id", "")
        if not _ID.fullmatch(pid) or pid in seen:
            raise CatalogueError(f"invalid or duplicate plugin id {pid!r}")
        seen.add(pid)
        for key in ("name", "description", "licence", "source"):
            if not isinstance(plugin.get(key), str) or not plugin[key].strip():
                raise CatalogueError(f"{pid}: missing {key}")
        if not plugin["source"].startswith("https://"):
            raise CatalogueError(f"{pid}: source must be an https URL")
        entries = plugin.get("versions")
        if not isinstance(entries, list) or not entries:
            raise CatalogueError(f"{pid}: needs at least one version")
        numbers = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise CatalogueError(f"{pid}: every version must be an object")
            item = _version(pid, entry)
            if item.version in numbers:
                raise CatalogueError(f"{pid}: version {item.version} is listed twice")
            numbers.add(item.version)
            versions.append(item)
    return versions


def _version(pid: str, entry: dict) -> PluginVersion:
    version, api = entry.get("version", ""), entry.get("api_version", "")
    if not _VERSION.fullmatch(version):
        raise CatalogueError(f"{pid}: version {version!r} must be pinned as MAJOR.MINOR.PATCH")
    if not re.fullmatch(r"\d+\.\d+", api):
        raise CatalogueError(f"{pid} {version}: api_version {api!r} must be MAJOR.MINOR")
    builtin = entry.get("builtin") is True
    url, sha = entry.get("url"), entry.get("sha256")
    if builtin:
        if url is not None or sha is not None:
            raise CatalogueError(f"{pid} {version}: a built-in version has no download")
    else:
        if not (isinstance(url, str) and url.startswith(OFFICIAL_RELEASES)
                and _ASSET.fullmatch(url.removeprefix(OFFICIAL_RELEASES)) and ".." not in url):
            raise CatalogueError(f"{pid} {version}: url must be an official release asset")
        if not isinstance(sha, str) or not _SHA256.fullmatch(sha):
            raise CatalogueError(f"{pid} {version}: sha256 must be 64 lowercase hex digits")
    return PluginVersion(pid, version, api, builtin, url, sha)
