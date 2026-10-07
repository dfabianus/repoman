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


def test_redact_url_credentials() -> None:
    from repoman.remotes.url_normalize import redact_url_credentials

    assert (
        redact_url_credentials("https://oauth2:SECRET@gitlab.example.com/g/x.git")
        == "https://oauth2:***@gitlab.example.com/g/x.git"
    )
    assert redact_url_credentials("https://SECRET@github.com/o/r.git") == (
        "https://***@github.com/o/r.git"
    )
    assert redact_url_credentials("git@github.com:o/r.git") == "git@github.com:o/r.git"
    assert redact_url_credentials("ssh://git@host/o/r.git") == "ssh://git@host/o/r.git"
    assert redact_url_credentials("https://github.com/o/r.git") == "https://github.com/o/r.git"
