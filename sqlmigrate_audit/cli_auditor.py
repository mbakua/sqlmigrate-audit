"""CLI commands for the audit log feature."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from sqlmigrate_audit.auditor import (
    AuditEvent,
    events_by_actor,
    events_for_migration,
    format_audit_log,
    record_event,
)


# ---------------------------------------------------------------------------
# Persistence helpers (simple JSON file)
# ---------------------------------------------------------------------------

def _load_log(path: str) -> List[AuditEvent]:
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    return [AuditEvent.from_dict(d) for d in data]


def _save_log(path: str, log: List[AuditEvent]) -> None:
    Path(path).write_text(json.dumps([e.to_dict() for e in log], indent=2))


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def _cmd_log_event(args: argparse.Namespace) -> None:
    log = _load_log(args.log_file)
    event = record_event(
        log,
        migration_id=args.migration_id,
        action=args.action,
        actor=args.actor,
        note=args.note or None,
    )
    _save_log(args.log_file, log)
    print(f"Recorded: {event.action} on {event.migration_id} by {event.actor} at {event.timestamp}")


def _cmd_show_log(args: argparse.Namespace) -> None:
    log = _load_log(args.log_file)

    if args.migration_id:
        log = events_for_migration(log, args.migration_id)
    if args.actor:
        log = events_by_actor(log, args.actor)

    print(format_audit_log(log))


# ---------------------------------------------------------------------------
# Parser builder
# ---------------------------------------------------------------------------

def build_auditor_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    audit_p = subparsers.add_parser("audit", help="Manage the migration audit log")
    audit_sub = audit_p.add_subparsers(dest="audit_cmd", required=True)

    # log-event
    log_p = audit_sub.add_parser("log", help="Record an audit event")
    log_p.add_argument("log_file", help="Path to the audit log JSON file")
    log_p.add_argument("migration_id", help="Migration ID the event relates to")
    log_p.add_argument("action", help="Action performed (e.g. applied, rolled_back)")
    log_p.add_argument("actor", help="Name or identifier of the person/system")
    log_p.add_argument("--note", default="", help="Optional free-text note")
    log_p.set_defaults(func=_cmd_log_event)

    # show
    show_p = audit_sub.add_parser("show", help="Display the audit log")
    show_p.add_argument("log_file", help="Path to the audit log JSON file")
    show_p.add_argument("--migration-id", dest="migration_id", default="", help="Filter by migration ID")
    show_p.add_argument("--actor", default="", help="Filter by actor")
    show_p.set_defaults(func=_cmd_show_log)
