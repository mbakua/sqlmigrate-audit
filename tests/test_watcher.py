"""Tests for sqlmigrate_audit.watcher."""

from __future__ import annotations

import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.snapshot import take_snapshot
from sqlmigrate_audit.watcher import WatchResult, snapshot_and_watch, watch_for_changes


def _make_record(mid: str, description: str = "desc") -> MigrationRecord:
    return MigrationRecord(
        migration_id=mid,
        description=description,
        status=MigrationStatus.APPLIED,
    )


@pytest.fixture()
def base_registry() -> MigrationRegistry:
    reg = MigrationRegistry()
    reg.register(_make_record("m001"))
    reg.register(_make_record("m002"))
    return reg


def test_no_changes_when_identical(base_registry):
    baseline = take_snapshot(base_registry, label="v1")
    result = watch_for_changes(baseline, base_registry)
    assert not result.has_changes
    assert result.new_migration_ids == []
    assert result.modified_migration_ids == []
    assert result.removed_migration_ids == []


def test_detects_new_migration(base_registry):
    baseline = take_snapshot(base_registry, label="v1")
    base_registry.register(_make_record("m003"))
    result = watch_for_changes(baseline, base_registry)
    assert result.has_changes
    assert "m003" in result.new_migration_ids
    assert result.removed_migration_ids == []
    assert result.modified_migration_ids == []


def test_detects_removed_migration(base_registry):
    baseline = take_snapshot(base_registry, label="v1")
    current = MigrationRegistry()
    current.register(_make_record("m001"))
    result = watch_for_changes(baseline, current)
    assert result.has_changes
    assert "m002" in result.removed_migration_ids
    assert result.new_migration_ids == []


def test_detects_modified_migration(base_registry):
    baseline = take_snapshot(base_registry, label="v1")
    current = MigrationRegistry()
    current.register(_make_record("m001", description="updated description"))
    current.register(_make_record("m002"))
    result = watch_for_changes(baseline, current)
    assert result.has_changes
    assert "m001" in result.modified_migration_ids


def test_summary_no_changes(base_registry):
    baseline = take_snapshot(base_registry)
    result = watch_for_changes(baseline, base_registry)
    summary = result.summary()
    assert "no changes" in summary


def test_summary_with_changes(base_registry):
    baseline = take_snapshot(base_registry, label="v1")
    base_registry.register(_make_record("m003"))
    result = watch_for_changes(baseline, base_registry)
    summary = result.summary()
    assert "New" in summary
    assert "1" in summary


def test_snapshot_and_watch_returns_new_snapshot(base_registry):
    baseline = take_snapshot(base_registry, label="v1")
    base_registry.register(_make_record("m003"))
    result, new_snap = snapshot_and_watch(baseline, base_registry, label="v2")
    assert isinstance(result, WatchResult)
    assert new_snap.label == "v2"
    assert len(new_snap.records) == 3


def test_watch_result_ids_are_sorted(base_registry):
    baseline = take_snapshot(base_registry)
    base_registry.register(_make_record("a001"))
    base_registry.register(_make_record("z999"))
    result = watch_for_changes(baseline, base_registry)
    assert result.new_migration_ids == sorted(result.new_migration_ids)
