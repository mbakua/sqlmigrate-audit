"""Reporter module: generate human-readable summary reports from a MigrationRegistry."""

from __future__ import annotations

from typing import List

from sqlmigrate_audit.models import MigrationRecord, MigrationStatus
from sqlmigrate_audit.registry import MigrationRegistry


def _status_label(status: MigrationStatus) -> str:
    labels = {
        MigrationStatus.PENDING: "PENDING",
        MigrationStatus.APPLIED: "APPLIED",
        MigrationStatus.ROLLED_BACK: "ROLLED_BACK",
        MigrationStatus.FAILED: "FAILED",
    }
    return labels.get(status, str(status))


def _format_record(record: MigrationRecord, index: int) -> str:
    lines = [
        f"  [{index}] {record.migration_id}",
        f"      Status      : {_status_label(record.status)}",
        f"      Description : {record.description or '(none)'}",
        f"      Applied at  : {record.applied_at or '(not applied)'}",
        f"      Has rollback: {'yes' if record.rollback_sql else 'no'}",
    ]
    return "\n".join(lines)


def generate_report(registry: MigrationRegistry, *, title: str = "Migration Report") -> str:
    """Return a formatted text report for all records in *registry*."""
    records: List[MigrationRecord] = registry.all()

    status_counts: dict[str, int] = {}
    for record in records:
        label = _status_label(record.status)
        status_counts[label] = status_counts.get(label, 0) + 1

    header = f"{'=' * 50}\n{title}\n{'=' * 50}"
    summary_lines = [f"  Total migrations : {len(records)}"]
    for label, count in sorted(status_counts.items()):
        summary_lines.append(f"  {label:<16} : {count}")
    summary = "Summary:\n" + "\n".join(summary_lines)

    if not records:
        detail = "No migrations registered."
    else:
        detail = "Details:\n" + "\n".join(
            _format_record(r, i + 1) for i, r in enumerate(records)
        )

    return "\n".join([header, "", summary, "", detail, ""])


def print_report(registry: MigrationRegistry, *, title: str = "Migration Report") -> None:
    """Print the report directly to stdout."""
    print(generate_report(registry, title=title))
