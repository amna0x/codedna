"""Contain trusted analysis workers before sending them any project input.

This is process ownership, not a sandbox for untrusted repository code. Only
CodeDNA chooses worker commands; build/test execution is outside this module.
"""
from __future__ import annotations

import os
import signal
import subprocess
from threading import Lock


class ContainmentError(RuntimeError):
    """Reliable termination of a worker tree could not be established."""


class _WindowsJob:
    def __init__(self, pid: int):
        import ctypes
        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [
                ('PerProcessUserTimeLimit', ctypes.c_longlong),
                ('PerJobUserTimeLimit', ctypes.c_longlong),
                ('LimitFlags', wintypes.DWORD),
                ('MinimumWorkingSetSize', ctypes.c_size_t),
                ('MaximumWorkingSetSize', ctypes.c_size_t),
                ('ActiveProcessLimit', wintypes.DWORD),
                ('Affinity', ctypes.c_size_t),
                ('PriorityClass', wintypes.DWORD),
                ('SchedulingClass', wintypes.DWORD),
            ]

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in (
                'ReadOperationCount', 'WriteOperationCount', 'OtherOperationCount',
                'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [('BasicLimitInformation', BasicLimits),
                        ('IoInfo', IoCounters),
                        ('ProcessMemoryLimit', ctypes.c_size_t),
                        ('JobMemoryLimit', ctypes.c_size_t),
                        ('PeakProcessMemoryUsed', ctypes.c_size_t),
                        ('PeakJobMemoryUsed', ctypes.c_size_t)]

        api = ctypes.WinDLL('kernel32', use_last_error=True)
        api.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        api.CreateJobObjectW.restype = wintypes.HANDLE
        api.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                               ctypes.c_void_p, wintypes.DWORD]
        api.SetInformationJobObject.restype = wintypes.BOOL
        api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        api.OpenProcess.restype = wintypes.HANDLE
        api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        api.AssignProcessToJobObject.restype = wintypes.BOOL
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        api.CloseHandle.restype = wintypes.BOOL
        self._api = api
        self._handle = api.CreateJobObjectW(None, None)
        if not self._handle:
            raise ctypes.WinError(ctypes.get_last_error())
        process = None
        try:
            limits = ExtendedLimits()
            limits.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE
            if not api.SetInformationJobObject(self._handle, 9, ctypes.byref(limits),
                                              ctypes.sizeof(limits)):
                raise ctypes.WinError(ctypes.get_last_error())
            # Assignment requires PROCESS_SET_QUOTA | PROCESS_TERMINATE.
            process = api.OpenProcess(0x0101, False, pid)
            if not process or not api.AssignProcessToJobObject(self._handle, process):
                raise ctypes.WinError(ctypes.get_last_error())
        except BaseException:
            self.close()
            raise
        finally:
            if process:
                api.CloseHandle(process)

    def close(self):
        if self._handle:
            if not self._api.CloseHandle(self._handle):
                import ctypes
                raise ctypes.WinError(ctypes.get_last_error())
            self._handle = None


class OwnedProcess:
    """A private process tree, terminated by close even if its leader has exited.

    The trusted worker must wait on stdin before importing plugins or examining
    project input. Do not send that input until this constructor has succeeded.
    Only the owner may use this object; it is never populated from API PIDs.
    """
    def __init__(self, command: list[str], *, cwd=None, env=None):
        self._lock = Lock()
        self._closed = False
        self._job = None
        self.process = subprocess.Popen(
            command, cwd=cwd, env=env, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            start_new_session=os.name != 'nt',
        )
        try:
            if os.name == 'nt':
                self._job = _WindowsJob(self.process.pid)
        except BaseException as exc:
            # No input has been sent, so this trusted bootstrap has no children.
            self.process.kill()
            self.process.communicate()
            raise ContainmentError('analysis worker containment could not be established') from exc

    def close(self):
        """Stop the owned tree only. Safe after exit and repeated cancellation."""
        with self._lock:
            if not self._closed:
                if self._job is not None:
                    self._job.close()
                elif os.name != 'nt':
                    try:
                        os.killpg(self.process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                self._closed = True
            # Concurrent cancellation callers must also wait for cleanup.
            self.process.wait(timeout=10)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
