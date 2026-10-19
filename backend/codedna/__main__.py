"""Allow running the CLI as ``python -m codedna``."""

import sys

from codedna.cli import main

sys.exit(main())
