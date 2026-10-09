# Workspace UI and graph view (M2.3)

`python3 -m app.server`, then open the printed private link.

## Layout

- **Files** (left): the full inventory with a filter. Files the extractor did not
  map are marked `(not mapped)`. The list shows up to 2,000 rows; filter to narrow.
- **Ask + graph** (center): a question box, a legend, and the dependency graph.
- **Evidence** (right): the answer status and reason, choices when ambiguous,
  answer files with their witness chains, file details (group, lines, SHA-256,
  extraction status, observed imports and importers), and limitations.

## Graph (`web/graph-view.js`)

- Columns run from consumers on the left to dependencies on the right. A file's
  column is the longest consumer depth of its strongly connected component, so
  files in a genuine import cycle share a column. Every edge is kept, and cycle
  edges are drawn as dashed back-arcs.
- Proposed groups (folder labels) are horizontal lanes sorted by label.
- Layout is deterministic regardless of input order and unit-tested for
  no-overlap and complete edges.
- Above 1,500 mapped files it draws a proposed-group overview with a notice, and
  the file list and questions still reach every file.
- Labels are SVG text nodes; nothing is parsed as HTML.

## Highlight rules

- `matched` answers highlight exactly the packet's selected nodes and edges and
  dim the rest. The node asked about gets an amber outline, relevant nodes blue,
  and potentially affected nodes a red dashed outline. The legend states the
  styles in words, so state is not shown by colour alone.
- `needs-choice`, `no-match`, `unsupported` and `stale` never dim or highlight
  anything; the choices appear in the evidence panel.
- `no-path` marks only the two endpoints, without dimming or a claimed route.
- Selecting a file highlights it with its direct observed import links.
- Escape or Clear removes every highlight and returns focus to the question box.

## Behaviour

- After an import, focus moves to the question box. A failed import shows the
  error, leaves the current project loaded and keeps the form ready to retry.
- Switching revisions within a project keeps the graph scroll position.
- The page is keyboard-operable (file list, results, choices, file details;
  details take focus) and responsive: three panels at 1280 px and wider, one
  column at 390 px with no page-level horizontal overflow.
- Reduced motion disables smooth scrolling and transitions.

## Verification

- `node --test tests/graph-view.test.cjs`: layout and highlight rules.
- `python3 -m unittest discover -s tests -p test_workspace_ui.py`: a real
  Chromium session against a live loopback server and local fixture repository.
  It covers import, typed question plus Enter, exact highlights, an ambiguous
  question with no dimming, choice, Escape, keyboard and graph selection,
  unmapped files, inert hostile file names, failed-import recovery, real CSP
  blocking inline script, axe (WCAG 2.1 A/AA) at 1920, 1280 and 390 px, and no
  external requests or page errors. It skips if Playwright is unavailable.
- `scripts/smoke_workspace_server.cjs`: the same flow against a real GitHub import.

## Not yet

There is no fit-to-screen zoom yet; wide graphs scroll. Source excerpts and
agent explanations are M3; live refresh is M4.
