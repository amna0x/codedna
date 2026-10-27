"""Real process-tree cancellation; never enumerate or terminate user processes."""
import ctypes
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from codedna.api.owned_process import ContainmentError, OwnedProcess


def wait_file(path):
    end = time.monotonic() + 15
    while time.monotonic() < end:
        if path.exists() and path.read_text().strip():
            return path.read_text().strip()
        time.sleep(.02)
    raise AssertionError(f'fixture did not become ready: {path}')


def alive(pid):
    if os.name == 'nt':
        from ctypes import wintypes
        api = ctypes.WinDLL('kernel32', use_last_error=True)
        api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        api.OpenProcess.restype = wintypes.HANDLE
        api.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = api.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        try:
            code = wintypes.DWORD()
            assert api.GetExitCodeProcess(handle, ctypes.byref(code))
            return code.value == 259
        finally:
            api.CloseHandle(handle)
    # A terminated orphan may briefly be a zombie on Linux containers.
    stat = Path(f'/proc/{pid}/stat')
    if stat.exists() and stat.read_text().split()[2] == 'Z':
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


@pytest.mark.parametrize('leader_exits', [False, True])
def test_owned_descendant_stops_but_unrelated_process_survives(repo, tmp_path, leader_exits):
    repo.write('A.java', 'class A {}'); repo.commit('fixture')
    before = repo.git('status', '--porcelain')
    child_ready = tmp_path / 'child.txt'
    script = tmp_path / 'trusted_worker.py'
    script.write_text('''import subprocess, sys, time
from pathlib import Path
sys.stdin.readline()  # no project work or children before containment
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])
Path(sys.argv[1]).write_text(str(child.pid))
if sys.argv[2] == 'True':
    sys.exit(0)
time.sleep(120)
''')
    unrelated = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])
    owned = None
    try:
        owned = OwnedProcess([sys.executable, str(script), str(child_ready), str(leader_exits)], cwd=repo.path)
        owned.process.stdin.write(b'go\n'); owned.process.stdin.flush()
        child_pid = int(wait_file(child_ready))
        assert alive(child_pid)
        if leader_exits:
            assert owned.process.wait(timeout=15) == 0
        owned.close(); owned.close()
        end = time.monotonic() + 10
        while alive(child_pid) and time.monotonic() < end:
            time.sleep(.02)
        assert not alive(child_pid)
        assert unrelated.poll() is None
        assert repo.git('status', '--porcelain') == before
        # A subsequent owned operation can start after cancellation.
        with OwnedProcess([sys.executable, '-c', "import sys; print(sys.stdin.readline().strip())"]) as later:
            output, error = later.process.communicate(b'later\n', timeout=15)
            assert output.strip() == b'later' and error == b''
    finally:
        if owned:
            owned.close()
            for stream in (owned.process.stdin, owned.process.stdout, owned.process.stderr):
                stream.close()
        unrelated.kill(); unrelated.wait(timeout=10)


def test_failed_containment_receives_no_input_and_leaves_no_worker(monkeypatch):
    if os.name != 'nt':
        pytest.skip('Windows Job Object assignment failure')
    import codedna.api.owned_process as module
    spawned = []
    original = module.subprocess.Popen
    def start(*args, **kwargs):
        process = original(*args, **kwargs); spawned.append(process); return process
    def fail(_pid):
        raise OSError('fixture assignment failure')
    monkeypatch.setattr(module.subprocess, 'Popen', start)
    monkeypatch.setattr(module, '_WindowsJob', fail)
    with pytest.raises(ContainmentError):
        OwnedProcess([sys.executable, '-c', 'import sys; sys.stdin.read(); raise SystemExit(91)'])
    assert len(spawned) == 1 and spawned[0].poll() is not None
