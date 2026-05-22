"""CLI entry point for sqlmigrate-audit."""

from __future__ import annotations

import argparse
import sys

from sqlmigrate_audit.exporter import export_registry, import_registry
from sqlmigrate_audit.reporter import generate_report
from sqlmigrate_audit.validator import validate_registry


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        registry = import_registry(args.file, fmt="json")
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 2
    result = validate_registry(registry)
    if result.is_valid():
        print("Validation passed — no issues found.")
        return 0
    print(result.summary())
    return 1


def _cmd_export(args: argparse.Namespace) -> int:
    try:
        registry = import_registry(args.input, fmt="json")
    except FileNotFoundError:
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        return 2
    try:
        export_registry(registry, args.output, fmt=args.format)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Exported to {args.output} (format: {args.format})")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    try:
        registry = import_registry(args.file, fmt="json")
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 2
    title = args.title if args.title else "Migration Report"
    print(generate_report(registry, title=title))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlmigrate-audit",
        description="Track and annotate SQL migration history.",
    )
    sub = parser.add_subparsers(dest="command")

    p_validate = sub.add_parser("validate", help="Validate a JSON registry file.")
    p_validate.add_argument("file", help="Path to JSON registry file.")

    p_export = sub.add_parser("export", help="Export registry to another format.")
    p_export.add_argument("input", help="Input JSON registry file.")
    p_export.add_argument("output", help="Output file path.")
    p_export.add_argument("--format", default="csv", choices=["json", "csv"], dest="format")

    p_report = sub.add_parser("report", help="Print a human-readable migration report.")
    p_report.add_argument("file", help="Path to JSON registry file.")
    p_report.add_argument("--title", default="", help="Custom report title.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        return _cmd_validate(args)
    if args.command == "export":
        return _cmd_export(args)
    if args.command == "report":
        return _cmd_report(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
