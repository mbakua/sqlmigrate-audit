"""Tests for sqlmigrate_audit.cli — including the new 'report' subcommand."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from sqlmigrate_audit.cli import main
from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.exporter import export_registry
from sqlmigrate_audit.registry import MigrationRegistry


@pytest.fixture()
def json_registry_file(tmp_path):
    reg = MigrationRegistry()
    reg.register(
        MigrationRecord(
            migration_id="0001_init",
            description="Initial schema",
            status=MigrationStatus.APPLIED,
            applied_at="2024-01-01T00:00:00",
            rollback_sql="DROP TABLE foo;",
        )
    )
    path = str(tmp_path / "registry.json")
    export_registry(reg, path, fmt="json")
    return path


def test_validate_valid_registry(json_registry_file):
    result = main(["validate", json_registry_file])
    assert result == 0


def test_validate_invalid_registry(tmp_path):
    reg = MigrationRegistry()
    reg.register(
        MigrationRecord(
            migration_id="",
            description="",
            status=MigrationStatus.APPLIED,
        )
    )
    path = str(tmp_path / "bad.json")
    export_registry(reg, path, fmt="json")
    result = main(["validate", path])
    assert result == 1


def test_validate_missing_file():
    result = main(["validate", "/nonexistent/path/registry.json"])
    assert result == 2


def test_export_json_to_csv(json_registry_file, tmp_path):
    out = str(tmp_path / "out.csv")
    result = main(["export", json_registry_file, out, "--format", "csv"])
    assert result == 0
    assert os.path.exists(out)


def test_export_missing_input(tmp_path):
    out = str(tmp_path / "out.csv")
    result = main(["export", "/no/such/file.json", out])
    assert result == 2


def test_report_command_output(json_registry_file, capsys):
    result = main(["report", json_registry_file])
    assert result == 0
    captured = capsys.readouterr()
    assert "0001_init" in captured.out
    assert "APPLIED" in captured.out
    assert "Migration Report" in captured.out


def test_report_command_custom_title(json_registry_file, capsys):
    result = main(["report", json_registry_file, "--title", "My Custom Report"])
    assert result == 0
    captured = capsys.readouterr()
    assert "My Custom Report" in captured.out


def test_report_missing_file(capsys):
    result = main(["report", "/no/such/file.json"])
    assert result == 2
