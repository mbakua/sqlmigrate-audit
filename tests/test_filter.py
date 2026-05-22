"""Tests for sqlmigrate_audit.filter module."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.filter import (
    filter_by_author,
    filter_by_date_range,
    filter_by_status,
    filter_by_tag,
)


def _dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


@pytest.fixture()
def registry() -> MigrationRegistry:
    reg = MigrationRegistry()
    reg.register(
        MigrationRecord(
            migration_id="m001",
            description="First",
            status=MigrationStatus.APPLIED,
            author="alice",
            applied_at=_dt(2024, 1, 10),
        )
    )
    reg.register(
        MigrationRecord(
            migration_id="m002",
            description="Second",
            status=MigrationStatus.PENDING,
            author="bob",
            applied_at=_dt(2024, 3, 5),
        )
    )
    reg.register(
        MigrationRecord(
            migration_id="m003",
            description="Third",
            status=MigrationStatus.ROLLED_BACK,
            author="alice",
            applied_at=None,
        )
    )
    return reg


def test_filter_by_status_applied(registry):
    results = filter_by_status(registry, MigrationStatus.APPLIED)
    assert len(results) == 1
    assert results[0].migration_id == "m001"


def test_filter_by_status_pending(registry):
    results = filter_by_status(registry, MigrationStatus.PENDING)
    assert len(results) == 1
    assert results[0].migration_id == "m002"


def test_filter_by_status_no_match(registry):
    results = filter_by_status(registry, MigrationStatus.FAILED)
    assert results == []


def test_filter_by_author_alice(registry):
    results = filter_by_author(registry, "alice")
    ids = {r.migration_id for r in results}
    assert ids == {"m001", "m003"}


def test_filter_by_author_case_insensitive(registry):
    results = filter_by_author(registry, "BOB")
    assert len(results) == 1
    assert results[0].migration_id == "m002"


def test_filter_by_author_no_match(registry):
    assert filter_by_author(registry, "carol") == []


def test_filter_by_date_range_full(registry):
    results = filter_by_date_range(registry, start=_dt(2024, 1, 1), end=_dt(2024, 12, 31))
    ids = {r.migration_id for r in results}
    assert ids == {"m001", "m002"}


def test_filter_by_date_range_start_only(registry):
    results = filter_by_date_range(registry, start=_dt(2024, 2, 1))
    assert len(results) == 1
    assert results[0].migration_id == "m002"


def test_filter_by_date_range_excludes_none_applied_at(registry):
    results = filter_by_date_range(registry)
    ids = {r.migration_id for r in results}
    assert "m003" not in ids


def test_filter_by_tag_no_tags_attr(registry):
    """Records without tags should be silently excluded."""
    results = filter_by_tag(registry, "hotfix")
    assert results == []
