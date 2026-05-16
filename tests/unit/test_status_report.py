"""Tests for local status reporting (pure)."""

from __future__ import annotations

from repoman.local.status_probe import RepoWorktreeFacts
from repoman.local.status_report import (
    snapshot_to_json_dict,
    status_payload_to_json_dict,
    summarize_local_repo_status,
)


def _facts(**kwargs: object) -> RepoWorktreeFacts:
    base = {
        "path_missing": False,
        "not_git_directory": False,
        "has_git": True,
        "submodule_dotfile": False,
        "detached": False,
        "dirty": False,
        "branch": "main",
        "upstream": "origin/main",
        "ahead": 0,
        "behind": 0,
        "origin_url": "git@github.com:o/r.git",
        "last_fetch_epoch": 1_700_000_000.0,
    }
    base.update(kwargs)
    return RepoWorktreeFacts(**base)  # type: ignore[arg-type]


def test_missing_clone_ok_not_cloned() -> None:
    snap, lines = summarize_local_repo_status(
        subject="o/r",
        relative_path="github/o/r",
        facts=_facts(path_missing=True, has_git=False, branch=""),
        expected_ssh_url="git@github.com:o/r.git",
        expected_https_url="https://github.com/o/r.git",
    )
    assert snap.level == "OK"
    assert snap.detail == "not cloned"
    assert lines[0].level == "OK"
    assert lines[0].detail == "not cloned"


def test_behind_reports_commits_behind() -> None:
    snap, lines = summarize_local_repo_status(
        subject="o/r",
        relative_path="github/o/r",
        facts=_facts(behind=4),
        expected_ssh_url="git@github.com:o/r.git",
        expected_https_url="https://github.com/o/r.git",
    )
    assert snap.level == "OK"
    assert "4 commits behind" in snap.detail
    assert lines[0].detail == snap.detail


def test_diverged_warn_non_ff() -> None:
    snap, _lines = summarize_local_repo_status(
        subject="o/r",
        relative_path="github/o/r",
        facts=_facts(ahead=2, behind=3),
        expected_ssh_url="git@github.com:o/r.git",
        expected_https_url="https://github.com/o/r.git",
    )
    assert snap.level == "WARN"
    assert "non-ff" in snap.detail


def test_origin_drift_emits_extra_warn_line() -> None:
    _snap, lines = summarize_local_repo_status(
        subject="o/r",
        relative_path="github/o/r",
        facts=_facts(origin_url="https://other.example/o/r.git"),
        expected_ssh_url="git@github.com:o/r.git",
        expected_https_url="https://github.com/o/r.git",
    )
    assert len(lines) == 2
    assert lines[1].level == "WARN"
    assert "origin URL differs" in lines[1].detail


def test_json_payload_shape() -> None:
    snap, _ = summarize_local_repo_status(
        subject="o/r",
        relative_path="github/o/r",
        facts=_facts(),
        expected_ssh_url="git@github.com:o/r.git",
        expected_https_url="https://github.com/o/r.git",
    )
    repo_json = snapshot_to_json_dict(snap)
    assert repo_json["subject"] == "o/r"
    assert repo_json["last_fetch_epoch"] == 1_700_000_000.0

    payload = status_payload_to_json_dict(
        schema_version=1,
        workspace_root="/tmp/ws",
        prelude=[],
        repositories=[snap],
    )
    assert payload["schema_version"] == 1
    assert payload["workspace_root"] == "/tmp/ws"
    assert len(payload["repositories"]) == 1
