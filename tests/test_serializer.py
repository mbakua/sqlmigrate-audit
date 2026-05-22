"""Tests for sqlmigrate_audit.serializer (JSON and CSV round-trips)."""

import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.serializer import (
    records_from_csv,
    records_from_json,
    records_to_csv,
    records_to_json,
)


@pytest.fixture
def sample_records():
    return [
        MigrationRecord(
            migration_id="0001_initial",
            description="Create users table",
            status=MigrationStatus.APPLIED,
            rollback_sql="DROP TABLE users;",
        ),
        MigrationRecord(
            migration_id="0002_add_email",
            description="Add email column",
            status=MigrationStatus.PENDING,
        ),
    ]


def test_json_roundtrip(sample_records):
    serialized = records_to_json(sample_records)
    restored = records_from_json(serialized)
    assert len(restored) == 2
    assert restored[0].migration_id == "0001_initial"
    assert restored[0].rollback_sql == "DROP TABLE users;"
    assert restored[1].status == MigrationStatus.PENDING


def test_json_invalid_raises():
    with pytest.raises(ValueError, match="Expected a JSON array"):
        records_from_json('{"key": "value"}')


def test_csv_roundtrip(sample_records):
    serialized = records_to_csv(sample_records)
    assert "0001_initial" in serialized
    restored = records_from_csv(serialized)
    assert len(restored) == 2
    assert restored[0].migration_id == "0001_initial"
    assert restored[1].migration_id == "0002_add_email"


def test_csv_empty_list():
    result = records_to_csv([])
    assert result == ""


def test_json_preserves_status(sample_records):
    serialized = records_to_json(sample_records)
    restored = records_from_json(serialized)
    assert restored[0].status == MigrationStatus.APPLIED
