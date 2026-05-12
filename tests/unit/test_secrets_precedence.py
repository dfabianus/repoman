"""Secrets resolver precedence tests."""

import os
from pathlib import Path

import pytest

from repoman.secrets import resolve_token


def test_cli_overrides_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MY_TOKEN", "from-env")
    cfg = {"token_env": "MY_TOKEN"}
    tok, src = resolve_token(
        "gitlab",
        cfg,
        cli_token="from-cli",
        credentials_file=tmp_path / "x.toml",
    )
    assert tok == "from-cli"
    assert src == "cli"


def test_env_used_when_no_cli(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MY_TOKEN", "secret")
    cfg = {"token_env": "MY_TOKEN"}
    tok, src = resolve_token("gitlab", cfg, cli_token=None, credentials_file=tmp_path / "x.toml")
    assert tok == "secret"
    assert src == "env:MY_TOKEN"


def test_credentials_toml_when_env_missing(tmp_path: Path) -> None:
    cred = tmp_path / "credentials.toml"
    cred.write_text('[gitlab]\ntoken = "glpat-xx"\n', encoding="utf-8")
    os.chmod(cred, 0o600)
    cfg = {"token_credentials": "gitlab"}
    tok, src = resolve_token(
        "gitlab",
        cfg,
        cli_token=None,
        credentials_file=cred,
    )
    assert tok == "glpat-xx"
    assert src == "credentials.toml:gitlab"


def test_credentials_wrong_mode_raises(tmp_path: Path) -> None:
    cred = tmp_path / "credentials.toml"
    cred.write_text('[gitlab]\ntoken = "x"\n', encoding="utf-8")
    os.chmod(cred, 0o644)
    cfg = {"token_credentials": "gitlab"}
    with pytest.raises(PermissionError):
        resolve_token("gitlab", cfg, cli_token=None, credentials_file=cred)
