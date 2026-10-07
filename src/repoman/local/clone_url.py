"""Clone URLs and per-command HTTPS authentication for ``git`` (pure)."""

from __future__ import annotations

import base64
from collections.abc import Mapping
from typing import Literal
from urllib.parse import urlsplit

from repoman.remotes.url_normalize import canonical_git_remote

ForgeKind = Literal["gitlab", "github"]

# Basic-auth user name each forge expects with a token as the password. These are also
# the user names that repoman <= 0.5 embedded in HTTPS origin URLs.
FORGE_TOKEN_USER: dict[str, str] = {"github": "x-access-token", "gitlab": "oauth2"}


def clone_url(*, clone_protocol: str, ssh_url: str, https_url: str) -> str:
    """Return the URL passed to ``git clone``; never contains credentials."""
    if clone_protocol.strip().lower() == "ssh":
        return ssh_url
    return https_url


def http_auth_scope(https_url: str) -> str | None:
    """Return the ``http.<url>.*`` scope (``https://host[:port]/``) for an HTTPS URL."""
    parts = urlsplit(https_url)
    scheme = parts.scheme.lower()
    host = parts.hostname
    if scheme not in {"http", "https"} or not host:
        return None
    port = f":{parts.port}" if parts.port else ""
    return f"{scheme}://{host}{port}/"


def basic_auth_header(forge_kind: ForgeKind, token: str) -> str:
    """Return the ``Authorization`` header line for ``token`` on ``forge_kind``."""
    user = FORGE_TOKEN_USER[forge_kind]
    cred = base64.b64encode(f"{user}:{token}".encode()).decode("ascii")
    return f"Authorization: Basic {cred}"


def git_auth_env(
    *,
    forge_kind: ForgeKind,
    clone_protocol: str,
    https_url: str,
    token: str | None,
    base_env: Mapping[str, str],
) -> dict[str, str]:
    """
    Return environment overrides that authenticate one ``git`` command over HTTPS.

    Uses ``GIT_CONFIG_COUNT``/``GIT_CONFIG_KEY_<n>``/``GIT_CONFIG_VALUE_<n>`` (git >= 2.31)
    to set ``http.<scope>.extraheader``, so the token reaches neither argv nor
    ``.git/config``. Entries already declared in ``base_env`` are kept; ours is appended.
    Returns ``{}`` for SSH or when there is no token.
    """
    if clone_protocol.strip().lower() == "ssh" or not token:
        return {}
    scope = http_auth_scope(https_url)
    if scope is None:
        return {}
    try:
        idx = max(0, int(base_env.get("GIT_CONFIG_COUNT", "0") or "0"))
    except ValueError:
        idx = 0
    return {
        "GIT_CONFIG_COUNT": str(idx + 1),
        f"GIT_CONFIG_KEY_{idx}": f"http.{scope}.extraheader",
        f"GIT_CONFIG_VALUE_{idx}": basic_auth_header(forge_kind, token),
    }


def has_repoman_credentials(
    origin_url: str, *, forge_kind: ForgeKind, expected_https_url: str
) -> bool:
    """
    True when ``origin_url`` is the HTTPS URL older repoman versions produced.

    That is: the configured HTTPS URL with ``<forge user>:<token>@`` in front of the host.
    Works on raw and redacted URLs. Any other credentialed URL is left alone.
    """
    parts = urlsplit(origin_url.strip())
    if parts.scheme.lower() not in {"http", "https"} or "@" not in parts.netloc:
        return False
    userinfo = parts.netloc.rsplit("@", 1)[0]
    user, sep, secret = userinfo.partition(":")
    if not sep or not secret or user != FORGE_TOKEN_USER[forge_kind]:
        return False
    return canonical_git_remote(origin_url) == canonical_git_remote(expected_https_url)


def redact_secret(text: str, secret: str | None) -> str:
    """Replace every occurrence of ``secret`` in ``text`` with ``***``."""
    if not secret:
        return text
    return text.replace(secret, "***")
