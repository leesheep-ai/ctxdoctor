# Agent support notes

ctxdoctor models repository-visible instruction surfaces, not user or organization settings that live outside the repository.

## Codex

Codex aggregates `AGENTS.md` / `AGENTS.override.md` instructions from the project hierarchy. More specific repository instructions can override broader instructions. ctxdoctor discovers those files recursively so the hierarchy is visible even when the scan is launched from the root.

## Claude Code

Claude Code uses `CLAUDE.md` project memory and supports `@path` imports. Nested project memory and `.claude/rules` can add more specific context. ctxdoctor validates repository-local imports and maps both memory and rule artifacts.

## Cursor

Cursor supports project rules in `.cursor/rules/*.mdc`, `AGENTS.md`, and the legacy `.cursorrules`. Rules can be always-on, scoped, agent-requested, or manual based on frontmatter. v0.1 discovers them; frontmatter-level applicability simulation is on the roadmap.

## Gemini CLI

Gemini CLI uses hierarchical `GEMINI.md` context files and supports `@file.md` imports. v0.1 discovers nested context files and validates imports.

## GitHub Copilot

Repository custom instructions include `.github/copilot-instructions.md` and path-specific `.github/instructions/**/*.instructions.md`. Copilot CLI and cloud-agent surfaces can also consume agent instruction files such as `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`; support differs across Copilot experiences. v0.1 maps repository-visible artifacts conservatively; exact `applyTo` parsing is on the roadmap.
