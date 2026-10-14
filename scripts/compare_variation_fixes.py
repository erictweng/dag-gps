#!/usr/bin/env python3
"""Compare corrected-grid receipts; never silently compare different questions."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/question-parser/benchmark-fixes'


def read(path):
    return json.loads(path.read_text())


def main():
    before = read(OUT / 'baseline/variation_results.json')
    after = read(ROOT / 'eval/variation_results.json')
    assert before['templatesSha256'] == after['templatesSha256']
    checks_before = read(OUT / 'baseline/raw/verification.json')
    checks_after = read(ROOT / 'artifacts/variation-benchmark/verification.json')
    result = {}
    lines = ['# Question-parser benchmark fixes', '',
             'Corrected-grid before/after, same seed, templates, targets and pins. Counts are strict construction labels, not real-user accuracy.', '',
             '| Repo / axis | N | Correct before → after | Correct-or-choose before → after | Wrong before → after |',
             '|---|---:|---:|---:|---:|']
    for repo in ['honcho', 'salesroom']:
        b, a = before['repos'][repo], after['repos'][repo]
        assert b['gridSha256'] == a['gridSha256']
        b, a = b['parser'], a['parser']
        groups = [('total', b['positive'], a['positive'])]
        groups.extend((key, b['axis'][key], value) for key, value in a['axis'].items()
                      if key.startswith(('punctuation:', 'target-form:stem', 'target-form:folder-name', 'target-form:synonym:')))
        groups.extend(('construction:' + key, b['constructionStratum'][key], value)
                      for key, value in a['constructionStratum'].items())
        for key, old, new in groups:
            assert old['total'] == new['total']
            lines.append(f"| {repo} / {key} | {new['total']} | {old['correct']} → {new['correct']} | "
                         f"{old['correct'] + old['choose-correct']} → {new['correct'] + new['choose-correct']} | {old['wrong']} → {new['wrong']} |")
        def rows(path):
            return [json.loads(line) for line in path.read_text().splitlines()]
        old_rows = rows(OUT / f'baseline/raw/{repo}-parser.jsonl')
        new_rows = rows(ROOT / f'artifacts/variation-benchmark/{repo}-parser.jsonl')
        assert len(old_rows) == len(new_rows)
        for x, y in zip(old_rows, new_rows):
            assert (x['id'], x['question'], x['targets']) == (y['id'], y['question'], y['targets'])
        turned_choice = sum(x['outcome'] == 'correct' and y['status'] == 'needs-choice' for x, y in zip(old_rows, new_rows))
        new_wrong = sum(x['outcome'] != 'wrong' and y['outcome'] == 'wrong' for x, y in zip(old_rows, new_rows))
        choice_with_target = sum(x['outcome'] == 'correct' and y['outcome'] == 'choose-correct' for x, y in zip(old_rows, new_rows))
        frozen_b, frozen_a = read(OUT / f'frozen-{repo}-before.json'), read(OUT / f'frozen-{repo}-after.json')
        assert frozen_b['datasetSha256'] == frozen_a['datasetSha256']
        old_cases = {r['id']: r for r in frozen_b['results']}
        frozen_new_wrong = sum(r['wrong'] and not old_cases[r['id']]['wrong'] for r in frozen_a['results'])
        result[repo] = dict(correctToChoice=turned_choice, newWrongVersusParserBefore=new_wrong,
                            correctToChoiceContainingTarget=choice_with_target,
                            newWrongStrata={key: sum(x['outcome'] != 'wrong' and y['outcome'] == 'wrong' and y['constructionStratum'] == key
                                                    for x, y in zip(old_rows, new_rows))
                                            for key in ['unambiguous', 'ambiguous', 'mismatching-kind']},
                            newWrongVersusMainBefore=checks_before[repo]['newWrongCases'],
                            newWrongVersusMainAfter=checks_after[repo]['newWrongCases'],
                            negativeBefore=b['negative'], negativeAfter=a['negative'],
                            directP95Before=b['latency']['p95'], directP95After=a['latency']['p95'],
                            frozenNewWrong=frozen_new_wrong, frozenBefore=frozen_b['splits'], frozenAfter=frozen_a['splits'])
        result[repo]['acceptance'] = {
            'periodEqualsQuestionMark': a['axis']['punctuation:.'] == a['axis']['punctuation:?'],
            'fewerWrong': a['positive']['wrong'] < b['positive']['wrong'],
            'zeroOverconfidentNegatives': a['negative']['overconfident'] == 0,
            'zeroNewFrozenWrong': frozen_new_wrong == 0,
            'holdoutMatchesRetained': frozen_a['splits']['holdout']['matchCorrect'] >= frozen_b['splits']['holdout']['matchCorrect'],
            'directP95Under2ms': a['latency']['p95'] < 2,
        }
    lines += ['', '## Safety and speed', '', '| Repo | Correct → choice | New wrong vs pre-fix | New wrong vs main before → after | Overconfident negatives before → after | Direct p95 ms before → after |', '|---|---:|---:|---:|---:|---:|']
    for repo, r in result.items():
        lines.append(f"| {repo} | {r['correctToChoice']} | {r['newWrongVersusParserBefore']} | {r['newWrongVersusMainBefore']} → {r['newWrongVersusMainAfter']} | {r['negativeBefore']['overconfident']} → {r['negativeAfter']['overconfident']} | {r['directP95Before']:.3f} → {r['directP95After']:.3f} |")
    lines += ['', '## Frozen hand-written sets', '', '| Repo / split | Correct matches before → after | Correct choices before → after | Wrong before → after | Negative no-match before → after |', '|---|---:|---:|---:|---:|']
    for repo, r in result.items():
        for split, a in r['frozenAfter'].items():
            b = r['frozenBefore'][split]
            lines.append(f"| {repo}/{split} | {b['matchCorrect']} → {a['matchCorrect']} | {b['chooseCorrect']} → {a['chooseCorrect']} | {b['wrong']} → {a['wrong']} | {b['noMatchCorrect']} → {a['noMatchCorrect']} |")
    lines.append('\nNew wrong frozen answers versus pre-fix: ' + ', '.join(f"{repo}={r['frozenNewWrong']}" for repo, r in result.items()) + '.\n')
    lines += ['', '## Interpretation and retained limits', '',
              '- The synonym table is unchanged and literal names retain priority. A generated `db` intention for a folder named `database` is therefore still allowed to disagree with a valid literal `db` file answer. The safer new policy asks when comparable literal kinds or synonym-only candidates compete; it does not erase useful literals to satisfy invented intentions.',
              '- The before/after grid is identical. The correction preceding it added omitted supported patterns and file PATH pairs; the original narrower receipt is preserved in Git at `2f7a2fb`. Corrected baseline summary: `eval/variation_before_benchmark_fixes.json` (query code unchanged at `103b6e5`).',
              '- New wrong counts include strict construction-label collisions and mismatching kinds, not just definite regressions. Restoring period support also exposes pre-existing interpretation mistakes that formerly abstained; see the diagnostic counts below.',
              '- The seven newly wrong Salesroom cases are period-ending LOCATE variants of `app/(seller)/seller`. Their question-mark counterparts were already wrong before this change: the existing parenthesized-route-path normalization loses the literal path. This is a real retained parser limitation, not an ambiguous-label excuse. Keeping consistent punctuation handling still reduces total wrong answers on both repos.',
              '- First-page grading can count a choice as unresolved if the intended target is absent from that page. Correct-to-choice counts are disclosed rather than treating every abstention as success.', '',
              '| Repo | Correct → choice containing intended target | New wrong unambiguous / ambiguous / mismatching-kind | Acceptance checks |',
              '|---|---:|---|---|']
    for repo, r in result.items():
        lines.append(f"| {repo} | {r['correctToChoiceContainingTarget']} / {r['correctToChoice']} | "
                     + ' / '.join(str(v) for v in r['newWrongStrata'].values()) + ' | '
                     + '; '.join(key + ': ' + ('pass' if value else 'not met') for key, value in r['acceptance'].items()) + ' |')
    (ROOT / 'eval/variation_fixes_comparison.json').write_text(json.dumps(result, indent=2) + '\n')
    (ROOT / 'docs/QUESTION_PARSER_BENCHMARK_FIXES.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
