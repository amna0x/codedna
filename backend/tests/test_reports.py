"""Tests for the Surefire and JaCoCo XML parsers."""

from __future__ import annotations

import pytest

from codedna.test_mapping.reports import (
    ReportError,
    jvm_class_to_type_id,
    parse_jacoco_report,
    parse_surefire_reports,
)

SUREFIRE = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="a.CartTest" time="1,234.5" tests="4" failures="1" errors="1" skipped="1">
  <properties><property name="java.version" value="17"/></properties>
  <testcase name="ok" classname="a.CartTest" time="0.25"/>
  <testcase name="bad" classname="a.CartTest" time="0.5">
    <failure message="expected 2" type="org.opentest4j.AssertionFailedError">trace</failure>
  </testcase>
  <testcase name="skip" classname="a.CartTest" time="0"><skipped/></testcase>
  <testcase name="boom" classname="a.CartTest$WhenFull" time="1,000.25">
    <error message="NPE" type="java.lang.NullPointerException"/>
  </testcase>
</testsuite>
"""

JACOCO = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!DOCTYPE report PUBLIC "-//JACOCO//DTD Report 1.1//EN" "report.dtd">
<report name="demo">
  <sessioninfo id="x" start="1" dump="2"/>
  <package name="example">
    <class name="example/PriceCalculator" sourcefilename="PriceCalculator.java">
      <method name="applyDiscount" desc="(D)D" line="22">
        <counter type="INSTRUCTION" missed="0" covered="7"/>
      </method>
      <counter type="INSTRUCTION" missed="3" covered="7"/>
    </class>
    <class name="example/PriceCalculator$Helper$1" sourcefilename="PriceCalculator.java">
      <counter type="INSTRUCTION" missed="0" covered="2"/>
    </class>
    <class name="example/Unused" sourcefilename="Unused.java">
      <counter type="INSTRUCTION" missed="5" covered="0"/>
    </class>
    <sourcefile name="PriceCalculator.java">
      <line nr="22" mi="0" ci="3" mb="0" cb="0"/>
      <line nr="23" mi="0" ci="4" mb="0" cb="0"/>
      <line nr="30" mi="3" ci="0" mb="0" cb="0"/>
    </sourcefile>
    <sourcefile name="Unused.java">
      <line nr="3" mi="5" ci="0" mb="0" cb="0"/>
    </sourcefile>
  </package>
</report>
"""


def test_surefire_results_are_aggregated_per_top_level_class(tmp_path):
    (tmp_path / "TEST-a.CartTest.xml").write_text(SUREFIRE, encoding="utf-8")
    (tmp_path / "a.CartTest.txt").write_text("ignored", encoding="utf-8")

    results = parse_surefire_reports(tmp_path)

    cart = results["a.CartTest"]
    assert cart.status == "error" and cart.failed
    assert cart.time == pytest.approx(1000.25 + 0.75)
    statuses = {case.name: case.status for case in cart.cases}
    assert statuses == {"ok": "passed", "bad": "failed", "skip": "skipped",
                        "WhenFull.boom": "error"}
    assert next(c for c in cart.cases if c.name == "bad").message == "expected 2"


def test_all_skipped_class_is_skipped_not_failed(tmp_path):
    (tmp_path / "TEST-a.S.xml").write_text(
        '<testsuite name="a.S"><testcase name="t" classname="a.S"><skipped/></testcase></testsuite>',
        encoding="utf-8")

    result = parse_surefire_reports(tmp_path)["a.S"]
    assert result.status == "skipped" and not result.failed


def test_malformed_report_raises_report_error(tmp_path):
    (tmp_path / "TEST-bad.xml").write_text("<testsuite>", encoding="utf-8")
    with pytest.raises(ReportError, match="TEST-bad.xml"):
        parse_surefire_reports(tmp_path)


def test_jacoco_report_gives_covered_types_and_lines(tmp_path):
    report = tmp_path / "jacoco.xml"
    report.write_text(JACOCO, encoding="utf-8")

    coverage = parse_jacoco_report(report)

    assert coverage.covered_types == {"example.PriceCalculator", "example.PriceCalculator.Helper"}
    assert coverage.covered_lines == {("example", "PriceCalculator.java"): {22, 23}}


@pytest.mark.parametrize("jvm_name,type_id", [
    ("example/Outer", "example.Outer"),
    ("example/Outer$Inner", "example.Outer.Inner"),
    ("example/Outer$1", "example.Outer"),
    ("example/Outer$Inner$2", "example.Outer.Inner"),
    ("example/Outer$1Local", "example.Outer"),
    ("Default", "Default"),
])
def test_jvm_class_names_map_to_type_ids(jvm_name, type_id):
    assert jvm_class_to_type_id(jvm_name) == type_id
