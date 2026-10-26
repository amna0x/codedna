"""Static build layout of one commit: Maven (single or multi-module) or Gradle.

Read from committed build files only; no build tool runs here. Maven modules
come from ``<modules>`` (followed recursively); custom Surefire ``<includes>``
and ``<excludes>`` come from each module's own ``pom.xml`` (inherited parent
configuration and profiles are not resolved; modules listed only inside
profiles are reported, not followed). A module's test sources are its
``<testSourceDirectory>`` (default ``src/test/java``) plus any directory added
with build-helper-maven-plugin's ``add-test-source`` goal, which projects use
to share one test folder between modules (HikariCP 2.x does this). Gradle modules come from ``include`` lines in
``settings.gradle(.kts)`` (a syntactic reading, recorded as such); Gradle runs
every class in the ``test`` source set by default, so no name filter applies.
A Gradle test source set moved with ``test.java.srcDirs = [...]`` (or
``+=``, ``srcDir``) is read syntactically from the ``.gradle`` scripts: in a
module's own build script it applies to that module, in any other script
(such as a shared ``gradle/*.gradle`` applied to all projects) to every
module, which is reported as a warning (D-064).
"""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

from codedna.git_analysis.blobs import list_files, read_blobs

SUREFIRE_DEFAULTS = ["**/Test*.java", "**/*Test.java", "**/*Tests.java", "**/*TestCase.java"]
_GRADLE_SETTINGS = ("settings.gradle", "settings.gradle.kts")
_GRADLE_BUILD = ("build.gradle", "build.gradle.kts")
# `include "a", "b"` or `include("a",\n "b")`; comments are removed first.
_INCLUDE = re.compile(r"""^[ \t]*include\b[ \t]*(\([^)]*\)|[^\n]*)""", re.MULTILINE)
_QUOTED = re.compile(r"""["']([^"']+)["']""")
_COMMENT = re.compile(r"""//[^\n]*|/\*.*?\*/""", re.DOTALL)
# test.java.srcDirs = ['src/test'], += [...], test.java.srcDir 'x', test.java.srcDir("x")
_TEST_SRC = re.compile(
    r"""\btest\.java\.(srcDirs?)\s*(\+?=)?\s*\(?\s*(\[[^\]]*\]|["'][^"']*["'])""")


@dataclass
class BuildLayout:
    tool: str | None  # "maven" | "gradle" | None
    modules: list[str]  # module directories relative to the root; "" is the root
    includes: dict[str, list[str]] = field(default_factory=dict)  # module → Surefire includes
    excludes: dict[str, list[str]] = field(default_factory=dict)  # module → Surefire excludes
    warnings: list[str] = field(default_factory=list)
    # module → test source roots ("dir/", repository-relative); default <module>/src/test/java/
    test_roots: dict[str, list[str]] = field(default_factory=dict)

    def roots(self, module: str) -> list[str]:
        return self.test_roots.get(module) or [f"{module}/src/test/java/" if module else "src/test/java/"]

    def _match(self, path: str) -> tuple[str, str] | None:
        """(module, root) of the most specific test root containing ``path``.

        A folder shared by several modules (build-helper) belongs to the first
        of them in sorted order; its tests run in each, under the same ID.
        """
        best = None
        for module in self.modules:
            for root in self.roots(module):
                if path.startswith(root) and (best is None or len(root) > len(best[1])):
                    best = (module, root)
        return best

    def module_of(self, path: str) -> str | None:
        """Module whose test sources contain ``path`` (most specific root wins)."""
        match = self._match(path)
        return match[0] if match else None

    def runs_by_default(self, path: str) -> bool:
        """Would the build tool run this test file without extra configuration?"""
        match = self._match(path)
        if match is None:
            return False
        if self.tool == "gradle":
            return True
        module, root = match
        relative = path.removeprefix(root)
        patterns = self.includes.get(module) or SUREFIRE_DEFAULTS
        return (any(_matches(relative, p) for p in patterns)
                and not any(_matches(relative, p) for p in self.excludes.get(module, ())))


def _matches(relative: str, pattern: str) -> bool:
    """Surefire include pattern; "**/Name*.java" matches the file name at any depth.

    Surefire treats ``.class`` and ``.java`` endings alike (both name test
    classes), so ``**/*.class`` selects every test class.
    """
    pattern = pattern.strip().lstrip("/")
    if pattern.endswith(".class"):
        pattern = pattern.removesuffix(".class") + ".java"
    rest = pattern.removeprefix("**/")
    if rest != pattern and "/" not in rest:
        return fnmatch(PurePosixPath(relative).name, rest)
    return fnmatch(relative, pattern)


def detect_build(repo: Path, commit: str) -> BuildLayout:
    files = {path: blob for path, blob in list_files(repo, commit)}
    if "pom.xml" in files:
        return _maven(repo, files)
    if any(name in files for name in _GRADLE_SETTINGS + _GRADLE_BUILD):
        return _gradle(repo, files)
    return BuildLayout(None, [], warnings=["no pom.xml or Gradle build file at the repository root"])


def _maven(repo: Path, files: dict[str, str]) -> BuildLayout:
    layout = BuildLayout("maven", [])
    pending = [""]
    while pending:
        module = pending.pop()
        pom = f"{module}/pom.xml" if module else "pom.xml"
        if module in layout.modules:
            continue
        if pom not in files:
            layout.warnings.append(f"module {module!r} listed but {pom} is missing")
            continue
        layout.modules.append(module)
        try:
            root = ElementTree.fromstring(read_blobs(repo, [files[pom]])[files[pom]])
        except ElementTree.ParseError as exc:
            layout.warnings.append(f"{pom}: not readable XML ({exc}); its modules are unknown")
            continue
        for child in _all(root, "modules", "module"):
            name = (child.text or "").strip().removesuffix("/pom.xml").strip("/")
            if not name:
                continue
            path = posixpath.normpath(posixpath.join(module, name))
            if path == ".." or path.startswith("../") or posixpath.isabs(path):
                layout.warnings.append(f"{pom}: module {name!r} is outside the repository; not followed")
            else:
                pending.append("" if path == "." else path)
        if _all(root, "profiles", "profile", "modules", "module"):
            layout.warnings.append(f"{pom}: modules inside <profiles> are not followed")
        roots = _maven_test_roots(root, module, pom, layout.warnings)
        if roots:
            layout.test_roots[module] = roots
        surefire = [plugin for plugin in _all(root, "build", "plugins", "plugin")
                    if (_child_text(plugin, "artifactId") or "") == "maven-surefire-plugin"]
        for name, store in (("include", layout.includes), ("exclude", layout.excludes)):
            patterns = [i.text.strip() for plugin in surefire
                        for i in _all(plugin, "configuration", name + "s", name)
                        if i.text and i.text.strip()]
            if patterns:
                store[module] = patterns
    layout.modules.sort()
    return layout


def _maven_test_roots(pom_root: ElementTree.Element, module: str, pom: str,
                      warnings: list[str]) -> list[str]:
    """Test source roots of one module; [] means the default ``src/test/java``."""
    configured = [(_child_text(b, "testSourceDirectory") or "").strip()
                  for b in _all(pom_root, "build")]
    main = next((d for d in configured if d), "src/test/java")
    extra = [s.text.strip() for plugin in _all(pom_root, "build", "plugins", "plugin")
             if (_child_text(plugin, "artifactId") or "") == "build-helper-maven-plugin"
             for execution in _all(plugin, "executions", "execution")
             if any((g.text or "").strip() == "add-test-source"
                    for g in _all(execution, "goals", "goal"))
             for s in _all(execution, "configuration", "sources", "source")
             if s.text and s.text.strip()]
    if main == "src/test/java" and not extra:
        return []
    roots = []
    for directory in [main, *extra]:
        if "${" in directory:
            warnings.append(f"{pom}: test source {directory!r} uses a property; not followed")
            continue
        path = posixpath.normpath(posixpath.join(module, directory))
        if path == ".." or path.startswith("../") or posixpath.isabs(path):
            warnings.append(f"{pom}: test source {directory!r} is outside the repository; not followed")
            continue
        root = "" if path == "." else path + "/"
        if root not in roots:
            roots.append(root)
    return roots


def _gradle(repo: Path, files: dict[str, str]) -> BuildLayout:
    layout = BuildLayout("gradle", [""])
    settings = next((f for f in _GRADLE_SETTINGS if f in files), None)
    if settings:
        text = read_blobs(repo, [files[settings]])[files[settings]].decode("utf-8", "replace")
        text = _COMMENT.sub("", text)
        for arguments in _INCLUDE.findall(text):
            for name in _QUOTED.findall(arguments):
                module = name.strip(":").replace(":", "/")
                if module and module not in layout.modules:
                    layout.modules.append(module)
        layout.warnings.append(f"Gradle modules read syntactically from {settings}; "
                               "programmatic includes are not seen")
        if "projectDir" in text:
            layout.warnings.append(f"{settings} moves project directories (projectDir); "
                                   "those modules may be placed wrongly")
    layout.modules.sort()
    _gradle_test_roots(repo, files, layout)
    return layout


def _gradle_test_roots(repo: Path, files: dict[str, str], layout: BuildLayout) -> None:
    """Apply ``test.java.srcDirs`` settings; shared scripts first, then module scripts."""
    scripts = sorted(path for path in files if path.endswith((".gradle", ".gradle.kts"))
                     and PurePosixPath(path).name not in _GRADLE_SETTINGS)
    contents = read_blobs(repo, [files[path] for path in scripts])
    shared: list[tuple[bool, list[str]]] = []  # (replaces the defaults, directories)
    own: dict[str, list[tuple[bool, list[str]]]] = {}
    for script in scripts:
        text = _COMMENT.sub("", contents[files[script]].decode("utf-8", "replace"))
        for kind, operator, value in _TEST_SRC.findall(text):
            rule = (kind == "srcDirs" and operator == "=", _QUOTED.findall(value))
            folder = posixpath.dirname(script)
            if PurePosixPath(script).name in _GRADLE_BUILD and folder in layout.modules:
                own.setdefault(folder, []).append(rule)
            else:
                shared.append(rule)
                layout.warnings.append(f"{script} sets the test sources to {rule[1]}; read "
                                       "syntactically and applied to every Gradle module")
    for module in layout.modules:
        roots = ["src/test/java"]
        for replace, dirs in shared + own.get(module, []):
            dirs = [d.strip("/") for d in dirs]
            roots = dirs if replace else roots + [d for d in dirs if d not in roots]
        if roots != ["src/test/java"]:
            layout.test_roots[module] = [posixpath.join(module, root) + "/" for root in roots]


def _all(element: ElementTree.Element, *names: str) -> list[ElementTree.Element]:
    """Children along ``names`` ignoring the POM namespace."""
    current = [element]
    for name in names:
        current = [c for e in current for c in e if _local(c.tag) == name]
    return current


def _child_text(element: ElementTree.Element, name: str) -> str | None:
    return next((c.text for c in element if _local(c.tag) == name), None)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
