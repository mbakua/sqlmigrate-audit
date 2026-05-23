"""Integration tests: timeline + exporter + registry round-trip."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from sqlmigrate_audit.exporter import export_registry, import_registry
from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.timeline import build_timeline, format_timeline


def _dt(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, tzinfo=timezone.utc)


@pytest.fixture()
def rich_registry() -> MigrationRegistry:
    reg = MigrationRegistry()
    data = [
        ("m_a", _dt(2023, 6, 1), MigrationStatus.APPLIED, "dev", ["v1"]),
        ("m_b", _dt(2023, 8, 15), MigrationStatus.ROLLED_BACK, "ops", []),
        ("m_c", _dt(2024, 1, 20), MigrationStatus.APPLIED, "dev", ["v2", "hotfix"]),
        ("m_d", _dt(2024, 3, 3), MigrationStatus.PENDING, "qa", []),
        ("m_e", _dt(2024, 3, 10), MigrationStatus.FAILED, "dev", ["v2"]),
    ]
    for mid, ts, status, author, tags in data:
        reg.register(
            MigrationRecord(
                migration_id=mid,
                description=f"Desc {mid}",
                author=author,
                applied_at=ts,
                status=status,
                tags=tags,
            )
        )
    return reg


def test_timeline_order_matches_dates(rich_registry):
    entries = build_timeline(rich_registry)
    dates = [e.applied_at for e in entries]
    assert dates == sorted(dates)


def test_timeline_all_records_present(rich_registry):
    entries = build_timeline(rich_registry)
    assert len(entries) == 5


def test_timeline_tags_preserved(rich_registry):
    entries = build_timeline(rich_registry)
    entry_c = next(e for e in entries if e.migration_id == "m_c")
    assert set(entry_c.tags) == {"v2", "hotfix"}


def test_timeline_roundtrip_via_json(rich_registry, tmp_path: Path):
    dest = tmp_path / "reg.json"
    export_registry(rich_registry, str(dest), fmt="json")
    loaded = import_registry(str(dest))
    entries = build_timeline(loaded)
    ids = [e.migration_id for e in entries]
    assert "m_a" in ids and "m_e" in ids


def test_format_timeline_includes_author(rich_registry):
    entries = build_timeline(rich_registry)
    output = format_timeline(entries)
    assert "dev" in output
    assert "ops" in output


def test_format_timeline_status_labels(rich_registry):
    entries = build_timeline(rich_registry)
    output = format_timeline(entries)
    assert MigrationStatus.APPLIED.value in output
    assert MigrationStatus.ROLLED_BACK.value in output
