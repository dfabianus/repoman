"""Forge client protocol (minimal MVP)."""

from __future__ import annotations

from typing import Protocol


class ForgeClient(Protocol):
    def probe_api(self) -> tuple[bool, str]:
        """Return (ok, detail)."""
