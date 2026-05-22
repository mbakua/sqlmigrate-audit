"""In-memory and file-backed registry for migration audit records."""

import hashlib
import json
from pathlib import Path
from typing import Optional

from .models import MigrationRecord, MigrationStatus


class MigrationRegistry:
    """Manages the collection of migration audit records."""

    def __init__(self, storage_path: Optional[Path] = None):
        self._records: dict[str, MigrationRecord] = {}
        self.storage_path = storage_path
        if storage_path and Path(storage_path).exists():
            self._load()

    def register(self, record: MigrationRecord) -> None:
        """Add or update a migration record in the registry."""
        self._records[record.migration_id] = record
        if self.storage_path:
            self._save()

    def get(self, migration_id: str) -> Optional[MigrationRecord]:
        return self._records.get(migration_id)

    def all(self) -> list[MigrationRecord]:
        return list(self._records.values())

    def by_status(self, status: MigrationStatus) -> list[MigrationRecord]:
        return [r for r in self._records.values() if r.status == status]

    def remove(self, migration_id: str) -> bool:
        if migration_id in self._records:
            del self._records[migration_id]
            if self.storage_path:
                self._save()
            return True
        return False

    @staticmethod
    def compute_checksum(sql: str) -> str:
        return hashlib.sha256(sql.encode()).hexdigest()

    def _save(self) -> None:
        data = {mid: rec.to_dict() for mid, rec in self._records.items()}
        Path(self.storage_path).write_text(json.dumps(data, indent=2))

    def _load(self) -> None:
        raw = json.loads(Path(self.storage_path).read_text())
        self._records = {
            mid: MigrationRecord.from_dict(rec) for mid, rec in raw.items()
        }

    def __len__(self) -> int:
        return len(self._records)

    def __contains__(self, migration_id: str) -> bool:
        return migration_id in self._records
