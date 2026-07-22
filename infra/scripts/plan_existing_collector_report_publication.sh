#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
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
EOF
}

resource_group=''
location=''
prefix=''
environment=''
allowed_origin=''
artifact_dir=''
maximum_monthly_cost_cad='10.00'

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

[[ "$resource_group" =~ ^rg-servicetracer-(dev|test)(-[a-z0-9-]+)?$ ]] || {
  echo 'Resource group is outside the bounded ServiceTracer naming contract.' >&2
  exit 2
}
[[ "$location" =~ ^[a-z0-9]+$ ]] || {
  echo 'Location must contain lowercase letters and digits only.' >&2
  exit 2
}
[[ "$prefix" =~ ^[a-z0-9]{2,12}$ ]] || {
  echo 'Prefix must contain 2-12 lowercase letters or digits.' >&2
  exit 2
}
[[ "$environment" =~ ^(dev|test)$ ]] || {
  echo 'Environment must be dev or test.' >&2
  exit 2
}
[[ "$allowed_origin" =~ ^https://[A-Za-z0-9.-]+(:[0-9]+)?$ ]] || {
  echo 'Allowed origin must be an HTTPS origin without a path.' >&2
  exit 2
}
[[ "$maximum_monthly_cost_cad" =~ ^[0-9]+([.][0-9]{1,2})?$ ]] || {
  echo 'Maximum monthly cost must be a non-negative CAD amount.' >&2
  exit 2
}
awk -v amount="$maximum_monthly_cost_cad" 'BEGIN { exit !(amount <= 10.00) }' || {
  echo 'Maximum monthly cost ceiling cannot exceed CAD 10.00.' >&2
  exit 2
}

for command_name in az jq; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Required command is unavailable: $command_name" >&2
    exit 127
  }
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
template="$repo_root/infra/report-publication-existing-collector.bicep"
[[ -f "$template" ]] || {
  echo "Missing template: $template" >&2
  exit 1
}

mkdir -p "$artifact_dir"
collector_vm="vm-stcollector-${prefix}-${environment}"
observed_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

az account show \
  --query '{subscription_id:id,subscription_name:name,tenant_id:tenantId,cloud:environmentName,user_type:user.type}' \
  --output json > "$artifact_dir/azure-context.json"

az group show \
  --name "$resource_group" \
  --output json > "$artifact_dir/resource-group.json"

actual_location="$(jq -r '.location' "$artifact_dir/resource-group.json")"
[[ "$actual_location" == "$location" ]] || {
  echo "Resource group is in $actual_location, not $location." >&2
  exit 1
}
[[ "$(jq -r '.tags.workload // empty' "$artifact_dir/resource-group.json")" == 'azure-iac-msp-lab' ]] || {
  echo 'Resource group workload tag does not match azure-iac-msp-lab.' >&2
  exit 1
}
[[ "$(jq -r '.tags.purpose // empty' "$artifact_dir/resource-group.json")" == 'servicetracer-demo' ]] || {
  echo 'Resource group purpose tag does not match servicetracer-demo.' >&2
  exit 1
}
resource_group_id="$(jq -r '.id' "$artifact_dir/resource-group.json")"

az vm show \
  --resource-group "$resource_group" \
  --name "$collector_vm" \
  --query '{id:id,name:name,location:location,provisioning_state:provisioningState,vm_size:hardwareProfile.vmSize,identity_type:identity.type,principal_id:identity.principalId,image:storageProfile.imageReference}' \
  --output json > "$artifact_dir/existing-collector.json"

jq -e --arg location "$location" '
  .id != null and
  .name != null and
  .location == $location and
  .provisioning_state == "Succeeded" and
  (.identity_type | type == "string") and
  (.identity_type | contains("SystemAssigned")) and
  (.principal_id | type == "string" and length == 36)
' "$artifact_dir/existing-collector.json" >/dev/null || {
  echo 'Existing collector does not have a usable system-assigned identity in the expected location.' >&2
  exit 1
}
collector_principal_id="$(jq -r '.principal_id' "$artifact_dir/existing-collector.json")"

az storage account list \
  --resource-group "$resource_group" \
  --query "[?tags.component=='servicetracer-public-report'].{id:id,name:name,location:location,provisioning_state:provisioningState,public_network_access:publicNetworkAccess,allow_blob_public_access:allowBlobPublicAccess,allow_shared_key_access:allowSharedKeyAccess}" \
  --output json > "$artifact_dir/existing-report-storage.json"

az role assignment list \
  --assignee-object-id "$collector_principal_id" \
  --scope "$resource_group_id" \
  --include-inherited \
  --all \
  --query '[].{id:id,scope:scope,role_definition_name:roleDefinitionName,principal_id:principalId}' \
  --output json > "$artifact_dir/visible-collector-role-assignments.json"

jq -n \
  --arg prefix "$prefix" \
  --arg environment "$environment" \
  --arg location "$location" \
  --arg collectorPrincipalId "$collector_principal_id" \
  --arg allowedOrigin "$allowed_origin" \
  '{
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
  }' > "$artifact_dir/deployment-parameters.json"

az deployment group validate \
  --resource-group "$resource_group" \
  --template-file "$template" \
  --parameters "@$artifact_dir/deployment-parameters.json" \
  --output json > "$artifact_dir/arm-validation.json"

az deployment group what-if \
  --resource-group "$resource_group" \
  --template-file "$template" \
  --parameters "@$artifact_dir/deployment-parameters.json" \
  --result-format FullResourcePayloads \
  --no-pretty-print \
  --output json > "$artifact_dir/arm-what-if.json"

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
  --argjson existing_storage_count "$(jq 'length' "$artifact_dir/existing-report-storage.json")" \
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
    arm_validation: "completed",
    arm_what_if: "completed",
    current_price_review: "required_before_deployment",
    deployment_authorized: false,
    azure_mutations_performed: false,
    next_gate: "Review the What-If, obtain fresh cost evidence and explicit mutation authorization, then promote a separately reviewed execution workflow."
  }' > "$artifact_dir/plan-summary.json"

cat "$artifact_dir/plan-summary.json"
