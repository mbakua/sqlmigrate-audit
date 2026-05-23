"""Integration tests: comparator works end-to-end with real registry mutations."""
from __future__ import annotations

import datetime
import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.snapshot import take_snapshot
from sqlmigrate_audit.comparator import compare_snapshots, format_comparison


def _dt(day: int) -> datetime.datetime:
    return datetime.datetime(2024, 6, day, 8, 0, 0)


def _rec(mid: str, status: MigrationStatus = MigrationStatus.APPLIED, tags=None) -> MigrationRecord:
    return MigrationRecord(
        migration_id=mid,
        description=f"Migration {mid}",
        status=status,
        applied_at=_dt(1),
        author="integrator",
        tags=tags or [],
    )


def test_full_lifecycle_comparison():
    """Simulate a migration lifecycle: add, apply, rollback across snapshots."""
    reg = MigrationRegistry()
    reg.register(_rec("m001"))
    reg.register(_rec("m002"))
    snap_before = take_snapshot(reg, label="before")

    # Simulate adding a migration and rolling back another
    reg.register(_rec("m003"))
    updated = _rec("m002", status=MigrationStatus.ROLLED_BACK)
    reg._records["m002"] = updated  # direct mutation for test purposes
    snap_after = take_snapshot(reg, label="after")

    report = compare_snapshots(snap_before, snap_after)
    assert report.has_differences
    assert any(e.migration_id == "m003" for e in report.added)


def test_comparison_labels_preserved():
    reg = MigrationRegistry()
    reg.register(_rec("m001"))
    s1 = take_snapshot(reg, label="release-1.0")
    s2 = take_snapshot(reg, label="release-1.1")
    report = compare_snapshots(s1, s2)
    assert report.snapshot_a_label == "release-1.0"
    assert report.snapshot_b_label == "release-1.1"


def test_format_output_contains_summary_header():
    reg = MigrationRegistry()
    reg.register(_rec("m001"))
    s1 = take_snapshot(reg, label="s1")
    reg.register(_rec("m002"))
    s2 = take_snapshot(reg, label="s2")
    text = format_comparison(compare_snapshots(s1, s2))
    assert "Comparing" in text
    assert "s1" in text
    assert "s2" in text


def test_multiple_additions_all_reported():
    reg = MigrationRegistry()
    snap_empty = take_snapshot(reg, label="empty")
    for i in range(1, 6):
        reg.register(_rec(f"m{i:03d}"))
    snap_full = take_snapshot(reg, label="full")
    report = compare_snapshots(snap_empty, snap_full)
    assert len(report.added) == 5
    assert report.removed == []


def test_symmetric_diff_reversal():
    """Swapping snap_a and snap_b should swap added/removed counts."""
    reg_a = MigrationRegistry()
    reg_a.register(_rec("m001"))
    reg_b = MigrationRegistry()
    reg_b.register(_rec("m001"))
    reg_b.register(_rec("m002"))

    s_a = take_snapshot(reg_a, label="a")
    s_b = take_snapshot(reg_b, label="b")

    fwd = compare_snapshots(s_a, s_b)
    rev = compare_snapshots(s_b, s_a)

    assert len(fwd.added) == len(rev.removed)
    assert len(fwd.removed) == len(rev.added)
