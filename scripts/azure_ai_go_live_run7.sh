#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_SHA:?GITHUB_SHA is required}"
: "${GITHUB_RUN_ID:?GITHUB_RUN_ID is required}"
: "${AZURE_CLIENT_ID:?AZURE_CLIENT_ID is required}"
: "${AZURE_SUBSCRIPTION_ID:?AZURE_SUBSCRIPTION_ID is required}"
: "${RUNNER_TEMP:?RUNNER_TEMP is required}"

ATTEMPT_ID="azure-ai-go-live-run7"
EXPECTED_SUBSCRIPTION_NAME="Azure for Students"
RESOURCE_GROUP="rg-ai-msp-dev-eastus"
ACCOUNT_NAME="oai-msp-anthony-dev-eastus"
LOCATION="eastus"
ROLE_NAME="Cognitive Services OpenAI User"
ROLE_DEFINITION_GUID="5e0bd9bd-7b93-4f28-af87-19fc36ad61bd"
MODEL_NAME="gpt-4.1-mini"
MODEL_VERSION="2025-04-14"
DEPLOYMENT_NAME="gpt-41-mini-msp-dev"
DEPLOYMENT_SKU="GlobalStandard"
DEPLOYMENT_CAPACITY="1"
MAX_OUTPUT_TOKENS="32"
REQUEST_FILE=".project/deployment-requests/azure-ai-go-live-run7.json"
TEMPLATE_FILE="infra/azure-ai-existing-account-model-only.bicep"
EVIDENCE_DIR="${RUNNER_TEMP}/azure-ai-live-evidence"
DEPLOYMENT_RECORD="azure-ai-run7-${GITHUB_RUN_ID}"

mkdir -p "$EVIDENCE_DIR"

CURRENT_STAGE="repository_authorization"
DEPLOYMENT_STARTED=false
MODEL_REQUEST_PERFORMED=false
ENDPOINT_LIVE=false
ROLE_VERIFIED=false
AVAILABLE_CAPACITY=0
MODEL_LIFECYCLE="not_observed"

write_terminal_summary() {
  local status="$1"
  local stage="$2"
  jq -n \
    --arg attempt_id "$ATTEMPT_ID" \
    --arg commit "$GITHUB_SHA" \
    --arg status "$status" \
    --arg stage "$stage" \
    --arg resource_group "$RESOURCE_GROUP" \
    --arg account "$ACCOUNT_NAME" \
    --arg location "$LOCATION" \
    --arg role "$ROLE_NAME" \
    --arg model "$MODEL_NAME" \
    --arg version "$MODEL_VERSION" \
    --arg deployment "$DEPLOYMENT_NAME" \
    --arg sku "$DEPLOYMENT_SKU" \
    --arg lifecycle "$MODEL_LIFECYCLE" \
    --arg available "$AVAILABLE_CAPACITY" \
    --argjson role_verified "$ROLE_VERIFIED" \
    --argjson deployment_started "$DEPLOYMENT_STARTED" \
    --argjson model_request_performed "$MODEL_REQUEST_PERFORMED" \
    --argjson endpoint_live "$ENDPOINT_LIVE" \
    '{
      schema_version:"project.azure-ai-go-live-result.v5",
      status:$status,
      failure_or_completion_stage:$stage,
      attempt_id:$attempt_id,
      exact_commit:$commit,
      resource_group:$resource_group,
      account:$account,
      location:$location,
      required_role:$role,
      direct_account_role_verified:$role_verified,
      model:$model,
      model_version:$version,
      model_lifecycle:$lifecycle,
      deployment:$deployment,
      deployment_sku:$sku,
      reported_available_capacity:($available|tonumber? // 0),
      deployment_started:$deployment_started,
      model_request_performed:$model_request_performed,
      endpoint_live:$endpoint_live,
      separate_verified_gpt5_runtime_modified:false,
      azure_mcp_connected:false
    }' > "$EVIDENCE_DIR/go-live-summary.json"
}

fail_closed() {
  local status="$1"
  local stage="$2"
  write_terminal_summary "$status" "$stage"
  exit 1
}

on_exit() {
  local rc=$?
  if (( rc != 0 )) && [[ ! -f "$EVIDENCE_DIR/go-live-summary.json" ]]; then
    write_terminal_summary "unexpected_failure" "$CURRENT_STAGE" || true
  fi
}
trap on_exit EXIT

jq -e \
  --arg attempt "$ATTEMPT_ID" \
  --arg instruction "Proceed with Azure AI run 7 using the existing account and existing account-scoped inference role." \
  --arg subscription "$EXPECTED_SUBSCRIPTION_NAME" \
  --arg rg "$RESOURCE_GROUP" \
  --arg account "$ACCOUNT_NAME" \
  --arg location "$LOCATION" \
  --arg role "$ROLE_NAME" \
  --arg role_guid "$ROLE_DEFINITION_GUID" \
  --arg model "$MODEL_NAME" \
  --arg version "$MODEL_VERSION" \
  --arg deployment "$DEPLOYMENT_NAME" \
  --arg sku "$DEPLOYMENT_SKU" '
  .attempt_id == $attempt and
  .source_instruction == $instruction and
  .status == "active_one_attempt" and
  .active == true and
  .attempt_limit == 1 and
  .attempts_observed == 0 and
  .scope.subscription_name == $subscription and
  .scope.resource_group_name == $rg and
  .scope.account_name == $account and
  .scope.location == $location and
  .scope.inference_role_name == $role and
  .scope.inference_role_definition_id == $role_guid and
  .scope.direct_account_scoped_role_preexisting_required == true and
  .scope.role_assignment_creation_authorized == false and
  .scope.model_name == $model and
  .scope.model_version == $version and
  .scope.deployment_name == $deployment and
  .scope.deployment_sku == $sku and
  .scope.deployment_capacity == 1 and
  .scope.deployment_attempt_limit == 1 and
  .scope.account_hardening_update_limit == 1 and
  .scope.model_request_count == 1 and
  .scope.max_output_tokens == 32 and
  .authority.one_model_deployment_authorized == true and
  .authority.one_account_hardening_update_authorized == true and
  .authority.one_model_request_authorized == true and
  .authority.role_assignment_creation_authorized == false and
  .authority.automatic_retry_authorized == false and
  .authority.manual_rerun_authorized == false and
  .authority.second_deployment_attempt_authorized == false and
  .authority.regional_fallback_authorized == false and
  .authority.model_fallback_authorized == false
' "$REQUEST_FILE" >/dev/null

CURRENT_STAGE="azure_context"
subscription_id="$(az account show --query id --output tsv)"
subscription_name="$(az account show --query name --output tsv)"
subscription_state="$(az account show --query state --output tsv)"
test "$subscription_id" = "$AZURE_SUBSCRIPTION_ID"
test "$subscription_name" = "$EXPECTED_SUBSCRIPTION_NAME"
test "$subscription_state" = "Enabled"

principal_id="$(az ad sp show --id "$AZURE_CLIENT_ID" --query id --output tsv 2>/dev/null || true)"
if [[ -z "$principal_id" ]]; then
  principal_id="$(az role assignment list --assignee "$AZURE_CLIENT_ID" --all --query '[0].principalId' --output tsv 2>/dev/null || true)"
fi
test -n "$principal_id"

provider_state="$(az provider show --namespace Microsoft.CognitiveServices --query registrationState --output tsv)"
test "$provider_state" = "Registered"

principal_hash="$(printf '%s' "$principal_id" | sha256sum | cut -c1-16)"
subscription_hash="$(printf '%s' "$subscription_id" | sha256sum | cut -c1-16)"

redact_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    sed -i \
      -e "s#${subscription_id}#<subscription>#g" \
      -e "s#${principal_id}#<principal>#g" \
      "$path"
  fi
}

jq -n \
  --arg schema_version "project.azure-ai-go-live-context.v5" \
  --arg attempt_id "$ATTEMPT_ID" \
  --arg commit "$GITHUB_SHA" \
  --arg subscription_name "$subscription_name" \
  --arg subscription_state "$subscription_state" \
  --arg subscription_fingerprint "sha256:$subscription_hash" \
  --arg provider_state "$provider_state" \
  --arg principal_fingerprint "sha256:$principal_hash" \
  '{
    schema_version:$schema_version,
    attempt_id:$attempt_id,
    exact_commit:$commit,
    subscription_name:$subscription_name,
    subscription_state:$subscription_state,
    subscription_fingerprint:$subscription_fingerprint,
    provider_registration_state:$provider_state,
    principal_fingerprint:$principal_fingerprint,
    raw_subscription_id_persisted:false,
    raw_principal_id_persisted:false
  }' > "$EVIDENCE_DIR/context.json"

CURRENT_STAGE="existing_resource_validation"
group_tmp="${RUNNER_TEMP}/run7-resource-group.json"
account_tmp="${RUNNER_TEMP}/run7-account.json"
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
  fail_closed "existing_resource_missing" "$CURRENT_STAGE"
fi

jq -e --arg name "$RESOURCE_GROUP" --arg location "$LOCATION" '
  .name == $name and
  (.location | ascii_downcase) == $location and
  (.properties.provisioningState // "") == "Succeeded"
' "$group_tmp" >/dev/null || fail_closed "resource_group_mismatch" "$CURRENT_STAGE"

jq -e --arg name "$ACCOUNT_NAME" --arg location "$LOCATION" '
  .name == $name and
  (.location | ascii_downcase) == $location and
  .kind == "OpenAI" and
  .sku.name == "S0" and
  (.properties.provisioningState // "") == "Succeeded" and
  (.properties.publicNetworkAccess // "Enabled") == "Enabled"
' "$account_tmp" >/dev/null || fail_closed "account_mismatch" "$CURRENT_STAGE"

jq '{name,location,provisioningState:.properties.provisioningState,tags}' \
  "$group_tmp" > "$EVIDENCE_DIR/resource-group-baseline.json"
jq '{name,location,kind,sku:.sku.name,provisioningState:.properties.provisioningState,disableLocalAuth:.properties.disableLocalAuth,publicNetworkAccess:.properties.publicNetworkAccess,customSubDomainName:.properties.customSubDomainName,tags}' \
  "$account_tmp" > "$EVIDENCE_DIR/account-baseline.json"

account_id="$(jq -r '.id' "$account_tmp")"
test -n "$account_id"
test "$account_id" != "null"

CURRENT_STAGE="existing_direct_role_validation"
rbac_tmp="${RUNNER_TEMP}/run7-rbac.json"
set +e
az role assignment list \
  --assignee-object-id "$principal_id" \
  --scope "$account_id" \
  --all \
  --output json > "$rbac_tmp" 2>"$EVIDENCE_DIR/rbac-query.err"
rbac_rc=$?
set -e
redact_file "$EVIDENCE_DIR/rbac-query.err"
if (( rbac_rc != 0 )); then
  fail_closed "role_assignment_query_failed" "$CURRENT_STAGE"
fi

jq \
  --arg role "$ROLE_NAME" \
  --arg role_guid "$ROLE_DEFINITION_GUID" \
  --arg scope "$account_id" '[
    .[]?
    | select(
        (.roleDefinitionName // "") == $role and
        ((.roleDefinitionId // "") | endswith("/" + $role_guid)) and
        ((.scope // "") | ascii_downcase) == ($scope | ascii_downcase)
      )
    | {
        roleDefinitionName,
        roleDefinitionGuid:((.roleDefinitionId // "") | split("/") | last),
        principalType,
        scope:"<target-account>",
        directAccountScope:true
      }
  ]' "$rbac_tmp" > "$EVIDENCE_DIR/rbac-baseline.json"

if ! jq -e 'length > 0' "$EVIDENCE_DIR/rbac-baseline.json" >/dev/null; then
  fail_closed "required_direct_role_missing" "$CURRENT_STAGE"
fi
ROLE_VERIFIED=true

CURRENT_STAGE="deployment_inventory"
deployments_tmp="${RUNNER_TEMP}/run7-deployments.json"
set +e
az cognitiveservices account deployment list \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACCOUNT_NAME" \
  --output json > "$deployments_tmp" 2>"$EVIDENCE_DIR/deployment-inventory.err"
deployments_rc=$?
set -e
redact_file "$EVIDENCE_DIR/deployment-inventory.err"
if (( deployments_rc != 0 )); then
  fail_closed "deployment_inventory_failed" "$CURRENT_STAGE"
fi

jq '[.[]? | {name,provisioningState:.properties.provisioningState,model:.properties.model,sku}]' \
  "$deployments_tmp" > "$EVIDENCE_DIR/deployment-inventory.json"

existing_exact_deployment=false
if jq -e --arg deployment "$DEPLOYMENT_NAME" '.[]? | select(.name == $deployment)' "$deployments_tmp" >/dev/null; then
  if ! jq -e \
    --arg deployment "$DEPLOYMENT_NAME" \
    --arg model "$MODEL_NAME" \
    --arg version "$MODEL_VERSION" \
    --arg sku "$DEPLOYMENT_SKU" '
      .[]?
      | select(.name == $deployment)
      | select(
          (.properties.model.format // "") == "OpenAI" and
          (.properties.model.name // "") == $model and
          (.properties.model.version // "") == $version and
          (.sku.name // "") == $sku
        )
    ' "$deployments_tmp" >/dev/null; then
    fail_closed "conflicting_existing_deployment" "$CURRENT_STAGE"
  fi
  existing_exact_deployment=true
fi

CURRENT_STAGE="model_listing"
models_tmp="${RUNNER_TEMP}/run7-models.json"
set +e
az rest \
  --method get \
  --url "https://management.azure.com/subscriptions/${subscription_id}/providers/Microsoft.CognitiveServices/locations/${LOCATION}/models?api-version=2024-10-01" \
  --output json > "$models_tmp" 2>"$EVIDENCE_DIR/model-listing.err"
models_rc=$?
set -e
redact_file "$EVIDENCE_DIR/model-listing.err"
if (( models_rc != 0 )); then
  fail_closed "model_listing_failed" "$CURRENT_STAGE"
fi

jq \
  --arg name "$MODEL_NAME" \
  --arg version "$MODEL_VERSION" \
  --arg sku "$DEPLOYMENT_SKU" '[
    .value[]?
    | select(
        (.model.format // "") == "OpenAI" and
        (.model.name // "") == $name and
        (.model.version // "") == $version
      )
    | {
        location,
        model:{
          format:.model.format,
          name:.model.name,
          version:.model.version,
          lifecycleStatus:.model.lifecycleStatus,
          deprecation:.model.deprecation,
          responsesCapable:((.model.capabilities.responses // "false") == "true")
        },
        selectedSku:(
          [.model.skus[]? | select(.name == $sku) | {name,deprecationDate,capacity,rateLimits}]
          | first
        )
      }
  ]' "$models_tmp" > "$EVIDENCE_DIR/model-listing.json"

if ! jq -e 'length == 1 and .[0].selectedSku.name == "GlobalStandard" and .[0].model.responsesCapable == true' \
  "$EVIDENCE_DIR/model-listing.json" >/dev/null; then
  fail_closed "model_or_sku_not_listed" "$CURRENT_STAGE"
fi
MODEL_LIFECYCLE="$(jq -r '.[0].model.lifecycleStatus // "unknown"' "$EVIDENCE_DIR/model-listing.json")"
case "$MODEL_LIFECYCLE" in
  GenerallyAvailable|Preview|Deprecating) ;;
  *) fail_closed "model_lifecycle_not_deployable" "$CURRENT_STAGE" ;;
esac

CURRENT_STAGE="capacity_query"
capacity_tmp="${RUNNER_TEMP}/run7-capacity.json"
set +e
az rest \
  --method get \
  --url "https://management.azure.com/subscriptions/${subscription_id}/providers/Microsoft.CognitiveServices/locations/${LOCATION}/modelCapacities?api-version=2024-10-01&modelFormat=OpenAI&modelName=${MODEL_NAME}&modelVersion=${MODEL_VERSION}" \
  --output json > "$capacity_tmp" 2>"$EVIDENCE_DIR/model-capacity.err"
capacity_rc=$?
set -e
redact_file "$EVIDENCE_DIR/model-capacity.err"
if (( capacity_rc != 0 )); then
  fail_closed "capacity_query_failed" "$CURRENT_STAGE"
fi

jq --arg sku "$DEPLOYMENT_SKU" '[
  .value[]?
  | select((.properties.skuName // .name // "") == $sku)
  | {
      skuName:(.properties.skuName // .name),
      availableCapacity:((.properties.availableCapacity // 0) | tonumber? // 0)
    }
]' "$capacity_tmp" > "$EVIDENCE_DIR/model-capacity.json"
AVAILABLE_CAPACITY="$(jq -r '[.[].availableCapacity] | max // 0' "$EVIDENCE_DIR/model-capacity.json")"
if [[ "$existing_exact_deployment" != true ]] && (( AVAILABLE_CAPACITY < DEPLOYMENT_CAPACITY )); then
  fail_closed "capacity_unavailable" "$CURRENT_STAGE"
fi

CURRENT_STAGE="model_only_what_if"
what_if_json="$EVIDENCE_DIR/what-if.json"
what_if_err="$EVIDENCE_DIR/what-if.err"
set +e
az deployment group what-if \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DEPLOYMENT_RECORD" \
  --template-file "$TEMPLATE_FILE" \
  --parameters \
    accountName="$ACCOUNT_NAME" \
    deploymentName="$DEPLOYMENT_NAME" \
    modelName="$MODEL_NAME" \
    modelVersion="$MODEL_VERSION" \
    deploymentSkuName="$DEPLOYMENT_SKU" \
    deploymentCapacity="$DEPLOYMENT_CAPACITY" \
  --result-format FullResourcePayloads \
  --output json > "$what_if_json" 2>"$what_if_err"
what_if_rc=$?
set -e
redact_file "$what_if_json"
redact_file "$what_if_err"
if (( what_if_rc != 0 )); then
  fail_closed "what_if_failed" "$CURRENT_STAGE"
fi

CURRENT_STAGE="pre_deployment_revalidation"
az group show --name "$RESOURCE_GROUP" --query '[name,location,properties.provisioningState]' --output tsv \
  | grep -Fx $'rg-ai-msp-dev-eastus\teastus\tSucceeded' >/dev/null
az cognitiveservices account show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACCOUNT_NAME" \
  --query '[name,location,kind,sku.name,properties.provisioningState]' \
  --output tsv \
  | grep -Fx $'oai-msp-anthony-dev-eastus\teastus\tOpenAI\tS0\tSucceeded' >/dev/null

predeploy_role_count="$(az role assignment list \
  --assignee-object-id "$principal_id" \
  --scope "$account_id" \
  --all \
  --query "[?roleDefinitionName=='${ROLE_NAME}' && scope=='${account_id}'] | length(@)" \
  --output tsv)"
if (( predeploy_role_count < 1 )); then
  fail_closed "required_direct_role_disappeared" "$CURRENT_STAGE"
fi

CURRENT_STAGE="single_model_deployment"
DEPLOYMENT_STARTED=true
deployment_json="$EVIDENCE_DIR/deployment.json"
deployment_err="$EVIDENCE_DIR/deployment.err"
set +e
az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DEPLOYMENT_RECORD" \
  --template-file "$TEMPLATE_FILE" \
  --parameters \
    accountName="$ACCOUNT_NAME" \
    deploymentName="$DEPLOYMENT_NAME" \
    modelName="$MODEL_NAME" \
    modelVersion="$MODEL_VERSION" \
    deploymentSkuName="$DEPLOYMENT_SKU" \
    deploymentCapacity="$DEPLOYMENT_CAPACITY" \
  --output json > "$deployment_json" 2>"$deployment_err"
deploy_rc=$?
set -e
redact_file "$deployment_json"
redact_file "$deployment_err"
if (( deploy_rc != 0 )); then
  fail_closed "deployment_failed" "$CURRENT_STAGE"
fi

CURRENT_STAGE="single_account_hardening_update"
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
  fail_closed "account_hardening_failed" "$CURRENT_STAGE"
fi

CURRENT_STAGE="post_deployment_verification"
az cognitiveservices account show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACCOUNT_NAME" \
  --output json \
  | jq '{name,location,kind,sku:.sku.name,provisioningState:.properties.provisioningState,disableLocalAuth:.properties.disableLocalAuth,publicNetworkAccess:.properties.publicNetworkAccess,customSubDomainName:.properties.customSubDomainName}' \
  > "$EVIDENCE_DIR/account-verification.json"
jq -e '.name == "oai-msp-anthony-dev-eastus" and .location == "eastus" and .kind == "OpenAI" and .sku == "S0" and .provisioningState == "Succeeded" and .disableLocalAuth == true and .publicNetworkAccess == "Enabled"' \
  "$EVIDENCE_DIR/account-verification.json" >/dev/null || fail_closed "account_verification_failed" "$CURRENT_STAGE"

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
    .sku.name == $sku and
    (.sku.capacity | tonumber) == 1
  ' "$EVIDENCE_DIR/model-verification.json" >/dev/null || fail_closed "model_verification_failed" "$CURRENT_STAGE"

az role assignment list \
  --assignee-object-id "$principal_id" \
  --scope "$account_id" \
  --all \
  --output json \
  | jq \
      --arg role "$ROLE_NAME" \
      --arg role_guid "$ROLE_DEFINITION_GUID" \
      --arg scope "$account_id" '[
        .[]?
        | select(
            (.roleDefinitionName // "") == $role and
            ((.roleDefinitionId // "") | endswith("/" + $role_guid)) and
            ((.scope // "") | ascii_downcase) == ($scope | ascii_downcase)
          )
        | {roleDefinitionName,roleDefinitionGuid:((.roleDefinitionId // "") | split("/") | last),principalType,scope:"<target-account>",directAccountScope:true}
      ]' > "$EVIDENCE_DIR/rbac-verification.json"
jq -e 'length > 0' "$EVIDENCE_DIR/rbac-verification.json" >/dev/null || fail_closed "role_verification_failed" "$CURRENT_STAGE"

CURRENT_STAGE="single_model_request"
MODEL_REQUEST_PERFORMED=true
token="$(az account get-access-token --scope https://cognitiveservices.azure.com/.default --query accessToken --output tsv)"
base_url="https://${ACCOUNT_NAME}.openai.azure.com/openai/v1/"
request='{"model":"'"$DEPLOYMENT_NAME"'","input":"Reply with exactly: AZURE AI RUN 7 LIVE","max_output_tokens":'"$MAX_OUTPUT_TOKENS"'}'
headers_tmp="${RUNNER_TEMP}/run7-response-headers.txt"
response_tmp="${RUNNER_TEMP}/run7-response.json"
http_code="$(curl --silent --show-error \
  --dump-header "$headers_tmp" \
  --output "$response_tmp" \
  --write-out '%{http_code}' \
  --request POST \
  --url "${base_url}responses?api-version=v1" \
  --header "Authorization: Bearer ${token}" \
  --header 'Content-Type: application/json' \
  --data "$request" || true)"
printf '%s\n' "$http_code" > "$EVIDENCE_DIR/model-call-http-status.txt"
awk 'BEGIN{IGNORECASE=1} /^HTTP\// || /^apim-request-id:/ {print}' "$headers_tmp" > "$EVIDENCE_DIR/model-call-headers.txt"

if [[ "$http_code" != "200" ]]; then
  jq '{error}' "$response_tmp" > "$EVIDENCE_DIR/model-call-failure.json" 2>/dev/null || true
  fail_closed "inference_failed" "$CURRENT_STAGE"
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
' "$response_tmp" > "$EVIDENCE_DIR/model-call-receipt.json"
jq -e '.output_text | contains("AZURE AI RUN 7 LIVE")' "$EVIDENCE_DIR/model-call-receipt.json" >/dev/null || fail_closed "unexpected_model_output" "$CURRENT_STAGE"

ENDPOINT_LIVE=true
CURRENT_STAGE="complete"
write_terminal_summary "live_verified" "$CURRENT_STAGE"
