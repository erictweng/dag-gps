# Status — DAG GPS

Last updated: 2026-10-07

## Current Focus

M0 `build_map.py` is done. Next: M1 (canvas), once Eric extends `layers.json` to cover
the files added to quest-coder `origin/main` since `71bc83a` (see Blockers).

## Active Worker

None.

## Last Verified

2026-10-07, branch `m0-build-map`:

- `python3 -m unittest discover -s tests -q` — 63 tests, OK.
- `python3 scripts/build_map.py --repo … --ref 71bc83a --layers maps/quest-coder/layers.json
  --out maps/quest-coder/map.json` — 8/8 checks passed, exit 0.
  18 layers + 259 files = 277 nodes, 52 edges (import 43, http 6, build 1, data 1, realtime 1),
  238 KB. `maps/quest-coder/map.json` is committed at this ref.

## Blockers

The `.verify.json` smoke command targets `origin/main`, which moved past the approved
map commit `71bc83a` during the M0 run (→ `9e3dbc8` → `c6e2e49` → `749d8b5`). At
`749d8b5` the unmapped check FAILs with 4 files that no glob in `layers.json` covers:

- `lib/party-lock.ts`, `lib/party-lock-server.ts` (PR #88, party lock)
- `lib/story-beats.ts`, `lib/story-scenes.ts`

Eric owns layer membership, so the worker did not touch the map. Either extend
`layers.json` with globs for these four files, or pin `.verify.json`'s smoke to a ref.
`build_map.py` itself is green at `71bc83a`, `9e3dbc8` and `c6e2e49`.

## Rule

Complete and verify one mini-milestone before launching the next worker.
Update this file whenever a worker starts, finishes, or gets blocked.
