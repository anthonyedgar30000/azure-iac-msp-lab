#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import servicetracer_targeted_reality_sync as base


def resource_properties(item: dict[str, Any]) -> dict[str, Any]:
    value = item.get("properties")
    return value if isinstance(value, dict) else {}


def cost_month_to_date(scope: str) -> dict[str, Any]:
    body = {
        "type": "ActualCost",
        "timeframe": "MonthToDate",
        "dataset": {
            "granularity": "None",
            "aggregation": {
                "totalCost": {"name": "PreTaxCost", "function": "Sum"}
            },
        },
    }
    errors: list[str] = []
    for attempt, delay in enumerate((0, 5, 10, 20), start=1):
        if delay:
            time.sleep(delay)
        ok, response, error = base.az(
            [
                "rest",
                "--method", "post",
                "--uri", f"{scope}/providers/Microsoft.CostManagement/query?api-version=2025-03-01",
                "--body", json.dumps(body),
            ],
            allow_failure=True,
        )
        if ok:
            properties = (response or {}).get("properties") or {}
            columns = [column.get("name") for column in properties.get("columns", [])]
            rows = properties.get("rows", [])
            mapped_rows = [dict(zip(columns, row)) for row in rows]
            return {
                "status": "observed",
                "query_type": "ActualCost",
                "timeframe": "MonthToDate",
                "attempts_required": attempt,
                "rows": base.redact(mapped_rows),
                "claim_boundary": "Month-to-date usage data may lag and is not an invoice or forecast.",
            }
        errors.append(error)
        if "429" not in error and "Too Many Requests" not in error:
            break
    return {
        "status": "observation_failed",
        "attempt_count": len(errors),
        "errors": errors,
        "claim_boundary": "Cost remains not_observed; throttling or query failure is not a zero-cost result.",
    }


def main() -> int:
    evidence_dir = Path(
        os.environ.get(
            "SERVICETRACER_SYNC_EVIDENCE_DIR",
            "servicetracer-targeted-reality-sync-evidence",
        )
    )
    evidence_dir.mkdir(parents=True, exist_ok=False)
    started = base.observed_at()
    try:
        expected_subscription = os.environ["EXPECTED_TARGET_SUBSCRIPTION_ID"]
        expected_tenant = os.environ["EXPECTED_AZURE_TENANT_ID"]
        _, account, _ = base.az(["account", "show"])
        if (
            account.get("id") != expected_subscription
            or account.get("tenantId") != expected_tenant
            or account.get("state") != "Enabled"
        ):
            raise RuntimeError("Azure account context does not match the protected target identity")

        account_record = {
            "subscription_name": account.get("name"),
            "subscription_sha256": base.digest(account.get("id")),
            "tenant_sha256": base.digest(account.get("tenantId")),
            "state": account.get("state"),
        }
        base.write(evidence_dir / "account.json", account_record)

        _, group, _ = base.az(["group", "show", "--name", base.RESOURCE_GROUP])
        group_properties = resource_properties(group)
        group_id = group.get("id")
        _, resources, _ = base.az(
            ["resource", "list", "--resource-group", base.RESOURCE_GROUP]
        )
        inventory = {
            "resource_group": {
                "name": group.get("name"),
                "location": group.get("location"),
                "provisioning_state": group_properties.get("provisioningState"),
            },
            "resource_count": len(resources or []),
            "resources": [
                {
                    "name": item.get("name"),
                    "type": item.get("type"),
                    "location": item.get("location"),
                    "provisioning_state": resource_properties(item).get("provisioningState"),
                }
                for item in (resources or [])
            ],
        }
        base.write(evidence_dir / "inventory.json", base.redact(inventory))

        _, vm, _ = base.az(
            [
                "vm", "show",
                "--resource-group", base.RESOURCE_GROUP,
                "--name", base.VM_NAME,
                "--show-details",
            ]
        )
        _, instance_view, _ = base.az(
            [
                "vm", "get-instance-view",
                "--resource-group", base.RESOURCE_GROUP,
                "--name", base.VM_NAME,
            ]
        )
        vm_record = {
            "name": vm.get("name"),
            "location": vm.get("location"),
            "hardware_profile": vm.get("hardwareProfile"),
            "provisioning_state": vm.get("provisioningState"),
            "power_state": vm.get("powerState"),
            "public_ips": vm.get("publicIps"),
            "fqdn": vm.get("fqdns"),
            "identity_type": (vm.get("identity") or {}).get("type"),
            "statuses": (instance_view or {}).get("statuses"),
        }
        base.write(evidence_dir / "vm.json", base.redact(vm_record))

        _, deployments, _ = base.az(
            ["deployment", "group", "list", "--resource-group", base.RESOURCE_GROUP]
        )
        deployment_records = []
        for item in deployments or []:
            properties = resource_properties(item)
            deployment_records.append(
                {
                    "name": item.get("name"),
                    "provisioning_state": properties.get("provisioningState"),
                    "timestamp": properties.get("timestamp"),
                    "duration": properties.get("duration"),
                }
            )
        base.write(evidence_dir / "deployments.json", deployment_records)

        _, compute_usage, _ = base.az(
            ["vm", "list-usage", "--location", base.LOCATION]
        )
        _, network_usage, _ = base.az(
            ["network", "list-usages", "--location", base.LOCATION]
        )
        quota = {
            "location": base.LOCATION,
            "total_regional_vcpus": base.quota_record(
                compute_usage or [], ("cores", "total regional vcpus")
            ),
            "standard_falsv7_family_vcpus": base.quota_record(
                compute_usage or [],
                ("standardfalsv7family", "standard falsv7 family vcpus"),
            ),
            "standard_ipv4_public_ips": base.quota_record(
                network_usage or [], ("PublicIPAddresses", "public ip addresses")
            ),
        }
        base.write(evidence_dir / "quota.json", quota)

        cost = cost_month_to_date(group_id)
        base.write(evidence_dir / "cost-month-to-date-retry.json", cost)
        health = base.public_health()
        base.write(evidence_dir / "public-health.json", health)
        guest = base.guest_observation()
        base.write(evidence_dir / "guest.json", guest)

        summary = {
            "schema_version": "servicetracer.targeted-reality-sync.v2",
            "started_at": started,
            "completed_at": base.observed_at(),
            "repository_sha": os.environ.get("GITHUB_SHA"),
            "target": {
                "resource_group": base.RESOURCE_GROUP,
                "vm": base.VM_NAME,
                "location": base.LOCATION,
                "fqdn": base.FQDN,
            },
            "account": account_record,
            "inventory_resource_count": inventory["resource_count"],
            "vm_power_state": vm_record["power_state"],
            "cost_observation_status": cost.get("status"),
            "public_health_status": health.get("status"),
            "public_health_http_status": health.get("http_status"),
            "guest_observation_status": guest.get("status"),
            "guest_source_ref": (guest.get("result") or {}).get("source_ref"),
            "guest_proxy_read_timeout_seconds": (
                ((guest.get("result") or {}).get("nginx") or {}).get(
                    "proxy_read_timeout_seconds"
                )
            ),
            "azure_authentication_performed": True,
            "azure_control_plane_queries_performed": True,
            "guest_read_only_command_attempted": True,
            "guest_read_only_command_observed": guest.get("status") == "observed",
            "azure_resource_configuration_mutations_performed": False,
            "transaction_replay_performed": False,
            "deployment_performed": False,
            "service_restart_performed": False,
            "cleanup_performed": False,
            "claim_boundary": (
                "Read-only observation refreshes evidence; it does not deploy PR #84, "
                "prove least privilege, prove recovery, or authorize a transaction replay."
            ),
        }
        base.write(evidence_dir / "summary.json", summary)
        manifest = [
            {
                "file": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in sorted(evidence_dir.glob("*.json"))
        ]
        base.write(evidence_dir / "manifest.json", {"files": manifest})
        print(json.dumps(summary, indent=2))
        return 0
    except Exception as exc:
        base.write(
            evidence_dir / "failure.json",
            {
                "status": "observation_failed",
                "started_at": started,
                "failed_at": base.observed_at(),
                "error": base.redact(str(exc)),
                "azure_resource_configuration_mutations_performed": False,
                "transaction_replay_performed": False,
                "claim_boundary": "Observation failure does not establish absence.",
            },
        )
        print(f"ERROR: {base.redact(str(exc))}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
