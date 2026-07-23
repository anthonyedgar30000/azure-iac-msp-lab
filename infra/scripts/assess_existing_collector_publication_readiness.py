from __future__ import annotations

import argparse
import base64
import fnmatch
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from verify_existing_collector_publication_plan import classify_what_if

TARGET_RBAC_ACTION = "Microsoft.Authorization/roleAssignments/write"
STORAGE_USAGE_API_VERSION = "2025-06-01"
DENY_ASSIGNMENTS_API_VERSION = "2022-04-01"
PRICE_API = "https://prices.azure.com/api/retail/prices"
PRICE_CURRENCY = "CAD"
COST_ASSUMPTIONS = {
    "stored_gb_month": 10.0,
    "write_operations": 100_000,
    "read_operations": 1_000_000,
    "other_operations": 100_000,
    "retrieval_gb": 10.0,
    "uncaptured_cost_contingency_cad": 2.0,
}


class EvidenceError(RuntimeError):
    pass


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"Invalid JSON evidence {path}: {exc}") from exc


def run_capture(command: list[str], *, sensitive_stdout: bool = False) -> dict[str, Any]:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": "<redacted-sensitive-output>" if sensitive_stdout else completed.stdout,
        "stderr": completed.stderr,
    }


def run_json(command: list[str], output_path: Path) -> Any:
    result = run_capture(command)
    write_json(output_path.with_suffix(output_path.suffix + ".command.json"), result)
    if result["returncode"] != 0:
        raise EvidenceError(f"Read-only command failed: {' '.join(command)}")
    try:
        payload = json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"Command returned invalid JSON: {' '.join(command)}") from exc
    write_json(output_path, payload)
    return payload


def decode_executor_oid() -> str:
    result = subprocess.run(
        [
            "az",
            "account",
            "get-access-token",
            "--resource",
            "https://management.azure.com/",
            "--query",
            "accessToken",
            "--output",
            "tsv",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise EvidenceError("Could not obtain an Azure management token for local claim decoding")
    token = result.stdout.strip()
    parts = token.split(".")
    if len(parts) != 3:
        raise EvidenceError("Azure access token was not a JWT")
    padding = "=" * (-len(parts[1]) % 4)
    claims = json.loads(base64.urlsafe_b64decode(parts[1] + padding))
    oid = str(claims.get("oid") or "")
    if not oid:
        raise EvidenceError("Azure token did not contain an oid claim")
    return oid


def fetch_retail_prices(location: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    filter_value = (
        "serviceName eq 'Storage' and "
        f"armRegionName eq '{location}' and "
        "priceType eq 'Consumption'"
    )
    query = urlencode({"currencyCode": PRICE_CURRENCY, "$filter": filter_value})
    next_url = f"{PRICE_API}?{query}"
    items: list[dict[str, Any]] = []
    pages = 0
    while next_url:
        request = Request(next_url, headers={"User-Agent": "azure-iac-msp-lab-readiness/1.0"})
        with urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        pages += 1
        page_items = payload.get("Items") or []
        if not isinstance(page_items, list):
            raise EvidenceError("Retail Prices API Items was not an array")
        items.extend(page_items)
        next_url = str(payload.get("NextPageLink") or "")
        if pages > 20:
            raise EvidenceError("Retail Prices API pagination exceeded the bounded page limit")
    metadata = {
        "endpoint": PRICE_API,
        "currency": PRICE_CURRENCY,
        "filter": filter_value,
        "pages": pages,
        "items": len(items),
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }
    return items, metadata


def _candidate_rows(items: list[dict[str, Any]], category: str) -> list[dict[str, Any]]:
    patterns = {
        "data_stored": ("data stored", "1 gb/month"),
        "write_operations": ("write operations", "10k"),
        "read_operations": ("read operations", "10k"),
        "other_operations": ("other operations", "10k"),
        "data_retrieval": ("data retrieval", "1 gb"),
    }
    meter_fragment, unit_fragment = patterns[category]
    candidates: list[dict[str, Any]] = []
    for item in items:
        product = str(item.get("productName") or "").lower()
        sku = str(item.get("skuName") or "").lower()
        meter = str(item.get("meterName") or "").lower()
        unit = str(item.get("unitOfMeasure") or "").lower()
        price = item.get("retailPrice")
        if not isinstance(price, (int, float)) or isinstance(price, bool):
            continue
        if "blob" not in product or "lrs" not in sku:
            continue
        if meter_fragment not in meter or unit_fragment not in unit:
            continue
        candidates.append(item)
    return candidates


def estimate_cost(items: list[dict[str, Any]], ceiling_cad: float) -> dict[str, Any]:
    selected: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for category in (
        "data_stored",
        "write_operations",
        "read_operations",
        "other_operations",
        "data_retrieval",
    ):
        candidates = _candidate_rows(items, category)
        if not candidates:
            missing.append(category)
            continue
        selected[category] = max(candidates, key=lambda item: float(item["retailPrice"]))

    if missing:
        return {
            "status": "unresolved_missing_price_meters",
            "currency": PRICE_CURRENCY,
            "ceiling_cad": ceiling_cad,
            "assumptions": COST_ASSUMPTIONS,
            "missing_categories": missing,
            "selected_meters": selected,
            "estimated_monthly_cost_cad": None,
            "under_ceiling": False,
        }

    components = {
        "data_stored": COST_ASSUMPTIONS["stored_gb_month"]
        * float(selected["data_stored"]["retailPrice"]),
        "write_operations": COST_ASSUMPTIONS["write_operations"]
        / 10_000
        * float(selected["write_operations"]["retailPrice"]),
        "read_operations": COST_ASSUMPTIONS["read_operations"]
        / 10_000
        * float(selected["read_operations"]["retailPrice"]),
        "other_operations": COST_ASSUMPTIONS["other_operations"]
        / 10_000
        * float(selected["other_operations"]["retailPrice"]),
        "data_retrieval": COST_ASSUMPTIONS["retrieval_gb"]
        * float(selected["data_retrieval"]["retailPrice"]),
        "uncaptured_cost_contingency": COST_ASSUMPTIONS[
            "uncaptured_cost_contingency_cad"
        ],
    }
    total = round(sum(components.values()), 6)
    return {
        "status": "calculated_conservative_retail_estimate",
        "currency": PRICE_CURRENCY,
        "ceiling_cad": ceiling_cad,
        "assumptions": COST_ASSUMPTIONS,
        "selected_meters": selected,
        "components_cad": components,
        "estimated_monthly_cost_cad": total,
        "under_ceiling": total <= ceiling_cad,
        "claim_boundary": (
            "Retail-rate estimate with explicit workload assumptions and contingency; "
            "not a bill, quote, negotiated rate, tax calculation, or actual-cost measurement."
        ),
    }


def assignment_scope_applies(assignment_scope: str, target_scope: str) -> bool:
    normalized_assignment = assignment_scope.rstrip("/").lower()
    normalized_target = target_scope.rstrip("/").lower()
    return normalized_target == normalized_assignment or normalized_target.startswith(
        normalized_assignment + "/"
    )


def role_grants_action(role: dict[str, Any], action: str) -> bool:
    action_lower = action.lower()
    permissions = role.get("permissions") or []
    for permission in permissions:
        actions = [str(value).lower() for value in permission.get("actions") or []]
        not_actions = [
            str(value).lower() for value in permission.get("notActions") or []
        ]
        allowed = any(fnmatch.fnmatchcase(action_lower, pattern) for pattern in actions)
        denied = any(fnmatch.fnmatchcase(action_lower, pattern) for pattern in not_actions)
        if allowed and not denied:
            return True
    return False


def parse_storage_usage(payload: Any) -> dict[str, Any]:
    values = payload.get("value") if isinstance(payload, dict) else None
    if not isinstance(values, list):
        return {"status": "unresolved_invalid_payload", "headroom": None}
    for item in values:
        name = item.get("name") or {}
        name_value = str(name.get("value") or item.get("name") or "")
        if name_value.lower() != "storageaccounts":
            continue
        current = item.get("currentValue")
        limit = item.get("limit")
        if not isinstance(current, int) or not isinstance(limit, int):
            return {"status": "unresolved_invalid_values", "headroom": None}
        return {
            "status": "captured",
            "current": current,
            "limit": limit,
            "headroom": limit - current,
            "one_account_available": current + 1 <= limit,
            "unit": item.get("unit"),
        }
    return {"status": "unresolved_storage_accounts_entry_missing", "headroom": None}


def command_json_result(result: dict[str, Any]) -> Any | None:
    if result["returncode"] != 0:
        return None
    try:
        return json.loads(result["stdout"])
    except json.JSONDecodeError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture fail-closed predeployment readiness evidence without Azure mutation"
    )
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--location", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--allowed-origin", required=True)
    parser.add_argument("--maximum-monthly-cost-cad", required=True, type=float)
    parser.add_argument("--plan-verification", required=True)
    parser.add_argument("--plan-parameters", required=True)
    parser.add_argument("--artifact-dir", required=True)
    args = parser.parse_args()

    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    plan_verification = load_json(Path(args.plan_verification))
    planned_parameters = load_json(Path(args.plan_parameters))
    planned_principal = str(plan_verification.get("collector_principal_id") or "")
    storage_account_name = str(plan_verification.get("storage_account_name") or "")
    collector_vm = f"vm-stcollector-{args.prefix}-{args.environment}"

    try:
        account = run_json(
            ["az", "account", "show", "--output", "json"],
            artifact_dir / "azure-context.json",
        )
        subscription_id = str(account.get("id") or "")
        group = run_json(
            ["az", "group", "show", "--name", args.resource_group, "--output", "json"],
            artifact_dir / "resource-group.json",
        )
        group_id = str(group.get("id") or "")
        collector = run_json(
            [
                "az",
                "vm",
                "show",
                "--resource-group",
                args.resource_group,
                "--name",
                collector_vm,
                "--show-details",
                "--output",
                "json",
            ],
            artifact_dir / "collector.json",
        )
        storage_accounts = run_json(
            ["az", "storage", "account", "list", "--output", "json"],
            artifact_dir / "storage-accounts.json",
        )
        matching_storage = [
            item
            for item in storage_accounts
            if item.get("name") == storage_account_name
            or (item.get("tags") or {}).get("component")
            == "servicetracer-public-report"
        ]
        write_json(artifact_dir / "matching-report-storage.json", matching_storage)

        storage_usage_url = (
            f"https://management.azure.com/subscriptions/{subscription_id}"
            f"/providers/Microsoft.Storage/locations/{args.location}/usages"
            f"?api-version={STORAGE_USAGE_API_VERSION}"
        )
        storage_usage = run_json(
            ["az", "rest", "--method", "get", "--url", storage_usage_url],
            artifact_dir / "storage-usage.json",
        )
        quota = parse_storage_usage(storage_usage)
        write_json(artifact_dir / "storage-quota-assessment.json", quota)

        policy_result = run_capture(
            [
                "az",
                "policy",
                "assignment",
                "list",
                "--scope",
                group_id,
                "--filter",
                "atScope()",
                "--expand",
                "LatestDefinitionVersion,EffectiveDefinitionVersion",
                "--output",
                "json",
            ]
        )
        write_json(artifact_dir / "policy-assignments-command.json", policy_result)
        policy_payload = command_json_result(policy_result)
        if policy_payload is not None:
            write_json(artifact_dir / "policy-assignments.json", policy_payload)

        deny_url = (
            f"https://management.azure.com{group_id}"
            f"/providers/Microsoft.Authorization/denyAssignments"
            f"?api-version={DENY_ASSIGNMENTS_API_VERSION}"
        )
        deny_result = run_capture(
            ["az", "rest", "--method", "get", "--url", deny_url]
        )
        write_json(artifact_dir / "deny-assignments-command.json", deny_result)
        deny_payload = command_json_result(deny_result)
        if deny_payload is not None:
            write_json(artifact_dir / "deny-assignments.json", deny_payload)

        executor_oid = decode_executor_oid()
        write_json(
            artifact_dir / "execution-principal.json",
            {"object_id": executor_oid, "source": "management_access_token_oid_claim"},
        )
        assignments = run_json(
            [
                "az",
                "role",
                "assignment",
                "list",
                "--assignee-object-id",
                executor_oid,
                "--include-groups",
                "--include-inherited",
                "--all",
                "--fill-principal-name",
                "false",
                "--output",
                "json",
            ],
            artifact_dir / "execution-role-assignments.json",
        )
        role_definitions: dict[str, dict[str, Any]] = {}
        for assignment in assignments:
            role_id = str(assignment.get("roleDefinitionId") or "")
            role_name = role_id.rsplit("/", 1)[-1]
            if not role_name or role_name in role_definitions:
                continue
            role_list = run_json(
                ["az", "role", "definition", "list", "--name", role_name, "--output", "json"],
                artifact_dir / "role-definitions" / f"{role_name}.json",
            )
            if isinstance(role_list, list) and len(role_list) == 1:
                role_definitions[role_name] = role_list[0]
        write_json(artifact_dir / "execution-role-definitions.json", role_definitions)

        future_storage_id = (
            f"{group_id}/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
        )
        granting_assignments: list[dict[str, Any]] = []
        for assignment in assignments:
            scope = str(assignment.get("scope") or "")
            role_name = str(assignment.get("roleDefinitionId") or "").rsplit("/", 1)[-1]
            role = role_definitions.get(role_name)
            if (
                role
                and assignment_scope_applies(scope, future_storage_id)
                and role_grants_action(role, TARGET_RBAC_ACTION)
            ):
                granting_assignments.append(
                    {
                        "assignment_id": assignment.get("id"),
                        "scope": scope,
                        "role_definition_id": assignment.get("roleDefinitionId"),
                        "role_name": role.get("roleName"),
                    }
                )
        permission_assessment = {
            "target_action": TARGET_RBAC_ACTION,
            "target_future_storage_scope": future_storage_id,
            "declared_grant_found": bool(granting_assignments),
            "granting_assignments": granting_assignments,
            "claim_boundary": (
                "Role declaration analysis does not override deny assignments, Azure Policy, "
                "conditional access, propagation delay, or Provider validation."
            ),
        }
        write_json(artifact_dir / "execution-permission-assessment.json", permission_assessment)

        price_items, price_metadata = fetch_retail_prices(args.location)
        write_json(
            artifact_dir / "retail-prices-storage-cad.json",
            {"metadata": price_metadata, "items": price_items},
        )
        cost = estimate_cost(price_items, args.maximum_monthly_cost_cad)
        cost["evidence_sha256"] = hashlib.sha256(
            (artifact_dir / "retail-prices-storage-cad.json").read_bytes()
        ).hexdigest()
        write_json(artifact_dir / "cost-estimate.json", cost)

        template = str(
            Path(__file__).resolve().parents[1]
            / "report-publication-existing-collector.bicep"
        )
        parameters_path = str(Path(args.plan_parameters).resolve())
        provider_validation = run_capture(
            [
                "az",
                "deployment",
                "group",
                "validate",
                "--resource-group",
                args.resource_group,
                "--name",
                "existing-collector-publication-readiness",
                "--template-file",
                template,
                "--parameters",
                f"@{parameters_path}",
                "--validation-level",
                "Provider",
                "--output",
                "json",
            ]
        )
        write_json(artifact_dir / "provider-validation-command.json", provider_validation)
        provider_validation_payload = command_json_result(provider_validation)
        if provider_validation_payload is not None:
            write_json(
                artifact_dir / "provider-validation.json", provider_validation_payload
            )

        provider_what_if = run_capture(
            [
                "az",
                "deployment",
                "group",
                "what-if",
                "--resource-group",
                args.resource_group,
                "--name",
                "existing-collector-publication-readiness",
                "--template-file",
                template,
                "--parameters",
                f"@{parameters_path}",
                "--validation-level",
                "Provider",
                "--no-pretty-print",
                "--result-format",
                "FullResourcePayloads",
                "--output",
                "json",
            ]
        )
        write_json(artifact_dir / "provider-what-if-command.json", provider_what_if)
        provider_what_if_payload = command_json_result(provider_what_if)
        provider_what_if_exact = False
        if provider_what_if_payload is not None:
            write_json(artifact_dir / "provider-what-if.json", provider_what_if_payload)
            try:
                creates, _ = classify_what_if(
                    provider_what_if_payload,
                    expected_origin=args.allowed_origin,
                    expected_collector_principal=planned_principal,
                )
                provider_what_if_exact = len(creates) == 4
            except SystemExit:
                provider_what_if_exact = False

        norbac_what_if = run_capture(
            [
                "az",
                "deployment",
                "group",
                "what-if",
                "--resource-group",
                args.resource_group,
                "--name",
                "existing-collector-publication-readiness-norbac",
                "--template-file",
                template,
                "--parameters",
                f"@{parameters_path}",
                "--validation-level",
                "ProviderNoRbac",
                "--no-pretty-print",
                "--result-format",
                "FullResourcePayloads",
                "--output",
                "json",
            ]
        )
        write_json(artifact_dir / "provider-no-rbac-what-if-command.json", norbac_what_if)
        norbac_payload = command_json_result(norbac_what_if)
        norbac_exact = False
        if norbac_payload is not None:
            write_json(artifact_dir / "provider-no-rbac-what-if.json", norbac_payload)
            try:
                creates, _ = classify_what_if(
                    norbac_payload,
                    expected_origin=args.allowed_origin,
                    expected_collector_principal=planned_principal,
                )
                norbac_exact = len(creates) == 4
            except SystemExit:
                norbac_exact = False

        collector_principal = str((collector.get("identity") or {}).get("principalId") or "")
        checks = {
            "resource_group_location_matches": group.get("location") == args.location,
            "collector_provisioning_succeeded": collector.get("provisioningState")
            == "Succeeded",
            "collector_principal_unchanged": collector_principal == planned_principal,
            "report_storage_absent": len(matching_storage) == 0,
            "storage_quota_has_one_account_headroom": quota.get("one_account_available")
            is True,
            "policy_inventory_captured": policy_payload is not None,
            "deny_assignment_inventory_captured": deny_payload is not None,
            "retail_cost_estimate_under_ceiling": cost.get("under_ceiling") is True,
            "declared_role_assignment_write_grant_found": permission_assessment[
                "declared_grant_found"
            ],
            "provider_validation_succeeded": provider_validation["returncode"] == 0,
            "provider_what_if_exact_four_create": provider_what_if_exact,
            "provider_no_rbac_what_if_exact_four_create": norbac_exact,
        }
        ready = all(checks.values())
        summary = {
            "schema_version": "servicetracer.publication-readiness.v1",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "resource_group": args.resource_group,
            "location": args.location,
            "collector_vm": collector_vm,
            "planned_collector_principal_id": planned_principal,
            "current_collector_principal_id": collector_principal,
            "planned_storage_account": storage_account_name,
            "checks": checks,
            "ready_for_separate_deployment_decision": ready,
            "deployment_authorized": False,
            "azure_mutations_performed": False,
            "publisher_preflight_status": "not_run_by_design_requires_execution_authority",
            "blocking_checks": [name for name, passed in checks.items() if not passed],
            "claim_boundary": (
                "Readiness evidence does not authorize deployment. Provider validation and "
                "What-If are time-bounded and must be repeated by the execution workflow."
            ),
        }
        write_json(artifact_dir / "readiness-summary.json", summary)
        return 0
    except Exception as exc:
        write_json(
            artifact_dir / "readiness-failure.json",
            {
                "status": "evidence_capture_failed",
                "error": str(exc),
                "deployment_authorized": False,
                "azure_mutations_performed": False,
            },
        )
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
