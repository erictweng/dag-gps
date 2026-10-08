# Alias learning implementation progress

Branch `alias-learning` from verified `ba72d1b`; initially clean worktree, Eric git identity preserved. No Claude, quest-coder modifications, map/layer membership edits, network calls or remote Git actions.

Implemented opt-in correction offers, exact-text review and confirmation, repo/version-scoped local store, immutable scorer overlays, exact file precedence, conflicts, orphan quarantine, inspect/remove/clear and validated previewed merge/replace import/export. PATH learning is deliberately disabled; a separate endpoint query avoids learning a full route question.

Narrow gates: 13 pure JS alias tests and 17 real browser checks pass. Existing 19 lookup browser checks still pass, including zero persistence without explicit consent. Found `Python judge` already resolves to runner-service in the baseline: report this honestly and additionally demonstrate abstained synthetic `Python judge station` becoming accepted only after confirmation. Browser smoke development fixes: heading CSS uppercase requires case-insensitive text assertion; shipped numeric parity requires the existing 1e-12 tolerance rather than strict float equality.

Full verification and report pending. All examples are synthetic worker regressions, not supplied user evidence.
