"""CLI smoke tests."""

from pathlib import Path

import yaml
from click.testing import CliRunner

from repoman.cli import main
from repoman.config import SCHEMA_VERSION


def test_version_option() -> None:
    runner = CliRunner()
    r = runner.invoke(main, ["--version"])
    assert r.exit_code == 0
    assert "repoman" in r.output


def test_config_validate_missing_file() -> None:
    runner = CliRunner()
    r = runner.invoke(main, ["config", "validate", "--config", "/nonexistent/repoman.yaml"])
    assert r.exit_code == 2


def test_config_validate_ok(tmp_path: Path) -> None:
    cfg = tmp_path / "repoman.yaml"
    cfg.write_text(
        yaml.safe_dump({"version": SCHEMA_VERSION, "remotes": {}}),
        encoding="utf-8",
    )
    runner = CliRunner()
    r = runner.invoke(main, ["config", "validate", "--config", str(cfg)])
    assert r.exit_code == 0
    assert "config.version" in r.output


def test_config_init_and_set(tmp_path: Path) -> None:
    cfg = tmp_path / "repoman.yaml"
    runner = CliRunner()
    init_r = runner.invoke(main, ["config", "init", "--config", str(cfg)])
    assert init_r.exit_code == 0
    assert "Next steps" in init_r.output

    preview = runner.invoke(
        main,
        ["config", "set", "paths.workspace_root", "~/work", "--config", str(cfg)],
    )
    assert preview.exit_code == 0
    assert "WOULD UPDATE" in preview.output

    write_r = runner.invoke(
        main,
        [
            "config",
            "set",
            "paths.workspace_root",
            "~/work",
            "--write",
            "--config",
            str(cfg),
        ],
    )
    assert write_r.exit_code == 0
    assert "UPDATED" in write_r.output
    data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    assert data["paths"]["workspace_root"] == "~/work"
