# ctxdoctor

See what your coding agents actually read — and catch instruction drift before they do.

`ctxdoctor` is a zero-runtime-dependency CLI for auditing coding-agent instruction files across a repository. It discovers the files used by Codex, Claude Code, Cursor, Gemini CLI, and GitHub Copilot, then checks them for stale imports, broken paths, invalid package scripts, missing Make targets, and cross-agent drift.

## Why

Coding agents increasingly rely on repository-local instructions such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules`, and `.github/copilot-instructions.md`. These files quietly become part of your build system: when they drift from the real repository, agents follow instructions that no longer exist.

`ctxdoctor` makes those instructions testable.

## Quick start

```bash
pip install ctxdoctor
ctxdoctor .
```

Or run it directly from a checkout:

```bash
python -m ctxdoctor .
```

Example output:

```text
ctxdoctor: scanning .

✓ discovered AGENTS.md          [codex]
✓ discovered CLAUDE.md          [claude]
✓ discovered GEMINI.md          [gemini]

WARN CLAUDE.md:12  missing path: docs/architecture.md
WARN AGENTS.md:18  package script does not exist: pnpm test:unit
WARN root          overlapping root instructions differ across agents

3 findings
```

Machine-readable output:

```bash
ctxdoctor . --json
```

## GitHub Action

Use `ctxdoctor` as a CI gate without installing anything in your repository:

```yaml
name: Agent context check

on:
  pull_request:
  push:

jobs:
  ctxdoctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: leesheep-ai/ctxdoctor@v0
```

## What it checks

- Discovers common instruction files for Codex, Claude Code, Cursor, Gemini CLI, and GitHub Copilot.
- Resolves lightweight `@file` imports used by instruction files.
- Flags referenced repository paths that no longer exist.
- Flags package-manager commands that reference missing scripts.
- Flags `make <target>` commands when the target is absent from the repository Makefile.
- Detects overlapping root-level agent instruction files that have drifted apart.
- Emits human-readable or JSON output for CI and automation.

See [`docs/agent-support.md`](docs/agent-support.md) for the current discovery model and deliberate limitations.

## Philosophy

`ctxdoctor` does **not** generate another giant prompt file. It treats agent context as configuration: small, explicit, reviewable, and continuously checked against the repository it describes.

The first release intentionally uses deterministic local checks instead of an LLM. That keeps it fast, private, reproducible, and useful in CI.

## Development

```bash
python -m unittest discover -s tests -v
python -m ctxdoctor .
```

Python 3.10+ is supported. Runtime dependencies: none.

## Status

`ctxdoctor` is early-stage. The cross-agent configuration formats are evolving, so discovery is intentionally conservative. Contributions that add well-documented, testable support for new instruction formats are welcome.

## License

MIT
