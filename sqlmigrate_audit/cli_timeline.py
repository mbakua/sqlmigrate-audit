"""CLI sub-commands for the timeline feature."""

from __future__ import annotations

import argparse
import sys

from .exporter import import_registry
from .models import MigrationStatus
from .timeline import build_timeline, format_timeline


def _cmd_timeline(args: argparse.Namespace) -> None:  # pragma: no cover
    """Load a registry file and print a formatted timeline."""
    try:
        registry = import_registry(args.file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading registry: {exc}", file=sys.stderr)
        sys.exit(1)

    status_filter = None
    if args.status:
        try:
            status_filter = MigrationStatus(args.status)
        except ValueError:
            valid = [s.value for s in MigrationStatus]
            print(
                f"Error: invalid status '{args.status}'. Choose from: {valid}",
                file=sys.stderr,
            )
            sys.exit(1)

    entries = build_timeline(registry, status_filter=status_filter)
    print(format_timeline(entries))


def build_timeline_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the 'timeline' sub-command to an existing subparsers group."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "timeline",
        help="Display a chronological timeline of migrations.",
    )
    parser.add_argument(
        "file",
        help="Path to a JSON registry file.",
    )
    parser.add_argument(
        "--status",
        default=None,
        metavar="STATUS",
        help=(
            "Filter by migration status. "
            "Choices: applied, pending, rolled_back, failed."
        ),
    )
    parser.set_defaults(func=_cmd_timeline)
