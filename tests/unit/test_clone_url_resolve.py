"""Tests for authenticated clone URLs."""

from __future__ import annotations

from repoman.local.clone_url import authenticated_clone_url, inject_https_credentials


def test_ssh_protocol_uses_ssh_clone_url() -> None:
    u = authenticated_clone_url(
        forge_kind="gitlab",
        clone_protocol="ssh",
        ssh_url="git@gitlab.com:g/x.git",
        https_url="https://gitlab.com/g/x.git",
        token="sekret",
    )
    assert u == "git@gitlab.com:g/x.git"


def test_gitlab_https_injects_oauth() -> None:
    u = inject_https_credentials(
        forge_kind="gitlab", https_url="https://gitlab.com/g/x.git", token="ABC"
    )
    assert "gitlab.com" in u
    assert "oauth2:ABC@" in u


def test_github_https_injects_x_access_token() -> None:
    u = inject_https_credentials(
        forge_kind="github",
        https_url="https://github.com/o/r.git",
        token="TOKEN",
    )
    assert "x-access-token:TOKEN@" in u
