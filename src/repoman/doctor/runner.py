"""Doctor runner."""

from __future__ import annotations

from pathlib import Path

from repoman.config import apply_defaults, load_yaml, validate
from repoman.doctor.checks import check_config_file_exists
from repoman.paths import credentials_path_for_config
from repoman.remotes.github_client import GithubRemoteClient
from repoman.remotes.gitlab_client import GitlabRemoteClient
from repoman.secrets import resolve_token
from repoman.status import StatusRecord


def run_doctor(
    config_path: Path,
    *,
    skip_network: bool,
    cli_tokens: dict[str, str] | None = None,
) -> list[StatusRecord]:
    cli_tokens = cli_tokens or {}
    records: list[StatusRecord] = []

    exist = check_config_file_exists(config_path)
    if exist:
        records.append(exist)
    if exist and exist.level == "ERROR":
        return records

    try:
        raw = load_yaml(config_path)
    except Exception as e:
        records.append(StatusRecord("ERROR", "config.load", str(e)))
        return records

    merged = apply_defaults(raw)
    records.extend(validate(merged))
    if any(r.level == "ERROR" for r in records):
        return records

    cred_path = credentials_path_for_config(config_path)
    remotes = merged.get("remotes") or {}
    if not isinstance(remotes, dict):
        return records

    for rname, rcfg in sorted(remotes.items()):
        subj = f"remotes.{rname}"
        if not isinstance(rcfg, dict):
            continue
        try:
            token, src = resolve_token(
                rname,
                rcfg,
                cli_token=cli_tokens.get(rname),
                credentials_file=cred_path,
            )
        except PermissionError as e:
            records.append(StatusRecord("ERROR", subj + ".credentials", str(e)))
            continue

        if not token:
            records.append(
                StatusRecord(
                    "WARN",
                    subj + ".token",
                    "not resolved — set env or credentials",
                )
            )
            continue

        records.append(StatusRecord("OK", subj + ".token", f"resolved via {src}"))

        if skip_network:
            records.append(StatusRecord("OK", subj + ".api", "skipped (--skip-network)"))
            continue

        kind = rcfg.get("kind")
        base_url = str(rcfg.get("base_url", "")).strip()
        if kind == "gitlab":
            client = GitlabRemoteClient(base_url=base_url, token=token)
            ok, detail = client.probe_api()
            records.append(StatusRecord("OK" if ok else "ERROR", subj + ".api", detail))
        elif kind == "github":
            # github.com API lives at api.github.com; design stores api URL in base_url
            client = GithubRemoteClient(base_url=base_url or None, token=token)
            ok, detail = client.probe_api()
            records.append(StatusRecord("OK" if ok else "ERROR", subj + ".api", detail))

    return records
