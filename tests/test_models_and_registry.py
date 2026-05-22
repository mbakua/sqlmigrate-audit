"""Tests for MigrationRecord model and MigrationRegistry."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry


@pytest.fixture
def sample_record():
    return MigrationRecord(
        migration_id="0001",
        filename="0001_create_users.sql",
        checksum="abc123",
        description="Create users table",
        rollback_sql="DROP TABLE users;",
        tags=["schema", "users"],
    )


def test_migration_record_defaults(sample_record):
    assert sample_record.status == MigrationStatus.PENDING
    assert sample_record.applied_at is None
    assert sample_record.execution_time_ms is None


def test_migration_record_to_dict(sample_record):
    d = sample_record.to_dict()
    assert d["migration_id"] == "0001"
    assert d["status"] == "pending"
    assert d["tags"] == ["schema", "users"]
    assert d["applied_at"] is None


def test_migration_record_roundtrip(sample_record):
    sample_record.applied_at = datetime(2024, 1, 15, 10, 0, 0)
    sample_record.status = MigrationStatus.APPLIED
    restored = MigrationRecord.from_dict(sample_record.to_dict())
    assert restored.migration_id == sample_record.migration_id
    assert restored.status == MigrationStatus.APPLIED
    assert restored.applied_at == sample_record.applied_at
    assert restored.tags == sample_record.tags


def test_registry_register_and_get(sample_record):
    registry = MigrationRegistry()
    registry.register(sample_record)
    assert "0001" in registry
    assert registry.get("0001") is sample_record
    assert len(registry) == 1


def test_registry_by_status(sample_record):
    registry = MigrationRegistry()
    registry.register(sample_record)
    pending = registry.by_status(MigrationStatus.PENDING)
    assert len(pending) == 1
    applied = registry.by_status(MigrationStatus.APPLIED)
    assert len(applied) == 0


def test_registry_remove(sample_record):
    registry = MigrationRegistry()
    registry.register(sample_record)
    assert registry.remove("0001") is True
    assert registry.remove("0001") is False
    assert len(registry) == 0


def test_registry_checksum():
    sql = "CREATE TABLE users (id SERIAL PRIMARY KEY);"
    cs1 = MigrationRegistry.compute_checksum(sql)
    cs2 = MigrationRegistry.compute_checksum(sql)
    assert cs1 == cs2
    assert len(cs1) == 64


def test_registry_persistence(sample_record):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = Path(f.name)
    try:
        reg1 = MigrationRegistry(storage_path=path)
        reg1.register(sample_record)
        reg2 = MigrationRegistry(storage_path=path)
        assert "0001" in reg2
        assert reg2.get("0001").filename == sample_record.filename
    finally:
        path.unlink(missing_ok=True)
