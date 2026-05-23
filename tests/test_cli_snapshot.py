"""Integration tests for cli_snapshot sub-commands."""

import json
import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.exporter import export_registry
from sqlmigrate_audit.snapshot import take_snapshot
from sqlmigrate_audit.snapshot_store import SnapshotStore
from sqlmigrate_audit.cli_snapshot import build_snapshot_subparser
import argparse


def _build_parser():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd")
    build_snapshot_subparser(sp)
    return p


@pytest.fixture()
def registry_file(tmp_path):
    reg = MigrationRegistry()
    reg.register(MigrationRecord(migration_id="m001", description="Init", status=MigrationStatus.APPLIED))
    reg.register(MigrationRecord(migration_id="m002", description="Add table", status=MigrationStatus.PENDING))
    path = str(tmp_path / "registry.json")
    export_registry(reg, path, fmt="json")
    return path


@pytest.fixture()
def store_path(tmp_path):
    return str(tmp_path / "snaps.json")


def _run(parser, args_list):
    args = parser.parse_args(args_list)
    args.func(args)


def test_take_creates_snapshot(registry_file, store_path, capsys):
    parser = _build_parser()
    _run(parser, ["snapshot", "take", registry_file, "--store", store_path, "--label", "v1"])
    out = capsys.readouterr().out
    assert "v1" in out
    assert "2 records" in out


def test_list_shows_labels(registry_file, store_path, capsys):
    parser = _build_parser()
    _run(parser, ["snapshot", "take", registry_file, "--store", store_path, "--label", "snap1"])
    capsys.readouterr()  # clear
    _run(parser, ["snapshot", "list", "--store", store_path])
    out = capsys.readouterr().out
    assert "snap1" in out


def test_list_empty_store(store_path, capsys):
    parser = _build_parser()
    _run(parser, ["snapshot", "list", "--store", store_path])
    out = capsys.readouterr().out
    assert "No snapshots" in out


def test_diff_two_snapshots(registry_file, store_path, capsys):
    parser = _build_parser()
    _run(parser, ["snapshot", "take", registry_file, "--store", store_path, "--label", "before"])
    _run(parser, ["snapshot", "take", registry_file, "--store", store_path, "--label", "after"])
    capsys.readouterr()
    _run(parser, ["snapshot", "diff", "--store", store_path, "before", "after"])
    out = capsys.readouterr().out
    assert out  # some summary output produced


def test_diff_missing_label_exits(store_path, capsys):
    import sys
    parser = _build_parser()
    with pytest.raises(SystemExit):
        _run(parser, ["snapshot", "diff", "--store", store_path, "ghost_a", "ghost_b"])
