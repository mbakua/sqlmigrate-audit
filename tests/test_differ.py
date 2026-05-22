"""Tests for sqlmigrate_audit.differ module."""

import pytest
from datetime import datetime, timezone
from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.differ import diff_registries, summarize_diff, DiffEntry


def _make_registry(*records: MigrationRecord) -> MigrationRegistry:
    reg = MigrationRegistry()
    for r in records:
        reg.register(r)
    return reg


@pytest.fixture
def base_record():
    return MigrationRecord(
        migration_id="0001_initial",
        description="Initial schema",
        status=MigrationStatus.APPLIED,
        applied_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        rollback_sql="DROP TABLE users;",
        tags=["core"],
    )


def test_no_diff_identical_registries(base_record):
    reg_a = _make_registry(base_record)
    reg_b = _make_registry(base_record)
    diffs = diff_registries(reg_a, reg_b)
    assert diffs == []


def test_diff_detects_added_migration(base_record):
    new_rec = MigrationRecord(migration_id="0002_add_email", description="Add email col")
    reg_a = _make_registry(base_record)
    reg_b = _make_registry(base_record, new_rec)
    diffs = diff_registries(reg_a, reg_b)
    assert len(diffs) == 1
    assert diffs[0].change_type == "added"
    assert diffs[0].migration_id == "0002_add_email"


def test_diff_detects_removed_migration(base_record):
    extra = MigrationRecord(migration_id="0002_add_email", description="Add email col")
    reg_a = _make_registry(base_record, extra)
    reg_b = _make_registry(base_record)
    diffs = diff_registries(reg_a, reg_b)
    assert len(diffs) == 1
    assert diffs[0].change_type == "removed"
    assert diffs[0].migration_id == "0002_add_email"


def test_diff_detects_modified_field(base_record):
    modified = MigrationRecord(
        migration_id="0001_initial",
        description="Initial schema",
        status=MigrationStatus.ROLLED_BACK,  # changed
        applied_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        rollback_sql="DROP TABLE users;",
        tags=["core"],
    )
    reg_a = _make_registry(base_record)
    reg_b = _make_registry(modified)
    diffs = diff_registries(reg_a, reg_b)
    assert len(diffs) == 1
    assert diffs[0].change_type == "modified"
    assert diffs[0].field == "status"
    assert diffs[0].old_value == MigrationStatus.APPLIED
    assert diffs[0].new_value == MigrationStatus.ROLLED_BACK


def test_diff_empty_registries():
    diffs = diff_registries(MigrationRegistry(), MigrationRegistry())
    assert diffs == []


def test_summarize_no_diff():
    assert summarize_diff([]) == "No differences found."


def test_summarize_mixed_diffs():
    diffs = [
        DiffEntry("a", "added"),
        DiffEntry("b", "removed"),
        DiffEntry("c", "modified", field="status", old_value="applied", new_value="rolled_back"),
        DiffEntry("d", "modified", field="description", old_value="old", new_value="new"),
    ]
    summary = summarize_diff(diffs)
    assert "1 added" in summary
    assert "1 removed" in summary
    assert "2 field(s) modified" in summary
