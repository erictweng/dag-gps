#!/usr/bin/env python3
"""Render a bounded layer draft as standalone offline review HTML."""
import argparse
import json
from pathlib import Path
from onboarding import DRAFT_SCHEMA, MAX_BYTES

ROOT = Path(__file__).resolve().parents[1]


def render_editor(draft):
    if draft.get('schema') != DRAFT_SCHEMA or draft.get('reviewed') is not False:
        raise ValueError('Expected an unapproved layer draft v1')
    data = json.dumps(draft, ensure_ascii=True).replace('<', '\\u003c')
    if len(data.encode()) > MAX_BYTES:
        raise ValueError('Layer draft exceeds 8 MiB')
    # Source is trusted repository-owned code; data never enters executable context.
    source = (ROOT / 'web/layer-editor.js').read_text().replace('</script', '<\\/script')
    return (ROOT / 'web/layer-editor.html').read_text().replace('__EDITOR_JS__', source).replace('__DRAFT_JSON__', data)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--draft', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    raw = Path(a.draft).read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError('Layer draft exceeds 8 MiB')
    html = render_editor(json.loads(raw))
    target = Path(a.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html)
    print(target)


if __name__ == '__main__':
    main()
