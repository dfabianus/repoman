"""Pure planning for local sync (no filesystem or subprocess I/O)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from repoman.local.status_probe import RepoWorktreeFacts
from repoman.remotes.url_normalize import canonical_git_remote
from repoman.status import StatusRecord

SyncStrategy = Literal["ff-only", "fetch-only"]


@dataclass(frozen=True)
class LocalSyncPlan:
    """What to do for one repository before any mutating ``git`` invocation."""

    records: tuple[StatusRecord, ...]
    should_clone: bool
    should_fetch: bool
    should_merge_ff: bool


def plan_local_sync(
    *,
    subject: str,
    facts: RepoWorktreeFacts,
    expected_ssh_url: str,
    expected_https_url: str,
    strategy: SyncStrategy,
) -> LocalSyncPlan:
    """
    Decide whether to clone, fetch, fast-forward, or skip for a single subject.

    Implements the conflict policy from ``docs/design/repoman.md`` §8.2: never
    destructive merges; dirty trees and non-fast-forward states are skipped.
    """
    rows: list[StatusRecord] = []

    if facts.path_missing:
        return LocalSyncPlan(
            records=tuple(rows),
            should_clone=True,
            should_fetch=False,
            should_merge_ff=False,
        )

    if facts.not_git_directory:
        rows.append(
            StatusRecord(
                "ERROR",
                subject,
                "path exists but is not a Git work tree",
            ),
        )
        return LocalSyncPlan(
            records=tuple(rows),
            should_clone=False,
            should_fetch=False,
            should_merge_ff=False,
        )

    if not facts.has_git:
        rows.append(StatusRecord("ERROR", subject, "internal state: missing Git metadata"))
        return LocalSyncPlan(
            records=tuple(rows),
            should_clone=False,
            should_fetch=False,
            should_merge_ff=False,
        )

    if facts.origin_url:
        cur = canonical_git_remote(facts.origin_url)
        exp_s = canonical_git_remote(expected_ssh_url)
        exp_h = canonical_git_remote(expected_https_url)
        if cur not in {exp_s, exp_h}:
            rows.append(
                StatusRecord(
                    "WARN",
                    subject,
                    f"origin URL differs from configured forge URL ({facts.origin_url})",
                ),
            )

    if facts.submodule_dotfile:
        rows.append(
            StatusRecord(
                "SKIP",
                subject,
                "WARN: contains submodules — skipped (MVP)",
            ),
        )
        return LocalSyncPlan(
            records=tuple(rows),
            should_clone=False,
            should_fetch=False,
            should_merge_ff=False,
        )

    if facts.dirty:
        rows.append(
            StatusRecord("SKIP", subject, "working tree dirty — left untouched"),
        )
        return LocalSyncPlan(
            records=tuple(rows),
            should_clone=False,
            should_fetch=False,
            should_merge_ff=False,
        )

    if facts.detached:
        rows.append(StatusRecord("SKIP", subject, "detached HEAD — skipped"))
        return LocalSyncPlan(
            records=tuple(rows),
            should_clone=False,
            should_fetch=False,
            should_merge_ff=False,
        )

    if facts.upstream is None:
        rows.append(
            StatusRecord("SKIP", subject, "no upstream tracking branch (@{upstream})"),
        )
        return LocalSyncPlan(
            records=tuple(rows),
            should_clone=False,
            should_fetch=False,
            should_merge_ff=False,
        )

    if facts.ahead > 0 and facts.behind > 0:
        rows.append(
            StatusRecord(
                "SKIP",
                subject,
                f"non-ff: {facts.ahead} ahead, {facts.behind} behind",
            ),
        )
        return LocalSyncPlan(
            records=tuple(rows),
            should_clone=False,
            should_fetch=False,
            should_merge_ff=False,
        )

    if facts.ahead > 0 and facts.behind == 0:
        rows.append(
            StatusRecord("SKIP", subject, f"local ahead by {facts.ahead} — skipped"),
        )
        return LocalSyncPlan(
            records=tuple(rows),
            should_clone=False,
            should_fetch=False,
            should_merge_ff=False,
        )

    if facts.ahead == 0 and facts.behind == 0:
        rows.append(StatusRecord("OK", subject, "up-to-date"))
        return LocalSyncPlan(
            records=tuple(rows),
            should_clone=False,
            should_fetch=False,
            should_merge_ff=False,
        )

    # Behind-only (ff possible) or unknown counter fall-through
    if facts.behind > 0 and facts.ahead == 0:
        merge = strategy == "ff-only"
        return LocalSyncPlan(
            records=tuple(rows),
            should_clone=False,
            should_fetch=True,
            should_merge_ff=merge,
        )

    rows.append(StatusRecord("OK", subject, "up-to-date"))
    return LocalSyncPlan(
        records=tuple(rows),
        should_clone=False,
        should_fetch=False,
        should_merge_ff=False,
    )
