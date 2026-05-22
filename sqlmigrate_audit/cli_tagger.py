"""CLI sub-commands for tag management, registered into the main CLI parser."""

import argparse
import json
from pathlib import Path

from .exporter import export_registry, import_registry
from .tagger import add_tag, remove_tag, list_all_tags, tag_counts


def _cmd_add_tag(args: argparse.Namespace) -> None:
    registry = import_registry(args.file, fmt=args.format)
    record = registry.get(args.migration_id)
    if record is None:
        print(f"ERROR: migration '{args.migration_id}' not found.")
        return
    updated = add_tag(record, args.tag)
    registry._records[args.migration_id] = updated  # type: ignore[attr-defined]
    export_registry(registry, args.file, fmt=args.format)
    print(f"Tag '{args.tag}' added to '{args.migration_id}'.")


def _cmd_remove_tag(args: argparse.Namespace) -> None:
    registry = import_registry(args.file, fmt=args.format)
    record = registry.get(args.migration_id)
    if record is None:
        print(f"ERROR: migration '{args.migration_id}' not found.")
        return
    updated = remove_tag(record, args.tag)
    registry._records[args.migration_id] = updated  # type: ignore[attr-defined]
    export_registry(registry, args.file, fmt=args.format)
    print(f"Tag '{args.tag}' removed from '{args.migration_id}'.")


def _cmd_list_tags(args: argparse.Namespace) -> None:
    registry = import_registry(args.file, fmt=args.format)
    tags = list_all_tags(registry)
    if not tags:
        print("No tags found.")
        return
    counts = tag_counts(registry)
    for tag in tags:
        print(f"  {tag}  ({counts[tag]} migration(s))")


def build_tag_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach tag sub-commands to an existing subparsers group."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--file", required=True, help="Registry file path")
    common.add_argument("--format", default="json", choices=["json", "csv"])

    p_add = subparsers.add_parser("add-tag", parents=[common], help="Add a tag to a migration")
    p_add.add_argument("migration_id")
    p_add.add_argument("tag")
    p_add.set_defaults(func=_cmd_add_tag)

    p_rm = subparsers.add_parser("remove-tag", parents=[common], help="Remove a tag from a migration")
    p_rm.add_argument("migration_id")
    p_rm.add_argument("tag")
    p_rm.set_defaults(func=_cmd_remove_tag)

    p_ls = subparsers.add_parser("list-tags", parents=[common], help="List all tags in a registry")
    p_ls.set_defaults(func=_cmd_list_tags)
