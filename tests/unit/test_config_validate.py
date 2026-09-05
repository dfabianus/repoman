"""Config validation unit tests."""

from repoman.config import SCHEMA_VERSION, apply_defaults, validate


def test_validate_minimal_ok() -> None:
    raw = {"version": SCHEMA_VERSION, "remotes": {}}
    merged = apply_defaults(raw)
    recs = validate(merged)
    assert all(r.level != "ERROR" for r in recs)


def test_validate_unknown_layout_placeholder() -> None:
    raw = {
        "version": SCHEMA_VERSION,
        "remotes": {},
        "layout": "{remote}/{whoops}/{repo}",
    }
    merged = apply_defaults(raw)
    recs = validate(merged)
    assert any(r.subject == "layout" and r.level == "ERROR" for r in recs)


def test_validate_mirror_duplicate_id() -> None:
    raw = {
        "version": SCHEMA_VERSION,
        "remotes": {
            "gitlab": {
                "kind": "gitlab",
                "base_url": "https://gitlab.example.com",
                "token_env": "T",
            },
            "github": {
                "kind": "github",
                "base_url": "https://api.github.com",
                "token_env": "G",
            },
        },
        "mirrors": [
            {
                "id": "dup",
                "source": {"remote": "gitlab", "path": "a/b"},
                "target": {"remote": "github", "path": "x/y"},
                "direction": "push",
                "backend": "gitlab_remote_mirror",
            },
            {
                "id": "dup",
                "source": {"remote": "gitlab", "path": "c/d"},
                "target": {"remote": "github", "path": "m/n"},
                "direction": "push",
                "backend": "gitlab_remote_mirror",
            },
        ],
    }
    merged = apply_defaults(raw)
    recs = validate(merged)
    assert any("duplicate mirror id" in r.detail for r in recs if r.level == "ERROR")


def test_validate_gitlab_mirror_requires_gitlab_source() -> None:
    raw = {
        "version": SCHEMA_VERSION,
        "remotes": {
            "gitlab": {
                "kind": "gitlab",
                "base_url": "https://gitlab.example.com",
                "token_env": "T",
            },
            "github": {
                "kind": "github",
                "base_url": "https://api.github.com",
                "token_env": "G",
            },
        },
        "mirrors": [
            {
                "id": "bad",
                "source": {"remote": "github", "path": "o/r"},
                "target": {"remote": "gitlab", "path": "a/b"},
                "direction": "push",
                "backend": "gitlab_remote_mirror",
            },
        ],
    }
    merged = apply_defaults(raw)
    recs = validate(merged)
    assert any("gitlab_remote_mirror requires source remote kind=gitlab" in r.detail for r in recs)


def _remote_with(**extra: object) -> dict:
    return {
        "version": SCHEMA_VERSION,
        "remotes": {
            "github": {
                "kind": "github",
                "base_url": "https://api.github.com",
                **extra,
            }
        },
    }


def test_validate_token_command_counts_as_token_source() -> None:
    recs = validate(apply_defaults(_remote_with(token_command=["gh", "auth", "token"])))
    assert all(r.level != "ERROR" for r in recs)
    assert not any(r.subject == "remotes.github.token" and r.level == "WARN" for r in recs)


def test_validate_no_token_source_warns() -> None:
    recs = validate(apply_defaults(_remote_with()))
    assert any(r.subject == "remotes.github.token" and r.level == "WARN" for r in recs)


def test_validate_token_command_must_be_list_of_strings() -> None:
    for bad in ("gh auth token", [], ["gh", 3], [""]):
        recs = validate(apply_defaults(_remote_with(token_command=bad)))
        assert any(
            r.subject == "remotes.github.token_command" and r.level == "ERROR" for r in recs
        ), bad
