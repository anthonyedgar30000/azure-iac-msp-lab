#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

TARGET_RG = "rg-st-demo-api-dev-westus2"
TARGET_VM = "vm-st-demo-api-mst-dev"
TARGET_FQDN = "st-demo-api-vm-aeg30000.westus2.cloudapp.azure.com"
UUID = re.compile(r"/subscriptions/[^/]+", re.IGNORECASE)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def digest(value: str | None) -> str | None:
    return hashlib.sha256(value.encode()).hexdigest() if value else None


def sanitize_id(value: Any) -> Any:
    return UUID.sub("/subscriptions/<redacted>", value) if isinstance(value, str) else value


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items() if k not in {"subscriptionId", "tenantId", "principalId", "objectId"}}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return sanitize_id(value)


def az(args: list[str], *, allow_failure: bool = False) -> tuple[bool, Any, str]:
    command = ["az", *args, "--only-show-errors", "--output", "json"]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        if allow_failure:
            return False, None, " ".join(result.stderr.split())[:500]
        raise RuntimeError(" ".join(result.stderr.split())[:500])
    return True, json.loads(result.stdout or "null"), ""


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def discover() -> dict[str, Any]:
    _, subscriptions, _ = az(["account", "list", "--all"])
    candidates: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    for subscription in subscriptions or []:
        if subscription.get("state") != "Enabled":
            continue
        sid = subscription["id"]
        ok, group, error = az(["group", "show", "--name", TARGET_RG, "--subscription", sid], allow_failure=True)
        record = {
            "subscription_name": subscription.get("name"),
            "subscription_sha256": digest(sid),
            "tenant_sha256": digest(subscription.get("tenantId")),
            "resource_group_status": "observed" if ok else "not_observed",
            "error_present": bool(error),
        }
        observations.append(record)
        if ok:
            candidates.append({"subscription": subscription, "group": group})
    if len(candidates) != 1:
        raise RuntimeError(f"expected one subscription containing {TARGET_RG}; observed {len(candidates)}")
    return {"selected": candidates[0], "observations": observations}


def collect_rbac(scope: str, subscription_id: str) -> dict[str, Any]:
    ok, assignments, error = az(
        [
            "role", "assignment", "list",
            "--scope", scope,
            "--include-inherited",
            "--fill-principal-name", "false",
            "--subscription", subscription_id,
        ],
        allow_failure=True,
    )
    if not ok:
        return {"status": "observation_failed", "error": error, "claim_boundary": "RBAC remains not_observed."}
    result = []
    for item in assignments or []:
        pid = item.get("principalId")
        result.append(
            {
                "principal_sha256": digest(pid),
                "principal_type": item.get("principalType"),
                "role_definition_name": item.get("roleDefinitionName"),
                "role_definition_id": sanitize_id(item.get("roleDefinitionId")),
                "scope": sanitize_id(item.get("scope")),
                "inherited": str(item.get("scope", "")).lower() != scope.lower(),
            }
        )
    return {
        "status": "observed",
        "assignment_count": len(result),
        "assignments": result,
        "claim_boundary": "Assignments were observed; effective least privilege and deny assignments require separate evaluation.",
    }


def collect_cost(scope: str, subscription_id: str) -> dict[str, Any]:
    body = {
        "type": "Usage",
        "timeframe": "MonthToDate",
        "dataset": {
            "granularity": "Daily",
            "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
            "grouping": [{"type": "Dimension", "name": "ResourceId"}],
        },
    }
    ok, response, error = az(
        [
            "rest", "--method", "post",
            "--uri", f"{scope}/providers/Microsoft.CostManagement/query?api-version=2025-03-01",
            "--body", json.dumps(body),
            "--subscription", subscription_id,
        ],
        allow_failure=True,
    )
    if not ok:
        return {"status": "observation_failed", "error": error, "claim_boundary": "Cost remains not_observed."}
    properties = (response or {}).get("properties", {})
    columns = [column.get("name") for column in properties.get("columns", [])]
    rows = []
    for source in properties.get("rows", []):
        row = list(source)
        for index, name in enumerate(columns):
            if name == "ResourceId" and index < len(row):
                row[index] = sanitize_id(row[index])
        rows.append(row)
    return {
        "status": "observed",
        "timeframe": "MonthToDate",
        "columns": columns,
        "rows": rows,
        "claim_boundary": "Usage data may lag and is not an invoice or forecast.",
    }


def collect_backup(vm_id: str, subscription_id: str) -> dict[str, Any]:
    ok, vaults, error = az(
        ["resource", "list", "--resource-type", "Microsoft.RecoveryServices/vaults", "--subscription", subscription_id],
        allow_failure=True,
    )
    if not ok:
        return {"status": "observation_failed", "error": error, "claim_boundary": "Backup remains not_observed."}
    matches: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    target = vm_id.lower()
    for vault in vaults or []:
        name, group = vault.get("name"), vault.get("resourceGroup")
        if not name or not group:
            continue
        item_ok, items, item_error = az(
            [
                "backup", "item", "list",
                "--vault-name", str(name),
                "--resource-group", str(group),
                "--backup-management-type", "AzureIaasVM",
                "--subscription", subscription_id,
            ],
            allow_failure=True,
        )
        if not item_ok:
            failures.append({"vault_name": name, "vault_resource_group": group, "error": item_error})
            continue
        for item in items or []:
            props = item.get("properties") or {}
            ids = [props.get("sourceResourceId"), props.get("virtualMachineId"), props.get("sourceResourceIdWithStorageType")]
            if any(str(value or "").lower() == target for value in ids):
                matches.append(
                    sanitize(
                        {
                            "vault_name": name,
                            "vault_resource_group": group,
                            "item_id": item.get("id"),
                            "item_name": item.get("name"),
                            "protection_state": props.get("protectionState"),
                            "protection_status": props.get("protectionStatus"),
                            "last_backup_status": props.get("lastBackupStatus"),
                            "last_backup_time": props.get("lastBackupTime"),
                        }
                    )
                )
    if failures:
        return {
            "status": "partial_observation",
            "vault_count": len(vaults or []),
            "matching_items": matches,
            "query_failures": failures,
            "claim_boundary": "Some vault queries failed; backup absence is not established.",
        }
    return {
        "status": "observed",
        "vault_count": len(vaults or []),
        "matching_item_count": len(matches),
        "matching_items": matches,
        "backup_item_observed": bool(matches),
        "claim_boundary": "Recovery Services AzureIaasVM items were queried. An empty result does not exclude other backup methods or prove recovery testing.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", default=os.environ.get("SERVICETRACER_FOLLOWUP_WORKDIR") or str(Path.home() / "clouddrive" / f"servicetracer-readonly-follow-up-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}"))
    args = parser.parse_args()
    workdir = Path(args.workdir).expanduser().resolve()
    evidence = workdir / "evidence"
    evidence.mkdir(parents=True, exist_ok=False)
    os.chmod(workdir, 0o700)
    os.chmod(evidence, 0o700)

    started = now()
    try:
        found = discover()
        subscription = found["selected"]["subscription"]
        group = found["selected"]["group"]
        sid = subscription["id"]
        group_id = group["id"]
        _, vm, _ = az(["vm", "show", "--resource-group", TARGET_RG, "--name", TARGET_VM, "--subscription", sid])
        vm_id = vm["id"]

        write(evidence / "subscription-discovery.json", {"status": "resolved", "observations": found["observations"]})
        write(evidence / "rbac.json", collect_rbac(group_id, sid))
        write(evidence / "cost-month-to-date.json", collect_cost(group_id, sid))
        write(evidence / "backup.json", collect_backup(vm_id, sid))
        summary = {
            "schema_version": "servicetracer.readonly-follow-up.v1",
            "started_at": started,
            "completed_at": now(),
            "target": {"resource_group": TARGET_RG, "vm": TARGET_VM, "fqdn": TARGET_FQDN},
            "subscription_name": subscription.get("name"),
            "subscription_sha256": digest(sid),
            "tenant_sha256": digest(subscription.get("tenantId")),
            "azure_authentication_performed": True,
            "azure_control_plane_queried": True,
            "azure_mutations_authorized": False,
            "azure_mutations_performed": False,
            "guest_commands_performed": False,
            "transaction_replay_performed": False,
            "claim_boundary": "This follow-up corrects three observation defects. It does not prove least privilege, invoice accuracy, or recovery success.",
        }
        write(evidence / "summary.json", summary)
        manifest = [{"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(evidence.glob("*.json"))]
        write(evidence / "manifest.json", {"files": manifest})
        print(json.dumps(summary, indent=2))
        print(f"Evidence directory: {evidence}")
        print("STOP: no Azure mutation, guest command, transaction replay, deployment, or cleanup command was run.")
        return 0
    except Exception as exc:
        write(
            evidence / "failure.json",
            {
                "status": "observation_failed",
                "started_at": started,
                "failed_at": now(),
                "error": str(exc),
                "azure_mutations_performed": False,
                "claim_boundary": "Observation failure does not establish absence.",
            },
        )
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
