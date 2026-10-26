"""A bounded parse cache any language plugin can reuse across commits."""

from __future__ import annotations

from collections import OrderedDict


class BoundedParseCache(OrderedDict):
    """Least-recently-used parse cache shared across many commits.

    Consecutive commits share almost all files, so reusing parses by blob SHA
    avoids re-parsing the whole repository for every commit; the bound keeps
    memory flat on long histories.
    """

    def __init__(self, max_entries: int = 4000):
        super().__init__()
        self.max_entries = max_entries

    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.move_to_end(key)
        while len(self) > self.max_entries:
            self.popitem(last=False)
