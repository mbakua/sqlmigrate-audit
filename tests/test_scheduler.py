"""Unit tests for sqlmigrate_audit.scheduler."""

from __future__ import annotations

from datetime import datetime

import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.scheduler import (
    build_schedule,
    format_schedule,
    set_due_date,
    set_priority,
)


def _rec(mid: str, tags=None) -> MigrationRecord:
    return MigrationRecord(
        migration_id=mid,
        description="desc",
        status=MigrationStatus.PENDING,
        tags=tags or [],
    )


def _reg(*records: MigrationRecord) -> MigrationRegistry:
    r = MigrationRegistry()
    for rec in records:
        r.register(rec)
    return r


def test_set_due_date_adds_tag():
    rec = _rec("m001")
    updated = set_due_date(rec, datetime(2024, 6, 15))
    assert "due:2024-06-15" in updated.tags


def test_set_due_date_replaces_existing():
    rec = _rec("m001", tags=["due:2023-01-01"])
    updated = set_due_date(rec, datetime(2024, 6, 15))
    due_tags = [t for t in updated.tags if t.startswith("due:")]
    assert due_tags == ["due:2024-06-15"]


def test_set_due_date_does_not_mutate_original():
    rec = _rec("m001")
    set_due_date(rec, datetime(2024, 1, 1))
    assert not any(t.startswith("due:") for t in rec.tags)


def test_set_priority_adds_tag():
    rec = _rec("m001")
    updated = set_priority(rec, 2)
    assert "priority:2" in updated.tags


def test_set_priority_replaces_existing():
    rec = _rec("m001", tags=["priority:5"])
    updated = set_priority(rec, 1)
    pri_tags = [t for t in updated.tags if t.startswith("priority:")]
    assert pri_tags == ["priority:1"]


def test_set_priority_invalid_raises():
    with pytest.raises(ValueError):
        set_priority(_rec("m001"), 0)


def test_build_schedule_sorted_by_priority_then_due():
    r = _reg(
        set_priority(set_due_date(_rec("m003"), datetime(2024, 3, 1)), 2),
        set_priority(set_due_date(_rec("m001"), datetime(2024, 1, 1)), 1),
        set_priority(set_due_date(_rec("m002"), datetime(2024, 2, 1)), 1),
    )
    entries = build_schedule(r)
    ids = [e.migration_id for e in entries]
    assert ids == ["m001", "m002", "m003"]


def test_build_schedule_no_due_date_sorts_last():
    r = _reg(
        set_priority(_rec("m_no_due"), 1),
        set_priority(set_due_date(_rec("m_due"), datetime(2024, 1, 1)), 1),
    )
    entries = build_schedule(r)
    assert entries[0].migration_id == "m_due"
    assert entries[1].migration_id == "m_no_due"


def test_format_schedule_contains_ids():
    r = _reg(set_due_date(set_priority(_rec("m001"), 1), datetime(2024, 5, 10)))
    output = format_schedule(build_schedule(r))
    assert "m001" in output
    assert "2024-05-10" in output


def test_format_schedule_empty():
    assert format_schedule([]) == "No scheduled migrations."
