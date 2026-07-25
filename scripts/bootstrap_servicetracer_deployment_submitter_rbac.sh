#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bootstrap_servicetracer_deployment_submitter_rbac.sh --principal-object-id <object-id> [--apply]

Without --apply, the script performs subscription-scope validation and What-If only.
--apply performs the reviewed custom-role definition and resource-group assignment.
EOF
}

principal_object_id=''
apply=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --principal-object-id)
      principal_object_id="${2:-}"
      shift 2
      ;;
    --apply)
      apply=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

[[ "$principal_object_id" =~ ^[0-9a-fA-F-]{36}$ ]] || {
  echo "--principal-object-id must be a GUID" >&2
  exit 2
}

resource_group='rg-st-demo-api-dev-westus2'
location='westus2'
template='infra/rbac/servicetracer-demo-api-deployment-submitter-rbac.bicep'
evidence_dir='servicetracer-deployment-submitter-rbac-evidence'
deployment_name="servicetracer-deployment-submitter-rbac-$(date -u +%Y%m%d%H%M%S)"
mkdir -p "$evidence_dir"

az account show --query '{id:id,tenantId:tenantId,state:state,name:name}' -o json \
  > "$evidence_dir/account.json"
test "$(jq -r '.state' "$evidence_dir/account.json")" = 'Enabled'

az group show -n "$resource_group" \
  --query '{id:id,name:name,location:location,provisioningState:properties.provisioningState}' -o json \
  > "$evidence_dir/resource-group.json"
test "$(jq -r '.location' "$evidence_dir/resource-group.json")" = "$location"

params=(resourceGroupName="$resource_group" principalId="$principal_object_id")

az deployment sub validate \
  --location "$location" \
  --name "${deployment_name}-validate" \
  --template-file "$template" \
  --parameters "${params[@]}" -o json \
  > "$evidence_dir/validation.json"

az deployment sub what-if \
  --location "$location" \
  --name "${deployment_name}-whatif" \
  --template-file "$template" \
  --parameters "${params[@]}" \
  --no-pretty-print --result-format FullResourcePayloads -o json \
  > "$evidence_dir/what-if.json"

jq -e '
  [.changes[]? | select(.changeType != "Ignore" and .changeType != "NoChange")] as $changes |
  ($changes | length) <= 2 and
  all($changes[];
    (.resourceId | ascii_downcase | contains("/providers/microsoft.authorization/roledefinitions/")) or
    (.resourceId | ascii_downcase | contains("/providers/microsoft.authorization/roleassignments/"))
  ) and
  all($changes[]; .changeType != "Delete")
' "$evidence_dir/what-if.json" >/dev/null

if [[ "$apply" != true ]]; then
  jq -n '{status:"validated_and_what_if_accepted",rbac_mutation_performed:false,claim_boundary:"plan accepted != RBAC mutation authorized"}' \
    > "$evidence_dir/summary.json"
  echo "Validation and What-If accepted. Re-run with --apply only under a separate explicit RBAC mutation authorization."
  exit 0
fi

az deployment sub create \
  --location "$location" \
  --name "$deployment_name" \
  --template-file "$template" \
  --parameters "${params[@]}" -o json \
  > "$evidence_dir/deployment.json"

jq -e '.properties.provisioningState == "Succeeded"' "$evidence_dir/deployment.json" >/dev/null
jq -n '{status:"rbac_deployed",rbac_mutation_performed:true,followup:"refresh OIDC credentials and verify effective permissions before any workload deployment authorization"}' \
  > "$evidence_dir/summary.json"
