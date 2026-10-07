"""Normalize Git remote URLs for comparison (pure)."""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


def canonical_git_remote(url: str) -> str:
    """
    Compare remotes without leaking credentials and ignoring trailing ``.git``.

    Not a full Git URL parser; tuned for https/ssh schemes used by GitLab/GitHub.
    """
    raw = url.strip()
    if raw.endswith(".git"):
        raw = raw[:-4]
    parts = urlsplit(raw)
    scheme = (parts.scheme or "").lower()
    netloc = parts.netloc.lower()
    if "@" in netloc:
        _, hostpart = netloc.rsplit("@", 1)
        netloc = hostpart
    path = parts.path.rstrip("/").lower()
    if not path.startswith("/") and scheme in {"ssh", "git"}:
        path = "/" + path
    rebuilt = urlunsplit((scheme, netloc, path, "", ""))
    return rebuilt.rstrip("/")


def redact_url_credentials(url: str) -> str:
    """
    Replace credentials in an ``http(s)://`` URL with ``***`` for display.

    ``https://user:secret@host/p`` becomes ``https://user:***@host/p``; a bare
    ``https://secret@host/p`` becomes ``https://***@host/p``. Other schemes and
    scp-style SSH URLs are returned unchanged.
    """
    parts = urlsplit(url)
    if parts.scheme.lower() not in {"http", "https"} or "@" not in parts.netloc:
        return url
    userinfo, hostpart = parts.netloc.rsplit("@", 1)
    if ":" in userinfo:
        user = userinfo.split(":", 1)[0]
        safe = f"{user}:***"
    else:
        safe = "***"
    return urlunsplit((parts.scheme, f"{safe}@{hostpart}", parts.path, parts.query, parts.fragment))
