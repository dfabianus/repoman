"""Click CLI entrypoint."""

from __future__ import annotations

import json
from pathlib import Path

import click
import yaml

from repoman import __version__
from repoman.config import apply_defaults, load_yaml, validate
from repoman.doctor.runner import run_doctor
from repoman.local.runner import SyncStrategy, run_local, run_local_status
from repoman.local.status_report import status_payload_to_json_dict
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


@main.group("local")
def local_cmd() -> None:
    """Manage local clones under workspace_root (preview-first)."""


@local_cmd.command("plan")
@click.option(
    "--namespace",
    multiple=True,
    metavar="NAME",
    help="Limit discovery to namespaces with this exact name.",
)
@click.option(
    "--strategy",
    type=click.Choice(["ff-only", "fetch-only"]),
    default="ff-only",
    show_default=True,
    help="How existing clones align with upstream for preview text.",
)
@click.option(
    "--parallel",
    type=int,
    default=None,
    metavar="N",
    help="Worker count (defaults to settings.parallelism).",
)
@click.option(
    "--refresh-discovery",
    is_flag=True,
    help="Bypass discovery cache TTL and reload listings from APIs.",
)
@click.option("--changes-only", is_flag=True, help="Suppress OK-only status lines.")
@click.option("--config", type=click.Path(path_type=Path), default=None)
def local_plan_cmd(
    namespace: tuple[str, ...],
    strategy: str,
    parallel: int | None,
    refresh_discovery: bool,
    changes_only: bool,
    config: Path | None,
) -> None:
    """Show what ``local sync`` would do without writing to disk."""
    path = _config_path(config)
    strat: SyncStrategy = "ff-only" if strategy != "fetch-only" else "fetch-only"
    recs = run_local(
        path,
        namespace_filter=namespace,
        write=False,
        parallelism=parallel,
        refresh_discovery=refresh_discovery,
        strategy=strat,
        changes_only_cli=changes_only,
    )
    for r in recs:
        click.echo(format_line(r))
    raise SystemExit(exit_code_for_records(recs))


@local_cmd.command("sync")
@click.option("--namespace", multiple=True, metavar="NAME")
@click.option(
    "--strategy",
    type=click.Choice(["ff-only", "fetch-only"]),
    default="ff-only",
    show_default=True,
)
@click.option("--parallel", type=int, default=None, metavar="N")
@click.option("--refresh-discovery", is_flag=True)
@click.option("--changes-only", is_flag=True)
@click.option("--write", is_flag=True, help="Perform clones/fetches/ff-only merges.")
@click.option("--config", type=click.Path(path_type=Path), default=None)
def local_sync_cmd(
    namespace: tuple[str, ...],
    strategy: str,
    parallel: int | None,
    refresh_discovery: bool,
    changes_only: bool,
    write: bool,
    config: Path | None,
) -> None:
    """Clone/update repositories under workspace_root."""
    path = _config_path(config)
    strat: SyncStrategy = "ff-only" if strategy != "fetch-only" else "fetch-only"
    recs = run_local(
        path,
        namespace_filter=namespace,
        write=write,
        parallelism=parallel,
        refresh_discovery=refresh_discovery,
        strategy=strat,
        changes_only_cli=changes_only,
    )
    for r in recs:
        click.echo(format_line(r))
    raise SystemExit(exit_code_for_records(recs))


@local_cmd.command("status")
@click.option("--namespace", multiple=True, metavar="NAME")
@click.option("--parallel", type=int, default=None, metavar="N")
@click.option("--refresh-discovery", is_flag=True)
@click.option("--changes-only", is_flag=True, help="Suppress OK-only status lines.")
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON.")
@click.option("--config", type=click.Path(path_type=Path), default=None)
def local_status_cmd(
    namespace: tuple[str, ...],
    parallel: int | None,
    refresh_discovery: bool,
    changes_only: bool,
    json_output: bool,
    config: Path | None,
) -> None:
    """Report ahead/behind, dirty state, and clone presence (read-only)."""
    path = _config_path(config)
    result = run_local_status(
        path,
        namespace_filter=namespace,
        parallelism=parallel,
        refresh_discovery=refresh_discovery,
        changes_only_cli=changes_only,
    )
    all_records = list(result.prelude) + list(result.repo_lines)
    if json_output:
        payload = status_payload_to_json_dict(
            schema_version=1,
            workspace_root=str(result.workspace_root),
            prelude=list(result.prelude),
            repositories=list(result.snapshots),
        )
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for rec in result.prelude:
            click.echo(format_line(rec))
        for rec in result.repo_lines:
            click.echo(format_line(rec))
    raise SystemExit(exit_code_for_records(all_records))


if __name__ == "__main__":
    main()
