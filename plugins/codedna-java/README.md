# codedna-java

The Java language plugin for CodeDNA (D-018, D-054). It maps changed lines to
Java declarations, builds the code graph, discovers JUnit 4/5 test classes and
runs Maven or Gradle tests (only with `--allow-build`, D-014).

The core finds it through the `codedna.languages` entry point. Without it,
CodeDNA still lists changed files, but Java files are reported as not analysed.

Install it next to the core, in the same environment:

```
python -m pip install -e ".[ml,api,dev]"
python -m pip install -e plugins/codedna-java
```

`codedna plugins` shows whether it was found.
