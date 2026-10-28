"""Replacement workers must not activate pending desktop plugin changes."""
import json
import sys

import pytest

from codedna.plugins import desktop_store as store
from codedna.plugins.catalogue import CatalogueError


@pytest.fixture
def plugin_home(tmp_path, monkeypatch, repo):
    repo.write('A.java', 'class A {}'); repo.commit('fixture')
    home = tmp_path / 'plugins'
    monkeypatch.setenv('CODEDNA_PLUGIN_HOME', str(home))
    monkeypatch.setattr(store, '_BOOT', None)
    monkeypatch.setattr(store, '_WORKER_BOOT_ERROR', None)
    monkeypatch.setattr(sys, 'path', sys.path.copy())
    return home


def version(home, character):
    name = f'python-1.0.0-{character * 32}'
    site = home / 'versions' / name / 'site'; site.mkdir(parents=True)
    return name, site.resolve()


def manifest(home, name):
    (home / 'active.json').write_text(json.dumps({'schema_version': 1,
        'plugins': {'python': {'directory': name}}}))


@pytest.mark.parametrize('removed', [False, True])
def test_replacement_keeps_original_activation_after_pending_update_or_remove(plugin_home, monkeypatch, removed):
    home = plugin_home
    old, old_site = version(home, 'a'); new, new_site = version(home, 'b')
    manifest(home, old)
    assert store.activate() == (old_site,)
    manifest(home, new)
    if removed:
        (home / 'active.json').unlink()
    snapshot = store.worker_snapshot()
    assert snapshot['directories'] == [old]
    # Simulate an empty replacement worker, not the running parent's imports.
    monkeypatch.setattr(store, '_BOOT', None)
    sys.path.remove(str(old_site))
    store.pin_worker_snapshot(snapshot)
    assert store.activate() == (old_site,)
    assert str(new_site) not in sys.path
    assert sys.path[0] == str(old_site)
    with pytest.raises(CatalogueError, match='already activated'):
        store.pin_worker_snapshot(snapshot)


def test_parent_failure_stays_visible_even_when_manifest_is_repaired(plugin_home, monkeypatch):
    home = plugin_home; home.mkdir()
    (home / 'active.json').write_text('broken')
    snapshot = store.worker_snapshot()
    assert snapshot['error']
    name, site = version(home, 'a'); manifest(home, name)
    store.pin_worker_snapshot(snapshot)
    with pytest.raises(CatalogueError, match='cannot read desktop plugin manifest'):
        store.activate()
    assert str(site) not in sys.path


def test_bootstrap_rejects_escapes_wrong_home_missing_sites_and_duplicates(plugin_home):
    home = plugin_home
    name, site = version(home, 'a')
    valid = {'schema_version': 1, 'home': str(home.resolve()), 'directories': [name], 'error': None}
    bad = [dict(valid, directories=['../elsewhere']), dict(valid, home=str(home.parent)),
           dict(valid, directories=[name, name]), dict(valid, directories=['python-' + 'b' * 32])]
    before = sys.path.copy()
    for snapshot in bad:
        with pytest.raises(CatalogueError): store.pin_worker_snapshot(snapshot)
        assert sys.path == before and store._BOOT is None
