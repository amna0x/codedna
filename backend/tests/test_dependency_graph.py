"""Tests for the code graph builder (Milestone 2)."""

from __future__ import annotations

import json

import pytest

from codedna.cli import EXIT_ANALYSIS_ERROR, EXIT_OK, main
from codedna.dependency_graph import CONFIRMED, HEURISTIC, build_graph, file_role
from codedna.git_analysis import InvalidCommitError


def dependency_edges(graph):
    return {(e.source, e.target, e.kind): e for e in graph.edges.values() if e.kind != "contains"}


def build(repo, files: dict[str, str], **kwargs):
    for path, content in files.items():
        repo.write(path, content)
    repo.commit("snapshot")
    return build_graph(repo.path, "HEAD", **kwargs)


# --- structure ---------------------------------------------------------------


def test_nodes_have_stable_ids_and_contains_edges(repo):
    graph = build(repo, {
        "src/main/java/shop/Order.java":
            "package shop;\n\npublic class Order {\n    int qty;\n    Order() {}\n"
            "    int total(int price) { return price * qty; }\n    static class Line {}\n}\n",
    })

    assert graph.nodes["package:shop"].kind == "package"
    file_node = graph.nodes["file:src/main/java/shop/Order.java"]
    assert (file_node.parent, file_node.role) == ("package:shop", "main")
    order = graph.nodes["type:shop.Order"]
    assert (order.kind, order.lines, order.parent) == ("class", [3, 8], file_node.id)
    assert graph.nodes["type:shop.Order.Line"].parent == "type:shop.Order"
    assert graph.nodes["member:shop.Order#total(int)"].kind == "method"
    assert graph.nodes["member:shop.Order#<init>()"].kind == "constructor"
    assert graph.nodes["member:shop.Order#qty"].kind == "field"
    contains = {(e.source, e.target) for e in graph.edges.values() if e.kind == "contains"}
    assert ("package:shop", file_node.id) in contains
    assert (file_node.id, "type:shop.Order") in contains
    assert ("type:shop.Order", "type:shop.Order.Line") in contains
    assert ("type:shop.Order", "member:shop.Order#total(int)") in contains
    assert all(e.confidence == CONFIRMED for e in graph.edges.values() if e.kind == "contains")


def test_no_members_option_keeps_only_types(repo):
    graph = build(repo, {"A.java": "class A { void f() {} int x; }\n"}, include_members=False)

    assert "type:A" in graph.nodes
    assert not any(node_id.startswith("member:") for node_id in graph.nodes)


def test_non_java_files_are_ignored_and_default_package_works(repo):
    graph = build(repo, {"pom.xml": "<project/>\n", "A.java": "class A {}\n"})

    assert set(graph.nodes) == {"package:", "file:A.java", "type:A"}
    assert graph.nodes["package:"].label == "(default package)"


@pytest.mark.parametrize("path,role", [
    ("src/test/java/a/FooTest.java", "test"),
    ("src/main/java/a/Foo.java", "main"),
    ("module/src/test/java/a/Helper.java", "test"),
    ("src/main/java/a/FooIT.java", "test"),
    ("src/main/java/a/Testimony.java", "test"),  # path convention is only a heuristic
])
def test_file_role_uses_path_conventions(path, role):
    assert file_role(path) == role


# --- dependency edges ----------------------------------------------------------


def test_same_package_use_is_confirmed_with_evidence(repo):
    graph = build(repo, {
        "a/Price.java": "package a;\npublic class Price {}\n",
        "a/Order.java": "package a;\nclass Order {\n    Price price;\n    Price get() { return price; }\n}\n",
    })

    edge = dependency_edges(graph)[("type:a.Order", "type:a.Price", "uses")]
    assert edge.confidence == CONFIRMED
    assert edge.evidence_count == 2
    assert sorted(e.line for e in edge.evidence) == [3, 4]
    assert edge.evidence[0].file == "a/Order.java"


def test_extends_and_implements_edges(repo):
    graph = build(repo, {
        "a/Base.java": "package a;\npublic abstract class Base {}\n",
        "a/Shape.java": "package a;\npublic interface Shape {}\n",
        "a/Named.java": "package a;\npublic interface Named extends Shape {}\n",
        "a/Box.java": "package a;\nclass Box extends Base implements Named {}\n",
    })

    edges = dependency_edges(graph)
    assert edges[("type:a.Box", "type:a.Base", "extends")].confidence == CONFIRMED
    assert edges[("type:a.Box", "type:a.Named", "implements")].confidence == CONFIRMED
    assert edges[("type:a.Named", "type:a.Shape", "extends")].confidence == CONFIRMED


def test_generic_arguments_in_extends_are_uses(repo):
    graph = build(repo, {
        "a/Base.java": "package a;\npublic class Base<T> {}\n",
        "a/Item.java": "package a;\npublic class Item {}\n",
        "a/Box.java": "package a;\nclass Box extends Base<Item> {}\n",
    })

    edges = dependency_edges(graph)
    assert ("type:a.Box", "type:a.Base", "extends") in edges
    assert ("type:a.Box", "type:a.Item", "uses") in edges
    assert ("type:a.Box", "type:a.Item", "extends") not in edges


def test_single_type_import_from_other_package(repo):
    graph = build(repo, {
        "x/Money.java": "package x;\npublic class Money {}\n",
        "a/Order.java": "package a;\nimport x.Money;\nimport java.util.List;\n"
                        "class Order { Money m; List<Money> all; }\n",
    })

    edges = dependency_edges(graph)
    assert edges[("type:a.Order", "type:x.Money", "imports")].confidence == CONFIRMED
    assert edges[("type:a.Order", "type:x.Money", "uses")].evidence[0].note == "single-type import"
    assert graph.unresolved == {}
    assert graph.external_reference_count >= 2  # the java.util.List import and its use


def test_import_resolution_wins_over_same_package(repo):
    graph = build(repo, {
        "a/Money.java": "package a;\npublic class Money {}\n",
        "x/Money.java": "package x;\npublic class Money {}\n",
        "a/Order.java": "package a;\nimport x.Money;\nclass Order { Money m; }\n",
    })

    edges = dependency_edges(graph)
    assert ("type:a.Order", "type:x.Money", "uses") in edges
    assert ("type:a.Order", "type:a.Money", "uses") not in edges


def test_static_import_creates_import_edge(repo):
    graph = build(repo, {
        "x/MathUtil.java": "package x;\npublic class MathUtil { public static int twice(int v) { return 2 * v; } }\n",
        "a/Calc.java": "package a;\nimport static x.MathUtil.twice;\nclass Calc { int f() { return twice(2); } }\n",
    })

    edge = dependency_edges(graph)[("type:a.Calc", "type:x.MathUtil", "imports")]
    assert edge.evidence[0].note == "static import"


def test_unknown_names_are_unresolved_not_edges(repo):
    graph = build(repo, {"a/Order.java": "package a;\nclass Order { Mystery m; String s; }\n"})

    assert dependency_edges(graph) == {}
    unresolved = graph.unresolved[("type:a.Order", "Mystery")]
    assert unresolved.line == 2
    assert "not declared in repository" in unresolved.reason
    assert ("type:a.Order", "String") not in graph.unresolved  # java.lang is implicit
    assert graph.stats()["unresolved_references"] == 1


def test_static_access_is_heuristic(repo):
    graph = build(repo, {
        "a/Rounding.java": "package a;\npublic class Rounding { public static double cents(double v) { return v; } }\n",
        "a/Price.java": "package a;\nclass Price { double f(double v) { return Rounding.cents(v); } }\n",
    })

    edge = dependency_edges(graph)[("type:a.Price", "type:a.Rounding", "static_access")]
    assert edge.confidence == HEURISTIC
    assert "assumed" in edge.evidence[0].note


def test_wildcard_import_resolution_is_heuristic(repo):
    graph = build(repo, {
        "x/Money.java": "package x;\npublic class Money {}\n",
        "a/Order.java": "package a;\nimport x.*;\nclass Order { Money m; }\n",
    })

    edge = dependency_edges(graph)[("type:a.Order", "type:x.Money", "uses")]
    assert edge.confidence == HEURISTIC
    assert "wildcard" in edge.evidence[0].note


def test_var_and_all_java_lang_names_are_not_unresolved(repo):
    graph = build(repo, {"a/Job.java": (
        "package a;\nclass Job { void run() throws ClassNotFoundException {\n"
        "  var n = 1; AbstractMethodError e = null; } }\n")})

    assert graph.unresolved == {}
    assert graph.stats()["unresolved_references"] == 0


def test_static_imports_bring_member_types(repo):
    graph = build(repo, {
        "u/Elf.java": "package u;\npublic class Elf { public static class Policy {}\n"
                      "  public static class Factory {} }\n",
        "a/Pool.java": "package a;\nimport static u.Elf.*;\nclass Pool { Policy p; }\n",
        "a/Other.java": "package a;\nimport static u.Elf.Factory;\nclass Other { Factory f; }\n",
    })

    edges = dependency_edges(graph)
    on_demand = edges[("type:a.Pool", "type:u.Elf.Policy", "uses")]
    assert on_demand.confidence == HEURISTIC and "wildcard" in on_demand.evidence[0].note
    single = edges[("type:a.Other", "type:u.Elf.Factory", "uses")]
    assert single.confidence == CONFIRMED and single.evidence[0].note == "single static import"
    assert graph.unresolved == {}


def test_library_static_import_makes_same_package_type_heuristic(repo):
    graph = build(repo, {
        "p/Entry.java": "package p;\npublic class Entry {}\n",
        "p/Use.java": "package p;\nimport static java.util.Map.Entry;\nclass Use { Entry e; }\n",
    })
    edge = dependency_edges(graph)[("type:p.Use", "type:p.Entry", "uses")]
    assert edge.confidence == HEURISTIC and "may shadow" in edge.evidence[0].note


def test_post_java8_lang_names_prefer_a_wildcard_imported_repository_type(repo):
    graph = build(repo, {
        "m/Record.java": "package m;\npublic class Record {}\n",
        "m/Thread.java": "package m;\npublic class Thread {}\n",
        "a/Use.java": "package a;\nimport m.*;\nclass Use { Record r; Thread t; }\n",
    })
    edges = dependency_edges(graph)
    record = edges[("type:a.Use", "type:m.Record", "uses")]
    assert record.confidence == HEURISTIC and "Java 9+" in record.evidence[0].note
    # Thread is in java.lang on every JDK: with m.* too, javac reports an ambiguity,
    # so compiling code cannot mean m.Thread here; it stays external.
    assert ("type:a.Use", "type:m.Thread", "uses") not in edges


def test_member_types_inherited_from_supertypes(repo):
    graph = build(repo, {
        "a/Base.java": "package a;\nabstract class Base { static class Failure extends Exception {} }\n",
        "a/Mid.java": "package a;\nabstract class Mid extends Base {}\n",
        "a/Pool.java": "package a;\nclass Pool extends Mid { Failure f; }\n",
        "a/Rules.java": "package a;\npublic interface Rules { enum Override { KEEP } }\n",
        "a/Handler.java": "package a;\nclass Handler implements Rules {\n"
                          "  @java.lang.Override public String toString() { return \"\"; }\n"
                          "  Override pick() { return Override.KEEP; } }\n",
    })

    edges = dependency_edges(graph)
    inherited = edges[("type:a.Pool", "type:a.Base.Failure", "uses")]
    assert inherited.confidence == HEURISTIC
    assert inherited.evidence[0].note == "member type inherited from a.Base"
    # The inherited enum shadows java.lang.Override, as in Java.
    assert ("type:a.Handler", "type:a.Rules.Override", "uses") in edges
    assert graph.unresolved == {}


def test_supertype_cycles_do_not_loop(repo):
    graph = build(repo, {"a/A.java": "package a;\nclass A extends B { Inner i; }\n",
                         "a/B.java": "package a;\nclass B extends A {}\n"})

    assert ("type:a.A", "Inner") in graph.unresolved


def test_type_parameters_are_not_references(repo):
    graph = build(repo, {
        "a/T.java": "package a;\npublic class T {}\n",
        "a/Box.java": "package a;\nclass Box<T> { T value; <U> U get(U u) { return u; } }\n",
    })

    assert dependency_edges(graph) == {}
    assert graph.unresolved == {}


def test_nested_types_resolve_by_simple_and_qualified_name(repo):
    graph = build(repo, {
        "a/Outer.java": "package a;\npublic class Outer {\n    public static class Inner {}\n"
                        "    Inner make() { return new Inner(); }\n}\n",
        "a/User.java": "package a;\nclass User { Outer.Inner inner; a.Outer outer; }\n",
    })

    edges = dependency_edges(graph)
    assert edges[("type:a.Outer", "type:a.Outer.Inner", "uses")].confidence == CONFIRMED
    assert edges[("type:a.User", "type:a.Outer.Inner", "uses")].confidence == CONFIRMED
    assert edges[("type:a.User", "type:a.Outer", "uses")].confidence == CONFIRMED


def test_local_class_inside_method_belongs_to_enclosing_type(repo):
    graph = build(repo, {
        "a/Base.java": "package a;\npublic class Base {}\n",
        "a/Host.java": "package a;\nclass Host { void f() { class Local extends Base {} } }\n",
    })

    assert not any("Local" in node_id for node_id in graph.nodes)
    assert ("type:a.Host", "type:a.Base", "uses") in dependency_edges(graph)


def test_self_references_are_skipped(repo):
    graph = build(repo, {"a/Node.java": "package a;\nclass Node { Node next; }\n"})

    assert dependency_edges(graph) == {}


def test_duplicate_type_names_make_edges_heuristic(repo):
    graph = build(repo, {
        "one/a/Dup.java": "package a;\npublic class Dup {}\n",
        "two/a/Dup.java": "package a;\npublic class Dup {}\n",
        "one/a/User.java": "package a;\nclass User { Dup d; }\n",
    })

    assert dependency_edges(graph)[("type:a.User", "type:a.Dup", "uses")].confidence == HEURISTIC
    assert any("declared in 2 files" in w for w in graph.warnings)


def test_syntax_errors_are_flagged_and_edges_heuristic(repo):
    graph = build(repo, {
        "a/Price.java": "package a;\npublic class Price {}\n",
        "a/Broken.java": "package a;\nclass Broken { Price p; void f( { }\n",
    })

    assert graph.nodes["file:a/Broken.java"].has_syntax_errors is True
    assert any("syntax errors in a/Broken.java" in w for w in graph.warnings)
    assert dependency_edges(graph)[("type:a.Broken", "type:a.Price", "uses")].confidence == HEURISTIC


def test_graph_of_older_revision_uses_same_ids(repo):
    repo.write("a/A.java", "package a;\nclass A {}\n")
    first = repo.commit("one")
    repo.write("a/B.java", "package a;\nclass B { A a; }\n")
    repo.commit("two")

    old = build_graph(repo.path, first)
    new = build_graph(repo.path, "HEAD")

    assert "type:a.A" in old.nodes and "type:a.B" not in old.nodes
    assert ("type:a.B", "type:a.A", "uses") in dependency_edges(new)


def test_invalid_revision_is_rejected(repo):
    repo.write("A.java", "class A {}\n")
    repo.commit("one")
    with pytest.raises(InvalidCommitError):
        build_graph(repo.path, "nope")


# --- CLI -------------------------------------------------------------------------


def test_graph_command_exports_json(repo, capsys):
    repo.write("a/Price.java", "package a;\npublic class Price {}\n")
    repo.write("a/Order.java", "package a;\nclass Order { Price p; void f() {} }\n")
    repo.commit("one")

    assert main(["graph", "--repo", str(repo.path), "--no-members"]) == EXIT_OK
    data = json.loads(capsys.readouterr().out)

    assert {n["id"] for n in data["nodes"]} == {
        "package:a", "file:a/Order.java", "file:a/Price.java", "type:a.Order", "type:a.Price"}
    uses = [e for e in data["edges"] if e["kind"] == "uses"]
    assert uses[0]["source"] == "type:a.Order" and uses[0]["confidence"] == "confirmed"
    assert data["stats"]["edges"]["uses"] == {"confirmed": 1, "heuristic": 0}
    assert data["unresolved"] == [] and data["warnings"] == []


def test_graph_command_reports_bad_revision(repo, capsys):
    repo.write("A.java", "class A {}\n")
    repo.commit("one")

    assert main(["graph", "--repo", str(repo.path), "--rev", "nope"]) == EXIT_ANALYSIS_ERROR
    assert "unknown commit" in capsys.readouterr().err
