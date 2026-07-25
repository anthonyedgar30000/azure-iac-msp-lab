#!/usr/bin/env bash
set -euo pipefail

MODE="${1:---plan}"
[[ "$MODE" == "--plan" || "$MODE" == "--apply" ]] || {
  echo "usage: $0 [--plan|--apply]" >&2
  exit 2
}

RESOURCE_GROUP="${RESOURCE_GROUP:-rg-st-demo-api-dev-westus2}"
LOCATION="${LOCATION:-westus2}"
VM_NAME="${VM_NAME:-vm-st-demo-api-mst-dev}"
EXTENSION_NAME="${EXTENSION_NAME:-servicetracer-demo-api}"
PLANNER_ROLE_NAME="${PLANNER_ROLE_NAME:-ServiceTracer Demo API What-If Planner v1}"
ROLE_NAME="ServiceTracer Demo API Extension Updater v1"
ROLE_DEFINITION_GUID="a94875a8-373d-531e-bfe0-b213fd936082"
TEMPLATE_FILE="infra/rbac/servicetracer-demo-api-extension-updater-rbac.bicep"
ASSERT_SCRIPT="scripts/assert_servicetracer_extension_updater_rbac_what_if.py"
EVIDENCE_DIR="${EVIDENCE_DIR:-$HOME/servicetracer-extension-updater-rbac-evidence}"

mkdir -p "$EVIDENCE_DIR"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
evidence="$EVIDENCE_DIR/$timestamp"
mkdir -p "$evidence"

account_json="$(az account show -o json)"
subscription_id="$(jq -r '.id' <<<"$account_json")"
tenant_id="$(jq -r '.tenantId' <<<"$account_json")"
account_state="$(jq -r '.state' <<<"$account_json")"
[[ "$account_state" == "Enabled" ]]

if [[ -n "${TARGET_SUBSCRIPTION_ID:-}" ]]; then
  [[ "$subscription_id" == "$TARGET_SUBSCRIPTION_ID" ]] || {
    echo "Current subscription does not match TARGET_SUBSCRIPTION_ID." >&2
    exit 1
  }
fi
if [[ -n "${TARGET_TENANT_ID:-}" ]]; then
  [[ "$tenant_id" == "$TARGET_TENANT_ID" ]] || {
    echo "Current tenant does not match TARGET_TENANT_ID." >&2
    exit 1
  }
fi

rg_json="$(az group show -g "$RESOURCE_GROUP" -o json)"
rg_id="$(jq -r '.id' <<<"$rg_json")"
[[ "$(jq -r '.location' <<<"$rg_json")" == "$LOCATION" ]]
[[ "$(jq -r '.properties.provisioningState' <<<"$rg_json")" == "Succeeded" ]]

vm_json="$(az vm show -g "$RESOURCE_GROUP" -n "$VM_NAME" -o json)"
vm_id="$(jq -r '.id' <<<"$vm_json")"
[[ "$(jq -r '.provisioningState' <<<"$vm_json")" == "Succeeded" ]]

extension_json="$(az vm extension show -g "$RESOURCE_GROUP" --vm-name "$VM_NAME" -n "$EXTENSION_NAME" -o json)"
extension_id="$(jq -r '.id' <<<"$extension_json")"
[[ "$(jq -r '.provisioningState' <<<"$extension_json")" == "Succeeded" ]]
[[ "$extension_id" == "$vm_id/extensions/$EXTENSION_NAME" ]]

planner_role_id="$(az role definition list --name "$PLANNER_ROLE_NAME" --query '[0].id' -o tsv)"
[[ -n "$planner_role_id" ]] || {
  echo "Planner role definition was not found." >&2
  exit 1
}

az role assignment list \
  --scope "$rg_id" \
  --include-inherited \
  -o json > "$evidence/inherited-role-assignments.json"

mapfile -t principal_ids < <(
  jq -r --arg role_id "$planner_role_id" '
    [
      .[]
      | select((.roleDefinitionId | ascii_downcase) == ($role_id | ascii_downcase))
      | select(.principalType == "ServicePrincipal")
      | .principalId
    ]
    | unique
    | .[]
  ' "$evidence/inherited-role-assignments.json"
)
[[ "${#principal_ids[@]}" -eq 1 ]] || {
  echo "Expected exactly one service principal with the planner role; found ${#principal_ids[@]}." >&2
  exit 1
}
principal_id="${principal_ids[0]}"

role_definition_id="/subscriptions/$subscription_id/providers/Microsoft.Authorization/roleDefinitions/$ROLE_DEFINITION_GUID"
deployment_name="st-extension-updater-rbac-$timestamp"

jq -n \
  --arg subscription_sha256 "$(printf '%s' "$subscription_id" | sha256sum | awk '{print $1}')" \
  --arg tenant_sha256 "$(printf '%s' "$tenant_id" | sha256sum | awk '{print $1}')" \
  --arg principal_sha256 "$(printf '%s' "$principal_id" | sha256sum | awk '{print $1}')" \
  --arg resource_group "$RESOURCE_GROUP" \
  --arg resource_group_id "$rg_id" \
  --arg vm "$VM_NAME" \
  --arg extension "$EXTENSION_NAME" \
  --arg extension_scope "$extension_id" \
  --arg planner_role_id "$planner_role_id" \
  --arg role_name "$ROLE_NAME" \
  --arg role_definition_id "$role_definition_id" \
  --arg mode "$MODE" \
  '{
    status:"preflight_verified",
    mode:$mode,
    subscription_sha256:$subscription_sha256,
    tenant_sha256:$tenant_sha256,
    principal_sha256:$principal_sha256,
    resource_group:$resource_group,
    resource_group_id:$resource_group_id,
    vm:$vm,
    extension:$extension,
    assignment_scope:$extension_scope,
    planner_role_definition_id:$planner_role_id,
    new_role_name:$role_name,
    new_role_definition_id:$role_definition_id,
    exact_action:"Microsoft.Compute/virtualMachines/extensions/write"
  }' > "$evidence/preflight.json"

az deployment sub what-if \
  --location "$LOCATION" \
  --name "$deployment_name-whatif" \
  --template-file "$TEMPLATE_FILE" \
  --parameters \
    resourceGroupName="$RESOURCE_GROUP" \
    vmName="$VM_NAME" \
    extensionName="$EXTENSION_NAME" \
    principalId="$principal_id" \
    roleDefinitionGuid="$ROLE_DEFINITION_GUID" \
  --no-pretty-print \
  --result-format FullResourcePayloads \
  -o json > "$evidence/what-if.json"

python3 "$ASSERT_SCRIPT" \
  "$evidence/what-if.json" \
  --role-definition-guid "$ROLE_DEFINITION_GUID" \
  --extension-scope "$extension_id" \
  --output "$evidence/what-if-assessment.json"

if [[ "$MODE" == "--plan" ]]; then
  jq -n --arg evidence "$evidence" \
    '{status:"planned_not_applied",azure_mutation_performed:false,evidence_directory:$evidence}' \
    | tee "$evidence/result.json"
  exit 0
fi

az deployment sub create \
  --location "$LOCATION" \
  --name "$deployment_name-apply" \
  --template-file "$TEMPLATE_FILE" \
  --parameters \
    resourceGroupName="$RESOURCE_GROUP" \
    vmName="$VM_NAME" \
    extensionName="$EXTENSION_NAME" \
    principalId="$principal_id" \
    roleDefinitionGuid="$ROLE_DEFINITION_GUID" \
  -o json > "$evidence/deployment.json"

az role definition list --name "$ROLE_NAME" -o json > "$evidence/role-definition-after.json"
az role assignment list \
  --scope "$extension_id" \
  --assignee-object-id "$principal_id" \
  --role "$role_definition_id" \
  -o json > "$evidence/role-assignment-after.json"

jq -e --arg role_id "$role_definition_id" --arg rg_id "$rg_id" '
  length == 1 and
  .[0].id == $role_id and
  .[0].roleName == "ServiceTracer Demo API Extension Updater v1" and
  .[0].permissions == [{
    actions:["Microsoft.Compute/virtualMachines/extensions/write"],
    notActions:[],
    dataActions:[],
    notDataActions:[]
  }] and
  .[0].assignableScopes == [$rg_id]
' "$evidence/role-definition-after.json" >/dev/null

jq -e --arg extension_id "$extension_id" --arg principal_id "$principal_id" --arg role_id "$role_definition_id" '
  length == 1 and
  .[0].scope == $extension_id and
  .[0].principalId == $principal_id and
  .[0].roleDefinitionId == $role_id
' "$evidence/role-assignment-after.json" >/dev/null

deny_uri="${extension_id}/providers/Microsoft.Authorization/denyAssignments?api-version=2022-04-01"
set +e
az rest --method get --uri "$deny_uri" -o json > "$evidence/deny-assignments.json" 2> "$evidence/deny-assignments.error.txt"
deny_status=$?
set -e

jq -n \
  --arg evidence "$evidence" \
  --arg role_definition_id "$role_definition_id" \
  --arg assignment_scope "$extension_id" \
  --argjson deny_query_exit_status "$deny_status" \
  '{
    status:"role_definition_and_assignment_created",
    azure_rbac_mutation_performed:true,
    role_definition_id:$role_definition_id,
    assignment_scope:$assignment_scope,
    exact_action:"Microsoft.Compute/virtualMachines/extensions/write",
    deny_assignment_query_exit_status:$deny_query_exit_status,
    effective_permission_verified_by_target_identity:false,
    deployment_authorized:false,
    evidence_directory:$evidence,
    claim_boundary:"Role definition and assignment existence are verified. Effective use by the GitHub OIDC target identity requires a separate protected preflight; assignment existence is not deployment authorization."
  }' | tee "$evidence/result.json"

find "$evidence" -type f ! -name artifact-manifest.sha256 -print0 \
  | sort -z | xargs -0 -r sha256sum > "$evidence/artifact-manifest.sha256"
