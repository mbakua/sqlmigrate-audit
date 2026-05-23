"""Tests for sqlmigrate_audit.auditor."""
import pytest

from sqlmigrate_audit.auditor import (
    AuditEvent,
    events_by_actor,
    events_for_migration,
    format_audit_log,
    record_event,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_log():
    return []


# ---------------------------------------------------------------------------
# AuditEvent dataclass
# ---------------------------------------------------------------------------

def test_audit_event_to_dict():
    e = AuditEvent(
        migration_id="m001",
        action="applied",
        actor="alice",
        timestamp="2024-01-01T00:00:00",
        note="initial deploy",
    )
    d = e.to_dict()
    assert d["migration_id"] == "m001"
    assert d["action"] == "applied"
    assert d["actor"] == "alice"
    assert d["note"] == "initial deploy"


def test_audit_event_roundtrip():
    e = AuditEvent(
        migration_id="m002",
        action="rolled_back",
        actor="bob",
        timestamp="2024-06-15T12:00:00",
    )
    assert AuditEvent.from_dict(e.to_dict()) == e


def test_audit_event_no_note_defaults_none():
    e = AuditEvent.from_dict(
        {"migration_id": "m003", "action": "tagged", "actor": "carol", "timestamp": "2024-01-01T00:00:00"}
    )
    assert e.note is None


# ---------------------------------------------------------------------------
# record_event
# ---------------------------------------------------------------------------

def test_record_event_appends_to_log():
    log = _empty_log()
    event = record_event(log, "m001", "applied", "alice")
    assert len(log) == 1
    assert log[0] is event


def test_record_event_uses_provided_timestamp():
    log = _empty_log()
    event = record_event(log, "m001", "applied", "alice", timestamp="2024-03-01T10:00:00")
    assert event.timestamp == "2024-03-01T10:00:00"


def test_record_event_auto_timestamp_is_set():
    log = _empty_log()
    event = record_event(log, "m001", "applied", "alice")
    assert event.timestamp  # non-empty string


def test_record_event_note_stored():
    log = _empty_log()
    event = record_event(log, "m001", "applied", "alice", note="hotfix")
    assert event.note == "hotfix"


# ---------------------------------------------------------------------------
# events_for_migration
# ---------------------------------------------------------------------------

def test_events_for_migration_filters_correctly():
    log = _empty_log()
    record_event(log, "m001", "applied", "alice")
    record_event(log, "m002", "applied", "bob")
    record_event(log, "m001", "tagged", "alice")
    result = events_for_migration(log, "m001")
    assert len(result) == 2
    assert all(e.migration_id == "m001" for e in result)


def test_events_for_migration_empty_when_no_match():
    log = _empty_log()
    record_event(log, "m001", "applied", "alice")
    assert events_for_migration(log, "m999") == []


# ---------------------------------------------------------------------------
# events_by_actor
# ---------------------------------------------------------------------------

def test_events_by_actor_filters_correctly():
    log = _empty_log()
    record_event(log, "m001", "applied", "alice")
    record_event(log, "m002", "applied", "bob")
    record_event(log, "m003", "rolled_back", "alice")
    result = events_by_actor(log, "alice")
    assert len(result) == 2
    assert all(e.actor == "alice" for e in result)


# ---------------------------------------------------------------------------
# format_audit_log
# ---------------------------------------------------------------------------

def test_format_audit_log_empty():
    assert format_audit_log([]) == "Audit log is empty."


def test_format_audit_log_contains_actor_and_action():
    log = _empty_log()
    record_event(log, "m001", "applied", "alice", timestamp="2024-01-01T00:00:00")
    output = format_audit_log(log)
    assert "alice" in output
    assert "applied" in output
    assert "m001" in output


def test_format_audit_log_includes_note_when_present():
    log = _empty_log()
    record_event(log, "m001", "applied", "alice", note="prod deploy", timestamp="2024-01-01T00:00:00")
    output = format_audit_log(log)
    assert "prod deploy" in output
