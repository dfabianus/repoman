"""Click CLI entrypoint."""

from __future__ import annotations

from pathlib import Path

import click
import yaml

from repoman import __version__
from repoman.config import apply_defaults, load_yaml, validate
from repoman.doctor.runner import run_doctor
from repoman.paths import default_config_path
from repoman.status import StatusRecord, exit_code_for_records, format_line


def _config_path(config: Path | None) -> Path:
    return (config if config is not None else default_config_path()).expanduser()


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="repoman")
def main() -> None:
    """Declarative multi-forge Git workspace sync and mirror management (MVP)."""


@main.group("config")
def config_cmd() -> None:
    """Inspect and validate repoman.yaml."""


@config_cmd.command("path")
@click.option(
    "--config",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to repoman.yaml (default: platform default).",
)
def config_path_cmd(config: Path | None) -> None:
    """Print the active configuration file path."""
    click.echo(_config_path(config))


@config_cmd.command("validate")
@click.option("--config", type=click.Path(path_type=Path), default=None)
def config_validate_cmd(config: Path | None) -> None:
    """Load YAML and run schema validation."""
    path = _config_path(config)
    if not path.is_file():
        click.echo(
            format_line(StatusRecord("ERROR", "config.file", f"not found: {path}")),
            err=True,
        )
        raise SystemExit(2)
    try:
        raw = load_yaml(path)
    except Exception as e:
        click.echo(format_line(StatusRecord("ERROR", "config.load", str(e))), err=True)
        raise SystemExit(2) from None

    merged = apply_defaults(raw)
    records = validate(merged)
    for r in records:
        click.echo(format_line(r))
    raise SystemExit(exit_code_for_records(records))


@config_cmd.command("show")
@click.option("--config", type=click.Path(path_type=Path), default=None)
@click.option(
    "--resolved",
    is_flag=True,
    help="Merge defaults before printing.",
)
def config_show_cmd(config: Path | None, resolved: bool) -> None:
    """Print configuration as YAML."""
    path = _config_path(config)
    if not path.is_file():
        click.echo(
            format_line(StatusRecord("ERROR", "config.file", f"not found: {path}")),
            err=True,
        )
        raise SystemExit(2)
    try:
        raw = load_yaml(path)
    except Exception as e:
        click.echo(format_line(StatusRecord("ERROR", "config.load", str(e))), err=True)
        raise SystemExit(2) from None
    data = apply_defaults(raw) if resolved else raw
    click.echo(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


@main.command("doctor")
@click.option("--skip-network", is_flag=True, help="Resolve tokens only; skip HTTP probes.")
@click.option("--config", type=click.Path(path_type=Path), default=None)
def doctor_cmd(skip_network: bool, config: Path | None) -> None:
    """Check config, secrets, and remote API reachability."""
    path = _config_path(config)
    records = run_doctor(path, skip_network=skip_network)
    for r in records:
        click.echo(format_line(r))
    raise SystemExit(exit_code_for_records(records))


if __name__ == "__main__":
    main()
