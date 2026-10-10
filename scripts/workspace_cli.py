#!/usr/bin/env python3
"""One bounded JSON request on stdin, one JSON response on stdout."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.agent_bridge import AgentBridge, MAX_REQUEST_BYTES  # noqa: E402


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON field: ' + key)
        result[key] = value
    return result


def _constant(value):
    raise ValueError('Nonfinite JSON value')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path)
    options = parser.parse_args(argv)
    try:
        data = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        if len(data) > MAX_REQUEST_BYTES:
            raise ValueError('Request exceeds 1 MiB')
        request = json.loads(data.decode('utf-8'), object_pairs_hook=_object,
                             parse_constant=_constant)
        response = AgentBridge(options.workspace).call(request)
    except (ValueError, RecursionError, OverflowError, OSError) as error:
        response = {'ok': False, 'error': str(error)[:500] or 'Invalid request'}
    except Exception:
        # Unexpected failures remain machine-readable without leaking a traceback
        # into the stdout protocol; do not claim they are successful tool results.
        print('Agent bridge internal error', file=sys.stderr)
        response = {'ok': False, 'error': 'Internal error; see stderr'}
    sys.stdout.buffer.write((json.dumps(response, ensure_ascii=not response['ok'], allow_nan=False,
                                       separators=(',', ':')) + '\n').encode('utf-8'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
