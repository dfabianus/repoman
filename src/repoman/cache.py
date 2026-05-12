"""JSON discovery cache helpers (thin I/O wrappers)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_DISCOVERY_SUBDIR = "discovery"


def discovery_cache_filename(remote_name: str, namespace_slug: str) -> str:
    """Stable hashed filename fragment for a namespace listing."""
    key = f"{remote_name}:{namespace_slug}".encode()
    digest = hashlib.sha256(key).hexdigest()[:16]
    return f"{remote_name}_{digest}.json"


def discovery_cache_path(cache_root: Path, remote_name: str, namespace_slug: str) -> Path:
    return (
        Path(cache_root).expanduser()
        / _DISCOVERY_SUBDIR
        / discovery_cache_filename(remote_name, namespace_slug)
    )


def read_discovery_cache(path: Path) -> dict[str, Any] | None:
    """Return parsed payload or None when missing or corrupt."""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def write_discovery_cache(
    path: Path, fetched_at_epoch: float, *, projects: list[dict[str, Any]]
) -> None:
    """Write discovery cache payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body_dict: dict[str, Any] = {
        "fetched_at_epoch": fetched_at_epoch,
        "projects": projects,
    }
    path.write_text(json.dumps(body_dict, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def cache_payload_projects(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract project dict list from cached payload."""
    raw = data.get("projects")
    if not isinstance(raw, list):
        return []
    return [x for x in raw if isinstance(x, dict)]
