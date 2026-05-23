"""Tests for sqlmigrate_audit.notifier."""
import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.notifier import (
    Notification,
    check_record,
    notify_registry,
    format_notifications,
    _is_pending,
    _is_failed,
    _missing_rollback,
)


@pytest.fixture()
def pending_record() -> MigrationRecord:
    return MigrationRecord(
        migration_id="m001",
        description="Add users table",
        status=MigrationStatus.PENDING,
        rollback_sql="DROP TABLE users;",
    )


@pytest.fixture()
def failed_record() -> MigrationRecord:
    return MigrationRecord(
        migration_id="m002",
        description="Add orders table",
        status=MigrationStatus.FAILED,
        rollback_sql="DROP TABLE orders;",
    )


@pytest.fixture()
def applied_no_rollback() -> MigrationRecord:
    return MigrationRecord(
        migration_id="m003",
        description="Add index",
        status=MigrationStatus.APPLIED,
        rollback_sql="",
    )


@pytest.fixture()
def clean_record() -> MigrationRecord:
    return MigrationRecord(
        migration_id="m004",
        description="Rename column",
        status=MigrationStatus.APPLIED,
        rollback_sql="ALTER TABLE t RENAME COLUMN b TO a;",
    )


def test_check_record_pending_generates_warning(pending_record):
    notes = check_record(pending_record)
    assert any(n.severity == "warning" and "pending" in n.message.lower() for n in notes)


def test_check_record_failed_generates_error(failed_record):
    notes = check_record(failed_record)
    assert any(n.severity == "error" and "failed" in n.message.lower() for n in notes)


def test_check_record_missing_rollback_generates_warning(applied_no_rollback):
    notes = check_record(applied_no_rollback)
    assert any("rollback" in n.message.lower() for n in notes)


def test_check_record_clean_record_no_notifications(clean_record):
    notes = check_record(clean_record)
    assert notes == []


def test_notification_migration_id_matches(pending_record):
    notes = check_record(pending_record)
    for n in notes:
        assert n.migration_id == "m001"


def test_notify_registry_aggregates_all_records():
    reg = MigrationRegistry()
    reg.register(MigrationRecord(migration_id="a", description="A", status=MigrationStatus.PENDING, rollback_sql=""))
    reg.register(MigrationRecord(migration_id="b", description="B", status=MigrationStatus.FAILED, rollback_sql="x"))
    notes = notify_registry(reg)
    ids = {n.migration_id for n in notes}
    assert "a" in ids
    assert "b" in ids


def test_notify_registry_empty_returns_empty():
    reg = MigrationRegistry()
    assert notify_registry(reg) == []


def test_format_notifications_no_notifications():
    assert format_notifications([]) == "No notifications."


def test_format_notifications_includes_severity_and_id():
    notes = [Notification(migration_id="m001", message="Something wrong", severity="error")]
    output = format_notifications(notes)
    assert "ERROR" in output
    assert "m001" in output
    assert "Something wrong" in output


def test_custom_condition_used_when_provided(clean_record):
    def always_warn(record):
        return "always"

    notes = check_record(clean_record, conditions=[(always_warn, "warning")])
    assert len(notes) == 1
    assert notes[0].message == "always"
