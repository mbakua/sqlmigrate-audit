"""Audit log module: records who performed an action and when."""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import List, Optional

from sqlmigrate_audit.models import MigrationRecord
from sqlmigrate_audit.registry import MigrationRegistry


@dataclass
class AuditEvent:
    migration_id: str
    action: str          # e.g. "applied", "rolled_back", "registered", "tagged"
    actor: str
    timestamp: str       # ISO-8601
    note: Optional[str] = None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"AuditEvent(migration_id={self.migration_id!r}, action={self.action!r}, "
            f"actor={self.actor!r}, timestamp={self.timestamp!r})"
        )

    def to_dict(self) -> dict:
        return {
            "migration_id": self.migration_id,
            "action": self.action,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEvent":
        return cls(
            migration_id=data["migration_id"],
            action=data["action"],
            actor=data["actor"],
            timestamp=data["timestamp"],
            note=data.get("note"),
        )


def _now_iso() -> str:
    return datetime.datetime.utcnow().isoformat()


def record_event(
    log: List[AuditEvent],
    migration_id: str,
    action: str,
    actor: str,
    note: Optional[str] = None,
    *,
    timestamp: Optional[str] = None,
) -> AuditEvent:
    """Append a new AuditEvent to *log* and return it."""
    event = AuditEvent(
        migration_id=migration_id,
        action=action,
        actor=actor,
        timestamp=timestamp or _now_iso(),
        note=note,
    )
    log.append(event)
    return event


def events_for_migration(log: List[AuditEvent], migration_id: str) -> List[AuditEvent]:
    """Return all events related to *migration_id*, in insertion order."""
    return [e for e in log if e.migration_id == migration_id]


def events_by_actor(log: List[AuditEvent], actor: str) -> List[AuditEvent]:
    """Return all events performed by *actor*."""
    return [e for e in log if e.actor == actor]


def format_audit_log(log: List[AuditEvent]) -> str:
    """Return a human-readable audit log string."""
    if not log:
        return "Audit log is empty."
    lines = ["=== Audit Log ==="]
    for e in log:
        note_part = f" | note: {e.note}" if e.note else ""
        lines.append(f"[{e.timestamp}] {e.actor} -> {e.action} on {e.migration_id}{note_part}")
    return "\n".join(lines)
