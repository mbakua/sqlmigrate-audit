"""Sorting utilities for MigrationRecord collections."""

from __future__ import annotations

from typing import List, Optional

from sqlmigrate_audit.models import MigrationRecord


_VALID_FIELDS = {"migration_id", "applied_at", "author", "status", "description"}


def sort_records(
    records: List[MigrationRecord],
    field: str = "applied_at",
    reverse: bool = False,
) -> List[MigrationRecord]:
    """Return a new list of records sorted by *field*.

    Parameters
    ----------
    records:
        The records to sort.
    field:
        Attribute name to sort by.  Must be one of ``migration_id``,
        ``applied_at``, ``author``, ``status``, or ``description``.
    reverse:
        When ``True`` the sort order is descending.

    Raises
    ------
    ValueError
        If *field* is not a recognised sortable attribute.
    """
    if field not in _VALID_FIELDS:
        raise ValueError(
            f"Cannot sort by '{field}'. Valid fields are: {sorted(_VALID_FIELDS)}"
        )

    def _key(record: MigrationRecord):
        value = getattr(record, field)
        # None values sort last regardless of direction
        if value is None:
            # Use a sentinel that sorts after everything
            return (1, "") if not reverse else (0, "")
        return (0, str(value))

    return sorted(records, key=_key, reverse=reverse)


def sort_registry_records(
    registry,
    field: str = "applied_at",
    reverse: bool = False,
) -> List[MigrationRecord]:
    """Convenience wrapper: sort all records in *registry* and return them.

    The registry itself is **not** mutated.
    """
    return sort_records(list(registry.all()), field=field, reverse=reverse)
