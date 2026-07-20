"""Command-line entry point for ServiceTracer operational collectors."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

from .collector import (
    DEFAULT_MAX_HTTP_BODY_BYTES,
    DEFAULT_MAX_RECORD_BYTES,
    JsonlSpool,
    StructuredSyslogTCPServer,
    StructuredSyslogUDPServer,
    build_http_server,
    load_collector_records,
    write_receipt,
)


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def _port(value: str) -> int:
    parsed = int(value)
    if parsed < 0 or parsed > 65535:
        raise argparse.ArgumentTypeError("port must be between 0 and 65535")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect structured operational evidence for ServiceTracer"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser(
        "ingest", help="Append JSON, JSON-array, or JSONL records to a durable spool"
    )
    ingest.add_argument("--spool", required=True, help="Destination JSONL spool")
    ingest.add_argument(
        "--input",
        action="append",
        required=True,
        help="Input JSON or JSONL file. Repeat for multiple files.",
    )
    ingest.add_argument(
        "--max-record-bytes",
        type=_positive_int,
        default=DEFAULT_MAX_RECORD_BYTES,
    )

    status = subparsers.add_parser("status", help="Inspect a collector spool")
    status.add_argument("--spool", required=True)
    status.add_argument(
        "--max-record-bytes",
        type=_positive_int,
        default=DEFAULT_MAX_RECORD_BYTES,
    )

    http = subparsers.add_parser(
        "http", help="Run the authenticated HTTP or HTTPS collector"
    )
    http.add_argument("--spool", required=True)
    http.add_argument("--listen", default="127.0.0.1")
    http.add_argument("--port", type=_port, default=8080)
    http.add_argument(
        "--token-env",
        default="SERVICETRACER_COLLECTOR_TOKEN",
        help="Environment variable containing the bearer token",
    )
    http.add_argument(
        "--allow-unauthenticated",
        action="store_true",
        help="Allow requests without a bearer token. Intended only for isolated local tests.",
    )
    http.add_argument("--tls-cert", help="PEM certificate for HTTPS")
    http.add_argument("--tls-key", help="PEM private key for HTTPS")
    http.add_argument(
        "--max-record-bytes",
        type=_positive_int,
        default=DEFAULT_MAX_RECORD_BYTES,
    )
    http.add_argument(
        "--max-body-bytes",
        type=_positive_int,
        default=DEFAULT_MAX_HTTP_BODY_BYTES,
    )

    syslog = subparsers.add_parser(
        "syslog",
        help=(
            "Run a local structured-syslog receiver. Messages must contain "
            "'@servicetracer ' followed by a JSON source record."
        ),
    )
    syslog.add_argument("--spool", required=True)
    syslog.add_argument("--listen", default="127.0.0.1")
    syslog.add_argument("--port", type=_port, default=5514)
    syslog.add_argument("--transport", choices=("udp", "tcp"), default="tcp")
    syslog.add_argument(
        "--max-record-bytes",
        type=_positive_int,
        default=DEFAULT_MAX_RECORD_BYTES,
    )

    return parser


def _print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _run_ingest(args: argparse.Namespace) -> int:
    spool = JsonlSpool(args.spool, max_record_bytes=args.max_record_bytes)
    receipt = spool.append(load_collector_records(args.input))
    write_receipt(receipt, sys.stdout)
    return 0


def _run_status(args: argparse.Namespace) -> int:
    spool = JsonlSpool(args.spool, max_record_bytes=args.max_record_bytes)
    _print_json(spool.status())
    return 0


def _run_http(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    token = os.getenv(args.token_env)
    if not token and not args.allow_unauthenticated:
        parser.error(
            f"{args.token_env} must contain a bearer token unless "
            "--allow-unauthenticated is explicitly set"
        )
    if bool(args.tls_cert) != bool(args.tls_key):
        parser.error("--tls-cert and --tls-key must be supplied together")

    spool = JsonlSpool(args.spool, max_record_bytes=args.max_record_bytes)
    server = build_http_server(
        spool,
        args.listen,
        args.port,
        bearer_token=token,
        max_body_bytes=args.max_body_bytes,
        tls_cert=args.tls_cert,
        tls_key=args.tls_key,
    )
    scheme = "https" if args.tls_cert else "http"
    _print_json(
        {
            "status": "listening",
            "transport": scheme,
            "address": server.server_address[0],
            "port": server.server_address[1],
            "spool": str(Path(args.spool)),
            "authenticated": token is not None,
        }
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def _run_syslog(args: argparse.Namespace) -> int:
    spool = JsonlSpool(args.spool, max_record_bytes=args.max_record_bytes)
    server_class = (
        StructuredSyslogUDPServer
        if args.transport == "udp"
        else StructuredSyslogTCPServer
    )
    server = server_class(
        (args.listen, args.port),
        spool,
        max_message_bytes=args.max_record_bytes,
    )
    _print_json(
        {
            "status": "listening",
            "transport": f"syslog-{args.transport}",
            "address": server.server_address[0],
            "port": server.server_address[1],
            "spool": str(Path(args.spool)),
            "structured_marker": "@servicetracer ",
        }
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "ingest":
            return _run_ingest(args)
        if args.command == "status":
            return _run_status(args)
        if args.command == "http":
            return _run_http(args, parser)
        if args.command == "syslog":
            return _run_syslog(args)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    raise AssertionError(f"Unhandled collector command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
