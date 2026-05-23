"""Watcher module: detect new or changed migrations compared to a baseline snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.snapshot import Snapshot, take_snapshot


@dataclass
class WatchResult:
    """Result produced by watch_for_changes."""

    new_migration_ids: List[str] = field(default_factory=list)
    modified_migration_ids: List[str] = field(default_factory=list)
    removed_migration_ids: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(
            self.new_migration_ids
            or self.modified_migration_ids
            or self.removed_migration_ids
        )

    def summary(self) -> str:
        lines = ["WatchResult:"]
        lines.append(f"  New      : {len(self.new_migration_ids)}")
        lines.append(f"  Modified : {len(self.modified_migration_ids)}")
        lines.append(f"  Removed  : {len(self.removed_migration_ids)}")
        if not self.has_changes:
            lines.append("  (no changes detected)")
        return "\n".join(lines)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"WatchResult(new={self.new_migration_ids}, "
            f"modified={self.modified_migration_ids}, "
            f"removed={self.removed_migration_ids})"
        )


def watch_for_changes(
    baseline: Snapshot,
    current: MigrationRegistry,
    label: Optional[str] = None,
) -> WatchResult:
    """Compare *current* registry against a *baseline* snapshot.

    Returns a :class:`WatchResult` describing additions, modifications and
    removals since the baseline was taken.
    """
    baseline_records = {r.migration_id: r for r in baseline.records}
    current_records = {r.migration_id: r for r in current.all()}

    new_ids = [mid for mid in current_records if mid not in baseline_records]
    removed_ids = [mid for mid in baseline_records if mid not in current_records]
    modified_ids = [
        mid
        for mid, rec in current_records.items()
        if mid in baseline_records and rec != baseline_records[mid]
    ]

    return WatchResult(
        new_migration_ids=sorted(new_ids),
        modified_migration_ids=sorted(modified_ids),
        removed_migration_ids=sorted(removed_ids),
    )


def snapshot_and_watch(
    baseline: Snapshot,
    current: MigrationRegistry,
    label: Optional[str] = None,
) -> tuple[WatchResult, Snapshot]:
    """Convenience helper: watch for changes *and* take a new snapshot of *current*."""
    result = watch_for_changes(baseline, current, label=label)
    new_snapshot = take_snapshot(current, label=label)
    return result, new_snapshot
