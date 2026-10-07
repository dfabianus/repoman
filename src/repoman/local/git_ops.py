"""Thin wrappers around subprocess ``git`` calls."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from subprocess import CompletedProcess, run

GitOutcome = tuple[int, str, str]


def _env_with(extra: Mapping[str, str] | None) -> dict[str, str] | None:
    """Process environment plus ``extra`` (``None`` inherits unchanged)."""
    if not extra:
        return None
    env = dict(os.environ)
    env.update(extra)
    return env


def run_git(
    repo: Path | None,
    /,
    *git_args: str,
    timeout_sec: float = 300.0,
    env: Mapping[str, str] | None = None,
) -> GitOutcome:
    """
    Invoke ``git`` with arguments; optional ``repo`` passes ``--git-dir`` / cwd.

    When ``repo`` is set, passes ``-C`` so commands run inside that directory.
    ``env`` adds variables on top of the process environment (e.g. auth config).
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
        env=_env_with(env),
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git_clone(
    repo_url: str,
    dest: Path,
    *,
    timeout_sec: float = 600.0,
    env: Mapping[str, str] | None = None,
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
        env=_env_with(env),
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git_fetch(
    repo: Path,
    *,
    prune: bool = True,
    timeout_sec: float = 300.0,
    env: Mapping[str, str] | None = None,
) -> GitOutcome:
    """Run ``fetch`` (optional ``--prune``)."""
    args = ["fetch", "--tags"]
    if prune:
        args.append("--prune")
    return run_git(repo, *args, timeout_sec=timeout_sec, env=env)


def git_set_origin_url(repo: Path, url: str, *, timeout_sec: float = 60.0) -> GitOutcome:
    """Point ``origin`` at ``url``."""
    return run_git(repo, "remote", "set-url", "origin", url, timeout_sec=timeout_sec)


def git_merge_ff_only(repo: Path, *, timeout_sec: float = 120.0) -> GitOutcome:
    """Attempt fast-forward merge to upstream tracked branch."""
    return run_git(repo, "merge", "--ff-only", "@{upstream}", timeout_sec=timeout_sec)
