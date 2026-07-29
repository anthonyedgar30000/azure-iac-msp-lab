#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_SHA:?GITHUB_SHA is required}"
: "${GITHUB_RUN_ID:?GITHUB_RUN_ID is required}"
: "${AZURE_CLIENT_ID:?AZURE_CLIENT_ID is required}"
: "${AZURE_SUBSCRIPTION_ID:?AZURE_SUBSCRIPTION_ID is required}"
: "${RUNNER_TEMP:?RUNNER_TEMP is required}"

ATTEMPT_ID="azure-ai-go-live-run6"
EXPECTED_SUBSCRIPTION_NAME="Azure for Students"
RESOURCE_GROUP="rg-ai-msp-dev-eastus"
ACCOUNT_NAME="oai-msp-anthony-dev-eastus"
LOCATION="eastus"
MODEL_NAME="gpt-4.1-mini"
MODEL_VERSION="2025-04-14"
DEPLOYMENT_NAME="gpt-41-mini-msp-dev"
DEPLOYMENT_SKU="GlobalStandard"
DEPLOYMENT_CAPACITY="1"
REQUEST_FILE=".project/deployment-requests/azure-ai-go-live-run6.json"
TEMPLATE_FILE="infra/azure-ai-existing-account-adopt.bicep"
EVIDENCE_DIR="${RUNNER_TEMP}/azure-ai-live-evidence"
DEPLOYMENT_RECORD="azure-ai-adopt-run6-${GITHUB_RUN_ID}"

mkdir -p "$EVIDENCE_DIR"

jq -e \
  --arg attempt "$ATTEMPT_ID" \
  --arg subscription "$EXPECTED_SUBSCRIPTION_NAME" \
  --arg rg "$RESOURCE_GROUP" \
  --arg account "$ACCOUNT_NAME" \
  --arg location "$LOCATION" \
  --arg model "$MODEL_NAME" \
  --arg version "$MODEL_VERSION" \
  --arg deployment "$DEPLOYMENT_NAME" \
  --arg sku "$DEPLOYMENT_SKU" '
  .attempt_id == $attempt and
  .status == "active_one_attempt" and
  .active == true and
  .attempt_limit == 1 and
  .attempts_observed == 0 and
  .scope.subscription_name == $subscription and
  .scope.resource_group_name == $rg and
  .scope.account_name == $account and
  .scope.location == $location and
  .scope.account_preexisting_required == true and
  .scope.resource_group_preexisting_required == true and
  .scope.duplicate_account_authorized == false and
  .scope.duplicate_resource_group_authorized == false and
  .scope.model_name == $model and
  .scope.model_version == $version and
  .scope.deployment_name == $deployment and
  .scope.deployment_sku == $sku and
  .scope.deployment_capacity == 1 and
  .scope.deployment_attempt_limit == 1 and
  .scope.model_request_count == 1 and
  .scope.max_output_tokens == 32 and
  .authority.automatic_retry_authorized == false and
  .authority.manual_rerun_authorized == false and
  .authority.second_deployment_attempt_authorized == false and
  .authority.new_account_creation_authorized == false and
  .authority.new_resource_group_creation_authorized == false
' "$REQUEST_FILE" >/dev/null

subscription_id="$(az account show --query id --output tsv)"
subscription_name="$(az account show --query name --output tsv)"
subscription_state="$(az account show --query state --output tsv)"
test "$subscription_id" = "$AZURE_SUBSCRIPTION_ID"
test "$subscription_name" = "$EXPECTED_SUBSCRIPTION_NAME"
test "$subscription_state" = "Enabled"

principal_id="$(az role assignment list --assignee "$AZURE_CLIENT_ID" --all --query '[0].principalId' --output tsv 2>/dev/null || true)"
if [[ -z "$principal_id" ]]; then
  principal_id="$(az ad sp show --id "$AZURE_CLIENT_ID" --query id --output tsv)"
fi
test -n "$principal_id"

provider_state="$(az provider show --namespace Microsoft.CognitiveServices --query registrationState --output tsv)"
test "$provider_state" = "Registered"

principal_hash="$(printf '%s' "$principal_id" | sha256sum | cut -c1-16)"

redact_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    sed -i \
      -e "s#${subscription_id}#<subscription>#g" \
      -e "s#${principal_id}#<principal>#g" \
      "$path"
  fi
}

write_terminal_summary() {
  local status="$1"
  local stage="$2"
  local deployment_started="$3"
  local model_request_performed="$4"
  local endpoint_live="$5"
  jq -n \
    --arg attempt_id "$ATTEMPT_ID" \
    --arg commit "$GITHUB_SHA" \
    --arg status "$status" \
    --arg stage "$stage" \
    --arg resource_group "$RESOURCE_GROUP" \
    --arg account "$ACCOUNT_NAME" \
    --arg location "$LOCATION" \
    --arg model "$MODEL_NAME" \
    --arg version "$MODEL_VERSION" \
    --arg deployment "$DEPLOYMENT_NAME" \
    --arg sku "$DEPLOYMENT_SKU" \
    --argjson deployment_started "$deployment_started" \
    --argjson model_request_performed "$model_request_performed" \
    --argjson endpoint_live "$endpoint_live" \
    '{
      schema_version:"project.azure-ai-go-live-result.v4",
      status:$status,
      failure_or_completion_stage:$stage,
      attempt_id:$attempt_id,
      exact_commit:$commit,
      resource_group:$resource_group,
      account:$account,
      location:$location,
      model:$model,
      model_version:$version,
      deployment:$deployment,
      deployment_sku:$sku,
      deployment_started:$deployment_started,
      model_request_performed:$model_request_performed,
      endpoint_live:$endpoint_live
    }' > "$EVIDENCE_DIR/go-live-summary.json"
}

jq -n \
  --arg schema_version "project.azure-ai-go-live-context.v4" \
  --arg attempt_id "$ATTEMPT_ID" \
  --arg commit "$GITHUB_SHA" \
  --arg subscription_name "$subscription_name" \
  --arg subscription_state "$subscription_state" \
  --arg provider_state "$provider_state" \
  --arg principal_fingerprint "sha256:$principal_hash" \
  '{
    schema_version:$schema_version,
    attempt_id:$attempt_id,
    exact_commit:$commit,
    subscription_name:$subscription_name,
    subscription_state:$subscription_state,
    provider_registration_state:$provider_state,
    principal_fingerprint:$principal_fingerprint,
    raw_subscription_id_persisted:false,
    raw_principal_id_persisted:false
  }' > "$EVIDENCE_DIR/context.json"

group_tmp="${RUNNER_TEMP}/manual-resource-group.json"
account_tmp="${RUNNER_TEMP}/manual-account.json"

set +e
az group show --name "$RESOURCE_GROUP" --output json > "$group_tmp" 2>"$EVIDENCE_DIR/resource-group-query.err"
group_rc=$?
az cognitiveservices account show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACCOUNT_NAME" \
  --output json > "$account_tmp" 2>"$EVIDENCE_DIR/account-query.err"
account_rc=$?
set -e
redact_file "$EVIDENCE_DIR/resource-group-query.err"
redact_file "$EVIDENCE_DIR/account-query.err"

if (( group_rc != 0 || account_rc != 0 )); then
  write_terminal_summary "manual_resource_missing" "pre_mutation_existing_resource_validation" false false false
  exit 1
fi

if ! jq -e --arg name "$RESOURCE_GROUP" --arg location "$LOCATION" '
  .name == $name and
  (.location | ascii_downcase) == $location and
  (.properties.provisioningState // "") == "Succeeded"
' "$group_tmp" >/dev/null; then
  write_terminal_summary "manual_resource_mismatch" "pre_mutation_resource_group_validation" false false false
  exit 1
fi

if ! jq -e --arg name "$ACCOUNT_NAME" --arg location "$LOCATION" '
  .name == $name and
  (.location | ascii_downcase) == $location and
  .kind == "OpenAI" and
  (.properties.provisioningState // "") == "Succeeded"
' "$account_tmp" >/dev/null; then
  write_terminal_summary "manual_resource_mismatch" "pre_mutation_account_validation" false false false
  exit 1
fi

jq '{
  resource_group:{name:.name,location:.location,provisioningState:.properties.provisioningState}
}' "$group_tmp" > "$EVIDENCE_DIR/manual-resource-group-baseline.json"

jq '{
  name,
  location,
  kind,
  sku:.sku.name,
  provisioningState:.properties.provisioningState,
  disableLocalAuth:.properties.disableLocalAuth,
  publicNetworkAccess:.properties.publicNetworkAccess,
  customSubDomainName:.properties.customSubDomainName,
  tags
}' "$account_tmp" > "$EVIDENCE_DIR/manual-account-baseline.json"

account_id="$(jq -r '.id' "$account_tmp")"
test -n "$account_id"
test "$account_id" != "null"

existing_deployment_tmp="${RUNNER_TEMP}/existing-model-deployment.json"
set +e
az cognitiveservices account deployment show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACCOUNT_NAME" \
  --deployment-name "$DEPLOYMENT_NAME" \
  --output json > "$existing_deployment_tmp" 2>"$EVIDENCE_DIR/existing-deployment-query.err"
existing_deployment_rc=$?
set -e
redact_file "$EVIDENCE_DIR/existing-deployment-query.err"

existing_exact_deployment=false
if (( existing_deployment_rc == 0 )); then
  jq '{name,provisioningState:.properties.provisioningState,model:.properties.model,sku}' \
    "$existing_deployment_tmp" > "$EVIDENCE_DIR/existing-deployment-baseline.json"
  if ! jq -e \
    --arg deployment "$DEPLOYMENT_NAME" \
    --arg model "$MODEL_NAME" \
    --arg version "$MODEL_VERSION" \
    --arg sku "$DEPLOYMENT_SKU" '
      .name == $deployment and
      (.properties.model.format // "") == "OpenAI" and
      (.properties.model.name // "") == $model and
      (.properties.model.version // "") == $version and
      (.sku.name // "") == $sku
    ' "$existing_deployment_tmp" >/dev/null; then
    write_terminal_summary "conflicting_existing_deployment" "pre_mutation_deployment_conflict_check" false false false
    exit 1
  fi
  existing_exact_deployment=true
fi

models_tmp="${RUNNER_TEMP}/models-eastus.json"
capacity_tmp="${RUNNER_TEMP}/capacity-eastus.json"

set +e
az rest \
  --method get \
  --url "https://management.azure.com/subscriptions/${subscription_id}/providers/Microsoft.CognitiveServices/locations/${LOCATION}/models?api-version=2024-10-01" \
  --output json > "$models_tmp" 2>"$EVIDENCE_DIR/model-listing.err"
models_rc=$?
set -e
redact_file "$EVIDENCE_DIR/model-listing.err"

if (( models_rc != 0 )); then
  write_terminal_summary "model_listing_failed" "pre_mutation_model_listing" false false false
  exit 1
fi

jq --arg name "$MODEL_NAME" --arg version "$MODEL_VERSION" '[
  .value[]?
  | select((.model.format // "") == "OpenAI" and (.model.name // "") == $name and (.model.version // "") == $version)
]' "$models_tmp" > "$EVIDENCE_DIR/model-listing.json"

if ! jq -e 'length > 0' "$EVIDENCE_DIR/model-listing.json" >/dev/null; then
  write_terminal_summary "model_not_listed" "pre_mutation_model_listing" false false false
  exit 1
fi

set +e
az rest \
  --method get \
  --url "https://management.azure.com/subscriptions/${subscription_id}/providers/Microsoft.CognitiveServices/locations/${LOCATION}/modelCapacities?api-version=2024-10-01&modelFormat=OpenAI&modelName=${MODEL_NAME}&modelVersion=${MODEL_VERSION}" \
  --output json > "$capacity_tmp" 2>"$EVIDENCE_DIR/model-capacity.err"
capacity_rc=$?
set -e
redact_file "$EVIDENCE_DIR/model-capacity.err"

if (( capacity_rc != 0 )); then
  write_terminal_summary "capacity_query_failed" "pre_mutation_capacity_query" false false false
  exit 1
fi

jq --arg sku "$DEPLOYMENT_SKU" '[
  .value[]?
  | select((.properties.skuName // .name // "") == $sku)
  | {
      skuName:(.properties.skuName // .name),
      availableCapacity:((.properties.availableCapacity // 0) | tonumber? // 0)
    }
]' "$capacity_tmp" > "$EVIDENCE_DIR/model-capacity.json"

available_capacity="$(jq -r '[.[].availableCapacity] | max // 0' "$EVIDENCE_DIR/model-capacity.json")"
if [[ "$existing_exact_deployment" != true ]] && (( available_capacity < DEPLOYMENT_CAPACITY )); then
  write_terminal_summary "capacity_unavailable" "pre_mutation_capacity_query" false false false
  exit 1
fi

what_if_json="$EVIDENCE_DIR/what-if.json"
what_if_err="$EVIDENCE_DIR/what-if.err"
set +e
az deployment group what-if \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DEPLOYMENT_RECORD" \
  --template-file "$TEMPLATE_FILE" \
  --parameters \
    accountName="$ACCOUNT_NAME" \
    deployModel=true \
    deploymentName="$DEPLOYMENT_NAME" \
    modelName="$MODEL_NAME" \
    modelVersion="$MODEL_VERSION" \
    deploymentSkuName="$DEPLOYMENT_SKU" \
    deploymentCapacity="$DEPLOYMENT_CAPACITY" \
    assignInferenceRole=true \
    inferencePrincipalId="$principal_id" \
    inferencePrincipalType=ServicePrincipal \
  --result-format FullResourcePayloads \
  --output json > "$what_if_json" 2>"$what_if_err"
what_if_rc=$?
set -e
redact_file "$what_if_json"
redact_file "$what_if_err"

if (( what_if_rc != 0 )); then
  write_terminal_summary "what_if_failed" "pre_mutation_what_if" false false false
  exit 1
fi

# Reconfirm the exact manual resources immediately before the one authorized deployment.
az group show --name "$RESOURCE_GROUP" --query "[name,location]" --output tsv | grep -Fx $'rg-ai-msp-dev-eastus\teastus' >/dev/null
az cognitiveservices account show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACCOUNT_NAME" \
  --query "[name,location,kind,properties.provisioningState]" \
  --output tsv | grep -Fx $'oai-msp-anthony-dev-eastus\teastus\tOpenAI\tSucceeded' >/dev/null

deployment_json="$EVIDENCE_DIR/deployment.json"
deployment_err="$EVIDENCE_DIR/deployment.err"
set +e
az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DEPLOYMENT_RECORD" \
  --template-file "$TEMPLATE_FILE" \
  --parameters \
    accountName="$ACCOUNT_NAME" \
    deployModel=true \
    deploymentName="$DEPLOYMENT_NAME" \
    modelName="$MODEL_NAME" \
    modelVersion="$MODEL_VERSION" \
    deploymentSkuName="$DEPLOYMENT_SKU" \
    deploymentCapacity="$DEPLOYMENT_CAPACITY" \
    assignInferenceRole=true \
    inferencePrincipalId="$principal_id" \
    inferencePrincipalType=ServicePrincipal \
  --output json > "$deployment_json" 2>"$deployment_err"
deploy_rc=$?
set -e
redact_file "$deployment_json"
redact_file "$deployment_err"

if (( deploy_rc != 0 )); then
  write_terminal_summary "deployment_failed" "single_deployment_attempt" true false false
  exit 1
fi

# Harden the already-existing account after the model and Entra role are declared.
set +e
az resource update \
  --ids "$account_id" \
  --api-version 2024-10-01 \
  --set properties.disableLocalAuth=true properties.publicNetworkAccess=Enabled \
  --output json > "$EVIDENCE_DIR/account-hardening.json" 2>"$EVIDENCE_DIR/account-hardening.err"
hardening_rc=$?
set -e
redact_file "$EVIDENCE_DIR/account-hardening.json"
redact_file "$EVIDENCE_DIR/account-hardening.err"

if (( hardening_rc != 0 )); then
  write_terminal_summary "account_hardening_failed" "post_deployment_account_hardening" true false false
  exit 1
fi

az cognitiveservices account show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACCOUNT_NAME" \
  --output json \
  | jq '{name,location,kind,sku:.sku.name,provisioningState:.properties.provisioningState,disableLocalAuth:.properties.disableLocalAuth,publicNetworkAccess:.properties.publicNetworkAccess}' \
  > "$EVIDENCE_DIR/account-verification.json"
jq -e '.name == "oai-msp-anthony-dev-eastus" and .location == "eastus" and .kind == "OpenAI" and .provisioningState == "Succeeded" and .disableLocalAuth == true and .publicNetworkAccess == "Enabled"' \
  "$EVIDENCE_DIR/account-verification.json" >/dev/null

az cognitiveservices account deployment show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACCOUNT_NAME" \
  --deployment-name "$DEPLOYMENT_NAME" \
  --output json \
  | jq '{name,provisioningState:.properties.provisioningState,model:.properties.model,sku}' \
  > "$EVIDENCE_DIR/model-verification.json"
jq -e \
  --arg deployment "$DEPLOYMENT_NAME" \
  --arg model "$MODEL_NAME" \
  --arg version "$MODEL_VERSION" \
  --arg sku "$DEPLOYMENT_SKU" '
    .name == $deployment and
    .provisioningState == "Succeeded" and
    .model.format == "OpenAI" and
    .model.name == $model and
    .model.version == $version and
    .sku.name == $sku
  ' "$EVIDENCE_DIR/model-verification.json" >/dev/null

az role assignment list \
  --assignee-object-id "$principal_id" \
  --scope "$account_id" \
  --query "[?roleDefinitionName=='Cognitive Services OpenAI User'].{role:roleDefinitionName,scope:scope,principalType:principalType}" \
  --output json \
  | sed "s#${subscription_id}#<subscription>#g" \
  > "$EVIDENCE_DIR/rbac-verification.json"
jq -e 'length > 0' "$EVIDENCE_DIR/rbac-verification.json" >/dev/null

# One propagation wait, then exactly one authorized data-plane request. No retry loop.
sleep 90

token="$(az account get-access-token --scope https://ai.azure.com/.default --query accessToken --output tsv 2>/dev/null || az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken --output tsv)"
base_url="https://${ACCOUNT_NAME}.openai.azure.com/openai/v1/"
request='{"model":"'"$DEPLOYMENT_NAME"'","input":"Reply with exactly: AZURE AI LIVE","max_output_tokens":32}'
http_code="$(curl --silent --show-error \
  --output "${RUNNER_TEMP}/response.json" \
  --write-out '%{http_code}' \
  --request POST \
  --url "${base_url}responses" \
  --header "Authorization: Bearer ${token}" \
  --header 'Content-Type: application/json' \
  --data "$request" || true)"
printf '%s\n' "$http_code" > "$EVIDENCE_DIR/model-call-http-status.txt"

if [[ "$http_code" != "200" ]]; then
  jq '{error}' "${RUNNER_TEMP}/response.json" > "$EVIDENCE_DIR/model-call-failure.json" 2>/dev/null || true
  write_terminal_summary "deployed_verification_failed" "single_model_request" true true false
  exit 1
fi

jq '
  def output_text:
    .output_text // ([.output[]?.content[]? | select(.type == "output_text") | .text] | join(""));
  {
    status:"verified",
    id,
    model,
    output_text:output_text,
    usage,
    prompt_classification:"bounded_non_sensitive_demo",
    max_output_tokens:32
  }
' "${RUNNER_TEMP}/response.json" > "$EVIDENCE_DIR/model-call-receipt.json"
jq -e '.output_text | contains("AZURE AI LIVE")' "$EVIDENCE_DIR/model-call-receipt.json" >/dev/null

jq -n \
  --arg attempt_id "$ATTEMPT_ID" \
  --arg commit "$GITHUB_SHA" \
  --arg resource_group "$RESOURCE_GROUP" \
  --arg account "$ACCOUNT_NAME" \
  --arg location "$LOCATION" \
  --arg model "$MODEL_NAME" \
  --arg version "$MODEL_VERSION" \
  --arg deployment "$DEPLOYMENT_NAME" \
  --arg sku "$DEPLOYMENT_SKU" \
  --arg deployment_record "$DEPLOYMENT_RECORD" '
  {
    schema_version:"project.azure-ai-go-live-result.v4",
    status:"live_verified",
    attempt_id:$attempt_id,
    exact_commit:$commit,
    resource_group:$resource_group,
    account:$account,
    location:$location,
    model:$model,
    model_version:$version,
    deployment:$deployment,
    deployment_sku:$sku,
    deployment_record:$deployment_record,
    portal_created_account_adopted:true,
    duplicate_resource_created:false,
    local_authentication_disabled:true,
    entra_inference_verified:true,
    bounded_model_request_verified:true,
    model_request_count:1,
    azure_mcp_connected:false,
    endpoint_live:true
  }' > "$EVIDENCE_DIR/go-live-summary.json"
