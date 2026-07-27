#!/usr/bin/env bash
set -Eeuo pipefail

SERVICE_NAME="servicetracer-demo-backend.service"
INSTALL_ROOT="/opt/servicetracer-demo"
CONFIG_ROOT="/etc/servicetracer-demo"
UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}"
BACKEND_PATH="${INSTALL_ROOT}/backend.py"
LISTENER_PORT="${LISTENER_PORT:-443}"
BACKEND_ID="${BACKEND_ID:-VPN-LOCAL}"
BACKEND_MODE="${BACKEND_MODE:-healthy}"
PROBE_COUNT="${PROBE_COUNT:-12}"
PROBE_HOLD_SECONDS="${PROBE_HOLD_SECONDS:-3}"
ENABLE_UFW="${ENABLE_UFW:-1}"
FORCE_FAILURE_AFTER_INSTALL="${FORCE_FAILURE_AFTER_INSTALL:-0}"

usage() {
  cat <<'EOF'
Usage: sudo ./install-and-test.sh /path/to/azure-iac-msp-lab

Environment overrides:
  BACKEND_ID=VPN-LOCAL
  BACKEND_MODE=healthy|radius-timeout
  LISTENER_PORT=443
  PROBE_COUNT=12
  PROBE_HOLD_SECONDS=3
  ENABLE_UFW=1|0
  FORCE_FAILURE_AFTER_INSTALL=1|0

The script renders the exact backend embedded in cloud-init, installs it into a
local Ubuntu 24.04 VM, validates systemd and HTTPS readiness, simulates shallow
TCP probes that send no TLS ClientHello, and rolls back automatically on error.
EOF
}

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 2
fi

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this script with sudo." >&2
  exit 2
fi

REPO_ROOT="$(realpath "$1")"
RENDERER="${REPO_ROOT}/tools/local-vm-vpn-backend/render_artifacts.py"
if [[ ! -f "${RENDERER}" ]]; then
  echo "Renderer not found: ${RENDERER}" >&2
  exit 2
fi

case "${BACKEND_MODE}" in
  healthy|radius-timeout) ;;
  *) echo "Unsupported BACKEND_MODE: ${BACKEND_MODE}" >&2; exit 2 ;;
esac

for command in python3 openssl curl systemctl ss ip sha256sum jq; do
  command -v "${command}" >/dev/null || {
    echo "Required command is missing: ${command}" >&2
    exit 2
  }
done

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
EVIDENCE_ROOT="/var/tmp/servicetracer-local-vm/${RUN_ID}"
RENDERED_DIR="${EVIDENCE_ROOT}/rendered"
BACKUP_DIR="${EVIDENCE_ROOT}/backup"
LOG_PATH="${EVIDENCE_ROOT}/checkpoints.log"
mkdir -p "${RENDERED_DIR}" "${BACKUP_DIR}"
chmod 0700 "${EVIDENCE_ROOT}" "${BACKUP_DIR}"
exec > >(tee -a "${LOG_PATH}") 2>&1

checkpoint() {
  printf 'CHECKPOINT %-34s %s\n' "$1" "$(date -u +%FT%TZ)"
}

fail() {
  printf 'CHECKPOINT-FAIL %-29s %s\n' "$1" "$(date -u +%FT%TZ)" >&2
  return 1
}

wait_until() {
  local name="$1"
  local attempts="$2"
  local delay="$3"
  shift 3
  local attempt

  for attempt in $(seq 1 "${attempts}"); do
    if "$@"; then
      checkpoint "${name}"
      return 0
    fi
    sleep "${delay}"
  done

  fail "${name}"
}

file_existed_backend=0
file_existed_unit=0
cert_existed=0
key_existed=0
rollback_required=0

rollback() {
  local rc=$?
  trap - ERR

  if [[ ${rollback_required} -eq 1 ]]; then
    checkpoint "rollback-start"

    if [[ ${file_existed_backend} -eq 1 ]]; then
      install -o root -g root -m 0755 "${BACKUP_DIR}/backend.py.before" "${BACKEND_PATH}"
    else
      rm -f "${BACKEND_PATH}"
    fi

    if [[ ${file_existed_unit} -eq 1 ]]; then
      install -o root -g root -m 0644 "${BACKUP_DIR}/service.before" "${UNIT_PATH}"
    else
      rm -f "${UNIT_PATH}"
    fi

    if [[ ${cert_existed} -eq 1 ]]; then
      install -o root -g root -m 0644 "${BACKUP_DIR}/backend.crt.before" "${CONFIG_ROOT}/backend.crt"
    else
      rm -f "${CONFIG_ROOT}/backend.crt"
    fi

    if [[ ${key_existed} -eq 1 ]]; then
      install -o root -g root -m 0600 "${BACKUP_DIR}/backend.key.before" "${CONFIG_ROOT}/backend.key"
    else
      rm -f "${CONFIG_ROOT}/backend.key"
    fi

    systemctl daemon-reload || true
    if [[ ${file_existed_unit} -eq 1 ]]; then
      systemctl restart "${SERVICE_NAME}" || true
    else
      systemctl disable --now "${SERVICE_NAME}" >/dev/null 2>&1 || true
      systemctl reset-failed "${SERVICE_NAME}" >/dev/null 2>&1 || true
    fi

    checkpoint "rollback-complete"
    printf 'SERVICETRACER_LOCAL_ROLLBACK_PERFORMED run=%s rc=%s evidence=%s\n' \
      "${RUN_ID}" "${rc}" "${EVIDENCE_ROOT}" >&2
  fi

  exit "${rc}"
}
trap rollback ERR

checkpoint "host-observation"
{
  echo "run_id=${RUN_ID}"
  echo "repo_root=${REPO_ROOT}"
  echo "kernel=$(uname -srmo)"
  echo "os_release=$(source /etc/os-release && printf '%s %s' "${NAME}" "${VERSION_ID}")"
  echo "python=$(python3 --version 2>&1)"
  echo "openssl=$(openssl version)"
  echo "systemd=$(systemctl --version | head -n 1)"
} | tee "${EVIDENCE_ROOT}/host-observation.txt"

if ! grep -q '^VERSION_ID="24\.04"' /etc/os-release; then
  echo "This harness expects Ubuntu 24.04 LTS to match the Azure image declaration." >&2
  exit 2
fi

PRIVATE_IP="$(ip -4 route get 1.1.1.1 | awk '{for (i=1;i<=NF;i++) if ($i=="src") {print $(i+1); exit}}')"
if [[ -z "${PRIVATE_IP}" ]]; then
  PRIVATE_IP="$(hostname -I | awk '{print $1}')"
fi
[[ -n "${PRIVATE_IP}" ]] || fail "resolve-private-ip"
printf 'private_ip=%s\n' "${PRIVATE_IP}" | tee "${EVIDENCE_ROOT}/network.txt"

checkpoint "render-exact-artifacts"
python3 "${RENDERER}" \
  --repo-root "${REPO_ROOT}" \
  --output-dir "${RENDERED_DIR}" \
  --backend-id "${BACKEND_ID}" \
  --mode "${BACKEND_MODE}" \
  --listener-port "${LISTENER_PORT}" \
  | tee "${EVIDENCE_ROOT}/render-output.json"
python3 -m py_compile "${RENDERED_DIR}/backend.py"

install -d -m 0755 "${INSTALL_ROOT}" "${CONFIG_ROOT}"

if [[ -f "${BACKEND_PATH}" ]]; then
  file_existed_backend=1
  cp -a "${BACKEND_PATH}" "${BACKUP_DIR}/backend.py.before"
fi
if [[ -f "${UNIT_PATH}" ]]; then
  file_existed_unit=1
  cp -a "${UNIT_PATH}" "${BACKUP_DIR}/service.before"
fi
if [[ -f "${CONFIG_ROOT}/backend.crt" ]]; then
  cert_existed=1
  cp -a "${CONFIG_ROOT}/backend.crt" "${BACKUP_DIR}/backend.crt.before"
fi
if [[ -f "${CONFIG_ROOT}/backend.key" ]]; then
  key_existed=1
  cp -a "${CONFIG_ROOT}/backend.key" "${BACKUP_DIR}/backend.key.before"
fi
rollback_required=1

checkpoint "generate-local-certificate"
cat > "${EVIDENCE_ROOT}/openssl.cnf" <<EOF
[req]
distinguished_name = dn
x509_extensions = v3_req
prompt = no

[dn]
CN = ${BACKEND_ID}

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = ${BACKEND_ID}
IP.1 = 127.0.0.1
IP.2 = ${PRIVATE_IP}
EOF
openssl req -x509 -newkey rsa:2048 -nodes -days 7 \
  -keyout "${EVIDENCE_ROOT}/backend.key.new" \
  -out "${EVIDENCE_ROOT}/backend.crt.new" \
  -config "${EVIDENCE_ROOT}/openssl.cnf" >/dev/null 2>&1

checkpoint "install-rendered-artifacts"
install -o root -g root -m 0755 "${RENDERED_DIR}/backend.py" "${BACKEND_PATH}"
install -o root -g root -m 0644 "${RENDERED_DIR}/${SERVICE_NAME}" "${UNIT_PATH}"
install -o root -g root -m 0644 "${EVIDENCE_ROOT}/backend.crt.new" "${CONFIG_ROOT}/backend.crt"
install -o root -g root -m 0600 "${EVIDENCE_ROOT}/backend.key.new" "${CONFIG_ROOT}/backend.key"
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}" >/dev/null
systemctl restart "${SERVICE_NAME}"

if [[ "${ENABLE_UFW}" == "1" ]]; then
  checkpoint "configure-local-ufw"
  command -v ufw >/dev/null || fail "ufw-command-present"
  ufw default deny incoming >/dev/null
  ufw default allow outgoing >/dev/null
  ufw allow 22/tcp comment 'Local VM management' >/dev/null
  ufw allow "${LISTENER_PORT}/tcp" comment 'ServiceTracer local HTTPS' >/dev/null
  ufw --force enable >/dev/null
fi

service_active() {
  systemctl is-active --quiet "${SERVICE_NAME}"
}
listener_present() {
  ss -lnt "( sport = :${LISTENER_PORT} )" | grep -F ":${LISTENER_PORT}" >/dev/null
}
health_payload_matches() {
  local url="$1"
  local payload
  payload="$(curl -kfsS --connect-timeout 1 --max-time 3 "${url}")" || return 1
  python3 - "${payload}" "${BACKEND_ID}" "${BACKEND_MODE}" <<'PY'
import json
import sys
payload = json.loads(sys.argv[1])
assert payload["backend"] == sys.argv[2]
assert payload["listener"] == "available"
assert payload["mode"] == sys.argv[3]
PY
}
loopback_health() {
  health_payload_matches "https://127.0.0.1:${LISTENER_PORT}/healthz"
}
private_ip_health() {
  health_payload_matches "https://${PRIVATE_IP}:${LISTENER_PORT}/healthz"
}

wait_until "service-active" 20 0.5 service_active
wait_until "listener-present" 20 0.5 listener_present
wait_until "loopback-health" 20 0.5 loopback_health
wait_until "private-ip-health" 20 0.5 private_ip_health
systemctl is-enabled --quiet "${SERVICE_NAME}" || fail "service-enabled"
checkpoint "service-enabled"

if [[ "${ENABLE_UFW}" == "1" ]]; then
  ufw status | grep -F 'Status: active' >/dev/null || fail "ufw-active"
  ufw status | grep -F "${LISTENER_PORT}/tcp" >/dev/null || fail "ufw-listener-allowed"
  checkpoint "ufw-active-and-listener-allowed"
fi

checkpoint "rendered-hashes-match-installed"
python3 - "${RENDERED_DIR}/rendered-artifacts.json" "${BACKEND_PATH}" "${UNIT_PATH}" <<'PY'
import hashlib
import json
import pathlib
import sys

def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()

metadata = json.loads(pathlib.Path(sys.argv[1]).read_text())
actual_backend = sha256(pathlib.Path(sys.argv[2]))
actual_unit = sha256(pathlib.Path(sys.argv[3]))
assert actual_backend == metadata["files"]["backend.py"]["sha256"]
assert actual_unit == metadata["files"]["servicetracer-demo-backend.service"]["sha256"]
PY

cat > "${EVIDENCE_ROOT}/hold_raw_probes.py" <<'PY'
import socket
import sys
import time

host = sys.argv[1]
port = int(sys.argv[2])
count = int(sys.argv[3])
hold_seconds = float(sys.argv[4])
sockets = []
try:
    for _ in range(count):
        connection = socket.create_connection((host, port), timeout=2.0)
        sockets.append(connection)
    print(f"RAW_PROBES_CONNECTED count={len(sockets)}", flush=True)
    time.sleep(hold_seconds)
finally:
    for connection in sockets:
        connection.close()
PY

checkpoint "start-shallow-probe-simulation"
python3 "${EVIDENCE_ROOT}/hold_raw_probes.py" \
  127.0.0.1 "${LISTENER_PORT}" "${PROBE_COUNT}" "${PROBE_HOLD_SECONDS}" \
  > "${EVIDENCE_ROOT}/raw-probes.log" 2>&1 &
RAW_PROBE_PID=$!
for _ in $(seq 1 20); do
  grep -F 'RAW_PROBES_CONNECTED' "${EVIDENCE_ROOT}/raw-probes.log" >/dev/null 2>&1 && break
  sleep 0.1
done
grep -F "RAW_PROBES_CONNECTED count=${PROBE_COUNT}" "${EVIDENCE_ROOT}/raw-probes.log" >/dev/null \
  || fail "raw-probes-connected"
checkpoint "raw-probes-connected"

health_payload_matches "https://127.0.0.1:${LISTENER_PORT}/healthz" \
  || fail "https-survives-raw-probes"
checkpoint "https-survives-raw-probes"

read -r recvq backlog < <(
  ss -lnt "( sport = :${LISTENER_PORT} )" | awk 'NR == 2 {print $2, $3}'
)
[[ "${recvq}" =~ ^[0-9]+$ && "${backlog}" =~ ^[0-9]+$ ]] || fail "listener-queue-readable"
(( recvq < backlog )) || fail "listener-queue-below-backlog"
printf 'listener_recvq=%s listener_backlog=%s\n' "${recvq}" "${backlog}" \
  | tee "${EVIDENCE_ROOT}/listener-queue.txt"
checkpoint "listener-queue-below-backlog"

ps -eLf | grep '[b]ackend.py' | tee "${EVIDENCE_ROOT}/backend-threads.txt"
ss -lntp "( sport = :${LISTENER_PORT} )" | tee "${EVIDENCE_ROOT}/listener.txt"
wait "${RAW_PROBE_PID}"
checkpoint "shallow-probe-simulation-complete"

if [[ "${FORCE_FAILURE_AFTER_INSTALL}" == "1" ]]; then
  fail "forced-failure-for-rollback-test"
fi

journalctl -u "${SERVICE_NAME}" --since '-10 minutes' --no-pager \
  > "${EVIDENCE_ROOT}/service-journal.txt"
sha256sum "${BACKEND_PATH}" "${UNIT_PATH}" \
  > "${EVIDENCE_ROOT}/installed-sha256.txt"
systemctl show "${SERVICE_NAME}" \
  -p ActiveState -p SubState -p UnitFileState -p ExecMainPID -p ExecMainStatus \
  > "${EVIDENCE_ROOT}/systemd-state.txt"

rollback_required=0
trap - ERR
checkpoint "local-vm-validation-complete"
printf 'SERVICETRACER_LOCAL_VALIDATION_SUCCESS run=%s evidence=%s\n' \
  "${RUN_ID}" "${EVIDENCE_ROOT}"
