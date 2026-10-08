#!/usr/bin/env python3
"""Validate measured V1.5 milestone evidence, never substitute for real gates."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
QUEST = '749d8b5de490cc2e6a0c98c713fab3ab856da799'
SELF = 'f92d0cf9ad2fe6ef332dc5922e32c1e22dc96f93'
NEW_SELF = 'a5b02554e479b5184204ab6aa7c7190d6605fe91'


def read(name):
    return json.loads((ROOT / 'artifacts' / name).read_text())


def validate():
    browser = read('release-browser.json')
    assert browser['humanAcceptance'].startswith('pending')
    assert len(browser['sessions']) == 2
    pins = {'quest': (QUEST, QUEST), 'self': (SELF, NEW_SELF)}
    events = []
    for session in browser['sessions']:
        assert (session['initialSource'], session['refreshSource']) == pins[session['name']]
        assert session['stepCount'] == len(session['steps']) == 11
        for step in session['steps']:
            events.extend(step['events'])
        for key in ['downloadedLayers', 'downloadedAliases', 'downloadedFeedback']:
            assert Path(session[key]).is_file()
        layers = json.loads(Path(session['downloadedLayers']).read_text())
        assert layers['onboarding']['reviewed'] is True
        feedback = json.loads(Path(session['downloadedFeedback']).read_text())
        assert all(r['origin'] == 'generated-fixture' for r in feedback['records'])
    assert any(e['trusted'] and e['id'] == 'alias-confirm' for e in events)
    assert any(e['trusted'] and e['id'] == 'export' for e in events)
    assert any(e['key'] == 'Escape' for e in events)
    audit = read('release-accessibility.json')
    assert audit['axe'] and len(audit['states']) == 23
    assert {s['width'] for s in audit['states']} == {390, 1280, 1920}
    contrast = []
    for state in audit['states']:
        assert state['overflow']['document'] <= state['overflow']['viewport']
        assert not state['axe']['violations']
        contrast.extend(state.get('svgContrast', []))
        if 'reducedMotion' in state:
            assert state['reducedMotion']['preference']
            assert state['reducedMotion']['animation'] == state['reducedMotion']['transition'] == '0s'
    assert contrast and all(t['ratio'] >= 4.5 and float(t['opacity']) == 1 for t in contrast)
    performance = read('release-performance.json')
    expected = {'quest': 290, 'self-legacy': 30, 'self-onboarding': 51,
                'synthetic-1k': 1000, 'synthetic-5k': 5000}
    assert {f['name']: f['nodes'] for f in performance['fixtures']} == expected
    for fixture in performance['fixtures']:
        assert fixture['synthetic'] == fixture['name'].startswith('synthetic-')
        assert fixture['cold_scorer_init_ms'] >= 0
        assert {m['aliasMode'] for m in fixture['modes']} == {'on', 'off'}
        for mode in fixture['modes']:
            assert len(mode['queries']) == 5
            assert any(q['query'].startswith('path from ') for q in mode['queries'])
            assert any(q['query'] == 'quantum teleporter' for q in mode['queries'])
            assert all(q['samples'] == 1000 and 0 <= q['p95_ms'] < 10 for q in mode['queries'])
    ui = read('release-ui-performance.json')
    assert len(ui['fixtures']) == 5
    for fixture in ui['fixtures']:
        assert len(fixture['layout']['samples']) == 5
        assert fixture['layout']['count']['nodes'] == fixture['files']
        assert all(q['full_ask_render']['samples'] == 20 and
                   q['including_two_paint_opportunities']['samples'] == 20 for q in fixture['ask'])
        if fixture['name'].startswith('synthetic-'):
            assert fixture['boundedView']['cyclePreserved'] and fixture['boundedView']['lateFileAskVisible']
            assert fixture['boundedView']['controlsSeparated']
            assert fixture['boundedView']['fileGraphNodes'] == 80
    screenshots = set()
    for report in [browser, audit, ui]:
        errors = report.get('errors', report.get('pageErrors', []))
        requests = report.get('requests', report.get('externalRequests', []))
        assert not errors and not requests
        screenshots.update(report['screenshots'])
    assert len(screenshots) == 32
    assert all(Path(p).is_file() and Path(p).stat().st_size > 0 for p in screenshots)
    print(json.dumps(dict(sessions=2, step_groups=22, recorded_events=len(events),
                          axe_states=len(audit['states']), svg_text_instances=len(contrast),
                          screenshots=len(screenshots), scorer_samples=50000,
                          human_acceptance='pending Eric; no automatic approval')))


if __name__ == '__main__':
    try:
        validate()
    except (OSError, ValueError, AssertionError, KeyError) as error:
        print('Milestone evidence blocked: ' + str(error), file=sys.stderr)
        sys.exit(1)
