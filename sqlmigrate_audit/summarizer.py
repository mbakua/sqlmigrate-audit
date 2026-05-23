"""Summarizer module: produce aggregate statistics from a MigrationRegistry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry


@dataclass
class RegistrySummary:
    """Aggregate statistics for a MigrationRegistry."""

    total: int = 0
    by_status: Dict[str, int] = field(default_factory=dict)
    authors: Dict[str, int] = field(default_factory=dict)
    all_tags: Dict[str, int] = field(default_factory=dict)
    with_rollback_sql: int = 0
    without_rollback_sql: int = 0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RegistrySummary(total={self.total}, "
            f"by_status={self.by_status}, "
            f"authors={self.authors})"
        )


def summarize_registry(registry: MigrationRegistry) -> RegistrySummary:
    """Compute a RegistrySummary from all records in *registry*."""
    records: List[MigrationRecord] = registry.all()

    by_status: Dict[str, int] = {}
    authors: Dict[str, int] = {}
    all_tags: Dict[str, int] = {}
    with_rollback = 0
    without_rollback = 0

    for record in records:
        status_key = record.status.value if isinstance(record.status, MigrationStatus) else str(record.status)
        by_status[status_key] = by_status.get(status_key, 0) + 1

        author = record.author or "<unknown>"
        authors[author] = authors.get(author, 0) + 1

        for tag in record.tags:
            all_tags[tag] = all_tags.get(tag, 0) + 1

        if record.rollback_sql and record.rollback_sql.strip():
            with_rollback += 1
        else:
            without_rollback += 1

    return RegistrySummary(
        total=len(records),
        by_status=by_status,
        authors=authors,
        all_tags=all_tags,
        with_rollback_sql=with_rollback,
        without_rollback_sql=without_rollback,
    )


def format_summary(summary: RegistrySummary) -> str:
    """Return a human-readable string representation of *summary*."""
    lines = [
        "=== Migration Registry Summary ===",
        f"Total migrations : {summary.total}",
        "",
        "By status:",
    ]
    for status, count in sorted(summary.by_status.items()):
        lines.append(f"  {status:<20} {count}")

    lines += ["", "By author:"]
    for author, count in sorted(summary.authors.items()):
        lines.append(f"  {author:<30} {count}")

    lines += ["", "Rollback SQL coverage:"]
    lines.append(f"  With rollback SQL    : {summary.with_rollback_sql}")
    lines.append(f"  Without rollback SQL : {summary.without_rollback_sql}")

    if summary.all_tags:
        lines += ["", "Tags:"]
        for tag, count in sorted(summary.all_tags.items()):
            lines.append(f"  {tag:<30} {count}")

    return "\n".join(lines)
