"""YAML config loading, defaults, and validation (pure)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from repoman.paths import LAYOUT_PLACEHOLDERS, extract_layout_placeholders
from repoman.status import StatusRecord

SCHEMA_VERSION = 1

DEFAULT_SETTINGS: dict[str, Any] = {
    "default_action": "preview",
    "log_level": "info",
    "parallelism": 4,
    "changes_only": False,
    "discovery_cache_ttl": 900,
}

DEFAULT_PATHS: dict[str, Any] = {
    "workspace_root": "~/repositories",
    "cache_root": "~/.cache/repoman",
    "state_root": "~/.local/state/repoman",
}

DEFAULT_LAYOUT = "{remote}/{namespace}/{repo}"

DEFAULT_REMOTE_FIELDS: dict[str, Any] = {
    "clone_protocol": "ssh",
}


def load_yaml(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    data = yaml.safe_load(raw)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("top level must be a mapping")
    return data


def deep_merge_defaults(dst: dict[str, Any], defaults: dict[str, Any]) -> None:
    for k, v in defaults.items():
        if k not in dst:
            dst[k] = v


def apply_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with defaults merged (does not mutate input)."""
    out = dict(data)
    deep_merge_defaults(out, {"version": SCHEMA_VERSION})
    settings = dict(out.get("settings") or {})
    deep_merge_defaults(settings, DEFAULT_SETTINGS)
    out["settings"] = settings

    paths = dict(out.get("paths") or {})
    deep_merge_defaults(paths, DEFAULT_PATHS)
    out["paths"] = paths

    if not out.get("layout"):
        out["layout"] = DEFAULT_LAYOUT

    remotes = dict(out.get("remotes") or {})
    for name, cfg in remotes.items():
        if not isinstance(cfg, dict):
            continue
        merged = dict(cfg)
        deep_merge_defaults(merged, DEFAULT_REMOTE_FIELDS)
        remotes[name] = merged
    out["remotes"] = remotes

    if out.get("namespaces") is None:
        out["namespaces"] = []
    if out.get("repos") is None:
        out["repos"] = []
    if out.get("mirrors") is None:
        out["mirrors"] = []

    return out


def validate(data: dict[str, Any]) -> list[StatusRecord]:
    """Validate merged config; emits StatusRecord rows (ERROR/WARN/OK)."""
    records: list[StatusRecord] = []

    version = data.get("version")
    if version != SCHEMA_VERSION:
        records.append(
            StatusRecord(
                "ERROR",
                "config.version",
                f"expected {SCHEMA_VERSION}, got {version!r}",
            )
        )
        return records
    records.append(StatusRecord("OK", "config.version", str(SCHEMA_VERSION)))

    remotes = data.get("remotes")
    if not isinstance(remotes, dict):
        records.append(StatusRecord("ERROR", "remotes", "must be a mapping"))
        return records

    for rname, rcfg in remotes.items():
        subj = f"remotes.{rname}"
        if not isinstance(rcfg, dict):
            records.append(StatusRecord("ERROR", subj, "must be a mapping"))
            continue
        kind = rcfg.get("kind")
        if kind not in ("gitlab", "github"):
            records.append(StatusRecord("ERROR", subj + ".kind", f"invalid kind {kind!r}"))
            continue
        base_url = rcfg.get("base_url")
        if not isinstance(base_url, str) or not base_url.strip():
            records.append(StatusRecord("ERROR", subj + ".base_url", "must be non-empty string"))
            continue
        cp = rcfg.get("clone_protocol", DEFAULT_REMOTE_FIELDS["clone_protocol"])
        if cp not in ("https", "ssh"):
            records.append(StatusRecord("ERROR", subj + ".clone_protocol", f"invalid {cp!r}"))
            continue
        has_token_env = isinstance(rcfg.get("token_env"), str) and rcfg["token_env"].strip()
        has_cred = (
            isinstance(rcfg.get("token_credentials"), str) and rcfg["token_credentials"].strip()
        )
        if not has_token_env and not has_cred:
            records.append(
                StatusRecord(
                    "WARN",
                    subj + ".token",
                    "neither token_env nor token_credentials — doctor may fail",
                )
            )
        records.append(StatusRecord("OK", subj, f"kind={kind} base_url={base_url.strip()}"))

    layout = data.get("layout", DEFAULT_LAYOUT)
    if not isinstance(layout, str):
        records.append(StatusRecord("ERROR", "layout", "must be a string"))
    else:
        ph = extract_layout_placeholders(layout)
        unknown = ph - LAYOUT_PLACEHOLDERS
        if unknown:
            records.append(
                StatusRecord("ERROR", "layout", f"unknown placeholders: {sorted(unknown)}")
            )
        else:
            records.append(StatusRecord("OK", "layout", layout))

    remote_names = set(remotes.keys())

    def ensure_remote_ref(label: str, name: Any) -> bool:
        if not isinstance(name, str) or not name.strip():
            records.append(StatusRecord("ERROR", label, "remote must be non-empty string"))
            return False
        if name not in remote_names:
            records.append(StatusRecord("ERROR", label, f"unknown remote {name!r}"))
            return False
        return True

    namespaces = data.get("namespaces")
    if not isinstance(namespaces, list):
        records.append(StatusRecord("ERROR", "namespaces", "must be a list"))
    else:
        for i, ns in enumerate(namespaces):
            pref = f"namespaces[{i}]"
            if not isinstance(ns, dict):
                records.append(StatusRecord("ERROR", pref, "must be a mapping"))
                continue
            if not ensure_remote_ref(pref + ".remote", ns.get("remote")):
                continue
            n = ns.get("name")
            if not isinstance(n, str) or not n.strip():
                records.append(StatusRecord("ERROR", pref + ".name", "must be non-empty string"))

    repos = data.get("repos")
    if not isinstance(repos, list):
        records.append(StatusRecord("ERROR", "repos", "must be a list"))
    else:
        for i, repo in enumerate(repos):
            pref = f"repos[{i}]"
            if not isinstance(repo, dict):
                records.append(StatusRecord("ERROR", pref, "must be a mapping"))
                continue
            src = repo.get("source")
            if not isinstance(src, dict):
                records.append(StatusRecord("ERROR", pref + ".source", "must be a mapping"))
                continue
            if not ensure_remote_ref(pref + ".source.remote", src.get("remote")):
                continue
            p = src.get("path")
            if not isinstance(p, str) or not p.strip():
                records.append(StatusRecord("ERROR", pref + ".source.path", "required"))

    mirrors = data.get("mirrors")
    mirror_ids: dict[str, str] = {}
    if not isinstance(mirrors, list):
        records.append(StatusRecord("ERROR", "mirrors", "must be a list"))
    else:
        for i, m in enumerate(mirrors):
            pref = f"mirrors[{i}]"
            if not isinstance(m, dict):
                records.append(StatusRecord("ERROR", pref, "must be a mapping"))
                continue
            mid = m.get("id")
            if not isinstance(mid, str) or not mid.strip():
                records.append(StatusRecord("ERROR", pref + ".id", "must be non-empty string"))
            elif mid in mirror_ids:
                records.append(
                    StatusRecord(
                        "ERROR",
                        pref + ".id",
                        f"duplicate mirror id {mid!r} (also at {mirror_ids[mid]})",
                    )
                )
            else:
                mirror_ids[mid] = pref

            src = m.get("source")
            tgt = m.get("target")
            if not isinstance(src, dict) or not isinstance(tgt, dict):
                records.append(
                    StatusRecord("ERROR", pref, "source and target must be mappings"),
                )
                continue
            if not ensure_remote_ref(pref + ".source.remote", src.get("remote")):
                pass
            if not ensure_remote_ref(pref + ".target.remote", tgt.get("remote")):
                pass
            for side, side_obj in ("source", src), ("target", tgt):
                sp = side_obj.get("path")
                label = f"{pref}.{side}.path"
                if not isinstance(sp, str) or not sp.strip():
                    records.append(StatusRecord("ERROR", label, "required"))

            direction = m.get("direction", "push")
            if direction not in ("push", "pull"):
                records.append(StatusRecord("ERROR", pref + ".direction", f"invalid {direction!r}"))

            backend = m.get("backend", "gitlab_remote_mirror")
            src_remote = src.get("remote") if isinstance(src, dict) else None
            src_kind = None
            if isinstance(src_remote, str) and src_remote in remotes:
                sk = remotes[src_remote]
                if isinstance(sk, dict):
                    src_kind = sk.get("kind")

            if backend != "gitlab_remote_mirror":
                records.append(
                    StatusRecord(
                        "ERROR",
                        pref + ".backend",
                        f"MVP only supports gitlab_remote_mirror (got {backend!r})",
                    )
                )
            elif src_kind != "gitlab":
                records.append(
                    StatusRecord(
                        "ERROR",
                        pref + ".backend",
                        "gitlab_remote_mirror requires source remote kind=gitlab",
                    )
                )

    return records
