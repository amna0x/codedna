"""Tests for change-impact traversal (Milestone 2)."""

from __future__ import annotations

import json

from codedna.cli import EXIT_OK, main
from codedna.impact_analysis import compute_impact
from codedna.impact_analysis.impact import explanation_graph

CHAIN = {
    "a/Core.java": "package a;\npublic class Core {\n    int value() { return 1; }\n}\n",
    "a/Service.java": "package a;\npublic class Service {\n    Core core;\n}\n",
    "a/Api.java": "package a;\npublic class Api {\n    Service service;\n}\n",
    "a/Unrelated.java": "package a;\npublic class Unrelated {}\n",
    "src/test/java/a/ApiTest.java": "package a;\nclass ApiTest {\n    Api api;\n}\n",
}


def commit_files(repo, files: dict[str, str], message: str) -> str:
    for path, content in files.items():
        repo.write(path, content)
    return repo.commit(message)


def impacted_by_id(report):
    return {node.node: node for node in report.impacted}


def test_transitive_impact_with_explanation_path(repo):
    base = commit_files(repo, CHAIN, "base")
    head = commit_files(repo, {"a/Core.java": CHAIN["a/Core.java"].replace("1", "2")}, "head")

    report = compute_impact(repo.path, base, head)

    assert [s.node for s in report.seeds] == ["type:a.Core"]
    assert report.seeds[0].reasons == ["method a.Core#value() modified"]
    impacted = impacted_by_id(report)
    assert set(impacted) == {"type:a.Service", "type:a.Api", "type:a.ApiTest"}
    assert impacted["type:a.Service"].distance == 1
    api_test = impacted["type:a.ApiTest"]
    assert api_test.distance == 3 and api_test.confidence == "confirmed"
    assert [(s.dependent, s.depends_on) for s in api_test.path] == [
        ("type:a.ApiTest", "type:a.Api"),
        ("type:a.Api", "type:a.Service"),
        ("type:a.Service", "type:a.Core"),
    ]
    assert api_test.path[0].evidence == "src/test/java/a/ApiTest.java:3"
    assert [t["type"] for t in report.candidate_tests] == ["type:a.ApiTest"]
    assert "a/Unrelated.java" not in {f["path"] for f in report.impacted_files}


def test_max_depth_limits_traversal(repo):
    base = commit_files(repo, CHAIN, "base")
    head = commit_files(repo, {"a/Core.java": CHAIN["a/Core.java"].replace("1", "2")}, "head")

    assert set(impacted_by_id(compute_impact(repo.path, base, head, max_depth=1))) == {
        "type:a.Service"}
    assert compute_impact(repo.path, base, head, max_depth=0).impacted == []


def test_heuristic_edges_are_labelled_and_can_be_excluded(repo):
    files = {
        "a/Util.java": "package a;\npublic class Util {\n    public static int f() { return 1; }\n}\n",
        "a/Caller.java": "package a;\nclass Caller {\n    int g() { return Util.f(); }\n}\n",
    }
    base = commit_files(repo, files, "base")
    head = commit_files(repo, {"a/Util.java": files["a/Util.java"].replace("1", "2")}, "head")

    caller = impacted_by_id(compute_impact(repo.path, base, head))["type:a.Caller"]
    assert caller.confidence == "heuristic"
    assert caller.path[0].kind == "static_access"
    assert compute_impact(repo.path, base, head, include_heuristic=False).impacted == []


def test_confirmed_path_is_preferred_over_shorter_heuristic_path(repo):
    files = {
        "a/Util.java": "package a;\npublic class Util {\n    public static int f() { return 1; }\n}\n",
        "a/Mid.java": "package a;\nclass Mid {\n    Util util;\n}\n",
        "a/Top.java": "package a;\nclass Top {\n    Mid mid;\n    int g() { return Util.f(); }\n}\n",
    }
    base = commit_files(repo, files, "base")
    head = commit_files(repo, {"a/Util.java": files["a/Util.java"].replace("1", "2")}, "head")

    top = impacted_by_id(compute_impact(repo.path, base, head))["type:a.Top"]
    assert top.confidence == "confirmed"
    assert top.distance == 2


def test_comment_only_change_has_no_impact(repo):
    base = commit_files(repo, CHAIN, "base")
    head = commit_files(repo, {"a/Core.java": CHAIN["a/Core.java"].replace(
        "    int value()", "    // the value\n    int value()")}, "head")

    report = compute_impact(repo.path, base, head)

    assert report.seeds == [] and report.impacted == []
    assert report.ignored_changes and report.ignored_changes[0]["reason"].startswith("only comments")


def test_deleted_class_impacts_its_former_dependents(repo):
    base = commit_files(repo, CHAIN, "base")
    (repo.path / "a/Core.java").unlink()
    head = commit_files(repo, {"a/Service.java": "package a;\npublic class Service {\n}\n"}, "head")

    report = compute_impact(repo.path, base, head)

    seeds = {s.node: s for s in report.seeds}
    assert seeds["type:a.Core"].in_head is False
    assert "type:a.Service" in seeds
    assert set(impacted_by_id(report)) == {"type:a.Api", "type:a.ApiTest"}


def test_deleted_test_is_not_a_candidate(repo):
    base = commit_files(repo, CHAIN, "base")
    (repo.path / "src/test/java/a/ApiTest.java").unlink()
    head = repo.commit("delete test")

    report = compute_impact(repo.path, base, head)

    assert [s.node for s in report.seeds] == ["type:a.ApiTest"]
    assert report.candidate_tests == []


def test_import_change_seeds_top_level_types(repo):
    files = dict(CHAIN)
    files["x/Money.java"] = "package x;\npublic class Money {}\n"
    base = commit_files(repo, files, "base")
    head = commit_files(repo, {"a/Service.java": "package a;\nimport x.Money;\n"
                               "public class Service {\n    Core core;\n}\n"}, "head")

    report = compute_impact(repo.path, base, head)

    assert [s.node for s in report.seeds] == ["type:a.Service"]
    assert "import changed" in report.seeds[0].reasons[0]


def test_non_java_change_is_reported_as_unanalysed(repo):
    base = commit_files(repo, {**CHAIN, "pom.xml": "<project/>\n"}, "base")
    head = commit_files(repo, {"pom.xml": "<project></project>\n"}, "head")

    report = compute_impact(repo.path, base, head)

    assert report.seeds == []
    assert report.unanalysed_changes == [
        {"path": "pom.xml", "status": "modified", "reason": "non-Java file; impact not analysed"}]
    assert any("not analysed" in w for w in report.warnings)


def test_impact_command_outputs_json(repo, capsys):
    base = commit_files(repo, CHAIN, "base")
    head = commit_files(repo, {"a/Core.java": CHAIN["a/Core.java"].replace("1", "2")}, "head")

    exit_code = main(["impact", "--repo", str(repo.path), "--base", base, "--head", head,
                      "--max-depth", "2", "--confirmed-only"])

    assert exit_code == EXIT_OK
    data = json.loads(capsys.readouterr().out)
    assert data["max_depth"] == 2 and data["include_heuristic"] is False
    assert [n["node"] for n in data["impacted"]] == ["type:a.Service", "type:a.Api"]
    assert data["impacted"][1]["path"][0]["kind"] == "uses"


def test_explanation_graph_links_change_to_test_with_labelled_edges(repo):
    base = commit_files(repo, {**CHAIN, "pom.xml": "<project/>\n"}, "base")
    head = commit_files(repo, {"a/Core.java": CHAIN["a/Core.java"].replace("1", "2"),
                               "pom.xml": "<project></project>\n"}, "head")

    graph = compute_impact(repo.path, base, head).to_dict()["explanation_graph"]

    nodes = {n["id"]: n for n in graph["nodes"]}
    assert nodes["type:a.Core"]["category"] == "changed"
    assert nodes["type:a.Service"]["category"] == "impacted"
    assert nodes["type:a.ApiTest"]["category"] == "test"
    assert nodes["file:pom.xml"]["confidence"] == "unresolved"
    assert nodes["type:a.ApiTest"]["path_edges"] == [
        "type:a.ApiTest->type:a.Api:uses", "type:a.Api->type:a.Service:uses",
        "type:a.Service->type:a.Core:uses"]
    assert {e["confidence"] for e in graph["edges"]} <= {"confirmed", "heuristic"}
    assert all(e["source"] in nodes and e["target"] in nodes for e in graph["edges"])
    assert "type:a.Unrelated" not in nodes


def test_explanation_graph_keeps_edges_of_different_kinds_apart():
    step = lambda kind, confidence: {"dependent": "type:x.A", "depends_on": "type:x.B",
                                     "kind": kind, "confidence": confidence, "evidence": "A.java:1"}
    report = {"candidate_tests": [], "unanalysed_changes": [],
              "seeds": [{"node": "type:x.B", "file": "B.java", "reasons": ["changed"]}],
              "impacted": [
                  {"node": "type:x.A", "file": "A.java", "confidence": "confirmed", "distance": 1,
                   "seed": "type:x.B", "path": [step("extends", "confirmed")]},
                  {"node": "type:x.C", "file": "C.java", "confidence": "heuristic", "distance": 2,
                   "seed": "type:x.B", "path": [
                       {"dependent": "type:x.C", "depends_on": "type:x.A", "kind": "uses",
                        "confidence": "heuristic", "evidence": "C.java:3"},
                       step("same_package", "heuristic")]}]}

    graph = explanation_graph(report)

    edges = {e["id"]: e for e in graph["edges"]}
    assert edges["type:x.A->type:x.B:extends"]["confidence"] == "confirmed"
    assert edges["type:x.A->type:x.B:same_package"]["confidence"] == "heuristic"
    nodes = {n["id"]: n for n in graph["nodes"]}
    assert nodes["type:x.C"]["path_edges"][-1] == "type:x.A->type:x.B:same_package"
