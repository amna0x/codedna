"""The agent brake demo talks to a real `codedna mcp` process over stdio (no build)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

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
