"""Tests for mapping changed line ranges to Java declarations."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from codedna.java_analysis import analyze_changes, parse_java

ROOT = Path(__file__).resolve().parents[2]
PATH = "src/main/java/p/A.java"


def java_of(report, path=PATH):
    return next(f for f in report.changed_files if f.path == path).java


def by_id(java):
    return {d.id: d for d in java.declarations}


def analyze_edit(repo, before: str, after: str, path: str = PATH):
    repo.write(path, before)
    base = repo.commit("base")
    repo.write(path, after)
    head = repo.commit("head")
    report = analyze_changes(repo.path, base, head)
    return report, java_of(report, path)


# --- parser ---------------------------------------------------------------

def test_parser_builds_ids_for_overloads_constructors_and_nested_types():
    source = b"""package p.q;

public class Outer<T> {
    static int counter, other[];
    static { counter = 1; }
    { other = null; }
    Outer() {}
    Outer(int a, String b) {}
    void run(int x) {}
    void run(String s) {}
    void run(java.util.List< String > items, int values[], Object... rest) {}
    static class Inner {
        int size() { return 0; }
    }
    enum Color { RED, GREEN { void shade() {} } }
    record Point(int x, int y) { Point {} }
    interface Shape { double area(); }
    @interface Marker { int value() default 0; }
}
"""
    parsed = parse_java(source)

    assert parsed.package == "p.q"
    assert not parsed.has_syntax_errors
    assert parsed.unsupported == []
    ids = {d.id: d.kind for d in parsed.declarations}
    assert ids == {
        "p.q.Outer": "class",
        "p.q.Outer#counter": "field",
        "p.q.Outer#other": "field",
        "p.q.Outer#<clinit>[1]": "initializer",
        "p.q.Outer#<init-block>[1]": "initializer",
        "p.q.Outer#<init>()": "constructor",
        "p.q.Outer#<init>(int,String)": "constructor",
        "p.q.Outer#run(int)": "method",
        "p.q.Outer#run(String)": "method",
        "p.q.Outer#run(java.util.List<String>,int[],Object...)": "method",
        "p.q.Outer.Inner": "class",
        "p.q.Outer.Inner#size()": "method",
        "p.q.Outer.Color": "enum",
        "p.q.Outer.Color#RED": "enum_constant",
        "p.q.Outer.Color#GREEN": "enum_constant",
        "p.q.Outer.Point": "record",
        "p.q.Outer.Point#<init>(int,int)": "constructor",
        "p.q.Outer.Shape": "interface",
        "p.q.Outer.Shape#area()": "method",
        "p.q.Outer.Marker": "annotation_type",
        "p.q.Outer.Marker#value": "annotation_element",
    }
    inner_size = next(d for d in parsed.declarations if d.id == "p.q.Outer.Inner#size()")
    assert (inner_size.start_line, inner_size.end_line, inner_size.parent) == (
        13, 13, "p.q.Outer.Inner")
    outer = parsed.declarations[0]
    assert (outer.start_line, outer.end_line) == (3, 19)


def test_parser_default_package_and_syntax_errors():
    parsed = parse_java(b"class A {\n  void f( {\n}\n")

    assert parsed.package is None
    assert parsed.has_syntax_errors
    assert parse_java(b"class A { void f() {} }").declarations[1].id == "A#f()"


# --- mapping --------------------------------------------------------------

BASE = """package p;

import java.util.List;

public class A {

    private int count;

    public A() {
        count = 0;
    }

    public A(int start) {
        count = start;
    }

    int add(int x) {
        return count + x;
    }

    int add(String x) {
        return count + x.length();
    }

    int twice(int x) {
        // double it
        return x * 2;
    }
}
"""


def edit(text: str, old: str, new: str) -> str:
    assert old in text
    return text.replace(old, new, 1)


def test_overloaded_method_change_names_only_that_overload(repo):
    _, java = analyze_edit(repo, BASE, edit(BASE, "count + x.length()", "x.length() + count"))

    assert [(d.id, d.change, d.code_changed) for d in java.declarations] == [
        ("p.A#add(String)", "modified", True)]
    change = java.declarations[0]
    assert change.kind == "method"
    assert change.parent == "p.A"
    assert change.head_lines == [21, 23] and change.base_lines == [21, 23]
    assert change.changed_lines == [[22, 22]] and change.removed_lines == [[22, 22]]
    assert java.outside_declarations == [] and java.unresolved == []


def test_constructor_change(repo):
    _, java = analyze_edit(repo, BASE, edit(BASE, "count = start;", "count = start + 1;"))

    assert [(d.id, d.kind, d.change) for d in java.declarations] == [
        ("p.A#<init>(int)", "constructor", "modified")]


def test_nested_class_method(repo):
    before = "package p;\n\nclass A {\n    static class B {\n        int f() { return 1; }\n" \
             "        int g() { return 2; }\n    }\n}\n"
    _, java = analyze_edit(repo, before, edit(before, "return 2;", "return 3;"))

    assert [(d.id, d.parent) for d in java.declarations] == [("p.A.B#g()", "p.A.B")]


def test_multiple_methods_changed_in_one_file(repo):
    after = edit(edit(BASE, "count = 0;", "count = -1;"), "return x * 2;", "return x + x;")
    _, java = analyze_edit(repo, BASE, after)

    assert [(d.id, d.change, d.code_changed) for d in java.declarations] == [
        ("p.A#<init>()", "modified", True),
        ("p.A#twice(int)", "modified", True),
    ]


def test_change_spanning_two_methods(repo):
    after = edit(BASE, "        return count + x;\n    }\n\n    int add(String x) {\n",
                 "        return x + count;\n    }\n\n    int add(String x, int y) {\n")
    _, java = analyze_edit(repo, BASE, after)

    changes = {(d.id, d.change) for d in java.declarations}
    assert changes == {
        ("p.A#add(int)", "modified"),
        ("p.A#add(String,int)", "added"),
        ("p.A#add(String)", "deleted"),
    }
    # The blank line between the methods is part of the hunk but carries no code.
    assert "p.A" not in by_id(java)


def test_comment_only_change_inside_method(repo):
    _, java = analyze_edit(repo, BASE, edit(BASE, "// double it", "// multiply by two"))

    assert [(d.id, d.change, d.code_changed) for d in java.declarations] == [
        ("p.A#twice(int)", "modified", False)]


def test_formatting_only_change(repo):
    after = edit(BASE, "    int twice(int x) {\n        // double it\n        return x * 2;\n    }\n",
                 "    int twice( int x )\n    {\n        // double it\n        return x*2;\n    }\n")
    _, java = analyze_edit(repo, BASE, after)

    assert [(d.id, d.code_changed) for d in java.declarations] == [("p.A#twice(int)", False)]


def test_javadoc_between_members_is_a_type_level_comment_change(repo):
    after = edit(BASE, "    int twice(int x) {", "    /** Doubles x. */\n    int twice(int x) {")
    _, java = analyze_edit(repo, BASE, after)

    assert len(java.declarations) == 1
    change = java.declarations[0]
    assert (change.id, change.kind, change.change) == ("p.A", "class", "modified")
    assert change.code_changed is False
    assert change.parts == ["comment"]


def test_method_deletion_is_mapped_on_the_base_side(repo):
    after = edit(BASE, "\n    int add(String x) {\n        return count + x.length();\n    }\n", "")
    _, java = analyze_edit(repo, BASE, after)

    assert len(java.declarations) == 1
    deleted = java.declarations[0]
    assert (deleted.id, deleted.change) == ("p.A#add(String)", "deleted")
    assert deleted.head_lines is None and deleted.base_lines == [21, 23]
    assert deleted.changed_lines == [] and deleted.removed_lines == [[21, 23]]


def test_added_method_does_not_flag_the_class(repo):
    after = edit(BASE, "        return x * 2;\n    }\n",
                 "        return x * 2;\n    }\n\n    int zero() {\n        return 0;\n    }\n")
    _, java = analyze_edit(repo, BASE, after)

    assert [(d.id, d.change) for d in java.declarations] == [("p.A#zero()", "added")]


def test_changes_outside_methods_are_reported_explicitly(repo):
    after = edit(edit(edit(BASE, "import java.util.List;", "import java.util.Map;"),
                      "private int count;", "private long count;"),
                 "public class A {", "@Deprecated\npublic class A {")
    _, java = analyze_edit(repo, BASE, after)

    assert [(o.side, o.parts, o.code_changed) for o in java.outside_declarations] == [
        ("head", ["import"], True), ("base", ["import"], True)]
    changes = by_id(java)
    assert changes["p.A#count"].kind == "field"
    assert changes["p.A#count"].change == "modified"
    assert changes["p.A"].parts == ["annotation"]
    assert changes["p.A"].code_changed is True
    assert set(changes) == {"p.A", "p.A#count"}


def test_added_java_file_lists_all_declarations_as_added(repo):
    repo.write("README.md", "x\n")
    base = repo.commit("base")
    repo.write(PATH, "package p;\n\nclass A {\n    A() {}\n    void f() {}\n}\n")
    head = repo.commit("head")

    java = java_of(analyze_changes(repo.path, base, head))

    assert [(d.id, d.change) for d in java.declarations] == [
        ("p.A", "added"), ("p.A#<init>()", "added"), ("p.A#f()", "added")]
    assert [(o.side, o.parts) for o in java.outside_declarations] == [("head", ["package"])]


def test_deleted_java_file_lists_all_declarations_as_deleted(repo):
    repo.write(PATH, "package p;\n\nclass A {\n    void f() {}\n}\n")
    base = repo.commit("base")
    (repo.path / PATH).unlink()
    head = repo.commit("head")

    java = java_of(analyze_changes(repo.path, base, head))

    assert [(d.id, d.change, d.base_lines) for d in java.declarations] == [
        ("p.A", "deleted", [3, 5]), ("p.A#f()", "deleted", [4, 4])]
    assert java.package == "p"


def test_renamed_java_file_maps_base_side_on_old_path(repo):
    body = "".join(f"    int m{i}() {{ return {i}; }}\n" for i in range(10))
    repo.write("src/main/java/p/Util.java", f"package p;\n\nclass Util {{\n{body}}}\n")
    base = repo.commit("base")
    repo.git("mv", "src/main/java/p/Util.java", "src/main/java/p/Helpers.java")
    repo.write("src/main/java/p/Helpers.java",
               f"package p;\n\nclass Util {{\n{body.replace('return 3;', 'return 33;')}}}\n")
    head = repo.commit("head")

    report = analyze_changes(repo.path, base, head)
    changed = report.changed_files[0]

    assert changed.status == "renamed"
    assert [(d.id, d.change) for d in changed.java.declarations] == [("p.Util#m3()", "modified")]


def test_class_rename_shows_added_and_deleted_types(repo):
    _, java = analyze_edit(repo, "package p;\n\nclass A {\n    void f() {}\n}\n",
                           "package p;\n\nclass B {\n    void f() {}\n}\n")

    assert {(d.id, d.change) for d in java.declarations} == {
        ("p.B", "added"), ("p.A", "deleted")}


def test_syntax_error_goes_to_unresolved_with_warning(repo):
    report, java = analyze_edit(repo, "package p;\n\nclass A {\n    void f() {}\n}\n",
                                "package p;\n\nclass A {\n    void f( {}\n}\n")

    assert java.declarations == []
    assert [(u.side, u.lines) for u in java.unresolved] == [("head", [[4, 4]]), ("base", [[4, 4]])]
    assert all("syntax error in head version" in u.reason for u in java.unresolved)
    assert any("syntax error" in w for w in report.warnings)


def test_java_renamed_to_non_java_is_unresolved(repo):
    body = "".join(f"    int m{i}() {{ return {i}; }}\n" for i in range(10))
    repo.write("A.java", f"class A {{\n{body}}}\n")
    base = repo.commit("base")
    repo.git("mv", "A.java", "A.txt")
    repo.write("A.txt", f"class A {{\n{body.replace('return 3;', 'return 4;')}}}\n")
    head = repo.commit("head")

    report = analyze_changes(repo.path, base, head)
    assert report.changed_files[0].status == "renamed"
    java = report.changed_files[0].java

    assert java.declarations == []
    assert "not a .java file" in java.unresolved[0].reason
    assert report.warnings


def test_non_java_files_have_no_declaration_mapping(repo):
    repo.write("pom.xml", "<a/>\n")
    base = repo.commit("base")
    repo.write("pom.xml", "<b/>\n")
    head = repo.commit("head")

    report = analyze_changes(repo.path, base, head)

    assert report.analysis_level == "method"
    assert report.changed_files[0].java is None


def test_crlf_java_file_keeps_git_line_numbers(repo):
    before = "package p;\r\n\r\nclass A {\r\n    void f() {}\r\n    void g() {}\r\n}\r\n"
    repo.write_bytes(PATH, before.encode())
    base = repo.commit("base")
    repo.write_bytes(PATH, before.replace("void g() {}", "void g() { f(); }").encode())
    head = repo.commit("head")

    java = java_of(analyze_changes(repo.path, base, head))

    assert [(d.id, d.head_lines) for d in java.declarations] == [("p.A#g()", [5, 5])]


def test_demo_repository_names_modified_method_and_added_class(tmp_path):
    dest = tmp_path / "demo"
    output = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "make_demo_repo.py"), str(dest)],
        capture_output=True, text=True, check=True,
    ).stdout
    shas = dict(line.split("=", 1) for line in output.splitlines() if line[:5] in ("BASE=", "HEAD="))

    report = analyze_changes(dest, shas["BASE"], shas["HEAD"])
    calculator = java_of(report, "src/main/java/example/PriceCalculator.java")
    rounding = java_of(report, "src/main/java/example/Rounding.java")

    assert [(d.id, d.change, d.code_changed) for d in calculator.declarations] == [
        ("example.PriceCalculator#applyDiscount(double)", "modified", True)]
    assert ("example.Rounding", "class", "added") in [
        (d.id, d.kind, d.change) for d in rounding.declarations]
    assert report.warnings == []


def test_tree_sitter_version_avoids_known_crash():
    """tree-sitter 0.26.0 crashes (use-after-free) on ordinary files such as
    HikariCP's HikariConfig.java; 0.25.x does not (docs/DECISIONS.md D-033)."""
    from importlib.metadata import version

    major, minor = (int(part) for part in version("tree-sitter").split(".")[:2])
    assert (major, minor) < (0, 26)


def test_deeply_nested_expressions_do_not_exceed_the_recursion_limit():
    # Generated code can chain thousands of operators; this used to raise RecursionError.
    source = ("package a; class Deep { String s = " + " + ".join(['"x"'] * 6000) + "; }").encode()
    result = parse_java(source)
    field = next(d for d in result.declarations if d.id == "a.Deep#s")
    assert field.kind == "field"
