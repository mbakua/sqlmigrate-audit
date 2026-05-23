"""Timeline module: build a chronological view of migration history."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .models import MigrationRecord, MigrationStatus
from .registry import MigrationRegistry


@dataclass
class TimelineEntry:
    """A single entry in a migration timeline."""

    sequence: int
    migration_id: str
    applied_at: datetime
    status: MigrationStatus
    author: str
    description: str
    tags: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        ts = self.applied_at.strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"TimelineEntry(#{self.sequence} {self.migration_id} "
            f"[{self.status.value}] @ {ts})"
        )


def build_timeline(
    registry: MigrationRegistry,
    *,
    status_filter: Optional[MigrationStatus] = None,
) -> List[TimelineEntry]:
    """Return records sorted by applied_at, optionally filtered by status."""
    records: List[MigrationRecord] = list(registry.all())

    if status_filter is not None:
        records = [r for r in records if r.status == status_filter]

    records.sort(key=lambda r: r.applied_at)

    return [
        TimelineEntry(
            sequence=idx + 1,
            migration_id=rec.migration_id,
            applied_at=rec.applied_at,
            status=rec.status,
            author=rec.author,
            description=rec.description,
            tags=list(rec.tags),
        )
        for idx, rec in enumerate(records)
    ]


def format_timeline(entries: List[TimelineEntry]) -> str:
    """Render a timeline as a human-readable string."""
    if not entries:
        return "No timeline entries found."

    lines = ["Migration Timeline", "=" * 40]
    for entry in entries:
        ts = entry.applied_at.strftime("%Y-%m-%d %H:%M")
        tag_str = ", ".join(entry.tags) if entry.tags else "—"
        lines.append(
            f"  [{entry.sequence:>3}] {ts}  {entry.migration_id:<30}  "
            f"{entry.status.value:<12}  {entry.author}  tags=[{tag_str}]"
        )
    lines.append("=" * 40)
    lines.append(f"Total: {len(entries)} migration(s)")
    return "\n".join(lines)
