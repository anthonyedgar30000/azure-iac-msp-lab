#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  execute_existing_collector_report_publication.sh \
    --resource-group <name> \
    --location <region> \
    --prefix <prefix> \
    --environment <dev|test> \
    --allowed-origin <https-origin> \
    --frontend-url <https-url> \
    --plan-verification <json> \
    --plan-parameters <json> \
    --artifact-dir <directory> \
    [--attempts <2-100>] \
    [--github-output <path>]

Deploys only the dedicated public-report Storage account, Blob service, $web
container access configuration, and current collector Storage-scoped data role.
It then proves managed-identity publication and the browser-readable Blob CORS
path. Any post-deployment failure triggers bounded rollback of those resources.
USAGE
}

fail() {
  echo "$1" >&2
  exit "${2:-1}"
}

resource_group=''
location=''
prefix=''
environment=''
allowed_origin=''
frontend_url=''
plan_verification=''
plan_parameters=''
artifact_dir=''
attempts='30'
github_output=''

while (($# > 0)); do
  case "$1" in
    --resource-group) resource_group="${2:-}"; shift 2 ;;
    --location) location="${2:-}"; shift 2 ;;
    --prefix) prefix="${2:-}"; shift 2 ;;
    --environment) environment="${2:-}"; shift 2 ;;
    --allowed-origin) allowed_origin="${2:-}"; shift 2 ;;
    --frontend-url) frontend_url="${2:-}"; shift 2 ;;
    --plan-verification) plan_verification="${2:-}"; shift 2 ;;
    --plan-parameters) plan_parameters="${2:-}"; shift 2 ;;
    --artifact-dir) artifact_dir="${2:-}"; shift 2 ;;
    --attempts) attempts="${2:-}"; shift 2 ;;
    --github-output) github_output="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

for value_name in resource_group location prefix environment allowed_origin frontend_url plan_verification plan_parameters artifact_dir; do
  [[ -n "${!value_name}" ]] || fail "Missing required argument: ${value_name//_/-}" 2
done
[[ "$resource_group" =~ ^rg-servicetracer-(dev|test)(-[a-z0-9-]+)?$ ]] || fail 'Resource group is outside the ServiceTracer naming contract.' 2
[[ "$location" =~ ^[a-z0-9]+$ ]] || fail 'Location must contain lowercase letters and digits only.' 2
[[ "$prefix" =~ ^[a-z0-9]{2,12}$ ]] || fail 'Prefix must contain 2-12 lowercase letters or digits.' 2
[[ "$environment" =~ ^(dev|test)$ ]] || fail 'Environment must be dev or test.' 2
[[ "$allowed_origin" =~ ^https://[A-Za-z0-9.-]+(:[0-9]+)?$ ]] || fail 'Allowed origin must be an HTTPS origin without a path.' 2
[[ "$frontend_url" =~ ^https://[A-Za-z0-9./_-]+$ ]] || fail 'Frontend URL must be HTTPS.' 2
[[ "$attempts" =~ ^[0-9]+$ ]] || fail 'Attempts must be numeric.' 2
((attempts >= 2 && attempts <= 100)) || fail 'Attempts must be between 2 and 100.' 2
[[ -s "$plan_verification" ]] || fail 'Plan verification evidence is missing.'
[[ -s "$plan_parameters" ]] || fail 'Plan deployment parameters are missing.'

for command_name in az jq python curl base64 sha256sum; do
  command -v "$command_name" >/dev/null 2>&1 || fail "Required command is unavailable: $command_name" 127
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
template="$repo_root/infra/report-publication-existing-collector.bicep"
[[ -f "$template" ]] || fail "Missing template: $template"
mkdir -p "$artifact_dir"

collector_vm="vm-stcollector-${prefix}-${environment}"
storage_account="$(jq -r '.storage_account_name' "$plan_verification")"
collector_principal_id="$(jq -r '.collector_principal_id' "$plan_verification")"
[[ "$(jq -r '.create_change_count' "$plan_verification")" == '4' ]] || fail 'Pinned plan verification is not the four-create architecture.'
[[ "$(jq -r '.public_report_container' "$plan_verification")" == '$web' ]] || fail 'Pinned plan verification does not identify the $web container.'
[[ "$storage_account" =~ ^[a-z0-9]{3,24}$ ]] || fail 'Planned Storage account name is invalid.'
[[ "$collector_principal_id" =~ ^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$ ]] || fail 'Planned collector principal is not a canonical GUID.'
jq -e \
  --arg principal "$collector_principal_id" \
  --arg origin "$allowed_origin" \
  '.parameters.collectorPrincipalId.value == $principal and .parameters.allowedOrigins.value == [$origin]' \
  "$plan_parameters" >/dev/null || fail 'Pinned plan parameters do not match the reviewed principal and origin.'

rollback_required=false
rollback_completed=false
rollback_publication() {
  local reason="$1"
  mkdir -p "$artifact_dir/rollback"
  jq -n \
    --arg reason "$reason" \
    --arg resourceGroup "$resource_group" \
    --arg storageAccount "$storage_account" \
    --arg collectorPrincipalId "$collector_principal_id" \
    '{reason:$reason,resource_group:$resourceGroup,storage_account:$storageAccount,collector_principal_id:$collectorPrincipalId}' \
    > "$artifact_dir/rollback/request.json"

  if az storage account show --resource-group "$resource_group" --name "$storage_account" --output json > "$artifact_dir/rollback/storage-before.json" 2>/dev/null; then
    storage_id="$(jq -r '.id' "$artifact_dir/rollback/storage-before.json")"
    az role assignment list --scope "$storage_id" --include-inherited --output json \
      > "$artifact_dir/rollback/roles-before.json" || printf '[]\n' > "$artifact_dir/rollback/roles-before.json"
    jq -r \
      --arg principal "${collector_principal_id,,}" \
      --arg role 'ba92f5b4-2d11-453d-a403-e96b0029c9fe' \
      '.[] | select((.principalId | ascii_downcase) == $principal and (.roleDefinitionId | ascii_downcase | endswith($role))) | .id' \
      "$artifact_dir/rollback/roles-before.json" \
      | while IFS= read -r role_id; do
          [[ -z "$role_id" ]] || az role assignment delete --ids "$role_id"
        done
    az storage account delete --resource-group "$resource_group" --name "$storage_account" --yes
  fi

  if az storage account show --resource-group "$resource_group" --name "$storage_account" --output none 2>/dev/null; then
    echo 'Report Storage account still exists after rollback.' >&2
    return 1
  fi
  rollback_completed=true
  jq -n \
    --arg storageAccount "$storage_account" \
    --arg rolledBackAt "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    '{status:"rolled_back",storage_account:$storageAccount,rolled_back_at:$rolledBackAt,collector_compute_changed:false,network_changed:false}' \
    > "$artifact_dir/rollback/result.json"
}

on_exit() {
  status=$?
  if ((status != 0)) && [[ "$rollback_required" == true ]]; then
    rollback_publication "execution_failed_exit_${status}" || true
  fi
  find "$artifact_dir" -type f ! -name artifact-manifest.sha256 -printf '%P\0' \
    | sort -z \
    | while IFS= read -r -d '' relative; do
        sha256sum "$artifact_dir/$relative" | sed "s#  $artifact_dir/#  #"
      done > "$artifact_dir/artifact-manifest.sha256" || true
  exit "$status"
}
trap on_exit EXIT

az account show --output json > "$artifact_dir/azure-context.json"
az group show --name "$resource_group" --output json > "$artifact_dir/resource-group-prechange.json"
[[ "$(jq -r '.location' "$artifact_dir/resource-group-prechange.json")" == "$location" ]] || fail 'Resource-group location differs from the reviewed plan.'
[[ "$(jq -r '.tags.workload // empty' "$artifact_dir/resource-group-prechange.json")" == 'azure-iac-msp-lab' ]] || fail 'Resource-group workload tag differs from the reviewed plan.'
[[ "$(jq -r '.tags.purpose // empty' "$artifact_dir/resource-group-prechange.json")" == 'servicetracer-demo' ]] || fail 'Resource-group purpose tag differs from the reviewed plan.'

az vm show --resource-group "$resource_group" --name "$collector_vm" --show-details --output json > "$artifact_dir/collector-prechange.json"
current_principal="$(jq -r '.identity.principalId // empty' "$artifact_dir/collector-prechange.json")"
[[ "$current_principal" == "$collector_principal_id" ]] || fail 'Collector managed-identity principal changed after planning.'
[[ "$(jq -r '.provisioningState' "$artifact_dir/collector-prechange.json")" == 'Succeeded' ]] || fail 'Collector is not provisioned successfully.'

az storage account list --resource-group "$resource_group" --output json > "$artifact_dir/storage-accounts-prechange.json"
jq --arg name "$storage_account" \
  '[.[] | select(.name == $name or .tags.component == "servicetracer-public-report" or .tags.purpose == "servicetracer-live-report")]' \
  "$artifact_dir/storage-accounts-prechange.json" > "$artifact_dir/report-storage-prechange.json"
[[ "$(jq 'length' "$artifact_dir/report-storage-prechange.json")" == '0' ]] || fail 'A report Storage account already exists; use a separately reviewed update or recovery path.'

az vm run-command invoke \
  --resource-group "$resource_group" \
  --name "$collector_vm" \
  --command-id RunShellScript \
  --scripts 'set -euo pipefail; test -x /opt/servicetracer/bin/servicetracer-publish-report; /opt/servicetracer/bin/servicetracer-publish-report --help >/dev/null; echo SERVICETRACER_PUBLISHER_PREFLIGHT_OK' \
  --output json > "$artifact_dir/collector-publisher-preflight.json"
jq -e '.value[0].message | contains("SERVICETRACER_PUBLISHER_PREFLIGHT_OK")' "$artifact_dir/collector-publisher-preflight.json" >/dev/null || fail 'Collector publisher preflight failed before deployment.'

for backend in vpn01 vpn02; do
  az vm get-instance-view \
    --resource-group "$resource_group" \
    --name "vm-${backend}-${prefix}-${environment}" \
    --query '{name:name,statuses:instanceView.statuses[].code}' \
    --output json
done | jq -s '.' > "$artifact_dir/backend-preflight.json"
jq -e 'length == 2 and all(.[]; any(.statuses[]; . == "PowerState/running"))' "$artifact_dir/backend-preflight.json" >/dev/null || fail 'Both backend VMs must be running before publication deployment.'

az deployment group validate \
  --resource-group "$resource_group" \
  --name existing-collector-report-publication-execution \
  --template-file "$template" \
  --parameters "@$plan_parameters" \
  --validation-level Provider \
  --output json > "$artifact_dir/arm-provider-validation.json"
jq -e '.properties.provisioningState == "Succeeded" and .properties.validationLevel == "Provider"' "$artifact_dir/arm-provider-validation.json" >/dev/null || fail 'Provider validation did not prove current deployment permissions.'

az deployment group what-if \
  --resource-group "$resource_group" \
  --name existing-collector-report-publication-execution \
  --template-file "$template" \
  --parameters "@$plan_parameters" \
  --validation-level Provider \
  --no-pretty-print \
  --result-format FullResourcePayloads \
  --output json > "$artifact_dir/arm-provider-what-if.json"
python - "$artifact_dir/arm-provider-what-if.json" "$storage_account" "$allowed_origin" "$collector_principal_id" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
storage_name, origin, principal = sys.argv[2:]
if payload.get("status") != "Succeeded" or payload.get("error") is not None:
    raise SystemExit("Provider What-If failed")
changes = payload.get("changes") or []
forbidden = [c for c in changes if c.get("changeType") not in {"Create", "Ignore", "NoChange"}]
creates = [c for c in changes if c.get("changeType") == "Create"]
if forbidden or len(creates) != 4:
    raise SystemExit("Provider What-If is outside the reviewed four-create boundary")
by_type = {}
for change in creates:
    by_type.setdefault(change.get("after", {}).get("type"), []).append(change)
expected_types = {
    "Microsoft.Storage/storageAccounts",
    "Microsoft.Storage/storageAccounts/blobServices",
    "Microsoft.Storage/storageAccounts/blobServices/containers",
    "Microsoft.Authorization/roleAssignments",
}
if set(by_type) != expected_types or any(len(items) != 1 for items in by_type.values()):
    raise SystemExit("Provider What-If resource types differ from the pinned plan")
storage = by_type["Microsoft.Storage/storageAccounts"][0]
storage_id = str(storage.get("resourceId") or "")
if not storage_id.endswith("/storageAccounts/" + storage_name):
    raise SystemExit("Provider What-If Storage account differs from the pinned plan")
blob = by_type["Microsoft.Storage/storageAccounts/blobServices"][0]
container = by_type["Microsoft.Storage/storageAccounts/blobServices/containers"][0]
role = by_type["Microsoft.Authorization/roleAssignments"][0]
if str(blob.get("resourceId")) != storage_id + "/blobServices/default":
    raise SystemExit("Provider What-If Blob service scope differs from the pinned plan")
if str(container.get("resourceId")) != storage_id + "/blobServices/default/containers/$web":
    raise SystemExit("Provider What-If $web scope differs from the pinned plan")
if container.get("after", {}).get("properties", {}).get("publicAccess") != "Blob":
    raise SystemExit("Provider What-If does not preserve Blob-only anonymous access")
if not str(role.get("resourceId") or "").startswith(storage_id + "/providers/Microsoft.Authorization/roleAssignments/"):
    raise SystemExit("Provider What-If role scope differs from the pinned plan")
if str(role.get("after", {}).get("properties", {}).get("principalId") or "").lower() != principal.lower():
    raise SystemExit("Provider What-If role principal differs from the pinned plan")
properties = storage.get("after", {}).get("properties", {})
if properties.get("allowBlobPublicAccess") is not True or properties.get("allowSharedKeyAccess") is not False:
    raise SystemExit("Provider What-If Storage access boundary differs from the pinned plan")
cors = blob.get("after", {}).get("properties", {}).get("cors", {}).get("corsRules", [])
if len(cors) != 1 or cors[0].get("allowedOrigins") != [origin]:
    raise SystemExit("Provider What-If CORS origin differs from the pinned plan")
protected = ("Microsoft.Compute/", "Microsoft.Network/", "Microsoft.OperationalInsights/")
for change in changes:
    rid = str(change.get("resourceId") or "")
    provider_path = rid.split("/providers/", 1)[-1]
    if provider_path.startswith(protected) and change.get("changeType") not in {"Ignore", "NoChange"}:
        raise SystemExit("Provider What-If changes protected infrastructure")
PY

rollback_required=true
az deployment group create \
  --resource-group "$resource_group" \
  --name existing-collector-report-publication-execution \
  --template-file "$template" \
  --parameters "@$plan_parameters" \
  --output json > "$artifact_dir/deployment-result.json"
jq -e '.properties.provisioningState == "Succeeded"' "$artifact_dir/deployment-result.json" >/dev/null || fail 'Publication deployment did not succeed.'

az storage account show --resource-group "$resource_group" --name "$storage_account" --output json > "$artifact_dir/storage-postchange.json"
storage_id="$(jq -r '.id' "$artifact_dir/storage-postchange.json")"
blob_endpoint="$(jq -r '.primaryEndpoints.blob' "$artifact_dir/storage-postchange.json")"
[[ "$blob_endpoint" =~ ^https://[a-z0-9]+\.blob\.core\.windows\.net/$ ]] || fail 'Azure did not return the expected Blob service endpoint.'
public_report_url="${blob_endpoint}\$web/reports/technician-handoff-report.json"
jq -e '.provisioningState == "Succeeded" and .enableHttpsTrafficOnly == true and .minimumTlsVersion == "TLS1_2" and .allowSharedKeyAccess == false and .defaultToOAuthAuthentication == true and .allowBlobPublicAccess == true and .publicNetworkAccess == "Enabled"' "$artifact_dir/storage-postchange.json" >/dev/null || fail 'Storage security configuration differs from the reviewed contract.'

az storage account blob-service-properties show \
  --resource-group "$resource_group" \
  --account-name "$storage_account" \
  --output json > "$artifact_dir/blob-service-postchange.json"
jq -e --arg origin "$allowed_origin" '.isVersioningEnabled == true and .deleteRetentionPolicy.enabled == true and .deleteRetentionPolicy.days == 7 and .staticWebsite.enabled == true and (.cors.corsRules | length == 1) and (.cors.corsRules[0].allowedOrigins == [$origin]) and ((.cors.corsRules[0].allowedMethods | sort) == (["GET","HEAD","OPTIONS"] | sort))' "$artifact_dir/blob-service-postchange.json" >/dev/null || fail 'Blob service, CORS, versioning, or retention verification failed.'

container_id="${storage_id}/blobServices/default/containers/\$web"
az resource show --ids "$container_id" --api-version 2023-05-01 --output json > "$artifact_dir/web-container-postchange.json"
jq -e '.name == "$web" and .properties.publicAccess == "Blob"' "$artifact_dir/web-container-postchange.json" >/dev/null || fail '$web container is not configured for Blob-only anonymous read.'

az role assignment list --scope "$storage_id" --include-inherited --output json > "$artifact_dir/collector-storage-role-postchange.json"
jq -e \
  --arg storageId "${storage_id,,}" \
  --arg principal "${collector_principal_id,,}" \
  --arg roleId 'ba92f5b4-2d11-453d-a403-e96b0029c9fe' \
  '[.[] | select((.scope | ascii_downcase) == $storageId and (.principalId | ascii_downcase) == $principal and (.roleDefinitionId | ascii_downcase | endswith($roleId)))] | length == 1' \
  "$artifact_dir/collector-storage-role-postchange.json" >/dev/null || fail 'Current collector Storage role is missing or ambiguous.'

lb_name="lb-remote-access-${prefix}-${environment}"
pip_name="pip-remote-access-${prefix}-${environment}"
lb_id="$(az network lb show --resource-group "$resource_group" --name "$lb_name" --query id --output tsv)"
public_ip="$(az network public-ip show --resource-group "$resource_group" --name "$pip_name" --query ipAddress --output tsv)"
[[ -n "$lb_id" && -n "$public_ip" ]] || fail 'Live Azure load-balancer boundary could not be resolved.'
jq -n \
  --arg resourceGroup "$resource_group" \
  --arg loadBalancerId "$lb_id" \
  --arg loadBalancerName "$lb_name" \
  --arg publicIp "$public_ip" \
  --arg collectorVm "$collector_vm" \
  --arg storageAccount "$storage_account" \
  --arg publicReportUrl "$public_report_url" \
  '{resource_group:$resourceGroup,load_balancer_id:$loadBalancerId,load_balancer_name:$loadBalancerName,public_ip:$publicIp,collector_vm:$collectorVm,storage_account:$storageAccount,public_report_url:$publicReportUrl}' \
  > "$artifact_dir/azure-boundary.json"

healthy=false
for _ in $(seq 1 30); do
  az monitor metrics list \
    --resource "$lb_id" \
    --metric DipAvailability \
    --aggregation Average \
    --interval PT1M \
    --filter "BackendIPAddress eq '*' and BackendPort eq '*'" \
    --output json > "$artifact_dir/load-balancer-probe-metrics.json"
  python - "$artifact_dir/load-balancer-probe-metrics.json" "$artifact_dir/probe-status.json" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
ip_to_backend = {"10.20.10.11": "VPN-01", "10.20.10.12": "VPN-02"}
status = {backend: "unknown" for backend in ip_to_backend.values()}
values = payload.get("value") or []
if values:
    for series in values[0].get("timeseries") or []:
        dimensions = {
            item.get("name", {}).get("value"): item.get("value")
            for item in series.get("metadatavalues") or []
        }
        backend = ip_to_backend.get(dimensions.get("BackendIPAddress"))
        averages = [
            point.get("average")
            for point in series.get("data") or []
            if point.get("average") is not None
        ]
        if backend and averages:
            status[backend] = "healthy" if averages[-1] >= 1 else "unhealthy"
Path(sys.argv[2]).write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
PY
  if jq -e '.["VPN-01"] == "healthy" and .["VPN-02"] == "healthy"' "$artifact_dir/probe-status.json" >/dev/null; then
    healthy=true
    break
  fi
  sleep 20
done
[[ "$healthy" == true ]] || fail 'Both Azure backend probes did not become healthy within the bounded wait.'

PYTHONPATH="$repo_root/servicetracer/src" python -m servicetracer.azure_demo \
  --frontend-url "https://${public_ip}" \
  --probe-status "$artifact_dir/probe-status.json" \
  --attempts "$attempts" \
  --load-balancer-id "$lb_name" \
  --output "$artifact_dir/live-source-records.jsonl" \
  --raw-output "$artifact_dir/live-transactions.json"
PYTHONPATH="$repo_root/servicetracer/src" python -m servicetracer.collector_cli ingest \
  --spool "$artifact_dir/live-evidence-spool.jsonl" \
  --input "$artifact_dir/live-source-records.jsonl" \
  > "$artifact_dir/collector-receipt.json"
PYTHONPATH="$repo_root/servicetracer/src" python -m servicetracer.cli \
  --evidence-records "$artifact_dir/live-evidence-spool.jsonl" \
  --adapter-config "$repo_root/servicetracer/examples/evidence_adapters.json" \
  --service-path "$repo_root/servicetracer/examples/remote_access_service_path.json" \
  --report-view technician-handoff \
  --output "$artifact_dir/technician-handoff-report.json"
PYTHONPATH="$repo_root/servicetracer/src" python -m servicetracer.publish_cli \
  --input "$artifact_dir/technician-handoff-report.json" \
  --output "$artifact_dir/public-technician-handoff-report.json" \
  --source-id prepublication-runner-validation \
  --servicetracer-version 0.5.0 \
  --ttl-seconds 3600
jq -e '.load_balancer.status == "healthy_under_configured_probe" and .localization.suspect_backend == "VPN-02" and .localization.healthy_comparison_backend == "VPN-01" and .investigation_boundary.exact_root_cause_claimed == false' "$artifact_dir/technician-handoff-report.json" >/dev/null || fail 'Deterministic ServiceTracer claim boundary failed.'

report_b64="$(base64 -w 0 "$artifact_dir/technician-handoff-report.json")"
cat > "$artifact_dir/publish-live-report.sh" <<EOF
set -euo pipefail
umask 0077
echo '${report_b64}' | base64 -d > /tmp/servicetracer-live-handoff.json
cleanup() { rm -f /tmp/servicetracer-live-handoff.json; }
trap cleanup EXIT
for attempt in \$(seq 1 18); do
  if /opt/servicetracer/bin/servicetracer-publish-report \
    --input /tmp/servicetracer-live-handoff.json \
    --storage-account '${storage_account}' \
    --source-id '${collector_vm}' \
    --ttl-seconds 3600; then
    echo SERVICETRACER_PUBLICATION_OK
    exit 0
  fi
  sleep 10
done
exit 1
EOF
az vm run-command invoke \
  --resource-group "$resource_group" \
  --name "$collector_vm" \
  --command-id RunShellScript \
  --scripts "$(cat "$artifact_dir/publish-live-report.sh")" \
  --output json > "$artifact_dir/publish-run-command.json"
rm -f "$artifact_dir/publish-live-report.sh"
jq -e '.value[0].message | contains("SERVICETRACER_PUBLICATION_OK")' "$artifact_dir/publish-run-command.json" >/dev/null || fail 'Collector managed-identity publication failed.'

fetched=false
for _ in $(seq 1 18); do
  if curl --fail --silent --show-error \
    --header "Origin: $allowed_origin" \
    --dump-header "$artifact_dir/public-report-headers.txt" \
    --output "$artifact_dir/public-report-fetched.json" \
    "$public_report_url"; then
    fetched=true
    break
  fi
  sleep 10
done
[[ "$fetched" == true ]] || fail 'Public report could not be fetched from the Blob endpoint within the bounded wait.'
python - "$artifact_dir/public-report-fetched.json" "$artifact_dir/public-technician-handoff-report.json" "$artifact_dir/public-report-headers.txt" "$collector_vm" "$allowed_origin" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

fetched = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
local = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
headers = {}
for line in Path(sys.argv[3]).read_text(encoding="utf-8").splitlines():
    if ":" in line:
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()
if fetched.get("schema_version") != "servicetracer.public-report.v1":
    raise SystemExit("Unexpected public schema")
if fetched.get("source", {}).get("id") != sys.argv[4]:
    raise SystemExit("Public report was not published by the expected collector")
expires = datetime.fromisoformat(fetched["expires_at"].replace("Z", "+00:00"))
if expires <= datetime.now(timezone.utc):
    raise SystemExit("Public report is already stale")
if fetched.get("report") != local.get("report"):
    raise SystemExit("Fetched public report differs from the locally sanitized report")
if headers.get("access-control-allow-origin") != sys.argv[5]:
    raise SystemExit("Public report CORS origin does not match the reviewed frontend origin")
PY

frontend_test_url="$(python - "$frontend_url" "$public_report_url" <<'PY'
import sys
from urllib.parse import quote
print(f"{sys.argv[1]}?report={quote(sys.argv[2], safe='')}")
PY
)"
jq -n \
  --arg publicReportUrl "$public_report_url" \
  --arg frontendTestUrl "$frontend_test_url" \
  --arg collector "$collector_vm" \
  --arg storageAccount "$storage_account" \
  '{status:"live_report_path_verified",public_report_url:$publicReportUrl,frontend_test_url:$frontendTestUrl,collector_source:$collector,storage_account:$storageAccount,schema_verified:true,freshness_verified:true,cors_verified:true,report_content_match_verified:true,blob_endpoint_verified:true,web_container_blob_public_access_verified:true,real_azure_probe_metrics:true,real_frontend_transactions:true,collector_managed_identity_publication:true,frontend_query_url_generated:true,browser_rendering_verified:false,default_frontend_source_committed:false}' \
  > "$artifact_dir/live-integration-verification.json"

if [[ -n "$github_output" ]]; then
  {
    printf 'public_report_url=%s\n' "$public_report_url"
    printf 'frontend_test_url=%s\n' "$frontend_test_url"
    printf 'storage_account_name=%s\n' "$storage_account"
  } >> "$github_output"
fi

rollback_required=false
jq -n \
  --arg storageAccount "$storage_account" \
  --arg publicReportUrl "$public_report_url" \
  --arg frontendTestUrl "$frontend_test_url" \
  '{status:"succeeded",storage_account:$storageAccount,public_report_url:$publicReportUrl,frontend_test_url:$frontendTestUrl,rollback_required:false}' \
  > "$artifact_dir/execution-summary.json"
