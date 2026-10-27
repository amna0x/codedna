"""Entry point for the bundled desktop core (no separate Python installation)."""

import multiprocessing

import sys

from codedna.plugins import desktop_store
from codedna.plugins.catalogue import CatalogueError

if __name__ == "__main__":
    multiprocessing.freeze_support()
    try:
        desktop_store.activate()
    except CatalogueError:
        pass  # Registry reports store errors; bundled languages remain usable.
    if sys.argv[1:2] == ["--codedna-plugin-probe"]:
        raise SystemExit(desktop_store.probe_main(sys.argv[2:]))
    from codedna.cli import main
    raise SystemExit(main())
