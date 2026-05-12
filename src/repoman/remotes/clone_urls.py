"""Derive HTTPS/SSH clone targets when forge listings do not provide URLs."""

from __future__ import annotations

from typing import Literal
from urllib.parse import urlparse


def synthesized_clone_urls(
    kind: Literal["gitlab", "github"], *, base_api_url: str, forge_path: str
) -> tuple[str, str]:
    """
    Build ``(ssh_clone_url, https_clone_url)`` from API base URLs.

    Paths use ``/`` between namespace segments and end with ``.git`` per Git
    conventions.
    """
    fp = forge_path.strip().strip("/")
    if not fp:
        raise ValueError("forge_path empty")
    if kind == "github":
        pu = urlparse(base_api_url.rstrip("/"))
        host = pu.hostname or "github.com"
        if host == "api.github.com":
            host = "github.com"
        https_u = f"https://{host}/{fp}.git"
        ssh_u = f"git@{host}:{fp}.git"
        return ssh_u, https_u

    pu = urlparse(base_api_url.rstrip("/"))
    scheme = pu.scheme or "https"
    host = pu.hostname
    if not host:
        raise ValueError(f"cannot derive host from {base_api_url!r}")
    https_u = f"{scheme}://{host}/{fp}.git"
    ssh_u = f"git@{host}:{fp}.git"
    return ssh_u, https_u
