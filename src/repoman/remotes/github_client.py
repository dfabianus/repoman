"""Minimal GitHub API wrapper for doctor probes."""

from __future__ import annotations

from github import Auth, Github, GithubException


class GithubRemoteClient:
    def __init__(self, *, base_url: str | None, token: str) -> None:
        # GitHub.com: omit base_url; Enterprise: pass API root (e.g. https://api.github.com)
        kwargs: dict = {"auth": Auth.Token(token)}
        if base_url and base_url.rstrip("/") != "https://api.github.com":
            kwargs["base_url"] = base_url.rstrip("/")
        self._g = Github(**kwargs)

    def probe_api(self) -> tuple[bool, str]:
        try:
            user = self._g.get_user()
            login = user.login
            return True, f"GET /user ok (@{login})"
        except GithubException as e:
            data = getattr(e, "data", None)
            msg = data.get("message", str(e)) if isinstance(data, dict) else str(e)
            return False, f"{getattr(e, 'status', '?')}: {msg}"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"
