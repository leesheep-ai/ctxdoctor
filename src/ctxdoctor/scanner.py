from __future__ import annotations

from pathlib import Path

from .checks import run_checks
from .discovery import discover
from .model import ScanResult


def scan(root: Path) -> ScanResult:
    root = root.resolve()
    artifacts = discover(root)
    return ScanResult(root=root, artifacts=artifacts, findings=run_checks(root, artifacts))
