"""CLI for publishing a bounded ServiceTracer technician-handoff report."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import socket

from .report_publication import (
    DEFAULT_BLOB_PATH,
    DEFAULT_CONTAINER,
    DEFAULT_TTL_SECONDS,
    PublicationError,
    build_public_envelope,
    publish_to_azure_blob,
    write_public_envelope,
)


def _package_version() -> str:
    try:
        return version("servicetracer")
    except PackageNotFoundError:
        return "0.5.0-dev"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Sanitize and publish a ServiceTracer technician-handoff report. "
            "Unexpected analyzer fields are dropped before publication."
        )
    )
    parser.add_argument("--input", required=True, help="Technician-handoff report JSON")
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument(
        "--output",
        help="Write the public envelope to a local JSON path",
    )
    destination.add_argument(
        "--storage-account",
        help="Azure Storage account used for managed-identity Blob publication",
    )
    parser.add_argument(
        "--container",
        default=DEFAULT_CONTAINER,
        help=f"Azure Blob container (default: {DEFAULT_CONTAINER})",
    )
    parser.add_argument(
        "--blob-path",
        default=DEFAULT_BLOB_PATH,
        help=f"Azure Blob path (default: {DEFAULT_BLOB_PATH})",
    )
    parser.add_argument(
        "--managed-identity-client-id",
        help="Optional user-assigned managed identity client ID",
    )
    parser.add_argument(
        "--source-id",
        default=socket.gethostname(),
        help="Non-secret collector identifier included in provenance metadata",
    )
    parser.add_argument(
        "--ttl-seconds",
        type=int,
        default=DEFAULT_TTL_SECONDS,
        help="Freshness lifetime between 60 and 86400 seconds",
    )
    parser.add_argument(
        "--servicetracer-version",
        default=_package_version(),
        help="Version recorded in report provenance",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        report = json.loads(Path(args.input).read_text(encoding="utf-8"))
        envelope = build_public_envelope(
            report,
            source_id=args.source_id,
            servicetracer_version=args.servicetracer_version,
            ttl_seconds=args.ttl_seconds,
        )
        if args.output:
            destination = write_public_envelope(args.output, envelope)
            result = {
                "status": "written",
                "destination": str(destination),
                "schema_version": envelope["schema_version"],
                "expires_at": envelope["expires_at"],
            }
        else:
            destination = publish_to_azure_blob(
                envelope,
                storage_account=args.storage_account,
                container=args.container,
                blob_path=args.blob_path,
                managed_identity_client_id=args.managed_identity_client_id,
            )
            result = {
                "status": "published",
                "destination": destination,
                "schema_version": envelope["schema_version"],
                "expires_at": envelope["expires_at"],
            }
    except (OSError, json.JSONDecodeError, PublicationError) as exc:
        parser.error(str(exc))

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
