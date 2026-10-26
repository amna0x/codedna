"""Map file-level changed line ranges to Java declarations.

Second stage of the CodeDNA pipeline. For every changed ``.java`` file the
base and head versions are read with ``git show`` (never checked out, never
executed) and parsed with Tree-sitter. Then:

* head-side ``changed_lines`` are attributed to declarations of the head parse,
* base-side ``removed_lines`` are attributed to declarations of the base parse,

each line going to the innermost declaration that contains it. Declarations
are matched across versions by ID to decide whether they were added, deleted
or modified. Rules and ID format: docs/DECISIONS.md, D-008 and D-009.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from codedna.git_analysis.changes import ChangedFile, ChangeReport, LineRange, extract_changes
from codedna.git_analysis.git import run_git_bytes
from codedna_java.parser import TYPE_NODES, Declaration, JavaParseResult, parse_java

_TYPE_KINDS = frozenset(TYPE_NODES.values())


@dataclass
class DeclarationChange:
    """A declaration touched by the diff."""

    id: str
    kind: str
    change: str  # "added" | "deleted" | "modified"
    # False: only comments/formatting differ. None: could not be compared.
    code_changed: bool | None
    parent: str | None
    head_lines: LineRange | None  # declaration extent in the head file
    base_lines: LineRange | None  # declaration extent in the base file
    changed_lines: list[LineRange] = field(default_factory=list)  # head side
    removed_lines: list[LineRange] = field(default_factory=list)  # base side
    # For types only: which parts of the type itself changed
    # ("annotation", "modifiers", "header", "body", "comment").
    parts: list[str] = field(default_factory=list)


@dataclass
class OutsideChange:
    """Changed lines that lie outside every type (package, imports, comments)."""

    side: str  # "head" | "base"
    lines: list[LineRange]
    parts: list[str]
    code_changed: bool | None


@dataclass
class UnresolvedChange:
    """Changed lines that could not be mapped, with the reason."""

    side: str  # "head" | "base"
    lines: list[LineRange]
    reason: str


@dataclass
class JavaFileAnalysis:
    """Method-level view of one changed Java file."""

    package: str | None
    declarations: list[DeclarationChange] = field(default_factory=list)
    outside_declarations: list[OutsideChange] = field(default_factory=list)
    unresolved: list[UnresolvedChange] = field(default_factory=list)


def analyze_changes(repo_path: str | Path, base: str, head: str) -> ChangeReport:
    """File-level changes plus declaration mapping for every Java file."""
    report = extract_changes(repo_path, base, head)
    attach_java_declarations(report)
    return report


def attach_java_declarations(report: ChangeReport) -> None:
    """Fill ``changed.java`` for every Java file in ``report`` (in place)."""
    repo = Path(report.repository)
    for changed in report.changed_files:
        if changed.is_java:
            changed.java = analyze_java_file(
                repo, report.base_commit, report.head_commit, changed, report.warnings)
    report.analysis_level = "method"


def analyze_java_file(repo: Path, base_sha: str, head_sha: str, changed: ChangedFile,
                      warnings: list[str]) -> JavaFileAnalysis:
    """Attribute the changed/removed line ranges of one Java file to declarations."""
    base_path = None if changed.status == "added" else (changed.old_path or changed.path)
    head_path = None if changed.status == "deleted" else changed.path

    problem = _unparseable_reason(changed, base_path, head_path)
    if problem is not None:
        warnings.append(f"{changed.path}: {problem}; declarations not mapped")
        return JavaFileAnalysis(package=None, unresolved=_all_unresolved(changed, problem))

    base = _parse_side(repo, base_sha, base_path)
    head = _parse_side(repo, head_sha, head_path)
    package = (head or base).package if (head or base) else None

    for side, parsed in (("base", base), ("head", head)):
        if parsed is not None and parsed.has_syntax_errors:
            reason = (f"Java syntax error in {side} version near line "
                      f"{parsed.syntax_errors[0]}")
            warnings.append(f"{changed.path}: {reason}; declarations not mapped")
            return JavaFileAnalysis(package=package,
                                    unresolved=_all_unresolved(changed, reason))

    result = JavaFileAnalysis(package=package)
    head_hits = _attribute("head", head, changed.changed_lines, result)
    base_hits = _attribute("base", base, changed.removed_lines, result)
    _add_outside(result, base, head, base_hits.outside, head_hits.outside)
    _add_declarations(result, base, head, base_hits, head_hits)
    for side, parsed in (("base", base), ("head", head)):
        if parsed is not None and _duplicate_ids(parsed):
            warnings.append(f"{changed.path}: duplicate declaration IDs in {side} version "
                            f"({', '.join(_duplicate_ids(parsed))}); matching may be ambiguous")
    for entry in result.unresolved:
        warnings.append(f"{changed.path}: {entry.reason} ({entry.side} lines {entry.lines})")
    return result


def _unparseable_reason(changed: ChangedFile, base_path: str | None,
                        head_path: str | None) -> str | None:
    if changed.is_binary:
        return "binary Java file"
    for side, path in (("base", base_path), ("head", head_path)):
        if path is not None and not path.endswith(".java"):
            return f"{side} version is not a .java file ({path})"
    return None


def _parse_side(repo: Path, sha: str, path: str | None) -> JavaParseResult | None:
    if path is None:
        return None
    # "SHA:path" never starts with "-", so it cannot be read as an option.
    source = run_git_bytes(repo, "show", "--no-textconv", f"{sha}:{path}")
    return parse_java(source)


@dataclass
class _Hits:
    by_declaration: dict[str, set[int]] = field(default_factory=dict)
    outside: set[int] = field(default_factory=set)


def _attribute(side: str, parsed: JavaParseResult | None, ranges: list[LineRange],
               result: JavaFileAnalysis) -> _Hits:
    hits = _Hits()
    if parsed is None:
        return hits
    by_id = {d.id: d for d in parsed.declarations}
    unsupported: dict[str, set[int]] = {}
    for line in _lines(ranges):
        region = next((r for r in parsed.unsupported if r.start_line <= line <= r.end_line), None)
        if region is not None:
            unsupported.setdefault(region.reason, set()).add(line)
            continue
        innermost = _innermost(parsed.declarations, by_id, line)
        if not innermost or all(d.kind in _TYPE_KINDS for d in innermost):
            # Gap lines (between members or outside types): blank lines carry no code.
            if line in parsed.blank_lines:
                continue
        if not innermost:
            hits.outside.add(line)
        for declaration in innermost:
            hits.by_declaration.setdefault(declaration.id, set()).add(line)
    for reason, lines in unsupported.items():
        result.unresolved.append(UnresolvedChange(side, _to_ranges(lines), reason))
    return hits


def _innermost(declarations: list[Declaration], by_id: dict[str, Declaration],
               line: int) -> list[Declaration]:
    """Declarations containing ``line`` that contain no other such declaration."""
    containing = [d for d in declarations if d.start_line <= line <= d.end_line]
    ancestors: set[str] = set()
    for declaration in containing:
        parent = declaration.parent
        while parent is not None and parent not in ancestors:
            ancestors.add(parent)
            parent = by_id[parent].parent if parent in by_id else None
    return [d for d in containing if d.id not in ancestors]


def _add_outside(result: JavaFileAnalysis, base: JavaParseResult | None,
                 head: JavaParseResult | None, base_lines: set[int],
                 head_lines: set[int]) -> None:
    if base is not None and head is not None:
        code_changed: bool | None = base.file_tokens != head.file_tokens
    else:
        code_changed = True  # whole file added or deleted
    for side, parsed, lines in (("head", head, head_lines), ("base", base, base_lines)):
        if lines and parsed is not None:
            parts = _parts_touched(parsed.file_parts, lines, default="other")
            result.outside_declarations.append(
                OutsideChange(side, _to_ranges(lines), parts, code_changed))


def _add_declarations(result: JavaFileAnalysis, base: JavaParseResult | None,
                      head: JavaParseResult | None, base_hits: _Hits, head_hits: _Hits) -> None:
    base_by_id = {d.id: d for d in base.declarations} if base else {}
    head_by_id = {d.id: d for d in head.declarations} if head else {}

    touched = list(head_hits.by_declaration) + [
        i for i in base_hits.by_declaration if i not in head_hits.by_declaration]
    for declaration_id in touched:
        head_decl = head_by_id.get(declaration_id)
        base_decl = base_by_id.get(declaration_id)
        head_lines = head_hits.by_declaration.get(declaration_id, set())
        base_lines = base_hits.by_declaration.get(declaration_id, set())
        if base_decl is None:
            change, code_changed = "added", True
        elif head_decl is None:
            change, code_changed = "deleted", True
        else:
            change, code_changed = "modified", head_decl.tokens != base_decl.tokens
        reference = head_decl or base_decl
        parts: set[str] = set()
        if reference.kind in _TYPE_KINDS:
            if head_decl is not None and head_lines:
                parts.update(_parts_touched(head_decl.parts, head_lines, default="body"))
            if base_decl is not None and base_lines:
                parts.update(_parts_touched(base_decl.parts, base_lines, default="body"))
        result.declarations.append(DeclarationChange(
            id=declaration_id,
            kind=reference.kind,
            change=change,
            code_changed=code_changed,
            parent=reference.parent,
            head_lines=[head_decl.start_line, head_decl.end_line] if head_decl else None,
            base_lines=[base_decl.start_line, base_decl.end_line] if base_decl else None,
            changed_lines=_to_ranges(head_lines),
            removed_lines=_to_ranges(base_lines),
            parts=sorted(parts),
        ))


def _parts_touched(parts: list[tuple[str, int, int]], lines: set[int], default: str) -> list[str]:
    names = set()
    for line in lines:
        covering = [name for name, start, end in parts if start <= line <= end]
        names.update(covering or [default])
    return sorted(names)


def _duplicate_ids(parsed: JavaParseResult) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for declaration in parsed.declarations:
        if declaration.id in seen and declaration.id not in duplicates:
            duplicates.append(declaration.id)
        seen.add(declaration.id)
    return duplicates


def _all_unresolved(changed: ChangedFile, reason: str) -> list[UnresolvedChange]:
    entries = []
    if changed.changed_lines:
        entries.append(UnresolvedChange("head", list(changed.changed_lines), reason))
    if changed.removed_lines:
        entries.append(UnresolvedChange("base", list(changed.removed_lines), reason))
    return entries


def _lines(ranges: list[LineRange]) -> list[int]:
    return [line for start, end in ranges for line in range(start, end + 1)]


def _to_ranges(lines: set[int]) -> list[LineRange]:
    ranges: list[LineRange] = []
    for line in sorted(lines):
        if ranges and ranges[-1][1] == line - 1:
            ranges[-1][1] = line
        else:
            ranges.append([line, line])
    return ranges
