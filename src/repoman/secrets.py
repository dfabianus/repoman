"""Token resolution from env, CLI, and credentials.toml."""

from __future__ import annotations

import os
import stat
import tomllib
from pathlib import Path


def _credentials_must_be_secure(path: Path) -> tuple[bool, str]:
    if os.name == "nt":
        return True, "skipped on Windows"
    mode = path.stat().st_mode
    if stat.S_IMODE(mode) != 0o600:
        return False, f"permissions must be 0600 (got {oct(stat.S_IMODE(mode))})"
    return True, "0600"


def resolve_token(
    remote_name: str,
    remote_cfg: dict,
    *,
    cli_token: str | None,
    credentials_file: Path,
) -> tuple[str | None, str]:
    """
    Resolve token for one remote. Returns (token_or_none, source_label).

    Precedence: CLI > env (token_env) > credentials.toml (token_credentials).
    """
    if cli_token is not None and cli_token.strip():
        return cli_token.strip(), "cli"

    token_env = remote_cfg.get("token_env")
    if isinstance(token_env, str) and token_env.strip():
        val = os.environ.get(token_env.strip())
        if val:
            return val.strip(), f"env:{token_env.strip()}"

    cred_section = remote_cfg.get("token_credentials")
    if isinstance(cred_section, str) and cred_section.strip() and credentials_file.is_file():
        ok, hint = _credentials_must_be_secure(credentials_file)
        if not ok:
            raise PermissionError(f"credentials file {credentials_file}: {hint}")
        data = tomllib.loads(credentials_file.read_text(encoding="utf-8"))
        section = data.get(cred_section.strip())
        if isinstance(section, dict):
            token = section.get("token")
            if isinstance(token, str) and token.strip():
                return token.strip(), f"credentials.toml:{cred_section.strip()}"

    return None, "unresolved"
