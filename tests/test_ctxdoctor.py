from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ctxdoctor.scanner import scan


class CtxDoctorTests(unittest.TestCase):
    def test_discovers_cross_agent_instruction_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / ".cursor/rules").mkdir(parents=True)
            (root / ".github/instructions").mkdir(parents=True)
            (root / "AGENTS.md").write_text("# agents\n", encoding="utf-8")
            (root / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
            (root / "GEMINI.md").write_text("@AGENTS.md\n", encoding="utf-8")
            (root / ".cursor/rules/react.mdc").write_text("---\nalwaysApply: false\n---\n", encoding="utf-8")
            (root / ".github/instructions/python.instructions.md").write_text("Use ruff.\n", encoding="utf-8")

            result = scan(root)
            paths = {a.path.relative_to(root).as_posix() for a in result.artifacts}
            self.assertEqual(
                paths,
                {
                    "AGENTS.md",
                    "CLAUDE.md",
                    "GEMINI.md",
                    ".cursor/rules/react.mdc",
                    ".github/instructions/python.instructions.md",
                },
            )

    def test_missing_import_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "CLAUDE.md").write_text("Read @docs/testing.md before changes.\n", encoding="utf-8")
            result = scan(root)
            errors = [f for f in result.findings if f.code == "CTX001"]
            self.assertEqual(len(errors), 1)
            self.assertIn("docs/testing.md", errors[0].message)

    def test_bare_filename_import_is_supported_and_fenced_import_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "AGENTS.md").write_text("# shared\n", encoding="utf-8")
            (root / "CLAUDE.md").write_text(
                "@AGENTS.md\n```text\n@missing.md\n```\n", encoding="utf-8"
            )
            result = scan(root)
            self.assertFalse([f for f in result.findings if f.code == "CTX001"])

    def test_stale_package_script_is_warning(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "package.json").write_text(json.dumps({"scripts": {"test": "vitest"}}), encoding="utf-8")
            (root / "AGENTS.md").write_text("Run `pnpm test:unit` before finishing.\n", encoding="utf-8")
            result = scan(root)
            findings = [f for f in result.findings if f.code == "CTX101"]
            self.assertEqual(len(findings), 1)
            self.assertIn("test:unit", findings[0].message)

    def test_stale_backticked_path_is_warning(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "AGENTS.md").write_text("Follow `docs/architecture.md`.\n", encoding="utf-8")
            result = scan(root)
            findings = [f for f in result.findings if f.code == "CTX002"]
            self.assertEqual(len(findings), 1)

    def test_partially_overlapping_root_files_flag_divergence(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "AGENTS.md").write_text(
                "\n".join([
                    "- Run tests before every change",
                    "- Use type hints for public APIs",
                    "- Keep patches narrowly scoped",
                    "- Never edit generated files by hand",
                    "- Prefer pathlib over os.path calls",
                ]), encoding="utf-8"
            )
            (root / "CLAUDE.md").write_text(
                "\n".join([
                    "- Run tests before every change",
                    "- Use type hints for public APIs",
                    "- Keep patches narrowly scoped",
                    "- Use pytest for integration tests",
                    "- Add docstrings to service classes",
                ]), encoding="utf-8"
            )
            result = scan(root)
            findings = [f for f in result.findings if f.code == "CTX201"]
            self.assertEqual(len(findings), 1)

    def test_existing_import_and_script_are_clean(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "docs").mkdir()
            (root / "docs/testing.md").write_text("# Tests\n", encoding="utf-8")
            (root / "package.json").write_text(json.dumps({"scripts": {"test": "vitest"}}), encoding="utf-8")
            (root / "CLAUDE.md").write_text("Read @docs/testing.md. Run `pnpm test`.\n", encoding="utf-8")
            result = scan(root)
            self.assertFalse([f for f in result.findings if f.severity == "error"])
            self.assertFalse([f for f in result.findings if f.code == "CTX101"])


if __name__ == "__main__":
    unittest.main()
