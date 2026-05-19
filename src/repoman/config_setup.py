"""Bootstrap and dotted-key updates for repoman.yaml (pure helpers + small I/O)."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from repoman.config import load_yaml
from repoman.status import StatusRecord


def bundled_template_path() -> Path:
    """Path to the shipped repoman.yaml.example inside the package."""
    return Path(__file__).resolve().parent / "templates" / "repoman.yaml.example"


def parse_config_key(key: str) -> list[str | int]:
    """Parse a dotted key; numeric segments address list indices."""
    parts: list[str | int] = []
    for segment in key.split("."):
        if not segment:
            raise ValueError(f"invalid key {key!r}: empty segment")
        if segment.isdigit():
            parts.append(int(segment))
        else:
            parts.append(segment)
    if not parts:
        raise ValueError("key must not be empty")
    return parts


def coerce_config_value(raw: str) -> Any:
    """Parse a CLI value using YAML scalar rules (bool, int, lists, …)."""
    parsed = yaml.safe_load(raw)
    if parsed is None and raw.strip().lower() in ("null", "~"):
        return None
    if parsed is None:
        return raw
    return parsed


def get_nested(data: Any, parts: list[str | int]) -> Any:
    """Return nested value or raise KeyError."""
    cur: Any = data
    for part in parts:
        if isinstance(part, int):
            if not isinstance(cur, list) or part < 0 or part >= len(cur):
                raise KeyError(part)
            cur = cur[part]
        elif not isinstance(cur, dict) or part not in cur:
            raise KeyError(part)
        else:
            cur = cur[part]
    return cur


def set_nested(data: dict[str, Any], parts: list[str | int], value: Any) -> dict[str, Any]:
    """Return a deep copy of *data* with the nested key set to *value*."""
    out: dict[str, Any] = copy.deepcopy(data)
    if not parts:
        raise ValueError("parts must not be empty")
    cur: Any = out
    for i, part in enumerate(parts[:-1]):
        nxt = parts[i + 1]
        if isinstance(part, int):
            if not isinstance(cur, list):
                raise TypeError(f"expected list at index {i}")
            while len(cur) <= part:
                cur.append({} if not isinstance(nxt, int) else [])
            if cur[part] is None:
                cur[part] = [] if isinstance(nxt, int) else {}
            cur = cur[part]
        else:
            if not isinstance(cur, dict):
                raise TypeError(f"expected mapping at {part!r}")
            if part not in cur or cur[part] is None:
                cur[part] = [] if isinstance(nxt, int) else {}
            cur = cur[part]
    last = parts[-1]
    if isinstance(last, int):
        if not isinstance(cur, list):
            raise TypeError("expected list for final index")
        while len(cur) <= last:
            cur.append(None)
        cur[last] = value
    else:
        if not isinstance(cur, dict):
            raise TypeError("expected mapping for final key")
        cur[last] = value
    return out


def unset_nested(data: dict[str, Any], parts: list[str | int]) -> dict[str, Any]:
    """Return a deep copy of *data* with the nested key removed."""
    out: dict[str, Any] = copy.deepcopy(data)
    cur: Any = out
    for part in parts[:-1]:
        if isinstance(part, int):
            if not isinstance(cur, list) or part < 0 or part >= len(cur):
                raise KeyError(part)
            cur = cur[part]
        elif not isinstance(cur, dict) or part not in cur:
            raise KeyError(part)
        else:
            cur = cur[part]
    last = parts[-1]
    if isinstance(last, int):
        if not isinstance(cur, list) or last < 0 or last >= len(cur):
            raise KeyError(last)
        del cur[last]
    else:
        if not isinstance(cur, dict) or last not in cur:
            raise KeyError(last)
        del cur[last]
    return out


def plan_config_set(
    data: dict[str, Any],
    key: str,
    value: Any | None,
    *,
    unset: bool,
) -> tuple[dict[str, Any], StatusRecord]:
    """Compute updated config and a preview status line for *key*."""
    parts = parse_config_key(key)
    subject = f"config.{key}"
    try:
        if unset:
            new_data = unset_nested(data, parts)
            detail = "remove key"
        else:
            if value is None and not unset:
                raise ValueError("value required unless --unset")
            new_data = set_nested(data, parts, value)
            detail = f"set {value!r}"
    except (KeyError, TypeError, ValueError) as e:
        return data, StatusRecord("ERROR", subject, str(e))

    try:
        old = get_nested(data, parts)
        detail = f"{detail} (was {old!r})"
    except KeyError:
        detail = f"{detail} (new key)"

    return new_data, StatusRecord("WOULD UPDATE", subject, detail)


def write_config_file(path: Path, data: dict[str, Any]) -> None:
    """Persist *data* as YAML to *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def init_config_file(
    target: Path,
    *,
    force: bool,
    template: Path | None = None,
) -> list[StatusRecord]:
    """Create *target* from the bundled template."""
    subject = "config.file"
    if target.is_file() and not force:
        return [
            StatusRecord(
                "ERROR",
                subject,
                f"already exists: {target} (use --force to overwrite)",
            )
        ]
    src = template if template is not None else bundled_template_path()
    if not src.is_file():
        return [StatusRecord("ERROR", "config.template", f"not found: {src}")]
    existed = target.is_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    verb = "overwrote" if existed else "created"
    return [
        StatusRecord("OK", "config.template", str(src.name)),
        StatusRecord("UPDATED", subject, f"{verb} {target}"),
    ]


def load_config_for_edit(path: Path) -> dict[str, Any]:
    """Load YAML from disk; empty file becomes an empty mapping."""
    if not path.is_file():
        raise FileNotFoundError(path)
    return load_yaml(path)
