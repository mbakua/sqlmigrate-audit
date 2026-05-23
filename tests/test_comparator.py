"""Unit tests for sqlmigrate_audit.comparator."""
from __future__ import annotations

import datetime
import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.snapshot import take_snapshot
from sqlmigrate_audit.comparator import (
    compare_snapshots,
    format_comparison,
    ComparisonReport,
)


def _dt(day: int) -> datetime.datetime:
    return datetime.datetime(2024, 1, day, 12, 0, 0)


def _make_record(mid: str, status: MigrationStatus = MigrationStatus.APPLIED) -> MigrationRecord:
    return MigrationRecord(
        migration_id=mid,
        description=f"Migration {mid}",
        status=status,
        applied_at=_dt(1),
        author="dev",
    )


@pytest.fixture()
def base_registry() -> MigrationRegistry:
    reg = MigrationRegistry()
    reg.register(_make_record("m001"))
    reg.register(_make_record("m002"))
    return reg


def test_identical_snapshots_no_differences(base_registry):
    snap_a = take_snapshot(base_registry, label="v1")
    snap_b = take_snapshot(base_registry, label="v2")
    report = compare_snapshots(snap_a, snap_b)
    assert not report.has_differences
    assert report.added == []
    assert report.removed == []
    assert report.changed == []


def test_added_migration_detected(base_registry):
    snap_a = take_snapshot(base_registry, label="v1")
    base_registry.register(_make_record("m003"))
    snap_b = take_snapshot(base_registry, label="v2")
    report = compare_snapshots(snap_a, snap_b)
    assert report.has_differences
    assert len(report.added) == 1
    assert report.added[0].migration_id == "m003"


def test_removed_migration_detected(base_registry):
    snap_a = take_snapshot(base_registry, label="v1")
    reg2 = MigrationRegistry()
    reg2.register(_make_record("m001"))
    snap_b = take_snapshot(reg2, label="v2")
    report = compare_snapshots(snap_a, snap_b)
    assert report.has_differences
    assert len(report.removed) == 1
    assert report.removed[0].migration_id == "m002"


def test_summary_contains_labels(base_registry):
    snap_a = take_snapshot(base_registry, label="alpha")
    snap_b = take_snapshot(base_registry, label="beta")
    report = compare_snapshots(snap_a, snap_b)
    summary = report.summary()
    assert "alpha" in summary
    assert "beta" in summary


def test_format_comparison_no_diff(base_registry):
    snap_a = take_snapshot(base_registry, label="v1")
    snap_b = take_snapshot(base_registry, label="v2")
    report = compare_snapshots(snap_a, snap_b)
    text = format_comparison(report)
    assert "No differences found" in text


def test_format_comparison_shows_added(base_registry):
    snap_a = take_snapshot(base_registry, label="v1")
    base_registry.register(_make_record("m999"))
    snap_b = take_snapshot(base_registry, label="v2")
    report = compare_snapshots(snap_a, snap_b)
    text = format_comparison(report)
    assert "m999" in text
    assert "+" in text


def test_comparison_report_repr(base_registry):
    snap_a = take_snapshot(base_registry, label="v1")
    snap_b = take_snapshot(base_registry, label="v2")
    report = compare_snapshots(snap_a, snap_b)
    assert isinstance(repr(report), str)
