"""Pure formatting for ``local status`` (no filesystem or network I/O)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from repoman.local.status_probe import RepoWorktreeFacts
from repoman.remotes.url_normalize import canonical_git_remote
from repoman.status import StatusLevel, StatusRecord


@dataclass(frozen=True)
class RepoStatusSnapshot:
    """Read-only status for one configured repository."""

    subject: str
    relative_path: str
    level: StatusLevel
    detail: str
    branch: str
    upstream: str | None
    ahead: int
    behind: int
    dirty: bool
    detached: bool
    path_missing: bool
    not_git_directory: bool
    submodule_dotfile: bool
    origin_url: str | None
    origin_drift: bool
    last_fetch_epoch: float | None


def summarize_local_repo_status(
    *,
    subject: str,
    relative_path: str,
    facts: RepoWorktreeFacts,
    expected_ssh_url: str,
    expected_https_url: str,
) -> tuple[RepoStatusSnapshot, tuple[StatusRecord, ...]]:
    """
    Build a snapshot and zero or more status lines for one repository.

    Primary line uses ``OK`` / ``WARN`` / ``ERROR`` for read-only reporting;
    an optional second line records origin URL drift (same policy as sync).
    """
    origin_drift = False
    extra: list[StatusRecord] = []

    if facts.origin_url:
        cur = canonical_git_remote(facts.origin_url)
        exp_s = canonical_git_remote(expected_ssh_url)
        exp_h = canonical_git_remote(expected_https_url)
        if cur not in {exp_s, exp_h}:
            origin_drift = True
            extra.append(
                StatusRecord(
                    "WARN",
                    subject,
                    f"origin URL differs from configured forge URL ({facts.origin_url})",
                ),
            )

    if facts.path_missing:
        snap = RepoStatusSnapshot(
            subject=subject,
            relative_path=relative_path,
            level="OK",
            detail="not cloned",
            branch="",
            upstream=None,
            ahead=0,
            behind=0,
            dirty=False,
            detached=False,
            path_missing=True,
            not_git_directory=False,
            submodule_dotfile=False,
            origin_url=None,
            origin_drift=origin_drift,
            last_fetch_epoch=None,
        )
        primary = StatusRecord("OK", subject, "not cloned")
        return snap, (primary, *extra)

    if facts.not_git_directory:
        snap = _snapshot_from_facts(
            subject,
            relative_path,
            facts,
            level="ERROR",
            detail="path exists but is not a Git work tree",
            origin_drift=origin_drift,
        )
        primary = StatusRecord("ERROR", subject, snap.detail)
        return snap, (primary, *extra)

    if facts.submodule_dotfile:
        snap = _snapshot_from_facts(
            subject,
            relative_path,
            facts,
            level="WARN",
            detail="contains submodules",
            origin_drift=origin_drift,
        )
        primary = StatusRecord("WARN", subject, snap.detail)
        return snap, (primary, *extra)

    if facts.dirty:
        snap = _snapshot_from_facts(
            subject,
            relative_path,
            facts,
            level="WARN",
            detail="working tree dirty",
            origin_drift=origin_drift,
        )
        primary = StatusRecord("WARN", subject, snap.detail)
        return snap, (primary, *extra)

    if facts.detached:
        snap = _snapshot_from_facts(
            subject,
            relative_path,
            facts,
            level="WARN",
            detail="detached HEAD",
            origin_drift=origin_drift,
        )
        primary = StatusRecord("WARN", subject, snap.detail)
        return snap, (primary, *extra)

    if facts.upstream is None:
        snap = _snapshot_from_facts(
            subject,
            relative_path,
            facts,
            level="WARN",
            detail="no upstream tracking branch",
            origin_drift=origin_drift,
        )
        primary = StatusRecord("WARN", subject, snap.detail)
        return snap, (primary, *extra)

    if facts.ahead > 0 and facts.behind > 0:
        detail = f"non-ff: {facts.ahead} ahead, {facts.behind} behind"
        snap = _snapshot_from_facts(
            subject,
            relative_path,
            facts,
            level="WARN",
            detail=detail,
            origin_drift=origin_drift,
        )
        primary = StatusRecord("WARN", subject, detail)
        return snap, (primary, *extra)

    if facts.ahead > 0 and facts.behind == 0:
        detail = f"{facts.ahead} commits ahead"
        snap = _snapshot_from_facts(
            subject,
            relative_path,
            facts,
            level="WARN",
            detail=detail,
            origin_drift=origin_drift,
        )
        primary = StatusRecord("WARN", subject, detail)
        return snap, (primary, *extra)

    if facts.behind > 0 and facts.ahead == 0:
        detail = f"{facts.behind} commits behind"
        snap = _snapshot_from_facts(
            subject,
            relative_path,
            facts,
            level="OK",
            detail=detail,
            origin_drift=origin_drift,
        )
        primary = StatusRecord("OK", subject, detail)
        return snap, (primary, *extra)

    snap = _snapshot_from_facts(
        subject,
        relative_path,
        facts,
        level="OK",
        detail="up-to-date",
        origin_drift=origin_drift,
    )
    primary = StatusRecord("OK", subject, "up-to-date")
    return snap, (primary, *extra)


def _snapshot_from_facts(
    subject: str,
    relative_path: str,
    facts: RepoWorktreeFacts,
    *,
    level: StatusLevel,
    detail: str,
    origin_drift: bool,
) -> RepoStatusSnapshot:
    return RepoStatusSnapshot(
        subject=subject,
        relative_path=relative_path,
        level=level,
        detail=detail,
        branch=facts.branch,
        upstream=facts.upstream,
        ahead=facts.ahead,
        behind=facts.behind,
        dirty=facts.dirty,
        detached=facts.detached,
        path_missing=facts.path_missing,
        not_git_directory=facts.not_git_directory,
        submodule_dotfile=facts.submodule_dotfile,
        origin_url=facts.origin_url,
        origin_drift=origin_drift,
        last_fetch_epoch=facts.last_fetch_epoch,
    )


def snapshot_to_json_dict(snap: RepoStatusSnapshot) -> dict[str, Any]:
    """Serialize one repository snapshot for ``--json`` output."""
    return {
        "subject": snap.subject,
        "path": snap.relative_path,
        "level": snap.level,
        "detail": snap.detail,
        "branch": snap.branch,
        "upstream": snap.upstream,
        "ahead": snap.ahead,
        "behind": snap.behind,
        "dirty": snap.dirty,
        "detached": snap.detached,
        "path_missing": snap.path_missing,
        "not_git_directory": snap.not_git_directory,
        "submodule_dotfile": snap.submodule_dotfile,
        "origin_url": snap.origin_url,
        "origin_drift": snap.origin_drift,
        "last_fetch_epoch": snap.last_fetch_epoch,
    }


def status_payload_to_json_dict(
    *,
    schema_version: int,
    workspace_root: str,
    prelude: list[StatusRecord],
    repositories: list[RepoStatusSnapshot],
) -> dict[str, Any]:
    """Build the top-level JSON document for ``local status --json``."""
    return {
        "schema_version": schema_version,
        "workspace_root": workspace_root,
        "prelude": [{"level": r.level, "subject": r.subject, "detail": r.detail} for r in prelude],
        "repositories": [snapshot_to_json_dict(s) for s in repositories],
    }
