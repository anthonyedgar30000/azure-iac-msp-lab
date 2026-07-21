#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: resolve_vm_plan.sh \
  --resource-group NAME \
  --location REGION \
  --prefix PREFIX \
  --environment dev|test \
  --deploy-demo-backends true|false \
  --requested-backend-size auto|Standard_* \
  --deploy-public-report-endpoint true|false \
  --requested-collector-size auto|Standard_* \
  --collector-source-ref SHA \
  --expected-private-ip ADDRESS \
  --collector-port PORT \
  --collector-admin-ssh-public-key KEY \
  --artifact-dir PATH \
  --github-output PATH
EOF
}

RESOURCE_GROUP=''
LOCATION=''
PREFIX=''
LAB_ENVIRONMENT=''
DEPLOY_DEMO_BACKENDS='false'
REQUESTED_BACKEND_SIZE='auto'
DEPLOY_PUBLIC_REPORT_ENDPOINT='false'
REQUESTED_COLLECTOR_SIZE='auto'
COLLECTOR_SOURCE_REF=''
EXPECTED_PRIVATE_IP=''
COLLECTOR_PORT=''
COLLECTOR_ADMIN_SSH_PUBLIC_KEY=''
ARTIFACT_DIR=''
GITHUB_OUTPUT_PATH=''

while (($#)); do
  case "$1" in
    --resource-group) RESOURCE_GROUP="$2"; shift 2 ;;
    --location) LOCATION="$2"; shift 2 ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    --environment) LAB_ENVIRONMENT="$2"; shift 2 ;;
    --deploy-demo-backends) DEPLOY_DEMO_BACKENDS="$2"; shift 2 ;;
    --requested-backend-size) REQUESTED_BACKEND_SIZE="$2"; shift 2 ;;
    --deploy-public-report-endpoint) DEPLOY_PUBLIC_REPORT_ENDPOINT="$2"; shift 2 ;;
    --requested-collector-size) REQUESTED_COLLECTOR_SIZE="$2"; shift 2 ;;
    --collector-source-ref) COLLECTOR_SOURCE_REF="$2"; shift 2 ;;
    --expected-private-ip) EXPECTED_PRIVATE_IP="$2"; shift 2 ;;
    --collector-port) COLLECTOR_PORT="$2"; shift 2 ;;
    --collector-admin-ssh-public-key) COLLECTOR_ADMIN_SSH_PUBLIC_KEY="$2"; shift 2 ;;
    --artifact-dir) ARTIFACT_DIR="$2"; shift 2 ;;
    --github-output) GITHUB_OUTPUT_PATH="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

for required in RESOURCE_GROUP LOCATION PREFIX LAB_ENVIRONMENT COLLECTOR_SOURCE_REF EXPECTED_PRIVATE_IP COLLECTOR_PORT ARTIFACT_DIR GITHUB_OUTPUT_PATH; do
  [[ -n "${!required}" ]] || {
    echo "Missing required value: $required" >&2
    exit 2
  }
done

mkdir -p "$ARTIFACT_DIR"

[[ "$COLLECTOR_SOURCE_REF" =~ ^[0-9a-fA-F]{40}$ ]]
[[ "$DEPLOY_DEMO_BACKENDS" =~ ^(true|false)$ ]]
[[ "$DEPLOY_PUBLIC_REPORT_ENDPOINT" =~ ^(true|false)$ ]]
[[ "$REQUESTED_BACKEND_SIZE" == auto || "$REQUESTED_BACKEND_SIZE" =~ ^Standard_[A-Za-z0-9_]+$ ]]
[[ "$REQUESTED_COLLECTOR_SIZE" == auto || "$REQUESTED_COLLECTOR_SIZE" =~ ^Standard_[A-Za-z0-9_]+$ ]]

collector_vm_name="vm-stcollector-${PREFIX}-${LAB_ENVIRONMENT}"
current_collector_size="$(az vm show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$collector_vm_name" \
  --query hardwareProfile.vmSize \
  --output tsv 2>/dev/null || true)"

jq -n \
  --arg vmName "$collector_vm_name" \
  --arg vmSize "$current_collector_size" \
  '{collector_vm_name:$vmName,current_collector_vm_size:(if $vmSize=="" then null else $vmSize end)}' \
  > "$ARTIFACT_DIR/current-compute-state.json"

bounded_defaults=(
  Standard_B1s
  Standard_B1ms
  Standard_B2s
  Standard_B2ms
  Standard_D2as_v5
  Standard_D2s_v5
)

append_unique() {
  local -n destination="$1"
  local value="$2"
  local existing
  [[ -n "$value" ]] || return 0
  for existing in "${destination[@]:-}"; do
    [[ "$existing" == "$value" ]] && return 0
  done
  destination+=("$value")
}

build_candidates() {
  local requested="$1"
  local include_current="$2"
  local -n destination="$3"
  local sku

  if [[ "$requested" != auto ]]; then
    append_unique destination "$requested"
    return
  fi

  if [[ "$include_current" == true ]]; then
    append_unique destination "$current_collector_size"
  fi
  for sku in "${bounded_defaults[@]}"; do
    append_unique destination "$sku"
  done
}

backend_candidates=()
collector_candidates=()
build_candidates "$REQUESTED_BACKEND_SIZE" true backend_candidates
build_candidates "$REQUESTED_COLLECTOR_SIZE" true collector_candidates

printf '%s\n' "${backend_candidates[@]}" > "$ARTIFACT_DIR/backend-candidates.txt"
printf '%s\n' "${collector_candidates[@]}" > "$ARTIFACT_DIR/collector-candidates.txt"

# Azure SKU metadata is captured for provenance and troubleshooting, but it is
# deliberately not an admission gate. Restrictions can be broad, stale, or
# unrelated to the exact deployment shape. ARM deployment validation below is
# the authoritative pre-deployment decision.
az vm list-skus \
  --location "$LOCATION" \
  --resource-type virtualMachines \
  --all \
  --output json > "$ARTIFACT_DIR/vm-sku-catalog.json"

: > "$ARTIFACT_DIR/sku-metadata.jsonl"
record_sku_metadata() {
  local role="$1"
  local sku="$2"
  jq -c \
    --arg role "$role" \
    --arg sku "$sku" \
    '([.[] | select(.name == $sku)][0] // null) as $entry |
     {role:$role,sku:$sku,catalog_entry_found:($entry != null),restrictions:($entry.restrictions // [])}' \
    "$ARTIFACT_DIR/vm-sku-catalog.json" >> "$ARTIFACT_DIR/sku-metadata.jsonl"
}

for sku in "${backend_candidates[@]}"; do record_sku_metadata backend "$sku"; done
for sku in "${collector_candidates[@]}"; do record_sku_metadata collector "$sku"; done

: > "$ARTIFACT_DIR/sku-validation-attempts.jsonl"
selected_backend=''
selected_collector=''

is_capacity_related_error() {
  grep -Eqi \
    'SkuNotAvailable|NotAvailableForSubscription|AllocationFailed|OverconstrainedAllocationRequest|ZonalAllocationFailed|capacity restriction|currently not available|insufficient capacity|OperationNotAllowed.*quota|QuotaExceeded' \
    "$1"
}

for collector_size in "${collector_candidates[@]}"; do
  for backend_size in "${backend_candidates[@]}"; do
    safe_collector="${collector_size//[^A-Za-z0-9_-]/_}"
    safe_backend="${backend_size//[^A-Za-z0-9_-]/_}"
    validation_output="$ARTIFACT_DIR/deployment-validation-${safe_collector}-${safe_backend}.json"
    validation_error="$ARTIFACT_DIR/deployment-validation-${safe_collector}-${safe_backend}.stderr"

    common_parameters=(
      prefix="$PREFIX"
      environment="$LAB_ENVIRONMENT"
      location="$LOCATION"
      deployDemoBackends="$DEPLOY_DEMO_BACKENDS"
      demoBackendVmSize="$backend_size"
      deployOperationsCollector=true
      deployPublicReportEndpoint="$DEPLOY_PUBLIC_REPORT_ENDPOINT"
      collectorVmSize="$collector_size"
      collectorPrivateIpAddress="$EXPECTED_PRIVATE_IP"
      collectorPort="$COLLECTOR_PORT"
      collectorAdminSshPublicKey="$COLLECTOR_ADMIN_SSH_PUBLIC_KEY"
      collectorSourceRef="$COLLECTOR_SOURCE_REF"
    )

    if az deployment group validate \
      --resource-group "$RESOURCE_GROUP" \
      --template-file infra/main.bicep \
      --parameters "${common_parameters[@]}" \
      --output json > "$validation_output" 2> "$validation_error"; then
      selected_backend="$backend_size"
      selected_collector="$collector_size"
      cp "$validation_output" "$ARTIFACT_DIR/deployment-validation.json"
      jq -n \
        --arg collector "$collector_size" \
        --arg backend "$backend_size" \
        --arg status succeeded \
        '{collector_vm_size:$collector,demo_backend_vm_size:$backend,status:$status}' \
        >> "$ARTIFACT_DIR/sku-validation-attempts.jsonl"
      break 2
    fi

    error_text="$(cat "$validation_error")"
    jq -n \
      --arg collector "$collector_size" \
      --arg backend "$backend_size" \
      --arg status rejected \
      --arg error "$error_text" \
      '{collector_vm_size:$collector,demo_backend_vm_size:$backend,status:$status,error:$error}' \
      >> "$ARTIFACT_DIR/sku-validation-attempts.jsonl"

    if ! is_capacity_related_error "$validation_error"; then
      cat "$validation_error" >&2
      echo 'ARM validation failed for a reason other than capacity or quota; refusing to hide it behind VM-size fallback.' >&2
      exit 1
    fi
  done
done

[[ -n "$selected_backend" && -n "$selected_collector" ]] || {
  echo 'ARM validation rejected every bounded VM-size combination for this subscription and region.' >&2
  cat "$ARTIFACT_DIR/sku-validation-attempts.jsonl" >&2
  exit 1
}

selected_parameters=(
  prefix="$PREFIX"
  environment="$LAB_ENVIRONMENT"
  location="$LOCATION"
  deployDemoBackends="$DEPLOY_DEMO_BACKENDS"
  demoBackendVmSize="$selected_backend"
  deployOperationsCollector=true
  deployPublicReportEndpoint="$DEPLOY_PUBLIC_REPORT_ENDPOINT"
  collectorVmSize="$selected_collector"
  collectorPrivateIpAddress="$EXPECTED_PRIVATE_IP"
  collectorPort="$COLLECTOR_PORT"
  collectorAdminSshPublicKey="$COLLECTOR_ADMIN_SSH_PUBLIC_KEY"
  collectorSourceRef="$COLLECTOR_SOURCE_REF"
)

az deployment group what-if \
  --resource-group "$RESOURCE_GROUP" \
  --name "servicetracer-${LAB_ENVIRONMENT}" \
  --template-file infra/main.bicep \
  --parameters "${selected_parameters[@]}" \
  --no-pretty-print \
  --output json > "$ARTIFACT_DIR/what-if.json"

printf 'demo_backend_vm_size=%s\n' "$selected_backend" >> "$GITHUB_OUTPUT_PATH"
printf 'collector_vm_size=%s\n' "$selected_collector" >> "$GITHUB_OUTPUT_PATH"
printf 'collector_source_ref=%s\n' "$COLLECTOR_SOURCE_REF" >> "$GITHUB_OUTPUT_PATH"

jq -n \
  --arg sourceRef "$COLLECTOR_SOURCE_REF" \
  --arg collectorVmSize "$selected_collector" \
  --arg demoBackendVmSize "$selected_backend" \
  --arg currentCollectorVmSize "$current_collector_size" \
  '{collector_source_ref:$sourceRef,collector_vm_size:$collectorVmSize,demo_backend_vm_size:$demoBackendVmSize,current_collector_vm_size:(if $currentCollectorVmSize=="" then null else $currentCollectorVmSize end),decision_authority:"arm_deployment_validation",sku_metadata_role:"advisory"}' \
  > "$ARTIFACT_DIR/resolved-deployment-plan.json"
