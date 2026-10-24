"""Static build layout of one commit: Maven (single or multi-module) or Gradle.

Read from committed build files only; no build tool runs here. Maven modules
come from ``<modules>`` (followed recursively); custom Surefire ``<includes>``
and ``<excludes>`` come from each module's own ``pom.xml`` (inherited parent
configuration and profiles are not resolved; modules listed only inside
profiles are reported, not followed). Gradle modules come from ``include`` lines in
``settings.gradle(.kts)`` (a syntactic reading, recorded as such); Gradle runs
every class in the ``test`` source set by default, so no name filter applies.
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


@dataclass
class BuildLayout:
    tool: str | None  # "maven" | "gradle" | None
    modules: list[str]  # module directories relative to the root; "" is the root
    includes: dict[str, list[str]] = field(default_factory=dict)  # module → Surefire includes
    excludes: dict[str, list[str]] = field(default_factory=dict)  # module → Surefire excludes
    warnings: list[str] = field(default_factory=list)

    def module_of(self, path: str) -> str | None:
        """Deepest module whose ``src/test/java`` contains ``path``."""
        best = None
        for module in self.modules:
            root = f"{module}/src/test/java/" if module else "src/test/java/"
            if path.startswith(root) and (best is None or len(module) > len(best)):
                best = module
        return best

    def runs_by_default(self, path: str) -> bool:
        """Would the build tool run this test file without extra configuration?"""
        module = self.module_of(path)
        if module is None:
            return False
        if self.tool == "gradle":
            return True
        root = f"{module}/src/test/java/" if module else "src/test/java/"
        relative = path.removeprefix(root)
        patterns = self.includes.get(module) or SUREFIRE_DEFAULTS
        return (any(_matches(relative, p) for p in patterns)
                and not any(_matches(relative, p) for p in self.excludes.get(module, ())))


def _matches(relative: str, pattern: str) -> bool:
    """Surefire include pattern; "**/Name*.java" matches the file name at any depth."""
    pattern = pattern.strip().lstrip("/")
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
    return layout


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
