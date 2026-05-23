"""Tests for sqlmigrate_audit.timeline."""

from datetime import datetime, timezone

import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.timeline import TimelineEntry, build_timeline, format_timeline


def _dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


@pytest.fixture()
def populated_registry() -> MigrationRegistry:
    reg = MigrationRegistry()
    reg.register(
        MigrationRecord(
            migration_id="m_003",
            description="Third",
            author="alice",
            applied_at=_dt(2024, 3, 1),
            status=MigrationStatus.APPLIED,
            tags=["release"],
        )
    )
    reg.register(
        MigrationRecord(
            migration_id="m_001",
            description="First",
            author="bob",
            applied_at=_dt(2024, 1, 1),
            status=MigrationStatus.APPLIED,
        )
    )
    reg.register(
        MigrationRecord(
            migration_id="m_002",
            description="Second",
            author="alice",
            applied_at=_dt(2024, 2, 1),
            status=MigrationStatus.ROLLED_BACK,
        )
    )
    return reg


def test_build_timeline_sorted_by_applied_at(populated_registry):
    entries = build_timeline(populated_registry)
    ids = [e.migration_id for e in entries]
    assert ids == ["m_001", "m_002", "m_003"]


def test_build_timeline_sequence_numbers(populated_registry):
    entries = build_timeline(populated_registry)
    assert [e.sequence for e in entries] == [1, 2, 3]


def test_build_timeline_filter_by_status(populated_registry):
    entries = build_timeline(populated_registry, status_filter=MigrationStatus.APPLIED)
    assert all(e.status == MigrationStatus.APPLIED for e in entries)
    assert len(entries) == 2


def test_build_timeline_filter_no_match(populated_registry):
    entries = build_timeline(populated_registry, status_filter=MigrationStatus.PENDING)
    assert entries == []


def test_build_timeline_entry_fields(populated_registry):
    entries = build_timeline(populated_registry)
    first = entries[0]
    assert isinstance(first, TimelineEntry)
    assert first.migration_id == "m_001"
    assert first.author == "bob"
    assert first.description == "First"


def test_build_timeline_tags_copied(populated_registry):
    entries = build_timeline(populated_registry)
    third = next(e for e in entries if e.migration_id == "m_003")
    assert "release" in third.tags


def test_format_timeline_contains_ids(populated_registry):
    entries = build_timeline(populated_registry)
    output = format_timeline(entries)
    assert "m_001" in output
    assert "m_002" in output
    assert "m_003" in output


def test_format_timeline_contains_total(populated_registry):
    entries = build_timeline(populated_registry)
    output = format_timeline(entries)
    assert "Total: 3" in output


def test_format_timeline_empty():
    output = format_timeline([])
    assert "No timeline entries found." in output


def test_build_timeline_empty_registry():
    reg = MigrationRegistry()
    assert build_timeline(reg) == []
