"""Operational collectors for durable ServiceTracer evidence ingestion.

Collectors accept structured source records and append the original records to a JSONL
spool. They do not infer service stages or alter source evidence. The existing adapter
and transaction-assembly layer performs those responsibilities later.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import hmac
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socketserver
import ssl
import threading
from typing import Any, Iterable, TextIO

STRUCTURED_SYSLOG_MARKER = "@servicetracer "
DEFAULT_MAX_RECORD_BYTES = 1_048_576
DEFAULT_MAX_HTTP_BODY_BYTES = 8_388_608


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _record_identity(record: dict[str, Any]) -> str:
    event_id = record.get("event_id")
    if event_id is not None:
        identity = str(event_id).strip()
        if not identity:
            raise ValueError("event_id must not be empty when present")
        return identity
    return f"{record['source_type']}:{_fingerprint(record)[:24]}"


def validate_source_record(
    record: Any,
    *,
    max_record_bytes: int = DEFAULT_MAX_RECORD_BYTES,
) -> dict[str, Any]:
    """Validate the collector boundary without interpreting the source record."""
    if not isinstance(record, dict):
        raise ValueError("Collector records must be JSON objects")

    source_type = str(record.get("source_type", "")).strip()
    if not source_type:
        raise ValueError("Collector record is missing source_type")

    event_discriminator = record.get("event", record.get("event_type", record.get("record_type")))
    if event_discriminator is None or not str(event_discriminator).strip():
        raise ValueError("Collector record must contain event, event_type, or record_type")

    encoded = _canonical_json(record).encode("utf-8")
    if len(encoded) > max_record_bytes:
        raise ValueError(
            f"Collector record exceeds maximum size of {max_record_bytes} bytes"
        )

    _record_identity(record)
    return record


@dataclass(frozen=True)
class CollectorReceipt:
    received_at: str
    records_received: int
    records_accepted: int
    idempotent_duplicates: int
    spool_path: str
    accepted_identities: tuple[str, ...]
    duplicate_identities: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class JsonlSpool:
    """Single-writer durable JSONL spool with evidence-identity protection."""

    def __init__(
        self,
        path: str | Path,
        *,
        max_record_bytes: int = DEFAULT_MAX_RECORD_BYTES,
    ) -> None:
        self.path = Path(path)
        self.max_record_bytes = max_record_bytes
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def _load_index(self) -> tuple[dict[str, str], int]:
        identities: dict[str, str] = {}
        record_count = 0
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Spool contains invalid JSON on line {line_number}: {exc}"
                    ) from exc
                validate_source_record(record, max_record_bytes=self.max_record_bytes)
                identity = _record_identity(record)
                fingerprint = _fingerprint(record)
                existing = identities.get(identity)
                if existing and existing != fingerprint:
                    raise ValueError(
                        f"Spool contains divergent content for evidence identity {identity}"
                    )
                identities[identity] = fingerprint
                record_count += 1
        return identities, record_count

    def append(self, records: Iterable[dict[str, Any]]) -> CollectorReceipt:
        """Validate and append a batch atomically from the collector's perspective."""
        batch = [
            validate_source_record(record, max_record_bytes=self.max_record_bytes)
            for record in records
        ]
        if not batch:
            raise ValueError("Collector batch must contain at least one record")

        with self._lock:
            identities, _ = self._load_index()
            accepted: list[tuple[str, dict[str, Any], str]] = []
            duplicates: list[str] = []
            pending: dict[str, str] = {}

            for record in batch:
                identity = _record_identity(record)
                fingerprint = _fingerprint(record)
                existing = identities.get(identity, pending.get(identity))
                if existing:
                    if existing != fingerprint:
                        raise ValueError(
                            f"Evidence identity {identity} was reused with different content"
                        )
                    duplicates.append(identity)
                    continue
                pending[identity] = fingerprint
                accepted.append((identity, record, fingerprint))

            if accepted:
                with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                    for _, record, _ in accepted:
                        handle.write(_canonical_json(record))
                        handle.write("\n")
                    handle.flush()
                    os.fsync(handle.fileno())

            return CollectorReceipt(
                received_at=_utc_now(),
                records_received=len(batch),
                records_accepted=len(accepted),
                idempotent_duplicates=len(duplicates),
                spool_path=str(self.path),
                accepted_identities=tuple(item[0] for item in accepted),
                duplicate_identities=tuple(duplicates),
            )

    def status(self) -> dict[str, Any]:
        with self._lock:
            identities, record_count = self._load_index()
            stat = self.path.stat()
            return {
                "status": "ready",
                "spool_path": str(self.path),
                "records": record_count,
                "unique_evidence_identities": len(identities),
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(
                    stat.st_mtime, timezone.utc
                ).isoformat().replace("+00:00", "Z"),
                "max_record_bytes": self.max_record_bytes,
            }


def load_collector_records(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    """Load JSON, JSON arrays, or JSONL files for durable collector ingestion."""
    records: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path)
        text = path.read_text(encoding="utf-8")
        stripped = text.lstrip()
        if not stripped:
            continue

        if path.suffix.lower() == ".jsonl":
            for line_number, line in enumerate(text.splitlines(), start=1):
                value = line.strip()
                if not value:
                    continue
                try:
                    payload = json.loads(value)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSON in {path} line {line_number}: {exc}"
                    ) from exc
                if not isinstance(payload, dict):
                    raise ValueError(
                        f"Collector record in {path} line {line_number} must be an object"
                    )
                records.append(payload)
            continue

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
        if isinstance(payload, dict):
            records.append(payload)
        elif isinstance(payload, list):
            if not all(isinstance(item, dict) for item in payload):
                raise ValueError(f"Collector JSON array in {path} must contain only objects")
            records.extend(payload)
        else:
            raise ValueError(f"Collector input {path} must contain an object or array")
    return records


def extract_structured_syslog_record(message: str) -> dict[str, Any]:
    """Extract a structured record from an RFC3164/RFC5424 message payload.

    Vendor-specific parsing is deliberately outside this collector. A local parser,
    rsyslog template, or appliance integration emits the marker followed by JSON.
    """
    marker_index = message.find(STRUCTURED_SYSLOG_MARKER)
    if marker_index < 0:
        raise ValueError("Syslog message does not contain a ServiceTracer JSON marker")
    payload_text = message[marker_index + len(STRUCTURED_SYSLOG_MARKER) :].strip()
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Structured syslog payload is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Structured syslog payload must be a JSON object")
    return payload


class CollectorHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        spool: JsonlSpool,
        *,
        bearer_token: str | None,
        max_body_bytes: int = DEFAULT_MAX_HTTP_BODY_BYTES,
    ) -> None:
        self.spool = spool
        self.bearer_token = bearer_token
        self.max_body_bytes = max_body_bytes
        super().__init__(server_address, CollectorRequestHandler)


class CollectorRequestHandler(BaseHTTPRequestHandler):
    server: CollectorHTTPServer
    server_version = "ServiceTracerCollector/0.3"

    def log_message(self, format: str, *args: Any) -> None:
        # Avoid logging request bodies or authorization values. Standard access details
        # remain available to a supervising reverse proxy when one is used.
        return

    def _authorized(self) -> bool:
        expected = self.server.bearer_token
        if expected is None:
            return True
        supplied = self.headers.get("Authorization", "")
        prefix = "Bearer "
        if not supplied.startswith(prefix):
            return False
        return hmac.compare_digest(supplied[len(prefix) :], expected)

    def _write_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._write_json(HTTPStatus.OK, {"status": "ok"})
            return
        if self.path == "/v1/status":
            if not self._authorized():
                self._write_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            self._write_json(HTTPStatus.OK, self.server.spool.status())
            return
        self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/v1/records":
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        if not self._authorized():
            self._write_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            return

        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            self._write_json(HTTPStatus.LENGTH_REQUIRED, {"error": "content_length_required"})
            return
        try:
            content_length = int(raw_length)
        except ValueError:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_content_length"})
            return
        if content_length < 1 or content_length > self.server.max_body_bytes:
            self._write_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "body_too_large"})
            return

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            if isinstance(payload, dict):
                records = [payload]
            elif isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
                records = payload
            else:
                raise ValueError("Request body must be a record object or array of record objects")
            receipt = self.server.spool.append(records)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        self._write_json(HTTPStatus.ACCEPTED, receipt.to_dict())


def build_http_server(
    spool: JsonlSpool,
    host: str,
    port: int,
    *,
    bearer_token: str | None,
    max_body_bytes: int = DEFAULT_MAX_HTTP_BODY_BYTES,
    tls_cert: str | Path | None = None,
    tls_key: str | Path | None = None,
) -> CollectorHTTPServer:
    if bool(tls_cert) != bool(tls_key):
        raise ValueError("TLS certificate and key must be supplied together")
    server = CollectorHTTPServer(
        (host, port),
        spool,
        bearer_token=bearer_token,
        max_body_bytes=max_body_bytes,
    )
    if tls_cert and tls_key:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(certfile=str(tls_cert), keyfile=str(tls_key))
        server.socket = context.wrap_socket(server.socket, server_side=True)
    return server


class _StructuredSyslogMixin:
    spool: JsonlSpool
    max_message_bytes: int

    def ingest_message(self, raw: bytes) -> CollectorReceipt:
        if len(raw) > self.max_message_bytes:
            raise ValueError("Syslog message exceeds configured maximum size")
        message = raw.decode("utf-8")
        record = extract_structured_syslog_record(message)
        return self.spool.append([record])


class StructuredSyslogUDPServer(_StructuredSyslogMixin, socketserver.ThreadingUDPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        spool: JsonlSpool,
        *,
        max_message_bytes: int = DEFAULT_MAX_RECORD_BYTES,
    ) -> None:
        self.spool = spool
        self.max_message_bytes = max_message_bytes
        super().__init__(server_address, StructuredSyslogUDPHandler)


class StructuredSyslogUDPHandler(socketserver.BaseRequestHandler):
    server: StructuredSyslogUDPServer

    def handle(self) -> None:
        raw = self.request[0]
        try:
            self.server.ingest_message(raw)
        except (UnicodeDecodeError, ValueError):
            return


class StructuredSyslogTCPServer(_StructuredSyslogMixin, socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        spool: JsonlSpool,
        *,
        max_message_bytes: int = DEFAULT_MAX_RECORD_BYTES,
    ) -> None:
        self.spool = spool
        self.max_message_bytes = max_message_bytes
        super().__init__(server_address, StructuredSyslogTCPHandler)


class StructuredSyslogTCPHandler(socketserver.StreamRequestHandler):
    server: StructuredSyslogTCPServer

    def handle(self) -> None:
        while True:
            raw = self.rfile.readline(self.server.max_message_bytes + 1)
            if not raw:
                return
            if len(raw) > self.server.max_message_bytes:
                return
            try:
                self.server.ingest_message(raw.rstrip(b"\r\n"))
            except (UnicodeDecodeError, ValueError):
                continue


def write_receipt(receipt: CollectorReceipt, stream: TextIO) -> None:
    json.dump(receipt.to_dict(), stream, indent=2, sort_keys=True)
    stream.write("\n")
