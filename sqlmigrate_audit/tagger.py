"""Tag management utilities for MigrationRecord collections."""

from typing import List, Dict, Set
from .models import MigrationRecord
from .registry import MigrationRegistry


def add_tag(record: MigrationRecord, tag: str) -> MigrationRecord:
    """Return a new MigrationRecord with the given tag added (no duplicates)."""
    current_tags: List[str] = list(record.tags or [])
    if tag not in current_tags:
        current_tags.append(tag)
    return MigrationRecord(
        migration_id=record.migration_id,
        description=record.description,
        status=record.status,
        applied_at=record.applied_at,
        rolled_back_at=record.rolled_back_at,
        rollback_sql=record.rollback_sql,
        author=record.author,
        tags=current_tags,
    )


def remove_tag(record: MigrationRecord, tag: str) -> MigrationRecord:
    """Return a new MigrationRecord with the given tag removed."""
    current_tags: List[str] = [t for t in (record.tags or []) if t != tag]
    return MigrationRecord(
        migration_id=record.migration_id,
        description=record.description,
        status=record.status,
        applied_at=record.applied_at,
        rolled_back_at=record.rolled_back_at,
        rollback_sql=record.rollback_sql,
        author=record.author,
        tags=current_tags,
    )


def list_all_tags(registry: MigrationRegistry) -> List[str]:
    """Return a sorted list of all unique tags across all records in the registry."""
    tag_set: Set[str] = set()
    for record in registry.all():
        for tag in (record.tags or []):
            tag_set.add(tag)
    return sorted(tag_set)


def tag_counts(registry: MigrationRegistry) -> Dict[str, int]:
    """Return a dict mapping each tag to the number of records that carry it."""
    counts: Dict[str, int] = {}
    for record in registry.all():
        for tag in (record.tags or []):
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def apply_tag_to_registry(
    registry: MigrationRegistry, tag: str, migration_ids: List[str]
) -> MigrationRegistry:
    """Return a new registry where the given tag is added to the specified migrations."""
    new_registry = MigrationRegistry()
    for record in registry.all():
        if record.migration_id in migration_ids:
            record = add_tag(record, tag)
        new_registry.register(record)
    return new_registry
