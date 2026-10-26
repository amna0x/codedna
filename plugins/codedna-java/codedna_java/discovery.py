"""Static discovery of JUnit 3/4/5 test classes in one commit.

A *test class* is a top-level, non-abstract class that has test methods
(annotated ``@Test``, ``@ParameterizedTest``, ``@RepeatedTest``,
``@TestFactory`` or ``@TestTemplate``), either declared directly, in
``@Nested`` inner classes, or inherited from a test base class found through
the dependency graph's ``extends`` edges.

JUnit 3 style (D-064): in a class that extends ``junit.framework.TestCase``,
or a repository base class annotated ``@TestMethodProviders`` with a JUnit 3
method provider (randomizedtesting, used by Lucene), directly or through
repository ancestors, every ``public void test*()`` method with no
parameters is a test method too, as JUnit 3 and Surefire run them.

Discovery is syntactic. It also reports whether the build would run the class
by default, from the static build layout (``build.py``): Maven modules with
Surefire's default or the module's own ``<includes>``, or every class in a
Gradle module's ``src/test/java``. Without a build file it falls back to
Surefire's default name patterns.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath

from tree_sitter import Node, Parser

from codedna_java.builder import build_graph_for_commit
from codedna.git_analysis.blobs import list_files, read_blobs
from codedna.git_analysis.git import resolve_commit, resolve_repository
from codedna_java.parser import _LANGUAGE, TYPE_NODES
from codedna_java.build import detect_build

TEST_ANNOTATIONS = frozenset({
    "Test", "ParameterizedTest", "RepeatedTest", "TestFactory", "TestTemplate",
})
_BODY_NODES = frozenset({"class_body", "enum_body_declarations"})


@dataclass
class DiscoveredTest:
    id: str  # fully qualified top-level class name, same as the graph's type ID
    file: str
    framework: str  # "junit5" | "junit4" | "unknown"
    methods: list[str]  # "method" or "Nested.method"; inherited ones as "Base#method"
    inherited_from: list[str] = field(default_factory=list)
    in_test_sources: bool = False
    matches_surefire_defaults: bool = False
    module: str | None = None  # build module directory ("" = root), None if unknown
    selected_by_build: bool | None = None  # from the detected build layout, if any

    @property
    def runs_by_default(self) -> bool:
        if self.selected_by_build is not None:
            return self.selected_by_build
        return self.in_test_sources and self.matches_surefire_defaults


@dataclass
class DiscoveryReport:
    repository: str
    commit: str
    tests: list[DiscoveredTest]
    warnings: list[str]
    build_tool: str | None = None

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
class _TypeInfo:
    id: str
    file: str
    top_level: str
    is_abstract: bool
    is_class: bool
    nested_annotation: bool
    test_methods: list[str]
    junit3_methods: list[str] = field(default_factory=list)  # public void test*() candidates
    junit3_root: bool = False  # extends junit.framework.TestCase or declares a JUnit 3 provider


def discover_tests(repo_path: str | Path, revision: str = "HEAD") -> DiscoveryReport:
    repo = resolve_repository(repo_path)
    commit = resolve_commit(repo, revision)
    return discover_tests_for_commit(repo, commit)


def discover_tests_for_commit(repo: Path, commit: str, *, cache: dict | None = None) -> DiscoveryReport:
    """``cache``: optional parse cache keyed by blob SHA, shared with graph builds."""
    files = list_files(repo, commit, ".java")
    contents = read_blobs(repo, sorted({blob for _, blob in files}))
    types: dict[str, _TypeInfo] = {}
    frameworks: dict[str, str] = {}
    warnings: list[str] = []
    for path, blob in files:
        framework, file_types = _scan_file(path, contents[blob])
        frameworks[path] = framework
        if framework == "testng":
            warnings.append(f"{path}: TestNG is not supported; tests in this file are ignored")
            continue
        for info in file_types:
            types.setdefault(info.id, info)

    layout = detect_build(repo, commit)
    if layout.tool:
        warnings.extend(layout.warnings)
    superclasses = _superclasses(repo, commit, cache)
    tests: list[DiscoveredTest] = []
    for info in types.values():
        if info.id != info.top_level or not info.is_class or info.is_abstract:
            continue
        ancestors = _ancestors(info.id, superclasses)
        junit3 = info.junit3_root or any(
            types[base].junit3_root for base in ancestors if base in types)
        methods = list(info.test_methods)
        if junit3:
            methods.extend(m for m in info.junit3_methods if m not in methods)
        # @Nested inner classes run as part of their top-level class.
        for nested in types.values():
            if nested.top_level == info.id and nested.id != info.id and nested.nested_annotation:
                prefix = nested.id.removeprefix(f"{info.id}.")
                methods.extend(f"{prefix}.{m}" for m in nested.test_methods)
        inherited_from = []
        for base in ancestors:
            base_info = types.get(base)
            if base_info is None:
                continue
            base_methods = list(base_info.test_methods)
            if junit3:
                base_methods.extend(m for m in base_info.junit3_methods if m not in base_methods)
            if base_methods:
                inherited_from.append(base)
                methods.extend(f"{base}#{m}" for m in base_methods)
        if not methods:
            continue
        name = PurePosixPath(info.file).stem
        tests.append(DiscoveredTest(
            id=info.id, file=info.file,
            framework=_framework(frameworks.get(info.file, "unknown"), junit3, info.test_methods),
            methods=methods, inherited_from=inherited_from,
            in_test_sources="/src/test/java/" in f"/{info.file}"
            or bool(layout.tool and layout.module_of(info.file) is not None),
            matches_surefire_defaults=name.startswith("Test")
            or name.endswith(("Test", "Tests", "TestCase")),
            module=layout.module_of(info.file) if layout.tool else None,
            selected_by_build=layout.runs_by_default(info.file) if layout.tool else None,
        ))
        if not tests[-1].runs_by_default:
            warnings.append(f"{info.id}: not selected by the build's test includes; "
                            "it only runs if the project configures it")
    return DiscoveryReport(str(repo), commit, sorted(tests, key=lambda t: t.id), warnings,
                           layout.tool)


def _superclasses(repo: Path, commit: str, cache: dict | None = None) -> dict[str, list[str]]:
    graph = build_graph_for_commit(repo, commit, include_members=False, cache=cache)
    parents: dict[str, list[str]] = {}
    for edge in graph.edges.values():
        if edge.kind == "extends":
            parents.setdefault(edge.source.removeprefix("type:"), []).append(
                edge.target.removeprefix("type:"))
    return parents


def _ancestors(type_id: str, superclasses: dict[str, list[str]]) -> list[str]:
    seen: list[str] = []
    pending = list(superclasses.get(type_id, []))
    while pending:
        current = pending.pop(0)
        if current in seen or current == type_id:
            continue
        seen.append(current)
        pending.extend(superclasses.get(current, []))
    return seen


def _scan_file(path: str, source: bytes) -> tuple[str, list[_TypeInfo]]:
    root = Parser(_LANGUAGE).parse(source).root_node
    package = None
    framework = "unknown"
    junit3_imports = set()  # "TestCase" (single import) or "*" (junit.framework.*)
    for child in root.children:
        if child.type == "package_declaration":
            package = "".join(_text(child).removeprefix("package").rstrip(";").split())
        elif child.type == "import_declaration":
            text = _text(child)
            imported = "".join(text.removeprefix("import").rstrip(";").split())
            if imported == "junit.framework.TestCase":
                junit3_imports.add("TestCase")
            elif imported == "junit.framework.*":
                junit3_imports.add("*")
            if "org.junit.jupiter" in text:
                framework = "junit5"
            elif "org.junit." in text and framework == "unknown":
                framework = "junit4"
            elif "org.testng" in text:
                framework = "testng"

    found: list[_TypeInfo] = []

    def visit(node: Node, parent_id: str | None, top_level: str | None) -> None:
        name = _text(node.child_by_field_name("name"))
        type_id = f"{parent_id}.{name}" if parent_id else (f"{package}.{name}" if package else name)
        annotations, modifiers = _modifiers(node)
        info = _TypeInfo(
            id=type_id, file=path, top_level=top_level or type_id,
            is_abstract="abstract" in modifiers, is_class=node.type == "class_declaration",
            nested_annotation="Nested" in annotations, test_methods=[],
            junit3_root=_extends_junit3(node, junit3_imports) or _junit3_provider(node),
        )
        found.append(info)
        body = node.child_by_field_name("body")
        for member in body.children if body is not None else ():
            if member.type == "method_declaration":
                method_annotations, method_modifiers = _modifiers(member)
                method_name = _text(member.child_by_field_name("name"))
                if method_annotations & TEST_ANNOTATIONS:
                    info.test_methods.append(method_name)
                elif _junit3_candidate(member, method_name, method_modifiers):
                    info.junit3_methods.append(method_name)
            elif member.type in TYPE_NODES:
                visit(member, type_id, info.top_level)

    for child in root.children:
        if child.type in TYPE_NODES:
            visit(child, None, None)
    return framework, found


def _framework(file_framework: str, junit3: bool, annotated: list[str]) -> str:
    if junit3 and file_framework == "unknown" and not annotated:
        return "junit3"
    return file_framework


def _extends_junit3(node: Node, junit3_imports: set[str]) -> bool:
    """Does this class directly extend ``junit.framework.TestCase``?"""
    superclass = node.child_by_field_name("superclass")
    if node.type != "class_declaration" or superclass is None:
        return False
    name = "".join(_text(superclass).removeprefix("extends").split()).split("<", 1)[0]
    return name == "junit.framework.TestCase" or (name == "TestCase" and bool(junit3_imports))


def _junit3_provider(node: Node) -> bool:
    """``@TestMethodProviders({...JUnit3MethodProvider...})`` (randomizedtesting)."""
    for child in node.children:
        if child.type != "modifiers":
            continue
        for item in child.children:
            if (item.type == "annotation"
                    and _text(item.child_by_field_name("name")).rsplit(".", 1)[-1] == "TestMethodProviders"
                    and "JUnit3MethodProvider" in _text(item.child_by_field_name("arguments"))):
                return True
    return False


def _junit3_candidate(method: Node, name: str, modifiers: set[str]) -> bool:
    """JUnit 3 test method shape: ``public void test*()``, not static or abstract."""
    parameters = method.child_by_field_name("parameters")
    return (name.startswith("test") and "public" in modifiers
            and not modifiers & {"static", "abstract"}
            and _text(method.child_by_field_name("type")) == "void"
            and parameters is not None and parameters.named_child_count == 0)


def _modifiers(node: Node) -> tuple[set[str], set[str]]:
    """Return (annotation simple names, keyword modifiers) of a declaration."""
    annotations: set[str] = set()
    keywords: set[str] = set()
    for child in node.children:
        if child.type != "modifiers":
            continue
        for item in child.children:
            if item.type in ("marker_annotation", "annotation"):
                annotations.add(_text(item.child_by_field_name("name")).rsplit(".", 1)[-1])
            else:
                keywords.add(_text(item))
    return annotations, keywords


def _text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8", errors="replace")
