"""Static discovery of pytest tests in one commit.

A *test* is a test module (pytest's unit of selection here, like a JUnit
test class for Java): a file matching ``python_files`` (default
``test_*.py`` and ``*_test.py``) that defines test functions
(``python_functions``, default ``test``) or test classes (``python_classes``,
default ``Test``, without ``__init__``, or any ``unittest.TestCase``
subclass) with test methods. Its ID is the module's graph ID,
``py:<module>``.

pytest's settings are read from the repository root, in pytest's own order
(``pytest.ini``, ``.pytest.ini``, ``pyproject.toml`` ``[tool.pytest.ini_options]``,
``tox.ini`` ``[pytest]``, ``setup.cfg`` ``[tool:pytest]``): ``python_files``,
``python_classes``, ``python_functions``, ``testpaths`` and
``norecursedirs``. A test outside ``testpaths`` is reported but does not run
by default, as with a plain ``pytest`` call. Discovery is syntactic: test
methods inherited from another file's base class, plugins that change
collection, and ``conftest.py`` hooks are not seen.
"""

from __future__ import annotations

import configparser
import fnmatch
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath

from codedna.git_analysis.git import resolve_commit, resolve_repository, run_git, run_git_bytes
from codedna_python.builder import parse_commit
from codedna_python.parser import CLASS, FUNCTION, METHOD

DEFAULT_FILES = ("test_*.py", "*_test.py")
DEFAULT_NORECURSE = ("*.egg", ".*", "_darcs", "build", "CVS", "dist", "node_modules", "venv",
                     "{arch}")


@dataclass
class DiscoveredTest:
    id: str  # py:<module>, same as the graph's module node ID without "type:"
    file: str
    framework: str  # "pytest"
    methods: list[str]  # "test_x" or "TestClass.test_x"
    in_testpaths: bool = True

    @property
    def runs_by_default(self) -> bool:
        return self.in_testpaths


@dataclass
class DiscoveryReport:
    repository: str
    commit: str
    tests: list[DiscoveredTest]
    warnings: list[str]
    build_tool: str | None = "pytest"

    def to_dict(self) -> dict:
        tests = []
        for test in self.tests:
            entry = asdict(test)
            entry["runs_by_default"] = test.runs_by_default
            tests.append(entry)
        return {"repository": self.repository, "commit": self.commit,
                "build_tool": self.build_tool,
                "test_count": len(tests), "tests": tests, "warnings": self.warnings}


@dataclass
class PytestConfig:
    files: tuple[str, ...] = DEFAULT_FILES
    classes: tuple[str, ...] = ("Test",)
    functions: tuple[str, ...] = ("test",)
    testpaths: tuple[str, ...] = ()
    norecursedirs: tuple[str, ...] = DEFAULT_NORECURSE
    source: str | None = None  # config file it came from
    warnings: list[str] = field(default_factory=list)


def discover_tests(repo_path: str | Path, revision: str = "HEAD") -> DiscoveryReport:
    repo = resolve_repository(repo_path)
    return discover_tests_for_commit(repo, resolve_commit(repo, revision))


def discover_tests_for_commit(repo: Path, commit: str, cache: dict | None = None) -> DiscoveryReport:
    config = read_config(repo, commit)
    warnings = list(config.warnings)
    tests = []
    for path, result in sorted(parse_commit(repo, commit, cache).items()):
        if not _is_test_file(path, config):
            continue
        if result.has_syntax_errors:
            warnings.append(f"{path}: {result.error}; pytest will report it as a collection error")
            tests.append(DiscoveredTest(result.module_id, path, "pytest", [],
                                        _in_testpaths(path, config)))
            continue
        methods = _test_names(result, config)
        if methods:
            tests.append(DiscoveredTest(result.module_id, path, "pytest", methods,
                                        _in_testpaths(path, config)))
    seen: dict[str, str] = {}
    for test in tests:
        if test.id in seen:
            warnings.append(f"test module {test.id} comes from {seen[test.id]} and {test.file}; "
                            "results are matched to the first")
        seen.setdefault(test.id, test.file)
    return DiscoveryReport(str(repo), commit, tests, warnings)


def _test_names(result, config: PytestConfig) -> list[str]:
    module = result.module_id
    bases = {}
    for base in result.bases:
        bases.setdefault(base.class_id, []).append(base.name or "")
    names = [d.name for d in result.declarations
             if d.kind == FUNCTION and d.parent == module and _matches(d.name, config.functions)]
    for cls in (d for d in result.declarations if d.kind == CLASS and d.parent == module):
        unittest_case = any(b.rpartition(".")[2].endswith("TestCase") for b in bases.get(cls.id, ()))
        members = [d for d in result.declarations if d.kind == METHOD and d.parent == cls.id]
        if unittest_case:
            names += [f"{cls.name}.{m.name}" for m in members if m.name.startswith("test")]
            continue
        if not _matches(cls.name, config.classes) or any(m.name == "__init__" for m in members):
            continue
        own = [f"{cls.name}.{m.name}" for m in members if _matches(m.name, config.functions)]
        if not own and bases.get(cls.id):
            own = [f"{cls.name}.(inherited)"]  # tests may come from a base class
        names += own
    return sorted(dict.fromkeys(names))


def _matches(name: str, patterns: tuple[str, ...]) -> bool:
    """pytest's rule: a pattern with glob characters is a glob, otherwise a prefix."""
    return any(fnmatch.fnmatchcase(name, p) if any(c in p for c in "*?[") else name.startswith(p)
               for p in patterns)


def _is_test_file(path: str, config: PytestConfig) -> bool:
    pure = PurePosixPath(path)
    if any(fnmatch.fnmatchcase(part, pattern) for part in pure.parts[:-1]
           for pattern in config.norecursedirs):
        return False
    return any(fnmatch.fnmatchcase(pure.name, pattern) for pattern in config.files)


def _in_testpaths(path: str, config: PytestConfig) -> bool:
    if not config.testpaths:
        return True
    return any(path == tp or path.startswith(tp.rstrip("/") + "/") or fnmatch.fnmatchcase(path, tp)
               for tp in config.testpaths)


def read_config(repo: Path, commit: str) -> PytestConfig:
    """pytest settings from the first root config file that has a pytest section."""
    readers = (("pytest.ini", _ini("pytest")), (".pytest.ini", _ini("pytest")),
               ("pyproject.toml", _pyproject),
               ("tox.ini", _ini("pytest")), ("setup.cfg", _ini("tool:pytest")))
    present = set(run_git(repo, "ls-tree", "--name-only", "-z", commit, "--",
                          *(name for name, _ in readers)).split("\0"))
    for name, reader in readers:
        if name not in present:
            continue
        text = run_git_bytes(repo, "show", "--no-textconv", f"{commit}:{name}").decode(
            "utf-8", errors="replace")
        try:
            values = reader(text, name in ("pytest.ini", ".pytest.ini"))
        except (configparser.Error, tomllib.TOMLDecodeError, ValueError) as exc:
            return PytestConfig(warnings=[f"{name} could not be read ({exc}); pytest defaults "
                                          "are used for discovery"])
        if values is None:
            continue
        config = PytestConfig(source=name)
        for key, attribute in (("python_files", "files"), ("python_classes", "classes"),
                               ("python_functions", "functions"), ("testpaths", "testpaths"),
                               ("norecursedirs", "norecursedirs")):
            if key in values:
                setattr(config, attribute, tuple(values[key]))
        return config
    return PytestConfig()


def _ini(section: str):
    def read(text: str, always: bool) -> dict[str, list[str]] | None:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(text)
        if not parser.has_section(section):
            return {} if always else None  # an empty pytest.ini still marks the root
        return {key: parser.get(section, key).split() for key in parser.options(section)}
    return read


def _pyproject(text: str, _always: bool) -> dict[str, list[str]] | None:
    options = tomllib.loads(text).get("tool", {}).get("pytest", {}).get("ini_options")
    if options is None:
        return None
    return {key: value.split() if isinstance(value, str) else [str(v) for v in value]
            for key, value in options.items() if isinstance(value, (str, list))}
