"""Tests for sqlmigrate_audit.summarizer."""

import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.summarizer import RegistrySummary, format_summary, summarize_registry


def _make_registry() -> MigrationRegistry:
    reg = MigrationRegistry()
    reg.register(
        MigrationRecord(
            migration_id="0001",
            description="Create users",
            author="alice",
            status=MigrationStatus.APPLIED,
            rollback_sql="DROP TABLE users;",
            tags=["schema", "users"],
        )
    )
    reg.register(
        MigrationRecord(
            migration_id="0002",
            description="Add email column",
            author="alice",
            status=MigrationStatus.APPLIED,
            rollback_sql="",
            tags=["schema"],
        )
    )
    reg.register(
        MigrationRecord(
            migration_id="0003",
            description="Seed data",
            author="bob",
            status=MigrationStatus.PENDING,
            rollback_sql=None,
            tags=[],
        )
    )
    reg.register(
        MigrationRecord(
            migration_id="0004",
            description="Remove old index",
            author="bob",
            status=MigrationStatus.ROLLED_BACK,
            rollback_sql="CREATE INDEX ...",
            tags=["index"],
        )
    )
    return reg


@pytest.fixture()
def registry() -> MigrationRegistry:
    return _make_registry()


def test_summarize_total(registry):
    s = summarize_registry(registry)
    assert s.total == 4


def test_summarize_by_status(registry):
    s = summarize_registry(registry)
    assert s.by_status[MigrationStatus.APPLIED.value] == 2
    assert s.by_status[MigrationStatus.PENDING.value] == 1
    assert s.by_status[MigrationStatus.ROLLED_BACK.value] == 1


def test_summarize_authors(registry):
    s = summarize_registry(registry)
    assert s.authors["alice"] == 2
    assert s.authors["bob"] == 2


def test_summarize_rollback_coverage(registry):
    s = summarize_registry(registry)
    # 0001 and 0004 have non-empty rollback_sql
    assert s.with_rollback_sql == 2
    assert s.without_rollback_sql == 2


def test_summarize_tags(registry):
    s = summarize_registry(registry)
    assert s.all_tags["schema"] == 2
    assert s.all_tags["users"] == 1
    assert s.all_tags["index"] == 1


def test_summarize_empty_registry():
    s = summarize_registry(MigrationRegistry())
    assert s.total == 0
    assert s.by_status == {}
    assert s.authors == {}
    assert s.all_tags == {}
    assert s.with_rollback_sql == 0
    assert s.without_rollback_sql == 0


def test_format_summary_contains_total(registry):
    s = summarize_registry(registry)
    output = format_summary(s)
    assert "Total migrations" in output
    assert "4" in output


def test_format_summary_contains_status_labels(registry):
    s = summarize_registry(registry)
    output = format_summary(s)
    assert MigrationStatus.APPLIED.value in output
    assert MigrationStatus.PENDING.value in output


def test_format_summary_contains_authors(registry):
    s = summarize_registry(registry)
    output = format_summary(s)
    assert "alice" in output
    assert "bob" in output


def test_format_summary_no_tags_section_when_empty():
    s = RegistrySummary(total=0)
    output = format_summary(s)
    assert "Tags:" not in output
