#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: verify_collector_deployment.sh \
  --resource-group NAME \
  --prefix PREFIX \
  --environment dev|test \
  --expected-private-ip ADDRESS \
  --collector-port PORT \
  --verification-id ID \
  --output PATH
EOF
}

RESOURCE_GROUP=''
PREFIX=''
ENVIRONMENT=''
EXPECTED_PRIVATE_IP=''
COLLECTOR_PORT=''
VERIFICATION_ID=''
OUTPUT_PATH=''

while (($#)); do
  case "$1" in
    --resource-group) RESOURCE_GROUP="$2"; shift 2 ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    --environment) ENVIRONMENT="$2"; shift 2 ;;
    --expected-private-ip) EXPECTED_PRIVATE_IP="$2"; shift 2 ;;
    --collector-port) COLLECTOR_PORT="$2"; shift 2 ;;
    --verification-id) VERIFICATION_ID="$2"; shift 2 ;;
    --output) OUTPUT_PATH="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

for required_name in RESOURCE_GROUP PREFIX ENVIRONMENT EXPECTED_PRIVATE_IP COLLECTOR_PORT VERIFICATION_ID OUTPUT_PATH; do
  if [[ -z "${!required_name}" ]]; then
    echo "Missing required value: ${required_name}" >&2
    usage >&2
    exit 2
  fi
done

if [[ ! "$PREFIX" =~ ^[a-z0-9]{2,12}$ ]]; then
  echo 'Prefix must contain 2-12 lowercase letters or digits.' >&2
  exit 2
fi
if [[ ! "$ENVIRONMENT" =~ ^(dev|test)$ ]]; then
  echo 'Environment must be dev or test.' >&2
  exit 2
fi
if [[ ! "$COLLECTOR_PORT" =~ ^[0-9]+$ ]] || ((COLLECTOR_PORT < 1 || COLLECTOR_PORT > 65535)); then
  echo 'Collector port must be between 1 and 65535.' >&2
  exit 2
fi
if [[ ! "$VERIFICATION_ID" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo 'Verification ID contains unsupported characters.' >&2
  exit 2
fi

RESOURCE_SUFFIX="${PREFIX}-${ENVIRONMENT}"
VM_NAME="vm-stcollector-${RESOURCE_SUFFIX}"
NIC_NAME="nic-stcollector-${RESOURCE_SUFFIX}"
DISK_NAME="disk-stcollector-evidence-${RESOURCE_SUFFIX}"

mkdir -p "$(dirname "$OUTPUT_PATH")"

verification_phase='azure-resource-discovery'
principal_id=''
private_ip=''
public_ip_id=''
data_disk_delete_option=''
disk_network_access_policy=''
disk_public_network_access=''
run_command_message=''

write_result() {
  local status="$1"
  local reason="$2"

  jq -n \
    --arg status "$status" \
    --arg reason "$reason" \
    --arg phase "$verification_phase" \
    --arg verifiedAt "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    --arg resourceGroup "$RESOURCE_GROUP" \
    --arg vmName "$VM_NAME" \
    --arg nicName "$NIC_NAME" \
    --arg evidenceDiskName "$DISK_NAME" \
    --arg principalId "$principal_id" \
    --arg privateIp "$private_ip" \
    --arg publicIpId "$public_ip_id" \
    --arg dataDiskDeleteOption "$data_disk_delete_option" \
    --arg diskNetworkAccessPolicy "$disk_network_access_policy" \
    --arg diskPublicNetworkAccess "$disk_public_network_access" \
    --arg verificationId "$VERIFICATION_ID" \
    --arg runCommandMessage "$run_command_message" \
    '{
      status: $status,
      verified_at: $verifiedAt,
      verification_id: $verificationId,
      phase: $phase,
      failure_reason: (if $reason == "" then null else $reason end),
      azure: {
        resource_group: $resourceGroup,
        vm_name: $vmName,
        nic_name: $nicName,
        evidence_disk_name: $evidenceDiskName,
        system_assigned_principal_id: (if $principalId == "" then null else $principalId end),
        private_ip: (if $privateIp == "" then null else $privateIp end),
        public_ip_attached: ($publicIpId != ""),
        public_ip_id: (if $publicIpId == "" then null else $publicIpId end),
        evidence_disk_delete_option: (if $dataDiskDeleteOption == "" then null else $dataDiskDeleteOption end),
        disk_network_access_policy: (if $diskNetworkAccessPolicy == "" then null else $diskNetworkAccessPolicy end),
        disk_public_network_access: (if $diskPublicNetworkAccess == "" then null else $diskPublicNetworkAccess end)
      },
      guest_verification_output: (if $runCommandMessage == "" then null else $runCommandMessage end)
    }' >"$OUTPUT_PATH"
}

fail_verification() {
  local reason="$1"
  write_result 'failed' "$reason"
  echo "$reason" >&2
  if [[ -n "$run_command_message" ]]; then
    printf '%s\n' "$run_command_message" >&2
  fi
  exit 1
}

if ! vm_json="$(az vm show --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" --output json 2>&1)"; then
  run_command_message="$vm_json"
  fail_verification "Could not read collector VM ${VM_NAME}."
fi
if ! nic_json="$(az network nic show --resource-group "$RESOURCE_GROUP" --name "$NIC_NAME" --output json 2>&1)"; then
  run_command_message="$nic_json"
  fail_verification "Could not read collector NIC ${NIC_NAME}."
fi
if ! disk_json="$(az disk show --resource-group "$RESOURCE_GROUP" --name "$DISK_NAME" --output json 2>&1)"; then
  run_command_message="$disk_json"
  fail_verification "Could not read collector evidence disk ${DISK_NAME}."
fi

principal_id="$(jq -r '.identity.principalId // empty' <<<"$vm_json")"
private_ip="$(jq -r '.ipConfigurations[0].privateIPAddress // empty' <<<"$nic_json")"
public_ip_id="$(jq -r '.ipConfigurations[0].publicIPAddress.id // empty' <<<"$nic_json")"
data_disk_delete_option="$(jq -r '.storageProfile.dataDisks[] | select(.lun == 0) | .deleteOption // empty' <<<"$vm_json")"
disk_network_access_policy="$(jq -r '.networkAccessPolicy // empty' <<<"$disk_json")"
disk_public_network_access="$(jq -r '.publicNetworkAccess // empty' <<<"$disk_json")"

verification_phase='azure-contract-validation'
[[ -n "$principal_id" ]] || fail_verification 'Collector VM has no system-assigned principal ID.'
[[ "$private_ip" == "$EXPECTED_PRIVATE_IP" ]] || {
  fail_verification "Expected private IP ${EXPECTED_PRIVATE_IP}, observed ${private_ip:-<missing>}."
}
[[ -z "$public_ip_id" ]] || {
  fail_verification "Collector NIC unexpectedly references a public IP: $public_ip_id"
}
[[ "$data_disk_delete_option" == 'Detach' ]] || {
  fail_verification "Expected evidence-disk deleteOption Detach, observed ${data_disk_delete_option:-<missing>}."
}
[[ "$disk_network_access_policy" == 'DenyAll' ]] || {
  fail_verification "Expected disk networkAccessPolicy DenyAll, observed ${disk_network_access_policy:-<missing>}."
}
[[ "$disk_public_network_access" == 'Disabled' ]] || {
  fail_verification "Expected disk publicNetworkAccess Disabled, observed ${disk_public_network_access:-<missing>}."
}

remote_script="$(mktemp)"
trap 'rm -f "$remote_script"' EXIT
cat >"$remote_script" <<EOF
#!/usr/bin/env bash
set -euo pipefail

COLLECTOR_PORT='${COLLECTOR_PORT}'
VERIFICATION_ID='${VERIFICATION_ID}'
DATA_ROOT='/var/lib/servicetracer'
TOKEN_FILE="\${DATA_ROOT}/config/collector.env"
BASE_URL="https://127.0.0.1:\${COLLECTOR_PORT}"
VERIFY_PHASE='start'

emit_failure_diagnostics() {
  local rc="\$?"
  set +e
  trap - ERR
  printf '\nSERVICETRACER_VERIFY_FAILED phase=%s exit_code=%s\n' "\${VERIFY_PHASE}" "\${rc}"
  printf '\n--- cloud-init status ---\n'
  cloud-init status --long 2>&1
  printf '\n--- block devices ---\n'
  lsblk -f 2>&1
  printf '\n--- evidence mount ---\n'
  findmnt "\${DATA_ROOT}" 2>&1
  printf '\n--- collector service status ---\n'
  systemctl status servicetracer-collector.service --no-pager 2>&1
  printf '\n--- collector journal ---\n'
  journalctl -u servicetracer-collector.service --no-pager -n 120 2>&1
  printf '\n--- cloud-init output tail ---\n'
  tail -n 120 /var/log/cloud-init-output.log 2>&1
  exit "\${rc}"
}
trap emit_failure_diagnostics ERR

VERIFY_PHASE='cloud-init-wait'
cloud-init status --wait >/dev/null

VERIFY_PHASE='evidence-mount'
mountpoint -q "\${DATA_ROOT}"

VERIFY_PHASE='service-enabled'
systemctl is-enabled --quiet servicetracer-collector.service

VERIFY_PHASE='service-active'
systemctl is-active --quiet servicetracer-collector.service

VERIFY_PHASE='health-endpoint'
curl --fail --silent --show-error --insecure "\${BASE_URL}/healthz" >/dev/null

VERIFY_PHASE='token-load'
set -a
# shellcheck disable=SC1090
source "\${TOKEN_FILE}"
set +a
: "\${SERVICETRACER_COLLECTOR_TOKEN:?collector token is missing}"

auth_header="Authorization: Bearer \${SERVICETRACER_COLLECTOR_TOKEN}"

VERIFY_PHASE='status-before'
status_before="\$(curl --fail --silent --show-error --insecure -H "\${auth_header}" "\${BASE_URL}/v1/status")"
records_before="\$(python3 -c 'import json,sys; print(json.load(sys.stdin)["records"])' <<<"\${status_before}")"

payload="\$(python3 - "\${VERIFICATION_ID}" <<'PY'
import json
import sys
from datetime import datetime, timezone
verification_id = sys.argv[1]
print(json.dumps({
    "source_type": "deployment_verification",
    "event_id": f"AZURE-VERIFY-{verification_id}",
    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "source_id": "azure-run-command",
    "event": "collector_round_trip",
    "verification_id": verification_id,
}, separators=(",", ":")))
PY
)"

VERIFY_PHASE='record-append'
receipt="\$(curl --fail --silent --show-error --insecure \
  -H "\${auth_header}" \
  -H 'Content-Type: application/json' \
  --data "\${payload}" \
  "\${BASE_URL}/v1/records")"
records_accepted="\$(python3 -c 'import json,sys; print(json.load(sys.stdin)["records_accepted"])' <<<"\${receipt}")"
[[ "\${records_accepted}" == '1' ]]

VERIFY_PHASE='status-after-append'
status_after_append="\$(curl --fail --silent --show-error --insecure -H "\${auth_header}" "\${BASE_URL}/v1/status")"
records_after_append="\$(python3 -c 'import json,sys; print(json.load(sys.stdin)["records"])' <<<"\${status_after_append}")"
[[ "\${records_after_append}" -eq "\$((records_before + 1))" ]]

VERIFY_PHASE='service-restart'
systemctl restart servicetracer-collector.service
for _ in \$(seq 1 30); do
  if curl --fail --silent --show-error --insecure "\${BASE_URL}/healthz" >/dev/null; then
    break
  fi
  sleep 2
done
systemctl is-active --quiet servicetracer-collector.service

VERIFY_PHASE='restart-persistence'
status_after_restart="\$(curl --fail --silent --show-error --insecure -H "\${auth_header}" "\${BASE_URL}/v1/status")"
records_after_restart="\$(python3 -c 'import json,sys; print(json.load(sys.stdin)["records"])' <<<"\${status_after_restart}")"
[[ "\${records_after_restart}" -eq "\${records_after_append}" ]]

trap - ERR
python3 - "\${records_before}" "\${records_after_append}" "\${records_after_restart}" <<'PY'
import json
import sys
print(json.dumps({
    "marker": "SERVICETRACER_VERIFY_OK",
    "cloud_init": "complete",
    "evidence_mount": "/var/lib/servicetracer",
    "service": "active",
    "health": "ok",
    "authenticated_record": "accepted",
    "records_before": int(sys.argv[1]),
    "records_after_append": int(sys.argv[2]),
    "records_after_restart": int(sys.argv[3]),
    "restart_persistence": True,
}, sort_keys=True))
PY
EOF

verification_phase='guest-run-command'
if ! run_command_json="$(az vm run-command invoke \
  --resource-group "$RESOURCE_GROUP" \
  --name "$VM_NAME" \
  --command-id RunShellScript \
  --scripts "@$remote_script" \
  --output json 2>&1)"; then
  run_command_message="$run_command_json"
  fail_verification 'Azure VM Run Command invocation failed.'
fi

run_command_message="$(jq -r '[.value[].message // empty] | join("\n")' <<<"$run_command_json")"
if ! grep -q 'SERVICETRACER_VERIFY_OK' <<<"$run_command_message"; then
  fail_verification 'Collector guest verification did not return its success marker.'
fi

verification_phase='complete'
write_result 'verified' ''
cat "$OUTPUT_PATH"
