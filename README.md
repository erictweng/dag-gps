# DAG GPS

A System-1 navigator for codebases. Ask a short question, get an operation, a target, a confidence score, and a highlighted route on the architecture DAG in milliseconds. It runs fully offline in one HTML page.

The pattern is borrowed from [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast): an indexed table, an operation head plus per-operation target heads, and probabilities plus confidence. Here it is implemented locally.

- Plan: `docs/PLAN.md`
- Idea capture: `docs/IDEA.md`
- First map: `maps/quest-coder/layers.json` (draft, awaiting Eric's corrections)
- Map check:
  `python3 scripts/check_layers.py maps/quest-coder/layers.json <quest-coder-repo> origin/main <import_graph.json> maps/quest-coder/layers.mmd`
