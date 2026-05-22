"""Tests for sqlmigrate_audit.exporter (file-based export/import)."""

import os

import pytest

from sqlmigrate_audit.exporter import export_registry, import_registry
from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry


@pytest.fixture
def populated_registry():
    reg = MigrationRegistry()
    reg.register(
        MigrationRecord(
            migration_id="0001_initial",
            description="Bootstrap schema",
            status=MigrationStatus.APPLIED,
            rollback_sql="DROP TABLE bootstrap;",
        )
    )
    reg.register(
        MigrationRecord(
            migration_id="0002_add_index",
            description="Add performance index",
            status=MigrationStatus.PENDING,
        )
    )
    return reg


def test_export_json(tmp_path, populated_registry):
    dest = str(tmp_path / "migrations.json")
    path = export_registry(populated_registry, dest, fmt="json")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "0001_initial" in content
    assert "0002_add_index" in content


def test_export_csv(tmp_path, populated_registry):
    dest = str(tmp_path / "migrations.csv")
    path = export_registry(populated_registry, dest, fmt="csv")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "0001_initial" in content


def test_export_invalid_format(tmp_path, populated_registry):
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_registry(populated_registry, str(tmp_path / "out.xml"), fmt="xml")


def test_import_json_roundtrip(tmp_path, populated_registry):
    dest = str(tmp_path / "migrations.json")
    export_registry(populated_registry, dest, fmt="json")

    new_registry = MigrationRegistry()
    count = import_registry(new_registry, dest, fmt="json")
    assert count == 2
    assert new_registry.get("0001_initial") is not None


def test_import_skip_existing(tmp_path, populated_registry):
    dest = str(tmp_path / "migrations.json")
    export_registry(populated_registry, dest, fmt="json")

    # Pre-populate with one record
    new_registry = MigrationRegistry()
    new_registry.register(
        MigrationRecord(migration_id="0001_initial", description="existing")
    )
    count = import_registry(new_registry, dest, fmt="json", overwrite=False)
    # Only 0002 should be imported
    assert count == 1
    assert new_registry.get("0001_initial").description == "existing"


def test_import_overwrite_existing(tmp_path, populated_registry):
    dest = str(tmp_path / "migrations.json")
    export_registry(populated_registry, dest, fmt="json")

    new_registry = MigrationRegistry()
    new_registry.register(
        MigrationRecord(migration_id="0001_initial", description="old description")
    )
    import_registry(new_registry, dest, fmt="json", overwrite=True)
    assert new_registry.get("0001_initial").description == "Bootstrap schema"
