"""Choose the effective clone URL for ``git clone``."""

from __future__ import annotations

from typing import Literal
from urllib.parse import urlsplit, urlunsplit

ForgeKind = Literal["gitlab", "github"]


def authenticated_clone_url(
    *,
    forge_kind: ForgeKind,
    clone_protocol: str,
    ssh_url: str,
    https_url: str,
    token: str | None,
) -> str:
    """
    Resolve the URL passed to ``git clone`` respecting ``clone_protocol``.

    HTTPS clones embed tokens when present (never log this return value verbatim).
    """
    proto = clone_protocol.strip().lower()
    if proto == "ssh":
        return ssh_url
    return inject_https_credentials(forge_kind=forge_kind, https_url=https_url, token=token)


def inject_https_credentials(*, forge_kind: ForgeKind, https_url: str, token: str | None) -> str:
    """Return an HTTPS URL, embedding credentials when a token exists."""
    if not token:
        return https_url
    parts = urlsplit(https_url)
    host = parts.hostname
    if not host:
        return https_url
    port_suffix = ""
    if parts.port:
        port_suffix = f":{parts.port}"
    if forge_kind == "gitlab":
        netloc = f"oauth2:{token}@{host}{port_suffix}"
    else:
        netloc = f"x-access-token:{token}@{host}{port_suffix}"
    return urlunsplit((parts.scheme or "https", netloc, parts.path, parts.query, parts.fragment))
