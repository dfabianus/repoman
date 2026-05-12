"""Shared models for forge repository listings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ListedProject:
    """One repository returned from GitLab/GitHub discovery (before namespace filters)."""

    path_with_namespace: str
    ssh_url_to_repo: str
    http_url_to_repo: str
    archived: bool
    visibility: str
    default_branch: str | None

    def to_json_dict(self) -> dict[str, Any]:
        """Serialize for discovery cache payloads."""
        return {
            "path_with_namespace": self.path_with_namespace,
            "ssh_url_to_repo": self.ssh_url_to_repo,
            "http_url_to_repo": self.http_url_to_repo,
            "archived": self.archived,
            "visibility": self.visibility,
            "default_branch": self.default_branch,
        }

    @staticmethod
    def from_json_dict(data: dict[str, Any]) -> ListedProject | None:
        """Restore from cache; returns None when required keys are invalid."""
        try:
            pn = data["path_with_namespace"]
            if not isinstance(pn, str) or not pn.strip():
                return None
            return ListedProject(
                path_with_namespace=pn.strip(),
                ssh_url_to_repo=str(data.get("ssh_url_to_repo") or ""),
                http_url_to_repo=str(data.get("http_url_to_repo") or ""),
                archived=bool(data.get("archived")),
                visibility=str(data.get("visibility") or "unknown"),
                default_branch=(db if isinstance(db := data.get("default_branch"), str) else None),
            )
        except (KeyError, TypeError, ValueError):
            return None
