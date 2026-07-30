from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .catalog import CatalogError, list_profiles, load_catalog, prepare_lab_plan


def _parameter(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("parameters must use NAME=VALUE")
    name, parameter_value = value.split("=", 1)
    if not name or not parameter_value:
        raise argparse.ArgumentTypeError("parameters must use non-empty NAME=VALUE")
    return name, parameter_value


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="azure-lab-factory-lite",
        description="List fixed Azure lab profiles and prepare deterministic, non-executing lab plans.",
    )
    parser.add_argument("--catalog", type=Path, help="Optional catalog path.")
    parser.add_argument("--repository-root", type=Path, help="Repository root used to resolve templates.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List bounded lab profiles.")

    prepare = subparsers.add_parser("prepare", help="Prepare a lab request without querying or mutating Azure.")
    prepare.add_argument(
        "--catalog",
        dest="command_catalog",
        type=Path,
        help="Optional catalog path when supplied after the prepare command.",
    )
    prepare.add_argument(
        "--repository-root",
        dest="command_repository_root",
        type=Path,
        help="Repository root when supplied after the prepare command.",
    )
    prepare.add_argument("--profile", required=True)
    prepare.add_argument("--version")
    prepare.add_argument("--environment", default="dev")
    prepare.add_argument("--location")
    prepare.add_argument("--ttl-hours", type=int)
    prepare.add_argument("--request-id")
    prepare.add_argument(
        "--parameter",
        action="append",
        default=[],
        type=_parameter,
        metavar="NAME=VALUE",
        help="Supply an approved profile parameter. Values are validated but not echoed in the plan.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    command_catalog = getattr(args, "command_catalog", None)
    command_repository_root = getattr(args, "command_repository_root", None)
    catalog_path = command_catalog or args.catalog
    repository_root = command_repository_root or args.repository_root
    try:
        catalog = load_catalog(catalog_path, repository_root=repository_root)
        if args.command == "list":
            result = {
                "schema_version": "lab-factory.profile-list.v1",
                "profiles": list_profiles(catalog),
                "execution": {
                    "azure_queries_performed": False,
                    "azure_mutations_performed": False,
                },
            }
        else:
            supplied: dict[str, str] = {}
            for name, value in args.parameter:
                if name in supplied:
                    raise CatalogError(f"parameter supplied more than once: {name}")
                supplied[name] = value
            result = prepare_lab_plan(
                catalog,
                profile_id=args.profile,
                version=args.version,
                environment=args.environment,
                location=args.location,
                ttl_hours=args.ttl_hours,
                parameters=supplied,
                request_id=args.request_id,
                repository_root=repository_root,
            )
    except CatalogError as exc:
        print(
            json.dumps(
                {
                    "schema_version": "lab-factory.error.v1",
                    "error": str(exc),
                    "azure_queries_performed": False,
                    "azure_mutations_performed": False,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
