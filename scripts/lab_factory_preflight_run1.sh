#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REQUEST_PATH="$REPOSITORY_ROOT/.project/deployment-requests/lab-factory-preflight-run1.json"
EVIDENCE_DIR="${RUNNER_TEMP:?}/lab-factory-preflight-run1"
RAW_DIR="${RUNNER_TEMP:?}/lab-factory-preflight-run1-raw"
PROFILE_ID="servicetracer-demo-api"
PROFILE_VERSION="1.0.0"
ENVIRONMENT="test"
LOCATION="westus2"
TTL_HOURS="8"
RESOURCE_GROUP="rg-st-demo-api-test-westus2"
VM_SIZE="Standard_F1als_v7"
COST_CEILING_CAD="5.00"
SOURCE_REPOSITORY="https://github.com/anthonyedgar30000/azure-iac-msp-lab.git"
ALLOWED_ORIGIN="https://anthonyedgar30000.github.io"
DEPENDENCY_RESOURCE_GROUP="rg-servicetracer-dev-westus2"
DEPENDENCY_PUBLIC_IP="pip-remote-access-mst-dev"
CURRENT_STAGE="initialization"

mkdir -p "$EVIDENCE_DIR" "$RAW_DIR"

write_terminal_summary() {
  local exit_code="$1"
  local passed=false
  if [[ "$exit_code" -eq 0 ]]; then
    passed=true
  fi
  jq -n \
    --arg stage "$CURRENT_STAGE" \
    --arg reviewed_commit "${REVIEWED_COMMIT:-not-set}" \
    --arg profile "${PROFILE_ID}@${PROFILE_VERSION}" \
    --arg environment "$ENVIRONMENT" \
    --arg location "$LOCATION" \
    --arg resource_group "$RESOURCE_GROUP" \
    --argjson preflight_passed "$passed" \
    '{
      schema_version:"lab-factory.preflight-run1-summary.v1",
      stage:$stage,
      reviewed_commit:$reviewed_commit,
      profile:$profile,
      environment:$environment,
      location:$location,
      resource_group:$resource_group,
      preflight_passed:$preflight_passed,
      azure_mutation_performed:false,
      deployment_authorized:false,
      provider_registration_performed:false,
      rbac_mutation_performed:false,
      model_call_performed:false,
      retry_authorized:false,
      rollback_authorized:false,
      cleanup_authorized:false,
      next_gate:(if $preflight_passed then
        "independent evidence review and fresh explicit deployment authority"
      else
        "terminal reconciliation; no retry authority"
      end)
    }' > "$EVIDENCE_DIR/preflight-summary.json"
}
trap 'status=$?; write_terminal_summary "$status"; exit "$status"' EXIT

CURRENT_STAGE="repository-and-authority-validation"
[[ "${GITHUB_RUN_ATTEMPT:-}" == "1" ]]
[[ "${REVIEWED_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]]
[[ "$(git -C "$REPOSITORY_ROOT" rev-parse HEAD)" == "$REVIEWED_COMMIT" ]]
[[ -f "$REQUEST_PATH" ]]
jq -e '
  .schema_version == "project.lab-factory-preflight-authorization.v1"
  and .attempt_id == "lab-factory-preflight-run1"
  and .status == "active_one_attempt"
  and .attempt_limit == 1
  and .attempts_observed == 0
  and .profile.id == "servicetracer-demo-api"
  and .profile.version == "1.0.0"
  and .profile.environment == "test"
  and .profile.location == "westus2"
  and .profile.resource_group == "rg-st-demo-api-test-westus2"
  and .profile.vm_size == "Standard_F1als_v7"
  and .profile.cost_ceiling_CAD == 5
  and .authority.merge_triggered_preflight_authorized == true
  and .authority.azure_authentication_authorized == true
  and .authority.azure_read_only_queries_authorized == true
  and .authority.arm_validation_authorized == true
  and .authority.arm_what_if_authorized == true
  and .authority.provider_registration_authorized == false
  and .authority.azure_mutation_authorized == false
  and .authority.deployment_authorized == false
  and .authority.rbac_mutation_authorized == false
  and .authority.model_call_authorized == false
  and .authority.automatic_retry_authorized == false
  and .authority.manual_rerun_authorized == false
  and .authority.rollback_authorized == false
  and .authority.cleanup_authorized == false
' "$REQUEST_PATH" > /dev/null
cp "$REQUEST_PATH" "$EVIDENCE_DIR/request.json"

test -f "$REPOSITORY_ROOT/workloads/servicetracer-demo-api/infra/main.bicep"
test -f "$REPOSITORY_ROOT/workloads/servicetracer-demo-api/scripts/install.sh"
test -f "$REPOSITORY_ROOT/lab_factory/catalog.json"

CURRENT_STAGE="azure-context"
account_json="$(az account show --output json --only-show-errors)"
subscription_id="$(jq -r '.id' <<<"$account_json")"
tenant_id="$(jq -r '.tenantId' <<<"$account_json")"
subscription_name="$(jq -r '.name' <<<"$account_json")"
subscription_state="$(jq -r '.state' <<<"$account_json")"
[[ "$subscription_id" == "${AZURE_SUBSCRIPTION_ID:?}" ]]
[[ "$subscription_name" == "Azure for Students" ]]
[[ "$subscription_state" == "Enabled" ]]

subscription_hash="$(printf '%s' "$subscription_id" | sha256sum | awk '{print $1}')"
tenant_hash="$(printf '%s' "$tenant_id" | sha256sum | awk '{print $1}')"
DNS_LABEL="stlf-${subscription_hash:0:10}-test"

jq -n \
  --arg subscription_name "$subscription_name" \
  --arg subscription_state "$subscription_state" \
  --arg subscription_sha256 "$subscription_hash" \
  --arg tenant_sha256 "$tenant_hash" \
  '{
    schema_version:"lab-factory.azure-context.v1",
    subscription_name:$subscription_name,
    subscription_state:$subscription_state,
    subscription_id_sha256:$subscription_sha256,
    tenant_id_sha256:$tenant_sha256,
    raw_identifiers_persisted:false
  }' > "$EVIDENCE_DIR/azure-context.json"

CURRENT_STAGE="provider-observation"
for namespace in Microsoft.Resources Microsoft.Compute Microsoft.Network; do
  safe_name="${namespace//./-}"
  az provider show \
    --namespace "$namespace" \
    --query '{namespace:namespace,registrationState:registrationState}' \
    --output json \
    > "$EVIDENCE_DIR/provider-${safe_name}.json"
  [[ "$(jq -r '.registrationState' "$EVIDENCE_DIR/provider-${safe_name}.json")" == "Registered" ]]
done

CURRENT_STAGE="dependency-observation"
dependency_ip="$(az network public-ip show \
  --subscription "$subscription_id" \
  --resource-group "$DEPENDENCY_RESOURCE_GROUP" \
  --name "$DEPENDENCY_PUBLIC_IP" \
  --query ipAddress \
  --output tsv)"
[[ "$dependency_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
BACKEND_TRANSACTION_URL="https://${dependency_ip}/transaction"

dependency_health_status="$(curl --silent --show-error --location \
  --output /dev/null \
  --write-out '%{http_code}' \
  --max-time 20 \
  'https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/health' || true)"
[[ "$dependency_health_status" == "200" ]]
jq -n \
  --arg resource_group "$DEPENDENCY_RESOURCE_GROUP" \
  --arg public_ip_name "$DEPENDENCY_PUBLIC_IP" \
  --arg health_url "https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/health" \
  --arg health_status "$dependency_health_status" \
  '{
    schema_version:"lab-factory.dependency-observation.v1",
    resource_group:$resource_group,
    public_ip_name:$public_ip_name,
    public_ip_observed:true,
    raw_ip_persisted:false,
    health_url:$health_url,
    health_status:($health_status|tonumber),
    dependency_ready:($health_status=="200")
  }' > "$EVIDENCE_DIR/dependency-observation.json"

CURRENT_STAGE="request-preparation"
ssh-keygen -q -t ed25519 -N '' -C 'lab-factory-preflight-ephemeral' -f "$RAW_DIR/preflight_key"
ADMIN_SSH_PUBLIC_KEY="$(cat "$RAW_DIR/preflight_key.pub")"
rm -f "$RAW_DIR/preflight_key"
INSTALLER_URI="https://raw.githubusercontent.com/anthonyedgar30000/azure-iac-msp-lab/${REVIEWED_COMMIT}/workloads/servicetracer-demo-api/scripts/install.sh"

python -m lab_factory prepare \
  --repository-root "$REPOSITORY_ROOT" \
  --profile "$PROFILE_ID" \
  --environment "$ENVIRONMENT" \
  --location "$LOCATION" \
  --ttl-hours "$TTL_HOURS" \
  --request-id "lab-factory-preflight-run1" \
  --parameter "dnsLabel=${DNS_LABEL}" \
  --parameter "allowedOrigin=${ALLOWED_ORIGIN}" \
  --parameter "backendTransactionUrl=${BACKEND_TRANSACTION_URL}" \
  --parameter "adminSshPublicKey=${ADMIN_SSH_PUBLIC_KEY}" \
  --parameter "sourceRepository=${SOURCE_REPOSITORY}" \
  --parameter "sourceRef=${REVIEWED_COMMIT}" \
  --parameter "installerUri=${INSTALLER_URI}" \
  > "$EVIDENCE_DIR/prepared-plan.json"

jq -e '
  .next_gate == "preflight_required"
  and .gates.ready_for_preflight == true
  and .deployment.resource_group == "rg-st-demo-api-test-westus2"
  and .execution.azure_queries_performed == false
  and .execution.azure_mutations_performed == false
  and .execution.deployment_authorized == false
  and .execution.cleanup_authorized == false
' "$EVIDENCE_DIR/prepared-plan.json" > /dev/null

CURRENT_STAGE="resource-group-and-dns-observation"
resource_group_exists="$(az group exists \
  --subscription "$subscription_id" \
  --name "$RESOURCE_GROUP" \
  --output tsv)"
[[ "$resource_group_exists" == "false" ]]
jq -n \
  --arg resource_group "$RESOURCE_GROUP" \
  --arg exists "$resource_group_exists" \
  '{
    schema_version:"lab-factory.resource-group-state.v1",
    resource_group:$resource_group,
    exists:($exists=="true"),
    required_state:"absent",
    collision_free:($exists=="false")
  }' > "$EVIDENCE_DIR/resource-group-state.json"

az network public-ip check-dns-name \
  --subscription "$subscription_id" \
  --location "$LOCATION" \
  --domain-name-label "$DNS_LABEL" \
  --output json \
  > "$EVIDENCE_DIR/dns-availability.json"
[[ "$(jq -r '.available' "$EVIDENCE_DIR/dns-availability.json")" == "true" ]]

CURRENT_STAGE="sku-quota-and-cost-observation"
az vm list-skus \
  --subscription "$subscription_id" \
  --location "$LOCATION" \
  --size "$VM_SIZE" \
  --all \
  --output json \
  > "$EVIDENCE_DIR/vm-sku-inventory.json"
az vm list-usage \
  --subscription "$subscription_id" \
  --location "$LOCATION" \
  --output json \
  > "$EVIDENCE_DIR/compute-usage.json"
az network list-usages \
  --subscription "$subscription_id" \
  --location "$LOCATION" \
  --output json \
  > "$EVIDENCE_DIR/network-usage.json"

VM_SIZE="$VM_SIZE" LOCATION="$LOCATION" python - <<'PY' > "$EVIDENCE_DIR/retail-prices.json"
import json
import os
import urllib.parse
import urllib.request

filters = (
    f"armRegionName eq '{os.environ['LOCATION']}' "
    f"and armSkuName eq '{os.environ['VM_SIZE']}' "
    "and serviceName eq 'Virtual Machines' "
    "and priceType eq 'Consumption'"
)
query = urllib.parse.urlencode({"currencyCode": "CAD", "$filter": filters})
url = f"https://prices.azure.com/api/retail/prices?{query}"
request = urllib.request.Request(url, headers={"User-Agent": "azure-iac-msp-lab-preflight/1.0"})
with urllib.request.urlopen(request, timeout=30) as response:
    payload = json.load(response)
json.dump(payload, fp=os.sys.stdout, indent=2)
os.sys.stdout.write("\n")
PY

python scripts/assess_lab_factory_preflight.py \
  --sku-inventory "$EVIDENCE_DIR/vm-sku-inventory.json" \
  --compute-usage "$EVIDENCE_DIR/compute-usage.json" \
  --network-usage "$EVIDENCE_DIR/network-usage.json" \
  --retail-prices "$EVIDENCE_DIR/retail-prices.json" \
  --vm-size "$VM_SIZE" \
  --ttl-hours "$TTL_HOURS" \
  --cost-ceiling-cad "$COST_CEILING_CAD" \
  --output "$EVIDENCE_DIR/capacity-and-cost-assessment.json"

CURRENT_STAGE="arm-validation-and-what-if"
parameters=(
  prefix="mst"
  environment="$ENVIRONMENT"
  location="$LOCATION"
  dnsLabel="$DNS_LABEL"
  allowedOrigin="$ALLOWED_ORIGIN"
  backendTransactionUrl="$BACKEND_TRANSACTION_URL"
  vmSize="$VM_SIZE"
  adminUsername="azureadmin"
  adminSshPublicKey="$ADMIN_SSH_PUBLIC_KEY"
  sourceRepository="$SOURCE_REPOSITORY"
  sourceRef="$REVIEWED_COMMIT"
  installerUri="$INSTALLER_URI"
)

az deployment sub validate \
  --subscription "$subscription_id" \
  --location "$LOCATION" \
  --template-file workloads/servicetracer-demo-api/infra/main.bicep \
  --parameters "${parameters[@]}" \
  --output json \
  > "$RAW_DIR/arm-validation.json"

az deployment sub what-if \
  --subscription "$subscription_id" \
  --location "$LOCATION" \
  --template-file workloads/servicetracer-demo-api/infra/main.bicep \
  --parameters "${parameters[@]}" \
  --result-format FullResourcePayloads \
  --no-pretty-print \
  --output json \
  > "$RAW_DIR/arm-what-if.json"

SUBSCRIPTION_ID="$subscription_id" TENANT_ID="$tenant_id" python - <<'PY'
from pathlib import Path
import os

raw_dir = Path(os.environ["RUNNER_TEMP"]) / "lab-factory-preflight-run1-raw"
evidence_dir = Path(os.environ["RUNNER_TEMP"]) / "lab-factory-preflight-run1"
replacements = {
    os.environ["SUBSCRIPTION_ID"]: "<subscription-id>",
    os.environ["TENANT_ID"]: "<tenant-id>",
}
for name in ("arm-validation.json", "arm-what-if.json"):
    text = (raw_dir / name).read_text(encoding="utf-8")
    for source, target in replacements.items():
        text = text.replace(source, target)
    (evidence_dir / name).write_text(text, encoding="utf-8")
PY

python scripts/assert_lab_factory_preflight_what_if.py \
  --input "$EVIDENCE_DIR/arm-what-if.json" \
  --resource-group "$RESOURCE_GROUP" \
  --output "$EVIDENCE_DIR/what-if-assessment.json"

CURRENT_STAGE="preflight-complete"
jq -n \
  --arg reviewed_commit "$REVIEWED_COMMIT" \
  --arg profile "${PROFILE_ID}@${PROFILE_VERSION}" \
  --arg environment "$ENVIRONMENT" \
  --arg location "$LOCATION" \
  --arg resource_group "$RESOURCE_GROUP" \
  --arg dns_label "$DNS_LABEL" \
  --arg cost_ceiling_CAD "$COST_CEILING_CAD" \
  '{
    schema_version:"lab-factory.preflight-run1-decision.v1",
    reviewed_commit:$reviewed_commit,
    profile:$profile,
    environment:$environment,
    location:$location,
    resource_group:$resource_group,
    dns_label:$dns_label,
    cost_ceiling_CAD:($cost_ceiling_CAD|tonumber),
    exact_subscription_selected:true,
    subscription_enabled:true,
    providers_registered:true,
    dependency_health_verified:true,
    resource_group_collision_free:true,
    dns_label_available:true,
    location_and_sku_available:true,
    quota_sufficient:true,
    template_validation_passed:true,
    what_if_passed:true,
    cost_ceiling_accepted:true,
    preflight_passed:true,
    azure_mutation_performed:false,
    deployment_authorized:false,
    next_gate:"independent evidence review and fresh explicit deployment authority"
  }' > "$EVIDENCE_DIR/preflight-decision.json"
