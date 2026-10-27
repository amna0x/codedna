"""Entry point for the bundled desktop core (no separate Python installation)."""

import json
import os
import multiprocessing

import sys

from codedna.plugins import desktop_store
from codedna.plugins.catalogue import CatalogueError

if __name__ == "__main__":
    multiprocessing.freeze_support()
    if sys.argv[1:2] == ["--codedna-analysis-worker"]:
        # The worker reads its parent's pinned activation only after process
        # containment; never activate a pending plugin update from active.json.
        from codedna.api.analysis_worker import main as analysis_worker_main
        raise SystemExit(analysis_worker_main())
    pinned = os.environ.get("CODEDNA_DESKTOP_PLUGIN_SNAPSHOT")
    if pinned is not None:
        try:
            desktop_store.pin_worker_snapshot(json.loads(pinned))
        except (ValueError, CatalogueError) as exc:
            print(f"cannot restore desktop plugin activation: {exc}", file=sys.stderr)
            raise SystemExit(2)
    try:
        desktop_store.activate()
    except CatalogueError:
        pass  # Registry reports store errors; bundled languages remain usable.
    if sys.argv[1:2] == ["--codedna-plugin-probe"]:
        raise SystemExit(desktop_store.probe_main(sys.argv[2:]))
    from codedna.cli import main
    raise SystemExit(main())
