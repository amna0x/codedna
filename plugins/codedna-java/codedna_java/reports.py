"""Parsers for Maven Surefire and JaCoCo XML reports.

Both formats are produced by build tools on the analysed project, so the
parsers are defensive: unknown elements are ignored, malformed files raise
``ReportError`` with the file name. ``xml.etree`` does not fetch external
DTDs (JaCoCo's ``report.dtd``) or expand external entities.
"""

from __future__ import annotations

import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass, field
from pathlib import Path

from codedna.test_mapping.results import (
    ERROR,
    FAILED,
    PASSED,
    SKIPPED,
    ReportError,
    TestCaseResult,
    TestClassResult,
)


def top_level_class(binary_name: str) -> str:
    """``example.Outer$Inner`` -> ``example.Outer``."""
    return binary_name.split("$", 1)[0]


def parse_surefire_reports(directory: Path) -> dict[str, TestClassResult]:
    """Read every ``TEST-*.xml`` in a Surefire reports directory."""
    results: dict[str, TestClassResult] = {}
    for report in sorted(directory.glob("TEST-*.xml")):
        for case_class, case in _parse_surefire_file(report):
            test_id = top_level_class(case_class)
            results.setdefault(test_id, TestClassResult(test_id)).add(case)
    return results


def _parse_surefire_file(path: Path) -> list[tuple[str, TestCaseResult]]:
    root = _parse_xml(path)
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    cases = []
    for suite in suites:
        for element in suite.findall("testcase"):
            class_name = element.get("classname") or suite.get("name") or ""
            name = element.get("name") or ""
            nested = class_name.split("$", 1)[1].replace("$", ".") if "$" in class_name else ""
            status, message = PASSED, None
            for child, child_status in (("error", ERROR), ("failure", FAILED), ("skipped", SKIPPED)):
                found = element.find(child)
                if found is not None:
                    status, message = child_status, found.get("message")
                    break
            cases.append((class_name, TestCaseResult(
                name=f"{nested}.{name}" if nested else name,
                status=status, time=_float(element.get("time")), message=message,
            )))
    return cases


@dataclass
class JacocoCoverage:
    # Type IDs (dotted, nested types joined with ".") with covered instructions.
    covered_types: set[str] = field(default_factory=set)
    # (package path with "/", source file name) -> covered line numbers.
    covered_lines: dict[tuple[str, str], set[int]] = field(default_factory=dict)


def parse_jacoco_report(path: Path) -> JacocoCoverage:
    root = _parse_xml(path)
    coverage = JacocoCoverage()
    for package in root.iter("package"):
        package_name = package.get("name") or ""
        for class_element in package.findall("class"):
            if _covered(class_element, "INSTRUCTION"):
                coverage.covered_types.add(jvm_class_to_type_id(class_element.get("name") or ""))
        for source in package.findall("sourcefile"):
            lines = {int(line.get("nr", "0")) for line in source.findall("line")
                     if int(line.get("ci", "0")) > 0}
            if lines:
                coverage.covered_lines[(package_name, source.get("name") or "")] = lines
    return coverage


def jvm_class_to_type_id(name: str) -> str:
    """``example/Outer$Inner$1`` -> ``example.Outer.Inner`` (anonymous classes dropped)."""
    head, *nested = name.replace("/", ".").split("$")
    named = []
    for part in nested:
        # Anonymous (Outer$1) and local (Outer$1Local) classes start with a
        # digit; they and anything inside them belong to the enclosing type.
        if not part or part[0].isdigit():
            break
        named.append(part)
    return ".".join([head, *named])


def _covered(element: ElementTree.Element, counter_type: str) -> bool:
    for counter in element.findall("counter"):
        if counter.get("type") == counter_type:
            return int(counter.get("covered", "0")) > 0
    return False


def _parse_xml(path: Path) -> ElementTree.Element:
    try:
        return ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        raise ReportError(f"cannot read report {path}: {exc}") from exc


def _float(value: str | None) -> float:
    try:
        return float((value or "0").replace(",", ""))
    except ValueError:
        return 0.0
