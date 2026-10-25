"""Entry point for the bundled desktop core (no separate Python installation)."""

import multiprocessing

from codedna.cli import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
