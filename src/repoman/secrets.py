"""Token resolution from CLI, env, a forge CLI command, and credentials.toml."""

from __future__ import annotations

import os
import stat
import subprocess
import tomllib
from pathlib import Path

COMMAND_TIMEOUT_SECONDS = 15


class TokenCommandError(RuntimeError):
    """``token_command`` could not be run or returned no token."""


def _run_token_command(argv: list[str]) -> str:
    """Run ``argv`` without a shell; the token is its trimmed stdout."""
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise TokenCommandError(f"token_command {argv[0]!r}: {e}") from e
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip().splitlines()
        hint = detail[-1] if detail else f"exit {proc.returncode}"
        raise TokenCommandError(f"token_command {argv[0]!r} failed: {hint}")
    token = proc.stdout.strip()
    if not token:
        raise TokenCommandError(f"token_command {argv[0]!r} printed no token")
    return token


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

    Precedence: CLI > env (token_env) > token_command > credentials.toml
    (token_credentials). ``token_command`` is an argv list run without a shell,
    for example ``["gh", "auth", "token"]``; a failing command raises
    ``TokenCommandError`` instead of silently falling through, so a broken
    forge login is reported rather than masked by a stale credentials file.
    """
    if cli_token is not None and cli_token.strip():
        return cli_token.strip(), "cli"

    token_env = remote_cfg.get("token_env")
    if isinstance(token_env, str) and token_env.strip():
        val = os.environ.get(token_env.strip())
        if val:
            return val.strip(), f"env:{token_env.strip()}"

    token_command = remote_cfg.get("token_command")
    if isinstance(token_command, list) and token_command:
        argv = [str(part) for part in token_command]
        return _run_token_command(argv), f"command:{argv[0]}"

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
