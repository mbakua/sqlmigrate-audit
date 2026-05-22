"""Tests for sqlmigrate_audit.cli module."""

import json
import os
import tempfile

import pytest

from sqlmigrate_audit.cli import build_parser, main
from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.exporter import export_registry
from sqlmigrate_audit.registry import MigrationRegistry


@pytest.fixture
def json_registry_file():
    record = MigrationRecord(
        migration_id="0001_initial",
        description="Create users table",
        sql="CREATE TABLE users (id SERIAL PRIMARY KEY);",
        rollback_sql="DROP TABLE users;",
        status=MigrationStatus.APPLIED,
    )
    registry = MigrationRegistry()
    registry.register(record)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        path = f.name
    export_registry(registry, path, "json")
    yield path
    os.unlink(path)


def test_validate_valid_registry(json_registry_file):
    exit_code = main(["validate", json_registry_file, "--format", "json"])
    assert exit_code == 0


def test_validate_invalid_registry(tmp_path):
    bad_data = json.dumps([{"migration_id": "", "description": "", "sql": "SELECT 1;",
                             "status": "pending", "rollback_sql": None,
                             "applied_at": None, "rolled_back_at": None, "tags": []}])
    bad_file = tmp_path / "bad.json"
    bad_file.write_text(bad_data)
    exit_code = main(["validate", str(bad_file), "--format", "json"])
    assert exit_code == 2


def test_validate_missing_file():
    exit_code = main(["validate", "/nonexistent/path/registry.json"])
    assert exit_code == 1


def test_export_json_to_csv(json_registry_file, tmp_path):
    out_file = str(tmp_path / "out.csv")
    exit_code = main(["export", json_registry_file, out_file,
                      "--input-format", "json", "--output-format", "csv"])
    assert exit_code == 0
    assert os.path.exists(out_file)


def test_export_missing_input(tmp_path):
    out_file = str(tmp_path / "out.csv")
    exit_code = main(["export", "/no/such/file.json", out_file])
    assert exit_code == 1


def test_no_command_prints_help(capsys):
    exit_code = main([])
    assert exit_code == 0


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser.prog == "sqlmigrate-audit"
