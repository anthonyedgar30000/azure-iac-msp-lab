"""Normalize source records and assemble observable service transactions.

The operational analyzer consumes assembled attempts, not demo data. Source adapters
map structured records from monitoring systems into stage evidence, contextual
evidence, or operational-history records.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

TERMINAL_STATUSES = {"failed", "timeout", "rejected"}
SUPPORTED_STAGE_STATUSES = TERMINAL_STATUSES | {"success"}


@dataclass
class EvidenceBundle:
    attempts: list[dict[str, Any]]
    tickets: list[dict[str, Any]]
    context_observations: list[dict[str, Any]]
    incomplete_transactions: list[dict[str, Any]]
    ingestion_summary: dict[str, Any]

    def report(self) -> dict[str, Any]:
        return {
            "summary": self.ingestion_summary,
            "incomplete_transactions": self.incomplete_transactions,
            "context_observations": self.context_observations,
        }


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _read_path(record: dict[str, Any], path: str | None, *, required: bool = False) -> Any:
    if not path:
        if required:
            raise ValueError("A required adapter field path is not configured")
        return None

    current: Any = record
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            if required:
                raise ValueError(f"Record is missing required field path: {path}")
            return None
        current = current[part]
    return current


def _adapter_field(
    record: dict[str, Any],
    adapter: dict[str, Any],
    name: str,
    *,
    required: bool = False,
    default_path: str | None = None,
) -> Any:
    fields = adapter.get("fields", {})
    path = fields.get(name, default_path)
    return _read_path(record, path, required=required)


def _optional_int(
    record: dict[str, Any],
    mapping: dict[str, Any],
    mapping_key: str,
    default_field: str,
    *,
    default: int | None = None,
) -> int | None:
    path = mapping.get(mapping_key, default_field)
    value = _read_path(record, path)
    if value is None:
        return default
    return int(value)


def _extract_attributes(record: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
    attributes: dict[str, Any] = {}
    for output_name, field_path in mapping.get("attributes", {}).items():
        value = _read_path(record, str(field_path))
        if value is not None:
            attributes[str(output_name)] = value
    return attributes


def load_jsonl_records(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        with Path(path).open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON in {path} line {line_number}: {exc}") from exc
                if not isinstance(payload, dict):
                    raise ValueError(f"Evidence record in {path} line {line_number} must be an object")
                records.append(payload)
    return records


def load_adapter_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not isinstance(payload.get("adapters"), dict):
        raise ValueError("Adapter configuration must contain an adapters object")
    return payload


def _normalize_ticket(
    record: dict[str, Any],
    mapping: dict[str, Any],
) -> dict[str, Any]:
    ticket = mapping.get("ticket", {})
    ticket_id = _read_path(record, ticket.get("ticket_id_field"), required=True)
    summary = _read_path(record, ticket.get("summary_field"), required=True)
    changed_at = _read_path(record, ticket.get("changed_at_field"), required=True)
    assets = _read_path(record, ticket.get("assets_field"), required=True)
    service_stages = _read_path(
        record, ticket.get("service_stages_field"), required=True
    )
    if not isinstance(assets, list) or not isinstance(service_stages, list):
        raise ValueError("Ticket assets and service stages must be arrays")
    _parse_datetime(str(changed_at))
    return {
        "ticket_id": str(ticket_id),
        "summary": str(summary),
        "changed_at": str(changed_at),
        "assets": [str(value) for value in assets],
        "service_stages": [str(value) for value in service_stages],
    }


def _normalize_records(
    records: list[dict[str, Any]],
    adapter_config: dict[str, Any],
    stage_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    adapters = adapter_config["adapters"]
    stage_events: list[dict[str, Any]] = []
    context_events: list[dict[str, Any]] = []
    tickets: list[dict[str, Any]] = []
    seen_event_ids: dict[str, str] = {}
    source_counts: Counter[str] = Counter()
    kind_counts: Counter[str] = Counter()
    duplicate_count = 0

    for record in records:
        source_type = str(record.get("source_type", ""))
        if not source_type or source_type not in adapters:
            raise ValueError(f"Unsupported or missing source_type: {source_type or '<missing>'}")
        adapter = adapters[source_type]
        event_type = str(
            _adapter_field(
                record,
                adapter,
                "event_type",
                required=True,
                default_path="event_type",
            )
        )
        event_mapping = adapter.get("events", {}).get(event_type)
        if not isinstance(event_mapping, dict):
            raise ValueError(f"Unmapped event type {source_type}:{event_type}")

        source_counts[source_type] += 1
        record_hash = _fingerprint(record)
        configured_event_id = _adapter_field(
            record,
            adapter,
            "event_id",
            default_path="event_id",
        )
        event_id = (
            str(configured_event_id)
            if configured_event_id is not None
            else f"{source_type}:{record_hash[:24]}"
        )
        existing_hash = seen_event_ids.get(event_id)
        if existing_hash:
            if existing_hash != record_hash:
                raise ValueError(f"Evidence identity {event_id} was reused with different content")
            duplicate_count += 1
            continue
        seen_event_ids[event_id] = record_hash

        kind = str(event_mapping.get("kind", "stage"))
        kind_counts[kind] += 1
        if kind == "ticket":
            tickets.append(_normalize_ticket(record, event_mapping))
            continue

        observed_at = str(
            _adapter_field(
                record,
                adapter,
                "observed_at",
                required=True,
                default_path="observed_at",
            )
        )
        _parse_datetime(observed_at)
        source_id_value = _adapter_field(
            record, adapter, "source_id", default_path="source_id"
        )
        source_id = str(source_id_value) if source_id_value is not None else source_type
        asset_value = _adapter_field(record, adapter, "asset_id", default_path="asset_id")
        gateway_value = _adapter_field(record, adapter, "gateway", default_path="gateway")
        base = {
            "event_id": event_id,
            "observed_at": observed_at,
            "source_type": source_type,
            "source_id": source_id,
            "asset_id": str(asset_value) if asset_value is not None else None,
            "gateway": str(gateway_value) if gateway_value is not None else None,
            "event_type": event_type,
            "record_fingerprint": record_hash,
            "attributes": _extract_attributes(record, event_mapping),
        }

        if kind == "context":
            context_type = event_mapping.get("context_type")
            if not context_type:
                raise ValueError(f"Context mapping {source_type}:{event_type} has no context_type")
            context_events.append({**base, "context_type": str(context_type)})
            continue

        if kind != "stage":
            raise ValueError(f"Unsupported evidence kind: {kind}")

        stage_id = str(event_mapping.get("stage_id", ""))
        if stage_id not in stage_ids:
            raise ValueError(f"Event maps to unknown service stage: {stage_id or '<missing>'}")
        status = str(event_mapping.get("status", ""))
        status_field = event_mapping.get("status_field")
        if status_field:
            status = str(_read_path(record, str(status_field), required=True))
        if status not in SUPPORTED_STAGE_STATUSES:
            raise ValueError(f"Unsupported stage status: {status or '<missing>'}")

        correlation_id = str(
            _adapter_field(
                record,
                adapter,
                "correlation_id",
                required=True,
                default_path="correlation_id",
            )
        )
        stage_events.append(
            {
                **base,
                "correlation_id": correlation_id,
                "stage_id": stage_id,
                "status": status,
                "elapsed_ms": _optional_int(
                    record, event_mapping, "elapsed_ms_field", "elapsed_ms"
                ),
                "retries": _optional_int(
                    record,
                    event_mapping,
                    "retries_field",
                    "retries",
                    default=0,
                )
                or 0,
                "timeout_ms": _optional_int(
                    record, event_mapping, "timeout_ms_field", "timeout_ms"
                ),
            }
        )

    summary = {
        "records_received": len(records),
        "records_accepted": len(seen_event_ids),
        "idempotent_duplicates": duplicate_count,
        "source_counts": dict(sorted(source_counts.items())),
        "kind_counts": dict(sorted(kind_counts.items())),
    }
    return stage_events, context_events, tickets, summary


def _assemble_attempts(
    stage_events: list[dict[str, Any]],
    stage_order: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in stage_events:
        grouped[event["correlation_id"]].append(event)

    attempts: list[dict[str, Any]] = []
    incomplete: list[dict[str, Any]] = []
    stage_positions = {stage_id: index for index, stage_id in enumerate(stage_order)}

    for correlation_id, events in sorted(grouped.items()):
        events.sort(key=lambda item: _parse_datetime(item["observed_at"]))
        gateway_candidates = {
            event["gateway"] for event in events if event.get("gateway")
        }
        if len(gateway_candidates) > 1:
            raise ValueError(
                f"Transaction {correlation_id} contains conflicting gateway identities: "
                f"{sorted(gateway_candidates)}"
            )
        if not gateway_candidates:
            incomplete.append(
                {
                    "correlation_id": correlation_id,
                    "reason": "gateway_not_observed",
                    "missing_stages": [],
                }
            )
            continue
        gateway = next(iter(gateway_candidates))

        by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in events:
            by_stage[event["stage_id"]].append(event)

        statuses: dict[str, str] = {}
        for stage_id, observations in by_stage.items():
            observed_statuses = {item["status"] for item in observations}
            if len(observed_statuses) > 1:
                raise ValueError(
                    f"Transaction {correlation_id} has conflicting outcomes for {stage_id}: "
                    f"{sorted(observed_statuses)}"
                )
            statuses[stage_id] = next(iter(observed_statuses))

        terminal_stages = [
            stage_id for stage_id, status in statuses.items() if status in TERMINAL_STATUSES
        ]
        if len(terminal_stages) > 1:
            raise ValueError(
                f"Transaction {correlation_id} has multiple terminal failure stages: "
                f"{sorted(terminal_stages, key=stage_positions.get)}"
            )
        terminal_index = (
            stage_positions[terminal_stages[0]] if terminal_stages else len(stage_order) - 1
        )
        events_after_failure = [
            stage_id
            for stage_id in by_stage
            if terminal_stages and stage_positions[stage_id] > terminal_index
        ]
        if events_after_failure:
            raise ValueError(
                f"Transaction {correlation_id} contains stage evidence after terminal failure: "
                f"{sorted(events_after_failure, key=stage_positions.get)}"
            )

        required_prefix = stage_order[: terminal_index + 1]
        missing = [stage_id for stage_id in required_prefix if stage_id not in by_stage]
        if missing:
            incomplete.append(
                {
                    "correlation_id": correlation_id,
                    "gateway": gateway,
                    "reason": "insufficient_contiguous_stage_evidence",
                    "missing_stages": missing,
                }
            )
            continue

        assembled_stages: list[dict[str, Any]] = []
        for index, stage_id in enumerate(stage_order):
            observations = by_stage.get(stage_id, [])
            if terminal_stages and index > terminal_index:
                assembled_stages.append({"stage_id": stage_id, "status": "not_reached"})
                continue
            if not observations:
                raise AssertionError("Validated stage prefix unexpectedly contains a gap")
            status = statuses[stage_id]
            elapsed_values = [
                int(item["elapsed_ms"])
                for item in observations
                if item.get("elapsed_ms") is not None
            ]
            timeout_values = [
                int(item["timeout_ms"])
                for item in observations
                if item.get("timeout_ms") is not None
            ]
            assembled = {
                "stage_id": stage_id,
                "status": status,
                "retries": max(int(item.get("retries", 0)) for item in observations),
            }
            if elapsed_values:
                assembled["elapsed_ms"] = max(elapsed_values)
            if timeout_values:
                assembled["timeout_ms"] = max(timeout_values)
            assembled_stages.append(assembled)

        attempts.append(
            {
                "attempt_id": correlation_id,
                "started_at": events[0]["observed_at"],
                "gateway": gateway,
                "stages": assembled_stages,
            }
        )

    return attempts, incomplete


def build_evidence_bundle(
    records: list[dict[str, Any]],
    adapter_config: dict[str, Any],
    service_path: dict[str, Any],
) -> EvidenceBundle:
    stages = service_path.get("stages", [])
    if not stages:
        raise ValueError("Service path must define at least one stage")
    stage_order = [str(stage["stage_id"]) for stage in stages]
    if len(stage_order) != len(set(stage_order)):
        raise ValueError("Service path stage IDs must be unique")

    stage_events, contexts, tickets, summary = _normalize_records(
        records, adapter_config, set(stage_order)
    )
    attempts, incomplete = _assemble_attempts(stage_events, stage_order)
    summary.update(
        {
            "assembled_attempts": len(attempts),
            "incomplete_transactions": len(incomplete),
            "context_observations": len(contexts),
            "operational_history_records": len(tickets),
        }
    )
    return EvidenceBundle(
        attempts=attempts,
        tickets=tickets,
        context_observations=contexts,
        incomplete_transactions=incomplete,
        ingestion_summary=summary,
    )


def load_evidence_bundle(
    record_paths: Iterable[str | Path],
    adapter_config_path: str | Path,
    service_path: dict[str, Any],
) -> EvidenceBundle:
    return build_evidence_bundle(
        load_jsonl_records(record_paths),
        load_adapter_config(adapter_config_path),
        service_path,
    )


def derive_load_balancer_state(
    context_observations: list[dict[str, Any]],
) -> dict[str, Any] | None:
    candidates = [
        observation
        for observation in context_observations
        if observation.get("context_type") == "load_balancer_backend_state"
    ]
    if not candidates:
        return None

    latest_by_backend: dict[str, dict[str, Any]] = {}
    for observation in sorted(
        candidates, key=lambda item: _parse_datetime(item["observed_at"])
    ):
        attributes = observation.get("attributes", {})
        backend_id = str(
            attributes.get("backend_id")
            or observation.get("asset_id")
            or observation.get("gateway")
            or ""
        )
        if backend_id:
            latest_by_backend[backend_id] = observation
    if not latest_by_backend:
        return None

    representative = next(iter(latest_by_backend.values()))
    representative_attributes = representative.get("attributes", {})
    backends = []
    for backend_id, observation in sorted(latest_by_backend.items()):
        attributes = observation.get("attributes", {})
        backends.append(
            {
                "backend_id": backend_id,
                "probe_status": str(attributes.get("probe_status", "unknown")),
                "administrative_state": str(
                    attributes.get("administrative_state", "unknown")
                ),
            }
        )

    return {
        "load_balancer_id": str(
            representative_attributes.get("load_balancer_id", representative["source_id"])
        ),
        "selection_mode": str(
            representative_attributes.get("selection_mode", "unknown")
        ),
        "probe": {
            "name": str(representative_attributes.get("probe_name", "unknown")),
            "protocol": str(representative_attributes.get("probe_protocol", "unknown")),
            "port": int(representative_attributes.get("probe_port", 0)),
            "scope": str(representative_attributes.get("probe_scope", "unknown")),
        },
        "backends": backends,
    }
