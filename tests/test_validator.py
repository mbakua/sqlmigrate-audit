"""Tests for sqlmigrate_audit.validator module."""

from datetime import datetime, timezone

import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.validator import (
    ValidationIssue,
    ValidationResult,
    validate_record,
    validate_registry,
)


@pytest.fixture
def valid_record() -> MigrationRecord:
    return MigrationRecord(
        migration_id="0001_initial",
        description="Create users table",
        sql="CREATE TABLE users (id SERIAL PRIMARY KEY);",
        rollback_sql="DROP TABLE users;",
        status=MigrationStatus.APPLIED,
        applied_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


def test_valid_record_has_no_issues(valid_record):
    issues = validate_record(valid_record)
    assert issues == []


def test_empty_migration_id_raises_issue():
    record = MigrationRecord(
        migration_id="",
        description="Some migration",
        sql="SELECT 1;",
    )
    issues = validate_record(record)
    fields = [i.field for i in issues]
    assert "migration_id" in fields


def test_empty_description_raises_issue():
    record = MigrationRecord(
        migration_id="0002_fix",
        description="   ",
        sql="SELECT 1;",
    )
    issues = validate_record(record)
    fields = [i.field for i in issues]
    assert "description" in fields


def test_rolled_back_without_rollback_sql_raises_issue():
    record = MigrationRecord(
        migration_id="0003_drop",
        description="Drop old table",
        sql="DROP TABLE old;",
        rollback_sql=None,
        status=MigrationStatus.ROLLED_BACK,
    )
    issues = validate_record(record)
    fields = [i.field for i in issues]
    assert "rollback_sql" in fields


def test_rolled_back_at_before_applied_at_raises_issue():
    record = MigrationRecord(
        migration_id="0004_ts",
        description="Timestamp check",
        sql="SELECT 1;",
        applied_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        rolled_back_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        status=MigrationStatus.ROLLED_BACK,
        rollback_sql="SELECT 0;",
    )
    issues = validate_record(record)
    fields = [i.field for i in issues]
    assert "rolled_back_at" in fields


def test_validate_registry_all_valid(valid_record):
    registry = MigrationRegistry()
    registry.register(valid_record)
    result = validate_registry(registry)
    assert result.is_valid
    assert "valid" in result.summary().lower()


def test_validate_registry_with_issues():
    registry = MigrationRegistry()
    bad_record = MigrationRecord(
        migration_id="",
        description="",
        sql="SELECT 1;",
    )
    registry.register(bad_record)
    result = validate_registry(registry)
    assert not result.is_valid
    assert "issue" in result.summary().lower()


def test_validation_issue_repr():
    issue = ValidationIssue("0001", "description", "must not be empty")
    assert "0001" in repr(issue)
    assert "description" in repr(issue)
