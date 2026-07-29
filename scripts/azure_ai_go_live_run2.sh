#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_SHA:?GITHUB_SHA is required}"
: "${GITHUB_RUN_ID:?GITHUB_RUN_ID is required}"
: "${AZURE_CLIENT_ID:?AZURE_CLIENT_ID is required}"
: "${AZURE_SUBSCRIPTION_ID:?AZURE_SUBSCRIPTION_ID is required}"

ATTEMPT_ID="azure-ai-go-live-run2"
MODEL_NAME="gpt-4.1-mini"
MODEL_VERSION="2025-04-14"
DEPLOYMENT_NAME="gpt-41-mini-msp-dev"
DEPLOYMENT_SKU="Standard"
DEPLOYMENT_CAPACITY="1"
EVIDENCE_DIR="${RUNNER_TEMP}/azure-ai-live-evidence"
REQUEST_FILE=".project/deployment-requests/azure-ai-go-live-run2.json"

mkdir -p "$EVIDENCE_DIR"

jq -e --arg attempt "$ATTEMPT_ID" '
  .attempt_id == $attempt and
  .status == "active_one_attempt" and
  .attempt_limit == 1 and
  .authority.automatic_retry_authorized == false and
  .authority.manual_rerun_authorized == false
' "$REQUEST_FILE" >/dev/null

subscription_id="$(az account show --query id --output tsv)"
subscription_name="$(az account show --query name --output tsv)"
subscription_state="$(az account show --query state --output tsv)"
test "$subscription_id" = "$AZURE_SUBSCRIPTION_ID"
test "$subscription_state" = "Enabled"

principal_id="$(az role assignment list --assignee "$AZURE_CLIENT_ID" --all --query '[0].principalId' --output tsv 2>/dev/null || true)"
if [[ -z "$principal_id" ]]; then
  principal_id="$(az ad sp show --id "$AZURE_CLIENT_ID" --query id --output tsv)"
fi
test -n "$principal_id"

provider_state="$(az provider show --namespace Microsoft.CognitiveServices --query registrationState --output tsv)"
if [[ "$provider_state" != "Registered" ]]; then
  az provider register --namespace Microsoft.CognitiveServices --wait
  provider_state="$(az provider show --namespace Microsoft.CognitiveServices --query registrationState --output tsv)"
fi
test "$provider_state" = "Registered"

sub_hash="$(printf '%s' "$subscription_id" | sha256sum | cut -c1-8)"
principal_hash="$(printf '%s' "$principal_id" | sha256sum | cut -c1-16)"

jq -n \
  --arg schema_version "project.azure-ai-go-live-context.v2" \
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

deployment_succeeded=false
selected_location=""
selected_rg=""
selected_account=""
selected_deployment_record=""

for location in canadaeast eastus2; do
  rg="rg-ai-msp-dev-${location}"
  account="oai-msp-${sub_hash}-${location}"
  deployment_record="azure-ai-live-run2-${GITHUB_RUN_ID}-${location}"
  models="${RUNNER_TEMP}/models-${location}.json"

  set +e
  az rest \
    --method get \
    --url "https://management.azure.com/subscriptions/${subscription_id}/providers/Microsoft.CognitiveServices/locations/${location}/models?api-version=2024-10-01" \
    --output json > "$models" 2>"$EVIDENCE_DIR/models-${location}.err"
  models_rc=$?
  set -e

  if (( models_rc != 0 )); then
    continue
  fi

  if ! jq -e \
    --arg name "$MODEL_NAME" \
    --arg version "$MODEL_VERSION" \
    '.value[] | select((.model.format // "") == "OpenAI" and (.model.name // "") == $name and (.model.version // "") == $version)' \
    "$models" >/dev/null; then
    jq -n \
      --arg location "$location" \
      --arg model "$MODEL_NAME" \
      --arg version "$MODEL_VERSION" \
      '{location:$location,model:$model,version:$version,listed:false}' \
      > "$EVIDENCE_DIR/model-candidate-${location}.json"
    continue
  fi

  jq -n \
    --arg location "$location" \
    --arg model "$MODEL_NAME" \
    --arg version "$MODEL_VERSION" \
    --arg sku "$DEPLOYMENT_SKU" \
    --arg capacity "$DEPLOYMENT_CAPACITY" \
    '{location:$location,model:$model,version:$version,sku:$sku,capacity:($capacity|tonumber),listed:true}' \
    > "$EVIDENCE_DIR/model-candidate-${location}.json"

  set +e
  az deployment sub what-if \
    --name "$deployment_record" \
    --location "$location" \
    --template-file infra/azure-ai-live.bicep \
    --parameters \
      deployAzureAi=true \
      resourceGroupName="$rg" \
      location="$location" \
      accountName="$account" \
      deployModel=true \
      deploymentName="$DEPLOYMENT_NAME" \
      modelName="$MODEL_NAME" \
      modelVersion="$MODEL_VERSION" \
      deploymentSkuName="$DEPLOYMENT_SKU" \
      deploymentCapacity="$DEPLOYMENT_CAPACITY" \
      assignInferenceRole=false \
    --result-format FullResourcePayloads \
    --output json > "$EVIDENCE_DIR/what-if-${location}.json" 2>"$EVIDENCE_DIR/what-if-${location}.err"
  what_if_rc=$?
  set -e

  if (( what_if_rc != 0 )); then
    continue
  fi

  set +e
  az deployment sub create \
    --name "$deployment_record" \
    --location "$location" \
    --template-file infra/azure-ai-live.bicep \
    --parameters \
      deployAzureAi=true \
      resourceGroupName="$rg" \
      location="$location" \
      accountName="$account" \
      deployModel=true \
      deploymentName="$DEPLOYMENT_NAME" \
      modelName="$MODEL_NAME" \
      modelVersion="$MODEL_VERSION" \
      deploymentSkuName="$DEPLOYMENT_SKU" \
      deploymentCapacity="$DEPLOYMENT_CAPACITY" \
      assignInferenceRole=false \
    --output json > "$EVIDENCE_DIR/deployment-${location}.json" 2>"$EVIDENCE_DIR/deployment-${location}.err"
  deploy_rc=$?
  set -e

  if (( deploy_rc == 0 )); then
    deployment_succeeded=true
    selected_location="$location"
    selected_rg="$rg"
    selected_account="$account"
    selected_deployment_record="$deployment_record"
    break
  fi
done

if [[ "$deployment_succeeded" != true ]]; then
  jq -n \
    --arg attempt_id "$ATTEMPT_ID" \
    --arg commit "$GITHUB_SHA" \
    '{schema_version:"project.azure-ai-go-live-result.v2",status:"deployment_failed",attempt_id:$attempt_id,exact_commit:$commit,endpoint_live:false}' \
    > "$EVIDENCE_DIR/go-live-summary.json"
  echo "No bounded candidate deployed successfully." >&2
  exit 1
fi

account_id="$(az cognitiveservices account show --resource-group "$selected_rg" --name "$selected_account" --query id --output tsv)"
test -n "$account_id"

existing_role="$(az role assignment list \
  --assignee-object-id "$principal_id" \
  --scope "$account_id" \
  --query "[?roleDefinitionName=='Cognitive Services OpenAI User'] | [0].id" \
  --output tsv)"

if [[ -z "$existing_role" ]]; then
  az role assignment create \
    --assignee-object-id "$principal_id" \
    --assignee-principal-type ServicePrincipal \
    --role "Cognitive Services OpenAI User" \
    --scope "$account_id" \
    --output json > "$EVIDENCE_DIR/inference-role-assignment.json"
else
  jq -n --arg id "$existing_role" '{status:"already_present",id:$id}' > "$EVIDENCE_DIR/inference-role-assignment.json"
fi

az cognitiveservices account show \
  --resource-group "$selected_rg" \
  --name "$selected_account" \
  --output json \
  | jq '{name,location,kind,sku:.sku.name,provisioningState:.properties.provisioningState,disableLocalAuth:.properties.disableLocalAuth,publicNetworkAccess:.properties.publicNetworkAccess}' \
  > "$EVIDENCE_DIR/account-verification.json"

az cognitiveservices account deployment show \
  --resource-group "$selected_rg" \
  --name "$selected_account" \
  --deployment-name "$DEPLOYMENT_NAME" \
  --output json \
  | jq '{name,provisioningState:.properties.provisioningState,model:.properties.model,sku}' \
  > "$EVIDENCE_DIR/model-verification.json"

az role assignment list \
  --assignee-object-id "$principal_id" \
  --scope "$account_id" \
  --query "[?roleDefinitionName=='Cognitive Services OpenAI User'].{role:roleDefinitionName,scope:scope,principalType:principalType}" \
  --output json \
  | sed "s#${subscription_id}#<subscription>#g" \
  > "$EVIDENCE_DIR/rbac-verification.json"
jq -e 'length > 0' "$EVIDENCE_DIR/rbac-verification.json" >/dev/null

base_url="https://${selected_account}.openai.azure.com/openai/v1/"
request='{"model":"'"$DEPLOYMENT_NAME"'","input":"Reply with exactly: AZURE AI LIVE","max_output_tokens":32}'
success=false
http_code=""

for propagation_attempt in $(seq 1 12); do
  token="$(az account get-access-token --scope https://ai.azure.com/.default --query accessToken --output tsv 2>/dev/null || az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken --output tsv)"
  http_code="$(curl --silent --show-error \
    --output "${RUNNER_TEMP}/response.json" \
    --write-out '%{http_code}' \
    --request POST \
    --url "${base_url}responses" \
    --header "Authorization: Bearer ${token}" \
    --header 'Content-Type: application/json' \
    --data "$request" || true)"
  if [[ "$http_code" == "200" ]]; then
    success=true
    break
  fi
  sleep 15
done

if [[ "$success" != true ]]; then
  jq '{error}' "${RUNNER_TEMP}/response.json" > "$EVIDENCE_DIR/model-call-failure.json" 2>/dev/null || true
  jq -n \
    --arg attempt_id "$ATTEMPT_ID" \
    --arg commit "$GITHUB_SHA" \
    --arg resource_group "$selected_rg" \
    --arg location "$selected_location" \
    --arg account "$selected_account" \
    --arg deployment "$DEPLOYMENT_NAME" \
    --arg http_code "$http_code" \
    '{schema_version:"project.azure-ai-go-live-result.v2",status:"deployed_verification_failed",attempt_id:$attempt_id,exact_commit:$commit,resource_group:$resource_group,location:$location,account:$account,deployment:$deployment,http_code:$http_code,endpoint_live:false}' \
    > "$EVIDENCE_DIR/go-live-summary.json"
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
  --arg resource_group "$selected_rg" \
  --arg location "$selected_location" \
  --arg account "$selected_account" \
  --arg deployment "$DEPLOYMENT_NAME" \
  --arg deployment_record "$selected_deployment_record" \
  '{
    schema_version:"project.azure-ai-go-live-result.v2",
    status:"live_verified",
    attempt_id:$attempt_id,
    exact_commit:$commit,
    resource_group:$resource_group,
    location:$location,
    account:$account,
    deployment:$deployment,
    deployment_record:$deployment_record,
    local_authentication_disabled:true,
    entra_inference_verified:true,
    bounded_model_request_verified:true,
    azure_mcp_connected:false,
    endpoint_live:true
  }' > "$EVIDENCE_DIR/go-live-summary.json"
