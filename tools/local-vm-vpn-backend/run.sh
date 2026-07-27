#!/usr/bin/env bash
set -Eeuo pipefail

NAME="${NAME:-servicetracer-vpn-local}"
REPOSITORY="${REPOSITORY:-https://github.com/anthonyedgar30000/azure-iac-msp-lab.git}"
BRANCH="${BRANCH:-test/local-vm-vpn-backend}"
BACKEND_ID="${BACKEND_ID:-VPN-LOCAL}"
BACKEND_MODE="${BACKEND_MODE:-healthy}"
LISTENER_PORT="${LISTENER_PORT:-443}"
ENABLE_UFW="${ENABLE_UFW:-1}"
KEEP_EXISTING="${KEEP_EXISTING:-0}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CLOUD_INIT="${SCRIPT_DIR}/cloud-init.yaml"

command -v multipass >/dev/null || {
  echo "Multipass is not installed or is not on PATH." >&2
  exit 2
}
[[ -f "${CLOUD_INIT}" ]] || {
  echo "Cloud-init file not found: ${CLOUD_INIT}" >&2
  exit 2
}

if multipass info "${NAME}" >/dev/null 2>&1; then
  if [[ "${KEEP_EXISTING}" == "1" ]]; then
    multipass start "${NAME}" >/dev/null 2>&1 || true
  else
    echo "Deleting previous disposable instance: ${NAME}"
    multipass delete --purge "${NAME}"
  fi
fi

if ! multipass info "${NAME}" >/dev/null 2>&1; then
  echo "Launching Ubuntu 24.04 local validation VM: ${NAME}"
  multipass launch 24.04 \
    --name "${NAME}" \
    --cpus 1 \
    --memory 2G \
    --disk 12G \
    --cloud-init "${CLOUD_INIT}"
fi

multipass exec "${NAME}" -- cloud-init status --wait

printf -v guest_command '%q ' \
  env \
  "BACKEND_ID=${BACKEND_ID}" \
  "BACKEND_MODE=${BACKEND_MODE}" \
  "LISTENER_PORT=${LISTENER_PORT}" \
  "ENABLE_UFW=${ENABLE_UFW}" \
  bash /home/ubuntu/azure-iac-msp-lab/tools/local-vm-vpn-backend/install-and-test.sh \
  /home/ubuntu/azure-iac-msp-lab

multipass exec "${NAME}" -- bash -lc "
  set -Eeuo pipefail
  rm -rf /home/ubuntu/azure-iac-msp-lab
  git clone --quiet --branch '${BRANCH}' --single-branch '${REPOSITORY}' /home/ubuntu/azure-iac-msp-lab
  sudo ${guest_command}
" || {
  echo "Local VM validation failed. Recent evidence files:" >&2
  multipass exec "${NAME}" -- bash -lc \
    "sudo find /var/tmp/servicetracer-local-vm -maxdepth 2 -type f -printf '%TY-%Tm-%TdT%TH:%TM:%TSZ %p\\n' | sort | tail -n 40" \
    || true
  exit 1
}

echo "Local VM validation succeeded."
multipass info "${NAME}"
echo "Open a shell with: multipass shell ${NAME}"
echo "Evidence is under /var/tmp/servicetracer-local-vm/ inside the VM."
