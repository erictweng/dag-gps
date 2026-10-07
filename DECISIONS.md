# Decisions

Record durable decisions here. One entry per decision, newest at the bottom.

Format:

```text
## YYYY-MM-DD — <title>

Context: <why this came up>
Decision: <what was decided>
Why: <reasoning>
Tradeoffs: <what we gave up>
```

## 2026-10-07 — Project workspace initialized

Context: Need a durable file structure for Hermes orchestration and Claude Code workers.
Decision: Use the standard `hproj` layout (PROJECT/TASKS/STATUS/DECISIONS/NOTES/AGENTS, `docs/`, `.hsub/`, `.claude/agents/`, `.verify.json`).
Why: Keeps durable context in files instead of the chat context window.
Tradeoffs: Slight upfront structure overhead; much better continuity across workers.
