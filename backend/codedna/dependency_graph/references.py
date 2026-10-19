"""Collect the raw facts needed for dependency edges from one Java file.

Purely syntactic (Tree-sitter): imports, type-parameter names, and every
place a type *name* is written inside a type declaration, together with the
syntactic role of that name (``extends``, ``implements``, ``uses`` or the
heuristic ``static_access``). Resolving names to declarations happens later
in ``builder.py``, once every file in the repository is known.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tree_sitter import Node, Parser

from codedna.java_analysis.parser import _LANGUAGE, TYPE_NODES

_BODY_NODES = frozenset({
    "class_body", "interface_body", "enum_body", "enum_body_declarations",
    "annotation_type_body",
})
_HEADER_KINDS = {
    "superclass": "extends",
    "super_interfaces": "implements",
    "extends_interfaces": "extends",
}


@dataclass
class Import:
    name: str  # dotted name as written, without "static" or ".*"
    line: int
    static: bool = False
    wildcard: bool = False


@dataclass
class TypeReference:
    owner: str  # declaration ID of the innermost enclosing named type
    name: str  # simple (``Foo``) or qualified (``a.b.Foo``, ``Outer.Inner``) name
    line: int
    kind: str  # extends | implements | uses | static_access


@dataclass
class FileFacts:
    package: str | None
    imports: list[Import] = field(default_factory=list)
    type_parameters: set[str] = field(default_factory=set)
    references: list[TypeReference] = field(default_factory=list)


def extract_references(source: bytes) -> FileFacts:
    root = Parser(_LANGUAGE).parse(source).root_node
    facts = FileFacts(package=None)
    for child in root.children:
        if child.type == "package_declaration":
            facts.package = _compact(_first_named(child, ("scoped_identifier", "identifier")))
        elif child.type == "import_declaration":
            name_node = _first_named(child, ("scoped_identifier", "identifier"))
            facts.imports.append(Import(
                name=_compact(name_node),
                line=_line(child),
                static=any(c.type == "static" for c in child.children),
                wildcard=any(c.type == "asterisk" for c in child.children),
            ))
    _walk(root, facts)
    return facts


def _walk(root: Node, facts: FileFacts) -> None:
    # Iterative depth-first walk; each item is (node, owner type ID, reference kind).
    stack: list[tuple[Node, str | None, str]] = [(root, None, "uses")]
    while stack:
        node, owner, kind = stack.pop()
        node_type = node.type

        if node_type in ("package_declaration", "import_declaration"):
            continue
        if node_type in TYPE_NODES and _is_named_member_type(node):
            name = _text(node.child_by_field_name("name"))
            if owner is not None:
                type_id = f"{owner}.{name}"
            else:
                type_id = f"{facts.package}.{name}" if facts.package else name
            for child in node.children:
                stack.append((child, type_id, _HEADER_KINDS.get(child.type, "uses")))
            continue
        if owner is None:
            stack.extend((child, None, kind) for child in node.children)
            continue

        if node_type == "type_identifier":
            facts.references.append(TypeReference(owner, _text(node), _line(node), kind))
        elif node_type == "scoped_type_identifier":
            facts.references.append(TypeReference(owner, _compact(node), _line(node), kind))
        elif node_type == "type_parameter":
            # `<T extends Bound>`: T is a type variable, not a reference.
            name_node = _first_named(node, ("type_identifier",))
            if name_node is not None:
                facts.type_parameters.add(_text(name_node))
            stack.extend((c, owner, "uses") for c in node.named_children if c != name_node)
        elif node_type in ("marker_annotation", "annotation"):
            name_node = node.child_by_field_name("name")
            if name_node is not None:
                facts.references.append(
                    TypeReference(owner, _compact(name_node), _line(node), "uses"))
            arguments = node.child_by_field_name("arguments")
            if arguments is not None:
                stack.append((arguments, owner, "uses"))
        else:
            if node_type in ("method_invocation", "field_access"):
                target = node.child_by_field_name("object")
                # `Foo.bar()` / `Foo.BAR`: by Java naming conventions a
                # capitalised identifier is usually a class, but it could be
                # a variable, so this is only a heuristic reference.
                if target is not None and target.type == "identifier" and _text(target)[:1].isupper():
                    facts.references.append(
                        TypeReference(owner, _text(target), _line(target), "static_access"))
            # Generic arguments of `extends Base<Foo>` are ordinary uses.
            child_kind = "uses" if node_type == "type_arguments" else kind
            stack.extend((child, owner, child_kind) for child in node.children)


def _is_named_member_type(node: Node) -> bool:
    """True for top-level and member types; local classes inside methods are not."""
    parent = node.parent
    return parent is None or parent.type == "program" or parent.type in _BODY_NODES


def _first_named(node: Node, types: tuple[str, ...]) -> Node | None:
    return next((c for c in node.named_children if c.type in types), None)


def _text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8", errors="replace")


def _compact(node: Node | None) -> str:
    return "".join(_text(node).split())


def _line(node: Node) -> int:
    return node.start_point.row + 1
