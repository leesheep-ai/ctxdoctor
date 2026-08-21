from __future__ import annotations

from pathlib import Path

from .model import Artifact

SKIP_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "dist", "build",
    ".next", ".cache", "vendor", "target", "__pycache__",
}


def _scope_for(path: Path, root: Path) -> str:
    parent = path.parent
    try:
        rel = parent.relative_to(root)
    except ValueError:
        return "."
    return "." if str(rel) == "." else rel.as_posix() + "/**"


def _classify(path: Path, root: Path) -> Artifact | None:
    rel = path.relative_to(root).as_posix()
    name = path.name
    scope = _scope_for(path, root)

    if name in {"AGENTS.md", "AGENTS.override.md"}:
        return Artifact(path, "agents-md", ("codex", "cursor", "copilot"), scope, True)
    if name == "CLAUDE.md":
        return Artifact(path, "claude-memory", ("claude", "copilot"), scope, True)
    if name == "GEMINI.md":
        return Artifact(path, "gemini-context", ("gemini", "copilot"), scope, True)
    if rel == ".cursorrules":
        return Artifact(path, "cursor-legacy-rule", ("cursor",), ".", True)
    if rel.startswith(".cursor/rules/") and name.endswith(".mdc"):
        return Artifact(path, "cursor-rule", ("cursor",), scope, False)
    if rel.startswith(".claude/rules/") and name.endswith(".md"):
        return Artifact(path, "claude-rule", ("claude",), scope, False)
    if rel == ".github/copilot-instructions.md":
        return Artifact(path, "copilot-instructions", ("copilot",), ".", True)
    if rel.startswith(".github/instructions/") and name.endswith(".instructions.md"):
        return Artifact(path, "copilot-path-instructions", ("copilot",), scope, False)
    if name == "SKILL.md" and any(
        marker in rel
        for marker in ("/.agents/skills/", "/.claude/skills/", "/.cursor/skills/")
    ):
        return Artifact(path, "skill", ("codex", "claude", "cursor", "gemini"), scope, False)
    if name == "SKILL.md" and rel.startswith((".agents/skills/", ".claude/skills/", ".cursor/skills/")):
        return Artifact(path, "skill", ("codex", "claude", "cursor", "gemini"), scope, False)
    return None


def discover(root: Path) -> list[Artifact]:
    root = root.resolve()
    artifacts: list[Artifact] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in parts[:-1]):
            continue
        artifact = _classify(path, root)
        if artifact:
            artifacts.append(artifact)
    return sorted(artifacts, key=lambda item: item.path.relative_to(root).as_posix())
