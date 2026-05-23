"""Notifier module: emit alerts when migrations meet certain conditions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry


@dataclass
class Notification:
    """A single notification produced by the notifier."""
    migration_id: str
    message: str
    severity: str = "info"  # info | warning | error

    def __repr__(self) -> str:  # pragma: no cover
        return f"Notification(id={self.migration_id!r}, severity={self.severity!r}, msg={self.message!r})"


# ---------------------------------------------------------------------------
# Built-in condition helpers
# ---------------------------------------------------------------------------

def _is_pending(record: MigrationRecord) -> Optional[str]:
    if record.status == MigrationStatus.PENDING:
        return "Migration is still pending"
    return None


def _is_failed(record: MigrationRecord) -> Optional[str]:
    if record.status == MigrationStatus.FAILED:
        return "Migration has failed"
    return None


def _missing_rollback(record: MigrationRecord) -> Optional[str]:
    if not record.rollback_sql:
        return "Migration has no rollback SQL defined"
    return None


# Condition type: takes a record, returns a message string or None
ConditionFn = Callable[[MigrationRecord], Optional[str]]

_DEFAULT_CONDITIONS: List[tuple[ConditionFn, str]] = [
    (_is_pending, "warning"),
    (_is_failed, "error"),
    (_missing_rollback, "warning"),
]


def check_record(
    record: MigrationRecord,
    conditions: Optional[List[tuple[ConditionFn, str]]] = None,
) -> List[Notification]:
    """Run all conditions against a single record and return notifications."""
    conditions = conditions if conditions is not None else _DEFAULT_CONDITIONS
    notifications: List[Notification] = []
    for fn, severity in conditions:
        message = fn(record)
        if message is not None:
            notifications.append(
                Notification(
                    migration_id=record.migration_id,
                    message=message,
                    severity=severity,
                )
            )
    return notifications


def notify_registry(
    registry: MigrationRegistry,
    conditions: Optional[List[tuple[ConditionFn, str]]] = None,
) -> List[Notification]:
    """Run condition checks across all records in a registry."""
    results: List[Notification] = []
    for record in registry.all():
        results.extend(check_record(record, conditions))
    return results


def format_notifications(notifications: List[Notification]) -> str:
    """Return a human-readable summary of notifications."""
    if not notifications:
        return "No notifications."
    lines = [f"[{n.severity.upper()}] {n.migration_id}: {n.message}" for n in notifications]
    return "\n".join(lines)
