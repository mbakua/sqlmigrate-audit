"""Integration tests for cli_scheduler sub-commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from sqlmigrate_audit.cli_scheduler import build_scheduler_subparser
from sqlmigrate_audit.exporter import export_registry
from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd")
    build_scheduler_subparser(sp)
    return p


@pytest.fixture()
def registry_file(tmp_path: Path) -> Path:
    reg = MigrationRegistry()
    reg.register(MigrationRecord(
        migration_id="m001",
        description="first migration",
        status=MigrationStatus.PENDING,
    ))
    reg.register(MigrationRecord(
        migration_id="m002",
        description="second migration",
        status=MigrationStatus.PENDING,
    ))
    fpath = tmp_path / "registry.json"
    export_registry(reg, str(fpath), fmt="json")
    return fpath


def _run(parser: argparse.ArgumentParser, args_list: list) -> None:
    args = parser.parse_args(args_list)
    args.func(args)


def test_set_due_persists(registry_file: Path) -> None:
    parser = _build_parser()
    _run(parser, ["schedule", "set-due", str(registry_file), "m001", "2024-09-01"])
    data = json.loads(registry_file.read_text())
    tags = next(r["tags"] for r in data if r["migration_id"] == "m001")
    assert "due:2024-09-01" in tags


def test_set_priority_persists(registry_file: Path) -> None:
    parser = _build_parser()
    _run(parser, ["schedule", "set-priority", str(registry_file), "m002", "3"])
    data = json.loads(registry_file.read_text())
    tags = next(r["tags"] for r in data if r["migration_id"] == "m002")
    assert "priority:3" in tags


def test_show_schedule_prints_output(registry_file: Path, capsys) -> None:
    parser = _build_parser()
    _run(parser, ["schedule", "show", str(registry_file)])
    out = capsys.readouterr().out
    assert "Migration Schedule" in out
    assert "m001" in out


def test_set_due_missing_migration_exits(registry_file: Path) -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit):
        _run(parser, ["schedule", "set-due", str(registry_file), "nonexistent", "2024-01-01"])


def test_set_due_bad_date_exits(registry_file: Path) -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit):
        _run(parser, ["schedule", "set-due", str(registry_file), "m001", "not-a-date"])


def test_show_schedule_missing_file_exits(tmp_path: Path) -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit):
        _run(parser, ["schedule", "show", str(tmp_path / "missing.json")])
