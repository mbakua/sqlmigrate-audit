"""CLI sub-commands for snapshot comparison."""
from __future__ import annotations

import argparse
import sys

from sqlmigrate_audit.snapshot_store import SnapshotStore
from sqlmigrate_audit.comparator import compare_snapshots, format_comparison


def _resolve_snapshot(snapshots: list, label: str):
    """Return the snapshot matching *label*, or print an error and exit."""
    match = next((s for s in snapshots if s.label == label), None)
    if match is None:
        print(f"Error: snapshot '{label}' not found.", file=sys.stderr)
        sys.exit(1)
    return match


def _cmd_compare(args: argparse.Namespace) -> None:
    store = SnapshotStore(args.store)
    snapshots = store.list()

    snap_a = _resolve_snapshot(snapshots, args.label_a)
    snap_b = _resolve_snapshot(snapshots, args.label_b)

    report = compare_snapshots(snap_a, snap_b)
    print(format_comparison(report))


def _cmd_compare_latest(args: argparse.Namespace) -> None:
    store = SnapshotStore(args.store)
    snapshots = store.list()

    if len(snapshots) < 2:
        print("Error: need at least two snapshots to compare.", file=sys.stderr)
        sys.exit(1)

    snap_a, snap_b = snapshots[-2], snapshots[-1]
    report = compare_snapshots(snap_a, snap_b)
    print(format_comparison(report))


def build_comparator_subparser(subparsers: argparse._SubParsersAction) -> None:
    p_compare = subparsers.add_parser(
        "compare", help="Compare two named snapshots"
    )
    p_compare.add_argument("store", help="Path to snapshot store JSON file")
    p_compare.add_argument("label_a", help="Label of the first (base) snapshot")
    p_compare.add_argument("label_b", help="Label of the second snapshot")
    p_compare.set_defaults(func=_cmd_compare)

    p_latest = subparsers.add_parser(
        "compare-latest", help="Compare the two most recent snapshots"
    )
    p_latest.add_argument("store", help="Path to snapshot store JSON file")
    p_latest.set_defaults(func=_cmd_compare_latest)
