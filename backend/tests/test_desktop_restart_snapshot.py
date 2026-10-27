"""Internal desktop activation handoff; no new packaged binary is claimed."""
import json
from pathlib import Path
import runpy
import sys
from types import ModuleType

import pytest

from codedna.plugins import desktop_store


def test_frozen_announcement_carries_private_activation_for_api_restart(repo, monkeypatch, capsys):
    from codedna.api import server
    import uvicorn
    repo.write('A.java', 'class A {}'); repo.commit('fixture')
    snapshot = {'schema_version': 1, 'home': 'fixture', 'directories': [], 'error': None}
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(desktop_store, 'worker_snapshot', lambda: snapshot)
    monkeypatch.setattr(server, 'create_app', lambda *args, **kwargs: 'fixture app')
    calls = []
    monkeypatch.setattr(uvicorn, 'run', lambda *args, **kwargs: calls.append((args, kwargs)))
    assert server.serve(token='fixture-not-a-real-token-32chars') == 0
    announced = json.loads(capsys.readouterr().out)
    assert announced['plugin_snapshot'] == snapshot
    assert announced['allow_build'] is False
    assert calls[0][0] == ('fixture app',)


def test_desktop_restart_pins_before_default_activation(repo, monkeypatch):
    import multiprocessing
    repo.write('A.java', 'class A {}'); repo.commit('fixture')
    snapshot = {'schema_version': 1, 'home': 'fixture', 'directories': [], 'error': None}
    monkeypatch.setenv('CODEDNA_DESKTOP_PLUGIN_SNAPSHOT', json.dumps(snapshot))
    monkeypatch.setattr(sys, 'argv', ['codedna-core.exe', 'serve'])
    monkeypatch.setattr(multiprocessing, 'freeze_support', lambda: None)
    events = []
    monkeypatch.setattr(desktop_store, 'pin_worker_snapshot', lambda value: events.append(('pin', value)))
    monkeypatch.setattr(desktop_store, 'activate', lambda: events.append(('activate', None)))
    cli = ModuleType('codedna.cli'); cli.main = lambda: events.append(('cli', None)) or 0
    monkeypatch.setitem(sys.modules, 'codedna.cli', cli)
    with pytest.raises(SystemExit) as stopped:
        runpy.run_path(str(Path(__file__).resolve().parents[2] / 'scripts/desktop_core_entry.py'), run_name='__main__')
    assert stopped.value.code == 0
    assert events == [('pin', snapshot), ('activate', None), ('cli', None)]


def test_invalid_restart_snapshot_never_silently_activates_pending_plugins(repo, monkeypatch):
    import multiprocessing
    repo.write('A.java', 'class A {}'); repo.commit('fixture')
    monkeypatch.setenv('CODEDNA_DESKTOP_PLUGIN_SNAPSHOT', 'broken')
    monkeypatch.setattr(sys, 'argv', ['codedna-core.exe', 'serve'])
    monkeypatch.setattr(multiprocessing, 'freeze_support', lambda: None)
    monkeypatch.setattr(desktop_store, 'activate', lambda: pytest.fail('invalid handoff activated plugins'))
    with pytest.raises(SystemExit) as stopped:
        runpy.run_path(str(Path(__file__).resolve().parents[2] / 'scripts/desktop_core_entry.py'), run_name='__main__')
    assert stopped.value.code == 2
