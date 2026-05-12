"""Status vocabulary and line formatting (pure)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

StatusLevel = Literal["OK", "WOULD UPDATE", "UPDATED", "SKIP", "WARN", "ERROR"]


@dataclass(frozen=True)
class StatusRecord:
    level: StatusLevel
    subject: str
    detail: str


def format_line(record: StatusRecord) -> str:
    """Format one machine-friendly status line (fixed-width level column)."""
    return f"{record.level:<13} {record.subject:<28} {record.detail}"


def exit_code_for_records(records: list[StatusRecord]) -> int:
    """0 unless any ERROR."""
    if any(r.level == "ERROR" for r in records):
        return 1
    return 0
