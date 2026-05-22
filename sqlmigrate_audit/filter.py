"""Filtering utilities for MigrationRegistry queries."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry


def filter_by_status(
    registry: MigrationRegistry,
    status: MigrationStatus,
) -> List[MigrationRecord]:
    """Return all records whose status matches *status*."""
    return [r for r in registry.all() if r.status == status]


def filter_by_author(
    registry: MigrationRegistry,
    author: str,
) -> List[MigrationRecord]:
    """Return all records whose author matches *author* (case-insensitive)."""
    needle = author.lower()
    return [r for r in registry.all() if (r.author or "").lower() == needle]


def filter_by_date_range(
    registry: MigrationRegistry,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[MigrationRecord]:
    """Return records whose applied_at falls within [start, end] (inclusive).

    Records with no *applied_at* value are excluded.
    """
    results: List[MigrationRecord] = []
    for record in registry.all():
        ts = record.applied_at
        if ts is None:
            continue
        if start is not None and ts < start:
            continue
        if end is not None and ts > end:
            continue
        results.append(record)
    return results


def filter_by_tag(
    registry: MigrationRegistry,
    tag: str,
) -> List[MigrationRecord]:
    """Return records that contain *tag* in their tags list."""
    return [
        r for r in registry.all()
        if hasattr(r, "tags") and tag in (r.tags or [])
    ]
