"""Thin wrappers around subprocess ``git`` calls."""

from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess, run

GitOutcome = tuple[int, str, str]


def run_git(
    repo: Path | None,
    /,
    *git_args: str,
    timeout_sec: float = 300.0,
) -> GitOutcome:
    """
    Invoke ``git`` with arguments; optional ``repo`` passes ``--git-dir`` / cwd.

    When ``repo`` is set, passes ``-C`` so commands run inside that directory.
    """
    cmd = ["git"]
    if repo is not None:
        cmd += ["-C", str(repo)]
    cmd.extend(git_args)
    proc: CompletedProcess[str] = run(
        cmd,
        cwd=None,
        check=False,
        text=True,
        capture_output=True,
        timeout=timeout_sec,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git_clone(
    repo_url: str,
    dest: Path,
    *,
    timeout_sec: float = 600.0,
) -> GitOutcome:
    """Clone repository into ``dest`` (expects parent directories to exist)."""
    dest_parent = dest.parent
    dest_parent.mkdir(parents=True, exist_ok=True)
    proc: CompletedProcess[str] = run(
        ["git", "-C", str(dest_parent), "clone", repo_url, str(dest.name)],
        check=False,
        text=True,
        capture_output=True,
        timeout=timeout_sec,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git_fetch(
    repo: Path,
    *,
    prune: bool = True,
    timeout_sec: float = 300.0,
) -> GitOutcome:
    """Run ``fetch`` (optional ``--prune``)."""
    args = ["fetch", "--tags"]
    if prune:
        args.append("--prune")
    return run_git(repo, *args, timeout_sec=timeout_sec)


def git_merge_ff_only(repo: Path, *, timeout_sec: float = 120.0) -> GitOutcome:
    """Attempt fast-forward merge to upstream tracked branch."""
    return run_git(repo, "merge", "--ff-only", "@{upstream}", timeout_sec=timeout_sec)
