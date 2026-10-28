"""The agent brake demo talks to a real `codedna mcp` process over stdio (no build)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load():
    spec = importlib.util.spec_from_file_location("demo_agent_brake",
                                                  ROOT / "scripts/demo_agent_brake.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_demo_plans_tests_for_the_agents_edit_without_building(tmp_path):
    demo = load()
    result = demo.run_demo(tmp_path / "demo", check=False, mvn=None)
    assert result["tools"] == ["codedna_plan_tests", "codedna_impact"]  # no build consent
    assert result["plan"]["must_run"] == ["example.OrderServiceTest", "example.PriceCalculatorTest"]
    assert {t["type"] for t in result["linked_tests"]} == {
        "type:example.OrderServiceTest", "type:example.PriceCalculatorTest"}
    edited = (tmp_path / "demo/src/main/java/example/PriceCalculator.java").read_text()
    assert demo.WRONG in edited



def test_demo_ignores_editor_build_output_but_keeps_real_resource_changes(tmp_path):
    from codedna.git_analysis import extract_changes

    demo = load()
    project = tmp_path / "demo"
    demo.make_repo(project)
    compiled = project / "target/classes/example/PriceCalculator.class"
    compiled.parent.mkdir(parents=True)
    compiled.write_bytes(b"\xca\xfe\xba\xbe editor output")
    resource = project / "src/main/resources/settings.json"
    resource.parent.mkdir(parents=True)
    resource.write_text('{"discount": 0.2}', encoding="utf-8")
    report = extract_changes(project, "HEAD", "WORKTREE")
    assert {item.path for item in report.changed_files} == {
        "src/main/java/example/PriceCalculator.java", "src/main/resources/settings.json"}


def test_end_to_end_demo_plans_part_of_the_suite_on_validated_history(tmp_path):
    spec = importlib.util.spec_from_file_location("demo_brake_end_to_end",
                                                  ROOT / "scripts/demo_brake_end_to_end.py")
    e2e = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e2e)
    result = e2e.run_demo(tmp_path / "demo", run_check=False, mvn=None)
    for key in ("breaking_plan", "harmless_plan"):
        plan = result[key]
        assert plan["risk"]["status"] == "validated_history" and plan["risk"]["method"] == "crc"
        expected = ({"example.PriceCalculatorTest", "example.OrderServiceTest"}
                    if key == "breaking_plan" else {"example.PriceCalculatorTest"})
        assert set(plan["must_run"]) == expected
        assert set(plan["skipped"]) == set(e2e.TESTS) - expected
        assert "example.IndependentTest" in plan["skipped"]
        assert 0 < len(plan["must_run"]) < plan["total_tests"] == 3
        assert {item["test"] for item in plan["structural_plan"]["selected"]} <= expected
        assert plan["risk"]["conformal"]["corrected_bound"] <= 0.05


@pytest.mark.maven
def test_end_to_end_demo_blocks_the_breaking_edit_and_passes_the_harmless_one(tmp_path):
    spec = importlib.util.spec_from_file_location("demo_brake_end_to_end",
                                                  ROOT / "scripts/demo_brake_end_to_end.py")
    e2e = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e2e)
    result = e2e.run_demo(tmp_path / "demo", run_check=True, mvn=None)
    assert result["breaking_check"]["verdict"] == "blocked"
    assert result["breaking_check"]["failed"] == ["example.PriceCalculatorTest"]
    assert result["harmless_check"]["verdict"] == "passed"
