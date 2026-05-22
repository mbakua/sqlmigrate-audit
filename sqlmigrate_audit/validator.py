"""Validation utilities for migration records and registries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .models import MigrationRecord, MigrationStatus
from .registry import MigrationRegistry


@dataclass
class ValidationIssue:
    migration_id: str
    field: str
    message: str

    def __repr__(self) -> str:
        return f"ValidationIssue({self.migration_id!r}, {self.field!r}: {self.message})"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue]

    @property
    def is_valid(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.is_valid:
            return "All migrations are valid."
        lines = [f"{len(self.issues)} issue(s) found:"]
        for issue in self.issues:
            lines.append(f"  [{issue.migration_id}] {issue.field}: {issue.message}")
        return "\n".join(lines)


def validate_record(record: MigrationRecord) -> List[ValidationIssue]:
    """Validate a single MigrationRecord and return a list of issues."""
    issues: List[ValidationIssue] = []

    if not record.migration_id or not record.migration_id.strip():
        issues.append(ValidationIssue(record.migration_id or "", "migration_id", "migration_id must not be empty"))

    if not record.description or not record.description.strip():
        issues.append(ValidationIssue(record.migration_id, "description", "description must not be empty"))

    if record.status == MigrationStatus.ROLLED_BACK and not record.rollback_sql:
        issues.append(ValidationIssue(record.migration_id, "rollback_sql",
                                       "rollback_sql is required for ROLLED_BACK status"))

    if record.applied_at and record.rolled_back_at:
        if record.rolled_back_at < record.applied_at:
            issues.append(ValidationIssue(record.migration_id, "rolled_back_at",
                                           "rolled_back_at must not be before applied_at"))

    return issues


def validate_registry(registry: MigrationRegistry) -> ValidationResult:
    """Validate all records in a registry and return a ValidationResult."""
    all_issues: List[ValidationIssue] = []
    for record in registry.all():
        all_issues.extend(validate_record(record))
    return ValidationResult(issues=all_issues)
