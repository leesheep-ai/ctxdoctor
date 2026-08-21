# ctxdoctor

[![CI](https://github.com/leesheep-ai/ctxdoctor/actions/workflows/ci.yml/badge.svg)](https://github.com/leesheep-ai/ctxdoctor/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**See what your coding agents actually read — and catch instruction drift before they do.**

Your repo may contain `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Cursor rules, Copilot instructions, and a growing pile of skills. They overlap, inherit differently, and quietly go stale as commands and paths change.

`ctxdoctor` gives you one deterministic map of that context surface and flags drift without calling an LLM or sending your code anywhere.

```text
$ ctxdoctor .
ctxdoctor 0.1.0 — 6 instruction artifact(s)

Agent    Always-on / inherited   Scoped / on-demand
-----------------------------------------------------
codex    AGENTS.md               services/api/AGENTS.md
claude   CLAUDE.md               .claude/rules/testing.md
cursor   AGENTS.md               .cursor/rules/react.mdc
gemini   GEMINI.md               —
copilot  —                       .github/instructions/python.instructions.md

2 drift risk(s):
E CTX001 CLAUDE.md:7  imported context file does not exist: docs/testing.md
W CTX101 AGENTS.md:21 package script is not defined in package.json: test:unit
```

## Why this exists

Coding agents now have their own repository instruction systems. The hard part is no longer creating one markdown file; it is keeping **multiple instruction surfaces aligned with the repository and with each other**.

Common failure modes:

- an instruction says `pnpm test:unit`, but that script was renamed months ago;
- `CLAUDE.md` imports a file that moved;
- `AGENTS.md` and `GEMINI.md` started as copies and now disagree;
- nested rules exist, but nobody can see which agent they affect;
- a repo accumulates tool-specific files until no human knows the effective context anymore.

`ctxdoctor` treats those files like code: discover them, map them, verify their references, and fail CI when they rot.

Recent empirical work makes this maintenance problem more important, not less. A 2026 ETH Zurich study found that unnecessary repository context can increase agent cost by more than 20% without improving task success, while another 2026 study reported efficiency gains from well-maintained `AGENTS.md` files. The shared lesson is that **context quality matters**; `ctxdoctor` focuses on claims a repository can verify deterministically.

- Gloaguen et al., *Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?* — https://arxiv.org/abs/2602.11988
- Lulla et al., *On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents* — https://arxiv.org/abs/2601.20404

## Supported instruction surfaces

| Agent | Discovered today |
| --- | --- |
| OpenAI Codex | `AGENTS.md`, `AGENTS.override.md`, `.agents/skills/**/SKILL.md` |
| Claude Code | `CLAUDE.md`, `.claude/rules/**/*.md`, `.claude/skills/**/SKILL.md` |
| Cursor | `AGENTS.md`, `.cursor/rules/**/*.mdc`, `.cursorrules`, `.cursor/skills/**/SKILL.md` |
| Gemini CLI | `GEMINI.md`, shared skills |
| GitHub Copilot | `.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md`, plus agent instruction files on supported Copilot surfaces |

The map is intentionally conservative: it reports repository-visible instruction artifacts and whether they are normally inherited/always-on versus scoped/on-demand. User- and organization-level cloud rules are outside a repository scan.

## Install

Requires Python 3.10+ and has **zero runtime dependencies**.

```bash
pipx install git+https://github.com/leesheep-ai/ctxdoctor.git
# or, from a clone
python -m pip install -e .
```

Then run:

```bash
ctxdoctor .
```

Machine-readable output:

```bash
ctxdoctor . --json
```

CI mode:

```bash
ctxdoctor . --fail-on warning
```

Exit codes are stable: `0` means the configured threshold passed, `1` means findings crossed it, and `2` means the CLI invocation was invalid.

## Checks

### `CTX001` — broken context import

Checks `@path/to/file` imports in Claude, Gemini, and Cursor instruction files. Missing imports are errors.

### `CTX002` — stale referenced path

Checks path-like values wrapped in backticks, such as `docs/architecture.md`. Missing paths are warnings.

### `CTX101` — stale package script

When a repository has `package.json`, verifies documented `npm run`, `pnpm`, `yarn`, and `bun run` script names.

### `CTX102` — stale Make target

When a repository has a `Makefile`, verifies documented `make target` names.

### `CTX201` — cross-agent instruction divergence

Flags root `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` files that partially duplicate each other but have drifted apart. The recommended pattern is one source of truth plus tool-specific imports/references.

## Design principles

- **No LLM required.** Results should be reproducible in CI.
- **No network calls.** Source code and instructions stay local.
- **Low false-positive bias.** `ctxdoctor` only checks claims it can verify deterministically.
- **Cross-agent, not vendor-specific.** The problem is repository context, not one model.
- **Useful before clever.** A broken test command is more actionable than a vague “prompt quality score.”

## GitHub Actions

The shortest setup is the bundled composite action:

```yaml
name: Context hygiene
on: [push, pull_request]

jobs:
  ctxdoctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: leesheep-ai/ctxdoctor@v0
        with:
          fail-on: warning
```

The action uses the repository's own zero-dependency Python source directly and exposes a JSON report path as the `report` output.

## Roadmap

- exact per-path effective-context simulation (`ctxdoctor explain src/foo.ts`)
- `AGENTS.override.md` precedence visualization
- Cursor MDC frontmatter/glob validation
- Copilot `applyTo` scope parsing
- package-manager workspace awareness
- SARIF output for GitHub Code Scanning
- editor-friendly JSON schema and pre-commit hook

## Status

`v0.1.0` is intentionally small: discovery, mapping, deterministic drift checks, JSON output, and CI gating. Rule semantics will expand only when they can be tested against documented agent behavior.

## Contributing

Issues and pull requests are welcome. New checks should be deterministic, explainable, and include fixtures for both true and false positives.

## License

MIT © 2026 leesheep-ai
