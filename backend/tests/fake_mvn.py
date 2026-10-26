"""Stand-in for ``mvn`` used by the runner tests (no Maven or Java needed).

It reads a JSON spec from the file named in ``CODEDNA_FAKE_MVN_SPEC``::

    {"exit_code": 0,
     "tests": {"a.ATest": {"status": "passed", "time": 0.5,
                           "cases": ["t1"],
                           "classes": ["a/A"],
                           "lines": {"a/A.java": [3, 4]}}}}

and writes the Surefire and JaCoCo files a real Maven run would produce in
``target/``. With ``-Dtest=ID,...`` only that test is "run"; JaCoCo output is
written only when the jacoco ``report`` goal is requested. Every invocation is
appended to ``target/fake-mvn-calls.txt``.
"""

import json
import os
import sys
from pathlib import Path

spec = json.loads(Path(os.environ["CODEDNA_FAKE_MVN_SPEC"]).read_text(encoding="utf-8"))
args = sys.argv[1:]
target = Path("target")
target.mkdir(exist_ok=True)
with open(target / "fake-mvn-calls.txt", "a", encoding="utf-8") as calls:
    calls.write(" ".join(args) + "\n")

selected = None
for arg in args:
    if arg.startswith("-Dtest="):
        selected = arg.removeprefix("-Dtest=").split(",")
tests = {k: v for k, v in spec["tests"].items() if selected is None or k in selected}

reports = target / "surefire-reports"
reports.mkdir(parents=True, exist_ok=True)
for test_id, info in tests.items():
    cases = []
    for name in info.get("cases", ["test"]):
        body = ""
        if info["status"] == "failed":
            body = '<failure message="boom" type="AssertionError">trace</failure>'
        elif info["status"] == "skipped":
            body = "<skipped/>"
        cases.append(f'<testcase name="{name}" classname="{test_id}" time="{info["time"]}">'
                     f"{body}</testcase>")
    (reports / f"TEST-{test_id}.xml").write_text(
        f'<?xml version="1.0"?><testsuite name="{test_id}">{"".join(cases)}</testsuite>',
        encoding="utf-8")

if any(arg.endswith(":report") for arg in args):
    packages: dict[str, list[str]] = {}
    for info in tests.values():
        for class_name in info.get("classes", []):
            package = class_name.rsplit("/", 1)[0]
            packages.setdefault(package, []).append(
                f'<class name="{class_name}" sourcefilename="x.java">'
                '<counter type="INSTRUCTION" missed="0" covered="5"/></class>')
        for source, lines in info.get("lines", {}).items():
            package, name = source.rsplit("/", 1)
            line_xml = "".join(f'<line nr="{n}" mi="0" ci="2" mb="0" cb="0"/>' for n in lines)
            packages.setdefault(package, []).append(
                f'<sourcefile name="{name}">{line_xml}</sourcefile>')
    site = target / "site" / "jacoco"
    site.mkdir(parents=True, exist_ok=True)
    body = "".join(f'<package name="{p}">{"".join(items)}</package>' for p, items in packages.items())
    (site / "jacoco.xml").write_text(f'<report name="fake">{body}</report>', encoding="utf-8")

sys.exit(spec.get("exit_code", 0))
