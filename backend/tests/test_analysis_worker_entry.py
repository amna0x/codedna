"""Source/frozen dispatch contract without rebuilding the deferred installer."""
from pathlib import Path
import runpy
import sys
from types import ModuleType

import pytest

from codedna.api.analysis_jobs import worker_command


def test_worker_command_never_treats_a_frozen_executable_as_python(monkeypatch, repo):
    repo.write('A.java', 'class A {}'); repo.commit('fixture')
    monkeypatch.delattr(sys, 'frozen', raising=False)
    assert worker_command() == [sys.executable, '-m', 'codedna.api.analysis_worker']
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    assert worker_command() == [sys.executable, '--codedna-analysis-worker']


def test_frozen_dispatch_waits_for_worker_bootstrap_before_plugin_activation(monkeypatch, repo):
    from codedna.plugins import desktop_store
    repo.write('A.java', 'class A {}'); repo.commit('fixture')
    worker = ModuleType('codedna.api.analysis_worker')
    seen = []
    worker.main = lambda: seen.append('worker') or 0
    monkeypatch.setitem(sys.modules, 'codedna.api.analysis_worker', worker)
    monkeypatch.setattr(sys, 'argv', ['codedna-core.exe', '--codedna-analysis-worker'])
    monkeypatch.setattr(desktop_store, 'activate', lambda: pytest.fail('activated before internal bootstrap'))
    import multiprocessing
    monkeypatch.setattr(multiprocessing, 'freeze_support', lambda: None)
    with pytest.raises(SystemExit) as stopped:
        runpy.run_path(str(Path(__file__).resolve().parents[2] / 'scripts/desktop_core_entry.py'), run_name='__main__')
    assert stopped.value.code == 0 and seen == ['worker']
