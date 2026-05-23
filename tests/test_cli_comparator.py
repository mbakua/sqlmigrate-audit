"""Integration tests for the CLI comparator sub-commands."""
from __future__ import annotations

import json
import datetime
import argparse
import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.snapshot import take_snapshot, snapshot_to_dict
from sqlmigrate_audit.snapshot_store import SnapshotStore
from sqlmigrate_audit.cli_comparator import build_comparator_subparser


def _dt(day: int) -> datetime.datetime:
    return datetime.datetime(2024, 3, day, 10, 0, 0)


def _record(mid: str) -> MigrationRecord:
    return MigrationRecord(
        migration_id=mid,
        description=f"desc {mid}",
        status=MigrationStatus.APPLIED,
        applied_at=_dt(1),
        author="tester",
    )


@pytest.fixture()
def store_path(tmp_path):
    reg1 = MigrationRegistry()
    reg1.register(_record("m001"))
    snap1 = take_snapshot(reg1, label="snap-v1")

    reg2 = MigrationRegistry()
    reg2.register(_record("m001"))
    reg2.register(_record("m002"))
    snap2 = take_snapshot(reg2, label="snap-v2")

    store_file = tmp_path / "store.json"
    store = SnapshotStore(str(store_file))
    store.save(snap1)
    store.save(snap2)
    return str(store_file)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_comparator_subparser(sub)
    return parser


def _run(parser, argv, capsys):
    args = parser.parse_args(argv)
    args.func(args)
    return capsys.readouterr()


def test_compare_shows_added_migration(store_path, capsys):
    parser = _build_parser()
    out, _ = _run(parser, ["compare", store_path, "snap-v1", "snap-v2"], capsys)
    assert "m002" in out


def test_compare_no_diff_message(store_path, capsys):
    parser = _build_parser()
    out, _ = _run(parser, ["compare", store_path, "snap-v1", "snap-v1"], capsys)
    assert "No differences found" in out


def test_compare_latest_shows_diff(store_path, capsys):
    parser = _build_parser()
    out, _ = _run(parser, ["compare-latest", store_path], capsys)
    assert "m002" in out


def test_compare_missing_label_exits(store_path, capsys):
    parser = _build_parser()
    with pytest.raises(SystemExit):
        _run(parser, ["compare", store_path, "snap-v1", "nonexistent"], capsys)


def test_compare_latest_too_few_snapshots(tmp_path, capsys):
    reg = MigrationRegistry()
    reg.register(_record("m001"))
    snap = take_snapshot(reg, label="only-one")
    store_file = tmp_path / "store.json"
    store = SnapshotStore(str(store_file))
    store.save(snap)

    parser = _build_parser()
    with pytest.raises(SystemExit):
        _run(parser, ["compare-latest", str(store_file)], capsys)
