# Contributor instructions

ctxdoctor is a zero-runtime-dependency Python CLI. Keep checks deterministic: never execute commands found in scanned instruction files and never require network access for analysis.

## Commands

- Run the test suite with `PYTHONPATH=src python3 -m unittest discover -s tests -v`.
- Smoke-test the CLI with `PYTHONPATH=src python3 -m ctxdoctor . --fail-on never`.
- Keep Python compatibility at 3.10+ unless the project metadata changes.

## Structure

- `src/ctxdoctor/` contains the CLI, discovery, and checks.
- `tests/` contains deterministic unit tests using temporary repositories.
- `docs/agent-support.md` records intentionally conservative support boundaries.

## Rule changes

- Add a true-positive test and a nearby false-positive test.
- Prefer warnings when a repository claim is suspicious but not certainly broken.
- Do not add model-based scoring to the core scan path.
