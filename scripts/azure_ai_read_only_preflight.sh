#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_VERSION="1.0.0"
readonly REQUIRED_COMMANDS=(az jq sha256sum)

for command_name in "${REQUIRED_COMMANDS[@]}"; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Required command is unavailable: $command_name" >&2
    exit 1
  }
done

: "${AZURE_AI_HOSTING_SUBSCRIPTION_ID:?AZURE_AI_HOSTING_SUBSCRIPTION_ID is required}"
: "${AZURE_AI_RESOURCE_GROUP:?AZURE_AI_RESOURCE_GROUP is required}"
: "${AZURE_AI_CANDIDATE_LOCATIONS:?AZURE_AI_CANDIDATE_LOCATIONS is required}"
: "${AZURE_AI_CANDIDATE_MODELS_JSON:?AZURE_AI_CANDIDATE_MODELS_JSON is required}"
: "${AZURE_AI_WORKDIR:?AZURE_AI_WORKDIR is required}"

readonly EVIDENCE_DIR="$AZURE_AI_WORKDIR/evidence"
mkdir -p "$EVIDENCE_DIR"

fail() {
  echo "Azure AI preflight failed closed: $*" >&2
  exit 1
}

write_observation_failure() {
  local output_path="$1"
  local observation="$2"
  local message="$3"
  jq -n \
    --arg observation "$observation" \
    --arg message "$message" \
    '{status:"observation_failed",observation:$observation,message:$message}' \
    > "$output_path"
}

redact_subscription() {
  local input_path="$1"
  local output_path="$2"
  sed "s#${AZURE_AI_HOSTING_SUBSCRIPTION_ID}#<subscription>#g" \
    "$input_path" > "$output_path"
}

jq -e 'type == "array" and length > 0 and all(.[]; (.name | type == "string" and length > 0) and (.version | type == "string" and length > 0))' \
  <<< "$AZURE_AI_CANDIDATE_MODELS_JSON" >/dev/null \
  || fail "AZURE_AI_CANDIDATE_MODELS_JSON must be a non-empty array of name/version objects"

IFS=',' read -r -a candidate_locations <<< "$AZURE_AI_CANDIDATE_LOCATIONS"
(( ${#candidate_locations[@]} > 0 )) || fail "At least one candidate location is required"
for location in "${candidate_locations[@]}"; do
  [[ "$location" =~ ^[a-z0-9]+$ ]] || fail "Invalid candidate location: $location"
done

account_json="$(az account show --output json)" 
subscription_id="$(jq -r '.id // empty' <<< "$account_json")"
subscription_name="$(jq -r '.name // empty' <<< "$account_json")"
subscription_state="$(jq -r '.state // empty' <<< "$account_json")"
tenant_id="$(jq -r '.tenantId // empty' <<< "$account_json")"
principal_type="$(jq -r '.user.type // "unknown"' <<< "$account_json")"
principal_name="$(jq -r '.user.name // empty' <<< "$account_json")"

[[ "$subscription_id" == "$AZURE_AI_HOSTING_SUBSCRIPTION_ID" ]] \
  || fail "Azure CLI resolved a different subscription"
[[ "$subscription_state" == "Enabled" ]] \
  || fail "Azure subscription is not Enabled"
[[ -n "$tenant_id" ]] || fail "Azure tenant identity was not resolved"
[[ -n "$principal_name" ]] || fail "Azure principal identity was not resolved"

tenant_fingerprint="$(printf '%s' "$tenant_id" | sha256sum | awk '{print "sha256:"$1}')"
principal_fingerprint="$(printf '%s' "$principal_name" | sha256sum | awk '{print "sha256:"$1}')"

jq -n \
  --arg script_version "$SCRIPT_VERSION" \
  --arg subscription_name "$subscription_name" \
  --arg subscription_state "$subscription_state" \
  --arg tenant_fingerprint "$tenant_fingerprint" \
  --arg principal_type "$principal_type" \
  --arg principal_fingerprint "$principal_fingerprint" \
  '{
    status:"observed",
    script_version:$script_version,
    subscription_name:$subscription_name,
    subscription_state:$subscription_state,
    tenant_fingerprint:$tenant_fingerprint,
    principal_type:$principal_type,
    principal_fingerprint:$principal_fingerprint,
    raw_subscription_id_persisted:false,
    raw_tenant_id_persisted:false,
    raw_principal_identifier_persisted:false
  }' > "$EVIDENCE_DIR/account-context.json"

location_catalog="$(az account list-locations --output json)"
printf '%s' "$location_catalog" \
  | jq --argjson requested "$(printf '%s\n' "${candidate_locations[@]}" | jq -R . | jq -s .)" '
      {
        status:"observed",
        requested_locations:$requested,
        matches:[.[] | select(.name as $name | $requested | index($name)) | {name,displayName,regionalDisplayName}]
      }
    ' > "$EVIDENCE_DIR/location-catalog.json"

for location in "${candidate_locations[@]}"; do
  jq -e --arg location "$location" '.matches | any(.name == $location)' \
    "$EVIDENCE_DIR/location-catalog.json" >/dev/null \
    || fail "Candidate location is not available to the subscription: $location"
done

provider_state="$(az provider show --namespace Microsoft.CognitiveServices --query registrationState --output tsv)"
jq -n --arg registration_state "$provider_state" \
  '{status:"observed",namespace:"Microsoft.CognitiveServices",registration_state:$registration_state}' \
  > "$EVIDENCE_DIR/provider-state.json"
[[ "$provider_state" == "Registered" ]] \
  || fail "Microsoft.CognitiveServices is not registered; registration is not authorized by this preflight"

set +e
resource_group_json="$(az group show --name "$AZURE_AI_RESOURCE_GROUP" --output json 2>"$AZURE_AI_WORKDIR/resource-group.err")"
resource_group_rc=$?
set -e
if (( resource_group_rc == 0 )); then
  jq '{status:"observed_present",name,location,managedBy,tags,provisioningState:.properties.provisioningState}' \
    <<< "$resource_group_json" > "$EVIDENCE_DIR/resource-group-state.json"
elif grep -qiE 'ResourceGroupNotFound|could not be found' "$AZURE_AI_WORKDIR/resource-group.err"; then
  jq -n --arg name "$AZURE_AI_RESOURCE_GROUP" \
    '{status:"observed_not_present",name:$name}' \
    > "$EVIDENCE_DIR/resource-group-state.json"
else
  write_observation_failure \
    "$EVIDENCE_DIR/resource-group-state.json" \
    "resource_group" \
    "Azure resource-group observation failed"
  fail "Resource-group observation failed ambiguously"
fi

existing_accounts="$(az cognitiveservices account list --output json)"
printf '%s' "$existing_accounts" | jq '
  {
    status:"observed",
    accounts:[
      .[]
      | select(.kind == "OpenAI" or .kind == "AIServices")
      | {
          name,
          kind,
          location,
          resourceGroup,
          sku:.sku.name,
          disableLocalAuth:.properties.disableLocalAuth,
          publicNetworkAccess:.properties.publicNetworkAccess,
          provisioningState:.properties.provisioningState
        }
    ]
  }
' > "$EVIDENCE_DIR/existing-ai-accounts.json"

material_observation_failure=0
candidate_model_matches=0

for location in "${candidate_locations[@]}"; do
  models_raw="$AZURE_AI_WORKDIR/models-${location}-raw.json"
  set +e
  az rest \
    --method get \
    --url "https://management.azure.com/subscriptions/${subscription_id}/providers/Microsoft.CognitiveServices/locations/${location}/models?api-version=2024-10-01" \
    --output json > "$models_raw" 2>"$AZURE_AI_WORKDIR/models-${location}.err"
  models_rc=$?
  set -e
  if (( models_rc != 0 )); then
    write_observation_failure \
      "$EVIDENCE_DIR/models-${location}.json" \
      "models_${location}" \
      "Model inventory observation failed"
    material_observation_failure=1
  else
    jq --argjson candidates "$AZURE_AI_CANDIDATE_MODELS_JSON" '
      {
        status:"observed",
        candidates:$candidates,
        matches:[
          .value[] as $item
          | $candidates[] as $candidate
          | select(($item.model.format // "") == "OpenAI")
          | select(($item.model.name // "") == $candidate.name)
          | select(($item.model.version // "") == $candidate.version)
          | {
              kind:$item.kind,
              skuName:$item.skuName,
              model:$item.model,
              properties:$item.properties
            }
        ]
      }
    ' "$models_raw" > "$EVIDENCE_DIR/models-${location}.json"
    match_count="$(jq '.matches | length' "$EVIDENCE_DIR/models-${location}.json")"
    candidate_model_matches=$((candidate_model_matches + match_count))
  fi

  set +e
  az cognitiveservices usage list --location "$location" --output json \
    > "$AZURE_AI_WORKDIR/usage-${location}-raw.json" \
    2>"$AZURE_AI_WORKDIR/usage-${location}.err"
  usage_rc=$?
  set -e
  if (( usage_rc != 0 )); then
    write_observation_failure \
      "$EVIDENCE_DIR/usage-${location}.json" \
      "usage_${location}" \
      "Quota usage observation failed; Cognitive Services Usages Reader or broader read permission may be missing"
    material_observation_failure=1
  else
    jq '{status:"observed",usage:[.[] | {name,currentValue,limit,unit}]}' \
      "$AZURE_AI_WORKDIR/usage-${location}-raw.json" \
      > "$EVIDENCE_DIR/usage-${location}.json"
  fi

  set +e
  az cognitiveservices account list-skus \
    --kind OpenAI \
    --location "$location" \
    --output json > "$AZURE_AI_WORKDIR/skus-${location}-raw.json" \
    2>"$AZURE_AI_WORKDIR/skus-${location}.err"
  skus_rc=$?
  set -e
  if (( skus_rc != 0 )); then
    write_observation_failure \
      "$EVIDENCE_DIR/skus-${location}.json" \
      "skus_${location}" \
      "OpenAI account SKU observation failed"
    material_observation_failure=1
  else
    jq '{status:"observed",skus:[.[] | {name,kind,locations,resourceType,restrictions}]}' \
      "$AZURE_AI_WORKDIR/skus-${location}-raw.json" \
      > "$EVIDENCE_DIR/skus-${location}.json"
  fi

  while IFS= read -r model; do
    model_name="$(jq -r '.name' <<< "$model")"
    model_version="$(jq -r '.version' <<< "$model")"
    safe_model_name="$(tr -c 'A-Za-z0-9._-' '_' <<< "$model_name")"
    capacity_raw="$AZURE_AI_WORKDIR/capacity-${location}-${safe_model_name}-raw.json"
    set +e
    az rest \
      --method get \
      --url "https://management.azure.com/subscriptions/${subscription_id}/providers/Microsoft.CognitiveServices/locations/${location}/modelCapacities?api-version=2024-10-01&modelFormat=OpenAI&modelName=${model_name}&modelVersion=${model_version}" \
      --output json > "$capacity_raw" \
      2>"$AZURE_AI_WORKDIR/capacity-${location}-${safe_model_name}.err"
    capacity_rc=$?
    set -e
    if (( capacity_rc != 0 )); then
      write_observation_failure \
        "$EVIDENCE_DIR/capacity-${location}-${safe_model_name}.json" \
        "capacity_${location}_${model_name}" \
        "Model capacity observation failed"
      material_observation_failure=1
    else
      jq --arg model_name "$model_name" --arg model_version "$model_version" '
        {
          status:"observed",
          model:{format:"OpenAI",name:$model_name,version:$model_version},
          capacities:[.value[] | {name,type,properties}]
        }
      ' "$capacity_raw" \
        | sed "s#${AZURE_AI_HOSTING_SUBSCRIPTION_ID}#<subscription>#g" \
        > "$EVIDENCE_DIR/capacity-${location}-${safe_model_name}.json"
    fi
  done < <(jq -c '.[]' <<< "$AZURE_AI_CANDIDATE_MODELS_JSON")
done

set +e
az role assignment list --assignee "$principal_name" --all --output json \
  > "$AZURE_AI_WORKDIR/principal-role-assignments-raw.json" \
  2>"$AZURE_AI_WORKDIR/principal-role-assignments.err"
roles_rc=$?
set -e
if (( roles_rc != 0 )); then
  write_observation_failure \
    "$EVIDENCE_DIR/principal-role-assignments.json" \
    "principal_role_assignments" \
    "Principal role-assignment observation failed"
  material_observation_failure=1
else
  jq '[.[] | {roleDefinitionName,scope,principalType}]' \
    "$AZURE_AI_WORKDIR/principal-role-assignments-raw.json" \
    > "$AZURE_AI_WORKDIR/principal-role-assignments-filtered.json"
  redact_subscription \
    "$AZURE_AI_WORKDIR/principal-role-assignments-filtered.json" \
    "$EVIDENCE_DIR/principal-role-assignments.json"
fi

status="observation_complete"
if (( material_observation_failure != 0 )); then
  status="incomplete_fail_closed"
elif (( candidate_model_matches == 0 )); then
  status="no_candidate_model_match"
fi

jq -n \
  --arg status "$status" \
  --arg script_version "$SCRIPT_VERSION" \
  --arg resource_group "$AZURE_AI_RESOURCE_GROUP" \
  --argjson candidate_locations "$(printf '%s\n' "${candidate_locations[@]}" | jq -R . | jq -s .)" \
  --argjson candidate_models "$AZURE_AI_CANDIDATE_MODELS_JSON" \
  --argjson candidate_model_matches "$candidate_model_matches" \
  --argjson material_observation_failure "$material_observation_failure" \
  '{
    status:$status,
    script_version:$script_version,
    resource_group:$resource_group,
    candidate_locations:$candidate_locations,
    candidate_models:$candidate_models,
    candidate_model_matches:$candidate_model_matches,
    material_observation_failure:($material_observation_failure == 1),
    azure_mutations_performed:false,
    provider_registration_performed:false,
    resource_group_created:false,
    role_assignment_created:false,
    model_deployment_created:false,
    model_request_performed:false
  }' > "$EVIDENCE_DIR/preflight-summary.json"

[[ "$status" == "observation_complete" ]] \
  || fail "Preflight did not produce a complete deployable observation boundary: $status"
