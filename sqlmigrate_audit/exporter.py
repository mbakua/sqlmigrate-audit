"""Export migration registry contents to files on disk."""

import os
from typing import Literal

from sqlmigrate_audit.registry import MigrationRegistry
from sqlmigrate_audit.serializer import records_to_csv, records_to_json

ExportFormat = Literal["json", "csv"]


def export_registry(
    registry: MigrationRegistry,
    path: str,
    fmt: ExportFormat = "json",
) -> str:
    """
    Export all records in the registry to a file.

    Args:
        registry: The MigrationRegistry instance to export.
        path:     Destination file path (directory must exist).
        fmt:      Output format — 'json' or 'csv'.

    Returns:
        The absolute path of the written file.

    Raises:
        ValueError: If an unsupported format is requested.
    """
    records = registry.all()

    if fmt == "json":
        content = records_to_json(records)
    elif fmt == "csv":
        content = records_to_csv(records)
    else:
        raise ValueError(f"Unsupported export format: '{fmt}'. Use 'json' or 'csv'.")

    abs_path = os.path.abspath(path)
    with open(abs_path, "w", encoding="utf-8") as fh:
        fh.write(content)

    return abs_path


def import_registry(
    registry: MigrationRegistry,
    path: str,
    fmt: ExportFormat = "json",
    overwrite: bool = False,
) -> int:
    """
    Import records from a file into the registry.

    Args:
        registry:  Target MigrationRegistry.
        path:      Source file path.
        fmt:       File format — 'json' or 'csv'.
        overwrite: If True, existing records with the same migration_id
                   are replaced; otherwise they are skipped.

    Returns:
        Number of records imported.
    """
    from sqlmigrate_audit.serializer import records_from_csv, records_from_json

    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    if fmt == "json":
        records = records_from_json(content)
    elif fmt == "csv":
        records = records_from_csv(content)
    else:
        raise ValueError(f"Unsupported import format: '{fmt}'. Use 'json' or 'csv'.")

    imported = 0
    for record in records:
        existing = registry.get(record.migration_id)
        if existing is not None and not overwrite:
            continue
        registry.register(record)
        imported += 1

    return imported
