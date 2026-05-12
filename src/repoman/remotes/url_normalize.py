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
