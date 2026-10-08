# V1.3 onboarding — implementation / focused gates

Branch `v1-onboarding` from clean `a5b02554e479b5184204ab6aa7c7190d6605fe91`.
Deterministic pinned folder drafts, standalone offline review editor, exact-file reviewed
export and builder validation implemented. Existing legacy glob specs remain compatible.
Focused gates: 15 new Python + 18 new JS tests pass. Initial migration-warning regression
captured in `artifacts/onboarding-red.log`, then corrected.

Actual Playwright roundtrip passed on BOTH real pins: self a5b0255 (48 files, 3 layers,
38 file links), quest 749d8b5 (272 files, 38 folder proposals, 415 file links).
14 browser checks, 10 screenshots, zero errors/external requests; downloaded JSON used
by the actual builder, then real-file Ask; invalid ownership preserves all four outputs.
Quest runner-client split creates a real grouping cycle and UI merge repairs it without
removing any file links. Existing quest layers/map/tours not overwritten.

Important discovered limit: self all-source scan fails on archived smoke_refresh.cjs's
runtime-generated untracked artifacts/refresh-fixture.json. The failing draft is retained,
shown and cannot export. Supported demo explicitly excludes ONLY that JS extraction input,
retains the full 48-file assignment inventory, and records 47 scanned / 1 unscanned.
No generated data injection, source-pin change or extractor guessing. Unsupported Python
search-path constructs remain reported rather than inferred. This is scope evidence, not
full runtime completeness. Eric semantic review remains pending; automated samples are
not Eric-approved architecture. Full legacy gates and final review still underway.
