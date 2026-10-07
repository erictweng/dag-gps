# DAG GPS — idea capture

Captured 2026-10-07 from Eric (Discord #general → thread "Project — DAG GPS").

## Eric's pitch (verbatim)

> I want to build a system 1 AI model like jev, but I want it from DAG diagrams and file structures only. I want it to be quick and fast, where I can pinpoint a high level architecture of a system, ask it questions and where it is, and it can point me in the right direction. Kind of like a GPS navigating through a map. The goal is to build a high-level DAG diagram, and then my model can process that DAG diagram and quickly respond and highlight the structure of the diagram depending on my quick easy questions.

## Mini-Eric's first read

- "System 1" = fast/intuitive, no slow reasoning in the hot path.
- Inputs: a high-level architecture DAG + the repo's file tree. Nothing else.
- Interaction: quick questions ("where does auth live?", "what breaks if I change X?", "how does a request get from A to B?") → the diagram lights up the relevant nodes/paths.
- GPS metaphor: the map is precomputed; a query is a lookup + route, not a think.

## Open questions (asked in thread, unanswered)

1. What is "jev"?
2. Learn mode or build mode?
3. DAG source: hand-authored (Mermaid/JSON) vs auto-extracted from imports vs both (hand-drawn layer mapped onto folders)?
4. First repo to test against.
5. Surface: standalone HTML, Cabinet screen, or CLI.

## Related prior art in this workspace

- Skill `codebase-architecture-audit` already has `scripts/import_graph.py` (TS/JS/Python import graph → JSON) and an offline HTML DAG renderer. Candidate starting point for the "map".
