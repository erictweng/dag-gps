# Question-parser benchmark fixes

Corrected-grid before/after, same seed, templates, targets and pins. Counts are strict construction labels, not real-user accuracy.

| Repo / axis | N | Correct before → after | Correct-or-choose before → after | Wrong before → after |
|---|---:|---:|---:|---:|
| honcho / total | 92856 | 67450 → 85135 | 72179 → 89243 | 800 → 380 |
| honcho / punctuation:? | 2988 | 2390 → 2958 | 2390 → 2958 | 0 → 0 |
| honcho / punctuation:. | 2988 | 0 → 2958 | 1150 → 2958 | 0 → 0 |
| honcho / target-form:folder-name | 576 | 108 → 108 | 266 → 446 | 288 → 108 |
| honcho / target-form:stem | 2088 | 924 → 888 | 1710 → 1924 | 308 → 118 |
| honcho / target-form:synonym:config | 36 | 0 → 0 | 0 → 0 | 4 → 2 |
| honcho / target-form:synonym:configuration | 144 | 0 → 0 | 0 → 0 | 128 → 80 |
| honcho / target-form:synonym:database | 36 | 0 → 0 | 0 → 0 | 36 → 36 |
| honcho / target-form:synonym:db | 36 | 0 → 0 | 0 → 0 | 36 → 36 |
| honcho / target-form:synonym:environment | 72 | 0 → 0 | 72 → 72 | 0 → 0 |
| honcho / target-form:synonym:msg | 144 | 0 → 0 | 99 → 132 | 0 → 0 |
| honcho / target-form:synonym:settings | 180 | 0 → 0 | 99 → 165 | 0 → 0 |
| honcho / construction:ambiguous | 1998 | 214 → 202 | 1408 → 1533 | 364 → 306 |
| honcho / construction:mismatching-kind | 20958 | 17112 → 20284 | 17112 → 20284 | 0 → 0 |
| honcho / construction:unambiguous | 69900 | 50124 → 64649 | 53659 → 67426 | 436 → 74 |
| salesroom / total | 51410 | 34968 → 46358 | 37555 → 48257 | 777 → 712 |
| salesroom / punctuation:? | 1666 | 1216 → 1594 | 1245 → 1623 | 7 → 7 |
| salesroom / punctuation:. | 1666 | 0 → 1594 | 825 → 1623 | 0 → 7 |
| salesroom / target-form:folder-name | 396 | 252 → 252 | 324 → 360 | 36 → 0 |
| salesroom / target-form:stem | 1476 | 900 → 864 | 1137 → 1173 | 36 → 0 |
| salesroom / target-form:synonym:authentication | 36 | 0 → 0 | 0 → 0 | 0 → 0 |
| salesroom / target-form:synonym:database | 36 | 36 → 36 | 36 → 36 | 0 → 0 |
| salesroom / target-form:synonym:environment | 36 | 36 → 36 | 36 → 36 | 0 → 0 |
| salesroom / target-form:synonym:repository | 36 | 36 → 36 | 36 → 36 | 0 → 0 |
| salesroom / construction:ambiguous | 468 | 36 → 0 | 381 → 453 | 72 → 0 |
| salesroom / construction:mismatching-kind | 11412 | 8608 → 10560 | 8608 → 10560 | 136 → 136 |
| salesroom / construction:unambiguous | 39530 | 26324 → 35798 | 28566 → 37244 | 569 → 576 |

## Safety and speed

| Repo | Correct → choice | New wrong vs pre-fix | New wrong vs main before → after | Overconfident negatives before → after | Direct p95 ms before → after |
|---|---:|---:|---:|---:|---:|
| honcho | 36 | 0 | 149 → 61 | 0 → 0 | 0.814 → 1.080 |
| salesroom | 36 | 7 | 542 → 535 | 0 → 0 | 0.121 → 0.232 |

## Frozen hand-written sets

| Repo / split | Correct matches before → after | Correct choices before → after | Wrong before → after | Negative no-match before → after |
|---|---:|---:|---:|---:|
| honcho/dev | 46 → 46 | 12 → 13 | 2 → 1 | 16 → 16 |
| honcho/holdout | 18 → 18 | 5 → 5 | 0 → 0 | 4 → 4 |
| salesroom/dev | 20 → 20 | 5 → 5 | 0 → 0 | 6 → 6 |
| salesroom/holdout | 7 → 7 | 0 → 0 | 0 → 0 | 2 → 2 |

New wrong frozen answers versus pre-fix: honcho=0, salesroom=0.


## Interpretation and retained limits

- The synonym table is unchanged and literal names retain priority. A generated `db` intention for a folder named `database` is therefore still allowed to disagree with a valid literal `db` file answer. The safer new policy asks when comparable literal kinds or synonym-only candidates compete; it does not erase useful literals to satisfy invented intentions.
- The before/after grid is identical. The correction preceding it added omitted supported patterns and file PATH pairs; the original narrower receipt is preserved in Git at `2f7a2fb`. Corrected baseline summary: `eval/variation_before_benchmark_fixes.json` (query code unchanged at `103b6e5`).
- New wrong counts include strict construction-label collisions and mismatching kinds, not just definite regressions. Restoring period support also exposes pre-existing interpretation mistakes that formerly abstained; see the diagnostic counts below.
- The seven newly wrong Salesroom cases are period-ending LOCATE variants of `app/(seller)/seller`. Their question-mark counterparts were already wrong before this change: the existing parenthesized-route-path normalization loses the literal path. This is a real retained parser limitation, not an ambiguous-label excuse. Keeping consistent punctuation handling still reduces total wrong answers on both repos.
- First-page grading can count a choice as unresolved if the intended target is absent from that page. Correct-to-choice counts are disclosed rather than treating every abstention as success.

| Repo | Correct → choice containing intended target | New wrong unambiguous / ambiguous / mismatching-kind | Acceptance checks |
|---|---:|---|---|
| honcho | 36 / 36 | 0 / 0 / 0 | periodEqualsQuestionMark: pass; fewerWrong: pass; zeroOverconfidentNegatives: pass; zeroNewFrozenWrong: pass; holdoutMatchesRetained: pass; directP95Under2ms: pass |
| salesroom | 36 / 36 | 7 / 0 / 0 | periodEqualsQuestionMark: pass; fewerWrong: pass; zeroOverconfidentNegatives: pass; zeroNewFrozenWrong: pass; holdoutMatchesRetained: pass; directP95Under2ms: pass |
