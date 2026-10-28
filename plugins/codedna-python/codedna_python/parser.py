"""Parse one Python source file into declarations, imports and class bases.

Parsing uses the standard library's ``ast`` module of the interpreter that
runs CodeDNA (Python 3.11+): a file using newer syntax than that interpreter
knows is reported as a syntax error, never guessed at.

Declaration IDs (D-060) carry a ``py:`` prefix so they never collide with
Java's, and are built from the *module name*, which comes from the file path
(``module_name``):

* module    ``py:shop.orders``            (the file itself, kind ``module``)
* class     ``py:shop.orders.Order``      (nested: ``py:shop.orders.Order.Line``)
* function  ``py:shop.orders#total()``
* method    ``py:shop.orders.Order#add()``

Functions and classes are collected at module and class level, also inside
``if``/``try``/``with`` blocks there (conditional definitions). A function
defined inside another function belongs to the outer one. Python has no
overloading, so a name defined twice in one scope (a property getter and its
setter, say) is one declaration with several parts.
"""

from __future__ import annotations

from codedna.performance import timed

import ast
import copy
import io
import tokenize
from dataclasses import dataclass, field
from pathlib import PurePosixPath

MODULE, CLASS, FUNCTION, METHOD = "module", "class", "function", "method"
TYPE_KINDS = frozenset({MODULE, CLASS})

_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)


def module_name(path: str) -> str:
    """``src/shop/orders.py`` -> ``shop.orders``; ``shop/__init__.py`` -> ``shop``.

    A leading ``src/`` is dropped (the common "src layout"). A root
    ``__init__.py`` becomes ``__init__``.
    """
    parts = list(PurePosixPath(path).with_suffix("").parts)
    if len(parts) > 1 and parts[0] == "src":
        parts = parts[1:]
    if len(parts) > 1 and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def is_package_file(path: str) -> bool:
    return PurePosixPath(path).name == "__init__.py"


@dataclass
class Declaration:
    id: str
    kind: str  # class | function | method
    name: str
    parent: str  # enclosing class ID, or the module ID
    start_line: int  # first decorator line
    end_line: int
    tokens: str  # code without positions or comments (ast.dump), for "did code change?"
    # Classes only: (part, start, end) with part "decorator" | "header" | "body".
    parts: list[tuple[str, int, int]] = field(default_factory=list)


@dataclass
class ImportFact:
    line: int
    module: str | None  # absolute dotted name; None when a relative import leaves the root
    names: list[str]  # from-imports: imported names ("*" for a star import); [] for import
    alias: str | None  # ``import a.b as c`` -> "c"
    written: str  # as written, e.g. "..models" or "os.path"


@dataclass
class ClassBase:
    class_id: str
    name: str | None  # dotted name as written (``models.Base``); None if not a name
    line: int


@dataclass
class PythonParseResult:
    module: str
    module_id: str
    line_count: int
    declarations: list[Declaration] = field(default_factory=list)
    imports: list[ImportFact] = field(default_factory=list)
    bases: list[ClassBase] = field(default_factory=list)
    module_tokens: str = ""  # module-level code with definitions reduced to their names
    file_parts: list[tuple[str, int, int]] = field(default_factory=list)  # import/docstring/code
    blank_lines: set[int] = field(default_factory=set)
    syntax_errors: list[int] = field(default_factory=list)
    error: str | None = None  # why the file could not be parsed

    @property
    def has_syntax_errors(self) -> bool:
        return self.error is not None

    def by_id(self) -> dict[str, list[Declaration]]:
        grouped: dict[str, list[Declaration]] = {}
        for declaration in self.declarations:
            grouped.setdefault(declaration.id, []).append(declaration)
        return grouped


@timed('parse.python')
def parse_python(source: bytes, path: str = "module.py") -> PythonParseResult:
    """Parse ``source``, the contents of the repository file at ``path``."""
    module = module_name(path)
    text = _decode(source)
    lines = text.splitlines()
    result = PythonParseResult(module=module, module_id=f"py:{module}", line_count=len(lines),
                               blank_lines={i for i, line in enumerate(lines, 1)
                                            if not line.strip()})
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        result.syntax_errors = [exc.lineno or 1]
        result.error = f"Python syntax error near line {exc.lineno or 1}"
        return result
    except (ValueError, RecursionError, MemoryError) as exc:  # null bytes, absurd nesting
        result.syntax_errors = [1]
        result.error = f"Python file could not be parsed ({type(exc).__name__})"
        return result

    _collect(tree.body, result, owner=result.module_id, in_class=False)
    package = module if is_package_file(path) else module.rpartition(".")[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.imports.append(ImportFact(node.lineno, alias.name, [], alias.asname,
                                                 alias.name))
        elif isinstance(node, ast.ImportFrom):
            written = "." * node.level + (node.module or "")
            result.imports.append(ImportFact(
                node.lineno, _absolute(package, node.level, node.module),
                [alias.name for alias in node.names], None, written))
    result.module_tokens = ast.dump(ast.Module(body=_strip(tree.body), type_ignores=[]))
    result.file_parts = _file_parts(tree.body)
    return result


def _collect(body: list[ast.stmt], result: PythonParseResult, owner: str, in_class: bool) -> None:
    """Declarations of one scope (module or class body), through if/try/with blocks."""
    prefix = owner  # a module ID, or a class ID (which already carries the module)
    for node in _scope(body):
        start = min([d.lineno for d in node.decorator_list] + [node.lineno])
        if isinstance(node, ast.ClassDef):
            class_id = f"{prefix}.{node.name}"
            header_end = max(node.lineno, (node.body[0].lineno - 1) if node.body else node.lineno)
            if node.body and node.body[0].lineno == node.lineno:  # class A: pass
                header_end = node.lineno
            parts = [("header", node.lineno, header_end)]
            if node.decorator_list:
                parts.append(("decorator", start, node.lineno - 1))
            if node.body and header_end < node.end_lineno:
                parts.append(("body", header_end + 1, node.end_lineno))
            stripped = copy.copy(node)
            stripped.body = _strip(node.body)
            result.declarations.append(Declaration(
                id=class_id, kind=CLASS, name=node.name, parent=owner, start_line=start,
                end_line=node.end_lineno, tokens=ast.dump(stripped), parts=parts))
            for base in node.bases:
                result.bases.append(ClassBase(class_id, _dotted(base), base.lineno))
            _collect(node.body, result, owner=class_id, in_class=True)
        else:
            result.declarations.append(Declaration(
                id=f"{prefix}#{node.name}()", kind=METHOD if in_class else FUNCTION,
                name=node.name, parent=owner, start_line=start, end_line=node.end_lineno,
                tokens=ast.dump(node)))


def _scope(body: list[ast.stmt]):
    """Definitions directly in ``body``, also inside if/try/with statements there."""
    for node in body:
        if isinstance(node, _DEFS):
            yield node
        else:
            for block in _blocks(node):
                yield from _scope(block)


def _blocks(node: ast.stmt) -> list[list[ast.stmt]]:
    if isinstance(node, ast.If):
        return [node.body, node.orelse]
    if isinstance(node, (ast.Try, ast.TryStar)):
        return [node.body, *[h.body for h in node.handlers], node.orelse, node.finalbody]
    if isinstance(node, (ast.With, ast.AsyncWith)):
        return [node.body]
    return []


def _strip(body: list[ast.stmt]) -> list[ast.stmt]:
    """``body`` with each collected definition replaced by its name (for token comparison)."""
    stripped: list[ast.stmt] = []
    for node in body:
        if isinstance(node, _DEFS):
            stripped.append(ast.Expr(ast.Name(id=f"<def {node.name}>")))
            continue
        if _blocks(node):
            node = copy.copy(node)
            if isinstance(node, ast.If):
                node.body, node.orelse = _strip(node.body), _strip(node.orelse)
            elif isinstance(node, (ast.Try, ast.TryStar)):
                node.body, node.orelse = _strip(node.body), _strip(node.orelse)
                node.finalbody = _strip(node.finalbody)
                node.handlers = [copy.copy(h) for h in node.handlers]
                for handler in node.handlers:
                    handler.body = _strip(handler.body)
            else:
                node.body = _strip(node.body)
        stripped.append(node)
    return stripped


def _file_parts(body: list[ast.stmt]) -> list[tuple[str, int, int]]:
    parts = []
    for index, node in enumerate(body):
        if isinstance(node, _DEFS):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            name = "import"
        elif index == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            name = "docstring"
        else:
            name = "code"
        parts.append((name, node.lineno, node.end_lineno or node.lineno))
    return parts


def _absolute(package: str, level: int, module: str | None) -> str | None:
    """Resolve ``from <level dots><module> import ...`` inside ``package``."""
    if level == 0:
        return module
    base = package.split(".") if package else []
    if level - 1 >= len(base):  # beyond the top-level package (an ImportError in Python)
        return None
    base = base[:len(base) - (level - 1)]
    name = ".".join([*base, *([module] if module else [])])
    return name or None


def _dotted(node: ast.expr) -> str | None:
    if isinstance(node, ast.Subscript):  # Generic[T], list[int]
        node = node.value
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    return ".".join([node.id, *reversed(parts)])


def _decode(source: bytes) -> str:
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(source).readline)
        return source.decode(encoding)
    except (SyntaxError, LookupError, UnicodeDecodeError):
        return source.decode("utf-8", errors="replace")
