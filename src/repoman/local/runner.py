"""Orchestrate namespace discovery and local workspace sync."""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from repoman.cache import (
    cache_payload_projects,
    discovery_cache_path,
    read_discovery_cache,
    write_discovery_cache,
)
from repoman.config import apply_defaults, load_yaml, validate
from repoman.local.clone_url import authenticated_clone_url
from repoman.local.git_ops import git_clone, git_fetch, git_merge_ff_only
from repoman.local.planner import plan_local_sync
from repoman.local.status_probe import probe_worktree
from repoman.local.status_report import RepoStatusSnapshot, summarize_local_repo_status
from repoman.paths import credentials_path_for_config, render_layout
from repoman.remotes.catalog import ListedProject
from repoman.remotes.clone_urls import synthesized_clone_urls
from repoman.remotes.discovery import filter_listed_projects, relative_repo_path_under_namespace
from repoman.remotes.github_client import GithubRemoteClient
from repoman.remotes.gitlab_client import GitlabRemoteClient
from repoman.secrets import resolve_token
from repoman.status import StatusRecord

ForgeKind = Literal["gitlab", "github"]
SyncStrategy = Literal["ff-only", "fetch-only"]


@dataclass(frozen=True)
class LocalWorkspaceContext:
    """Shared outcome of config load + namespace discovery."""

    workspace_root: Path
    cache_root: Path
    targets: tuple[WorkspaceRepo, ...]
    remotes: dict[str, Any]
    credentials_path: Path
    changes_only_mode: bool
    parallelism_default: int


@dataclass(frozen=True)
class LocalStatusResult:
    """Read-only status run: prelude lines, per-repo lines, and structured snapshots."""

    prelude: tuple[StatusRecord, ...]
    repo_lines: tuple[StatusRecord, ...]
    snapshots: tuple[RepoStatusSnapshot, ...]
    workspace_root: Path


@dataclass(frozen=True)
class WorkspaceRepo:
    """One repository slated for sync under the workspace root."""

    subject: str
    remote_name: str
    forge_kind: ForgeKind
    forge_path: str
    relative_posix: str
    ssh_clone: str
    https_clone: str
    clone_protocol: str


def _truthy_changes_only(setting: dict[str, Any], flag: bool) -> bool:
    return bool(setting.get("changes_only")) if not flag else True


def _namespaces_filtered(
    namespaces: Iterable[dict[str, Any]], wanted: Sequence[str]
) -> list[dict[str, Any]]:
    ns_list = [n for n in namespaces if isinstance(n, dict)]
    if not wanted:
        return ns_list
    allow = frozenset(wanted)
    return [n for n in ns_list if isinstance(n.get("name"), str) and n["name"].strip() in allow]


def _collect_explicit_repos(cfg: dict[str, Any], remotes: dict[str, Any]) -> list[WorkspaceRepo]:
    """Repos from ``repos:`` entries use ``local`` verbatim under ``workspace_root``."""
    out: list[WorkspaceRepo] = []
    repos = cfg.get("repos")
    if not isinstance(repos, list):
        return out
    for entry in repos:
        if not isinstance(entry, dict):
            continue
        src = entry.get("source")
        loc = entry.get("local")
        if not isinstance(src, dict) or not isinstance(loc, str):
            continue
        rname_raw = src.get("remote")
        forge_path_raw = src.get("path")
        if not isinstance(rname_raw, str) or not isinstance(forge_path_raw, str):
            continue
        rname = rname_raw.strip()
        forge_path = forge_path_raw.strip()
        relative_posix = loc.strip().strip("/")
        if not rname or not forge_path or not relative_posix:
            continue
        rcfg = remotes.get(rname)
        if not isinstance(rcfg, dict):
            continue
        kind = rcfg.get("kind")
        if kind not in ("gitlab", "github"):
            continue
        base_u = str(rcfg.get("base_url") or "").strip()
        cp = str(rcfg.get("clone_protocol") or "ssh").lower()
        try:
            ssh_u, https_u = synthesized_clone_urls(
                kind,
                base_api_url=base_u,
                forge_path=forge_path,
            )
        except ValueError:
            continue
        out.append(
            WorkspaceRepo(
                subject=forge_path,
                remote_name=rname,
                forge_kind=kind,
                forge_path=forge_path,
                relative_posix=relative_posix.replace("\\", "/"),
                ssh_clone=ssh_u,
                https_clone=https_u,
                clone_protocol=cp,
            ),
        )
    return out


def _listed_to_workspace_repo(
    *,
    lp: ListedProject,
    remote_name: str,
    forge_kind: ForgeKind,
    namespace_name: str,
    layout_template: str,
    clone_protocol: str,
) -> WorkspaceRepo | None:
    """Map a ListedProject into a WorkspaceRepo entry."""
    rel_seg = relative_repo_path_under_namespace(lp.path_with_namespace, namespace_name)
    if rel_seg is None:
        return None
    repo_layout = rel_seg if rel_seg else lp.path_with_namespace.split("/")[-1]
    rel = render_layout(
        layout_template,
        remote=remote_name,
        namespace=namespace_name,
        subgroup="",
        repo=repo_layout,
    ).replace("\\", "/")
    ssh_u = lp.ssh_url_to_repo.strip()
    https_u = lp.http_url_to_repo.strip()
    if not ssh_u or not https_u:
        return None
    return WorkspaceRepo(
        subject=lp.path_with_namespace,
        remote_name=remote_name,
        forge_kind=forge_kind,
        forge_path=lp.path_with_namespace,
        relative_posix=rel,
        ssh_clone=ssh_u,
        https_clone=https_u,
        clone_protocol=clone_protocol,
    )


def _effective_cache_ttl(seconds: int | None, *, ci_mode: bool) -> int:
    if ci_mode:
        return 0
    if isinstance(seconds, int):
        return max(0, seconds)
    return 900


def _cache_needs_refresh(
    *,
    refresh_cli: bool,
    fetched_at_epoch: float | None,
    now: float,
    ttl_eff: int,
) -> bool:
    if refresh_cli:
        return True
    if fetched_at_epoch is None:
        return True
    if ttl_eff == 0:
        return True
    return (now - fetched_at_epoch) > float(ttl_eff)


def _prepare_local_workspace(
    config_path: Path,
    *,
    namespace_filter: Sequence[str],
    refresh_discovery: bool,
    changes_only_cli: bool,
    client_factory: Callable[[str, dict[str, Any], str], GithubRemoteClient | GitlabRemoteClient]
    | None = None,
) -> tuple[list[StatusRecord], LocalWorkspaceContext | None]:
    """
    Load config, run namespace discovery, and resolve workspace targets.

    Returns prelude status lines and a context object, or ``None`` when discovery
    cannot proceed (missing config, validation errors).
    """
    records: list[StatusRecord] = []
    if not config_path.is_file():
        records.append(StatusRecord("ERROR", "config.file", f"not found: {config_path}"))
        return records, None

    try:
        raw = load_yaml(config_path)
        merged = apply_defaults(raw)
    except Exception as e:
        records.append(StatusRecord("ERROR", "config.load", str(e)))
        return records, None

    vrec = validate(merged)
    if any(r.level == "ERROR" for r in vrec):
        records.extend(vrec)
        return records, None

    settings_any = merged.get("settings") or {}
    settings = settings_any if isinstance(settings_any, dict) else {}

    dsc_ttl = settings.get("discovery_cache_ttl")
    ttl_hint = dsc_ttl if isinstance(dsc_ttl, int) else None
    ci_mode = os.environ.get("CI", "").lower() in {"1", "true", "yes"}
    cache_ttl_eff = _effective_cache_ttl(ttl_hint, ci_mode=ci_mode)

    paths_cfg = merged.get("paths") or {}
    ws_root = Path(str(paths_cfg.get("workspace_root") or "~/repositories")).expanduser()
    cache_root = Path(str(paths_cfg.get("cache_root") or "~/.cache/repoman")).expanduser()

    records.append(StatusRecord("OK", "workspace_root", str(ws_root)))
    records.append(StatusRecord("OK", "cache_root", str(cache_root)))

    changes_only_mode = _truthy_changes_only(settings, changes_only_cli)
    parallelism_default = max(1, int(settings.get("parallelism") or 4))

    remotes = merged.get("remotes") if isinstance(merged.get("remotes"), dict) else {}
    namespaces_raw = merged.get("namespaces")
    namespaces_list = namespaces_raw if isinstance(namespaces_raw, list) else []
    layout_t = str(merged.get("layout") or "{remote}/{namespace}/{repo}")

    targets: dict[str, WorkspaceRepo] = {}
    cred_path = credentials_path_for_config(config_path)

    for entry in _collect_explicit_repos(merged, remotes):
        targets[entry.subject] = entry

    def mk_client(
        remote_name_local: str,
        rcfg_local: dict[str, Any],
    ) -> GithubRemoteClient | GitlabRemoteClient:
        tok, _src = resolve_token(
            remote_name_local,
            rcfg_local,
            cli_token=None,
            credentials_file=cred_path,
        )
        if not isinstance(tok, str) or not tok.strip():
            raise RuntimeError("token unresolved for remote")
        if client_factory is not None:
            return client_factory(remote_name_local, rcfg_local, tok)
        kind = rcfg_local.get("kind")
        base_u = str(rcfg_local.get("base_url") or "").strip()
        if kind == "gitlab":
            return GitlabRemoteClient(base_url=base_u, token=tok)
        return GithubRemoteClient(base_url=base_u or None, token=tok)

    now = time.time()
    for ns_cfg in _namespaces_filtered(namespaces_list, namespace_filter):
        remote_name_any = ns_cfg.get("remote")
        if not isinstance(remote_name_any, str) or not remote_name_any.strip():
            records.append(StatusRecord("ERROR", "namespaces[].remote", "missing remote name"))
            continue
        remote_name = remote_name_any.strip()
        rcfg_any = remotes.get(remote_name)
        if not isinstance(rcfg_any, dict):
            records.append(
                StatusRecord(
                    "ERROR",
                    f"discovery.{remote_name}",
                    f"unknown remote {remote_name}",
                ),
            )
            continue
        rcfg = rcfg_any

        ns_name_any = ns_cfg.get("name")
        if not isinstance(ns_name_any, str) or not ns_name_any.strip():
            records.append(StatusRecord("ERROR", "namespaces[].name", "missing namespace name"))
            continue
        ns_name = ns_name_any.strip()

        clone_protocol_setting = str(rcfg.get("clone_protocol") or "ssh").strip().lower()
        inc_subgroups = bool(ns_cfg.get("include_subgroups", True))

        raw_include = ns_cfg.get("include")
        include_patterns = (
            raw_include if isinstance(raw_include, list) and raw_include else ["**/*"]
        )
        include_patterns = [x for x in include_patterns if isinstance(x, str)] or ["**/*"]

        raw_exclude = ns_cfg.get("exclude")
        excludes = (
            [x for x in raw_exclude if isinstance(x, str)] if isinstance(raw_exclude, list) else []
        )

        visibility_allowlist = ns_cfg.get("visibility")
        if visibility_allowlist is not None and not isinstance(visibility_allowlist, list):
            visibility_allowlist = None

        subj_discovery = f"discovery.{remote_name}:{ns_name}"
        cache_path = discovery_cache_path(cache_root, remote_name, ns_name)
        fetched_at_epoch: float | None = None
        cache_payload_any = read_discovery_cache(cache_path)
        if isinstance(cache_payload_any, dict):
            fat = cache_payload_any.get("fetched_at_epoch")
            if isinstance(fat, int | float):
                fetched_at_epoch = float(fat)

        stale = _cache_needs_refresh(
            refresh_cli=refresh_discovery,
            fetched_at_epoch=fetched_at_epoch,
            now=now,
            ttl_eff=cache_ttl_eff,
        )

        if stale:
            try:
                client = mk_client(remote_name, rcfg)
                if rcfg.get("kind") == "gitlab":
                    assert isinstance(client, GitlabRemoteClient)
                    raw_list = client.list_group_projects(ns_name, include_subgroups=inc_subgroups)
                elif rcfg.get("kind") == "github":
                    assert isinstance(client, GithubRemoteClient)
                    raw_list = client.list_namespace_repositories(ns_name)
                else:
                    records.append(StatusRecord("ERROR", subj_discovery, "unsupported remote kind"))
                    continue

                filtered = filter_listed_projects(
                    raw_list,
                    namespace_root=ns_name,
                    include_patterns=include_patterns,
                    exclude_patterns=excludes,
                    visibility_allowlist=visibility_allowlist
                    if visibility_allowlist is None
                    else [str(x) for x in visibility_allowlist if isinstance(x, str)],
                )
                serialized = [p.to_json_dict() for p in raw_list]
                write_discovery_cache(cache_path, now, projects=serialized)
                records.append(
                    StatusRecord(
                        "OK",
                        subj_discovery,
                        f"{len(filtered)} repos after filters (fresh fetch)",
                    ),
                )
                listed_projects = filtered
            except PermissionError as e:
                records.append(StatusRecord("ERROR", subj_discovery, str(e)))
                continue
            except RuntimeError as e:
                records.append(StatusRecord("ERROR", subj_discovery, str(e)))
                continue
            except Exception as e:
                records.append(StatusRecord("ERROR", subj_discovery, str(e)))
                continue
        else:
            projects_raw = cache_payload_projects(cache_payload_any or {})
            raw_list_restore: list[ListedProject] = []
            for item in projects_raw:
                proj = ListedProject.from_json_dict(item)
                if proj is not None:
                    raw_list_restore.append(proj)

            filtered = filter_listed_projects(
                raw_list_restore,
                namespace_root=ns_name,
                include_patterns=include_patterns,
                exclude_patterns=excludes,
                visibility_allowlist=visibility_allowlist
                if visibility_allowlist is None
                else [str(x) for x in visibility_allowlist if isinstance(x, str)],
            )

            fetched_at_cached = fetched_at_epoch or 0.0
            age_s = max(0, int(now - fetched_at_cached))
            records.append(
                StatusRecord(
                    "OK",
                    subj_discovery,
                    f"{len(filtered)} repos after filters (cache age {age_s}s)",
                ),
            )
            listed_projects = filtered

        kind_fg: ForgeKind = "gitlab" if rcfg.get("kind") == "gitlab" else "github"
        for lp in listed_projects:
            mapped = _listed_to_workspace_repo(
                lp=lp,
                remote_name=remote_name,
                forge_kind=kind_fg,
                namespace_name=ns_name,
                layout_template=layout_t,
                clone_protocol=clone_protocol_setting,
            )
            if mapped is None:
                continue
            targets[mapped.subject] = mapped

    repos_sorted = tuple(sorted(targets.values(), key=lambda z: z.subject.lower()))
    if not repos_sorted:
        records.append(StatusRecord("OK", "local.targets", "no repositories matched configuration"))

    ctx = LocalWorkspaceContext(
        workspace_root=ws_root,
        cache_root=cache_root,
        targets=repos_sorted,
        remotes=remotes,
        credentials_path=cred_path,
        changes_only_mode=changes_only_mode,
        parallelism_default=parallelism_default,
    )
    return records, ctx


def run_local_status(
    config_path: Path,
    *,
    namespace_filter: Sequence[str],
    parallelism: int | None,
    refresh_discovery: bool,
    changes_only_cli: bool,
    client_factory: Callable[[str, dict[str, Any], str], GithubRemoteClient | GitlabRemoteClient]
    | None = None,
) -> LocalStatusResult:
    """
    Read-only workspace report: ahead/behind, dirty, clone presence per configured repo.

    Does not fetch, clone, or merge.
    """
    prelude_list, ctx = _prepare_local_workspace(
        config_path,
        namespace_filter=namespace_filter,
        refresh_discovery=refresh_discovery,
        changes_only_cli=changes_only_cli,
        client_factory=client_factory,
    )
    prelude = tuple(prelude_list)
    if ctx is None:
        return LocalStatusResult(
            prelude=prelude,
            repo_lines=(),
            snapshots=(),
            workspace_root=Path("."),
        )

    if not ctx.targets:
        if ctx.changes_only_mode:
            filtered = [r for r in prelude if r.level != "OK"]
        else:
            filtered = list(prelude)
        return LocalStatusResult(
            prelude=tuple(filtered),
            repo_lines=(),
            snapshots=(),
            workspace_root=ctx.workspace_root,
        )

    parallelism_n = parallelism if parallelism is not None else ctx.parallelism_default

    def process_one(repo: WorkspaceRepo) -> tuple[RepoStatusSnapshot, tuple[StatusRecord, ...]]:
        repo_dir = ctx.workspace_root.joinpath(*Path(repo.relative_posix).parts)
        facts = probe_worktree(repo_dir)
        snap, lines = summarize_local_repo_status(
            subject=repo.subject,
            relative_path=repo.relative_posix,
            facts=facts,
            expected_ssh_url=repo.ssh_clone,
            expected_https_url=repo.https_clone,
        )
        return snap, lines

    snapshots_ordered: list[RepoStatusSnapshot] = []
    lines_ordered: list[StatusRecord] = []

    if parallelism_n <= 1:
        for ent in ctx.targets:
            snap, lines = process_one(ent)
            snapshots_ordered.append(snap)
            lines_ordered.extend(lines)
    else:
        snap_by_subject: dict[str, RepoStatusSnapshot] = {}
        lines_by_subject: dict[str, tuple[StatusRecord, ...]] = {}
        with ThreadPoolExecutor(max_workers=parallelism_n) as executor:
            future_map = {executor.submit(process_one, r): r for r in ctx.targets}
            for fut in as_completed(future_map):
                repo_ent = future_map[fut]
                try:
                    snap, lines = fut.result()
                except Exception as exc:  # pragma: no cover - defensive
                    snap_by_subject[repo_ent.subject] = RepoStatusSnapshot(
                        subject=repo_ent.subject,
                        relative_path=repo_ent.relative_posix,
                        level="ERROR",
                        detail=str(exc),
                        branch="",
                        upstream=None,
                        ahead=0,
                        behind=0,
                        dirty=False,
                        detached=False,
                        path_missing=False,
                        not_git_directory=False,
                        submodule_dotfile=False,
                        origin_url=None,
                        origin_drift=False,
                        last_fetch_epoch=None,
                    )
                    lines_by_subject[repo_ent.subject] = (
                        StatusRecord("ERROR", repo_ent.subject, str(exc)),
                    )
                else:
                    snap_by_subject[repo_ent.subject] = snap
                    lines_by_subject[repo_ent.subject] = lines

        for ent in ctx.targets:
            snapshots_ordered.append(snap_by_subject[ent.subject])
            lines_ordered.extend(lines_by_subject.get(ent.subject, ()))

    repo_lines = tuple(lines_ordered)
    if ctx.changes_only_mode:
        prelude_out = tuple(r for r in prelude if r.level != "OK")
        repo_lines = tuple(r for r in repo_lines if r.level != "OK")
    else:
        prelude_out = prelude

    return LocalStatusResult(
        prelude=prelude_out,
        repo_lines=repo_lines,
        snapshots=tuple(snapshots_ordered),
        workspace_root=ctx.workspace_root,
    )


def run_local(
    config_path: Path,
    *,
    namespace_filter: Sequence[str],
    write: bool,
    parallelism: int | None,
    refresh_discovery: bool,
    strategy: SyncStrategy,
    changes_only_cli: bool,
    client_factory: Callable[[str, dict[str, Any], str], GithubRemoteClient | GitlabRemoteClient]
    | None = None,
) -> list[StatusRecord]:
    """
    Execute ``local plan`` / ``local sync``: discover namespaces, plan, mutate.

    ``client_factory`` is reserved for dependency injection during tests (remote
    name, remote YAML mapping, resolved token → client).
    """
    prelude, ctx = _prepare_local_workspace(
        config_path,
        namespace_filter=namespace_filter,
        refresh_discovery=refresh_discovery,
        changes_only_cli=changes_only_cli,
        client_factory=client_factory,
    )
    records: list[StatusRecord] = list(prelude)
    if ctx is None:
        return records

    if not ctx.targets:
        return [r for r in records if r.level != "OK"] if ctx.changes_only_mode else records

    parallelism_n = parallelism if parallelism is not None else ctx.parallelism_default

    ws_root = ctx.workspace_root
    remotes = ctx.remotes
    cred_path = ctx.credentials_path
    repos_sorted = list(ctx.targets)

    def resolve_clone_url(repo: WorkspaceRepo) -> str:
        rc_any_inner = remotes.get(repo.remote_name)
        tok_inner: str | None = None
        if isinstance(rc_any_inner, dict):
            try:
                tt, _s = resolve_token(
                    repo.remote_name,
                    rc_any_inner,
                    cli_token=None,
                    credentials_file=cred_path,
                )
                tok_inner = tt if isinstance(tt, str) and tt.strip() else None
            except PermissionError:
                tok_inner = None
        exe = authenticated_clone_url(
            forge_kind=repo.forge_kind,
            clone_protocol=repo.clone_protocol,
            ssh_url=repo.ssh_clone,
            https_url=repo.https_clone,
            token=tok_inner,
        )
        return exe

    def process_one(repo: WorkspaceRepo) -> list[StatusRecord]:
        rows: list[StatusRecord] = []
        repo_dir = ws_root.joinpath(*Path(repo.relative_posix).parts)
        rc_any = remotes.get(repo.remote_name)
        if not isinstance(rc_any, dict):
            rows.append(StatusRecord("ERROR", repo.subject, f"unknown remote {repo.remote_name!r}"))
            return rows

        exec_url = resolve_clone_url(repo)

        facts_probe = probe_worktree(repo_dir)
        if facts_probe.path_missing:
            try:
                detail = f"clone via {repo.clone_protocol} → {repo_dir.relative_to(ws_root)}"
            except ValueError:
                detail = f"clone via {repo.clone_protocol} → {repo_dir}"
            if not write:
                rows.append(StatusRecord("WOULD UPDATE", repo.subject, detail))
                return rows
            code_clone, stdout_c, stderr_c = git_clone(exec_url, repo_dir)
            if code_clone != 0:
                rows.append(
                    StatusRecord("ERROR", repo.subject, stderr_c or stdout_c or "git clone failed"),
                )
                return rows
            rows.append(StatusRecord("UPDATED", repo.subject, "cloned"))
            return rows

        plan = plan_local_sync(
            subject=repo.subject,
            facts=facts_probe,
            expected_ssh_url=repo.ssh_clone,
            expected_https_url=repo.https_clone,
            strategy=strategy,
        )
        rows.extend(plan.records)

        if plan.should_clone:
            rows.append(
                StatusRecord(
                    "ERROR",
                    repo.subject,
                    "internal planner error on existing path",
                ),
            )
            return rows

        if not plan.should_fetch:
            return rows

        pull_desc = "fetch + merge --ff-only" if strategy == "ff-only" else "fetch only"
        if not write:
            rows.append(StatusRecord("WOULD UPDATE", repo.subject, pull_desc))
            return rows
        fc, fout, ferr = git_fetch(repo_dir)
        if fc != 0:
            rows.append(StatusRecord("ERROR", repo.subject, ferr or fout or "git fetch failed"))
            return rows

        verbs = ["fetch"]
        if plan.should_merge_ff and strategy == "ff-only":
            mc, _, merr = git_merge_ff_only(repo_dir)
            if mc != 0:
                rows.append(StatusRecord("ERROR", repo.subject, merr or "merge --ff-only failed"))
                return rows
            verbs.append("merge_ff")

        rows.append(StatusRecord("UPDATED", repo.subject, ", ".join(verbs)))
        return rows

    if parallelism_n <= 1:
        merged_rows_ordered: list[StatusRecord] = []
        for ent in repos_sorted:
            merged_rows_ordered.extend(process_one(ent))
        records.extend(merged_rows_ordered)
    else:
        batch_lists: dict[str, list[StatusRecord]] = {}
        with ThreadPoolExecutor(max_workers=parallelism_n) as executor:
            future_map = {executor.submit(process_one, r): r for r in repos_sorted}
            for fut in as_completed(future_map):
                repo_ent = future_map[fut]
                try:
                    batch_lists[repo_ent.subject] = fut.result()
                except Exception as exc:  # pragma: no cover - defensive
                    batch_lists[repo_ent.subject] = [
                        StatusRecord("ERROR", repo_ent.subject, str(exc)),
                    ]

        merged_rows_ordered = []
        for ent in repos_sorted:
            merged_rows_ordered.extend(batch_lists.get(ent.subject, []))
        records.extend(merged_rows_ordered)

    if ctx.changes_only_mode:
        return [rec for rec in records if rec.level != "OK"]
    return records
