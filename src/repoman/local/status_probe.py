"""Parse local Git repository state via ``git`` (I/O-bound helper)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from repoman.local.git_ops import run_git


@dataclass(frozen=True)
class RepoWorktreeFacts:
    """Observed facts about an on-disk path (may be missing or non-Git)."""

    path_missing: bool
    not_git_directory: bool
    has_git: bool
    submodule_dotfile: bool
    detached: bool
    dirty: bool
    branch: str
    upstream: str | None
    ahead: int
    behind: int
    origin_url: str | None


def probe_worktree(repo_path: Path) -> RepoWorktreeFacts:
    """
    Inspect ``repo_path`` with ``git`` commands.

    When the path is missing, everything except ``path_missing`` is falsey.
    When the path exists but is not a work tree, ``not_git_directory`` is set.
    """
    if not repo_path.exists():
        return RepoWorktreeFacts(
            path_missing=True,
            not_git_directory=False,
            has_git=False,
            submodule_dotfile=False,
            detached=False,
            dirty=False,
            branch="",
            upstream=None,
            ahead=0,
            behind=0,
            origin_url=None,
        )

    code, _, _ = run_git(repo_path, "rev-parse", "--is-inside-work-tree")
    if code != 0:
        return RepoWorktreeFacts(
            path_missing=False,
            not_git_directory=True,
            has_git=False,
            submodule_dotfile=False,
            detached=False,
            dirty=False,
            branch="",
            upstream=None,
            ahead=0,
            behind=0,
            origin_url=None,
        )

    submodule_dotfile = (repo_path / ".gitmodules").is_file()

    sym_code, sym_out, _ = run_git(repo_path, "symbolic-ref", "-q", "HEAD")
    detached = sym_code != 0
    _, branch_out, _ = run_git(repo_path, "rev-parse", "--abbrev-ref", "HEAD")
    branch = branch_out.strip() or "HEAD"

    up_code, up_out, _ = run_git(
        repo_path,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
    )
    upstream = up_out.strip() if up_code == 0 and up_out.strip() else None

    dirt_code, dirt_out, _ = run_git(repo_path, "status", "--porcelain")
    dirty = dirt_code == 0 and bool(dirt_out.strip())

    origin_code, origin_out, _ = run_git(repo_path, "remote", "get-url", "origin")
    origin_url = origin_out.strip() if origin_code == 0 and origin_out.strip() else None

    ahead, behind = 0, 0
    if upstream and not detached:
        lr_code, lr_out, _ = run_git(
            repo_path,
            "rev-list",
            "--left-right",
            "--count",
            f"{upstream}...HEAD",
        )
        if lr_code == 0:
            parts = lr_out.strip().split()
            if len(parts) >= 2:
                try:
                    behind = max(0, int(parts[0]))
                    ahead = max(0, int(parts[1]))
                except ValueError:
                    ahead, behind = 0, 0

    return RepoWorktreeFacts(
        path_missing=False,
        not_git_directory=False,
        has_git=True,
        submodule_dotfile=submodule_dotfile,
        detached=detached,
        dirty=dirty,
        branch=branch,
        upstream=upstream,
        ahead=ahead,
        behind=behind,
        origin_url=origin_url,
    )
