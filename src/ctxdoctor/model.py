from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Severity = Literal["error", "warning", "info"]


@dataclass(frozen=True)
class Artifact:
    path: Path
    kind: str
    agents: tuple[str, ...]
    scope: str
    always_on: bool = True


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    path: Path
    line: int
    message: str
    hint: str = ""


@dataclass
class ScanResult:
    root: Path
    artifacts: list[Artifact] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        out = {"error": 0, "warning": 0, "info": 0}
        for finding in self.findings:
            out[finding.severity] += 1
        return out
