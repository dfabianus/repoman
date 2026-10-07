"""Tests for clean clone URLs and per-command HTTPS auth."""

from __future__ import annotations

import base64

from repoman.local.clone_url import (
    basic_auth_header,
    clone_url,
    git_auth_env,
    has_repoman_credentials,
    http_auth_scope,
    redact_secret,
)


def test_ssh_protocol_uses_ssh_clone_url() -> None:
    u = clone_url(
        clone_protocol="ssh",
        ssh_url="git@gitlab.example.com:g/x.git",
        https_url="https://gitlab.example.com/g/x.git",
    )
    assert u == "git@gitlab.example.com:g/x.git"


def test_https_protocol_uses_clean_https_url() -> None:
    u = clone_url(
        clone_protocol="HTTPS",
        ssh_url="git@github.com:o/r.git",
        https_url="https://github.com/o/r.git",
    )
    assert u == "https://github.com/o/r.git"
    assert "@" not in u


def test_http_auth_scope_keeps_port_and_drops_path() -> None:
    assert http_auth_scope("https://GitLab.example.com:8443/g/x.git") == (
        "https://gitlab.example.com:8443/"
    )
    assert http_auth_scope("https://github.com/o/r.git") == "https://github.com/"
    assert http_auth_scope("git@github.com:o/r.git") is None


def _decoded(header: str) -> str:
    prefix = "Authorization: Basic "
    assert header.startswith(prefix)
    return base64.b64decode(header[len(prefix) :]).decode()


def test_basic_auth_header_user_per_forge() -> None:
    assert _decoded(basic_auth_header("github", "TOK")) == "x-access-token:TOK"
    assert _decoded(basic_auth_header("gitlab", "TOK")) == "oauth2:TOK"


def test_git_auth_env_github() -> None:
    env = git_auth_env(
        forge_kind="github",
        clone_protocol="https",
        https_url="https://github.com/o/r.git",
        token="TOK",
        base_env={},
    )
    assert env["GIT_CONFIG_COUNT"] == "1"
    assert env["GIT_CONFIG_KEY_0"] == "http.https://github.com/.extraheader"
    assert _decoded(env["GIT_CONFIG_VALUE_0"]) == "x-access-token:TOK"


def test_git_auth_env_gitlab_appends_to_existing_env_config() -> None:
    env = git_auth_env(
        forge_kind="gitlab",
        clone_protocol="https",
        https_url="https://gitlab.example.com/g/x.git",
        token="TOK",
        base_env={"GIT_CONFIG_COUNT": "2"},
    )
    assert env == {
        "GIT_CONFIG_COUNT": "3",
        "GIT_CONFIG_KEY_2": "http.https://gitlab.example.com/.extraheader",
        "GIT_CONFIG_VALUE_2": basic_auth_header("gitlab", "TOK"),
    }


def test_git_auth_env_empty_for_ssh_or_missing_token() -> None:
    common = {"forge_kind": "github", "https_url": "https://github.com/o/r.git", "base_env": {}}
    assert git_auth_env(clone_protocol="ssh", token="TOK", **common) == {}  # type: ignore[arg-type]
    assert git_auth_env(clone_protocol="https", token=None, **common) == {}  # type: ignore[arg-type]


def test_has_repoman_credentials_matches_only_old_repoman_urls() -> None:
    gh = "https://github.com/o/r.git"
    assert has_repoman_credentials(
        "https://x-access-token:TOK@github.com/o/r.git", forge_kind="github", expected_https_url=gh
    )
    assert has_repoman_credentials(
        "https://x-access-token:***@github.com/o/r", forge_kind="github", expected_https_url=gh
    )
    # Different user name, wrong forge user, other repo, no secret, clean URL: untouched.
    for url in (
        "https://alice:pw@github.com/o/r.git",
        "https://oauth2:TOK@github.com/o/r.git",
        "https://x-access-token:TOK@github.com/o/other.git",
        "https://x-access-token@github.com/o/r.git",
        gh,
        "git@github.com:o/r.git",
    ):
        assert not has_repoman_credentials(url, forge_kind="github", expected_https_url=gh), url
    assert has_repoman_credentials(
        "https://oauth2:TOK@gitlab.example.com/g/x.git",
        forge_kind="gitlab",
        expected_https_url="https://gitlab.example.com/g/x.git",
    )


def test_redact_secret() -> None:
    assert redact_secret("fatal: bad TOK here TOK", "TOK") == "fatal: bad *** here ***"
    assert redact_secret("unchanged", None) == "unchanged"
