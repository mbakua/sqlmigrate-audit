"""High-level query helpers that combine filtering with sorting and pagination."""

from __future__ import annotations

from typing import List, Optional

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.filter import filter_by_status, filter_by_author


def query_records(
    registry: MigrationRegistry,
    *,
    status: Optional[MigrationStatus] = None,
    author: Optional[str] = None,
    sort_by: str = "migration_id",
    ascending: bool = True,
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[MigrationRecord]:
    """Filter, sort, and paginate records from *registry*.

    Parameters
    ----------
    registry:  Source registry to query.
    status:    Optional status filter.
    author:    Optional author filter (case-insensitive).
    sort_by:   Attribute name to sort by (must exist on MigrationRecord).
    ascending: Sort direction; True for ascending.
    limit:     Maximum number of records to return.
    offset:    Number of records to skip after sorting.
    """
    records: List[MigrationRecord] = registry.all()

    if status is not None:
        records = filter_by_status(registry, status)
        if author is not None:
            records = [r for r in records if (r.author or "").lower() == author.lower()]
    elif author is not None:
        records = filter_by_author(registry, author)

    try:
        records = sorted(
            records,
            key=lambda r: (getattr(r, sort_by) is None, getattr(r, sort_by)),
            reverse=not ascending,
        )
    except AttributeError as exc:
        raise ValueError(f"Unknown sort field: '{sort_by}'") from exc

    records = records[offset:]
    if limit is not None:
        records = records[:limit]

    return records


def count_by_status(registry: MigrationRegistry) -> dict:
    """Return a mapping of MigrationStatus -> count for all records."""
    counts: dict = {s: 0 for s in MigrationStatus}
    for record in registry.all():
        counts[record.status] = counts.get(record.status, 0) + 1
    return counts
