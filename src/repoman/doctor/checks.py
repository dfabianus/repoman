"""Doctor checks (filesystem / config helpers)."""

from __future__ import annotations

from pathlib import Path

from repoman.status import StatusRecord


def check_config_file_exists(path: Path) -> StatusRecord | None:
    if not path.is_file():
        return StatusRecord("ERROR", "config.file", f"not found: {path}")
    return StatusRecord("OK", "config.file", str(path.resolve()))
