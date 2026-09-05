"""Secrets resolver precedence tests."""

import os
from pathlib import Path

import pytest

from repoman.secrets import TokenCommandError, resolve_token


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


@pytest.mark.skipif(os.name == "nt", reason="POSIX 0600 enforcement is skipped on Windows")
def test_credentials_wrong_mode_raises(tmp_path: Path) -> None:
    cred = tmp_path / "credentials.toml"
    cred.write_text('[gitlab]\ntoken = "x"\n', encoding="utf-8")
    os.chmod(cred, 0o644)
    cfg = {"token_credentials": "gitlab"}
    with pytest.raises(PermissionError):
        resolve_token("gitlab", cfg, cli_token=None, credentials_file=cred)


def test_token_command_used_when_env_missing(tmp_path: Path) -> None:
    cfg = {"token_command": ["python", "-c", "print('  from-command\\n')"]}
    tok, src = resolve_token("github", cfg, cli_token=None, credentials_file=tmp_path / "x.toml")
    assert tok == "from-command"
    assert src == "command:python"


def test_env_beats_token_command(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MY_TOKEN", "from-env")
    cfg = {"token_env": "MY_TOKEN", "token_command": ["python", "-c", "print('nope')"]}
    tok, src = resolve_token("github", cfg, cli_token=None, credentials_file=tmp_path / "x.toml")
    assert tok == "from-env"
    assert src == "env:MY_TOKEN"


def test_token_command_beats_credentials_file(tmp_path: Path) -> None:
    cred = tmp_path / "credentials.toml"
    cred.write_text('[github]\ntoken = "from-file"\n', encoding="utf-8")
    os.chmod(cred, 0o600)
    cfg = {
        "token_command": ["python", "-c", "print('from-command')"],
        "token_credentials": "github",
    }
    tok, _src = resolve_token("github", cfg, cli_token=None, credentials_file=cred)
    assert tok == "from-command"


def test_token_command_failure_raises(tmp_path: Path) -> None:
    cfg = {"token_command": ["python", "-c", "import sys; sys.exit(3)"]}
    with pytest.raises(TokenCommandError):
        resolve_token("github", cfg, cli_token=None, credentials_file=tmp_path / "x.toml")


def test_token_command_empty_output_raises(tmp_path: Path) -> None:
    cfg = {"token_command": ["python", "-c", "print('   ')"]}
    with pytest.raises(TokenCommandError):
        resolve_token("github", cfg, cli_token=None, credentials_file=tmp_path / "x.toml")


def test_token_command_missing_binary_raises(tmp_path: Path) -> None:
    cfg = {"token_command": ["definitely-not-a-real-binary-xyz"]}
    with pytest.raises(TokenCommandError):
        resolve_token("github", cfg, cli_token=None, credentials_file=tmp_path / "x.toml")
