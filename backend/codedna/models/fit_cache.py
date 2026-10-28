"""Process-local fitted-model reuse; no cached audit, selection or verdict.

Only explicitly scoped consumers opt in. The full dataset is fingerprinted;
training/calibration parameters and implementation identity remain in the key.
No executable model serialization or persistent cache is used.
"""
from collections import OrderedDict
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from hashlib import sha256
import json
import os
from threading import RLock, get_ident
from time import monotonic

from codedna.performance import count, stage

_SCOPE = ContextVar('codedna_fitted_model_scope', default=None)
_CACHE = OrderedDict()
_LOCK = RLock()
_MAX_ENTRIES = 2
_TTL = 300.
_SCHEMA = 'gb200-balanced-seed0/isotonic/chronological-half-quarter:v1'


@contextmanager
def fitted_model_scope(namespace):
    if not isinstance(namespace, tuple) or not all(isinstance(item, str) for item in namespace):
        raise ValueError('model reuse namespace must be an immutable tuple of strings')
    token = _SCOPE.set((os.getpid(), get_ident(), namespace))
    try:
        yield
    finally:
        _SCOPE.reset(token)


def clear_fitted_models():
    with _LOCK:
        _CACHE.clear()


def _fingerprint(dataset):
    digest = sha256()
    def add(value):
        digest.update(json.dumps(value, separators=(',', ':'), ensure_ascii=True,
                                 allow_nan=True).encode('ascii'))
        digest.update(b'\n')
    add([dataset.feature_names, dataset.commits])
    for row in dataset.rows:
        add([row.commit, row.seq, row.test_id, row.label, row.duration,
             sorted(row.features.items())])
    return digest.hexdigest()


def fitted_models(dataset, features, risk_target, implementation, compute):
    """Return independent model/calibrator objects; always audit again outside."""
    scope = _SCOPE.get()
    if scope is None or scope[:2] != (os.getpid(), get_ident()):
        count('fit_cache.disabled')
        return compute()
    with stage('fit_cache.fingerprint'):
        key = (scope[0], scope[2], _SCHEMA, tuple(features), risk_target,
               implementation, _fingerprint(dataset))
    now = monotonic()
    with _LOCK:
        for old_key, (created, _) in list(_CACHE.items()):
            if now-created >= _TTL:
                del _CACHE[old_key]
        cached = _CACHE.get(key)
        if cached is not None:
            try:
                with stage('fit_cache.copy'):
                    result = deepcopy(cached[1])
            except Exception:
                del _CACHE[key]
                count('fit_cache.copy_failed')
            else:
                _CACHE.move_to_end(key)
                count('fit_cache.hit')
                return result
    count('fit_cache.miss')
    result = compute()  # failed fits are never stored
    try:
        with stage('fit_cache.copy'):
            stored = deepcopy(result)
    except Exception:
        count('fit_cache.copy_failed')
        return result
    with _LOCK:
        _CACHE[key] = (monotonic(), stored)
        _CACHE.move_to_end(key)
        while len(_CACHE) > _MAX_ENTRIES:
            _CACHE.popitem(last=False)
            count('fit_cache.evicted')
    return result
