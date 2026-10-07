## Project
DAG GPS: ask a short question about a codebase and get a Jev-style answer (operation + target + probabilities + confidence) highlighted on an architecture DAG, in one offline HTML page. Read `docs/PLAN.md`, `STATUS.md`, `TASKS.md` first. M0 (`scripts/build_map.py` → `maps/quest-coder/map.json`) is verified on main.

Target repo for real data: `/Users/aibert/projects/quest-coder`, ref `origin/main`. Never read or write its working tree; build_map already exports a snapshot.
Do NOT edit `maps/quest-coder/layers.json` (Eric owns layer membership). If origin/main gained unmapped files, stop and report.
Git: repo-local author is configured. Work on the branch named below (create it from main). Commit when verified. Do not push, do not merge.

## This mini-milestone ONLY — M1.1: file-level edges in map.json
Eric approved adding file→file edges so the M1 canvas can expand a layer into its files.

1. In `scripts/build_map.py`, add a top-level `file_edges` array to map.json. Keep `edges` exactly as is (layer→layer); do not change its shape.
   Each entry: `{from, to, type, cross_layer: bool}` where from/to are file node ids (paths).
   - `import`: every JS/TS edge and every Python edge from import_graph (dedupe identical pairs).
   - `http`: caller file → the matched `app/api/.../route.ts` file (reuse `resolve_api_route`).
   - `rpc`: caller file → migration file that last defines the function, when found.
2. Add `meta.counts.file_edges` and per-type counts in the printed summary line.
3. New check (FAIL → exit 1): every file_edge endpoint is a known file node id. Include it in the existing check list.
4. Tests in `tests/test_build_map.py`: file_edges dedupe, cross_layer flag, endpoint check failing on an unknown id. Fixtures must mirror the real import_graph shapes.
5. Regenerate `maps/quest-coder/map.json` with the `.verify.json` smoke command.

Branch: `m1-file-edges`. Commit message: "M1.1: file-level edges in map.json".
Allowed files: `scripts/build_map.py`, `tests/**`, `maps/quest-coder/map.json`, `STATUS.md`, `TASKS.md`.

## Verification (paste real output in your final message)
- `python3 -m unittest discover -s tests -q`
- the smoke command in `.verify.json` (must print all checks PASS, exit 0)
- counts: file_edges total, by type, cross_layer count.

## Stop conditions
Stop and report if a check fails because of layers.json/upstream changes, or anything needs files outside the allowed list.
