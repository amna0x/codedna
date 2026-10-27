"""Transactional, per-user wheel installation for the frozen desktop (D-074).

The caller verifies the official catalogue and full wheel checksum first.
No project interpreter, pip, package index or administrator access is used.
"""
from __future__ import annotations

import configparser
from contextlib import contextmanager
import importlib
from importlib import metadata
import inspect
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
import uuid
import zipfile

from codedna.plugins.base import LanguagePlugin, api_compatible
from codedna.plugins.catalogue import CatalogueError, PluginVersion

_BOOT: tuple[Path, ...] | None = None
_ID = re.compile(r"[a-z][a-z0-9-]{1,40}")


def root() -> Path:
    override = os.environ.get("CODEDNA_PLUGIN_HOME")
    path = Path(override) if override else Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/share")) / "CodeDNA/plugins"
    if not path.is_absolute():
        raise CatalogueError("CODEDNA_PLUGIN_HOME must be an absolute directory")
    return path.resolve()


def _path(home: Path, item: dict) -> Path:
    directory = item.get("directory", "")
    if not isinstance(directory, str) or not re.fullmatch(r"[a-z0-9.-]+-[0-9a-f]{32}", directory):
        raise CatalogueError("desktop plugin manifest contains an invalid directory")
    path = (home / "versions" / directory).resolve()
    if not path.is_relative_to((home / "versions").resolve()):
        raise CatalogueError("desktop plugin path escapes its managed directory")
    return path


def _read(home: Path) -> dict:
    file = home / "active.json"
    if not file.exists():
        return {}
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1 or not isinstance(data.get("plugins"), dict):
            raise ValueError("unsupported schema")
        for name, item in data["plugins"].items():
            if not _ID.fullmatch(name) or not isinstance(item, dict):
                raise ValueError("invalid plugin")
            _path(home, item)
        return data["plugins"]
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        raise CatalogueError(f"cannot read desktop plugin manifest: {exc}") from exc


@contextmanager
def _locked(home: Path):
    home.mkdir(parents=True, exist_ok=True)
    with (home / ".lock").open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        acquired = False
        try:
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except OSError as exc:
            raise CatalogueError("another desktop plugin change is in progress; retry when it finishes") from exc
        try:
            yield
        finally:
            if acquired:
                stream.seek(0)
                if sys.platform == "win32":
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _write(home: Path, items: dict) -> None:
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=home, suffix=".tmp", delete=False) as stream:
        temp = Path(stream.name)
        json.dump({"schema_version": 1, "plugins": items}, stream)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.replace(temp, home / "active.json")
    finally:
        temp.unlink(missing_ok=True)


def activate() -> tuple[Path, ...]:
    """Snapshot activation once per process; updates/removals take effect on restart."""
    global _BOOT
    if _BOOT is None:
        home = root()
        paths = tuple(_path(home, item) / "site" for _, item in sorted(_read(home).items()))
        for path in paths:
            if not path.is_dir():
                raise CatalogueError(f"installed desktop plugin files are missing: {path}")
        for path in reversed(paths):
            sys.path.insert(0, str(path))
        importlib.invalidate_caches()
        _BOOT = paths
    return _BOOT


def entry_points() -> list:
    return [point for dist in metadata.distributions(path=[str(p) for p in activate()])
            for point in dist.entry_points if point.group == "codedna.languages"]


def _dependencies(dist: metadata.Distribution) -> None:
    from packaging.requirements import Requirement
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version
    import platform
    python = dist.metadata.get("Requires-Python")
    if python and Version(platform.python_version()) not in SpecifierSet(python):
        raise CatalogueError(f"plugin requires Python {python}; desktop has {platform.python_version()}")
    pending = [(value, {""}) for value in dist.requires or []]
    seen = set()
    while pending:
        raw, extras = pending.pop()
        requirement = Requirement(raw)
        if requirement.marker and not any(requirement.marker.evaluate({"extra": extra}) for extra in extras):
            continue
        key = (requirement.name.lower(), tuple(sorted(requirement.extras)))
        if key in seen:
            continue
        seen.add(key)
        if requirement.url:
            raise CatalogueError(f"desktop plugins cannot install direct-URL dependencies: {requirement.name}")
        try:
            installed = metadata.distribution(requirement.name)
        except metadata.PackageNotFoundError as exc:
            raise CatalogueError(f"desktop dependency is missing: {requirement}; working plugin unchanged") from exc
        if installed.version not in requirement.specifier:
            raise CatalogueError(f"desktop dependency {requirement} is incompatible with installed {installed.version}; working plugin unchanged")
        pending.extend((value, {"", *requirement.extras}) for value in installed.requires or [])


def _wheel(wheel: Path, entry: PluginVersion, site: Path) -> None:
    from installer import install as install_wheel
    from installer.destinations import SchemeDictionaryDestination
    from installer.sources import WheelFile
    from packaging.tags import sys_tags
    from packaging.utils import canonicalize_name, parse_wheel_filename

    name, version, _, tags = parse_wheel_filename(wheel.name)
    if canonicalize_name(entry.package) != name or str(version) != entry.version:
        raise CatalogueError("wheel identity does not match its catalogue entry")
    if not tags.intersection(sys_tags()):
        raise CatalogueError("wheel is incompatible with this desktop's Python or operating system")
    namespace = name.replace("-", "_")
    if namespace in sys.stdlib_module_names or namespace in {"codedna", "installer", "packaging"}:
        raise CatalogueError("a language plugin cannot replace the core or its installation runtime")
    with zipfile.ZipFile(wheel) as archive:
        files = archive.infolist()
        if len(files) > 10000 or sum(item.file_size for item in files) > 200 * 1024 * 1024:
            raise CatalogueError("plugin wheel is too large when unpacked")
        seen = set()
        for item in files:
            path = PurePosixPath(item.filename)
            if (path.is_absolute() or ".." in path.parts or "\\" in item.filename or ":" in item.filename
                    or stat.S_ISLNK(item.external_attr >> 16)):
                raise CatalogueError("wheel contains an unsafe path or symbolic link")
            if item.is_dir():
                continue
            folded = item.filename.casefold()
            if folded in seen:
                raise CatalogueError("wheel contains duplicate file names")
            seen.add(folded)
            if path.suffix.lower() == ".pth":
                raise CatalogueError("desktop language plugins cannot contain .pth startup hooks")
            first = path.parts[0]
            if not first.endswith((".dist-info", ".data")) and first.split(".", 1)[0] != namespace:
                raise CatalogueError(f"plugin code must use its own {namespace} namespace")
            if first.endswith(".data"):
                if len(path.parts) < 3 or path.parts[1] not in {"purelib", "platlib", "data", "headers"}:
                    raise CatalogueError("desktop language plugins cannot install executable scripts")
                if path.parts[1] in {"purelib", "platlib"} and path.parts[2].split(".", 1)[0] != namespace:
                    raise CatalogueError("wheel data tries to replace another package")
            if path.name == "entry_points.txt":
                config = configparser.ConfigParser(interpolation=None)
                config.read_string(archive.read(item).decode("utf-8"))
                if config.has_section("console_scripts") or config.has_section("gui_scripts"):
                    raise CatalogueError("desktop language plugins cannot register Python command-line scripts")
    site.mkdir()
    scheme = {key: str(site) for key in ("purelib", "platlib")}
    scheme.update({key: str(site.parent / key) for key in ("scripts", "headers", "data")})

    class Destination(SchemeDictionaryDestination):
        def write_to_fs(self, scheme, path, stream, is_executable):
            target = (Path(self.scheme_dict[scheme]) / path).resolve()
            if not target.is_relative_to(site.parent.resolve()):
                raise CatalogueError("wheel installation escapes its staging directory")
            return super().write_to_fs(scheme, path, stream, is_executable)

    with WheelFile.open(wheel) as source:
        source.validate_record(validate_contents=True)
        install_wheel(source, Destination(scheme, interpreter=sys.executable, script_kind="win-amd64",
                                         bytecode_optimization_levels=()), {"INSTALLER": b"codedna-desktop\n"})
    distributions = list(metadata.distributions(path=[str(site)]))
    if len(distributions) != 1:
        raise CatalogueError("wheel must contain exactly one plugin distribution")
    dist = distributions[0]
    if canonicalize_name(dist.metadata["Name"]) != name or dist.version != entry.version:
        raise CatalogueError("wheel metadata does not match its catalogue identity")
    points = [p for p in dist.entry_points if p.group == "codedna.languages"]
    if len(points) != 1 or points[0].name != entry.plugin or points[0].module.split(".")[0] != namespace:
        raise CatalogueError("wheel must register the catalogue language in its own namespace")
    _dependencies(dist)


def probe(site: Path, plugin: str, package: str, version: str) -> None:
    """Run in an isolated child, never replace imports in the live IDE process."""
    sys.path.insert(0, str(site))
    importlib.invalidate_caches()
    from packaging.utils import canonicalize_name
    distributions = list(metadata.distributions(path=[str(site)]))
    if len(distributions) != 1 or canonicalize_name(distributions[0].metadata["Name"]) != canonicalize_name(package) or distributions[0].version != version:
        raise CatalogueError("staged plugin identity is invalid")
    point = next(p for p in distributions[0].entry_points if p.group == "codedna.languages" and p.name == plugin)
    factory = point.load()
    if not Path(inspect.getfile(factory)).resolve().is_relative_to(site.resolve()):
        raise CatalogueError("staged plugin resolved to code outside its wheel")
    instance = factory()
    if not isinstance(instance, LanguagePlugin) or instance.name != plugin or instance.version != version or not api_compatible(instance.api_version):
        raise CatalogueError("staged plugin does not implement the compatible language interface")


def _probe(site: Path, entry: PluginVersion) -> None:
    command = ([sys.executable, "--codedna-plugin-probe"] if getattr(sys, "frozen", False) else
               [sys.executable, "-m", "codedna.plugins.desktop_store", "--probe"])
    result = subprocess.run([*command, str(site), entry.plugin, entry.package, entry.version],
                            capture_output=True, text=True, timeout=60,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    if result.returncode:
        raise CatalogueError(f"plugin failed its isolated load check; working version unchanged: {result.stderr.strip()[-2000:]}")


def install(wheel: Path, entry: PluginVersion, digest: str) -> dict:
    home = root()
    try:
        with _locked(home):
            items = _read(home)
            previous = items.get(entry.plugin, {}).get("version")
            if previous is None:
                try:
                    previous = metadata.version(entry.package)
                except metadata.PackageNotFoundError:
                    pass
            versions = home / "versions"
            versions.mkdir(exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=".stage-", dir=home) as directory:
                stage = Path(directory).resolve()
                assert stage.parent == home and stage.name.startswith(".stage-")
                site = stage / "site"
                _wheel(wheel, entry, site)
                _probe(site, entry)
                target = versions / f"{entry.plugin}-{entry.version}-{uuid.uuid4().hex}"
                stage.rename(target)
                items[entry.plugin] = {"package": entry.package, "version": entry.version,
                                       "directory": target.name, "sha256": digest}
                _write(home, items)
            return {"plugin": entry.plugin, "version": entry.version, "sha256": digest,
                    "status": "installed", "previous_version": previous, "restart_required": True}
    except CatalogueError:
        raise
    except Exception as exc:
        raise CatalogueError(f"desktop plugin was not activated; working version unchanged: {exc}") from exc


def remove(plugin: str) -> dict:
    home = root()
    with _locked(home):
        items = _read(home)
        if plugin not in items:
            raise CatalogueError(f"{plugin} has no optional desktop installation; bundled plugins cannot be removed")
        del items[plugin]
        try:
            _write(home, items)
        except OSError as exc:
            raise CatalogueError(f"could not remove desktop plugin; active version unchanged: {exc}") from exc
    # Loaded native modules can be locked on Windows. Keep inactive versions as
    # rollback cache; no app/bundled files are removed while they may be in use.
    return {"plugin": plugin, "status": "removed", "restart_required": True}


def probe_main(args: list[str]) -> int:
    try:
        if len(args) != 4:
            raise CatalogueError("invalid plugin probe arguments")
        probe(Path(args[0]), *args[1:])
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(probe_main(sys.argv[2:]) if sys.argv[1:2] == ["--probe"] else 1)
