"""CLI smoke for ``repoman local``."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from repoman.cli import main
from repoman.config import SCHEMA_VERSION


def test_local_plan_no_targets_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = tmp_path / "repoman.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {
                "version": SCHEMA_VERSION,
                "paths": {"workspace_root": str(tmp_path / "ws")},
                "remotes": {},
                "namespaces": [],
                "repos": [],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    runner = CliRunner()
    out = runner.invoke(main, ["local", "plan", "--config", str(cfg)])
    assert out.exit_code == 0
    assert "workspace_root" in out.output.lower() or "local.targets" in out.output


def test_local_help_registered() -> None:
    runner = CliRunner()
    out = runner.invoke(main, ["local", "--help"])
    assert out.exit_code == 0
    assert "plan" in out.output and "sync" in out.output
