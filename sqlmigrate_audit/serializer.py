"""Serialization utilities for migration records (JSON and CSV)."""

import csv
import io
import json
from typing import List

from sqlmigrate_audit.models import MigrationRecord, from_dict


def records_to_json(records: List[MigrationRecord], indent: int = 2) -> str:
    """Serialize a list of MigrationRecord objects to a JSON string."""
    return json.dumps([r.to_dict() for r in records], indent=indent, default=str)


def records_from_json(data: str) -> List[MigrationRecord]:
    """Deserialize a JSON string into a list of MigrationRecord objects."""
    raw = json.loads(data)
    if not isinstance(raw, list):
        raise ValueError("Expected a JSON array of migration records.")
    return [from_dict(item) for item in raw]


def records_to_csv(records: List[MigrationRecord]) -> str:
    """Serialize a list of MigrationRecord objects to a CSV string."""
    if not records:
        return ""

    output = io.StringIO()
    fieldnames = list(records[0].to_dict().keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for record in records:
        writer.writerow(record.to_dict())
    return output.getvalue()


def records_from_csv(data: str) -> List[MigrationRecord]:
    """Deserialize a CSV string into a list of MigrationRecord objects."""
    reader = csv.DictReader(io.StringIO(data))
    records = []
    for row in reader:
        # Convert empty strings to None for optional fields
        cleaned = {k: (v if v != "" else None) for k, v in row.items()}
        records.append(from_dict(cleaned))
    return records
