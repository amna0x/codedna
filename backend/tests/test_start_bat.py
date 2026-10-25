"""start.bat: the Windows IDE launcher, run against stubbed tools (no Node, no build)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="start.bat is a Windows batch file")

ROOT = Path(__file__).resolve().parents[2]

# Each stub appends one line to %STUB_LOG%, so the test can see what ran.
THEIA = r"""@echo off
>>"%STUB_LOG%" echo theia cwd=%CD% args=%* exe=%CODEDNA_EXECUTABLE% java=%JAVA_HOME% gradle=%GRADLE_HOME% gradlecache=%GRADLE_USER_HOME% replay=%CODEDNA_REPLAY_FOLDERS%
"""
PYTHON = r"""@echo off
>>"%STUB_LOG%" echo python %*
mkdir "%~2"
"""
NPM = r"""@echo off
>>"%STUB_LOG%" echo npm %*
if "%1"=="install" (
    mkdir node_modules\.bin
    copy /y "%STUB_DIR%\theia.cmd" node_modules\.bin\theia.cmd >nul
)
if "%1"=="run" (
    mkdir electron-app\lib\backend
    type nul > electron-app\lib\backend\main.js
)
"""


def checkout(tmp_path: Path, *, built: bool) -> tuple[Path, dict[str, str], Path]:
    repo = tmp_path / "code dna"  # a space, as in many Windows paths
    (repo / "ide" / "electron-app").mkdir(parents=True)
    shutil.copy(ROOT / "start.bat", repo / "start.bat")
    scripts = repo / ".venv" / "Scripts"
    scripts.mkdir(parents=True)
    (scripts / "codedna.exe").write_bytes(b"")
    (scripts / "python.cmd").write_text(PYTHON)

    stubs = tmp_path / "stubs"
    stubs.mkdir()
    (stubs / "theia.cmd").write_text(THEIA)
    (stubs / "npm.cmd").write_text(NPM)
    if built:
        (repo / "ide" / "node_modules" / ".bin").mkdir(parents=True)
        shutil.copy(stubs / "theia.cmd", repo / "ide" / "node_modules" / ".bin" / "theia.cmd")
        (repo / "ide" / "electron-app" / "lib" / "backend").mkdir(parents=True)
        (repo / "ide" / "electron-app" / "lib" / "backend" / "main.js").write_text("")

    home = tmp_path / "home"
    tools = home / ".codex" / "tools"
    tools.mkdir(parents=True)
    (tools / "java-maven.json").write_text(json.dumps(
        {"java_home": str(tmp_path / "jdk"), "maven_home": str(tmp_path / "maven")}))

    log = tmp_path / "log.txt"
    env = {**os.environ, "USERPROFILE": str(home), "STUB_LOG": str(log), "STUB_DIR": str(stubs),
           "PATH": f"{stubs};{os.environ['PATH']}"}
    env.pop("JAVA_HOME", None)
    return repo, env, log


def run(repo: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess:
    # As typed at a prompt: cmd /s /c strips only the outer pair of quotes, so a
    # quoted script path followed by a quoted argument survives intact.
    line = " ".join(f'"{part}"' for part in (repo / "start.bat", *args))
    return subprocess.run(f'cmd /s /c "{line}"', cwd=repo.parent,
                          env=env, capture_output=True, text=True, timeout=120)


def test_default_run_creates_the_demo_and_opens_it(tmp_path):
    repo, env, log = checkout(tmp_path, built=True)
    result = run(repo, env)
    assert result.returncode == 0, result.stdout + result.stderr
    lines = log.read_text().splitlines()
    demo = Path(env["USERPROFILE"]) / "codedna-demo"
    assert lines[0].startswith("python ") and str(demo) in lines[0]
    assert demo.is_dir()
    theia = lines[-1]
    assert f"cwd={repo / 'ide' / 'electron-app'}" in theia
    assert f'args=start "{demo}"' in theia
    assert f"exe={repo / '.venv' / 'Scripts' / 'codedna.exe'}" in theia
    assert f"java={tmp_path / 'jdk'}" in theia
    results = repo / "experiments" / "results"
    assert (f"replay={results / 'replay-2026-10-25'};{results / 'study11-2026-10-21'}"
            in theia)
    assert not any(line.startswith("npm") for line in lines)  # already built

    run(repo, env)  # the demo now exists: it is reused, not recreated
    assert sum(line.startswith("python ") for line in log.read_text().splitlines()) == 1


def test_given_folder_is_opened_and_first_run_installs_and_builds(tmp_path):
    repo, env, log = checkout(tmp_path, built=False)
    project = tmp_path / "my project"
    project.mkdir()
    result = run(repo, env, str(project))
    assert result.returncode == 0, result.stdout + result.stderr
    lines = log.read_text().splitlines()
    assert lines[:2] == ["npm install", "npm run build"]
    assert f'args=start "{project}"' in lines[-1]
    assert not any(line.startswith("python ") for line in lines)


def test_missing_core_stops_with_setup_instructions(tmp_path):
    repo, env, log = checkout(tmp_path, built=True)
    (repo / ".venv" / "Scripts" / "codedna.exe").unlink()
    result = run(repo, env)
    assert result.returncode == 1
    assert "pip install" in result.stdout
    assert not log.exists()


def test_rebuilds_once_after_a_pull_that_changed_the_ide(tmp_path):
    repo, env, log = checkout(tmp_path, built=True)
    git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com"]
    (repo / "ide" / "package.json").write_text("{}\n")
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "ide/package.json"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "ide"], check=True)
    builds = lambda: sum(line == "npm run build" for line in log.read_text().splitlines())  # noqa: E731

    assert run(repo, env).returncode == 0  # built before, but by an unknown revision
    assert builds() == 1
    stamp = repo / "ide" / "electron-app" / "lib" / "codedna-build.txt"
    head = subprocess.run([*git, "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()
    assert stamp.read_text().strip() == head

    assert run(repo, env).returncode == 0  # nothing changed: no rebuild
    assert builds() == 1

    (repo / "README.md").write_text("docs only\n")  # outside ide/: no rebuild
    subprocess.run([*git, "add", "README.md"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "docs"], check=True)
    assert run(repo, env).returncode == 0
    assert builds() == 1

    (repo / "ide" / "package.json").write_text('{"v": 2}\n')
    subprocess.run([*git, "commit", "-q", "-am", "ide change"], check=True)
    assert run(repo, env).returncode == 0
    assert builds() == 2


@pytest.mark.parametrize("custom_cache", [False, True])
def test_launcher_reuses_portable_gradle_and_preserves_custom_cache(tmp_path, custom_cache):
    repo, env, log = checkout(tmp_path, built=True)
    metadata = Path(env["USERPROFILE"]) / ".codex" / "tools" / "gradle"
    metadata.mkdir()
    gradle = tmp_path / "gradle with spaces"
    (metadata / "runtime.json").write_text(json.dumps({"home": str(gradle)}))
    env.pop("GRADLE_HOME", None)
    env.pop("GRADLE_USER_HOME", None)
    expected_cache = metadata / "cache"
    if custom_cache:
        expected_cache = tmp_path / "my gradle cache"
        env["GRADLE_USER_HOME"] = str(expected_cache)
    result = run(repo, env)
    assert result.returncode == 0, result.stdout + result.stderr
    launched = log.read_text().splitlines()[-1]
    assert f"gradle={gradle}" in launched
    assert f"gradlecache={expected_cache}" in launched
