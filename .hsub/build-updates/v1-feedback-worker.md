# V1.4 worker handoff — 2026-10-07 PDT

Branch v1-feedback from clean main c6543f6. No worker merge/push.

- Full consented opt-in query history/labels, bounded portable export/import, separate
  aliases, immutable split/heldout safeguards and matching source/scorer provenance.
- Full latest .verify.json build/test/smoke return 0. 176 Python + 150 JS tests (20 feedback);
  18 actual browser checks / 6 inspected 1280/1920 screenshots, zero errors/network.
- Browser exported 8 generated fixtures: 3 Correct / 2 Wrong / 1 Unclear / 2 unlabelled;
  4 evaluable, 0 user labels. Actual CLI original/off/on separate; bearer-auth miss kept.
- No scorer tuning. Eric runner.py intent unconfirmed; mini c real-user improvement
  deferred until enough confirmed cases and genuine heldout designation before tuning.
- Parent independently reviews/reruns and integrates/pushes; Eric collection/semantic
  review/unaided session and V1.5 pending. No real-user accuracy or v1-release claim.

Details/commands/hashes: docs/USER_EVAL_REPORT.md. Evidence local/ignored:
artifacts/feedback-verification.json, feedback-{build,test,smoke}.log,
feedback-browser.json, feedback-export-{generated,eval}.json, feedback-*.png.
Dist: dist/quest-coder.html and dist/quest-refresh/index.html regenerated.
Initial smoke failure (uppercase CSS text assertion) fixed and retained as
feedback-smoke-attempt1.log; full later gates pass. Legacy maps/scorer/eval pins untouched.
