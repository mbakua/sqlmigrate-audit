"""Tests for sqlmigrate_audit.cli_timeline."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.exporter import export_registry
from sqlmigrate_audit.cli_timeline import build_timeline_subparser

import argparse


def _dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


@pytest.fixture()
def registry_file(tmp_path: Path) -> Path:
    reg = MigrationRegistry()
    reg.register(
        MigrationRecord(
            migration_id="m_001",
            description="Init schema",
            author="alice",
            applied_at=_dt(2024, 1, 10),
            status=MigrationStatus.APPLIED,
        )
    )
    reg.register(
        MigrationRecord(
            migration_id="m_002",
            description="Add users table",
            author="bob",
            applied_at=_dt(2024, 2, 5),
            status=MigrationStatus.ROLLED_BACK,
            rollback_sql="DROP TABLE users;",
        )
    )
    dest = tmp_path / "registry.json"
    export_registry(reg, str(dest), fmt="json")
    return dest


def _run(args: list[str]) -> tuple[int, str]:
    """Run CLI via argparse and capture stdout; return (exit_code, output)."""
    root = argparse.ArgumentParser()
    subs = root.add_subparsers(dest="command")
    build_timeline_subparser(subs)
    parsed = root.parse_args(args)
    import io, contextlib
    buf = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(buf):
        try:
            parsed.func(parsed)
        except SystemExit as exc:
            code = int(exc.code) if exc.code is not None else 0
    return code, buf.getvalue()


def test_timeline_shows_all_migrations(registry_file):
    code, out = _run(["timeline", str(registry_file)])
    assert code == 0
    assert "m_001" in out
    assert "m_002" in out


def test_timeline_filter_by_applied(registry_file):
    code, out = _run(["timeline", str(registry_file), "--status", "applied"])
    assert code == 0
    assert "m_001" in out
    assert "m_002" not in out


def test_timeline_filter_by_rolled_back(registry_file):
    code, out = _run(["timeline", str(registry_file), "--status", "rolled_back"])
    assert code == 0
    assert "m_002" in out
    assert "m_001" not in out


def test_timeline_sorted_output(registry_file):
    code, out = _run(["timeline", str(registry_file)])
    assert code == 0
    assert out.index("m_001") < out.index("m_002")


def test_timeline_contains_total(registry_file):
    code, out = _run(["timeline", str(registry_file)])
    assert "Total: 2" in out


def test_timeline_empty_after_filter(registry_file):
    code, out = _run(["timeline", str(registry_file), "--status", "pending"])
    assert code == 0
    assert "No timeline entries found." in out
