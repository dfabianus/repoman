"""Tests for local sync planning (pure)."""

from __future__ import annotations

from repoman.local.planner import plan_local_sync
from repoman.local.status_probe import RepoWorktreeFacts


def _facts(
    *,
    path_missing: bool = False,
    not_git_directory: bool = False,
    has_git: bool = True,
    submodule_dotfile: bool = False,
    detached: bool = False,
    dirty: bool = False,
    branch: str = "main",
    upstream: str | None = "origin/main",
    ahead: int = 0,
    behind: int = 0,
    origin_url: str | None = "git@github.com:o/r.git",
    last_fetch_epoch: float | None = None,
) -> RepoWorktreeFacts:
    return RepoWorktreeFacts(
        path_missing=path_missing,
        not_git_directory=not_git_directory,
        has_git=has_git,
        submodule_dotfile=submodule_dotfile,
        detached=detached,
        dirty=dirty,
        branch=branch,
        upstream=upstream,
        ahead=ahead,
        behind=behind,
        origin_url=origin_url,
        last_fetch_epoch=last_fetch_epoch,
    )


def test_behind_ff_triggers_fetch() -> None:
    plan = plan_local_sync(
        subject="o/r",
        facts=_facts(behind=3, ahead=0),
        expected_ssh_url="git@github.com:o/r.git",
        expected_https_url="https://github.com/o/r.git",
        strategy="ff-only",
    )
    assert not plan.records
    assert plan.should_fetch
    assert plan.should_merge_ff


def test_dirty_skips_without_fetch() -> None:
    plan = plan_local_sync(
        subject="o/r",
        facts=_facts(dirty=True),
        expected_ssh_url="git@github.com:o/r.git",
        expected_https_url="https://github.com/o/r.git",
        strategy="ff-only",
    )
    assert any(r.level == "SKIP" for r in plan.records)
    assert not plan.should_fetch


def test_noop_up_to_date() -> None:
    plan = plan_local_sync(
        subject="o/r",
        facts=_facts(),
        expected_ssh_url="git@github.com:o/r.git",
        expected_https_url="https://github.com/o/r.git",
        strategy="ff-only",
    )
    assert any(r.level == "OK" for r in plan.records)
    assert not plan.should_fetch


def test_submodule_skips_with_warn_detail() -> None:
    plan = plan_local_sync(
        subject="o/r",
        facts=_facts(submodule_dotfile=True),
        expected_ssh_url="git@github.com:o/r.git",
        expected_https_url="https://github.com/o/r.git",
        strategy="ff-only",
    )
    joined = " ".join(r.detail for r in plan.records)
    assert "submodule" in joined.lower()


def test_non_ff_skips_when_divergent() -> None:
    plan = plan_local_sync(
        subject="o/r",
        facts=_facts(ahead=1, behind=3),
        expected_ssh_url="git@github.com:o/r.git",
        expected_https_url="https://github.com/o/r.git",
        strategy="ff-only",
    )
    assert any("non-ff" in r.detail for r in plan.records)
