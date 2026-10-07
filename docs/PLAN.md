# DAG GPS — v0 plan

Status: Planning (2026-10-07). Answers to kickoff questions recorded in thread 1557481353694548120.

## Goal

Ask a short question about a codebase ("where does grading live?", "what depends on the runner?", "how does a submit reach the DB?") and get an answer in milliseconds: an operation, a target, a confidence score, and a highlighted route on the architecture DAG.

## Locked answers (from Eric)

1. **Jev pattern.** A System-1 chooser: fast composite scoring, returns choices with probabilities, a confidence score, and a yes/no outcome.
2. **Mode:** plan together; **workers do all the build work**. Eric reviews and corrects maps and eval answers. Priority: understand architecture fast.
3. **DAG source:** both. A hand-drawn high-level layer (Mermaid/JSON) mapped onto folders, plus an import graph extracted automatically underneath it.
4. **First repo:** quest-coder.
5. **Surface:** a standalone HTML page.

## Verified data sources

**Jev** (read from `browser-use/jev-ultrafast` `jev_ultrafast/model.py`):
- Each observation becomes an **indexed table** (`[1] button …`, `[2] combobox …`).
- One request asks an **operation head** (CLICK / TYPE_TEXT / SELECT / DONE / BLOCKED) and **one target head per operation** together. These are speculative, and only the matching target is used.
- Each head returns `{choice, probabilities, confidence}`. `validate_choice` rejects the answer unless the probabilities cover exactly the offered ids, sum to 1 (±0.02), and the choice is the argmax.
- `BLOCKED` is the honest "I can't" answer. Model output never turns directly into an action; it is resolved against observed ids.
- The scorer is TypeSafe's hosted `api.typesafe.ai/v1/systemone` (model `jev-latest`) and needs a `TYPESAFE_API_KEY`. It is a paid external API, not a local model.

**quest-coder:**
- `origin/main` = `71bc83a`. The local `main` checkout is behind at `a035ea2`, so audit an `origin/main` export, not the working tree.
- 254 TS/JS/PY/SQL files.
- Biggest areas: `tests/unit` 50, `tests/e2e` 33, `runner/tests` 17, `supabase/migrations` 14, `app/api` 10, `components/{solve,replay,party}` 8 each, `content/{server,public}` 7 each, `runner/service` 4, `lib/supabase` 4.

**Prior art:** the `codebase-architecture-audit` skill's `scripts/import_graph.py` handles TS/JS `@/` + relative imports, Python, `fetch('/api/…')`, `.rpc()`, and SQL functions. It also has an offline HTML DAG renderer.

## v0 architecture (deliberately boring)

```text
layers.json (hand-drawn) ─┐
                           ├─► build_map.py ─► map.json ─► index.html (scorer + renderer, all in-browser)
import_graph.py (auto) ────┘
```

1. **Map (`map.json`).**
   - Layer nodes: `{id, label, desc, aliases[], globs[]}`.
   - Layer edges: typed `import | http | rpc | spawn | data`.
   - File nodes, each assigned to exactly one layer by glob. Unmapped files are reported as a finding.
   - File→file import edges, rolled up into layer→layer edges.
2. **The indexed table (the Jev analogue).** Every layer and file gets an index, like Jev's `[n] role label` table.
3. **The System-1 scorer.** Same output contract as Jev, so it can be swapped for Jev later.
   - Operation head: `LOCATE | UPSTREAM | DOWNSTREAM | PATH | NOT_SURE`.
   - Target heads: `locate_target`, `from_target`, and `to_target` over the indexed nodes, all computed in one pass.
   - Composite score per candidate: label/alias match + description tokens + path tokens + a small fan-in prior, then softmax to get `{choice, probabilities, confidence}`.
   - Yes/no: if confidence ≥ threshold, answer; otherwise answer `NOT_SURE` and show the top 3 (the BLOCKED analogue).
   - Validate the result the same way as `validate_choice`.
4. **Router.** Deterministic graph ops on the chosen target: highlight a node, ancestors, descendants, or the shortest path. No model output is used directly as a highlight; everything is resolved against map ids.
5. **Surface.** One offline `index.html` with `map.json` inlined. The scorer runs in the page, so there's no server and no network in the hot path.

Swappable backend: `scorer: "local" | "jev"`. Both return the same JSON, and the eval set (M2) scores both on the same questions.

## Out of scope for v0

- LLM free-text answers.
- Code-level Q&A ("what does this function do").
- Multiple repos in one map.
- Cabinet integration, live file watching, and editing the DAG in the UI.

## Milestones (each with a smoke test)

- **M0 — Map.** Write the quest-coder `layers.json` (I draft from folders, Eric corrects), then extract + map with `build_map.py`.
  - Smoke: 0 unresolved imports, the unmapped-file count is printed (target 0), every layer has ≥1 file, and the layer graph is acyclic (back-edges are listed if not).
- **M1 — Canvas.** `index.html` renders the layer DAG, and clicking a layer expands it to its files.
  - Smoke: a Playwright run on `file://` with 0 console errors, plus 1920×1080 screenshots.
- **M2 — Scorer + eval set.** Write `eval.jsonl` with ~30 questions, each tagged with the expected op + target, then build the scorer.
  - Smoke: prints op accuracy, target top-1/top-3, NOT_SURE rate, and p95 latency (target < 10 ms).
- **M3 — Route highlight.** Wire the answer into the canvas (node/ancestors/descendants/path) and show the confidence bar and the top-3 alternatives.
  - Smoke: 5 canonical questions, with a screenshot of each.
- **M4 (optional) — Jev backend.** The same eval set run through TypeSafe `systemone`.
  - Smoke: local vs Jev accuracy and latency side by side.

## Decisions (2026-10-07, round 2)

1. Copy Jev's approach **locally** (no TypeSafe API). M4 hosted-Jev A/B dropped unless revisited.
2. Workers build every milestone. Eric + Mini-Eric plan together; Eric corrects the layer map and eval answers.
3. Mini-Eric drafts the quest-coder layer map from folders; Eric corrects `maps/quest-coder/layers.json`.
4. Private repo `erictweng/dag-gps`.

## M0 status

Draft `maps/quest-coder/layers.json` (18 layers), checked with `scripts/check_layers.py` against quest-coder `origin/main` 71bc83a:
259 source files, 0 unmapped, 0 double-mapped, 0 empty layers, 0 layer 2-cycles. Rendered: `maps/quest-coder/layers.mmd` / `layers.png`.
M0 closes when Eric approves the map; then a worker builds `build_map.py` -> `map.json`.

## Later

- Cabinet screen.
- Multiple repos.
- An "explain this route" LLM pass on top of a confident answer.
- Learning aliases from corrected answers.
