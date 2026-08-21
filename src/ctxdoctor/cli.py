from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .scanner import scan

AGENT_ORDER = ("codex", "claude", "cursor", "gemini", "copilot")
SYMBOL = {"error": "E", "warning": "W", "info": "I"}


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _render_map(result) -> str:
    rows = []
    for agent in AGENT_ORDER:
        items = [a for a in result.artifacts if agent in a.agents]
        always = [_rel(a.path, result.root) for a in items if a.always_on]
        scoped = [_rel(a.path, result.root) for a in items if not a.always_on]
        rows.append((agent, ", ".join(always) or "—", ", ".join(scoped) or "—"))
    widths = [max(len(row[i]) for row in [("Agent", "Always-on / inherited", "Scoped / on-demand"), *rows]) for i in range(3)]
    header = f"{'Agent':<{widths[0]}}  {'Always-on / inherited':<{widths[1]}}  Scoped / on-demand"
    sep = "-" * len(header)
    body = [header, sep]
    for row in rows:
        body.append(f"{row[0]:<{widths[0]}}  {row[1]:<{widths[1]}}  {row[2]}")
    return "\n".join(body)


def _as_json(result) -> dict:
    return {
        "version": __version__,
        "root": str(result.root),
        "artifacts": [
            {
                "path": _rel(a.path, result.root),
                "kind": a.kind,
                "agents": list(a.agents),
                "scope": a.scope,
                "always_on": a.always_on,
            }
            for a in result.artifacts
        ],
        "findings": [
            {
                "code": f.code,
                "severity": f.severity,
                "path": _rel(f.path, result.root),
                "line": f.line,
                "message": f.message,
                "hint": f.hint,
            }
            for f in result.findings
        ],
        "counts": result.counts(),
    }


def _exit_code(result, fail_on: str) -> int:
    counts = result.counts()
    if fail_on == "never":
        return 0
    if fail_on == "warning" and (counts["warning"] or counts["error"]):
        return 1
    if fail_on == "error" and counts["error"]:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ctxdoctor",
        description="Map coding-agent context files and catch instruction drift.",
    )
    parser.add_argument("path", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--fail-on", choices=("error", "warning", "never"), default="error",
        help="CI failure threshold (default: error)",
    )
    parser.add_argument("--version", action="version", version=f"ctxdoctor {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path)
    if not root.exists() or not root.is_dir():
        print(f"ctxdoctor: not a directory: {root}", file=sys.stderr)
        return 2
    result = scan(root)
    if args.json:
        print(json.dumps(_as_json(result), indent=2))
        return _exit_code(result, args.fail_on)

    counts = result.counts()
    print(f"ctxdoctor {__version__} — {len(result.artifacts)} instruction artifact(s)\n")
    print(_render_map(result))
    print()
    if result.findings:
        print(f"{len(result.findings)} drift risk(s):")
        for finding in result.findings:
            path = _rel(finding.path, result.root)
            print(f"{SYMBOL[finding.severity]} {finding.code} {path}:{finding.line}  {finding.message}")
            if finding.hint:
                print(f"  ↳ {finding.hint}")
    else:
        print("✓ No deterministic drift risks found.")
    print(f"\nerrors {counts['error']} · warnings {counts['warning']} · info {counts['info']}")
    return _exit_code(result, args.fail_on)


if __name__ == "__main__":
    raise SystemExit(main())
