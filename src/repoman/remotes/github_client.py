"""Minimal GitHub API wrapper for doctor probes."""

from __future__ import annotations

from github import Auth, Github, GithubException, UnknownObjectException

from repoman.remotes.catalog import ListedProject


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

    def list_namespace_repositories(self, namespace: str) -> list[ListedProject]:
        """
        List repositories for a GitHub organization or user slug.

        Fetches repositories for an organization when it exists; otherwise treats
        ``namespace`` as a user login and lists owner-visible repositories.

        Caller applies include/exclude/visibility filtering.
        """
        try:
            org = self._g.get_organization(namespace)
            repo_iter = org.get_repos(type="all")
        except UnknownObjectException:
            user = self._g.get_user(namespace)
            repo_iter = user.get_repos(type="owner")
        except GithubException:
            raise
        out: list[ListedProject] = []
        for r in repo_iter:
            archived = getattr(r, "archived", False)
            ssh_u = getattr(r, "ssh_url", "") or ""
            http_u = getattr(r, "clone_url", "") or ""
            if not isinstance(ssh_u, str):
                ssh_u = ""
            if not isinstance(http_u, str):
                http_u = ""
            full = getattr(r, "full_name", None)
            if not isinstance(full, str) or not full.strip():
                continue
            visibility_attr = getattr(r, "visibility", None)
            if visibility_attr is None:
                visibility_sl = "private" if getattr(r, "private", False) else "public"
            elif isinstance(visibility_attr, str):
                visibility_sl = visibility_attr.strip().lower()
            else:
                visibility_sl = str(visibility_attr).lower()
            db = getattr(r, "default_branch", None)
            default_branch = db if isinstance(db, str) else None
            out.append(
                ListedProject(
                    path_with_namespace=full.strip(),
                    ssh_url_to_repo=ssh_u.strip(),
                    http_url_to_repo=http_u.strip(),
                    archived=bool(archived),
                    visibility=visibility_sl,
                    default_branch=default_branch,
                )
            )
        return out
