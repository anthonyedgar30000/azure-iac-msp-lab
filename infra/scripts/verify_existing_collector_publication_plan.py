from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

BLOB_DATA_CONTRIBUTOR_ROLE_ID = "ba92f5b4-2d11-453d-a403-e96b0029c9fe"
PROTECTED_PROVIDER_PREFIXES = (
    "Microsoft.Compute/",
    "Microsoft.Network/",
    "Microsoft.OperationalInsights/",
)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid JSON evidence {path}: {exc}") from exc


def verify_manifest(directory: Path) -> int:
    manifest = directory / "artifact-manifest.sha256"
    if not manifest.is_file():
        raise SystemExit("Planner artifact is missing artifact-manifest.sha256")

    verified = 0
    seen: set[str] = set()
    for raw_line in manifest.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            expected, recorded_path = line.split(maxsplit=1)
        except ValueError as exc:
            raise SystemExit(f"Invalid manifest line: {raw_line!r}") from exc

        basename = Path(recorded_path.lstrip("* ")).name
        if basename in seen:
            raise SystemExit(f"Duplicate manifest basename: {basename}")
        seen.add(basename)

        candidate = directory / basename
        if not candidate.is_file():
            raise SystemExit(f"Manifest file missing after artifact extraction: {basename}")
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"Manifest digest mismatch for {basename}")
        verified += 1

    if verified < 10:
        raise SystemExit(f"Planner artifact manifest verified only {verified} files")
    return verified


def _single_create(creates: list[dict[str, Any]], resource_type: str) -> dict[str, Any]:
    matches = [item for item in creates if item.get("after", {}).get("type") == resource_type]
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one Create for {resource_type}, found {len(matches)}")
    return matches[0]


def classify_what_if(
    payload: dict[str, Any],
    *,
    expected_origin: str,
    expected_collector_principal: str,
) -> tuple[list[dict[str, Any]], str]:
    if payload.get("status") != "Succeeded" or payload.get("error") is not None:
        raise SystemExit("ARM What-If did not complete successfully")

    changes = payload.get("changes")
    if not isinstance(changes, list):
        raise SystemExit("ARM What-If changes must be an array")

    forbidden = [
        item
        for item in changes
        if item.get("changeType") not in {"Create", "Ignore", "NoChange"}
    ]
    if forbidden:
        raise SystemExit(
            "ARM What-If contains forbidden changes: "
            + ", ".join(str(item.get("resourceId")) for item in forbidden)
        )

    creates = [item for item in changes if item.get("changeType") == "Create"]
    if len(creates) != 4:
        raise SystemExit(f"Expected exactly four Create changes, found {len(creates)}")

    storage = _single_create(creates, "Microsoft.Storage/storageAccounts")
    blob = _single_create(creates, "Microsoft.Storage/storageAccounts/blobServices")
    container = _single_create(
        creates,
        "Microsoft.Storage/storageAccounts/blobServices/containers",
    )
    role = _single_create(creates, "Microsoft.Authorization/roleAssignments")

    storage_id = str(storage.get("resourceId") or "")
    blob_id = str(blob.get("resourceId") or "")
    container_id = str(container.get("resourceId") or "")
    role_id = str(role.get("resourceId") or "")
    if not storage_id:
        raise SystemExit("Storage account Create has no resource ID")
    if blob_id != f"{storage_id}/blobServices/default":
        raise SystemExit("Blob service is not scoped to the planned report Storage account")
    if container_id != f"{storage_id}/blobServices/default/containers/$web":
        raise SystemExit("$web container is not scoped to the planned Blob service")
    if not role_id.startswith(
        f"{storage_id}/providers/Microsoft.Authorization/roleAssignments/"
    ):
        raise SystemExit("Role assignment is not scoped to the planned report Storage account")

    storage_after = storage.get("after", {})
    storage_properties = storage_after.get("properties", {})
    if storage_after.get("kind") != "StorageV2":
        raise SystemExit("Planned report Storage account is not StorageV2")
    if storage_after.get("sku", {}).get("name") != "Standard_LRS":
        raise SystemExit("Planned report Storage account is not Standard_LRS")
    expected_storage_properties = {
        "allowBlobPublicAccess": True,
        "allowSharedKeyAccess": False,
        "defaultToOAuthAuthentication": True,
        "minimumTlsVersion": "TLS1_2",
        "publicNetworkAccess": "Enabled",
        "supportsHttpsTrafficOnly": True,
    }
    for name, expected in expected_storage_properties.items():
        if storage_properties.get(name) != expected:
            raise SystemExit(f"Planned Storage property {name} differs from the reviewed contract")

    blob_properties = blob.get("after", {}).get("properties", {})
    cors_rules = blob_properties.get("cors", {}).get("corsRules", [])
    if len(cors_rules) != 1:
        raise SystemExit("Planned Blob service must contain exactly one CORS rule")
    cors = cors_rules[0]
    if cors.get("allowedOrigins") != [expected_origin]:
        raise SystemExit("Planned Blob CORS origin differs from the reviewed origin")
    if sorted(cors.get("allowedMethods") or []) != ["GET", "HEAD", "OPTIONS"]:
        raise SystemExit("Planned Blob CORS methods differ from GET, HEAD, OPTIONS")
    if blob_properties.get("isVersioningEnabled") is not True:
        raise SystemExit("Planned Blob versioning is not enabled")
    retention = blob_properties.get("deleteRetentionPolicy", {})
    if retention.get("enabled") is not True or retention.get("days") != 7:
        raise SystemExit("Planned Blob deletion retention differs from seven days")

    container_properties = container.get("after", {}).get("properties", {})
    if container_properties.get("publicAccess") != "Blob":
        raise SystemExit("Planned $web container is not Blob-only anonymous read")

    role_properties = role.get("after", {}).get("properties", {})
    if str(role_properties.get("principalId") or "").lower() != expected_collector_principal.lower():
        raise SystemExit("Planned role principal differs from the observed collector identity")
    if not str(role_properties.get("roleDefinitionId") or "").lower().endswith(
        BLOB_DATA_CONTRIBUTOR_ROLE_ID
    ):
        raise SystemExit("Planned role is not Storage Blob Data Contributor")

    for item in changes:
        resource_id = str(item.get("resourceId") or "")
        provider_path = resource_id.split("/providers/", 1)[-1]
        if (
            provider_path.startswith(PROTECTED_PROVIDER_PREFIXES)
            and item.get("changeType") not in {"Ignore", "NoChange"}
        ):
            raise SystemExit(f"Protected infrastructure would change: {resource_id}")

    return creates, storage_id


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the successful read-only publication plan artifact"
    )
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--expected-run-id", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-resource-group", required=True)
    parser.add_argument("--expected-location", required=True)
    parser.add_argument("--expected-prefix", required=True)
    parser.add_argument("--expected-environment", required=True)
    parser.add_argument("--expected-allowed-origin", required=True)
    parser.add_argument("--expected-collector-vm", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    directory = Path(args.artifact_dir)
    verified_files = verify_manifest(directory)
    request = load_json(directory / "request.json")
    summary = load_json(directory / "plan-summary.json")
    validation = load_json(directory / "arm-validation.json")
    what_if = load_json(directory / "arm-what-if.json")
    existing_storage = load_json(directory / "existing-report-storage.json")
    collector_roles = load_json(directory / "visible-collector-role-assignments.json")
    parameters = load_json(directory / "deployment-parameters.json")

    if request.get("operation") != "existing_collector_report_publication_plan":
        raise SystemExit("Planner request operation is unexpected")
    if request.get("azure_mutations_authorized") is not False:
        raise SystemExit("Planner request unexpectedly authorizes Azure mutations")
    if request.get("reviewed_commit") != args.expected_commit:
        raise SystemExit("Planner request commit does not match the pinned commit")
    if request.get("resource_group") != args.expected_resource_group:
        raise SystemExit("Planner request resource group does not match")
    if summary.get("resource_group") != args.expected_resource_group:
        raise SystemExit("Planner summary resource group does not match")
    if summary.get("location") != args.expected_location:
        raise SystemExit("Planner summary location does not match")
    if summary.get("collector_vm") != args.expected_collector_vm:
        raise SystemExit("Planner summary collector VM does not match")

    collector_principal = str(summary.get("collector_principal_id") or "")
    expected_parameter_values = {
        "prefix": args.expected_prefix,
        "environment": args.expected_environment,
        "location": args.expected_location,
        "collectorPrincipalId": collector_principal,
        "allowedOrigins": [args.expected_allowed_origin],
    }
    parameter_values = parameters.get("parameters", {})
    for name, expected in expected_parameter_values.items():
        actual = parameter_values.get(name, {}).get("value")
        if actual != expected:
            raise SystemExit(f"Planner deployment parameter {name} does not match")

    if summary.get("arm_validation") != "completed" or summary.get("arm_what_if") != "completed":
        raise SystemExit("Planner did not complete validation and What-If")
    if summary.get("arm_validation_level") != "ProviderNoRbac":
        raise SystemExit("Planner did not use ProviderNoRbac")
    if summary.get("rbac_deployment_authorized") is not False:
        raise SystemExit("Planner artifact unexpectedly authorizes RBAC deployment")
    if summary.get("deployment_authorized") is not False:
        raise SystemExit("Planner artifact unexpectedly authorizes deployment")
    if summary.get("azure_mutations_performed") is not False:
        raise SystemExit("Planner artifact violates the no-mutation boundary")
    if existing_storage != [] or collector_roles != []:
        raise SystemExit("Planner baseline is not a clean first-deployment state")
    if validation.get("properties", {}).get("provisioningState") != "Succeeded":
        raise SystemExit("ARM validation evidence did not succeed")
    if validation.get("properties", {}).get("validationLevel") != "ProviderNoRbac":
        raise SystemExit("ARM validation evidence used the wrong validation level")

    creates, storage_id = classify_what_if(
        what_if,
        expected_origin=args.expected_allowed_origin,
        expected_collector_principal=collector_principal,
    )
    output = {
        "schema_version": "servicetracer.publication-plan-verification.v2",
        "planner_run_id": str(args.expected_run_id),
        "planner_commit": args.expected_commit,
        "verified_manifest_files": verified_files,
        "resource_group": args.expected_resource_group,
        "location": args.expected_location,
        "prefix": args.expected_prefix,
        "environment": args.expected_environment,
        "allowed_origin": args.expected_allowed_origin,
        "collector_vm": args.expected_collector_vm,
        "collector_principal_id": collector_principal,
        "storage_account_name": storage_id.rsplit("/", 1)[-1],
        "storage_account_id": storage_id,
        "public_report_container": "$web",
        "create_change_count": len(creates),
        "allowed_change_types": ["Create", "Ignore", "NoChange"],
        "deployment_authorized_by_planner": False,
    }
    Path(args.output).write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
