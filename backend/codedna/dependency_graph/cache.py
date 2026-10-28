"""A bounded parse cache any language plugin can reuse across commits."""

from __future__ import annotations

from collections import OrderedDict
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import os
from threading import get_ident
from codedna.performance import count


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
        count('parse_cache.get')
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        count('parse_cache.store')
        self.move_to_end(key)
        while len(self) > self.max_entries:
            self.popitem(last=False)
            count('parse_cache.evicted')


_OPERATION = ContextVar('codedna_operation_parse_cache', default=None)


@contextmanager
def parse_cache_scope():
    """Share only immutable parses inside one synchronous operation."""
    owner = (os.getpid(), get_ident())
    active = _OPERATION.get()
    if active is not None and active['owner'] == owner:
        yield
        return
    token = _OPERATION.set({'owner': owner, 'namespace': None, 'cache': None})
    try:
        yield
    finally:
        _OPERATION.reset(token)


def reuse_parse_cache(function):
    @wraps(function)
    def scoped(*args, **kwargs):
        with parse_cache_scope():
            return function(*args, **kwargs)
    return scoped


def operation_parse_cache(repo, registry):
    """One bounded partition; a repository/plugin identity change replaces it.

    Explicit caller caches keep their original contract. No trees, selected
    sets, configuration, outcomes, models or acceptance are cached here.
    """
    active = _OPERATION.get()
    if active is None or active['owner'] != (os.getpid(), get_ident()):
        return BoundedParseCache()
    namespace = (str(repo), tuple((name, type(plugin), plugin.version, plugin.api_version,
        getattr(type(plugin), 'parse', None), getattr(type(plugin), 'build_graph', None),
        getattr(type(plugin), 'discover_tests', None))
        for name, plugin in sorted(registry.plugins.items())))
    if active['namespace'] != namespace:
        active['namespace'] = namespace
        active['cache'] = BoundedParseCache()
    return active['cache']
