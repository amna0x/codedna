"""The PR demonstration analyses a real temporary Git repository without building it."""
import importlib.util
import json
from pathlib import Path


def test_pr_demo_saves_an_unvalidated_full_plan_without_running_builds(repo):
    repo.write("pyproject.toml", '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n')
    repo.write("tests/test_demo.py", "def test_ok():\n    assert True\n")
    base = repo.commit("base")
    repo.write("tests/test_demo.py", "def test_ok():\n    assert False\n")
    head = repo.commit("unexecuted change")
    script = Path(__file__).resolve().parents[2] / "scripts/pr_demo.py"
    spec = importlib.util.spec_from_file_location("pr_demo", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = repo.path.parent / "pr-demo-report"
    planned = module.write_report(repo.path, base, head, output)
    assert planned["risk"]["status"] == "unvalidated"
    assert planned["must_run"] == ["py:tests.test_demo"]
    assert json.loads((output / "plan.json").read_text()) == planned
    assert "Project tests have not been executed" in (output / "summary.md").read_text()
    assert not (repo.path / ".codedna/runs").exists()
    assert repo.git("status", "--porcelain") == ""
