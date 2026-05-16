"""Integration: ``local status`` against a real worktree."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from repoman.cli import main
from repoman.config import SCHEMA_VERSION


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_local_status_dirty_worktree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    empty_template = tmp_path / "git-template"
    empty_template.mkdir()
    ws = tmp_path / "ws"
    repo_dir = ws / "explicit" / "widget"
    repo_dir.mkdir(parents=True)
    _git(repo_dir, "init", "--template", str(empty_template))
    _git(repo_dir, "config", "user.email", "t@example.com")
    _git(repo_dir, "config", "user.name", "t")
    (repo_dir / "README.md").write_text("hello\n", encoding="utf-8")
    _git(repo_dir, "add", "README.md")
    _git(repo_dir, "commit", "-m", "init")

    cfg = tmp_path / "repoman.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {
                "version": SCHEMA_VERSION,
                "paths": {"workspace_root": str(ws)},
                "remotes": {
                    "gitlab": {
                        "kind": "gitlab",
                        "base_url": "https://gitlab.example.com",
                        "clone_protocol": "ssh",
                    },
                },
                "namespaces": [],
                "repos": [
                    {
                        "source": {"remote": "gitlab", "path": "acme/widget"},
                        "local": "explicit/widget",
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    (repo_dir / "dirty.txt").write_text("x\n", encoding="utf-8")

    runner = CliRunner()
    text_out = runner.invoke(main, ["local", "status", "--config", str(cfg)])
    assert text_out.exit_code == 0
    assert "acme/widget" in text_out.output
    assert "dirty" in text_out.output.lower()

    json_out = runner.invoke(main, ["local", "status", "--config", str(cfg), "--json"])
    assert json_out.exit_code == 0
    payload = json.loads(json_out.output)
    assert payload["repositories"][0]["dirty"] is True
    assert payload["repositories"][0]["level"] == "WARN"
