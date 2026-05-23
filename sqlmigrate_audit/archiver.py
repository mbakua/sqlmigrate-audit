"""Archive and restore migration registries with timestamped archive entries."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .registry import MigrationRegistry
from .serializer import records_to_json, records_from_json


@dataclass
class ArchiveEntry:
    """A single archived state of a registry."""

    archived_at: str
    label: str
    records_json: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"ArchiveEntry(label={self.label!r}, archived_at={self.archived_at!r})"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def archive_registry(
    registry: MigrationRegistry,
    archive_path: str | Path,
    label: str = "",
) -> ArchiveEntry:
    """Append a snapshot of *registry* to the JSON-lines archive at *archive_path*."""
    path = Path(archive_path)
    entry = ArchiveEntry(
        archived_at=_now_iso(),
        label=label or _now_iso(),
        records_json=records_to_json(list(registry.all())),
    )
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"archived_at": entry.archived_at, "label": entry.label, "records_json": entry.records_json}))
        fh.write("\n")
    return entry


def load_archives(archive_path: str | Path) -> List[ArchiveEntry]:
    """Return all archive entries stored in *archive_path* (oldest first)."""
    path = Path(archive_path)
    if not path.exists():
        return []
    entries: List[ArchiveEntry] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        data = json.loads(raw_line)
        entries.append(ArchiveEntry(**data))
    return entries


def restore_latest(archive_path: str | Path) -> Optional[MigrationRegistry]:
    """Restore the most-recently archived registry, or *None* if archive is empty."""
    entries = load_archives(archive_path)
    if not entries:
        return None
    latest = entries[-1]
    registry = MigrationRegistry()
    for record in records_from_json(latest.records_json):
        registry.register(record)
    return registry
