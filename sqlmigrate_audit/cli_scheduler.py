"""CLI sub-commands for the migration scheduler."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from sqlmigrate_audit.exporter import export_registry, import_registry
from sqlmigrate_audit.scheduler import (
    build_schedule,
    format_schedule,
    set_due_date,
    set_priority,
)


def _cmd_set_due(args: argparse.Namespace) -> None:
    try:
        registry = import_registry(args.file, fmt="json")
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    try:
        due = datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print("Error: date must be in YYYY-MM-DD format", file=sys.stderr)
        sys.exit(1)
    record = registry.get(args.migration_id)
    if record is None:
        print(f"Error: migration '{args.migration_id}' not found", file=sys.stderr)
        sys.exit(1)
    updated = set_due_date(record, due)
    registry.register(updated)
    export_registry(registry, args.file, fmt="json")
    print(f"Due date set to {args.date} for '{args.migration_id}'.")


def _cmd_set_priority(args: argparse.Namespace) -> None:
    try:
        registry = import_registry(args.file, fmt="json")
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    record = registry.get(args.migration_id)
    if record is None:
        print(f"Error: migration '{args.migration_id}' not found", file=sys.stderr)
        sys.exit(1)
    try:
        updated = set_priority(record, int(args.priority))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    registry.register(updated)
    export_registry(registry, args.file, fmt="json")
    print(f"Priority set to {args.priority} for '{args.migration_id}'.")


def _cmd_show_schedule(args: argparse.Namespace) -> None:
    try:
        registry = import_registry(args.file, fmt="json")
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    entries = build_schedule(registry)
    print(format_schedule(entries))


def build_scheduler_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("schedule", help="Manage migration schedule")
    sp = p.add_subparsers(dest="schedule_cmd", required=True)

    p_due = sp.add_parser("set-due", help="Set due date for a migration")
    p_due.add_argument("file")
    p_due.add_argument("migration_id")
    p_due.add_argument("date", help="YYYY-MM-DD")
    p_due.set_defaults(func=_cmd_set_due)

    p_pri = sp.add_parser("set-priority", help="Set priority for a migration")
    p_pri.add_argument("file")
    p_pri.add_argument("migration_id")
    p_pri.add_argument("priority", type=int)
    p_pri.set_defaults(func=_cmd_set_priority)

    p_show = sp.add_parser("show", help="Display migration schedule")
    p_show.add_argument("file")
    p_show.set_defaults(func=_cmd_show_schedule)
