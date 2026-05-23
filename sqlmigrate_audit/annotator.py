"""Annotator module: attach and retrieve free-form notes on migration records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .models import MigrationRecord
from .registry import MigrationRegistry


@dataclass
class Annotation:
    """A single timestamped note attached to a migration."""

    author: str
    note: str
    created_at: str  # ISO-8601 string

    def __repr__(self) -> str:  # pragma: no cover
        return f"Annotation(author={self.author!r}, created_at={self.created_at!r})"


def add_annotation(
    record: MigrationRecord,
    author: str,
    note: str,
    created_at: str,
) -> MigrationRecord:
    """Return a new MigrationRecord with the annotation appended to its tags.

    Annotations are encoded as tags with the prefix ``note:<author>:<created_at>:<note>``
    so they survive JSON/CSV round-trips without schema changes.
    """
    if not author:
        raise ValueError("author must not be empty")
    if not note:
        raise ValueError("note must not be empty")
    if not created_at:
        raise ValueError("created_at must not be empty")

    encoded = f"note:{author}:{created_at}:{note}"
    new_tags = list(record.tags) + [encoded]
    return MigrationRecord(
        migration_id=record.migration_id,
        description=record.description,
        status=record.status,
        applied_at=record.applied_at,
        rolled_back_at=record.rolled_back_at,
        rollback_sql=record.rollback_sql,
        author=record.author,
        tags=new_tags,
    )


def get_annotations(record: MigrationRecord) -> List[Annotation]:
    """Extract all annotations stored in a record's tags."""
    annotations: List[Annotation] = []
    for tag in record.tags:
        if tag.startswith("note:"):
            # Format: note:<author>:<created_at>:<note text (may contain colons)>
            parts = tag.split(":", 3)
            if len(parts) == 4:
                _, author, created_at, note_text = parts
                annotations.append(Annotation(author=author, note=note_text, created_at=created_at))
    return annotations


def annotate_in_registry(
    registry: MigrationRegistry,
    migration_id: str,
    author: str,
    note: str,
    created_at: str,
) -> MigrationRegistry:
    """Return a new registry with the annotation added to the specified migration."""
    record = registry.get(migration_id)
    if record is None:
        raise KeyError(f"Migration '{migration_id}' not found in registry")
    updated = add_annotation(record, author, note, created_at)
    new_registry = MigrationRegistry()
    for r in registry.all():
        new_registry.register(updated if r.migration_id == migration_id else r)
    return new_registry
