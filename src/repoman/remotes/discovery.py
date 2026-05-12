"""Pure discovery helpers — glob filters and visibility for namespace scans."""

from __future__ import annotations

from collections.abc import Sequence
from fnmatch import fnmatchcase

from repoman.remotes.catalog import ListedProject


def relative_repo_path_under_namespace(full_path: str, namespace_root: str) -> str | None:
    """
    Strip the configured namespace/group root prefix for Glob matching.

    ``full_path`` is the forge path (`path_with_namespace` / `full_name`).
    ``namespace_root`` is the namespaces[].name entry (no trailing slashes required).
    """
    fp = "/".join(p.strip() for p in full_path.split("/") if p.strip())
    nr = "/".join(p.strip() for p in namespace_root.split("/") if p.strip())
    if fp == nr:
        return ""
    prefix = nr + "/" if nr else ""
    if prefix and fp.startswith(prefix):
        return fp[len(prefix) :]
    if not prefix:
        return fp
    return None


def normalize_visibility_slug(value: str) -> str:
    """Normalize visibility labels for comparisons."""
    return value.strip().lower()


def passes_visibility(repo: ListedProject, allowed: Sequence[str] | None) -> bool:
    """Allow all when ``allowed`` is empty or unset."""
    if not allowed:
        return True
    vis = normalize_visibility_slug(repo.visibility)
    allowed_low = [normalize_visibility_slug(x) for x in allowed]
    return vis in allowed_low


def _glob_matches(relative_repo_path: str, pattern: str) -> bool:
    """Interpret ``fnmatch`` plus common ``**/`` sentinel patterns."""
    stripped = pattern.strip()
    # Design default ``**/*`` means "everything under namespace root", including repo
    # names without an extra subdirectory (Python's fnmatch would otherwise miss them).
    if stripped == "**/*":
        return bool(relative_repo_path.strip())
    return fnmatchcase(relative_repo_path, pattern)


def passes_path_globs(
    relative_repo_path: str | None,
    *,
    include_patterns: Sequence[str],
    exclude_patterns: Sequence[str],
) -> bool:
    """
    Apply include/exclude globs against the repository path under the namespace.

    Returns False when relative path is missing (outside namespace hierarchy).
    """
    if relative_repo_path is None:
        return False
    if not include_patterns:
        matched = True
    else:
        matched = any(_glob_matches(relative_repo_path, pattern) for pattern in include_patterns)
        if relative_repo_path == "":
            matched = matched or any(_glob_matches("", pattern) for pattern in include_patterns)
    if not matched:
        return False
    excluded = any(
        _glob_matches(relative_repo_path, pattern)
        or (relative_repo_path == "" and _glob_matches("", pattern))
        for pattern in exclude_patterns
    )
    return not excluded


def filter_listed_projects(
    projects: Sequence[ListedProject],
    *,
    namespace_root: str,
    include_patterns: Sequence[str],
    exclude_patterns: Sequence[str],
    visibility_allowlist: Sequence[str] | None,
) -> list[ListedProject]:
    """Apply namespace-relative filters to a forge listing."""
    out: list[ListedProject] = []
    for p in projects:
        if p.archived:
            continue
        rel = relative_repo_path_under_namespace(p.path_with_namespace, namespace_root)
        if not passes_path_globs(
            rel, include_patterns=include_patterns, exclude_patterns=exclude_patterns
        ):
            continue
        if not passes_visibility(p, visibility_allowlist):
            continue
        out.append(p)
    return sorted(out, key=lambda x: x.path_with_namespace.lower())
