"""End-to-end demo of the agent brake on validated history (D-059, D-068), over MCP stdio.

``demo_agent_brake.py`` shows the day-one path: no project history, so the
brake asks for the whole suite. This demo shows the other path. It builds a
throwaway copy of ``examples/sample-java-project`` with 240 earlier commits
and a **synthetic** recorded history (``.codedna/history.csv``) in which
``PriceCalculatorTest`` fails on three commits in five and
``OrderServiceTest`` and a genuinely unrelated ``IndependentTest`` never fail.
The structural plan still requires OrderServiceTest for the breaking edit;
IndependentTest lets the demo show partial selection without dropping it. Then, as an agent would, it asks
``codedna mcp`` for a plan with the conformal stop (``method: crc``) and runs
``codedna_check`` twice:

1. a wrong discount formula (breaks ``PriceCalculatorTest``) -> ``blocked``;
2. a harmless comment in ``OrderService`` -> ``passed``.

The history is invented to exercise the mechanism; the numbers it prints say
nothing about real projects. ``--check`` runs Maven on the demo repository
(needs a JDK and Maven); without it only the plans are shown.

Usage (from the repository root):
    python scripts/demo_brake_end_to_end.py DEST_DIR [--check] [--mvn PATH]
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMITS = 240
TESTS = ("example.IndependentTest", "example.OrderServiceTest", "example.PriceCalculatorTest")
INDEPENDENT_TEST = """package example;
import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;
class IndependentTest {
    @Test void shippingThresholdIsIndependentOfDiscounts() {
        assertEquals(500, ShippingCalculator.feeCents(1000));
        assertEquals(0, ShippingCalculator.feeCents(6000));
    }
}
"""
SHIPPING_COMPONENT = """package example;
final class ShippingCalculator {
    static int feeCents(int subtotalCents) { return subtotalCents >= 5000 ? 0 : 500; }
}
"""


def _load_demo():
    spec = importlib.util.spec_from_file_location("demo_agent_brake",
                                                  ROOT / "scripts" / "demo_agent_brake.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


demo = _load_demo()


def fails(test: str, index: int) -> bool:
    return test.endswith("PriceCalculatorTest") and index % 5 < 3


def make_history(repo: Path) -> Path:
    """240 empty first-parent commits, then a history CSV whose features use prior rows only."""
    from codedna.git_analysis.git import run_git, run_git_bytes
    from codedna.test_history.features import NEVER, Dataset, Row
    from codedna.test_history.recording import ignore_outputs
    from codedna_java.live import LIVE_FEATURES

    branch = run_git(repo, "symbolic-ref", "--short", "HEAD").strip()
    first = run_git(repo, "rev-parse", "HEAD").strip()
    stream = []
    for i in range(1, COMMITS + 1):
        parent = first if i == 1 else f":{i - 1}"
        stream.append(f"commit refs/heads/{branch}\nmark :{i}\ncommitter CodeDNA Demo "
                      f"<demo@example.invalid> {1700000000 + i} +0000\ndata 13\nearlier work\n"
                      f"from {parent}\n\n")
    run_git_bytes(repo, "fast-import", "--quiet", stdin="".join(stream).encode())
    shas = run_git(repo, "rev-list", "--first-parent", "--reverse", "HEAD").split()
    rows = []
    for i, sha in enumerate(shas):
        for test in TESTS:
            past = [fails(test, j) for j in range(i)]
            features = {name: 0.0 for name in LIVE_FEATURES}
            last_failure = max((j for j, failed in enumerate(past) if failed), default=None)
            features.update(
                past_runs=float(i), past_failures=float(sum(past)),
                failure_rate=sum(past) / i if i else 0.0,
                recent_failures=float(sum(past[-5:])),
                failed_last_run=float(past[-1]) if past else 0.0,
                commits_since_failure=float(i - last_failure) if last_failure is not None else NEVER,
                mean_duration=1.0, last_duration=1.0 if i else 0.0)
            rows.append(Row(sha, i, test, int(fails(test, i)), 1.0, features))
    ignore_outputs(repo)
    path = repo / ".codedna" / "history.csv"
    Dataset(rows, list(LIVE_FEATURES), shas).to_csv(path)
    return path


def edit(repo: Path, relative: str, old: str, new: str) -> None:
    source = repo / relative
    text = source.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"the sample project changed; update the demo edit in {relative}")
    with open(source, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.replace(old, new, 1))


def show_plan(client, label: str) -> dict:
    answer = client.request("tools/call", {"name": "codedna_plan_tests",
                                           "arguments": {"method": "crc"}})
    planned = answer["structuredContent"]
    risk = planned["risk"]
    print(f"\n[{label}] plan ({risk['status']}, method {risk['method']}): {planned['summary']}")
    for test in planned["must_run"]:
        print(f"  run  {test}")
    for test in planned["skipped"]:
        print(f"  skip {test}")
    return planned


def check(client, label: str) -> dict:
    answer = client.request("tools/call", {"name": "codedna_check", "arguments": {"method": "crc"}})
    verdict = answer["structuredContent"]
    print(f"[{label}] check: {verdict.get('verdict', 'error')}: "
          f"{verdict.get('message', verdict.get('error'))}")
    return verdict


def run_demo(dest: Path, run_check: bool, mvn: str | None) -> dict:
    demo.make_repo(dest)  # copies the sample, commits it, leaves the wrong formula uncommitted
    wrong = dest / "src/main/java/example/PriceCalculator.java"
    edited = wrong.read_text(encoding="utf-8")
    subprocess.run(["git", *demo.IDENTITY, "checkout", "--quiet", "--", str(wrong)],
                   cwd=dest, check=True)  # park the agent's edit while history is built
    # Add a real unrelated test before generating its synthetic history.
    # Never omit a dependency test merely to make the plan look partial.
    from codedna.git_analysis.git import run_git
    independent = "src/test/java/example/IndependentTest.java"
    (dest / independent).write_text(INDEPENDENT_TEST, encoding="utf-8", newline="\n")
    shipping = "src/main/java/example/ShippingCalculator.java"
    (dest / shipping).write_text(SHIPPING_COMPONENT, encoding="utf-8", newline="\n")
    run_git(dest, "add", "--", independent, shipping)
    run_git(dest, *demo.IDENTITY, "commit", "--quiet", "-m", "add independent demo test")
    make_history(dest)
    with open(wrong, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(edited)
    print(f"demo repository: {dest} ({COMMITS} synthetic commits plus setup; SYNTHETIC history)")
    command = [sys.executable, "-m", "codedna", "mcp", "--repo", str(dest)]
    if run_check:
        command.append("--allow-build")
    if mvn:
        command += ["--mvn", mvn]
    client = demo.Client(command)
    result: dict = {}
    try:
        client.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                      "clientInfo": {"name": "codedna-demo", "version": "1"}})
        client.notify("notifications/initialized")
        result["breaking_plan"] = show_plan(client, "wrong discount formula")
        if run_check:
            result["breaking_check"] = check(client, "wrong discount formula")
        subprocess.run(["git", *demo.IDENTITY, "checkout", "--quiet", "--", str(wrong)],
                       cwd=dest, check=True)
        edit(dest, "src/main/java/example/OrderService.java", "public class OrderService",
             "// Agent's harmless edit: a comment.\npublic class OrderService")
        result["harmless_plan"] = show_plan(client, "harmless comment")
        if run_check:
            result["harmless_check"] = check(client, "harmless comment")
    finally:
        client.close()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dest", type=Path, help="new, empty folder for the demo repository")
    parser.add_argument("--check", action="store_true",
                        help="also run the planned tests with Maven (executes the demo project)")
    parser.add_argument("--mvn", help="Maven executable, if not on PATH")
    args = parser.parse_args(argv)
    if args.check and not (args.mvn or shutil.which("mvn")):
        parser.error("--check needs Maven on PATH or --mvn PATH")
    result = run_demo(args.dest, args.check, args.mvn)
    plans = (result["breaking_plan"], result["harmless_plan"])
    ok = all(p["risk"]["status"] == "validated_history" and p["skipped"] for p in plans)
    if args.check:
        ok = ok and result["breaking_check"].get("verdict") == "blocked" \
            and result["harmless_check"].get("verdict") == "passed"
    print("\nend-to-end result:", "as expected" if ok else "NOT as expected")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
