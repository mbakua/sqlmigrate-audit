"""Core data models for SQL migration audit entries."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MigrationStatus(str, Enum):
    PENDING = "pending"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class MigrationRecord:
    """Represents a single SQL migration with audit metadata."""

    migration_id: str
    filename: str
    checksum: str
    applied_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None
    status: MigrationStatus = MigrationStatus.PENDING
    rollback_sql: Optional[str] = None
    description: Optional[str] = None
    applied_by: Optional[str] = None
    execution_time_ms: Optional[float] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "migration_id": self.migration_id,
            "filename": self.filename,
            "checksum": self.checksum,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "rolled_back_at": self.rolled_back_at.isoformat() if self.rolled_back_at else None,
            "status": self.status.value,
            "rollback_sql": self.rollback_sql,
            "description": self.description,
            "applied_by": self.applied_by,
            "execution_time_ms": self.execution_time_ms,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MigrationRecord":
        record = cls(
            migration_id=data["migration_id"],
            filename=data["filename"],
            checksum=data["checksum"],
            status=MigrationStatus(data.get("status", "pending")),
            rollback_sql=data.get("rollback_sql"),
            description=data.get("description"),
            applied_by=data.get("applied_by"),
            execution_time_ms=data.get("execution_time_ms"),
            tags=data.get("tags", []),
        )
        if data.get("applied_at"):
            record.applied_at = datetime.fromisoformat(data["applied_at"])
        if data.get("rolled_back_at"):
            record.rolled_back_at = datetime.fromisoformat(data["rolled_back_at"])
        return record
