"""Build the code graph of the Python files of one commit (shared schema, D-018).

All ``.py`` files are read from Git's object store (nothing is checked out,
imported or run) and parsed with ``ast``. The graph has:

* ``package:py:<package>`` → ``file:<path>`` → ``type:py:<module>`` (kind
  ``module``) → classes → ``member:`` functions and methods (``contains``);
* ``imports`` edges from a module to the repository modules it imports,
  ``uses`` edges to the classes it imports by name, and ``extends`` edges
  from a class to its base classes;
* a ``uses`` edge from every module to each class it defines, so a changed
  class also reaches the modules that import its module (conservative).

Name resolution (D-060):

* confirmed: an import naming a repository module exactly (relative imports
  are resolved against the importing package first); a base class defined
  in the same module or imported by name from a repository module;
* heuristic: an import matching exactly one repository module only as a
  dotted suffix (the repository's source root is not ``src/`` or the root),
  or one of several modules with that name; a base class matched only by a
  unique class name in the repository;
* external: standard-library and other imports not in the repository;
  counted, not turned into edges;
* unresolved: kept in ``unresolved`` (a relative import above the top-level
  package, a base class name that matches several classes or none).

Dynamic imports (``importlib``), ``sys.path`` changes, re-exports through
``__init__`` and attribute access on imported modules are not followed.
"""

from __future__ import annotations

import builtins
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from codedna.dependency_graph.model import (
    CONFIRMED,
    HEURISTIC,
    CodeGraph,
    Evidence,
    Node,
    UnresolvedReference,
)
from codedna.git_analysis.blobs import list_files, read_blobs
from codedna_python.parser import CLASS, MODULE, PythonParseResult, parse_python

_BUILTINS = frozenset(dir(builtins))
_STDLIB = frozenset(sys.stdlib_module_names)


def file_role(path: str) -> str:
    """"test" for pytest-style test files, conftest.py and files under a tests/ folder."""
    pure = PurePosixPath(path)
    if pure.name == "conftest.py" or pure.name.startswith("test_") or pure.stem.endswith("_test") \
            or any(part in ("test", "tests") for part in pure.parts[:-1]):
        return "test"
    return "main"


def parse_commit(repo: Path, commit: str, cache: dict | None) -> dict[str, PythonParseResult]:
    """Parses of every ``.py`` file of ``commit``, by path.

    Cache keys are ``("py", blob SHA, path)``: tuples, so they never collide
    with another plugin's keys in a shared cache, and with the path, because
    declaration IDs depend on it.
    """
    cache = {} if cache is None else cache
    files = list_files(repo, commit, ".py")
    parsed: dict[str, PythonParseResult] = {}
    missing = []
    for path, blob in files:
        key = ("py", blob, path)
        if key in cache:
            parsed[path] = cache[key]
        else:
            missing.append((path, blob))
    if missing:
        contents = read_blobs(repo, sorted({blob for _, blob in missing}))
        for path, blob in missing:
            parsed[path] = cache[("py", blob, path)] = parse_python(contents[blob], path)
    return parsed


def build_graph_for_commit(repo: Path, commit: str, *, include_members: bool = True,
                           cache: dict | None = None) -> CodeGraph:
    graph = CodeGraph(repository=str(repo), commit=commit)
    parsed = parse_commit(repo, commit, cache)
    _add_structure(graph, parsed, include_members)
    _Resolver(graph, parsed).add_dependency_edges()
    return graph


def _add_structure(graph: CodeGraph, parsed: dict[str, PythonParseResult],
                   include_members: bool) -> None:
    owners: dict[str, list[str]] = {}
    for path in sorted(parsed):
        result = parsed[path]
        package = "py:" + result.module.rpartition(".")[0]
        package_id = f"package:{package}"
        graph.add_node(Node(id=package_id, kind="package",
                            label=package.removeprefix("py:") or "(top level)", package=package))
        role = file_role(path)
        file_id = f"file:{path}"
        graph.add_node(Node(id=file_id, kind="file", label=PurePosixPath(path).name, file=path,
                            lines=[1, max(result.line_count, 1)], package=package,
                            parent=package_id, role=role,
                            has_syntax_errors=result.has_syntax_errors))
        graph.add_edge(package_id, file_id, "contains")
        module_id = f"type:{result.module_id}"
        owners.setdefault(module_id, []).append(path)
        if module_id in graph.nodes:
            continue  # same module name from two paths (src/x.py and x.py); reported below
        graph.add_node(Node(id=module_id, kind=MODULE, label=result.module.rpartition(".")[2],
                            file=path, lines=[1, max(result.line_count, 1)], package=package,
                            parent=file_id, role=role,
                            has_syntax_errors=result.has_syntax_errors))
        graph.add_edge(file_id, module_id, "contains")
        if result.has_syntax_errors:
            graph.warnings.append(f"{result.error} in {path}; its declarations and imports are "
                                  "not in the graph")
        for declaration in result.declarations:
            is_type = declaration.kind == CLASS
            if not is_type and not include_members:
                continue
            node_id = f"{'type' if is_type else 'member'}:{declaration.id}"
            if node_id in graph.nodes:
                continue  # redefined name (property setter, conditional definition)
            graph.add_node(Node(id=node_id, kind=declaration.kind, label=declaration.name,
                                file=path, lines=[declaration.start_line, declaration.end_line],
                                package=package, parent=f"type:{declaration.parent}",
                                role=role if is_type else None))
            graph.add_edge(f"type:{declaration.parent}", node_id, "contains")
            if is_type:
                # The module runs the class statement: importers of the module reach the class.
                graph.add_edge(module_id, node_id, "uses", Evidence(
                    path, declaration.start_line, CONFIRMED, "class defined in this module"))
    for module_id, paths in sorted(owners.items()):
        if len(paths) > 1:
            graph.warnings.append(f"module {module_id.removeprefix('type:py:')} comes from "
                                  f"{len(paths)} files ({', '.join(paths)}); only {paths[0]} "
                                  "is in the graph")


@dataclass
class _Bindings:
    """What the names a module imports refer to."""

    classes: dict[str, tuple[str, str]] = field(default_factory=dict)  # name -> (class ID, conf.)
    modules: dict[str, str] = field(default_factory=dict)  # name -> dotted module name
    external: set[str] = field(default_factory=set)  # names imported from outside the repository


class _Resolver:
    def __init__(self, graph: CodeGraph, parsed: dict[str, PythonParseResult]):
        self.graph = graph
        self.parsed = {path: result for path, result in parsed.items()
                       if not result.has_syntax_errors}
        self.modules = {r.module for r in parsed.values()}
        self.classes: dict[str, set[str]] = {}  # module -> its class IDs
        self.by_simple_name: dict[str, list[str]] = {}
        for result in self.parsed.values():
            for declaration in result.declarations:
                if declaration.kind == CLASS:
                    self.classes.setdefault(result.module, set()).add(declaration.id)
                    self.by_simple_name.setdefault(declaration.name, []).append(declaration.id)

    def add_dependency_edges(self) -> None:
        for path in sorted(self.parsed):
            result = self.parsed[path]
            source = f"type:{result.module_id}"
            if self.graph.nodes.get(source, Node("", "", "")).file != path:
                continue  # a duplicate module name; only the first file is in the graph
            self._add_bases(path, result, self._add_imports(path, result, source))

    # imports -----------------------------------------------------------------

    def _add_imports(self, path: str, result: PythonParseResult, source: str) -> "_Bindings":
        """Edges for every import; returns what the imported names refer to."""
        bound = _Bindings()
        for fact in result.imports:
            if fact.module is None:
                self._unresolved(source, fact.written, path, fact.line,
                                 reason="relative import above the top-level package")
                continue
            if not fact.names:  # import a.b.c [as x]
                bound.modules[fact.alias or fact.module.split(".", 1)[0]] = \
                    fact.module if fact.alias else fact.module.split(".", 1)[0]
                self._import_module(source, fact.module, path, fact.line, fact.written)
                continue
            target, confidence, note = self._resolve_module(fact.module)
            external = target is None and self._is_external(fact.module)
            for name in fact.names:
                if name == "*":
                    continue
                if external:
                    bound.external.add(name)
                    continue
                if target is not None and f"{target}.{name}" in self.modules:  # a submodule
                    bound.modules[name] = f"{target}.{name}"
                    self._edge(source, f"type:py:{target}.{name}", "imports", path, fact.line,
                               confidence, f"from {fact.written} import {name}" + note)
                    continue
                class_id = f"py:{target}.{name}" if target is not None else None
                if class_id in self.classes.get(target, ()):
                    self._edge(source, f"type:{class_id}", "uses", path, fact.line, confidence,
                               f"from {fact.written} import {name}" + note)
                    bound.classes[name] = (class_id, confidence)
            if target is not None:
                self._edge(source, f"type:py:{target}", "imports", path, fact.line, confidence,
                           f"from {fact.written} import ..." + note)
            elif external:
                self.graph.external_reference_count += 1
            else:
                self._unresolved(source, fact.written, path, fact.line, "")
        return bound

    def _import_module(self, source: str, module: str, path: str, line: int, written: str) -> None:
        target, confidence, note = self._resolve_module(module)
        if target is not None:
            self._edge(source, f"type:py:{target}", "imports", path, line, confidence,
                       f"import {written}" + note)
        elif self._is_external(module):
            self.graph.external_reference_count += 1
        else:
            self._unresolved(source, written, path, line, "")

    def _resolve_module(self, name: str) -> tuple[str | None, str, str]:
        """(repository module, confidence, note) for an absolute dotted module name."""
        if name in self.modules:
            return name, CONFIRMED, ""
        if self._is_external(name):
            return None, CONFIRMED, ""
        suffix = sorted(m for m in self.modules if m.endswith("." + name))
        if len(suffix) == 1:
            return suffix[0], HEURISTIC, f" (matched as {suffix[0]})"
        if suffix:
            return suffix[0], HEURISTIC, (f" (one of {len(suffix)} modules named like this: "
                                          f"{', '.join(suffix[:3])})")
        return None, CONFIRMED, ""

    def _is_external(self, name: str) -> bool:
        """Standard library, or a top-level name that no repository module path contains."""
        top = name.split(".", 1)[0]
        if top in _STDLIB and top not in self.modules:
            return True
        return not any(f".{top}." in f".{m}." for m in self.modules)

    # class bases ---------------------------------------------------------------

    def _add_bases(self, path: str, result: PythonParseResult, bound: "_Bindings") -> None:
        local = {d.name: d.id for d in result.declarations
                 if d.kind == CLASS and d.parent == result.module_id}
        for base in result.bases:
            source = f"type:{base.class_id}"
            if base.name is None:
                self._unresolved(source, "(expression)", path, base.line,
                                 reason="base class is not a plain name")
                continue
            head, _, rest = base.name.partition(".")
            if not rest:
                if head in local and local[head] != base.class_id:
                    self._edge(source, f"type:{local[head]}", "extends", path, base.line,
                               CONFIRMED, "defined in this module")
                elif head in bound.classes:
                    class_id, confidence = bound.classes[head]
                    self._edge(source, f"type:{class_id}", "extends", path, base.line,
                               confidence, "imported by name")
                elif head in bound.external or head in _BUILTINS:
                    self.graph.external_reference_count += 1
                else:
                    self._by_simple_name(source, base.name, path, base.line)
                continue
            if head in bound.modules:
                middle, _, name = rest.rpartition(".")
                module = bound.modules[head] + (f".{middle}" if middle else "")
                target, confidence, note = self._resolve_module(module)
                class_id = f"py:{target}.{name}" if target is not None else None
                if class_id in self.classes.get(target, ()):
                    self._edge(source, f"type:{class_id}", "extends", path, base.line,
                               confidence, f"{base.name} through import" + note)
                elif target is None and self._is_external(module):
                    self.graph.external_reference_count += 1
                else:
                    self._unresolved(source, base.name, path, base.line, "")
            elif head in bound.external:
                self.graph.external_reference_count += 1
            else:
                self._by_simple_name(source, base.name, path, base.line)

    def _by_simple_name(self, source: str, name: str, path: str, line: int) -> None:
        matches = self.by_simple_name.get(name.rpartition(".")[2], [])
        if len(matches) == 1 and f"type:{matches[0]}" != source:
            self._edge(source, f"type:{matches[0]}", "extends", path, line, HEURISTIC,
                       "the only class with this name in the repository")
        else:
            self._unresolved(source, name, path, line,
                             f" ({len(matches)} classes with this name)" if matches else "")

    # helpers -------------------------------------------------------------------

    def _edge(self, source: str, target: str, kind: str, path: str, line: int,
              confidence: str, note: str) -> None:
        if target == source or target not in self.graph.nodes:
            return
        self.graph.add_edge(source, target, kind, Evidence(path, line, confidence, note))

    def _unresolved(self, source: str, name: str, path: str, line: int, note: str = "",
                    reason: str = "not found in the repository") -> None:
        self.graph.add_unresolved(UnresolvedReference(source, name, path, line, reason + note))
