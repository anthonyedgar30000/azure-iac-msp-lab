#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  plan_existing_collector_report_publication.sh \
    --resource-group <name> \
    --location <region> \
    --prefix <prefix> \
    --environment <dev|test> \
    --allowed-origin <https-origin> \
    --artifact-dir <directory> \
    [--maximum-monthly-cost-cad <amount>]

This command is read-only. It resolves the existing collector identity, captures
current Azure context, runs ARM validation and What-If for the dedicated report
publication template, and records the unresolved current-price boundary. It does
not deploy, update, delete, publish a report, or alter RBAC.
USAGE
}

fail() {
  echo "$1" >&2
  exit "${2:-1}"
}

resource_group=''
location=''
prefix=''
environment=''
allowed_origin=''
artifact_dir=''
maximum_monthly_cost_cad='10.00'

declare -a temporary_evidence_files=()
cleanup_temporary_evidence() {
  if ((${#temporary_evidence_files[@]} > 0)); then
    rm -f -- "${temporary_evidence_files[@]}"
  fi
}
trap cleanup_temporary_evidence EXIT

capture_json() {
  local expected_type="$1"
  local destination="$2"
  shift 2

  local temp_path
  temp_path="$(mktemp "${destination}.partial.XXXXXX")"
  temporary_evidence_files+=("$temp_path")

  if ! "$@" > "$temp_path"; then
    echo "Failed to capture evidence for: $destination" >&2
    rm -f -- "$temp_path"
    return 1
  fi

  if [[ ! -s "$temp_path" ]]; then
    echo "Refusing empty evidence for: $destination" >&2
    rm -f -- "$temp_path"
    return 1
  fi

  if ! jq -e --arg expected_type "$expected_type" \
    'type == $expected_type' "$temp_path" >/dev/null; then
    echo "Refusing invalid or unexpected JSON evidence for: $destination" >&2
    rm -f -- "$temp_path"
    return 1
  fi

  mv -- "$temp_path" "$destination"
}

while (($# > 0)); do
  case "$1" in
    --resource-group)
      resource_group="${2:-}"
      shift 2
      ;;
    --location)
      location="${2:-}"
      shift 2
      ;;
    --prefix)
      prefix="${2:-}"
      shift 2
      ;;
    --environment)
      environment="${2:-}"
      shift 2
      ;;
    --allowed-origin)
      allowed_origin="${2:-}"
      shift 2
      ;;
    --artifact-dir)
      artifact_dir="${2:-}"
      shift 2
      ;;
    --maximum-monthly-cost-cad)
      maximum_monthly_cost_cad="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

for value_name in resource_group location prefix environment allowed_origin artifact_dir; do
  if [[ -z "${!value_name}" ]]; then
    echo "Missing required argument: ${value_name//_/-}" >&2
    usage >&2
    exit 2
  fi
done

[[ "$resource_group" =~ ^rg-servicetracer-(dev|test)(-[a-z0-9-]+)?$ ]] || \
  fail 'Resource group is outside the bounded ServiceTracer naming contract.' 2
[[ "$location" =~ ^[a-z0-9]+$ ]] || \
  fail 'Location must contain lowercase letters and digits only.' 2
[[ "$prefix" =~ ^[a-z0-9]{2,12}$ ]] || \
  fail 'Prefix must contain 2-12 lowercase letters or digits.' 2
[[ "$environment" =~ ^(dev|test)$ ]] || \
  fail 'Environment must be dev or test.' 2
[[ "$allowed_origin" =~ ^https://[A-Za-z0-9.-]+(:[0-9]+)?$ ]] || \
  fail 'Allowed origin must be an HTTPS origin without a path.' 2
[[ "$maximum_monthly_cost_cad" =~ ^[0-9]+([.][0-9]{1,2})?$ ]] || \
  fail 'Maximum monthly cost must be a non-negative CAD amount.' 2
awk -v amount="$maximum_monthly_cost_cad" \
  'BEGIN { exit !(amount <= 10.00) }' || \
  fail 'Maximum monthly cost ceiling cannot exceed CAD 10.00.' 2

for command_name in az jq awk mktemp; do
  command -v "$command_name" >/dev/null 2>&1 || \
    fail "Required command is unavailable: $command_name" 127
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
template="$repo_root/infra/report-publication-existing-collector.bicep"
[[ -f "$template" ]] || fail "Missing template: $template"

mkdir -p "$artifact_dir"
collector_vm="vm-stcollector-${prefix}-${environment}"
observed_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

capture_json object "$artifact_dir/azure-context.json" \
  az account show \
    --query '{subscription_id:id,subscription_name:name,tenant_id:tenantId,cloud:environmentName,user_type:user.type}' \
    --output json

capture_json object "$artifact_dir/resource-group.json" \
  az group show \
    --name "$resource_group" \
    --output json

actual_location="$(jq -r '.location' "$artifact_dir/resource-group.json")"
[[ "$actual_location" == "$location" ]] || \
  fail "Resource group is in $actual_location, not $location."
[[ "$(jq -r '.tags.workload // empty' "$artifact_dir/resource-group.json")" == \
  'azure-iac-msp-lab' ]] || \
  fail 'Resource group workload tag does not match azure-iac-msp-lab.'
[[ "$(jq -r '.tags.purpose // empty' "$artifact_dir/resource-group.json")" == \
  'servicetracer-demo' ]] || \
  fail 'Resource group purpose tag does not match servicetracer-demo.'
resource_group_id="$(jq -r '.id' "$artifact_dir/resource-group.json")"

capture_json object "$artifact_dir/existing-collector.json" \
  az vm show \
    --resource-group "$resource_group" \
    --name "$collector_vm" \
    --query '{id:id,name:name,location:location,provisioning_state:provisioningState,vm_size:hardwareProfile.vmSize,identity_type:identity.type,principal_id:identity.principalId,image:storageProfile.imageReference}' \
    --output json

jq -e --arg location "$location" '
  .id != null and
  .name != null and
  .location == $location and
  .provisioning_state == "Succeeded" and
  (.identity_type | type == "string") and
  (.identity_type | contains("SystemAssigned")) and
  (.principal_id | type == "string" and length == 36)
' "$artifact_dir/existing-collector.json" >/dev/null || \
  fail 'Existing collector does not have a usable system-assigned identity in the expected location.'

collector_principal_id="$(jq -r '.principal_id' "$artifact_dir/existing-collector.json")"
[[ "$collector_principal_id" =~ ^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$ ]] || \
  fail 'Existing collector principal ID is not a canonical GUID.'

capture_json array "$artifact_dir/existing-report-storage.json" \
  az storage account list \
    --resource-group "$resource_group" \
    --query "[?tags.component=='servicetracer-public-report'].{id:id,name:name,location:location,provisioning_state:provisioningState,public_network_access:publicNetworkAccess,allow_blob_public_access:allowBlobPublicAccess,allow_shared_key_access:allowSharedKeyAccess}" \
    --output json

existing_storage_count="$(jq 'length' "$artifact_dir/existing-report-storage.json")"
((existing_storage_count <= 1)) || \
  fail 'More than one report Storage account is already tagged in the resource group; refusing ambiguous planning.'

capture_json array "$artifact_dir/visible-resource-group-role-assignments-all.json" \
  az role assignment list \
    --scope "$resource_group_id" \
    --include-inherited \
    --output json

if ((existing_storage_count == 1)); then
  existing_storage_id="$(jq -r '.[0].id' "$artifact_dir/existing-report-storage.json")"
  capture_json array "$artifact_dir/visible-report-storage-role-assignments-all.json" \
    az role assignment list \
      --scope "$existing_storage_id" \
      --include-inherited \
      --output json
else
  capture_json array "$artifact_dir/visible-report-storage-role-assignments-all.json" \
    printf '[]\n'
fi

capture_json array "$artifact_dir/visible-collector-role-assignments.json" \
  jq -s --arg principal_id "$collector_principal_id" '
    [
      .[0][],
      .[1][]
      | select(.principalId == $principal_id)
      | {
          id: .id,
          scope: .scope,
          role_definition_name: .roleDefinitionName,
          principal_id: .principalId
        }
    ]
    | unique_by(.id)
  ' \
    "$artifact_dir/visible-resource-group-role-assignments-all.json" \
    "$artifact_dir/visible-report-storage-role-assignments-all.json"
visible_collector_role_assignment_count="$(jq 'length' "$artifact_dir/visible-collector-role-assignments.json")"

jq -n \
  --arg prefix "$prefix" \
  --arg environment "$environment" \
  --arg location "$location" \
  --arg collectorPrincipalId "$collector_principal_id" \
  --arg allowedOrigin "$allowed_origin" \
  '{
    "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
    contentVersion: "1.0.0.0",
    parameters: {
      prefix: {value: $prefix},
      environment: {value: $environment},
      location: {value: $location},
      collectorPrincipalId: {value: $collectorPrincipalId},
      allowedOrigins: {value: [$allowedOrigin]},
      tags: {value: {
        workload: "azure-iac-msp-lab",
        environment: $environment,
        managedBy: "bicep",
        purpose: "servicetracer-live-report",
        changeScope: "existing-collector-publication-only"
      }}
    }
  }' > "$artifact_dir/deployment-parameters.json"

capture_json object "$artifact_dir/arm-validation.json" \
  az deployment group validate \
    --resource-group "$resource_group" \
    --template-file "$template" \
    --parameters "@$artifact_dir/deployment-parameters.json" \
    --output json

capture_json object "$artifact_dir/arm-what-if.json" \
  az deployment group what-if \
    --resource-group "$resource_group" \
    --template-file "$template" \
    --parameters "@$artifact_dir/deployment-parameters.json" \
    --result-format FullResourcePayloads \
    --no-pretty-print \
    --output json

jq -n \
  --arg observed_at "$observed_at" \
  --arg ceiling "$maximum_monthly_cost_cad" \
  '{
    observed_at: $observed_at,
    currency: "CAD",
    maximum_monthly_cost_ceiling: ($ceiling | tonumber),
    current_price_evidence: null,
    estimate_status: "unresolved_requires_fresh_region_and_subscription_specific_price_evidence",
    deployment_blocked_until_price_review: true,
    claim_boundary: "ARM validation and What-If do not provide a current price quotation or actual-cost evidence."
  }' > "$artifact_dir/cost-boundary.json"

jq -n \
  --arg observed_at "$observed_at" \
  --arg resource_group "$resource_group" \
  --arg location "$location" \
  --arg collector_vm "$collector_vm" \
  --arg collector_principal_id "$collector_principal_id" \
  --arg allowed_origin "$allowed_origin" \
  --arg template "$template" \
  --argjson existing_storage_count "$existing_storage_count" \
  --argjson visible_role_assignment_count "$visible_collector_role_assignment_count" \
  '{
    schema_version: "servicetracer.existing-collector-report-plan.v1",
    observed_at: $observed_at,
    operation: "read_only_plan",
    resource_group: $resource_group,
    location: $location,
    collector_vm: $collector_vm,
    collector_principal_id: $collector_principal_id,
    allowed_origin: $allowed_origin,
    template: $template,
    existing_report_storage_count: $existing_storage_count,
    visible_collector_role_assignment_count: $visible_role_assignment_count,
    arm_validation: "completed",
    arm_what_if: "completed",
    current_price_review: "required_before_deployment",
    deployment_authorized: false,
    azure_mutations_performed: false,
    next_gate: "Review the What-If, obtain fresh cost evidence and explicit mutation authorization, then promote a separately reviewed execution workflow."
  }' > "$artifact_dir/plan-summary.json"

cat "$artifact_dir/plan-summary.json"
