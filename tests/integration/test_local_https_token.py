"""Integration: HTTPS tokens never reach ``.git/config``, argv or output.

The forge URL is redirected to a local bare repo with ``url.<base>.insteadOf`` in an isolated
global git config, so the full ``local sync`` path runs offline.
"""

from __future__ import annotations

import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

import repoman.local.runner as runner_mod
from repoman.cli import main
from repoman.config import SCHEMA_VERSION
from repoman.local.git_ops import GitOutcome

TOKEN = "test-token-not-real-0123456789"
FORGE_URL = "https://gitlab.example.com/acme/widget.git"


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )
    return out.stdout.strip()


@pytest.fixture()
def forge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """A bare repo standing in for the forge, plus config pointing at it over HTTPS."""
    gitconfig = tmp_path / "gitconfig"
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(gitconfig))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.delenv("GIT_CONFIG_COUNT", raising=False)
    monkeypatch.setenv("REPOMAN_TEST_TOKEN", TOKEN)
    monkeypatch.chdir(tmp_path)

    seed = tmp_path / "seed"
    seed.mkdir()
    _git(seed, "init", "-q", "-b", "main")
    _git(seed, "config", "user.email", "t@example.com")
    _git(seed, "config", "user.name", "t")
    (seed / "README.md").write_text("hello\n", encoding="utf-8")
    _git(seed, "add", "README.md")
    _git(seed, "commit", "-q", "-m", "init")

    bare_parent = tmp_path / "forge" / "acme"
    bare_parent.mkdir(parents=True)
    bare = bare_parent / "widget.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(bare)], check=True)
    gitconfig.write_text(
        f'[url "{(tmp_path / "forge").as_uri()}/"]\n'
        "\tinsteadOf = https://gitlab.example.com/\n"
        "[user]\n\temail = t@example.com\n\tname = t\n",
        encoding="utf-8",
    )

    ws = tmp_path / "ws"
    cfg = tmp_path / "repoman.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {
                "version": SCHEMA_VERSION,
                "paths": {"workspace_root": str(ws), "cache_root": str(tmp_path / "cache")},
                "remotes": {
                    "gitlab": {
                        "kind": "gitlab",
                        "base_url": "https://gitlab.example.com",
                        "token_env": "REPOMAN_TEST_TOKEN",
                        "clone_protocol": "https",
                    },
                },
                "namespaces": [],
                "repos": [
                    {
                        "source": {"remote": "gitlab", "path": "acme/widget"},
                        "local": "acme/widget",
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return {"cfg": cfg, "clone": ws / "acme" / "widget", "seed": seed, "bare": bare}


def _sync(cfg: Path, *extra: str) -> Any:
    return CliRunner().invoke(main, ["local", "sync", "--config", str(cfg), *extra])


def _git_config_text(clone: Path) -> str:
    return (clone / ".git" / "config").read_text(encoding="utf-8")


def test_clone_and_fetch_keep_token_out_of_config_and_argv(
    forge: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[tuple[str, ...], Mapping[str, str] | None]] = []
    real_clone, real_fetch = runner_mod.git_clone, runner_mod.git_fetch

    def spy_clone(url: str, dest: Path, **kw: Any) -> GitOutcome:
        calls.append(((url, str(dest)), kw.get("env")))
        return real_clone(url, dest, **kw)

    def spy_fetch(repo: Path, **kw: Any) -> GitOutcome:
        calls.append(((str(repo),), kw.get("env")))
        return real_fetch(repo, **kw)

    monkeypatch.setattr(runner_mod, "git_clone", spy_clone)
    monkeypatch.setattr(runner_mod, "git_fetch", spy_fetch)

    out = _sync(forge["cfg"], "--write")
    assert out.exit_code == 0, out.output
    assert "UPDATED" in out.output and "cloned" in out.output
    clone = forge["clone"]
    assert TOKEN not in _git_config_text(clone)
    assert _git(clone, "config", "--get", "remote.origin.url") == FORGE_URL

    # New upstream commit, then a fetch + ff-only merge through the same auth path.
    seed = forge["seed"]
    (seed / "more.txt").write_text("more\n", encoding="utf-8")
    _git(seed, "add", "more.txt")
    _git(seed, "commit", "-q", "-m", "more")
    _git(seed, "push", "-q", str(forge["bare"]), "main")
    _git(clone, "fetch", "-q")  # let the probe see "behind"
    _git(clone, "reset", "-q", "--hard", "HEAD")
    _git(clone, "update-ref", "refs/remotes/origin/main", _git(seed, "rev-parse", "HEAD"))

    out = _sync(forge["cfg"], "--write")
    assert out.exit_code == 0, out.output
    assert "fetch, merge_ff" in out.output
    assert TOKEN not in _git_config_text(clone)
    assert TOKEN not in out.output

    assert len(calls) == 2
    for argv, env in calls:
        assert all(TOKEN not in a for a in argv)
        assert env is not None
        assert env["GIT_CONFIG_KEY_0"] == "http.https://gitlab.example.com/.extraheader"
        assert env["GIT_CONFIG_VALUE_0"].startswith("Authorization: Basic ")


def test_old_tokenized_origin_is_rewritten(forge: dict[str, Path]) -> None:
    assert _sync(forge["cfg"], "--write").exit_code == 0
    clone = forge["clone"]
    _git(
        clone,
        "remote",
        "set-url",
        "origin",
        f"https://oauth2:{TOKEN}@gitlab.example.com/acme/widget.git",
    )

    preview = _sync(forge["cfg"])
    assert preview.exit_code == 0, preview.output
    assert "WOULD UPDATE" in preview.output and "remove token from origin URL" in preview.output
    assert TOKEN not in preview.output
    assert TOKEN in _git_config_text(clone)  # preview changes nothing

    applied = _sync(forge["cfg"], "--write")
    assert applied.exit_code == 0, applied.output
    assert "removed token from origin URL" in applied.output
    assert TOKEN not in applied.output
    assert TOKEN not in _git_config_text(clone)
    assert _git(clone, "config", "--get", "remote.origin.url") == FORGE_URL

    again = _sync(forge["cfg"])
    assert "token from origin URL" not in again.output


def test_foreign_credentials_left_alone_and_redacted(forge: dict[str, Path]) -> None:
    assert _sync(forge["cfg"], "--write").exit_code == 0
    clone = forge["clone"]
    foreign = f"https://alice:{TOKEN}@git.example.org/acme/widget.git"
    _git(clone, "remote", "set-url", "origin", foreign)

    out = _sync(forge["cfg"], "--write")
    assert "WARN" in out.output and "alice:***@git.example.org" in out.output
    assert TOKEN not in out.output
    assert _git(clone, "config", "--get", "remote.origin.url") == foreign

    status = CliRunner().invoke(main, ["local", "status", "--config", str(forge["cfg"]), "--json"])
    assert TOKEN not in status.output
