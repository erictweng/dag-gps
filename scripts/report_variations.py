#!/usr/bin/env python3
"""Render only measured results; no fabricated numbers or expectations."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def render():
    r = json.loads((ROOT / 'eval/variation_results.json').read_text())
    config = json.loads((ROOT / 'eval/variation_templates.json').read_text())
    lines = ['# Question-variation benchmark', '',
             'This measures **robustness to phrasing on known targets**, not real-user accuracy. No parser behavior was changed.', '',
             '## Headline', '',
             '| Repo | Version | Generated positive + negative | Correct | Correct or choose | Wrong | Overconfident negatives | Warm p50 / p95 ms |',
             '|---|---|---:|---:|---:|---:|---:|---:|']
    def pct(n, d):
        return f'{n}/{d} ({100*n/d:.2f}%)' if d else 'n/a'
    def cell(s):
        return str(s).replace('|', '\\|').replace('\n', ' ')
    def line(*values):
        lines.append('| ' + ' | '.join(cell(v) for v in values) + ' |')
    def f(n):
        return f'{n:.3f}'
    for repo, versions in r['repos'].items():
        for version in ['main', 'parser']:
            v = versions[version]; p, n, t = v['positive'], v['negative'], v['latency']
            line(repo, version, f"{p['total']} + {n['total']}", pct(p['correct'], p['total']),
                 pct(p['correct'] + p['choose-correct'], p['total']), pct(p['wrong'], p['total']),
                 pct(n['overconfident'], n['total']), f"{f(t['p50'])} / {f(t['p95'])}")
    lines += ['', 'Percentages above use positive constructed cases, except overconfidence which uses only negatives. Timing includes both.', '',
              '| Repo | Main distinct successful strings | Parser distinct successful strings | Unique generated strings | Targets (source checked) |',
              '|---|---:|---:|---:|---|']
    for repo, v in r['repos'].items():
        line(repo, v['main']['positive']['distinctSuccessful'], v['parser']['positive']['distinctSuccessful'],
             v['parser']['distinctQuestions'], json.dumps(v['targets']))
    lines += ['', 'Counts are case-weighted, not unique-string-weighted: repeated equivalent forms remain in axis cells. Distinct successes deduplicate exact strings across correct + choose-correct cases; one successful target interpretation suffices for this requested metric.', '',
              '## Frozen hand-written reference (unchanged)', '',
              'These are the existing reports, not generated-grid labels. They approximate real phrasing but are author-written, not independently sampled user traffic. Their stricter expected-match/expected-choice labels differ from the generated evaluator.', '',
              '| Repo/split | Version | Cases | Match correct / expected match | Choose correct / expected choose | Negative no-match | Wrong | Overconfident |',
              '|---|---|---:|---:|---:|---:|---:|---:|']
    for repo, suffix in [('honcho', ''), ('salesroom', '_salesroom')]:
        for version, stage in [('main', 'baseline'), ('parser', 'review_fixes')]:
            source = json.loads((ROOT / f'eval/question_parser{suffix}_{stage}.json').read_text())
            for split, s in source['splits'].items():
                line(repo + '/' + split, version, s['cases'], pct(s['matchCorrect'], s['matchTotal']),
                     pct(s['chooseCorrect'], s['chooseTotal']), pct(s['noMatchCorrect'], s['noMatchTotal']), s['wrong'], s['overconfident'])
    lines += ['', '## Method and scope', '',
              f"- Versions: main `{r['main']}`; parser query code at `{r['parser']}`. Both use the identical parser-era snapshots; this isolates query-code changes, not extraction-version changes. Baseline ignores the extra concept sidecar.",
              f"- Seed `{r['seed']}`; templates SHA-256 `{r['templatesSha256']}`. Frozen targets, pins, source checks and known directed-edge pairs are in `eval/variation_templates.json`.",
              '- Targets were selected before querying: SHA-256(seed + ID) order, minimum quotas, plus all applicable synonym-name targets. Each file is checked against a pinned Git blob; Python symbols against AST name/start; folders against Git tree descendants. PATH/FLOW pairs are directed observed edges, not runtime proofs. `python3 scripts/freeze_variation_targets.py --check` rechecks source selection without querying.',
              '- Grid is sparse and deterministic: operation phrase × target form, plus each independent perturbation on the canonical target, one axis at a time. This is not the exponential full Cartesian product or an interaction-completeness claim. No tuning or successful-target selection after running. Contractions are separate operation-phrase rows (straight/curly apostrophe and omitted apostrophe).',
              '- File/folder operations: LOCATE, UPSTREAM (dependencies), DOWNSTREAM (dependents). Python symbol operations: LOCATE, CALLERS, CALLEES, TRACE. PATH/FLOW use the chosen connected pairs. Zero-degree traversal is a valid operation; symbol dependency/import phrasings are not mislabeled as file-import operations. No TS/JS symbols exist in these snapshots.',
              '- Target forms include path, basename, stem, folder name, symbol name, qualified name and exact symbol ID; synonyms only where the frozen table applies. Case changes affect the target, not the sentence. Kind agreement is broad file/folder/symbol agreement, not function-vs-class semantic correctness. Typo inserts one `z` at the end; findings do not generalize to arbitrary edit errors.',
              '- Negatives: 240 per repo (80 absent-concept phrases, 80 nonsense, 80 existing-name + absent hash suffix). Exact generated names are checked absent. The concept phrases are synthetic, not a comprehensive semantic-absence oracle; the suffix near misses are easier than one-edit typos. Positive one-edit cases are measured separately.',
              '- Correct requires matched status, exact intended seed (not incidental selected nodes), and operation. Directed path success requires a witness from intended A to B. Choose-correct requires intended candidate(s) and operation; file choice packets leave operation NOT_SURE, so the same version scorer’s requestedOperation supplies the operation outside timed regions. Alternatives missing the intended target, unsupported and no-path are unresolved, never counted as successful or confident-wrong. No-match means actual no-match status. Wrong means confidently matched wrong seed or operation. Overconfident means any matched negative.',
              '- Confidence here means API matched status, not calibrated probability. Only the first packet/choice page is graded; no pagination or simulated human choice. The grid tests query interpretation, not completeness of all graph edges or traversal pages.',
              '', '### Reproduce', '',
              'From this worktree, with the existing pinned `artifacts/question-parser/{honcho,salesroom}/snapshot.json` and cached Git sources:', '',
              '```sh', 'node scripts/bench_variations.cjs && node scripts/verify_variations.cjs && python3 scripts/report_variations.py', '```', '',
              'The runner checks snapshot hashes, archives local main `7db31cd` without checking out another branch, runs both services, starts real loopback WorkspaceServers, and writes raw JSONL/HTTP logs under `artifacts/variation-benchmark/`. No network import, model calls, push, merge or PR. Large artifacts are local/ignored; `eval/variation_results.json` is the committed summary. A new checkout needs the same pinned snapshot artifacts; this command does not silently rebuild a different extraction.', '',
              '## Speed and variance', '',
              f"Machine: `{json.dumps(r['machine'])}`. Load averages before `{r['loadBefore']}`, after `{r['loadAfter']}`.", '',
              f"Direct path: real createQueryService.query, the same function as query_worker.cjs; {r['warmup']} seeded warmup requests and {r['repeats']} measured sweeps. Cold: {r['coldRepeats']} snapshot reads/JSON parses and service/index constructions, excluding require/module compilation; OS disk cache is not flushed. First construction is process-cold; later constructions are rebuilds.",
              'Version order is main then parser; no CPU isolation, process restart per sweep, randomized version order, or confidence intervals. Timing variance includes GC/scheduler effects. All direct raw timings are retained. Tier names are observable packet buckets: no-match status first, then BM25 fallback reason, synonym reason, otherwise literal (includes lexical/fuzzy alternatives). This is not internal stage-exclusive profiler instrumentation.', '',
              '| Repo/version | Scope | n | p50 ms | p95 ms | p99 ms | max ms | mean ± population SD ms |',
              '|---|---|---:|---:|---:|---:|---:|---|']
    for repo, versions in r['repos'].items():
        for version in ['main', 'parser']:
            v = versions[version]
            scopes = {'all': v['latency'], **{'tier:' + k: v['tier'].get(k, {'n': 0}) for k in ['literal', 'synonym', 'BM25 fallback', 'no-match']},
                      **{'op:' + k: t for k, t in v['operationLatency'].items()},
                      **{f'repeat:{i+1}': t for i, t in enumerate(v['repeatTimes'])}}
            for name, t in scopes.items():
                if not t['n']:
                    line(repo + '/' + version, name, 0, 'n/a', 'n/a', 'n/a', 'n/a', 'n/a'); continue
                line(repo + '/' + version, name, t['n'], *[f(t[k]) for k in ['p50', 'p95', 'p99', 'max']], f"{f(t['mean'])} ± {f(t['stddev'])}")
    lines += ['', '| Repo/version | Cold read+parse ms (3) | Cold service/index ms (3) |', '|---|---|---|']
    for repo, versions in r['repos'].items():
        for version in ['main', 'parser']:
            line(repo + '/' + version, ', '.join(f(c['loadMs']) for c in versions[version]['cold']), ', '.join(f(c['indexMs']) for c in versions[version]['cold']))
    lines += ['', '### Real HTTP overhead', '',
              '240 deterministic distributed questions × 2 repeats = 480 measured requests per repo/version, after 20 warmups. Serial loopback requests, fresh TCP connection per request, full JSON response read. Real Python WorkspaceServer → persistent Node worker → packet contract validation, not a mocked server. Each copied snapshot is explicitly rebound to that version’s query-code hashes and validated. No session capability is logged.',
              'Paired overhead subtracts each question’s median direct-service time from its HTTP time. It includes snapshot loading, integrity/contract validation, IPC, serialization, TCP and Python overhead, not just network transport; direct and HTTP timings are not simultaneous. Honcho HTTP is much slower than its JS algorithm. This card does not optimize it.', '',
              '| Repo/version | n | HTTP p50/p95/p99/max ms | Matched direct p50/p95 ms | Difference p50/p95 ms | Repeat p95 ms |',
              '|---|---:|---|---|---|---|']
    for repo, versions in r['repos'].items():
        for version in ['main', 'parser']:
            h = versions[version]['http']
            line(repo + '/' + version, h['latency']['n'], ' / '.join(f(h['latency'][k]) for k in ['p50', 'p95', 'p99', 'max']),
                 ' / '.join(f(h['pairedDirect'][k]) for k in ['p50', 'p95']), ' / '.join(f(h['pairedDifference'][k]) for k in ['p50', 'p95']),
                 ', '.join(f(t['p95']) for t in h['repeatLatency']))
    lines += ['', '### Worst 10 HTTP requests per repo/version', '', '| Repo/version | Operation | Question | ms | Response bytes |', '|---|---|---|---:|---:|']
    for repo in r['repos']:
        for version in ['main', 'parser']:
            base = ROOT / 'artifacts/variation-benchmark'
            samples = json.loads((base / f'{repo}-{version}-http-raw.json').read_text())
            inputs = {q['id']: q for q in json.loads((base / f'{repo}-{version}-http-input.json').read_text())}
            for q in sorted(samples, key=lambda q: q['ms'], reverse=True)[:10]:
                line(repo + '/' + version, q['operation'], '`' + inputs[q['id']]['question'] + '`', f(q['ms']), q['bytes'])
    for repo, versions in r['repos'].items():
        lines += ['', f'## {repo}: outcome tables', '',
                  'Each cell: correct count; correct-or-choose count/denominator (%); wrong count. Δ is percentage-point gain in correct-or-choose.', '']
        for group in ['operation', 'axis', 'kindAgreement', 'matrix']:
            lines += [f'### {group}', '', '| Axis / operation / phrase × form | Main | Parser | Δ pp |', '|---|---|---|---:|']
            for key, p in versions['parser'][group].items():
                m = versions['main'][group][key]
                def outcome(c):
                    return f"{pct(c['correct'], c['total'])} correct; {pct(c['correct'] + c['choose-correct'], c['total'])}; {c['wrong']} wrong"
                line(key, outcome(m), outcome(p), f"{p['successPct'] - m['successPct']:+.2f}")
        lines += ['', '### Worst axes by parser success (not independent causal effects)', '']
        for key, p in sorted(versions['parser']['axis'].items(), key=lambda kv: kv[1]['successPct'])[:8]:
            lines.append(f"- {key}: {pct(p['correct'] + p['choose-correct'], p['total'])}.")
        for version in ['main', 'parser']:
            lines += ['', f'### {version}: 15 most frequent failure patterns', '', '| Pattern | Count | Example → observed status / operation |', '|---|---:|---|']
            for key, data in versions[version]['failures']:
                e = data['examples'][0]
                line(key, data['count'], f"`{e['question']}` → {e['status']} / {e['operation']}; expected {e['target']}; selected {e['actual']}")
            lines += ['', f'### {version}: worst 10 direct queries', '', '| Operation | Question | Three timings (ms) |', '|---|---|---|']
            for q in versions[version]['slowest']:
                line(q['operation'], '`' + q['question'] + '`', ', '.join(f(t) for t in q['ms']))
        lines += ['', '### Negative outcomes', '', '| Version | No-match | Unresolved choices | Overconfident |', '|---|---:|---:|---:|']
        for version in ['main', 'parser']:
            n = versions[version]['negative']; line(version, pct(n['no-match'], n['total']), pct(n['unresolved'], n['total']), pct(n['overconfident'], n['total']))
    checks = json.loads((ROOT / 'artifacts/variation-benchmark/verification.json').read_text())
    lines += ['', '## New confident mistakes versus main', '',
              'Aggregate improvement does not imply zero regressions. These cases are wrong on the parser but were not confidently wrong on main; generated ambiguous/mismatching-kind cases remain in this count. No parser fixes were made.', '']
    for repo, check in checks.items():
        lines.append(f"- {repo}: {check['newWrongCases']} newly confident-wrong generated cases.")
        for example in check['newWrongExamples'][:3]:
            lines.append(f"  - `{example['question']}`: expected {example['operation']} on {example['expected']}; got {example['actualOperation']} on {example['actual']}.")
    lines += ['', '## Verification and retained attempts', '',
              'Generator tests cover determinism, quotas, label construction, axis coverage, directed path grading, seed vs incidental selection, choice-operation checks, negative classification, deduplication and percentile arithmetic. Full suite commands and counts are recorded in the task handoff and build update.',
              'Verified: Python 458/458, JS 204/204 (including five new benchmark tests), zero final skips; scorer 47/47, alias 15/15, lookup 39/40 (existing bearer-auth expected-label limitation). Raw-row construction, all outcome/latency totals and 1,920 HTTP response statuses reconcile. Frozen target source audit passes. Product code and frozen hand-written eval files have no changes.',
              'Python first passed with two browser skips; enabling Playwright exposed missing axe-core at an old default path. Installed axe-core in ignored benchmark tooling and set PLAYWRIGHT_DIR/AXE_CORE_PATH; final unchanged full suite passed with zero skips. These environment attempts remain in the logs; no tests were relaxed.',
              'During harness development an HTTP workspace directory was missing; fixed in the harness only. A 180-second HTTP probe and a 420-second foreground run were interrupted by tool deadlines. Their logs remain local; no timing pass/fail threshold or performance-driven retries were used. Headline numbers come from the completed background run, not a selection of the fastest attempts.',
              'Remaining caveats: synthetic wording and redundant rows, no multi-axis interaction coverage, known-target bias, source graph/extractor limitations, limited typo and negative distributions, first-page grading, and non-isolated timing. Findings are measurements, not parser fixes or a claim that arbitrary questions work. Consultant second opinion is requested; approval remains with the generalist.', '']
    return '\n'.join(lines)

if __name__ == '__main__':
    target = ROOT / 'docs/VARIATION_BENCHMARK.md'
    target.write_text(render())
    print(target)
