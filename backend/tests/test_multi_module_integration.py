"""Real multi-module Maven and Gradle runs (``--run-maven``; needs network for JUnit)."""

from __future__ import annotations

import shutil

import pytest

from codedna_java.maven import run_maven_tests

pytestmark = pytest.mark.maven

JUNIT = "5.10.2"
CORE = "package a;\npublic class Core {\n    public static int value() { return 2; }\n}\n"


def junit_class(package: str, name: str, expected: int) -> str:
    return (f"package {package};\nimport org.junit.jupiter.api.Test;\n"
            "import static org.junit.jupiter.api.Assertions.assertEquals;\n"
            f"class {name} {{\n    @Test void value() {{ assertEquals({expected}, a.Core.value()); }}\n}}\n")


def module_pom(artifact: str, extra: str = "") -> str:
    return f"""<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <parent><groupId>t</groupId><artifactId>root</artifactId><version>1</version></parent>
  <artifactId>{artifact}</artifactId>
  <dependencies>{extra}
    <dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter</artifactId>
      <version>{JUNIT}</version><scope>test</scope></dependency>
  </dependencies>
</project>
"""


MAVEN = {
    "pom.xml": """<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>t</groupId><artifactId>root</artifactId><version>1</version><packaging>pom</packaging>
  <properties><maven.compiler.release>17</maven.compiler.release></properties>
  <modules><module>core</module><module>app</module></modules>
  <build><pluginManagement><plugins><plugin><artifactId>maven-surefire-plugin</artifactId>
    <version>3.2.5</version></plugin></plugins></pluginManagement></build>
</project>
""",
    "core/pom.xml": module_pom("core"),
    "app/pom.xml": module_pom("app", "<dependency><groupId>t</groupId><artifactId>core</artifactId>"
                                     "<version>1</version></dependency>"),
    "core/src/main/java/a/Core.java": CORE,
    "core/src/test/java/a/CoreTest.java": junit_class("a", "CoreTest", 2),
    "app/src/test/java/b/AppTest.java": junit_class("b", "AppTest", 3),  # fails on purpose
}

GRADLE = {
    "settings.gradle": "rootProject.name = 'demo'\ninclude 'core', 'app'\n",
    "build.gradle": f"""subprojects {{
    apply plugin: 'java'
    // mavenLocal first: reuses JUnit fetched by the Maven tests (offline-friendly).
    repositories {{ mavenLocal(); mavenCentral() }}
    dependencies {{
        testImplementation 'org.junit.jupiter:junit-jupiter:{JUNIT}'
        testRuntimeOnly 'org.junit.platform:junit-platform-launcher:1.10.2'
    }}
    test {{ useJUnitPlatform() }}
}}
project(':app') {{ dependencies {{ implementation project(':core') }} }}
""",
    "core/src/main/java/a/Core.java": CORE,
    "core/src/test/java/a/CoreTest.java": junit_class("a", "CoreTest", 2),
    "app/src/test/java/b/AppChecks.java": junit_class("b", "AppChecks", 3),  # Gradle runs any name
}


def write(repo, files):
    for path, content in files.items():
        repo.write(path, content)
    return repo.commit("project")


def test_multi_module_maven_reports_every_module_and_selects_across_modules(repo, tmp_path):
    head = write(repo, MAVEN)

    run, _ = run_maven_tests(repo.path, head, tmp_path / "all", allow_build=True)
    assert set(run.tests) == {"a.CoreTest", "b.AppTest"}, run.warnings
    assert run.failing_tests == ["b.AppTest"]
    assert (tmp_path / "all/reports/full-suite/app/TEST-b.AppTest.xml").is_file()

    selected, _ = run_maven_tests(repo.path, head, tmp_path / "one", allow_build=True,
                                  selected_tests=["a.CoreTest"])
    assert set(selected.tests) == {"a.CoreTest"} and selected.failing_tests == [], selected.warnings


@pytest.mark.skipif(shutil.which("gradle") is None, reason="Gradle not installed")
def test_gradle_multi_project_runs_and_selects(repo, tmp_path):
    head = write(repo, GRADLE)

    run, _ = run_maven_tests(repo.path, head, tmp_path / "all", allow_build=True)
    assert run.tool == "gradle"
    assert set(run.tests) == {"a.CoreTest", "b.AppChecks"}, run.warnings
    assert run.failing_tests == ["b.AppChecks"]

    selected, _ = run_maven_tests(repo.path, head, tmp_path / "one", allow_build=True,
                                  selected_tests=["a.CoreTest"])
    assert set(selected.tests) == {"a.CoreTest"} and selected.failing_tests == [], selected.warnings

    # A class the build's test task does not run is reported as missing, not dropped.
    excluded = dict(GRADLE, **{"build.gradle": GRADLE["build.gradle"]
                               + "project(':core') { test { exclude '**/CoreTest*' } }\n"})
    head = write(repo, excluded)
    partial, _ = run_maven_tests(repo.path, head, tmp_path / "partial", allow_build=True,
                                 selected_tests=["a.CoreTest"])
    assert partial.tests == {} and any("missing from reports" in w for w in partial.warnings)
