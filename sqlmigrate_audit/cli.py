"""Minimal CLI entry point for sqlmigrate-audit."""

from __future__ import annotations

import argparse
import sys

from .exporter import export_registry, import_registry
from .validator import validate_registry


def _cmd_validate(args: argparse.Namespace) -> int:
    """Load a registry file and validate all records."""
    try:
        fmt = args.format
        registry = import_registry(args.file, fmt)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading registry: {exc}", file=sys.stderr)
        return 1

    result = validate_registry(registry)
    print(result.summary())
    return 0 if result.is_valid else 2


def _cmd_export(args: argparse.Namespace) -> int:
    """Export a registry file to another format."""
    try:
        fmt_in = args.input_format
        fmt_out = args.output_format
        registry = import_registry(args.input, fmt_in)
        export_registry(registry, args.output, fmt_out)
        print(f"Exported {len(registry.all())} record(s) to '{args.output}' as {fmt_out}.")
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlmigrate-audit",
        description="Track and annotate SQL migration history.",
    )
    sub = parser.add_subparsers(dest="command")

    # validate sub-command
    p_validate = sub.add_parser("validate", help="Validate a migration registry file")
    p_validate.add_argument("file", help="Path to registry file")
    p_validate.add_argument("--format", choices=["json", "csv"], default="json",
                             help="File format (default: json)")
    p_validate.set_defaults(func=_cmd_validate)

    # export sub-command
    p_export = sub.add_parser("export", help="Convert a registry between formats")
    p_export.add_argument("input", help="Input registry file")
    p_export.add_argument("output", help="Output registry file")
    p_export.add_argument("--input-format", choices=["json", "csv"], default="json")
    p_export.add_argument("--output-format", choices=["json", "csv"], default="csv")
    p_export.set_defaults(func=_cmd_export)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
