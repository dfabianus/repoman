"""Minimal GitLab API wrapper for doctor probes."""

from __future__ import annotations

import gitlab
from gitlab.exceptions import GitlabAuthenticationError, GitlabError


class GitlabRemoteClient:
    def __init__(self, *, base_url: str, token: str, ssl_verify: bool = True) -> None:
        url = base_url.rstrip("/")
        self._gl = gitlab.Gitlab(url=url, private_token=token, ssl_verify=ssl_verify)

    def probe_api(self) -> tuple[bool, str]:
        try:
            info = self._gl.version()
            ver = info.get("version", info) if isinstance(info, dict) else info
            return True, f"GET /version ok ({ver!r})"
        except GitlabAuthenticationError as e:
            return False, f"authentication failed: {e.error_message}"
        except GitlabError as e:
            return False, str(e)
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"
