"""The official catalogue index follows D-020 (pinned, checksummed, official URLs only)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from codedna import __version__
from codedna.plugins.catalogue import (
    OFFICIAL_RELEASES,
    CatalogueError,
    load_catalogue,
    validate_catalogue,
)

INDEX = Path(__file__).resolve().parents[2] / "website" / "catalogue" / "index.json"
DOWNLOAD = {"version": "1.2.3", "api_version": "1.0", "url": OFFICIAL_RELEASES + "v1/p.whl",
            "sha256": "a" * 64}


def catalogue(**version):
    return {"schema_version": 1, "plugins": [{
        "id": "python", "name": "Python", "description": "d", "licence": "MIT",
        "source": "https://example.org/src", "versions": [{**DOWNLOAD, **version}]}]}


def test_published_index_is_valid_and_lists_the_builtin_java_plugin():
    data = load_catalogue(INDEX)
    java = next(p for p in data["plugins"] if p["id"] == "java")
    assert java["versions"][-1]["builtin"] is True
    assert java["versions"][-1]["version"] == __version__


def test_valid_download_entry_is_accepted():
    [entry] = validate_catalogue(catalogue())
    assert entry.compatible and not entry.builtin


@pytest.mark.parametrize("change", [
    {"url": "https://evil.example/p.whl"},
    {"url": OFFICIAL_RELEASES + "../../other/p.whl"},
    {"sha256": "ABC"},
    {"sha256": None},
    {"version": "1.2"},
    {"version": ">=1.0.0"},
])
def test_rule_breaking_entries_are_rejected(change):
    with pytest.raises(CatalogueError):
        validate_catalogue(catalogue(**change))


def test_duplicate_ids_and_wrong_schema_are_rejected():
    data = catalogue()
    data["plugins"].append(copy.deepcopy(data["plugins"][0]))
    with pytest.raises(CatalogueError, match="duplicate"):
        validate_catalogue(data)
    with pytest.raises(CatalogueError, match="schema_version"):
        validate_catalogue({**catalogue(), "schema_version": 2})
