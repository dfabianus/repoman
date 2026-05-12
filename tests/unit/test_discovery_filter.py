"""Tests for forge discovery glob filtering."""

from __future__ import annotations

from repoman.remotes.catalog import ListedProject
from repoman.remotes.discovery import (
    filter_listed_projects,
    passes_path_globs,
    relative_repo_path_under_namespace,
)


def test_relative_under_namespace_strip() -> None:
    assert relative_repo_path_under_namespace("acme/widget", "acme") == "widget"


def test_relative_subgroup() -> None:
    assert relative_repo_path_under_namespace("acme/sub/widget", "acme") == "sub/widget"


def test_exclude_archived_in_filter_layer() -> None:
    repos = [
        ListedProject(
            path_with_namespace="acme/widget",
            ssh_url_to_repo="git@gitlab.test:acme/widget.git",
            http_url_to_repo="https://gitlab.test/acme/widget.git",
            archived=True,
            visibility="internal",
            default_branch=None,
        ),
        ListedProject(
            path_with_namespace="acme/ok",
            ssh_url_to_repo="git@gitlab.test:acme/ok.git",
            http_url_to_repo="https://gitlab.test/acme/ok.git",
            archived=False,
            visibility="internal",
            default_branch=None,
        ),
    ]
    out = filter_listed_projects(
        repos,
        namespace_root="acme",
        include_patterns=["**/*"],
        exclude_patterns=[],
        visibility_allowlist=None,
    )
    assert len(out) == 1 and out[0].path_with_namespace.endswith("ok")


def test_include_exclude_star() -> None:
    assert passes_path_globs("foo/bar", include_patterns=["**/*"], exclude_patterns=[])
    assert not passes_path_globs(
        "evil/bad", include_patterns=["**/*"], exclude_patterns=["evil/**"]
    )
