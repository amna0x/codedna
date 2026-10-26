"""Build the code graph of one commit.

All ``.java`` files of the commit are read straight from Git's object store
(``git ls-tree`` + ``git cat-file --batch``): nothing is checked out, built or
executed. Each file is parsed twice with Tree-sitter — once for declarations
(``java_analysis.parser``) and once for type references (``references``) —
and then every reference is resolved against the types declared in the
repository.

Name resolution follows a simplified version of Java's rules (JLS §6.4/§7.5);
see docs/DECISIONS.md D-010 for exactly what is and is not handled.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from codedna.dependency_graph.model import (
    CONFIRMED,
    HEURISTIC,
    CodeGraph,
    Evidence,
    Node,
    UnresolvedReference,
)
from codedna.dependency_graph.references import FileFacts, extract_references
from codedna.git_analysis.blobs import list_files, read_blobs
from codedna.git_analysis.git import resolve_commit, resolve_repository
from codedna.java_analysis.parser import TYPE_NODES, JavaParseResult, parse_java

_TYPE_KINDS = frozenset(TYPE_NODES.values())

# java.lang is imported implicitly into every compilation unit, so these
# names refer to the JDK unless a repository type shadows them (checked first).
# The public top-level types of java.lang in JDK 21.
_JAVA_LANG = frozenset({
    "AbstractMethodError", "Appendable", "ArithmeticException", "ArrayIndexOutOfBoundsException",
    "ArrayStoreException", "AssertionError", "AutoCloseable", "Boolean", "BootstrapMethodError",
    "Byte", "CharSequence", "Character", "Class", "ClassCastException", "ClassCircularityError",
    "ClassFormatError", "ClassLoader", "ClassNotFoundException", "ClassValue",
    "CloneNotSupportedException", "Cloneable", "Comparable", "Deprecated", "Double", "Enum",
    "EnumConstantNotPresentException", "Error", "Exception", "ExceptionInInitializerError",
    "Float", "FunctionalInterface", "IllegalAccessError", "IllegalAccessException",
    "IllegalArgumentException", "IllegalCallerException", "IllegalMonitorStateException",
    "IllegalStateException", "IllegalThreadStateException", "IncompatibleClassChangeError",
    "IndexOutOfBoundsException", "InheritableThreadLocal", "InstantiationError",
    "InstantiationException", "Integer", "InternalError", "InterruptedException", "Iterable",
    "LayerInstantiationException", "LinkageError", "Long", "MatchException", "Math", "Module",
    "ModuleLayer", "NegativeArraySizeException", "NoClassDefFoundError", "NoSuchFieldError",
    "NoSuchFieldException", "NoSuchMethodError", "NoSuchMethodException", "NullPointerException",
    "Number", "NumberFormatException", "Object", "OutOfMemoryError", "Override", "Package",
    "Process", "ProcessBuilder", "ProcessHandle", "Readable", "Record",
    "ReflectiveOperationException", "Runnable", "Runtime", "RuntimeException", "RuntimePermission",
    "SafeVarargs", "ScopedValue", "SecurityException", "SecurityManager", "Short",
    "StackOverflowError", "StackTraceElement", "StackWalker", "StrictMath", "String",
    "StringBuffer", "StringBuilder", "StringIndexOutOfBoundsException", "StringTemplate",
    "SuppressWarnings", "System", "Thread", "ThreadDeath", "ThreadGroup", "ThreadLocal",
    "Throwable", "TypeNotPresentException", "UnknownError", "UnsatisfiedLinkError",
    "UnsupportedClassVersionError", "UnsupportedOperationException", "VerifyError",
    "VirtualMachineError", "Void", "WrongThreadException",
})
# Added after Java 8. On an older JDK a wildcard-imported repository type with
# the same name is what the code means, so those names are not taken as
# java.lang when such a type exists (the edge is then heuristic).
_JAVA_LANG_SINCE_9 = frozenset({
    "IllegalCallerException", "LayerInstantiationException", "MatchException", "Module",
    "ModuleLayer", "ProcessHandle", "Record", "ScopedValue", "StackWalker", "StringTemplate",
    "WrongThreadException",
})

# Parsed files keyed by Git blob SHA, so identical files in two commits are
# parsed only once.
ParseCache = dict[str, tuple[JavaParseResult, FileFacts]]


@dataclass
class _Resolution:
    status: str  # "repo" | "external" | "unresolved" | "skip"
    target: str | None = None
    confidence: str = CONFIRMED
    note: str = ""


def build_graph(repo_path: str | Path, revision: str, *, include_members: bool = True,
                cache: ParseCache | None = None) -> CodeGraph:
    """Build the code graph for ``revision`` of the repository at ``repo_path``."""
    repo = resolve_repository(repo_path)
    commit = resolve_commit(repo, revision)
    return build_graph_for_commit(repo, commit, include_members=include_members, cache=cache)


def build_graph_for_commit(repo: Path, commit: str, *, include_members: bool = True,
                           cache: ParseCache | None = None) -> CodeGraph:
    cache = {} if cache is None else cache
    files = list_files(repo, commit, ".java")
    by_blob = _parse_missing(repo, files, cache)

    graph = CodeGraph(repository=str(repo), commit=commit)
    parsed = {path: by_blob[blob] for path, blob in files}
    _add_structure(graph, parsed, include_members)
    _Resolver(graph, parsed).add_dependency_edges()
    return graph


# --- reading files from Git ---------------------------------------------------


def _parse_missing(repo: Path, files: list[tuple[str, str]],
                   cache: ParseCache) -> dict[str, tuple[JavaParseResult, FileFacts]]:
    """Parses for every blob of ``files``: from ``cache`` when present, else parsed now.

    The result is returned directly, so a bounded cache evicting entries
    while new ones are added cannot make this commit's lookups fail.
    """
    needed = sorted({blob for _, blob in files})
    result = {blob: cache[blob] for blob in needed if blob in cache}
    missing = [blob for blob in needed if blob not in result]
    if missing:
        contents = read_blobs(repo, missing)
        for blob in missing:
            source = contents[blob]
            result[blob] = cache[blob] = (parse_java(source), extract_references(source))
    return result


class BoundedParseCache(OrderedDict):
    """Least-recently-used parse cache shared across many commits.

    Consecutive commits share almost all files, so reusing parses by blob SHA
    avoids re-parsing the whole repository for every commit; the bound keeps
    memory flat on long histories.
    """

    def __init__(self, max_entries: int = 4000):
        super().__init__()
        self.max_entries = max_entries

    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.move_to_end(key)
        while len(self) > self.max_entries:
            self.popitem(last=False)


# --- structural nodes and "contains" edges ------------------------------------


def file_role(path: str) -> str:
    """Classify a file as test or main code by Maven/JUnit path conventions."""
    pure = PurePosixPath(path)
    if "src/test/" in f"/{path}" or pure.stem.endswith(("Test", "Tests", "IT", "TestCase")) \
            or pure.stem.startswith("Test"):
        return "test"
    return "main"


def _add_structure(graph: CodeGraph, parsed: dict[str, tuple[JavaParseResult, FileFacts]],
                   include_members: bool) -> None:
    declared_in: dict[str, list[str]] = {}
    for path, (result, _facts) in parsed.items():
        package = result.package or ""
        package_id = f"package:{package}"
        graph.add_node(Node(id=package_id, kind="package",
                            label=package or "(default package)", package=package))
        file_id = f"file:{path}"
        role = file_role(path)
        graph.add_node(Node(
            id=file_id, kind="file", label=PurePosixPath(path).name, file=path,
            lines=[1, result.line_count], package=package, parent=package_id, role=role,
            has_syntax_errors=result.has_syntax_errors,
        ))
        graph.add_edge(package_id, file_id, "contains")
        if result.has_syntax_errors:
            graph.warnings.append(
                f"syntax errors in {path} (lines {result.syntax_errors[:5]}); "
                "its edges are marked heuristic")

        for declaration in result.declarations:
            is_type = declaration.kind in _TYPE_KINDS
            if not is_type and not include_members:
                continue
            node_id = f"{'type' if is_type else 'member'}:{declaration.id}"
            parent_id = f"type:{declaration.parent}" if declaration.parent else file_id
            if is_type:
                declared_in.setdefault(declaration.id, []).append(path)
                if node_id in graph.nodes:
                    continue  # duplicate FQN; reported below
            graph.add_node(Node(
                id=node_id, kind=declaration.kind, label=declaration.name, file=path,
                lines=[declaration.start_line, declaration.end_line], package=package,
                parent=parent_id, role=role if is_type else None,
            ))
            graph.add_edge(parent_id, node_id, "contains")

    for type_id, paths in sorted(declared_in.items()):
        if len(paths) > 1:
            graph.warnings.append(
                f"type {type_id} is declared in {len(paths)} files ({', '.join(paths)}); "
                "references to it are marked heuristic")


# --- resolving references into dependency edges -------------------------------


class _Resolver:
    def __init__(self, graph: CodeGraph, parsed: dict[str, tuple[JavaParseResult, FileFacts]]):
        self.graph = graph
        self.parsed = parsed
        self.all_types: dict[str, list[str]] = {}  # type ID -> files declaring it
        self.top_level: set[str] = set()
        self.packages: set[str] = set()
        for path, (result, _facts) in parsed.items():
            self.packages.add(result.package or "")
            for declaration in result.declarations:
                if declaration.kind in _TYPE_KINDS:
                    self.all_types.setdefault(declaration.id, []).append(path)
                    if declaration.parent is None:
                        self.top_level.add(declaration.id)
        # Names written after `extends` / `implements`, per declaring type.
        self.declared_supertypes: dict[str, list[tuple[str, str]]] = {}
        for path, (_result, facts) in parsed.items():
            for reference in facts.references:
                if reference.kind in ("extends", "implements"):
                    self.declared_supertypes.setdefault(reference.owner, []).append(
                        (path, reference.name))
        self.contexts: dict[str, _FileContext] = {}
        self.supertype_cache: dict[str, list[str]] = {}
        self._resolving: set[str] = set()

    def add_dependency_edges(self) -> None:
        for path, (result, facts) in self.parsed.items():
            context = self._context(path)
            self._add_import_edges(context)
            for reference in facts.references:
                self._add_reference(context, reference.owner, reference.name,
                                    reference.line, reference.kind)

    # Import declarations ------------------------------------------------------

    def _add_import_edges(self, context: _FileContext) -> None:
        top_types = [d.id for d in context.result.declarations
                     if d.kind in _TYPE_KINDS and d.parent is None]
        for imported in context.facts.imports:
            if imported.wildcard and not imported.static:
                continue  # `import a.b.*` names a package, used only for resolution
            # `import static a.Y.z` and `import static a.Y.*` both depend on type a.Y.
            type_name = imported.name.rsplit(".", 1)[0] if imported.static and not imported.wildcard \
                else imported.name
            if type_name not in self.all_types:
                self.graph.external_reference_count += 1
                continue
            confidence = self._confidence_for(type_name, context, CONFIRMED)
            for owner in top_types:
                if owner != type_name:
                    self.graph.add_edge(
                        f"type:{owner}", f"type:{type_name}", "imports",
                        Evidence(context.path, imported.line, confidence,
                                 "static import" if imported.static else "import"))

    # Type references -----------------------------------------------------------

    def _add_reference(self, context: _FileContext, owner: str, name: str, line: int,
                       kind: str) -> None:
        if kind == "static_access":
            resolution = self._resolve_simple(name, context, owner)
            if resolution.status != "repo" or resolution.target == owner:
                return  # probably a variable or external class; not evidence of anything
            confidence = HEURISTIC
            note = f"{name}.<member> assumed to be a static access on a type"
        else:
            resolution = self._resolve(name, context, owner)
            if resolution.status == "skip":
                return
            if resolution.status == "external":
                self.graph.external_reference_count += 1
                return
            if resolution.status == "unresolved":
                self.graph.add_unresolved(UnresolvedReference(
                    f"type:{owner}", name, context.path, line, resolution.note))
                return
            if resolution.target == owner:
                return
            confidence, note = resolution.confidence, resolution.note

        confidence = self._confidence_for(resolution.target, context, confidence)
        self.graph.add_edge(f"type:{owner}", f"type:{resolution.target}", kind,
                            Evidence(context.path, line, confidence, note))

    def _context(self, path: str) -> _FileContext:
        if path not in self.contexts:
            result, facts = self.parsed[path]
            self.contexts[path] = _FileContext(path, result, facts)
        return self.contexts[path]

    def _supertypes(self, type_id: str) -> list[str]:
        """Repository supertypes of ``type_id``, transitively, nearest first."""
        if type_id in self.supertype_cache:
            return self.supertype_cache[type_id]
        if type_id in self._resolving:
            return []  # a cycle (invalid code) or one being resolved further up
        self._resolving.add(type_id)
        found: list[str] = []
        for path, name in self.declared_supertypes.get(type_id, []):
            resolution = self._resolve(name.split("<", 1)[0], self._context(path), type_id)
            if resolution.status == "repo" and resolution.target not in found:
                found.append(resolution.target)
        for direct in list(found):
            found += [t for t in self._supertypes(direct) if t not in found]
        self._resolving.discard(type_id)
        self.supertype_cache[type_id] = found
        return found

    def _confidence_for(self, target: str, context: _FileContext, confidence: str) -> str:
        if len(self.all_types.get(target, ())) > 1 or context.result.has_syntax_errors:
            return HEURISTIC
        return confidence

    def _resolve(self, name: str, context: _FileContext, owner: str) -> _Resolution:
        if "." not in name:
            return self._resolve_simple(name, context, owner)
        if name in self.all_types:
            return _Resolution("repo", name, CONFIRMED, "fully qualified name")

        first, rest = name.split(".", 1)
        head = self._resolve_simple(first, context, owner)
        if head.status == "repo":
            candidate = f"{head.target}.{rest}"
            if candidate in self.all_types:
                return _Resolution("repo", candidate, head.confidence, head.note)
            return _Resolution("unresolved", note=f"member type {rest} not found in {head.target}")
        if head.status == "external":
            return head
        # A package-qualified name: external unless it points into a repository package.
        package = name.rsplit(".", 1)[0]
        if first[:1].islower() and not any(
                p == package or p.startswith(f"{package}.") or package.startswith(f"{p}.")
                for p in self.packages if p):
            return _Resolution("external")
        return _Resolution("unresolved", note="qualified name not declared in repository")

    def _resolve_simple(self, name: str, context: _FileContext, owner: str) -> _Resolution:
        if name in context.facts.type_parameters or name == "var":
            return _Resolution("skip")  # `var` infers a local variable's type; no type is named

        # 1. The type itself, enclosing types, and their member types.
        scope = owner
        while scope:
            if scope.rsplit(".", 1)[-1] == name and scope in self.all_types:
                return _Resolution("repo", scope, CONFIRMED, "enclosing type")
            member = f"{scope}.{name}"
            if member in self.all_types:
                return _Resolution("repo", member, CONFIRMED, "member type in scope")
            if scope in self.all_types:
                for supertype in self._supertypes(scope):
                    if f"{supertype}.{name}" in self.all_types:
                        # Hiding rules and library supertypes are not checked.
                        return _Resolution("repo", f"{supertype}.{name}", HEURISTIC,
                                           f"member type inherited from {supertype}")
            scope = scope.rsplit(".", 1)[0] if "." in scope else ""
            if scope == (context.package or ""):
                break  # reached the package; not a type

        # 2. Single-type imports, and single static imports naming a member type.
        imported = context.single_imports.get(name)
        if imported is not None:
            if imported in self.all_types:
                return _Resolution("repo", imported, CONFIRMED, "single-type import")
            return _Resolution("external")
        static_import = context.static_single_imports.get(name)
        if static_import is not None and static_import in self.all_types:
            return _Resolution("repo", static_import, CONFIRMED, "single static import")

        # 3. Top-level types of the same package (including this file).
        same_package = f"{context.package}.{name}" if context.package else name
        if same_package in self.top_level:
            if static_import is not None:
                # `import static lib.T.Name` shadows the package's type if it names a library
                # member type, but not if it names a static method or field.
                return _Resolution("repo", same_package, HEURISTIC,
                                   f"same package; static import {static_import} may shadow it")
            return _Resolution("repo", same_package, CONFIRMED, "same package")

        # 5. On-demand (wildcard) imports.
        # `import static a.T.*` also imports T's static member types.
        candidates = [f"{p}.{name}" for p in context.wildcard_imports + context.static_wildcards
                      if f"{p}.{name}" in self.all_types]

        # 4. java.lang (implicitly imported), checked before wildcards.
        if name in _JAVA_LANG:
            if name in _JAVA_LANG_SINCE_9 and len(candidates) == 1:
                return _Resolution("repo", candidates[0], HEURISTIC,
                                   f"wildcard import; java.lang.{name} exists only on Java 9+")
            return _Resolution("external")
        if len(candidates) == 1:
            return _Resolution("repo", candidates[0], HEURISTIC,
                               "wildcard import; assumes no same-named library type")
        if len(candidates) > 1:
            return _Resolution("unresolved", note=f"ambiguous wildcard imports: {candidates}")
        if context.wildcard_imports:
            return _Resolution(
                "unresolved",
                note="not declared in repository; may come from a wildcard-imported library")
        return _Resolution("unresolved", note="not declared in repository (likely JDK or library)")


class _FileContext:
    def __init__(self, path: str, result: JavaParseResult, facts: FileFacts):
        self.path = path
        self.result = result
        self.facts = facts
        self.package = result.package
        self.single_imports = {
            i.name.rsplit(".", 1)[-1]: i.name
            for i in facts.imports if not i.static and not i.wildcard
        }
        self.wildcard_imports = [i.name for i in facts.imports if i.wildcard and not i.static]
        self.static_wildcards = [i.name for i in facts.imports if i.wildcard and i.static]
        self.static_single_imports = {
            i.name.rsplit(".", 1)[-1]: i.name for i in facts.imports if i.static and not i.wildcard
        }
