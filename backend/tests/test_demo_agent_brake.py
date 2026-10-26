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


def test_end_to_end_demo_plans_part_of_the_suite_on_validated_history(tmp_path):
    spec = importlib.util.spec_from_file_location("demo_brake_end_to_end",
                                                  ROOT / "scripts/demo_brake_end_to_end.py")
    e2e = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e2e)
    result = e2e.run_demo(tmp_path / "demo", run_check=False, mvn=None)
    for key in ("breaking_plan", "harmless_plan"):
        plan = result[key]
        assert plan["risk"]["status"] == "validated_history" and plan["risk"]["method"] == "crc"
        assert plan["must_run"] == ["example.PriceCalculatorTest"]
        assert plan["skipped"] == ["example.OrderServiceTest"]
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
