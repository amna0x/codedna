"""Syntax-level extraction of Java declarations with Tree-sitter.

``parse_java`` turns the bytes of one ``.java`` file into a flat list of
:class:`Declaration` objects (types and their members) with 1-based,
inclusive line ranges. It is purely syntactic: names and types are recorded
as written in the source and nothing is resolved (see docs/DECISIONS.md,
D-008 and D-009 for the ID format and its limits).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import tree_sitter_java
from tree_sitter import Language, Node, Parser

_LANGUAGE = Language(tree_sitter_java.language())

COMMENT_NODES = frozenset({"line_comment", "block_comment"})

# Tree-sitter node type -> declaration kind.
TYPE_NODES = {
    "class_declaration": "class",
    "interface_declaration": "interface",
    "enum_declaration": "enum",
    "record_declaration": "record",
    "annotation_type_declaration": "annotation_type",
}
_BODY_NODES = frozenset({
    "class_body", "interface_body", "enum_body", "enum_body_declarations",
    "annotation_type_body",
})


@dataclass
class Declaration:
    """A type or member declared in a Java source file."""

    id: str
    kind: str
    name: str
    start_line: int
    end_line: int
    parent: str | None = None
    # Non-comment tokens that belong to this declaration itself. For types
    # this excludes the tokens of nested members, so a type only counts as
    # changed when its own header/annotations/modifiers change.
    tokens: tuple[str, ...] = field(default=(), repr=False, compare=False)
    # Line ranges of the parts of a type (header, annotations, ...) used to
    # explain type-level changes. Empty for members.
    parts: list[tuple[str, int, int]] = field(default_factory=list, repr=False, compare=False)


@dataclass
class UnsupportedRegion:
    """Lines whose syntax the extractor does not understand."""

    start_line: int
    end_line: int
    reason: str


@dataclass
class JavaParseResult:
    """All declarations found in one Java source file."""

    package: str | None
    declarations: list[Declaration]
    # Top-level parts of the file outside every type: (part, start, end).
    file_parts: list[tuple[str, int, int]]
    file_tokens: tuple[str, ...]
    line_count: int
    syntax_errors: list[int]  # 1-based lines with ERROR/MISSING nodes
    unsupported: list[UnsupportedRegion]
    blank_lines: frozenset[int]

    @property
    def has_syntax_errors(self) -> bool:
        return bool(self.syntax_errors)


def parse_java(source: bytes) -> JavaParseResult:
    """Parse one Java file and return its declarations."""
    tree = Parser(_LANGUAGE).parse(source)
    root = tree.root_node
    lines = source.split(b"\n")
    blank = frozenset(number for number, text in enumerate(lines, start=1) if not text.strip())
    extractor = _Extractor()

    package = None
    file_parts: list[tuple[str, int, int]] = []
    file_tokens: list[str] = []
    for child in root.children:
        if child.type in TYPE_NODES:
            extractor.visit_type(child, package, parent=None)
            continue
        if child.type == "package_declaration":
            package = _package_name(child)
        part = {
            "package_declaration": "package",
            "import_declaration": "import",
            "module_declaration": "module",
        }.get(child.type, "comment" if child.type in COMMENT_NODES else child.type)
        file_parts.append((part, _start(child), _end(child)))
        file_tokens.extend(_tokens(child))
        if part not in ("package", "import", "module", "comment", ";"):
            extractor.unsupported.append(UnsupportedRegion(
                _start(child), _end(child), f"unsupported top-level syntax: {child.type}"))

    return JavaParseResult(
        package=package,
        declarations=extractor.declarations,
        file_parts=file_parts,
        file_tokens=tuple(file_tokens),
        line_count=len(lines),
        syntax_errors=sorted(_error_lines(root)) if root.has_error else [],
        unsupported=extractor.unsupported,
        blank_lines=blank,
    )


class _Extractor:
    def __init__(self) -> None:
        self.declarations: list[Declaration] = []
        self.unsupported: list[UnsupportedRegion] = []

    def visit_type(self, node: Node, package: str | None, parent: Declaration | None) -> None:
        name = _text(node.child_by_field_name("name"))
        if parent is not None:
            type_id = f"{parent.id}.{name}"
        else:
            type_id = f"{package}.{name}" if package else name
        declaration = Declaration(
            id=type_id, kind=TYPE_NODES[node.type], name=name,
            start_line=_start(node), end_line=_end(node),
            parent=parent.id if parent else None,
        )
        self.declarations.append(declaration)

        # Record components double as the parameters of a compact constructor.
        record_params = _parameter_types(node) if node.type == "record_declaration" else ""
        own_tokens: list[str] = []
        counters = {"<clinit>": 0, "<init-block>": 0}
        for child in node.children:
            if child.type in _BODY_NODES:
                own_tokens.extend(
                    self._visit_body(child, declaration, package, counters, record_params))
            else:
                own_tokens.extend(_tokens(child))
                declaration.parts.append((_type_part(child), _start(child), _end(child)))
        declaration.tokens = tuple(own_tokens)

    def _visit_body(self, body: Node, owner: Declaration, package: str | None,
                    counters: dict[str, int], record_params: str) -> list[str]:
        """Collect members of a type body; return the tokens that belong to the type."""
        own_tokens: list[str] = []
        for child in body.children:
            kind = child.type
            if kind in COMMENT_NODES:
                owner.parts.append(("comment", _start(child), _end(child)))
            elif kind in ("{", "}", ";", ","):
                own_tokens.append(kind)
                owner.parts.append(("body", _start(child), _end(child)))
            elif kind == "enum_body_declarations":
                own_tokens.extend(
                    self._visit_body(child, owner, package, counters, record_params))
            elif kind in TYPE_NODES:
                self.visit_type(child, package, owner)
            elif kind in ("method_declaration", "annotation_type_element_declaration"):
                name = _text(child.child_by_field_name("name"))
                if kind == "method_declaration":
                    member_id = f"{owner.id}#{name}({_parameter_types(child)})"
                    member_kind = "method"
                else:
                    member_id, member_kind = f"{owner.id}#{name}", "annotation_element"
                self._add_member(child, owner, member_id, member_kind, name)
            elif kind == "constructor_declaration":
                self._add_member(child, owner, f"{owner.id}#<init>({_parameter_types(child)})",
                                 "constructor", "<init>")
            elif kind == "compact_constructor_declaration":
                self._add_member(child, owner, f"{owner.id}#<init>({record_params})",
                                 "constructor", "<init>")
            elif kind in ("field_declaration", "constant_declaration"):
                for declarator in child.children_by_field_name("declarator"):
                    name = _text(declarator.child_by_field_name("name"))
                    self._add_member(child, owner, f"{owner.id}#{name}", "field", name)
            elif kind == "enum_constant":
                name = _text(child.child_by_field_name("name"))
                self._add_member(child, owner, f"{owner.id}#{name}", "enum_constant", name)
            elif kind in ("static_initializer", "block"):
                label = "<clinit>" if kind == "static_initializer" else "<init-block>"
                counters[label] += 1
                self._add_member(child, owner, f"{owner.id}#{label}[{counters[label]}]",
                                 "initializer", label)
            else:
                self.unsupported.append(UnsupportedRegion(
                    _start(child), _end(child), f"unsupported declaration syntax: {kind}"))
        return own_tokens

    def _add_member(self, node: Node, owner: Declaration, member_id: str, kind: str,
                    name: str) -> None:
        self.declarations.append(Declaration(
            id=member_id, kind=kind, name=name,
            start_line=_start(node), end_line=_end(node), parent=owner.id,
            tokens=tuple(_tokens(node)),
        ))


def _parameter_types(node: Node) -> str:
    parameters = node.child_by_field_name("parameters")
    return _parameter_list(parameters) if parameters is not None else ""


def _parameter_list(parameters: Node) -> str:
    types = []
    for parameter in parameters.named_children:
        if parameter.type == "formal_parameter":
            text = _compact(parameter.child_by_field_name("type"))
            dimensions = parameter.child_by_field_name("dimensions")
            if dimensions is not None:  # C-style `int values[]`
                text += _compact(dimensions)
            types.append(text)
        elif parameter.type == "spread_parameter":  # varargs `String... names`
            type_node = next(
                child for child in parameter.named_children
                if child.type not in ("modifiers", "variable_declarator")
            )
            types.append(_compact(type_node) + "...")
        # receiver_parameter (`Outer this`) is not part of the signature.
    return ",".join(types)


def _type_part(node: Node) -> str:
    if node.type == "modifiers":
        has_annotation = any(c.type in ("annotation", "marker_annotation") for c in node.children)
        return "annotation" if has_annotation else "modifiers"
    if node.type in COMMENT_NODES:
        return "comment"
    return "header"


def _package_name(node: Node) -> str:
    for child in node.named_children:
        if child.type in ("scoped_identifier", "identifier"):
            return _compact(child)
    return ""


def _tokens(node: Node) -> list[str]:
    """Leaf tokens under ``node`` excluding comments (whitespace is never a token).

    Iterative, so deeply nested code (e.g. long generated ``a + b + ...``
    chains) cannot exceed Python's recursion limit.
    """
    tokens: list[str] = []
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type in COMMENT_NODES:
            continue
        if current.child_count == 0:
            tokens.append(_text(current))
        else:
            stack.extend(reversed(current.children))
    return tokens


def _error_lines(node: Node) -> set[int]:
    lines: set[int] = set()
    stack = [node]
    while stack:
        current = stack.pop()
        if current.is_error or current.is_missing:
            lines.add(_start(current))
            continue
        stack.extend(c for c in current.children if c.has_error or c.is_missing)
    return lines


def _text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8", errors="replace")


def _compact(node: Node | None) -> str:
    return "".join(_text(node).split())


def _start(node: Node) -> int:
    return node.start_point.row + 1


def _end(node: Node) -> int:
    # A node ending at column 0 stops before that line (e.g. trailing newline).
    row, column = node.end_point
    return row if column == 0 and row > node.start_point.row else row + 1
