"""Command-line interface for ServiceTracer demo analysis."""

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze ordered service transactions")
    parser.add_argument("--attempts", required=True, help="JSONL transaction attempts")
    parser.add_argument("--service-path", required=True, help="Service path JSON")
    parser.add_argument("--tickets", help="Optional ticket-history JSON array")
    parser.add_argument(
        "--load-balancer-state",
        help="Optional load-balancer probe and backend-state JSON object",
    )
    parser.add_argument(
        "--containment-attempts",
        help="Optional JSONL attempts captured after draining the suspect backend",
    )
    parser.add_argument("--output", help="Optional report JSON path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    with Path(args.service_path).open("r", encoding="utf-8") as handle:
        service_path = json.load(handle)

    tickets = load_tickets(args.tickets) if args.tickets else []
    report = analyze_incident(load_attempts(args.attempts), service_path, tickets)

    if args.load_balancer_state:
        report["load_balancer_assessment"] = assess_load_balancer(
            report,
            load_json_object(args.load_balancer_state),
        )

    containment_attempts = (
        load_attempts(args.containment_attempts) if args.containment_attempts else None
    )
    report["containment"] = build_containment_plan(
        report,
        service_path,
        containment_attempts,
    )

    rendered = json.dumps(report, indent=2, sort_keys=True)

    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
