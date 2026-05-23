"""Unit tests for snapshot.py and snapshot_store.py."""

import json
import os
import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.snapshot import (
    take_snapshot,
    snapshot_to_dict,
    snapshot_from_dict,
    snapshot_to_registry,
)
from sqlmigrate_audit.snapshot_store import SnapshotStore


@pytest.fixture()
def populated_registry():
    reg = MigrationRegistry()
    reg.register(MigrationRecord(migration_id="m001", description="First", status=MigrationStatus.APPLIED))
    reg.register(MigrationRecord(migration_id="m002", description="Second", status=MigrationStatus.PENDING))
    return reg


def test_take_snapshot_captures_all_records(populated_registry):
    snap = take_snapshot(populated_registry, label="v1")
    assert len(snap.records) == 2
    assert snap.label == "v1"
    assert snap.taken_at  # non-empty ISO string


def test_take_snapshot_no_label(populated_registry):
    snap = take_snapshot(populated_registry)
    assert snap.label is None


def test_snapshot_roundtrip_via_dict(populated_registry):
    snap = take_snapshot(populated_registry, label="round")
    restored = snapshot_from_dict(snapshot_to_dict(snap))
    assert restored.label == snap.label
    assert restored.taken_at == snap.taken_at
    assert len(restored.records) == len(snap.records)
    ids_original = {r.migration_id for r in snap.records}
    ids_restored = {r.migration_id for r in restored.records}
    assert ids_original == ids_restored


def test_snapshot_to_registry_contains_records(populated_registry):
    snap = take_snapshot(populated_registry, label="reg")
    reg2 = snapshot_to_registry(snap)
    assert reg2.get("m001") is not None
    assert reg2.get("m002") is not None


def test_snapshot_store_save_and_load(tmp_path, populated_registry):
    store_path = str(tmp_path / "snaps.json")
    store = SnapshotStore(store_path)
    snap = take_snapshot(populated_registry, label="alpha")
    store.save(snap)
    loaded = store.load("alpha")
    assert loaded.label == "alpha"
    assert len(loaded.records) == 2


def test_snapshot_store_list_labels(tmp_path, populated_registry):
    store_path = str(tmp_path / "snaps.json")
    store = SnapshotStore(store_path)
    store.save(take_snapshot(populated_registry, label="b"))
    store.save(take_snapshot(populated_registry, label="a"))
    assert store.list_labels() == ["a", "b"]


def test_snapshot_store_delete(tmp_path, populated_registry):
    store_path = str(tmp_path / "snaps.json")
    store = SnapshotStore(store_path)
    store.save(take_snapshot(populated_registry, label="del_me"))
    store.delete("del_me")
    assert "del_me" not in store.list_labels()


def test_snapshot_store_delete_missing_raises(tmp_path):
    store_path = str(tmp_path / "snaps.json")
    store = SnapshotStore(store_path)
    with pytest.raises(KeyError):
        store.delete("ghost")


def test_snapshot_store_load_missing_raises(tmp_path):
    store_path = str(tmp_path / "snaps.json")
    store = SnapshotStore(store_path)
    with pytest.raises(KeyError):
        store.load("nope")


def test_snapshot_store_no_label_raises(tmp_path, populated_registry):
    store_path = str(tmp_path / "snaps.json")
    store = SnapshotStore(store_path)
    snap = take_snapshot(populated_registry)  # label=None
    with pytest.raises(ValueError):
        store.save(snap)
