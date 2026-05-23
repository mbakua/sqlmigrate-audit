"""Tests for sqlmigrate_audit.archiver."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sqlmigrate_audit.archiver import archive_registry, load_archives, restore_latest
from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry


def _make_registry() -> MigrationRegistry:
    reg = MigrationRegistry()
    reg.register(
        MigrationRecord(
            migration_id="0001_initial",
            description="Initial schema",
            status=MigrationStatus.APPLIED,
            author="alice",
        )
    )
    reg.register(
        MigrationRecord(
            migration_id="0002_add_users",
            description="Add users table",
            status=MigrationStatus.PENDING,
            author="bob",
        )
    )
    return reg


@pytest.fixture()
def archive_file(tmp_path: Path) -> Path:
    return tmp_path / "archive.jsonl"


def test_archive_creates_file(archive_file: Path) -> None:
    reg = _make_registry()
    archive_registry(reg, archive_file, label="v1")
    assert archive_file.exists()


def test_archive_entry_has_correct_label(archive_file: Path) -> None:
    reg = _make_registry()
    entry = archive_registry(reg, archive_file, label="release-1.0")
    assert entry.label == "release-1.0"


def test_load_archives_returns_all_entries(archive_file: Path) -> None:
    reg = _make_registry()
    archive_registry(reg, archive_file, label="snap-a")
    archive_registry(reg, archive_file, label="snap-b")
    entries = load_archives(archive_file)
    assert len(entries) == 2
    assert entries[0].label == "snap-a"
    assert entries[1].label == "snap-b"


def test_load_archives_missing_file_returns_empty(tmp_path: Path) -> None:
    entries = load_archives(tmp_path / "nonexistent.jsonl")
    assert entries == []


def test_restore_latest_returns_none_for_empty_archive(archive_file: Path) -> None:
    result = restore_latest(archive_file)
    assert result is None


def test_restore_latest_contains_all_records(archive_file: Path) -> None:
    reg = _make_registry()
    archive_registry(reg, archive_file, label="first")
    restored = restore_latest(archive_file)
    assert restored is not None
    ids = {r.migration_id for r in restored.all()}
    assert ids == {"0001_initial", "0002_add_users"}


def test_restore_latest_picks_most_recent(archive_file: Path) -> None:
    reg1 = _make_registry()
    archive_registry(reg1, archive_file, label="old")

    reg2 = MigrationRegistry()
    reg2.register(
        MigrationRecord(
            migration_id="0003_only",
            description="Only in second archive",
            status=MigrationStatus.APPLIED,
            author="carol",
        )
    )
    archive_registry(reg2, archive_file, label="new")

    restored = restore_latest(archive_file)
    assert restored is not None
    ids = {r.migration_id for r in restored.all()}
    assert ids == {"0003_only"}
