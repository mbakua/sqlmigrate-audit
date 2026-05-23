"""CLI sub-commands for annotating migration records."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from .annotator import annotate_in_registry, get_annotations
from .exporter import export_registry, import_registry


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _cmd_add_note(args: argparse.Namespace) -> int:
    """Add a note annotation to a migration in a registry file."""
    try:
        registry = import_registry(args.file, fmt="json")
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading registry: {exc}", file=sys.stderr)
        return 1

    created_at = args.at if args.at else _now_iso()

    try:
        updated_registry = annotate_in_registry(
            registry,
            migration_id=args.migration_id,
            author=args.author,
            note=args.note,
            created_at=created_at,
        )
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        return 1

    export_registry(updated_registry, args.file, fmt="json")
    print(f"Annotation added to '{args.migration_id}' by {args.author}.")
    return 0


def _cmd_list_notes(args: argparse.Namespace) -> int:
    """List all annotations on a specific migration."""
    try:
        registry = import_registry(args.file, fmt="json")
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    record = registry.get(args.migration_id)
    if record is None:
        print(f"Error: migration '{args.migration_id}' not found.", file=sys.stderr)
        return 1

    annotations = get_annotations(record)
    if not annotations:
        print(f"No annotations for '{args.migration_id}'.")
        return 0

    print(f"Annotations for '{args.migration_id}':")
    for ann in annotations:
        print(f"  [{ann.created_at}] {ann.author}: {ann.note}")
    return 0


def build_annotator_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register 'add-note' and 'list-notes' sub-commands onto *subparsers*."""
    # add-note
    p_add = subparsers.add_parser("add-note", help="Annotate a migration with a note")
    p_add.add_argument("file", help="Path to the JSON registry file")
    p_add.add_argument("migration_id", help="ID of the migration to annotate")
    p_add.add_argument("author", help="Name of the person adding the note")
    p_add.add_argument("note", help="The note text")
    p_add.add_argument("--at", default="", help="ISO-8601 timestamp (default: now)")
    p_add.set_defaults(func=_cmd_add_note)

    # list-notes
    p_list = subparsers.add_parser("list-notes", help="List annotations on a migration")
    p_list.add_argument("file", help="Path to the JSON registry file")
    p_list.add_argument("migration_id", help="ID of the migration to inspect")
    p_list.set_defaults(func=_cmd_list_notes)
