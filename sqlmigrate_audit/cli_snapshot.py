"""CLI sub-commands for snapshot management."""

from __future__ import annotations

import argparse
import sys

from .exporter import import_registry
from .snapshot import take_snapshot, snapshot_to_registry
from .snapshot_store import SnapshotStore
from .differ import diff_registries, summarize_diff


def _cmd_take(args: argparse.Namespace) -> None:
    registry = import_registry(args.registry, fmt=args.format)
    store = SnapshotStore(args.store)
    snap = take_snapshot(registry, label=args.label)
    store.save(snap)
    print(f"Snapshot '{args.label}' saved to {args.store} ({len(snap.records)} records).")


def _cmd_list(args: argparse.Namespace) -> None:
    store = SnapshotStore(args.store)
    labels = store.list_labels()
    if not labels:
        print("No snapshots stored.")
        return
    for label in labels:
        snap = store.load(label)
        print(f"  {label}  ({snap.taken_at}, {len(snap.records)} records)")


def _cmd_diff(args: argparse.Namespace) -> None:
    store = SnapshotStore(args.store)
    try:
        snap_a = store.load(args.label_a)
        snap_b = store.load(args.label_b)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    reg_a = snapshot_to_registry(snap_a)
    reg_b = snapshot_to_registry(snap_b)
    entries = diff_registries(reg_a, reg_b)
    print(summarize_diff(entries))


def build_snapshot_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("snapshot", help="Manage registry snapshots")
    sp = p.add_subparsers(dest="snapshot_cmd", required=True)

    take_p = sp.add_parser("take", help="Take a snapshot of a registry file")
    take_p.add_argument("registry", help="Path to registry file")
    take_p.add_argument("--format", default="json", choices=["json", "csv"])
    take_p.add_argument("--store", required=True, help="Path to snapshot store file")
    take_p.add_argument("--label", required=True, help="Unique label for this snapshot")
    take_p.set_defaults(func=_cmd_take)

    list_p = sp.add_parser("list", help="List stored snapshots")
    list_p.add_argument("--store", required=True, help="Path to snapshot store file")
    list_p.set_defaults(func=_cmd_list)

    diff_p = sp.add_parser("diff", help="Diff two stored snapshots")
    diff_p.add_argument("--store", required=True, help="Path to snapshot store file")
    diff_p.add_argument("label_a", help="First snapshot label")
    diff_p.add_argument("label_b", help="Second snapshot label")
    diff_p.set_defaults(func=_cmd_diff)
