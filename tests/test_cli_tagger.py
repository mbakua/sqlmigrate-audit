"""Tests for the tag-related CLI sub-commands in cli_tagger."""

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone
from argparse import Namespace

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.exporter import export_registry
from sqlmigrate_audit.cli_tagger import _cmd_add_tag, _cmd_remove_tag, _cmd_list_tags


@pytest.fixture
def registry_file(tmp_path):
    reg = MigrationRegistry()
    reg.register(MigrationRecord(
        migration_id="m001",
        description="First migration",
        status=MigrationStatus.APPLIED,
        tags=["core"],
    ))
    reg.register(MigrationRecord(
        migration_id="m002",
        description="Second migration",
        status=MigrationStatus.PENDING,
        tags=["core", "v2"],
    ))
    out = tmp_path / "registry.json"
    export_registry(reg, str(out), fmt="json")
    return str(out)


def test_add_tag_persists(registry_file):
    args = Namespace(file=registry_file, format="json", migration_id="m001", tag="hotfix")
    _cmd_add_tag(args)
    data = json.loads(Path(registry_file).read_text())
    m001 = next(r for r in data if r["migration_id"] == "m001")
    assert "hotfix" in m001["tags"]


def test_add_tag_no_duplicate(registry_file):
    args = Namespace(file=registry_file, format="json", migration_id="m001", tag="core")
    _cmd_add_tag(args)
    data = json.loads(Path(registry_file).read_text())
    m001 = next(r for r in data if r["migration_id"] == "m001")
    assert m001["tags"].count("core") == 1


def test_add_tag_missing_migration_prints_error(registry_file, capsys):
    args = Namespace(file=registry_file, format="json", migration_id="m999", tag="x")
    _cmd_add_tag(args)
    captured = capsys.readouterr()
    assert "ERROR" in captured.out


def test_remove_tag_persists(registry_file):
    args = Namespace(file=registry_file, format="json", migration_id="m002", tag="v2")
    _cmd_remove_tag(args)
    data = json.loads(Path(registry_file).read_text())
    m002 = next(r for r in data if r["migration_id"] == "m002")
    assert "v2" not in m002["tags"]


def test_remove_tag_missing_migration_prints_error(registry_file, capsys):
    args = Namespace(file=registry_file, format="json", migration_id="m999", tag="x")
    _cmd_remove_tag(args)
    captured = capsys.readouterr()
    assert "ERROR" in captured.out


def test_list_tags_output(registry_file, capsys):
    args = Namespace(file=registry_file, format="json")
    _cmd_list_tags(args)
    captured = capsys.readouterr()
    assert "core" in captured.out
    assert "v2" in captured.out


def test_list_tags_empty_registry(tmp_path, capsys):
    empty = MigrationRegistry()
    out = tmp_path / "empty.json"
    export_registry(empty, str(out), fmt="json")
    args = Namespace(file=str(out), format="json")
    _cmd_list_tags(args)
    captured = capsys.readouterr()
    assert "No tags" in captured.out
