"""Tests for config bootstrap and dotted-key updates."""

from pathlib import Path

import pytest
import yaml

from repoman.config import SCHEMA_VERSION
from repoman.config_setup import (
    coerce_config_value,
    get_nested,
    init_config_file,
    parse_config_key,
    plan_config_set,
    set_nested,
    unset_nested,
    write_config_file,
)


def test_parse_config_key_with_index() -> None:
    assert parse_config_key("namespaces.0.name") == ["namespaces", 0, "name"]


def test_coerce_config_value_types() -> None:
    assert coerce_config_value("true") is True
    assert coerce_config_value("42") == 42
    assert coerce_config_value("plain") == "plain"


def test_set_and_unset_nested() -> None:
    data = {"paths": {"workspace_root": "~/old"}}
    updated = set_nested(data, parse_config_key("paths.workspace_root"), "~/new")
    assert updated["paths"]["workspace_root"] == "~/new"
    assert data["paths"]["workspace_root"] == "~/old"

    removed = unset_nested(updated, parse_config_key("paths.workspace_root"))
    assert "workspace_root" not in removed["paths"]


def test_plan_config_set_preview() -> None:
    data = {"version": SCHEMA_VERSION, "paths": {}}
    new_data, rec = plan_config_set(
        data,
        "paths.workspace_root",
        "~/repositories",
        unset=False,
    )
    assert rec.level == "WOULD UPDATE"
    assert new_data["paths"]["workspace_root"] == "~/repositories"


def test_init_config_file_refuses_existing(tmp_path: Path) -> None:
    target = tmp_path / "repoman.yaml"
    target.write_text("version: 1\n", encoding="utf-8")
    records = init_config_file(target, force=False)
    assert any(r.level == "ERROR" for r in records)


def test_init_config_file_creates(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "repoman.yaml"
    records = init_config_file(target, force=False)
    assert target.is_file()
    assert any(r.level == "UPDATED" for r in records)
    loaded = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert loaded["version"] == SCHEMA_VERSION


def test_write_config_file_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "repoman.yaml"
    data = {"version": SCHEMA_VERSION, "paths": {"workspace_root": "~/x"}}
    write_config_file(path, data)
    assert yaml.safe_load(path.read_text(encoding="utf-8"))["paths"]["workspace_root"] == "~/x"


def test_get_nested_missing_raises() -> None:
    with pytest.raises(KeyError):
        get_nested({"a": {}}, parse_config_key("a.b"))
