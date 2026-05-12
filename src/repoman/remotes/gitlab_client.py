"""Minimal GitLab API wrapper for doctor probes."""

from __future__ import annotations

import gitlab
from gitlab.exceptions import GitlabAuthenticationError, GitlabError

from repoman.remotes.catalog import ListedProject


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

    def list_group_projects(
        self,
        group_path: str,
        *,
        include_subgroups: bool,
    ) -> list[ListedProject]:
        """
        List projects under the given group identifier (supports nested namespaces).

        ``include_subgroups`` walks subgroup projects recursively.
        """
        group = self._gl.groups.get(group_path)
        out: list[ListedProject] = []
        for p in group.projects.list(iterator=True, all=True, include_subgroups=include_subgroups):
            attrs_raw = getattr(p, "attributes", {}) or {}
            attrs = attrs_raw if isinstance(attrs_raw, dict) else {}
            raw_vis = getattr(p, "visibility", None)
            if isinstance(raw_vis, str) and raw_vis.strip():
                vis_out = raw_vis.strip().lower()
            elif isinstance(attrs.get("visibility"), str) and attrs["visibility"].strip():
                vis_out = attrs["visibility"].strip().lower()
            else:
                vis_out = "unknown"
            pn = getattr(p, "path_with_namespace", None) or attrs.get(
                "path_with_namespace",
            )
            if not isinstance(pn, str) or not pn.strip():
                continue
            archived = bool(getattr(p, "archived", False) or attrs.get("archived"))
            ssh_u = getattr(p, "ssh_url_to_repo", None) or attrs.get("ssh_url_to_repo") or ""
            http_u = getattr(p, "http_url_to_repo", None) or attrs.get("http_url_to_repo") or ""
            if not isinstance(ssh_u, str):
                ssh_u = ""
            if not isinstance(http_u, str):
                http_u = ""
            branch = getattr(p, "default_branch", None)
            if branch is None and isinstance(attrs, dict):
                db = attrs.get("default_branch")
                branch = db if isinstance(db, str) else None
            out.append(
                ListedProject(
                    path_with_namespace=pn.strip(),
                    ssh_url_to_repo=ssh_u.strip(),
                    http_url_to_repo=http_u.strip(),
                    archived=archived,
                    visibility=vis_out,
                    default_branch=branch,
                )
            )
        return out
