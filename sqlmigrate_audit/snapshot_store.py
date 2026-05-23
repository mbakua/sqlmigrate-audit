"""Persist and load named snapshots to/from a JSON file."""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from .snapshot import Snapshot, snapshot_to_dict, snapshot_from_dict


class SnapshotStore:
    """Simple file-backed store for multiple named snapshots."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._data: Dict[str, dict] = {}
        if os.path.exists(path):
            self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        with open(self._path, "r", encoding="utf-8") as fh:
            self._data = json.load(fh)

    def _save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(self, snapshot: Snapshot) -> None:
        """Persist *snapshot*. Uses its label as key; raises if label is None."""
        if not snapshot.label:
            raise ValueError("Snapshot must have a label to be stored.")
        self._data[snapshot.label] = snapshot_to_dict(snapshot)
        self._save()

    def load(self, label: str) -> Snapshot:
        """Load a snapshot by *label*. Raises KeyError if not found."""
        if label not in self._data:
            raise KeyError(f"No snapshot with label '{label}'.")
        return snapshot_from_dict(self._data[label])

    def list_labels(self) -> List[str]:
        """Return all stored snapshot labels, sorted alphabetically."""
        return sorted(self._data.keys())

    def delete(self, label: str) -> None:
        """Remove a snapshot by *label*. Raises KeyError if not found."""
        if label not in self._data:
            raise KeyError(f"No snapshot with label '{label}'.")
        del self._data[label]
        self._save()
