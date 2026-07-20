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

vm_json="$(az vm show --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" --output json)"
nic_json="$(az network nic show --resource-group "$RESOURCE_GROUP" --name "$NIC_NAME" --output json)"
disk_json="$(az disk show --resource-group "$RESOURCE_GROUP" --name "$DISK_NAME" --output json)"

principal_id="$(jq -r '.identity.principalId // empty' <<<"$vm_json")"
private_ip="$(jq -r '.ipConfigurations[0].privateIPAddress // empty' <<<"$nic_json")"
public_ip_id="$(jq -r '.ipConfigurations[0].publicIPAddress.id // empty' <<<"$nic_json")"
data_disk_delete_option="$(jq -r '.storageProfile.dataDisks[] | select(.lun == 0) | .deleteOption // empty' <<<"$vm_json")"
disk_network_access_policy="$(jq -r '.networkAccessPolicy // empty' <<<"$disk_json")"
disk_public_network_access="$(jq -r '.publicNetworkAccess // empty' <<<"$disk_json")"

[[ -n "$principal_id" ]] || { echo 'Collector VM has no system-assigned principal ID.' >&2; exit 1; }
[[ "$private_ip" == "$EXPECTED_PRIVATE_IP" ]] || {
  echo "Expected private IP ${EXPECTED_PRIVATE_IP}, observed ${private_ip:-<missing>}." >&2
  exit 1
}
[[ -z "$public_ip_id" ]] || { echo "Collector NIC unexpectedly references a public IP: $public_ip_id" >&2; exit 1; }
[[ "$data_disk_delete_option" == 'Detach' ]] || {
  echo "Expected evidence-disk deleteOption Detach, observed ${data_disk_delete_option:-<missing>}." >&2
  exit 1
}
[[ "$disk_network_access_policy" == 'DenyAll' ]] || {
  echo "Expected disk networkAccessPolicy DenyAll, observed ${disk_network_access_policy:-<missing>}." >&2
  exit 1
}
[[ "$disk_public_network_access" == 'Disabled' ]] || {
  echo "Expected disk publicNetworkAccess Disabled, observed ${disk_public_network_access:-<missing>}." >&2
  exit 1
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

cloud-init status --wait >/dev/null
mountpoint -q "\${DATA_ROOT}"
systemctl is-enabled --quiet servicetracer-collector.service
systemctl is-active --quiet servicetracer-collector.service
curl --fail --silent --show-error --insecure "\${BASE_URL}/healthz" >/dev/null

set -a
# shellcheck disable=SC1090
source "\${TOKEN_FILE}"
set +a
: "\${SERVICETRACER_COLLECTOR_TOKEN:?collector token is missing}"

auth_header="Authorization: Bearer \${SERVICETRACER_COLLECTOR_TOKEN}"
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

receipt="\$(curl --fail --silent --show-error --insecure \
  -H "\${auth_header}" \
  -H 'Content-Type: application/json' \
  --data "\${payload}" \
  "\${BASE_URL}/v1/records")"
records_accepted="\$(python3 -c 'import json,sys; print(json.load(sys.stdin)["records_accepted"])' <<<"\${receipt}")"
[[ "\${records_accepted}" == '1' ]]

status_after_append="\$(curl --fail --silent --show-error --insecure -H "\${auth_header}" "\${BASE_URL}/v1/status")"
records_after_append="\$(python3 -c 'import json,sys; print(json.load(sys.stdin)["records"])' <<<"\${status_after_append}")"
[[ "\${records_after_append}" -eq "\$((records_before + 1))" ]]

systemctl restart servicetracer-collector.service
for _ in \$(seq 1 30); do
  if curl --fail --silent --show-error --insecure "\${BASE_URL}/healthz" >/dev/null; then
    break
  fi
  sleep 2
done
systemctl is-active --quiet servicetracer-collector.service

status_after_restart="\$(curl --fail --silent --show-error --insecure -H "\${auth_header}" "\${BASE_URL}/v1/status")"
records_after_restart="\$(python3 -c 'import json,sys; print(json.load(sys.stdin)["records"])' <<<"\${status_after_restart}")"
[[ "\${records_after_restart}" -eq "\${records_after_append}" ]]

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

run_command_json="$(az vm run-command invoke \
  --resource-group "$RESOURCE_GROUP" \
  --name "$VM_NAME" \
  --command-id RunShellScript \
  --scripts "@$remote_script" \
  --output json)"

run_command_message="$(jq -r '[.value[].message // empty] | join("\n")' <<<"$run_command_json")"
if ! grep -q 'SERVICETRACER_VERIFY_OK' <<<"$run_command_message"; then
  echo 'Collector guest verification did not return its success marker.' >&2
  printf '%s\n' "$run_command_message" >&2
  exit 1
fi

jq -n \
  --arg verifiedAt "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
  --arg resourceGroup "$RESOURCE_GROUP" \
  --arg vmName "$VM_NAME" \
  --arg nicName "$NIC_NAME" \
  --arg evidenceDiskName "$DISK_NAME" \
  --arg principalId "$principal_id" \
  --arg privateIp "$private_ip" \
  --arg dataDiskDeleteOption "$data_disk_delete_option" \
  --arg diskNetworkAccessPolicy "$disk_network_access_policy" \
  --arg diskPublicNetworkAccess "$disk_public_network_access" \
  --arg verificationId "$VERIFICATION_ID" \
  --arg runCommandMessage "$run_command_message" \
  '{
    status: "verified",
    verified_at: $verifiedAt,
    verification_id: $verificationId,
    azure: {
      resource_group: $resourceGroup,
      vm_name: $vmName,
      nic_name: $nicName,
      evidence_disk_name: $evidenceDiskName,
      system_assigned_principal_id: $principalId,
      private_ip: $privateIp,
      public_ip_attached: false,
      evidence_disk_delete_option: $dataDiskDeleteOption,
      disk_network_access_policy: $diskNetworkAccessPolicy,
      disk_public_network_access: $diskPublicNetworkAccess
    },
    guest_verification_output: $runCommandMessage
  }' >"$OUTPUT_PATH"

cat "$OUTPUT_PATH"
