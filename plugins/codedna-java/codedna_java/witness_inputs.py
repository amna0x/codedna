"""Bounded typed inputs and reductions; no project execution or correctness oracle."""
import base64
import json
import random
import re

KINDS = ('int', 'long', 'int[]', 'int...', 'boolean', 'String')


def parameter_types(symbol):
    tail = symbol.rsplit('(', 1)[-1]
    values = tail[:-1].split(',') if tail.endswith(')') else []
    if not 1 <= len(values) <= 2 or any(v not in KINDS for v in values):
        raise ValueError('Witness requires one or two bounded numeric/boolean/String arguments')
    return values


def arguments(types, value):
    values = value if len(types) == 2 else [value]
    if not isinstance(values, list) or len(values) != len(types):
        raise ValueError('Two arguments require a two-element input array; one argument requires a scalar')
    for kind, item in zip(types, values):
        valid = (kind == 'int' and type(item) is int and -(2**31) <= item < 2**31
                 or kind == 'long' and type(item) is int and -(2**63) <= item < 2**63
                 or kind in ('int[]', 'int...') and isinstance(item, list) and len(item) <= 8
                    and all(type(v) is int and -(2**31) <= v < 2**31 for v in item)
                 or kind == 'boolean' and type(item) is bool
                 or kind == 'String' and isinstance(item, str) and len(item) <= 128)
        if not valid:
            raise ValueError('Input does not match its declared bounded Java argument types')
        if isinstance(item, str):
            item.encode('utf-8')  # reject isolated surrogates
    return values


def encode(types, value):
    values = arguments(types, value)
    return ':'.join(','.join(map(str,v)) if k in ('int[]','int...') else
                    base64.b64encode(v.encode('utf-8')).decode('ascii') if k == 'String'
                    else str(v).lower() for k, v in zip(types, values))


def java_arguments(types, value):
    values = arguments(types, value)
    return ', '.join('new int[]{'+','.join(map(str,v))+'}' if k in ('int[]','int...') else
                     str(v)+'L' if k == 'long' else json.dumps(v, ensure_ascii=True) if k == 'String' else
                     str(v).lower() for k, v in zip(types, values))


def generate(types, base_tokens, head_tokens, *, mode, seed, maximum, int_candidates):
    if types == ['int']:
        return int_candidates(base_tokens, head_tokens, mode=mode, seed=seed, maximum=maximum)
    pools = []
    for position, kind in enumerate(types):
        if kind == 'int':
            pool = int_candidates(base_tokens, head_tokens, mode=mode, seed=seed+position, maximum=maximum)
        elif kind == 'long':
            pool = int_candidates(base_tokens, head_tokens, mode=mode,
                                  seed=seed+position, maximum=maximum, bits=64)
        elif kind in ('int[]','int...'):
            pool = [[],[0],[1],[-1],[1,-1],[-1,1],[-(2**31)],[2**31-1],[-(2**31),2**31-1]]
            rng = random.Random(seed+position)
            while len(pool)<maximum:
                value=[rng.randint(-100,100) for _ in range(rng.randrange(1,9))]
                if value not in pool:pool.append(value)
        elif kind == 'boolean':
            pool = [False, True]
        else:
            pool = ['', 'a', '0', '-1', ' ', '\n', '\0', 'é', '😀']
            if mode == 'guided':
                literals = []
                for text in [''.join(head_tokens), ''.join(base_tokens)]:
                    for match in re.finditer(r'"(?:\\.|[^"\\])*"', text):
                        try: value = json.loads(match.group())
                        except ValueError: continue
                        if len(value) <= 128: literals.append(value)
                # Only JSON-compatible literal escapes are used as suggestions;
                # Java-specific escapes are not guessed.
                pool = literals + pool
            pool = list(dict.fromkeys(pool))
            rng = random.Random(seed+position)
            while len(pool) < maximum:
                value = ''.join(rng.choice('ab019 -') for _ in range(rng.randrange(1, 17)))
                if value not in pool: pool.append(value)
        pools.append(pool[:maximum])
    if len(types) == 1:
        return pools[0]
    result = []
    # Diagonal allocation avoids consuming the entire budget on one argument.
    for diagonal in range(sum(map(len, pools))-1):
        for first in range(len(pools[0])):
            second = diagonal-first
            if 0 <= second < len(pools[1]):
                result.append([pools[0][first], pools[1][second]])
                if len(result) == maximum: return result
    return result


def complexity(value):
    if isinstance(value, list): return len(value) + sum(complexity(v) for v in value)
    if isinstance(value, str): return len(value)
    return abs(value)


def reductions(value, int_smaller, types=None):
    if isinstance(value, list):
        result = []
        # Delete elements only for a declared single array argument. Never
        # change the arity of a two-argument method during shrinking.
        if types and len(types) == 1 and types[0] in ('int[]', 'int...'):
            result.append([])
            result.extend(value[:i]+value[i+1:] for i in range(len(value)))
        for index, item in enumerate(value):
            child_types = [types[index]] if types and len(types) == 2 else None
            for reduced in reductions(item, int_smaller, child_types):
                candidate = list(value);candidate[index] = reduced;result.append(candidate)
        return sorted(result, key=complexity)
    if isinstance(value, bool): return [False] if value else []
    if isinstance(value, int): return int_smaller(value)
    candidates = ['']
    width = len(value)//2
    while width:
        for start in range(0, len(value), width):
            candidates.append(value[:start]+value[start+width:])
        width //= 2
    return sorted(set(candidates)-{value}, key=lambda v: (len(v), v))
