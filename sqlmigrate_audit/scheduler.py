"""Scheduled migration planner: attach due dates and priority to registry records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from sqlmigrate_audit.models import MigrationRecord
from sqlmigrate_audit.registry import MigrationRegistry

_TAG_PREFIX_DUE = "due:"
_TAG_PREFIX_PRIORITY = "priority:"


@dataclass
class ScheduleEntry:
    migration_id: str
    due_date: Optional[datetime]
    priority: int  # 1 = highest
    record: MigrationRecord

    def __repr__(self) -> str:  # pragma: no cover
        due = self.due_date.isoformat() if self.due_date else "none"
        return f"<ScheduleEntry id={self.migration_id} due={due} priority={self.priority}>"


def set_due_date(record: MigrationRecord, due_date: datetime) -> MigrationRecord:
    """Return a new record with the due-date tag set (replaces any existing one)."""
    iso = due_date.strftime("%Y-%m-%d")
    new_tag = f"{_TAG_PREFIX_DUE}{iso}"
    filtered = [t for t in record.tags if not t.startswith(_TAG_PREFIX_DUE)]
    return MigrationRecord(**{**record.__dict__, "tags": filtered + [new_tag]})


def set_priority(record: MigrationRecord, priority: int) -> MigrationRecord:
    """Return a new record with the priority tag set (replaces any existing one)."""
    if priority < 1:
        raise ValueError("Priority must be >= 1")
    new_tag = f"{_TAG_PREFIX_PRIORITY}{priority}"
    filtered = [t for t in record.tags if not t.startswith(_TAG_PREFIX_PRIORITY)]
    return MigrationRecord(**{**record.__dict__, "tags": filtered + [new_tag]})


def _parse_due(record: MigrationRecord) -> Optional[datetime]:
    for tag in record.tags:
        if tag.startswith(_TAG_PREFIX_DUE):
            try:
                return datetime.strptime(tag[len(_TAG_PREFIX_DUE):], "%Y-%m-%d")
            except ValueError:
                pass
    return None


def _parse_priority(record: MigrationRecord) -> int:
    for tag in record.tags:
        if tag.startswith(_TAG_PREFIX_PRIORITY):
            try:
                return int(tag[len(_TAG_PREFIX_PRIORITY):])
            except ValueError:
                pass
    return 999  # default low priority


def build_schedule(registry: MigrationRegistry) -> List[ScheduleEntry]:
    """Build a list of ScheduleEntry objects sorted by priority then due date."""
    entries: List[ScheduleEntry] = []
    for record in registry.all():
        entries.append(ScheduleEntry(
            migration_id=record.migration_id,
            due_date=_parse_due(record),
            priority=_parse_priority(record),
            record=record,
        ))
    entries.sort(key=lambda e: (
        e.priority,
        e.due_date or datetime.max,
    ))
    return entries


def format_schedule(entries: List[ScheduleEntry]) -> str:
    """Return a human-readable schedule table."""
    if not entries:
        return "No scheduled migrations."
    lines = ["Migration Schedule", "=================="]
    for e in entries:
        due = e.due_date.strftime("%Y-%m-%d") if e.due_date else "—"
        lines.append(f"  [{e.priority:>3}] {e.migration_id:<30} due: {due}")
    return "\n".join(lines)
