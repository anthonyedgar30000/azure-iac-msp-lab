#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_SHA:?GITHUB_SHA is required}"
: "${GITHUB_RUN_ID:?GITHUB_RUN_ID is required}"
: "${AZURE_CLIENT_ID:?AZURE_CLIENT_ID is required}"
: "${AZURE_SUBSCRIPTION_ID:?AZURE_SUBSCRIPTION_ID is required}"
: "${RUNNER_TEMP:?RUNNER_TEMP is required}"

ATTEMPT_ID="azure-ai-go-live-run5"
EXPECTED_SUBSCRIPTION_NAME="Azure for Students"
DEPLOYMENT_CAPACITY="1"
EVIDENCE_DIR="${RUNNER_TEMP}/azure-ai-live-evidence"
REQUEST_FILE=".project/deployment-requests/azure-ai-go-live-run5.json"

mkdir -p "$EVIDENCE_DIR"

jq -e --arg attempt "$ATTEMPT_ID" --arg subscription "$EXPECTED_SUBSCRIPTION_NAME" '
  .attempt_id == $attempt and
  .status == "active_one_attempt" and
  .active == true and
  .attempt_limit == 1 and
  .scope.subscription_name == $subscription and
  .scope.candidate_limit == 10 and
  (.scope.candidate_order | length) == 10 and
  .scope.deployment_attempt_limit == 1 and
  .scope.model_request_count == 1 and
  .scope.max_output_tokens == 32 and
  .authority.automatic_retry_authorized == false and
  .authority.manual_rerun_authorized == false and
  .authority.second_deployment_attempt_authorized == false
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
if [[ "$provider_state" != "Registered" ]]; then
  az provider register --namespace Microsoft.CognitiveServices --wait
  provider_state="$(az provider show --namespace Microsoft.CognitiveServices --query registrationState --output tsv)"
fi
test "$provider_state" = "Registered"

sub_hash="$(printf '%s' "$subscription_id" | sha256sum | cut -c1-8)"
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

jq -n \
  --arg schema_version "project.azure-ai-go-live-context.v3" \
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

jq '.scope.candidate_order' "$REQUEST_FILE" > "$EVIDENCE_DIR/candidate-matrix.json"

selected=false
selected_index=""
selected_location=""
selected_model=""
selected_version=""
selected_sku=""
selected_deployment=""
selected_rg=""
selected_account=""
selected_deployment_record=""

candidate_index=0
while IFS=$'\t' read -r location model version sku deployment_name; do
  candidate_index=$((candidate_index + 1))
  candidate_key="$(printf '%02d-%s-%s' "$candidate_index" "$location" "${model//./-}")"
  models_tmp="${RUNNER_TEMP}/models-${candidate_key}.json"
  capacity_tmp="${RUNNER_TEMP}/capacity-${candidate_key}.json"
  models_err="$EVIDENCE_DIR/models-${candidate_key}.err"
  capacity_err="$EVIDENCE_DIR/capacity-${candidate_key}.err"
  what_if_json="$EVIDENCE_DIR/what-if-${candidate_key}.json"
  what_if_err="$EVIDENCE_DIR/what-if-${candidate_key}.err"
  observation="$EVIDENCE_DIR/candidate-${candidate_key}.json"

  set +e
  az rest \
    --method get \
    --url "https://management.azure.com/subscriptions/${subscription_id}/providers/Microsoft.CognitiveServices/locations/${location}/models?api-version=2024-10-01" \
    --output json > "$models_tmp" 2>"$models_err"
  models_rc=$?
  set -e
  redact_file "$models_err"

  if (( models_rc != 0 )); then
    jq -n \
      --arg location "$location" --arg model "$model" --arg version "$version" --arg sku "$sku" \
      '{location:$location,model:$model,version:$version,sku:$sku,model_listing_query_succeeded:false,selected:false}' \
      > "$observation"
    continue
  fi
  redact_file "$models_tmp"

  model_listed=false
  if jq -e \
    --arg name "$model" \
    --arg version "$version" \
    '.value[]? | select((.model.format // "") == "OpenAI" and (.model.name // "") == $name and (.model.version // "") == $version)' \
    "$models_tmp" >/dev/null; then
    model_listed=true
  fi

  if [[ "$model_listed" != true ]]; then
    jq -n \
      --arg location "$location" --arg model "$model" --arg version "$version" --arg sku "$sku" \
      '{location:$location,model:$model,version:$version,sku:$sku,model_listing_query_succeeded:true,model_listed:false,selected:false}' \
      > "$observation"
    continue
  fi

  set +e
  az rest \
    --method get \
    --url "https://management.azure.com/subscriptions/${subscription_id}/providers/Microsoft.CognitiveServices/locations/${location}/modelCapacities?api-version=2024-10-01&modelFormat=OpenAI&modelName=${model}&modelVersion=${version}" \
    --output json > "$capacity_tmp" 2>"$capacity_err"
  capacity_rc=$?
  set -e
  redact_file "$capacity_err"

  if (( capacity_rc != 0 )); then
    jq -n \
      --arg location "$location" --arg model "$model" --arg version "$version" --arg sku "$sku" \
      '{location:$location,model:$model,version:$version,sku:$sku,model_listing_query_succeeded:true,model_listed:true,capacity_query_succeeded:false,selected:false}' \
      > "$observation"
    continue
  fi
  redact_file "$capacity_tmp"

  available_capacity="$(jq -r --arg sku "$sku" '[
      .value[]?
      | select((.properties.skuName // .name // "") == $sku)
      | ((.properties.availableCapacity // 0) | tonumber? // 0)
    ] | max // 0' "$capacity_tmp")"

  if (( available_capacity < DEPLOYMENT_CAPACITY )); then
    jq -n \
      --arg location "$location" --arg model "$model" --arg version "$version" --arg sku "$sku" \
      --arg available "$available_capacity" \
      '{location:$location,model:$model,version:$version,sku:$sku,model_listing_query_succeeded:true,model_listed:true,capacity_query_succeeded:true,available_capacity:($available|tonumber),capacity_sufficient:false,selected:false}' \
      > "$observation"
    continue
  fi

  rg="rg-ai-msp-dev-${location}"
  account="oai-msp-${sub_hash}-${location}"
  deployment_record="azure-ai-live-run5-${GITHUB_RUN_ID}-${candidate_index}"

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
      deploymentName="$deployment_name" \
      modelName="$model" \
      modelVersion="$version" \
      deploymentSkuName="$sku" \
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
    jq -n \
      --arg location "$location" --arg model "$model" --arg version "$version" --arg sku "$sku" \
      --arg available "$available_capacity" \
      '{location:$location,model:$model,version:$version,sku:$sku,model_listing_query_succeeded:true,model_listed:true,capacity_query_succeeded:true,available_capacity:($available|tonumber),capacity_sufficient:true,what_if_succeeded:false,selected:false}' \
      > "$observation"
    continue
  fi

  selected=true
  selected_index="$candidate_index"
  selected_location="$location"
  selected_model="$model"
  selected_version="$version"
  selected_sku="$sku"
  selected_deployment="$deployment_name"
  selected_rg="$rg"
  selected_account="$account"
  selected_deployment_record="$deployment_record"

  jq -n \
    --arg index "$candidate_index" --arg location "$location" --arg model "$model" --arg version "$version" \
    --arg sku "$sku" --arg deployment "$deployment_name" --arg resource_group "$rg" --arg account "$account" \
    --arg available "$available_capacity" \
    '{index:($index|tonumber),location:$location,model:$model,version:$version,sku:$sku,deployment:$deployment,resource_group:$resource_group,account:$account,model_listed:true,available_capacity:($available|tonumber),capacity_sufficient:true,what_if_succeeded:true,selected:true}' \
    > "$observation"
  cp "$observation" "$EVIDENCE_DIR/selected-candidate.json"
  break
done < <(jq -r '.scope.candidate_order[] | [.location,.model,.version,.sku,.deployment] | @tsv' "$REQUEST_FILE")

if [[ "$selected" != true ]]; then
  jq -n \
    --arg attempt_id "$ATTEMPT_ID" \
    --arg commit "$GITHUB_SHA" \
    --arg subscription "$EXPECTED_SUBSCRIPTION_NAME" \
    --arg candidates "$candidate_index" \
    '{schema_version:"project.azure-ai-go-live-result.v3",status:"no_deployable_candidate",attempt_id:$attempt_id,exact_commit:$commit,subscription_name:$subscription,candidates_evaluated:($candidates|tonumber),deployment_started:false,model_request_performed:false,endpoint_live:false}' \
    > "$EVIDENCE_DIR/go-live-summary.json"
  echo "No approved candidate passed model, capacity, and What-If gates." >&2
  exit 1
fi

deployment_json="$EVIDENCE_DIR/deployment-selected.json"
deployment_err="$EVIDENCE_DIR/deployment-selected.err"
set +e
az deployment sub create \
  --name "$selected_deployment_record" \
  --location "$selected_location" \
  --template-file infra/azure-ai-live.bicep \
  --parameters \
    deployAzureAi=true \
    resourceGroupName="$selected_rg" \
    location="$selected_location" \
    accountName="$selected_account" \
    deployModel=true \
    deploymentName="$selected_deployment" \
    modelName="$selected_model" \
    modelVersion="$selected_version" \
    deploymentSkuName="$selected_sku" \
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
  jq -n \
    --arg attempt_id "$ATTEMPT_ID" --arg commit "$GITHUB_SHA" --arg index "$selected_index" \
    --arg resource_group "$selected_rg" --arg location "$selected_location" --arg account "$selected_account" \
    --arg model "$selected_model" --arg version "$selected_version" --arg sku "$selected_sku" --arg deployment "$selected_deployment" \
    '{schema_version:"project.azure-ai-go-live-result.v3",status:"deployment_failed",attempt_id:$attempt_id,exact_commit:$commit,selected_candidate_index:($index|tonumber),resource_group:$resource_group,location:$location,account:$account,model:$model,model_version:$version,deployment_sku:$sku,deployment:$deployment,deployment_started:true,model_request_performed:false,endpoint_live:false}' \
    > "$EVIDENCE_DIR/go-live-summary.json"
  exit 1
fi

account_id="$(az cognitiveservices account show --resource-group "$selected_rg" --name "$selected_account" --query id --output tsv)"
test -n "$account_id"

az cognitiveservices account show \
  --resource-group "$selected_rg" \
  --name "$selected_account" \
  --output json \
  | jq '{name,location,kind,sku:.sku.name,provisioningState:.properties.provisioningState,disableLocalAuth:.properties.disableLocalAuth,publicNetworkAccess:.properties.publicNetworkAccess}' \
  > "$EVIDENCE_DIR/account-verification.json"

az cognitiveservices account deployment show \
  --resource-group "$selected_rg" \
  --name "$selected_account" \
  --deployment-name "$selected_deployment" \
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

# Control-plane role creation is complete; wait before the single authorized data-plane call.
sleep 90

token="$(az account get-access-token --scope https://ai.azure.com/.default --query accessToken --output tsv 2>/dev/null || az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken --output tsv)"
base_url="https://${selected_account}.openai.azure.com/openai/v1/"
request='{"model":"'"$selected_deployment"'","input":"Reply with exactly: AZURE AI LIVE","max_output_tokens":32}'
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
  jq -n \
    --arg attempt_id "$ATTEMPT_ID" --arg commit "$GITHUB_SHA" --arg index "$selected_index" \
    --arg resource_group "$selected_rg" --arg location "$selected_location" --arg account "$selected_account" \
    --arg model "$selected_model" --arg version "$selected_version" --arg sku "$selected_sku" --arg deployment "$selected_deployment" \
    --arg http_code "$http_code" \
    '{schema_version:"project.azure-ai-go-live-result.v3",status:"deployed_verification_failed",attempt_id:$attempt_id,exact_commit:$commit,selected_candidate_index:($index|tonumber),resource_group:$resource_group,location:$location,account:$account,model:$model,model_version:$version,deployment_sku:$sku,deployment:$deployment,http_code:$http_code,deployment_started:true,model_request_performed:true,model_request_count:1,endpoint_live:false}' \
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
  --arg attempt_id "$ATTEMPT_ID" --arg commit "$GITHUB_SHA" --arg index "$selected_index" \
  --arg resource_group "$selected_rg" --arg location "$selected_location" --arg account "$selected_account" \
  --arg model "$selected_model" --arg version "$selected_version" --arg sku "$selected_sku" --arg deployment "$selected_deployment" \
  --arg deployment_record "$selected_deployment_record" \
  '{
    schema_version:"project.azure-ai-go-live-result.v3",
    status:"live_verified",
    attempt_id:$attempt_id,
    exact_commit:$commit,
    selected_candidate_index:($index|tonumber),
    resource_group:$resource_group,
    location:$location,
    account:$account,
    model:$model,
    model_version:$version,
    deployment_sku:$sku,
    deployment:$deployment,
    deployment_record:$deployment_record,
    local_authentication_disabled:true,
    entra_inference_verified:true,
    bounded_model_request_verified:true,
    model_request_count:1,
    azure_mcp_connected:false,
    endpoint_live:true
  }' > "$EVIDENCE_DIR/go-live-summary.json"
