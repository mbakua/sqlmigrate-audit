"""Compare two snapshots and produce a structured comparison report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlmigrate_audit.snapshot import Snapshot, snapshot_to_registry
from sqlmigrate_audit.differ import diff_registries, DiffEntry, summarize_diff


@dataclass
class ComparisonReport:
    """Structured result of comparing two snapshots."""

    snapshot_a_label: Optional[str]
    snapshot_b_label: Optional[str]
    added: List[DiffEntry] = field(default_factory=list)
    removed: List[DiffEntry] = field(default_factory=list)
    changed: List[DiffEntry] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = [
            f"Comparing '{self.snapshot_a_label}' -> '{self.snapshot_b_label}'",
            f"  Added  : {len(self.added)}",
            f"  Removed: {len(self.removed)}",
            f"  Changed: {len(self.changed)}",
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ComparisonReport(a={self.snapshot_a_label!r}, "
            f"b={self.snapshot_b_label!r}, "
            f"added={len(self.added)}, removed={len(self.removed)}, "
            f"changed={len(self.changed)})"
        )


def compare_snapshots(snap_a: Snapshot, snap_b: Snapshot) -> ComparisonReport:
    """Diff two snapshots and return a ComparisonReport."""
    reg_a = snapshot_to_registry(snap_a)
    reg_b = snapshot_to_registry(snap_b)
    entries = diff_registries(reg_a, reg_b)

    added = [e for e in entries if e.change_type == "added"]
    removed = [e for e in entries if e.change_type == "removed"]
    changed = [e for e in entries if e.change_type == "changed"]

    return ComparisonReport(
        snapshot_a_label=snap_a.label,
        snapshot_b_label=snap_b.label,
        added=added,
        removed=removed,
        changed=changed,
    )


def format_comparison(report: ComparisonReport) -> str:
    """Render a ComparisonReport as a human-readable string."""
    lines = [report.summary()]
    if report.added:
        lines.append("\nAdded migrations:")
        for e in report.added:
            lines.append(f"  + {e.migration_id}")
    if report.removed:
        lines.append("\nRemoved migrations:")
        for e in report.removed:
            lines.append(f"  - {e.migration_id}")
    if report.changed:
        lines.append("\nChanged migrations:")
        for e in report.changed:
            lines.append(f"  ~ {e.migration_id}: {e.detail}")
    if not report.has_differences:
        lines.append("\nNo differences found.")
    return "\n".join(lines)
