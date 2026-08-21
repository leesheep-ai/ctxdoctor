from __future__ import annotations

import json
import re
from pathlib import Path

from .model import Artifact, Finding

IMPORT_RE = re.compile(r"(?<![`\w])@(?P<path>(?:\.?\.?/|~/)[^\s`),]+|[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+|[A-Za-z0-9_.-]+\.(?:md|mdc|json|toml|ya?ml))")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
NPM_RUN_RE = re.compile(r"\b(?:npm\s+run|pnpm(?:\s+run)?|yarn(?:\s+run)?|bun\s+run)\s+([A-Za-z0-9:_-]+)")
MAKE_RE = re.compile(r"\bmake\s+([A-Za-z0-9_.-]+)")
PATHISH_RE = re.compile(r"^(?:\.?\.?/)?(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.@*{}-]+/?$")


def _lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []


def _resolve_reference(root: Path, source: Path, raw: str) -> Path | None:
    value = raw.rstrip(".,:;!?")
    if value.startswith("~/"):
        return None
    if any(ch in value for ch in "*{}"):
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    if value.startswith("./") or value.startswith("../"):
        return (source.parent / candidate).resolve()
    return (root / candidate).resolve()


def check_imports(root: Path, artifact: Artifact) -> list[Finding]:
    findings: list[Finding] = []
    if artifact.kind not in {"claude-memory", "gemini-context", "cursor-rule", "copilot-instructions"}:
        return findings
    in_fence = False
    for lineno, line in enumerate(_lines(artifact.path), 1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in IMPORT_RE.finditer(line):
            target = _resolve_reference(root, artifact.path, match.group("path"))
            if target is not None and not target.exists():
                findings.append(Finding(
                    "CTX001", "error", artifact.path, lineno,
                    f"imported context file does not exist: {match.group('path')}",
                    "Fix the import or remove stale context.",
                ))
    return findings


def check_backticked_paths(root: Path, artifact: Artifact) -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in enumerate(_lines(artifact.path), 1):
        for raw in BACKTICK_RE.findall(line):
            value = raw.strip()
            if " " in value or not PATHISH_RE.match(value):
                continue
            target = _resolve_reference(root, artifact.path, value)
            if target is not None and not target.exists():
                findings.append(Finding(
                    "CTX002", "warning", artifact.path, lineno,
                    f"referenced path does not exist: {value}",
                    "Instruction files age quickly; verify this path is still correct.",
                ))
    return findings


def _package_scripts(root: Path) -> set[str]:
    path = root / "package.json"
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return set()
    scripts = data.get("scripts", {})
    return set(scripts) if isinstance(scripts, dict) else set()


def _make_targets(root: Path) -> set[str]:
    path = root / "Makefile"
    if not path.exists():
        return set()
    targets: set[str] = set()
    for line in _lines(path):
        if line.startswith((" ", "\t", ".")) or ":" not in line:
            continue
        target = line.split(":", 1)[0].strip()
        if target and " " not in target and "%" not in target and "$" not in target:
            targets.add(target)
    return targets


def check_commands(root: Path, artifact: Artifact) -> list[Finding]:
    findings: list[Finding] = []
    scripts = _package_scripts(root)
    targets = _make_targets(root)
    has_package = (root / "package.json").exists()
    has_make = (root / "Makefile").exists()

    for lineno, line in enumerate(_lines(artifact.path), 1):
        for script in NPM_RUN_RE.findall(line):
            if has_package and script not in scripts:
                findings.append(Finding(
                    "CTX101", "warning", artifact.path, lineno,
                    f"package script is not defined in package.json: {script}",
                    "Update the documented command or restore the package script.",
                ))
        for target in MAKE_RE.findall(line):
            if has_make and target not in targets:
                findings.append(Finding(
                    "CTX102", "warning", artifact.path, lineno,
                    f"Make target is not defined in Makefile: {target}",
                    "Update the documented command or restore the Make target.",
                ))
    return findings


def _instruction_lines(path: Path) -> set[str]:
    out: set[str] = set()
    for raw in _lines(path):
        line = raw.strip().lower()
        if line.startswith(("- ", "* ", "+ ")):
            normalized = re.sub(r"\s+", " ", line[2:]).strip(" .")
            if len(normalized) >= 12:
                out.add(normalized)
    return out


def check_root_divergence(root: Path, artifacts: list[Artifact]) -> list[Finding]:
    candidates: list[Path] = []
    for artifact in artifacts:
        rel = artifact.path.relative_to(root).as_posix()
        if rel in {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}:
            candidates.append(artifact.path)
    findings: list[Finding] = []
    for index, left in enumerate(candidates):
        left_lines = _instruction_lines(left)
        if len(left_lines) < 4:
            continue
        for right in candidates[index + 1:]:
            right_lines = _instruction_lines(right)
            if len(right_lines) < 4:
                continue
            union = left_lines | right_lines
            similarity = len(left_lines & right_lines) / len(union) if union else 1.0
            if 0.15 <= similarity < 0.80:
                findings.append(Finding(
                    "CTX201", "warning", right, 1,
                    f"root instruction files partially overlap but diverge ({similarity:.0%} shared bullets): "
                    f"{left.name} vs {right.name}",
                    "Prefer one source of truth and import/reference it from tool-specific files.",
                ))
    return findings


def run_checks(root: Path, artifacts: list[Artifact]) -> list[Finding]:
    findings: list[Finding] = []
    for artifact in artifacts:
        findings.extend(check_imports(root, artifact))
        findings.extend(check_backticked_paths(root, artifact))
        findings.extend(check_commands(root, artifact))
    findings.extend(check_root_divergence(root, artifacts))
    deduped = {(f.code, f.path, f.line, f.message): f for f in findings}
    return sorted(
        deduped.values(),
        key=lambda f: ({"error": 0, "warning": 1, "info": 2}[f.severity], str(f.path), f.line, f.code),
    )
