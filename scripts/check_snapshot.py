#!/usr/bin/env python3
"""Verify pinned rebuild preserves every map field except provenance ref/time."""
import copy
import json
import sys


def check(original, rebuilt):
    a, b = copy.deepcopy(original), copy.deepcopy(rebuilt)
    for data in (a, b):
        for key in ('ref', 'built_at'):
            data['meta'].pop(key, None)
    if a != b:
        raise ValueError('Pinned rebuild differs from committed map; do not silently remap')
    return True


if __name__ == '__main__':
    with open(sys.argv[1], encoding='utf-8') as fh:
        original = json.load(fh)
    with open(sys.argv[2], encoding='utf-8') as fh:
        rebuilt = json.load(fh)
    check(original, rebuilt)
    print('PASS pinned map parity: %s, %d nodes, %d layer edges, %d file edges; only ref/time ignored' % (
        original['meta']['commit'], len(original['nodes']), len(original['edges']), len(original['file_edges'])))
