#!/usr/bin/env bash
set -euo pipefail

: "${ARTIFACT_DIR:?ARTIFACT_DIR is required}"
: "${LAB_ENVIRONMENT:?LAB_ENVIRONMENT is required}"
: "${LOCATION:?LOCATION is required}"
: "${VM_SIZE:?VM_SIZE is required}"
: "${AZURE_SUBSCRIPTION_ID:?AZURE_SUBSCRIPTION_ID is required}"
: "${AZURE_TENANT_ID:?AZURE_TENANT_ID is required}"

mkdir -p "$ARTIFACT_DIR"
diagnostics_ndjson="$ARTIFACT_DIR/azure-inspection-diagnostics.ndjson"
: > "$diagnostics_ndjson"

target_resource_group="rg-st-demo-api-${LAB_ENVIRONMENT}-${LOCATION}"

capture_command() {
  local name="$1"
  local stdout_file="$2"
  local stderr_file="$3"
  shift 3

  set +e
  "$@" > "$stdout_file" 2> "$stderr_file"
  local exit_status=$?
  set -e

  jq -n \
    --arg name "$name" \
    --arg stdout_file "$(basename "$stdout_file")" \
    --arg stderr_file "$(basename "$stderr_file")" \
    --argjson exit_status "$exit_status" \
    '{name:$name,exit_status:$exit_status,stdout_file:$stdout_file,stderr_file:$stderr_file,succeeded:($exit_status==0)}' \
    >> "$diagnostics_ndjson"
}

jq -e \
  --arg subscription "$AZURE_SUBSCRIPTION_ID" \
  --arg tenant "$AZURE_TENANT_ID" \
  '.subscriptionId==$subscription and .tenantId==$tenant and .state=="Enabled"' \
  "$ARTIFACT_DIR/azure-context.json" > /dev/null

capture_command provider_compute \
  "$ARTIFACT_DIR/provider-compute.json" \
  "$ARTIFACT_DIR/provider-compute.error.txt" \
  az provider show --namespace Microsoft.Compute --query '{namespace:namespace,registrationState:registrationState}' --output json

capture_command provider_network \
  "$ARTIFACT_DIR/provider-network.json" \
  "$ARTIFACT_DIR/provider-network.error.txt" \
  az provider show --namespace Microsoft.Network --query '{namespace:namespace,registrationState:registrationState}' --output json

capture_command policy_assignments \
  "$ARTIFACT_DIR/target-policy-assignments.json" \
  "$ARTIFACT_DIR/target-policy-assignments.error.txt" \
  az policy assignment list --disable-scope-strict-match true --output json

capture_command compute_usage \
  "$ARTIFACT_DIR/compute-usage.json" \
  "$ARTIFACT_DIR/compute-usage.error.txt" \
  az vm list-usage --location "$LOCATION" --output json

capture_command network_usage \
  "$ARTIFACT_DIR/network-usage.json" \
  "$ARTIFACT_DIR/network-usage.error.txt" \
  az network list-usages --location "$LOCATION" --output json

capture_command vm_size_availability \
  "$ARTIFACT_DIR/vm-size-availability.json" \
  "$ARTIFACT_DIR/vm-size-availability.error.txt" \
  az vm list-skus --location "$LOCATION" --size "$VM_SIZE" --all --output json

jq -s \
  '{schema_version:"servicetracer.azure-inspection-diagnostics.v1",commands:.,all_succeeded:all(.[];.succeeded)}' \
  "$diagnostics_ndjson" > "$ARTIFACT_DIR/azure-inspection-diagnostics.json"

if ! jq -e '.all_succeeded==true' "$ARTIFACT_DIR/azure-inspection-diagnostics.json" > /dev/null; then
  jq -c '.commands[] | select(.succeeded==false)' "$ARTIFACT_DIR/azure-inspection-diagnostics.json" >&2
  exit 1
fi

group_stdout="$ARTIFACT_DIR/existing-target-resource-group.raw.json"
group_stderr="$ARTIFACT_DIR/existing-target-resource-group.error.txt"
set +e
az group show --name "$target_resource_group" --output json > "$group_stdout" 2> "$group_stderr"
group_show_exit_status=$?
set -e

if (( group_show_exit_status == 0 )); then
  mv "$group_stdout" "$ARTIFACT_DIR/existing-target-resource-group.json"
  resources_stdout="$ARTIFACT_DIR/existing-target-resources.raw.json"
  resources_stderr="$ARTIFACT_DIR/existing-target-resources.error.txt"
  set +e
  az resource list --resource-group "$target_resource_group" --output json > "$resources_stdout" 2> "$resources_stderr"
  resource_list_exit_status=$?
  set -e
  if (( resource_list_exit_status == 0 )); then
    mv "$resources_stdout" "$ARTIFACT_DIR/existing-target-resources.json"
    jq -n --arg resource_group "$target_resource_group" --argjson group_show_exit_status "$group_show_exit_status" --argjson resource_list_exit_status "$resource_list_exit_status" \
      '{status:"observed_existing",resource_group:$resource_group,group_show_exit_status:$group_show_exit_status,resource_list_exit_status:$resource_list_exit_status,error_code:null,evidence_authoritative:true}' \
      > "$ARTIFACT_DIR/target-resource-group-state.json"
  else
    rm -f "$resources_stdout"
    jq -n --arg resource_group "$target_resource_group" --arg stage resource_list --argjson group_show_exit_status "$group_show_exit_status" --argjson resource_list_exit_status "$resource_list_exit_status" \
      '{status:"observation_failed",resource_group:$resource_group,stage:$stage,group_show_exit_status:$group_show_exit_status,resource_list_exit_status:$resource_list_exit_status,error_code:null,evidence_authoritative:false}' \
      > "$ARTIFACT_DIR/target-resource-group-state.json"
    jq -n '{status:"not_observed",resources:null,evidence_authoritative:false}' > "$ARTIFACT_DIR/existing-target-resources.json"
  fi
elif grep -Eq '(^|[^[:alnum:]_])ResourceGroupNotFound([^[:alnum:]_]|$)' "$group_stderr"; then
  rm -f "$group_stdout"
  jq -n --arg resource_group "$target_resource_group" --argjson group_show_exit_status "$group_show_exit_status" --rawfile error "$group_stderr" \
    '{status:"not_present",resource_group:$resource_group,group_show_exit_status:$group_show_exit_status,error_code:"ResourceGroupNotFound",error:$error,evidence_authoritative:true}' \
    > "$ARTIFACT_DIR/existing-target-resource-group.json"
  jq -n --arg resource_group "$target_resource_group" --argjson group_show_exit_status "$group_show_exit_status" \
    '{status:"not_present",resource_group:$resource_group,group_show_exit_status:$group_show_exit_status,resource_list_exit_status:null,error_code:"ResourceGroupNotFound",evidence_authoritative:true}' \
    > "$ARTIFACT_DIR/target-resource-group-state.json"
  printf '[]\n' > "$ARTIFACT_DIR/existing-target-resources.json"
else
  rm -f "$group_stdout"
  jq -n --arg resource_group "$target_resource_group" --argjson group_show_exit_status "$group_show_exit_status" --rawfile error "$group_stderr" \
    '{status:"observation_failed",resource_group:$resource_group,group_show_exit_status:$group_show_exit_status,error_code:null,error:$error,evidence_authoritative:false}' \
    > "$ARTIFACT_DIR/existing-target-resource-group.json"
  jq -n --arg resource_group "$target_resource_group" --arg stage group_show --argjson group_show_exit_status "$group_show_exit_status" \
    '{status:"observation_failed",resource_group:$resource_group,stage:$stage,group_show_exit_status:$group_show_exit_status,resource_list_exit_status:null,error_code:null,evidence_authoritative:false}' \
    > "$ARTIFACT_DIR/target-resource-group-state.json"
  jq -n '{status:"not_observed",resources:null,evidence_authoritative:false}' > "$ARTIFACT_DIR/existing-target-resources.json"
fi

jq -n --arg vm_size "$VM_SIZE" --slurpfile sku "$ARTIFACT_DIR/vm-size-availability.json" \
  '{vm_size:$vm_size,matching_records:([$sku[0][] | select(.name==$vm_size)] | length),unrestricted_records:([$sku[0][] | select(.name==$vm_size and ((.restrictions // []) | length)==0)] | length),restrictions:[$sku[0][] | select(.name==$vm_size) | (.restrictions // [])[]?]}' \
  > "$ARTIFACT_DIR/vm-size-assessment.json"

required_cores="$(jq -r --arg vm_size "$VM_SIZE" '[.[] | select(.name==$vm_size) | .capabilities[]? | select(.name=="vCPUs") | .value] | first // 0' "$ARTIFACT_DIR/vm-size-availability.json")"
[[ "$required_cores" =~ ^[0-9]+$ ]]
jq -n --argjson required_cores "$required_cores" --slurpfile usage "$ARTIFACT_DIR/compute-usage.json" \
  '{required_cores:$required_cores,total_regional_cores:([$usage[0][] | select(.name.value=="cores")][0] // null)} | . + {sufficient:(.total_regional_cores!=null and ((.total_regional_cores.currentValue|tonumber) + .required_cores <= (.total_regional_cores.limit|tonumber)))}' \
  > "$ARTIFACT_DIR/compute-quota-assessment.json"

python workloads/servicetracer-demo-api/scripts/assess_target_readiness.py \
  --vm-size "$VM_SIZE" \
  --provider-compute "$ARTIFACT_DIR/provider-compute.json" \
  --provider-network "$ARTIFACT_DIR/provider-network.json" \
  --vm-size-availability "$ARTIFACT_DIR/vm-size-availability.json" \
  --compute-usage "$ARTIFACT_DIR/compute-usage.json" \
  --network-usage "$ARTIFACT_DIR/network-usage.json" \
  --target-resource-group-state "$ARTIFACT_DIR/target-resource-group-state.json" \
  --existing-target-resources "$ARTIFACT_DIR/existing-target-resources.json" \
  --output "$ARTIFACT_DIR/target-readiness-assessment.json"

if ! jq -e '.status=="ready_for_arm_what_if"' "$ARTIFACT_DIR/target-readiness-assessment.json" > /dev/null; then
  jq -c '.blocking_reasons' "$ARTIFACT_DIR/target-readiness-assessment.json" >&2
  exit 1
fi
