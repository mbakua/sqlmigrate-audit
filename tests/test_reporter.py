"""Tests for sqlmigrate_audit.reporter."""

from __future__ import annotations

import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.reporter import generate_report, print_report


@pytest.fixture()
def populated_registry() -> MigrationRegistry:
    reg = MigrationRegistry()
    reg.register(
        MigrationRecord(
            migration_id="0001_initial",
            description="Create users table",
            status=MigrationStatus.APPLIED,
            applied_at="2024-01-10T08:00:00",
            rollback_sql="DROP TABLE users;",
        )
    )
    reg.register(
        MigrationRecord(
            migration_id="0002_add_email",
            description="Add email column",
            status=MigrationStatus.ROLLED_BACK,
            applied_at="2024-01-11T09:00:00",
            rollback_sql="ALTER TABLE users DROP COLUMN email;",
        )
    )
    reg.register(
        MigrationRecord(
            migration_id="0003_pending",
            description="Pending migration",
            status=MigrationStatus.PENDING,
        )
    )
    return reg


def test_report_contains_title(populated_registry):
    report = generate_report(populated_registry, title="My Report")
    assert "My Report" in report


def test_report_contains_migration_ids(populated_registry):
    report = generate_report(populated_registry)
    assert "0001_initial" in report
    assert "0002_add_email" in report
    assert "0003_pending" in report


def test_report_contains_status_labels(populated_registry):
    report = generate_report(populated_registry)
    assert "APPLIED" in report
    assert "ROLLED_BACK" in report
    assert "PENDING" in report


def test_report_summary_counts(populated_registry):
    report = generate_report(populated_registry)
    assert "Total migrations : 3" in report


def test_report_rollback_flag(populated_registry):
    report = generate_report(populated_registry)
    # 0001 has rollback sql
    lines = report.splitlines()
    rollback_lines = [l for l in lines if "Has rollback" in l]
    yes_count = sum(1 for l in rollback_lines if "yes" in l)
    no_count = sum(1 for l in rollback_lines if "no" in l)
    assert yes_count == 2
    assert no_count == 1


def test_empty_registry_report():
    reg = MigrationRegistry()
    report = generate_report(reg)
    assert "No migrations registered." in report
    assert "Total migrations : 0" in report


def test_print_report_outputs_to_stdout(populated_registry, capsys):
    print_report(populated_registry, title="CLI Report")
    captured = capsys.readouterr()
    assert "CLI Report" in captured.out
    assert "0001_initial" in captured.out
