"""Static build layout: Maven modules, Surefire includes, Gradle settings."""

from __future__ import annotations

from codedna.git_analysis.git import resolve_commit
from codedna_java.build import detect_build
from codedna_java.discovery import discover_tests

JUNIT = "import org.junit.jupiter.api.Test;\n"
POM_NS = 'xmlns="http://maven.apache.org/POM/4.0.0"'


def junit_class(package: str, name: str) -> str:
    return f"package {package};\n{JUNIT}class {name} {{\n    @Test void ok() {{}}\n}}\n"


def commit(repo, files: dict[str, str]) -> str:
    for path, content in files.items():
        repo.write(path, content)
    return repo.commit("layout")


def test_maven_modules_are_followed_and_custom_includes_read(repo):
    head = commit(repo, {
        "pom.xml": f"<project {POM_NS}><modules><module>core</module>"
                   "<module>apps</module></modules></project>\n",
        "core/pom.xml": f"<project {POM_NS}><build><plugins><plugin>"
                        "<artifactId>maven-surefire-plugin</artifactId><configuration>"
                        "<includes><include>**/*Check.java</include></includes>"
                        "</configuration></plugin></plugins></build></project>\n",
        "apps/pom.xml": "<project><modules><module>web</module></modules></project>\n",
        "apps/web/pom.xml": "<project/>\n",
        "core/src/test/java/a/PriceCheck.java": junit_class("a", "PriceCheck"),
        "core/src/test/java/a/PriceTest.java": junit_class("a", "PriceTest"),
        "apps/web/src/test/java/w/PageTest.java": junit_class("w", "PageTest"),
        "loose/src/test/java/x/LooseTest.java": junit_class("x", "LooseTest"),
    })

    layout = detect_build(repo.path, resolve_commit(repo.path, head))

    assert layout.tool == "maven"
    assert layout.modules == ["", "apps", "apps/web", "core"]
    assert layout.includes == {"core": ["**/*Check.java"]}
    tests = {t.id: t for t in discover_tests(repo.path, head).tests}
    assert tests["a.PriceCheck"].module == "core" and tests["a.PriceCheck"].runs_by_default
    assert not tests["a.PriceTest"].runs_by_default  # excluded by the module's own includes
    assert tests["w.PageTest"].module == "apps/web" and tests["w.PageTest"].runs_by_default
    assert tests["x.LooseTest"].module is None and not tests["x.LooseTest"].runs_by_default


def test_missing_module_pom_is_reported_not_guessed(repo):
    head = commit(repo, {"pom.xml": "<project><modules><module>gone</module></modules></project>\n"})

    layout = detect_build(repo.path, resolve_commit(repo.path, head))

    assert layout.modules == [""]
    assert any("gone" in w for w in layout.warnings)


def test_gradle_settings_modules_run_every_junit_class(repo):
    head = commit(repo, {
        "settings.gradle.kts": 'rootProject.name = "demo"\ninclude("core", ":tools:cli")\n',
        "build.gradle.kts": "plugins { java }\n",
        "core/src/test/java/a/Checks.java": junit_class("a", "Checks"),
        "tools/cli/src/test/java/c/CliTest.java": junit_class("c", "CliTest"),
    })

    report = discover_tests(repo.path, head)

    assert report.build_tool == "gradle"
    tests = {t.id: t for t in report.tests}
    assert tests["a.Checks"].module == "core" and tests["a.Checks"].runs_by_default
    assert tests["c.CliTest"].module == "tools/cli"
    assert any("syntactically" in w for w in report.warnings)


def test_surefire_excludes_and_unsafe_or_profile_modules(repo):
    head = commit(repo, {
        "pom.xml": "<project><modules><module>core/</module><module>../outside</module>"
                   "<module>./core</module></modules><profiles><profile><modules>"
                   "<module>extra</module></modules></profile></profiles></project>\n",
        "core/pom.xml": "<project><build><plugins><plugin>"
                        "<artifactId>maven-surefire-plugin</artifactId><configuration>"
                        "<excludes><exclude>**/*SlowTest.java</exclude></excludes>"
                        "</configuration></plugin></plugins></build></project>\n",
        "core/src/test/java/a/FastTest.java": junit_class("a", "FastTest"),
        "core/src/test/java/a/DbSlowTest.java": junit_class("a", "DbSlowTest"),
        "extra/pom.xml": "<project/>\n",
    })

    layout = detect_build(repo.path, resolve_commit(repo.path, head))

    assert layout.modules == ["", "core"]
    assert layout.excludes == {"core": ["**/*SlowTest.java"]}
    assert any("outside the repository" in w for w in layout.warnings)
    assert any("<profiles>" in w for w in layout.warnings)
    tests = {t.id: t for t in discover_tests(repo.path, head).tests}
    assert tests["a.FastTest"].runs_by_default
    assert not tests["a.DbSlowTest"].runs_by_default


def test_gradle_multi_line_include_and_comments(repo):
    head = commit(repo, {
        "settings.gradle": "rootProject.name = 'demo'\n// include 'old'\n"
                           "include(\n    ':core',\n    ':tools:cli'\n)\n/* include 'gone' */\n"
                           "include 'web'\n",
        "build.gradle": "plugins { id 'java' }\n",
    })

    layout = detect_build(repo.path, resolve_commit(repo.path, head))

    assert layout.modules == ["", "core", "tools/cli", "web"]


def test_shared_and_custom_test_source_folders_are_followed(repo):
    # HikariCP 2.x layout: two modules add one shared test folder with build-helper.
    helper = ("<plugin><artifactId>build-helper-maven-plugin</artifactId><executions>"
              "<execution><goals><goal>add-source</goal></goals><configuration><sources>"
              "<source>../common/src/main/java</source></sources></configuration></execution>"
              "<execution><goals><goal>add-test-source</goal></goals><configuration><sources>"
              "<source>../common/src/test/java</source><source>${extra.dir}</source>"
              "<source>../../outside</source></sources></configuration></execution>"
              "</executions></plugin>")
    head = commit(repo, {
        "pom.xml": f"<project {POM_NS}><modules><module>java8</module><module>java6</module>"
                   "<module>legacy</module></modules></project>\n",
        "java8/pom.xml": f"<project {POM_NS}><build><plugins>{helper}</plugins></build></project>\n",
        "java6/pom.xml": f"<project {POM_NS}><build><plugins>{helper}</plugins></build></project>\n",
        "legacy/pom.xml": f"<project {POM_NS}><build><testSourceDirectory>tests</testSourceDirectory>"
                          "</build></project>\n",
        "common/src/test/java/a/SharedTest.java": junit_class("a", "SharedTest"),
        "common/src/main/java/a/NotATest.java": junit_class("a", "NotATest"),
        "java6/src/test/java/a/OnlySixTest.java": junit_class("a", "OnlySixTest"),
        "legacy/tests/l/OldTest.java": junit_class("l", "OldTest"),
        "legacy/src/test/java/l/IgnoredTest.java": junit_class("l", "IgnoredTest"),
    })

    layout = detect_build(repo.path, resolve_commit(repo.path, head))

    assert layout.roots("java8") == ["java8/src/test/java/", "common/src/test/java/"]
    assert layout.roots("legacy") == ["legacy/tests/"]
    assert any("${extra.dir}" in w for w in layout.warnings)
    assert any("'../../outside' is outside the repository" in w for w in layout.warnings)
    tests = {t.id: t for t in discover_tests(repo.path, head).tests}
    assert tests["a.SharedTest"].runs_by_default and tests["a.SharedTest"].module == "java6"
    assert tests["a.OnlySixTest"].module == "java6"
    assert tests["l.OldTest"].runs_by_default and tests["l.OldTest"].module == "legacy"
    assert not tests["l.IgnoredTest"].runs_by_default  # legacy moved its test folder
    assert not tests["a.NotATest"].runs_by_default  # main sources are not test sources


def test_class_patterns_in_surefire_includes_select_test_classes(repo):
    head = commit(repo, {
        "pom.xml": f"<project {POM_NS}><build><plugins><plugin>"
                   "<artifactId>maven-surefire-plugin</artifactId><configuration>"
                   "<includes><include>**/*.class</include></includes><excludes>"
                   "<exclude>**/Slow*.class</exclude></excludes>"
                   "</configuration></plugin></plugins></build></project>\n",
        "src/test/java/a/Checks.java": junit_class("a", "Checks"),
        "src/test/java/a/SlowChecks.java": junit_class("a", "SlowChecks"),
    })
    tests = {t.id: t for t in discover_tests(repo.path, head).tests}
    assert tests["a.Checks"].runs_by_default  # wicket-bootstrap configures **/*.class
    assert not tests["a.SlowChecks"].runs_by_default


def test_gradle_test_source_sets_moved_by_scripts(repo):
    head = commit(repo, {
        "settings.gradle": 'include "core"\ninclude "extra"\n',
        "build.gradle": "allprojects { apply from: rootProject.file('gradle/layout.gradle') }\n",
        # A shared script, as in Lucene: applied to every module.
        "gradle/layout.gradle": "sourceSets {\n  test.java.srcDirs = ['src/test']\n}\n",
        "extra/build.gradle": "sourceSets { test.java.srcDirs += ['src/it'] }\n",
        "core/src/test/a/Checks.java": junit_class("a", "Checks"),
        "extra/src/it/b/Flow.java": junit_class("b", "Flow"),
        "extra/src/test/b/Unit.java": junit_class("b", "Unit"),
    })

    layout = detect_build(repo.path, head)
    report = discover_tests(repo.path, head)

    assert layout.test_roots["core"] == ["core/src/test/"]
    assert layout.test_roots["extra"] == ["extra/src/test/", "extra/src/it/"]
    tests = {t.id: t for t in report.tests}
    assert tests["a.Checks"].runs_by_default and tests["a.Checks"].module == "core"
    assert tests["b.Flow"].runs_by_default and tests["b.Unit"].runs_by_default
    assert any("gradle/layout.gradle" in w and "every Gradle module" in w for w in report.warnings)
