"""Tests for sqlmigrate_audit.sorter."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.sorter import sort_records, sort_registry_records


def _dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


@pytest.fixture()
def sample_records() -> list[MigrationRecord]:
    return [
        MigrationRecord(
            migration_id="003",
            description="Third",
            status=MigrationStatus.PENDING,
            author="charlie",
            applied_at=_dt(2024, 3, 1),
        ),
        MigrationRecord(
            migration_id="001",
            description="First",
            status=MigrationStatus.APPLIED,
            author="alice",
            applied_at=_dt(2024, 1, 1),
        ),
        MigrationRecord(
            migration_id="002",
            description="Second",
            status=MigrationStatus.ROLLED_BACK,
            author="bob",
            applied_at=_dt(2024, 2, 1),
        ),
    ]


def test_sort_by_applied_at_ascending(sample_records):
    result = sort_records(sample_records, field="applied_at")
    ids = [r.migration_id for r in result]
    assert ids == ["001", "002", "003"]


def test_sort_by_applied_at_descending(sample_records):
    result = sort_records(sample_records, field="applied_at", reverse=True)
    ids = [r.migration_id for r in result]
    assert ids == ["003", "002", "001"]


def test_sort_by_migration_id(sample_records):
    result = sort_records(sample_records, field="migration_id")
    ids = [r.migration_id for r in result]
    assert ids == ["001", "002", "003"]


def test_sort_by_author(sample_records):
    result = sort_records(sample_records, field="author")
    authors = [r.author for r in result]
    assert authors == ["alice", "bob", "charlie"]


def test_sort_does_not_mutate_original(sample_records):
    original_ids = [r.migration_id for r in sample_records]
    sort_records(sample_records, field="migration_id")
    assert [r.migration_id for r in sample_records] == original_ids


def test_sort_invalid_field_raises(sample_records):
    with pytest.raises(ValueError, match="Cannot sort by"):
        sort_records(sample_records, field="nonexistent_field")


def test_sort_records_with_none_applied_at():
    records = [
        MigrationRecord(migration_id="b", description="B", applied_at=_dt(2024, 1, 2)),
        MigrationRecord(migration_id="a", description="A", applied_at=None),
    ]
    result = sort_records(records, field="applied_at")
    # None sorts last
    assert result[0].migration_id == "b"
    assert result[1].migration_id == "a"


def test_sort_registry_records(sample_records):
    registry = MigrationRegistry()
    for rec in sample_records:
        registry.register(rec)
    result = sort_registry_records(registry, field="migration_id")
    assert [r.migration_id for r in result] == ["001", "002", "003"]
