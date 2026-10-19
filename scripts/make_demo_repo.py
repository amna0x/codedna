"""Create a throwaway Git repository for demonstrating ``codedna analyze``.

The script copies examples/sample-java-project into a new directory, commits
it (BASE), applies a small set of edits, and commits again (HEAD):

* modifies a method in PriceCalculator.java
* adds a new class Rounding.java
* renames OrderServiceTest.java to OrderTotalsTest.java
* edits a non-Java file (README.md)

Usage:
    python scripts/make_demo_repo.py DEST_DIR
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SAMPLE = Path(__file__).resolve().parent.parent / "examples" / "sample-java-project"
IDENTITY = ("-c", "user.name=CodeDNA Demo", "-c", "user.email=demo@example.invalid")


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *IDENTITY, *args], cwd=repo, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def write(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dest", help="Directory to create (must not already exist).")
    dest = Path(parser.parse_args().dest).resolve()
    if dest.exists():
        print(f"error: {dest} already exists; choose a new directory", file=sys.stderr)
        return 1

    shutil.copytree(SAMPLE, dest, ignore=shutil.ignore_patterns("target"))
    # A Windows checkout may have CRLF line endings; use LF so the edits below
    # change only the intended lines.
    for copied in dest.rglob("*"):
        if copied.suffix in (".java", ".xml"):
            write(copied, copied.read_text(encoding="utf-8"))
    write(dest / "README.md", "# Demo shop\n\nSample project for CodeDNA.\n")
    git(dest, "init", "--quiet")
    git(dest, "add", "--all")
    git(dest, "commit", "--quiet", "-m", "Initial sample project")
    base = git(dest, "rev-parse", "HEAD")

    java = dest / "src" / "main" / "java" / "example"
    calculator = java / "PriceCalculator.java"
    write(calculator, calculator.read_text(encoding="utf-8").replace(
        "        return amount * (1.0 - discountRate);\n",
        "        double discounted = amount * (1.0 - discountRate);\n"
        "        return Rounding.toCents(discounted);\n",
    ))
    write(java / "Rounding.java",
          "package example;\n\n"
          "/** Rounds monetary amounts to two decimal places. */\n"
          "public final class Rounding {\n\n"
          "    private Rounding() {}\n\n"
          "    public static double toCents(double amount) {\n"
          "        return Math.round(amount * 100.0) / 100.0;\n"
          "    }\n"
          "}\n")
    tests = Path("src", "test", "java", "example")
    git(dest, "mv", str(tests / "OrderServiceTest.java"), str(tests / "OrderTotalsTest.java"))
    renamed = dest / tests / "OrderTotalsTest.java"
    write(renamed, renamed.read_text(encoding="utf-8").replace(
        "class OrderServiceTest", "class OrderTotalsTest"))
    write(dest / "README.md", "# Demo shop\n\nSample project for CodeDNA.\n\nPrices are rounded to cents.\n")
    git(dest, "add", "--all")
    git(dest, "commit", "--quiet", "-m", "Round discounted prices to cents")
    head = git(dest, "rev-parse", "HEAD")

    print(f"Demo repository: {dest}")
    print(f"BASE={base}")
    print(f"HEAD={head}")
    print()
    print("Try:")
    print(f'  codedna analyze --repo "{dest}" --base {base} --head {head}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
