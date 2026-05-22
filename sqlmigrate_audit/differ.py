"""Diff utilities for comparing migration registry states."""

from dataclasses import dataclass
from typing import List, Optional
from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry


@dataclass
class DiffEntry:
    """Represents a single difference between two registry states."""
    migration_id: str
    change_type: str  # 'added', 'removed', 'modified'
    field: Optional[str] = None
    old_value: Optional[object] = None
    new_value: Optional[object] = None

    def __repr__(self) -> str:
        if self.change_type == "modified":
            return (
                f"DiffEntry({self.migration_id!r}, modified {self.field!r}: "
                f"{self.old_value!r} -> {self.new_value!r})"
            )
        return f"DiffEntry({self.migration_id!r}, {self.change_type})"


COMPARED_FIELDS = ["description", "status", "applied_at", "rollback_sql", "tags"]


def diff_registries(
    base: MigrationRegistry,
    target: MigrationRegistry,
) -> List[DiffEntry]:
    """Compare two registries and return a list of differences.

    Args:
        base: The original registry state.
        target: The new registry state to compare against.

    Returns:
        List of DiffEntry objects describing each change.
    """
    diffs: List[DiffEntry] = []

    base_ids = {r.migration_id for r in base.all()}
    target_ids = {r.migration_id for r in target.all()}

    for mid in base_ids - target_ids:
        diffs.append(DiffEntry(migration_id=mid, change_type="removed"))

    for mid in target_ids - base_ids:
        diffs.append(DiffEntry(migration_id=mid, change_type="added"))

    for mid in base_ids & target_ids:
        base_rec: MigrationRecord = base.get(mid)
        target_rec: MigrationRecord = target.get(mid)
        for field in COMPARED_FIELDS:
            old_val = getattr(base_rec, field)
            new_val = getattr(target_rec, field)
            if old_val != new_val:
                diffs.append(
                    DiffEntry(
                        migration_id=mid,
                        change_type="modified",
                        field=field,
                        old_value=old_val,
                        new_value=new_val,
                    )
                )

    return diffs


def summarize_diff(diffs: List[DiffEntry]) -> str:
    """Return a human-readable summary of a diff result."""
    if not diffs:
        return "No differences found."
    added = sum(1 for d in diffs if d.change_type == "added")
    removed = sum(1 for d in diffs if d.change_type == "removed")
    modified = sum(1 for d in diffs if d.change_type == "modified")
    parts = []
    if added:
        parts.append(f"{added} added")
    if removed:
        parts.append(f"{removed} removed")
    if modified:
        parts.append(f"{modified} field(s) modified")
    return "; ".join(parts) + "."
