"""Tests for layout placeholders and rendering."""

from pathlib import Path

import pytest

from repoman.paths import (
    credentials_path_for_config,
    default_config_dir,
    extract_layout_placeholders,
    render_layout,
)


def test_extract_placeholders_unknown() -> None:
    assert extract_layout_placeholders("{remote}/{repo}") == {"remote", "repo"}


def test_render_layout() -> None:
    out = render_layout(
        "{remote}/{namespace}/{repo}",
        remote="gitlab",
        namespace="grp",
        subgroup="",
        repo="proj",
    )
    assert out == "gitlab/grp/proj"


def test_credentials_path_next_to_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("REPOMAN_HOME", raising=False)
    cfg = tmp_path / "nested" / "repoman.yaml"
    assert credentials_path_for_config(cfg) == tmp_path / "nested" / "credentials.toml"


def test_default_config_dir_respects_repoman_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("REPOMAN_HOME", str(tmp_path / "rh"))
    assert default_config_dir() == tmp_path / "rh"
