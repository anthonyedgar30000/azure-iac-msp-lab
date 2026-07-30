#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

readonly attempt_id="servicetracer-lab-factory-preflight-run1"
readonly expected_subscription_name="Azure for Students"
readonly profile_id="servicetracer-demo-api"
readonly profile_version="1.0.0"
readonly environment_name="dev"
readonly location_name="westus2"
readonly ttl_hours="8"
readonly target_resource_group="rg-st-demo-api-dev-westus2"
readonly vm_size="Standard_F1als_v7"
readonly deployment_name="servicetracer-lab-factory-preflight-run1"
readonly template_path="workloads/servicetracer-demo-api/infra/main.bicep"
readonly cost_ceiling_cad="5.00"
readonly overhead_contingency_cad="2.00"
readonly evidence_root="${HOME}/clouddrive/servicetracer-lab-factory-preflight-run1"
readonly evidence_dir="${evidence_root}/evidence"
readonly temp_dir="${evidence_root}/private-work"
readonly consumption_marker="${HOME}/.${attempt_id}.consumed"
readonly summary_path="${evidence_dir}/preflight-summary.json"
readonly manifest_path="${evidence_dir}/artifact-manifest.sha256"

consumed=false

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

need_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command is unavailable: $1"
}

fingerprint() {
  printf '%s' "$1" | sha256sum | awk '{print "sha256:" $1}'
}

write_failure_summary() {
  local exit_status="$1"
  local failed_command="$2"
  mkdir -p "$evidence_dir"
  jq -n \
    --arg attempt_id "$attempt_id" \
    --arg observed_at_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg failed_command "$failed_command" \
    --argjson exit_status "$exit_status" \
    '{
      schema_version:"lab-factory.preflight-receipt.v1",
      attempt_id:$attempt_id,
      observed_at_utc:$observed_at_utc,
      preflight_status:"observation_failed",
      failure:{exit_status:$exit_status,failed_command:$failed_command,stderr_persisted:false},
      authorization_consumed:true,
      azure_authentication_performed:true,
      arm_validation_performed:false,
      arm_what_if_performed:false,
      azure_mutations_authorized:false,
      azure_mutations_performed:false,
      deployment_authorized:false,
      deployment_performed:false,
      secrets_returned:false,
      retry_authorized:false
    }' > "$summary_path"
  find "$evidence_dir" -maxdepth 1 -type f ! -name artifact-manifest.sha256 -print0 \
    | sort -z \
    | xargs -0 -r sha256sum \
    > "$manifest_path" || true
}

on_error() {
  local exit_status=$?
  local failed_command=${BASH_COMMAND:-unknown}
  trap - ERR
  if [[ "$consumed" == true ]]; then
    write_failure_summary "$exit_status" "$failed_command" || true
    printf 'Attempt consumed. Do not rerun without new authority.\n' >&2
    printf 'Partial evidence: %s\n' "$evidence_dir" >&2
  fi
  exit "$exit_status"
}
trap on_error ERR

cleanup_private_material() {
  rm -rf "$temp_dir" 2>/dev/null || true
  unset AZURE_LAB_FACTORY_ALLOWED_SUBSCRIPTION_ID 2>/dev/null || true
}
trap cleanup_private_material EXIT

for command_name in az jq python3 git ssh-keygen sha256sum curl find sort xargs awk grep sed; do
  need_command "$command_name"
done

: "${AZURE_LAB_FACTORY_RUN1_SUBSCRIPTION_ID:?Set the exact Azure for Students subscription UUID.}"
: "${AZURE_LAB_FACTORY_RUN1_REVIEWED_COMMIT:?Set the exact reviewed merge commit.}"
: "${AZURE_LAB_FACTORY_RUN1_CONFIRMATION:?Set the exact run-1 confirmation string.}"

[[ "$AZURE_LAB_FACTORY_RUN1_SUBSCRIPTION_ID" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]] \
  || fail "subscription ID must be an exact UUID"
[[ "$AZURE_LAB_FACTORY_RUN1_REVIEWED_COMMIT" =~ ^[0-9a-f]{40}$ ]] \
  || fail "reviewed commit must be a lowercase 40-character SHA"

readonly expected_confirmation="PREFLIGHT-SERVICETRACER-RUN1:${expected_subscription_name}:${target_resource_group}:${location_name}:${ttl_hours}h:CAD${cost_ceiling_cad}:${AZURE_LAB_FACTORY_RUN1_REVIEWED_COMMIT}"
[[ "$AZURE_LAB_FACTORY_RUN1_CONFIRMATION" == "$expected_confirmation" ]] \
  || fail "confirmation must exactly equal: $expected_confirmation"

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" \
  || fail "run from inside the azure-iac-msp-lab repository"
cd "$repo_root"
[[ "$(git rev-parse HEAD)" == "$AZURE_LAB_FACTORY_RUN1_REVIEWED_COMMIT" ]] \
  || fail "repository HEAD differs from the reviewed commit"
[[ -z "$(git status --porcelain=v1 --untracked-files=normal)" ]] \
  || fail "repository working tree must be clean"
[[ -f "$template_path" ]] || fail "reviewed Bicep template is missing"
[[ ! -e "$consumption_marker" ]] || fail "the one-attempt authorization is already consumed"
[[ ! -e "$evidence_root" ]] || fail "evidence directory already exists; do not overwrite prior evidence"

mkdir -p "$evidence_dir" "$temp_dir"
umask 077

# Local-only preparation happens before authority consumption.
az bicep build \
  --file "$template_path" \
  --outfile "$temp_dir/servicetracer-template.json" \
  --only-show-errors
sha256sum "$template_path" > "$evidence_dir/template-source.sha256"
sha256sum "$temp_dir/servicetracer-template.json" > "$evidence_dir/template-compiled.sha256"

ssh-keygen -q -t ed25519 -N '' -f "$temp_dir/preflight-key" -C "$attempt_id"
dns_label="mst-st-${AZURE_LAB_FACTORY_RUN1_REVIEWED_COMMIT:0:12}"
source_repository="https://github.com/anthonyedgar30000/azure-iac-msp-lab.git"
source_ref="$AZURE_LAB_FACTORY_RUN1_REVIEWED_COMMIT"
installer_uri="https://raw.githubusercontent.com/anthonyedgar30000/azure-iac-msp-lab/${source_ref}/workloads/servicetracer-demo-api/scripts/install.sh"

jq -n \
  --arg environment "$environment_name" \
  --arg location "$location_name" \
  --arg dnsLabel "$dns_label" \
  --arg allowedOrigin "https://servicetracer-preflight.invalid" \
  --arg backendTransactionUrl "https://servicetracer-backend-preflight.invalid/api/demo/run" \
  --arg adminSshPublicKey "$(cat "$temp_dir/preflight-key.pub")" \
  --arg sourceRepository "$source_repository" \
  --arg sourceRef "$source_ref" \
  --arg installerUri "$installer_uri" \
  '{
    environment:{value:$environment},
    location:{value:$location},
    dnsLabel:{value:$dnsLabel},
    allowedOrigin:{value:$allowedOrigin},
    backendTransactionUrl:{value:$backendTransactionUrl},
    adminSshPublicKey:{value:$adminSshPublicKey},
    sourceRepository:{value:$sourceRepository},
    sourceRef:{value:$sourceRef},
    installerUri:{value:$installerUri}
  }' > "$temp_dir/parameters.json"

jq -n \
  --arg attempt_id "$attempt_id" \
  --arg reviewed_commit "$AZURE_LAB_FACTORY_RUN1_REVIEWED_COMMIT" \
  --arg profile "${profile_id}@${profile_version}" \
  --arg environment "$environment_name" \
  --arg location "$location_name" \
  --arg resource_group "$target_resource_group" \
  --arg vm_size "$vm_size" \
  --arg ttl_hours "$ttl_hours" \
  --arg cost_ceiling_cad "$cost_ceiling_cad" \
  --arg dns_label_fingerprint "$(fingerprint "$dns_label")" \
  '{
    attempt_id:$attempt_id,
    reviewed_commit:$reviewed_commit,
    profile:$profile,
    environment:$environment,
    location:$location,
    resource_group:$resource_group,
    vm_size:$vm_size,
    ttl_hours:($ttl_hours|tonumber),
    cost_ceiling:{currency:"CAD",amount:($cost_ceiling_cad|tonumber)},
    dns_label_fingerprint:$dns_label_fingerprint,
    parameter_names:[
      "adminSshPublicKey","allowedOrigin","backendTransactionUrl","dnsLabel",
      "environment","installerUri","location","sourceRef","sourceRepository"
    ],
    parameter_values_persisted:false,
    production_application_values_verified:false,
    deployment_authorized:false
  }' > "$evidence_dir/request.json"

# Consume immediately before the first authenticated Azure observation.
(
  set -o noclobber
  printf '%s\n' \
    "attempt_id=${attempt_id}" \
    "consumed_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    "reviewed_commit=${AZURE_LAB_FACTORY_RUN1_REVIEWED_COMMIT}" \
    "profile=${profile_id}@${profile_version}" \
    "resource_group=${target_resource_group}" \
    > "$consumption_marker"
) 2>/dev/null || fail "could not atomically claim the one-attempt authorization"
consumed=true

az account set --subscription "$AZURE_LAB_FACTORY_RUN1_SUBSCRIPTION_ID"
account_json="$(az account show --output json --only-show-errors)"
subscription_id="$(jq -r '.id' <<<"$account_json")"
subscription_name="$(jq -r '.name' <<<"$account_json")"
subscription_state="$(jq -r '.state' <<<"$account_json")"
tenant_id="$(jq -r '.tenantId' <<<"$account_json")"
principal_type="$(jq -r '.user.type // "unknown"' <<<"$account_json")"
[[ "${subscription_id,,}" == "${AZURE_LAB_FACTORY_RUN1_SUBSCRIPTION_ID,,}" ]] \
  || fail "active Azure subscription differs from the explicit run scope"
[[ "$subscription_name" == "$expected_subscription_name" ]] \
  || fail "active subscription name is not Azure for Students"
[[ "${subscription_state,,}" == "enabled" ]] || fail "active subscription is not enabled"

jq -n \
  --arg observed_at_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg subscription_name "$subscription_name" \
  --arg subscription_fingerprint "$(fingerprint "$subscription_id")" \
  --arg tenant_fingerprint "$(fingerprint "$tenant_id")" \
  --arg principal_type "$principal_type" \
  '{
    observation_status:"observed",
    observed_at_utc:$observed_at_utc,
    subscription_name:$subscription_name,
    subscription_state:"Enabled",
    subscription_fingerprint:$subscription_fingerprint,
    tenant_fingerprint:$tenant_fingerprint,
    principal_type:$principal_type,
    raw_identifiers_persisted:false
  }' > "$evidence_dir/account-context.json"

: > "$temp_dir/provider-states.jsonl"
for provider in Microsoft.Resources Microsoft.Compute Microsoft.Network Microsoft.ManagedIdentity; do
  set +e
  provider_json="$(az provider show --subscription "$subscription_id" --namespace "$provider" --output json --only-show-errors 2>/dev/null)"
  provider_exit=$?
  set -e
  if (( provider_exit == 0 )); then
    jq -n \
      --arg namespace "$provider" \
      --arg registration_state "$(jq -r '.registrationState' <<<"$provider_json")" \
      '{namespace:$namespace,observation_status:"observed",registration_state:$registration_state}' \
      >> "$temp_dir/provider-states.jsonl"
  else
    jq -n \
      --arg namespace "$provider" \
      --argjson exit_status "$provider_exit" \
      '{namespace:$namespace,observation_status:"observation_failed",registration_state:null,exit_status:$exit_status,stderr_persisted:false}' \
      >> "$temp_dir/provider-states.jsonl"
  fi
done
jq -s '.' "$temp_dir/provider-states.jsonl" > "$evidence_dir/provider-states.json"

az vm list-skus \
  --subscription "$subscription_id" \
  --location "$location_name" \
  --resource-type virtualMachines \
  --all \
  --query "[?name=='${vm_size}'] | [0]" \
  --output json \
  --only-show-errors \
  > "$temp_dir/vm-sku.raw.json"

python3 - "$temp_dir/vm-sku.raw.json" "$evidence_dir/vm-sku.json" "$location_name" <<'PY'
import json, sys
from pathlib import Path
source, target, location = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3].lower()
value = json.loads(source.read_text())
if value is None:
    summary = {"observation_status":"observed","sku_found":False,"available_for_subscription":False,"family":None,"vcpus":None,"restrictions":[]}
else:
    capabilities = {str(item.get("name")): str(item.get("value")) for item in value.get("capabilities", [])}
    restrictions = []
    relevant = []
    for item in value.get("restrictions", []):
        info = item.get("restrictionInfo") or {}
        locations = [str(x).lower() for x in (info.get("locations") or [])]
        values = [str(x).lower() for x in (item.get("values") or [])]
        record = {"type":item.get("type"),"reason_code":item.get("reasonCode"),"locations":locations,"values":values}
        restrictions.append(record)
        if str(item.get("type", "")).lower() == "location" and (not locations and not values or location in locations or location in values):
            relevant.append(record)
    vcpus_text = capabilities.get("vCPUs") or capabilities.get("vCPUsAvailable")
    try:
        vcpus = int(float(vcpus_text))
    except (TypeError, ValueError):
        vcpus = None
    summary = {
        "observation_status":"observed",
        "sku_found":True,
        "name":value.get("name"),
        "resource_type":value.get("resourceType"),
        "family":value.get("family"),
        "vcpus":vcpus,
        "available_for_subscription":not relevant,
        "relevant_restrictions":relevant,
        "all_restrictions":restrictions,
    }
target.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
PY

az vm list-usage \
  --subscription "$subscription_id" \
  --location "$location_name" \
  --output json \
  --only-show-errors \
  > "$temp_dir/vm-usage.raw.json"

python3 - "$temp_dir/vm-usage.raw.json" "$evidence_dir/vm-sku.json" "$evidence_dir/quota-summary.json" <<'PY'
import json, sys
from pathlib import Path
usage = json.loads(Path(sys.argv[1]).read_text())
sku = json.loads(Path(sys.argv[2]).read_text())
family = str(sku.get("family") or "")
required = sku.get("vcpus")
entries = []
for item in usage:
    name = item.get("name") or {}
    value = str(name.get("value") or "")
    localized = str(name.get("localizedValue") or "")
    if value.lower() == "cores" or (family and value.lower() == family.lower()):
        entries.append({"name":value,"localized_name":localized,"current_value":item.get("currentValue"),"limit":item.get("limit")})
regional = next((item for item in entries if item["name"].lower() == "cores"), None)
family_entry = next((item for item in entries if family and item["name"].lower() == family.lower()), None)
def sufficient(item):
    return bool(item is not None and isinstance(required, int) and item.get("limit") is not None and item.get("current_value") is not None and item["limit"] - item["current_value"] >= required)
summary = {
    "observation_status":"observed",
    "required_vcpus":required,
    "sku_family":family or None,
    "regional_quota":regional,
    "family_quota":family_entry,
    "regional_quota_sufficient":sufficient(regional),
    "family_quota_sufficient":sufficient(family_entry),
}
summary["quota_sufficient"] = summary["regional_quota_sufficient"] and summary["family_quota_sufficient"]
Path(sys.argv[3]).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
PY

group_stderr="$temp_dir/group.stderr"
set +e
az group show \
  --subscription "$subscription_id" \
  --name "$target_resource_group" \
  --output json \
  --only-show-errors \
  > "$temp_dir/group.raw.json" \
  2> "$group_stderr"
group_exit=$?
set -e
if (( group_exit == 0 )); then
  jq '{observation_status:"observed",name:.name,location:.location,provisioning_state:.properties.provisioningState}' \
    "$temp_dir/group.raw.json" > "$evidence_dir/target-resource-group.json"
  az resource list \
    --subscription "$subscription_id" \
    --resource-group "$target_resource_group" \
    --query '[].{name:name,type:type,location:location}' \
    --output json \
    --only-show-errors \
    > "$evidence_dir/existing-resource-summary.json"
elif grep -Eqi 'ResourceGroupNotFound|could not be found' "$group_stderr"; then
  jq -n --arg name "$target_resource_group" \
    '{observation_status:"not_present",name:$name,location:null,provisioning_state:null}' \
    > "$evidence_dir/target-resource-group.json"
  jq -n '{observation_status:"not_applicable",resources:[]}' \
    > "$evidence_dir/existing-resource-summary.json"
else
  jq -n --arg name "$target_resource_group" --argjson exit_status "$group_exit" \
    '{observation_status:"observation_failed",name:$name,exit_status:$exit_status,stderr_persisted:false}' \
    > "$evidence_dir/target-resource-group.json"
  jq -n '{observation_status:"not_observed",resources:null}' \
    > "$evidence_dir/existing-resource-summary.json"
fi

retail_filter="armRegionName eq '${location_name}' and armSkuName eq '${vm_size}' and priceType eq 'Consumption'"
curl --fail --silent --show-error --get \
  'https://prices.azure.com/api/retail/prices' \
  --data-urlencode "currencyCode='CAD'" \
  --data-urlencode "\$filter=${retail_filter}" \
  > "$temp_dir/retail-price.raw.json"

python3 - "$temp_dir/retail-price.raw.json" "$evidence_dir/retail-price-summary.json" "$ttl_hours" "$overhead_contingency_cad" "$cost_ceiling_cad" <<'PY'
import json, sys
from decimal import Decimal
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
items = []
for item in payload.get("Items", []):
    meter = str(item.get("meterName") or "")
    product = str(item.get("productName") or "")
    if item.get("currencyCode") != "CAD" or item.get("type") != "Consumption":
        continue
    if "spot" in meter.lower() or "low priority" in meter.lower() or "windows" in product.lower():
        continue
    if not item.get("isPrimaryMeterRegion", False):
        continue
    items.append(item)
if items:
    chosen = min(items, key=lambda item: Decimal(str(item["retailPrice"])))
    hourly = Decimal(str(chosen["retailPrice"]))
    hours = Decimal(sys.argv[3])
    contingency = Decimal(sys.argv[4])
    ceiling = Decimal(sys.argv[5])
    estimate = hourly * hours + contingency
    summary = {
        "observation_status":"observed",
        "currency":"CAD",
        "arm_sku_name":chosen.get("armSkuName"),
        "meter_name":chosen.get("meterName"),
        "product_name":chosen.get("productName"),
        "unit_of_measure":chosen.get("unitOfMeasure"),
        "hourly_retail_price":float(hourly),
        "ttl_hours":int(hours),
        "storage_network_contingency_cad":float(contingency),
        "planning_estimate_cad":float(estimate),
        "planning_ceiling_cad":float(ceiling),
        "within_ceiling":estimate <= ceiling,
        "estimate_complete":False,
        "estimate_is_actual_cost":False,
    }
else:
    summary = {
        "observation_status":"not_observed",
        "currency":"CAD",
        "hourly_retail_price":None,
        "planning_estimate_cad":None,
        "planning_ceiling_cad":float(Decimal(sys.argv[5])),
        "within_ceiling":False,
        "estimate_complete":False,
        "estimate_is_actual_cost":False,
    }
Path(sys.argv[2]).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
PY

cost_body='{"type":"ActualCost","timeframe":"MonthToDate","dataset":{"granularity":"None","aggregation":{"totalCost":{"name":"Cost","function":"Sum"}}}}'
set +e
az rest \
  --method post \
  --url "https://management.azure.com/subscriptions/${subscription_id}/providers/Microsoft.CostManagement/query?api-version=2025-03-01" \
  --body "$cost_body" \
  --headers Content-Type=application/json \
  --output json \
  > "$temp_dir/cost-context.raw.json" \
  2> "$temp_dir/cost-context.stderr"
cost_exit=$?
set -e
if (( cost_exit == 0 )); then
  python3 - "$temp_dir/cost-context.raw.json" "$evidence_dir/cost-management-context.json" <<'PY'
import json, sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
properties = payload.get("properties") or {}
columns = [item.get("name") for item in properties.get("columns", [])]
rows = properties.get("rows") or []
record = dict(zip(columns, rows[0])) if rows else {}
summary = {
    "observation_status":"observed",
    "timeframe":"MonthToDate",
    "total_cost":record.get("Cost"),
    "currency":record.get("Currency"),
    "actual_cost_scope":"subscription_month_to_date_not_incremental_lab_cost",
}
Path(sys.argv[2]).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
PY
else
  jq -n --argjson exit_status "$cost_exit" \
    '{observation_status:"not_observed",reason:"query_failed_or_not_permitted",exit_status:$exit_status,stderr_persisted:false,total_cost:null,currency:null}' \
    > "$evidence_dir/cost-management-context.json"
fi

set +e
az deployment sub validate \
  --subscription "$subscription_id" \
  --name "$deployment_name" \
  --location "$location_name" \
  --template-file "$template_path" \
  --parameters @"$temp_dir/parameters.json" \
  --output json \
  --only-show-errors \
  > "$temp_dir/template-validation.raw.json" \
  2> "$temp_dir/template-validation.stderr"
validation_exit=$?
set -e
if (( validation_exit == 0 )); then
  jq -n '{observation_status:"observed",validation_succeeded:true,parameter_values_persisted:false,azure_mutations_performed:false}' \
    > "$evidence_dir/template-validation-summary.json"
else
  jq -n --argjson exit_status "$validation_exit" \
    '{observation_status:"observed",validation_succeeded:false,exit_status:$exit_status,stderr_persisted:false,parameter_values_persisted:false,azure_mutations_performed:false}' \
    > "$evidence_dir/template-validation-summary.json"
fi

if (( validation_exit == 0 )); then
  set +e
  az deployment sub what-if \
    --subscription "$subscription_id" \
    --name "$deployment_name" \
    --location "$location_name" \
    --template-file "$template_path" \
    --parameters @"$temp_dir/parameters.json" \
    --result-format ResourceIdOnly \
    --no-pretty-print \
    --output json \
    --only-show-errors \
    > "$temp_dir/what-if.raw.json" \
    2> "$temp_dir/what-if.stderr"
  what_if_exit=$?
  set -e
else
  what_if_exit=125
fi

if (( what_if_exit == 0 )); then
  python3 - "$temp_dir/what-if.raw.json" "$evidence_dir/what-if-summary.json" "$subscription_id" "$target_resource_group" <<'PY'
import json, re, sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
subscription_id, resource_group = sys.argv[3], sys.argv[4]
changes = payload.get("changes") or (payload.get("properties") or {}).get("changes") or []
expected_types = {
    "microsoft.resources/resourcegroups",
    "microsoft.network/networksecuritygroups",
    "microsoft.network/virtualnetworks",
    "microsoft.network/publicipaddresses",
    "microsoft.network/networkinterfaces",
    "microsoft.compute/virtualmachines",
    "microsoft.compute/virtualmachines/extensions",
}
required_types = set(expected_types)
records, seen_types, unexpected_types, unexpected_change_types, outside_scope = [], set(), [], [], []
rg_prefix = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}".lower()

def resource_type(resource_id: str) -> str:
    parts = [part for part in resource_id.strip("/").split("/") if part]
    lower = [part.lower() for part in parts]
    if "providers" not in lower:
        return "microsoft.resources/resourcegroups" if "resourcegroups" in lower else "unknown"
    index = lower.index("providers")
    provider = parts[index + 1]
    remainder = parts[index + 2:]
    type_segments = remainder[0::2]
    return "/".join([provider, *type_segments]).lower()

for change in changes:
    change_type = str(change.get("changeType") or change.get("change_type") or "unknown")
    resource_id = str(change.get("resourceId") or change.get("resource_id") or "")
    kind = resource_type(resource_id)
    seen_types.add(kind)
    if kind not in expected_types:
        unexpected_types.append(kind)
    if change_type not in {"Create", "NoChange", "Ignore"}:
        unexpected_change_types.append(change_type)
    lower_id = resource_id.lower()
    if kind == "microsoft.resources/resourcegroups":
        in_scope = lower_id == rg_prefix
    else:
        in_scope = lower_id.startswith(rg_prefix + "/providers/")
    if not in_scope:
        outside_scope.append(resource_id)
    redacted = re.sub(r"(?i)/subscriptions/[0-9a-f-]+", "/subscriptions/<redacted>", resource_id)
    records.append({"change_type":change_type,"resource_type":kind,"resource_id":redacted})
missing_types = sorted(required_types - seen_types)
safe = not unexpected_types and not unexpected_change_types and not outside_scope and not missing_types and bool(changes)
summary = {
    "observation_status":"observed",
    "what_if_succeeded":True,
    "result_format":"ResourceIdOnly",
    "change_count":len(changes),
    "changes":records,
    "observed_resource_types":sorted(seen_types),
    "missing_expected_resource_types":missing_types,
    "unexpected_resource_types":sorted(set(unexpected_types)),
    "unexpected_change_types":sorted(set(unexpected_change_types)),
    "outside_authorized_scope_count":len(outside_scope),
    "what_if_safe":safe,
    "parameter_values_persisted":False,
    "azure_mutations_performed":False,
}
Path(sys.argv[2]).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
PY
else
  jq -n --argjson exit_status "$what_if_exit" \
    '{observation_status:"observed",what_if_succeeded:false,what_if_safe:false,exit_status:$exit_status,stderr_persisted:false,parameter_values_persisted:false,azure_mutations_performed:false}' \
    > "$evidence_dir/what-if-summary.json"
fi

python3 - "$evidence_dir" "$summary_path" "$attempt_id" "$AZURE_LAB_FACTORY_RUN1_REVIEWED_COMMIT" <<'PY'
import json, sys
from pathlib import Path
evidence = Path(sys.argv[1])
def load(name):
    return json.loads((evidence / name).read_text())
providers = load("provider-states.json")
sku = load("vm-sku.json")
quota = load("quota-summary.json")
group = load("target-resource-group.json")
price = load("retail-price-summary.json")
validation = load("template-validation-summary.json")
what_if = load("what-if-summary.json")
checks = {
    "subscription_enabled": load("account-context.json").get("subscription_state") == "Enabled",
    "providers_registered": all(item.get("observation_status") == "observed" and item.get("registration_state") == "Registered" for item in providers),
    "sku_available": sku.get("sku_found") is True and sku.get("available_for_subscription") is True,
    "quota_sufficient": quota.get("quota_sufficient") is True,
    "target_resource_group_absent": group.get("observation_status") == "not_present",
    "retail_price_observed": price.get("observation_status") == "observed",
    "planning_estimate_within_ceiling": price.get("within_ceiling") is True,
    "template_validation_succeeded": validation.get("validation_succeeded") is True,
    "what_if_succeeded": what_if.get("what_if_succeeded") is True,
    "what_if_safe": what_if.get("what_if_safe") is True,
}
required_observation_failed = any(
    value.get("observation_status") == "observation_failed"
    for value in (sku, quota, group, price, validation, what_if)
) or any(item.get("observation_status") == "observation_failed" for item in providers)
if required_observation_failed:
    status = "observation_failed"
elif all(checks.values()):
    status = "passed"
else:
    status = "blocked"
summary = {
    "schema_version":"lab-factory.preflight-receipt.v1",
    "attempt_id":sys.argv[3],
    "reviewed_commit":sys.argv[4],
    "observed_at_utc":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    "profile":"servicetracer-demo-api@1.0.0",
    "request":{"environment":"dev","location":"westus2","ttl_hours":8,"resource_group":"rg-st-demo-api-dev-westus2","vm_size":"Standard_F1als_v7"},
    "checks":checks,
    "preflight_status":status,
    "next_gate":"separate_deployment_authorization_required" if status == "passed" else "stop_and_reconcile_preflight_evidence",
    "authorization_consumed":True,
    "azure_authentication_performed":True,
    "arm_validation_performed":validation.get("validation_succeeded") is not None,
    "arm_what_if_performed":what_if.get("what_if_succeeded") is not None,
    "azure_mutations_authorized":False,
    "azure_mutations_performed":False,
    "deployment_authorized":False,
    "deployment_performed":False,
    "model_call_performed":False,
    "remote_mcp_action_performed":False,
    "cleanup_authorized":False,
    "secrets_returned":False,
    "retry_authorized":False,
    "cost_boundary":{
        "currency":"CAD",
        "planning_ceiling":5.0,
        "planning_estimate":price.get("planning_estimate_cad"),
        "estimate_complete":price.get("estimate_complete"),
        "estimated_cost_is_actual_cost":False,
    },
    "limitations":[
        "production application parameter values were not validated",
        "DNS label availability was not independently queried outside ARM validation and What-If",
        "the cost estimate includes an explicit contingency and is not an invoice or actual incremental cost",
        "authentication success does not prove effective least privilege",
        "What-If success does not authorize deployment",
    ],
}
Path(sys.argv[2]).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
PY

find "$evidence_dir" -maxdepth 1 -type f ! -name artifact-manifest.sha256 -print0 \
  | sort -z \
  | xargs -0 -r sha256sum \
  > "$manifest_path"

printf '\nServiceTracer Lab Factory read-only preflight completed.\n'
printf 'Status: %s\n' "$(jq -r '.preflight_status' "$summary_path")"
printf 'Evidence: %s\n' "$evidence_dir"
printf 'Manifest: %s\n' "$manifest_path"
printf 'Azure mutations performed: false\n'
printf 'Deployment authorized: false\n'
printf 'Attempt consumed: true — do not rerun without new authority.\n'
