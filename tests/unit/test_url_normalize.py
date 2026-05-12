"""Tests for remote URL normalization."""

from __future__ import annotations

from repoman.remotes.url_normalize import canonical_git_remote


def test_strip_git_suffix_and_https_user() -> None:
    ssh = canonical_git_remote("git@gitlab.com:acme/repo.git")
    https = canonical_git_remote("https://gitlab-ci-token:TOKEN@gitlab.com/acme/repo.git")
    assert ssh.endswith("acme/repo")
    assert ":token@" not in https  # lowercase host/path
    assert "gitlab-ci-token" not in https
    assert https.endswith("/acme/repo")
