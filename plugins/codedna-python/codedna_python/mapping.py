"""Map file-level changed line ranges to Python declarations.

The same rules as the Java plugin's mapping (D-008), in the same result
shape, so the core treats both alike: base and head versions are read with
``git show`` (never imported or executed) and parsed with ``ast``; head-side
``changed_lines`` go to declarations of the head parse, base-side
``removed_lines`` to the base parse, each line to the innermost declaration
containing it. Declarations are matched across versions by ID.

* Lines outside every function and class (imports, module-level code,
  comments) become ``outside_declarations``; whether code changed there is
  decided by comparing the module-level code without definitions.
* ``code_changed`` is False when only comments, blank lines or formatting
  changed (``ast.dump`` ignores them). Docstrings are code: they are values
  at run time.
* A syntax error in either version makes every changed line of the file
  unresolved, and the core then treats the whole file as changed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from codedna.git_analysis.changes import ChangedFile, ChangeReport, LineRange
from codedna.git_analysis.git import run_git_bytes
from codedna_python.parser import TYPE_KINDS, Declaration, PythonParseResult, parse_python


@dataclass
class DeclarationChange:
    id: str
    kind: str
    change: str  # "added" | "deleted" | "modified"
    code_changed: bool | None  # False: only comments/formatting differ
    parent: str | None
    head_lines: LineRange | None
    base_lines: LineRange | None
    changed_lines: list[LineRange] = field(default_factory=list)
    removed_lines: list[LineRange] = field(default_factory=list)
    parts: list[str] = field(default_factory=list)  # classes: decorator/header/body


@dataclass
class OutsideChange:
    side: str
    lines: list[LineRange]
    parts: list[str]  # import | docstring | code | comment
    code_changed: bool | None


@dataclass
class UnresolvedChange:
    side: str
    lines: list[LineRange]
    reason: str


@dataclass
class PythonFileAnalysis:
    """Function-level view of one changed Python file (same shape as Java's)."""

    package: str | None  # the module name, e.g. "shop.orders"
    declarations: list[DeclarationChange] = field(default_factory=list)
    outside_declarations: list[OutsideChange] = field(default_factory=list)
    unresolved: list[UnresolvedChange] = field(default_factory=list)


def handles(path: str | None) -> bool:
    return bool(path) and path.endswith(".py")


def attach_python_declarations(report: ChangeReport) -> None:
    """Fill ``changed.analysis`` for every Python file in ``report`` (in place)."""
    repo = Path(report.repository)
    found = False
    for changed in report.changed_files:
        if handles(changed.path) or handles(changed.old_path):
            changed.analysis = analyze_python_file(
                repo, report.base_commit, report.head_commit, changed, report.warnings)
            found = True
    if found:
        report.analysis_level = "method"


def analyze_python_file(repo: Path, base_sha: str, head_sha: str, changed: ChangedFile,
                        warnings: list[str]) -> PythonFileAnalysis:
    base_path = None if changed.status == "added" else (changed.old_path or changed.path)
    head_path = None if changed.status == "deleted" else changed.path

    problem = None
    if changed.is_binary:
        problem = "binary Python file"
    for side, path in (("base", base_path), ("head", head_path)):
        if problem is None and path is not None and not handles(path):
            problem = f"{side} version is not a .py file ({path})"
    if problem is not None:
        warnings.append(f"{changed.path}: {problem}; declarations not mapped")
        return PythonFileAnalysis(package=None, unresolved=_all_unresolved(changed, problem))

    base = _parse_side(repo, base_sha, base_path)
    head = _parse_side(repo, head_sha, head_path)
    module = (head or base).module
    for side, parsed in (("base", base), ("head", head)):
        if parsed is not None and parsed.has_syntax_errors:
            reason = parsed.error.replace("near line", f"in {side} version near line", 1)
            warnings.append(f"{changed.path}: {reason}; declarations not mapped")
            return PythonFileAnalysis(package=module, unresolved=_all_unresolved(changed, reason))

    result = PythonFileAnalysis(package=module)
    head_hits = _attribute(head, changed.changed_lines)
    base_hits = _attribute(base, changed.removed_lines)
    _add_outside(result, base, head, base_hits.outside, head_hits.outside)
    _add_declarations(result, base, head, base_hits, head_hits)
    return result


def _parse_side(repo: Path, sha: str, path: str | None) -> PythonParseResult | None:
    if path is None:
        return None
    # "SHA:path" never starts with "-", so it cannot be read as an option.
    return parse_python(run_git_bytes(repo, "show", "--no-textconv", f"{sha}:{path}"), path)


@dataclass
class _Hits:
    by_declaration: dict[str, set[int]] = field(default_factory=dict)
    outside: set[int] = field(default_factory=set)


def _attribute(parsed: PythonParseResult | None, ranges: list[LineRange]) -> _Hits:
    hits = _Hits()
    if parsed is None:
        return hits
    for line in (n for start, end in ranges for n in range(start, end + 1)):
        innermost = _innermost(parsed.declarations, line)
        if innermost is None or innermost.kind in TYPE_KINDS:
            if line in parsed.blank_lines:  # blank gap lines carry no code
                continue
        if innermost is None:
            hits.outside.add(line)
        else:
            hits.by_declaration.setdefault(innermost.id, set()).add(line)
    return hits


def _innermost(declarations: list[Declaration], line: int) -> Declaration | None:
    """The smallest declaration containing ``line`` (definitions nest, never overlap)."""
    containing = [d for d in declarations if d.start_line <= line <= d.end_line]
    return min(containing, key=lambda d: d.end_line - d.start_line, default=None)


def _add_outside(result: PythonFileAnalysis, base: PythonParseResult | None,
                 head: PythonParseResult | None, base_lines: set[int],
                 head_lines: set[int]) -> None:
    if base is not None and head is not None:
        code_changed: bool | None = base.module_tokens != head.module_tokens
    else:
        code_changed = True  # whole file added or deleted
    for side, parsed, lines in (("head", head, head_lines), ("base", base, base_lines)):
        if lines and parsed is not None:
            result.outside_declarations.append(OutsideChange(
                side, _to_ranges(lines), _parts_touched(parsed.file_parts, lines, "comment"),
                code_changed))


def _add_declarations(result: PythonFileAnalysis, base: PythonParseResult | None,
                      head: PythonParseResult | None, base_hits: _Hits, head_hits: _Hits) -> None:
    base_by_id = base.by_id() if base else {}
    head_by_id = head.by_id() if head else {}
    touched = list(head_hits.by_declaration) + [
        i for i in base_hits.by_declaration if i not in head_hits.by_declaration]
    for declaration_id in touched:
        head_decls = head_by_id.get(declaration_id, [])
        base_decls = base_by_id.get(declaration_id, [])
        head_lines = head_hits.by_declaration.get(declaration_id, set())
        base_lines = base_hits.by_declaration.get(declaration_id, set())
        if not base_decls:
            change, code_changed = "added", True
        elif not head_decls:
            change, code_changed = "deleted", True
        else:
            change = "modified"
            code_changed = [d.tokens for d in head_decls] != [d.tokens for d in base_decls]
        reference = (head_decls or base_decls)[0]
        parts: set[str] = set()
        if reference.kind in TYPE_KINDS:
            for decls, lines in ((head_decls, head_lines), (base_decls, base_lines)):
                if decls and lines:
                    parts.update(_parts_touched(decls[0].parts, lines, "body"))
        result.declarations.append(DeclarationChange(
            id=declaration_id, kind=reference.kind, change=change, code_changed=code_changed,
            parent=reference.parent, head_lines=_extent(head_decls), base_lines=_extent(base_decls),
            changed_lines=_to_ranges(head_lines), removed_lines=_to_ranges(base_lines),
            parts=sorted(parts)))


def _extent(declarations: list[Declaration]) -> LineRange | None:
    if not declarations:
        return None
    return [min(d.start_line for d in declarations), max(d.end_line for d in declarations)]


def _parts_touched(parts: list[tuple[str, int, int]], lines: set[int], default: str) -> list[str]:
    names = set()
    for line in lines:
        covering = [name for name, start, end in parts if start <= line <= end]
        names.update(covering or [default])
    return sorted(names)


def _all_unresolved(changed: ChangedFile, reason: str) -> list[UnresolvedChange]:
    entries = []
    if changed.changed_lines:
        entries.append(UnresolvedChange("head", list(changed.changed_lines), reason))
    if changed.removed_lines:
        entries.append(UnresolvedChange("base", list(changed.removed_lines), reason))
    return entries


def _to_ranges(lines: set[int]) -> list[LineRange]:
    ranges: list[LineRange] = []
    for line in sorted(lines):
        if ranges and ranges[-1][1] == line - 1:
            ranges[-1][1] = line
        else:
            ranges.append([line, line])
    return ranges
