# Agent support

ctxdoctor discovers common local instruction files:

| Agent | Files |
|---|---|
| Codex | AGENTS.md |
| Claude Code | CLAUDE.md, imported markdown files |
| Gemini CLI | GEMINI.md |
| Cursor | .cursor/rules |
| Copilot | .github/copilot-instructions.md |

The first version intentionally focuses on deterministic checks and does not call an LLM.
