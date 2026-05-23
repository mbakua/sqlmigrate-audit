"""Snapshot support: capture and compare registry state at a point in time."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .models import MigrationRecord
from .registry import MigrationRegistry
from .serializer import records_to_json, records_from_json


@dataclass
class Snapshot:
    """Immutable capture of a registry's records at a given moment."""

    taken_at: str
    label: Optional[str]
    records: List[MigrationRecord] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Snapshot(label={self.label!r}, taken_at={self.taken_at!r}, records={len(self.records)})"


def take_snapshot(registry: MigrationRegistry, label: Optional[str] = None) -> Snapshot:
    """Capture all records from *registry* into a new Snapshot."""
    taken_at = datetime.datetime.utcnow().isoformat()
    records = list(registry.all())
    return Snapshot(taken_at=taken_at, label=label, records=records)


def snapshot_to_dict(snapshot: Snapshot) -> Dict:
    """Serialise a Snapshot to a plain dict (JSON-safe)."""
    return {
        "taken_at": snapshot.taken_at,
        "label": snapshot.label,
        "records_json": records_to_json(snapshot.records),
    }


def snapshot_from_dict(data: Dict) -> Snapshot:
    """Deserialise a Snapshot from a plain dict produced by *snapshot_to_dict*."""
    records = records_from_json(data["records_json"])
    return Snapshot(
        taken_at=data["taken_at"],
        label=data.get("label"),
        records=records,
    )


def snapshot_to_registry(snapshot: Snapshot) -> MigrationRegistry:
    """Reconstruct a MigrationRegistry from a Snapshot (read-only convenience)."""
    reg = MigrationRegistry()
    for record in snapshot.records:
        reg.register(record)
    return reg
