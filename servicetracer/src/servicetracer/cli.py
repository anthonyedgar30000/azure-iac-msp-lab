"""Command-line interface for ServiceTracer incident analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analyzer import analyze_incident, load_attempts, load_tickets
from .containment import (
    assess_load_balancer,
    build_containment_plan,
    load_json_object,
)
from .demo_report import build_technician_handoff
from .evidence import derive_load_balancer_state, load_evidence_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze ordered service transactions")
    incident_source = parser.add_mutually_exclusive_group(required=True)
    incident_source.add_argument(
        "--attempts",
        help="Preassembled JSONL transaction attempts (compatibility and replay mode)",
    )
    incident_source.add_argument(
        "--evidence-records",
        action="append",
        help=(
            "Structured source-record JSONL input. Repeat for multiple collector or "
            "export files. Records are normalized and assembled into transactions."
        ),
    )
    parser.add_argument(
        "--adapter-config",
        help="Source-adapter mapping JSON required with evidence-record inputs",
    )
    parser.add_argument("--service-path", required=True, help="Service path JSON")
    parser.add_argument(
        "--tickets",
        help="Optional additional ticket-history JSON array",
    )
    parser.add_argument(
        "--load-balancer-state",
        help=(
            "Optional load-balancer state JSON. When omitted, ServiceTracer derives "
            "state from matching contextual evidence when available."
        ),
    )
    containment_source = parser.add_mutually_exclusive_group()
    containment_source.add_argument(
        "--containment-attempts",
        help="Optional preassembled JSONL attempts captured after containment",
    )
    containment_source.add_argument(
        "--containment-evidence-records",
        action="append",
        help="Optional structured source records captured after containment",
    )
    parser.add_argument(
        "--report-view",
        choices=("full", "technician-handoff"),
        default="full",
        help=(
            "Report shape. The technician-handoff view deliberately stops at the "
            "affected VPN backend and leaves device-specific diagnosis to the technician."
        ),
    )
    parser.add_argument("--output", help="Optional report JSON path")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    with Path(args.service_path).open("r", encoding="utf-8") as handle:
        service_path = json.load(handle)

    file_tickets = load_tickets(args.tickets) if args.tickets else []
    incident_bundle = None
    if args.evidence_records:
        if not args.adapter_config:
            parser.error("--adapter-config is required with --evidence-records")
        incident_bundle = load_evidence_bundle(
            args.evidence_records,
            args.adapter_config,
            service_path,
        )
        if not incident_bundle.attempts:
            parser.error(
                "No complete observable transactions were assembled; inspect the "
                "evidence-ingestion report and source correlation fields"
            )
        attempts = incident_bundle.attempts
        tickets = [*incident_bundle.tickets, *file_tickets]
        input_mode = "source_evidence"
    else:
        attempts = load_attempts(args.attempts)
        tickets = file_tickets
        input_mode = "preassembled_attempts"

    report = analyze_incident(attempts, service_path, tickets)
    report["input_mode"] = input_mode
    if incident_bundle:
        report["evidence_ingestion"] = incident_bundle.report()

    if args.load_balancer_state:
        load_balancer_state = load_json_object(args.load_balancer_state)
    elif incident_bundle:
        load_balancer_state = derive_load_balancer_state(
            incident_bundle.context_observations
        )
    else:
        load_balancer_state = None

    if load_balancer_state:
        report["load_balancer_assessment"] = assess_load_balancer(
            report,
            load_balancer_state,
        )

    containment_attempts = None
    containment_bundle = None
    if args.containment_evidence_records:
        if not args.adapter_config:
            parser.error(
                "--adapter-config is required with --containment-evidence-records"
            )
        containment_bundle = load_evidence_bundle(
            args.containment_evidence_records,
            args.adapter_config,
            service_path,
        )
        containment_attempts = containment_bundle.attempts
    elif args.containment_attempts:
        containment_attempts = load_attempts(args.containment_attempts)

    report["containment"] = build_containment_plan(
        report,
        service_path,
        containment_attempts,
    )
    if containment_bundle:
        report["containment"]["evidence_ingestion"] = containment_bundle.report()

    output_report = report
    if args.report_view == "technician-handoff":
        load_balancer_assessment = report.get("load_balancer_assessment")
        if not load_balancer_assessment:
            parser.error(
                "--report-view technician-handoff requires load-balancer state or "
                "matching load-balancer context evidence"
            )
        output_report = build_technician_handoff(
            report,
            load_balancer_assessment,
            report.get("containment"),
        )
        output_report["input_mode"] = input_mode
        if incident_bundle:
            output_report["evidence_ingestion_summary"] = (
                incident_bundle.ingestion_summary
            )

    rendered = json.dumps(output_report, indent=2, sort_keys=True)

    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
