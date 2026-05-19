"""Default paths and layout templating (pure)."""

from __future__ import annotations

import os
import re
from pathlib import Path

LAYOUT_PLACEHOLDERS = frozenset({"remote", "namespace", "subgroup", "repo"})
_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


def default_config_dir() -> Path:
    """Config directory: REPOMAN_HOME if set, else OS default per design doc."""
    repoman_home = os.environ.get("REPOMAN_HOME")
    if repoman_home:
        return Path(repoman_home).expanduser()
    if os.name == "nt":
        profile = os.environ.get("USERPROFILE", "")
        return Path(profile).expanduser() / ".repoman"
    return Path("~/.config/repoman").expanduser()


def default_config_path() -> Path:
    return default_config_dir() / "repoman.yaml"


def credentials_path_for_config(config_file: Path) -> Path:
    """credentials.toml lives next to repoman.yaml."""
    return config_file.parent / "credentials.toml"


def extract_layout_placeholders(layout: str) -> set[str]:
    return set(_PLACEHOLDER_RE.findall(layout))


def render_layout(
    layout: str,
    *,
    remote: str,
    namespace: str,
    subgroup: str,
    repo: str,
) -> str:
    """Fill layout template; missing placeholders raise KeyError."""
    return layout.format(remote=remote, namespace=namespace, subgroup=subgroup, repo=repo)
