# codedna-python

The Python language plugin for CodeDNA (D-060). It needs only the standard
library (`ast`).

```bash
python -m pip install -e plugins/codedna-python
codedna plugins            # lists "python" next to "java"
```

What it does:

- **Change mapping:** changed lines → functions, methods and classes, with
  comment/formatting-only edits recognised (`ast.dump` comparison).
- **Code graph:** modules, classes, functions and methods, with `imports`,
  `uses` and `extends` edges labelled confirmed or heuristic; outside and
  unresolvable imports are counted or kept as unresolved, never guessed.
- **Test discovery:** pytest test modules, following the root pytest config
  (`python_files`, `python_classes`, `python_functions`, `testpaths`,
  `norecursedirs`).
- **Test runs** (`codedna run-tests --allow-build`, optionally
  `--python PATH`): pytest in an exported copy of the commit, results per
  test module. This runs the project's code.

IDs start with `py:` (module `py:shop.orders`, class `py:shop.orders.Order`,
function `py:shop.orders#total()`), so they never clash with Java's. In a
mixed repository both plugins run; no dependency between the two languages is
followed. Limits and rules: `docs/DECISIONS.md`, D-060.
