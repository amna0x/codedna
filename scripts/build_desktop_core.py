"""Build the Windows desktop core; generated binaries stay outside version control.

Run with a Python environment containing CodeDNA's ml/api/desktop extras.
The console executable keeps stdin/stdout available for the IDE's API handshake;
the IDE starts it with windowsHide, so no terminal window is shown.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "codedna-core"
# codedna_java and codedna_python are the language plugins (D-054, D-060); their
# metadata carries the codedna.languages entry points, without which the bundled
# core finds no plugin.
PACKAGES = ("codedna", "codedna_java", "codedna_python", "uvicorn", "tree_sitter_java")
VERSIONS = ("codedna", "codedna-java", "codedna-python", "pyinstaller", "pyinstaller-hooks-contrib", "scikit-learn",
            "scipy", "numpy", "tree-sitter", "tree-sitter-java", "fastapi", "uvicorn")


def build_command(root: Path) -> list[str]:
    work = root / "build" / "desktop-core"
    args = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
            "--onedir", "--console", "--noupx", "--name", NAME,
            "--distpath", str(root / "ide" / "electron-app" / "resources"),
            "--workpath", str(work / "work"), "--specpath", str(work),
            "--paths", str(root / "backend"),
            "--paths", str(root / "plugins" / "codedna-java"),
            "--paths", str(root / "plugins" / "codedna-python"), "--copy-metadata", "codedna",
            "--copy-metadata", "codedna-java", "--copy-metadata", "codedna-python"]
    for package in PACKAGES:
        args += ["--collect-all", package]
    for module in ("matplotlib", "pytest", "IPython", "notebook", "sklearn.tests",
                   "scipy.tests", "numpy.tests"):
        args += ["--exclude-module", module]
    return args + [str(root / "scripts" / "desktop_core_entry.py")]


def write_manifest(bundle: Path) -> dict:
    files = {}
    for file in sorted(bundle.rglob("*")):
        if file.is_file() and file.name != "bundle-manifest.json":
            with file.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            files[file.relative_to(bundle).as_posix()] = digest
    manifest = {"python": platform.python_version(), "platform": sys.platform,
                "machine": platform.machine(), "packages": {
                    name: importlib.metadata.version(name) for name in VERSIONS},
                "files": files}
    (bundle / "bundle-manifest.json").write_text(json.dumps(manifest, indent=2),
                                                encoding="utf-8")
    return manifest


def main() -> int:
    if sys.platform != "win32":
        print("Build the Windows desktop core on Windows with Windows Python.", file=sys.stderr)
        return 1
    try:
        importlib.metadata.version("pyinstaller")
    except importlib.metadata.PackageNotFoundError:
        print('Install build prerequisites: python -m pip install -e ".[ml,api,desktop]"',
              file=sys.stderr)
        return 1
    for plugin, label in (("codedna-java", "Java"), ("codedna-python", "Python")):
        try:
            importlib.metadata.version(plugin)
        except importlib.metadata.PackageNotFoundError:
            print(f"Install the {label} plugin first: python -m pip install -e plugins/{plugin}",
                  file=sys.stderr)
            return 1
    (ROOT / "build" / "desktop-core").mkdir(parents=True, exist_ok=True)
    subprocess.run(build_command(ROOT), cwd=ROOT, check=True)
    bundle = ROOT / "ide" / "electron-app" / "resources" / NAME
    if not (bundle / f"{NAME}.exe").is_file():
        raise RuntimeError("freezer completed without the desktop core executable")
    manifest = write_manifest(bundle)
    print(f"Desktop core ready: {bundle} ({len(manifest['files'])} verified files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
