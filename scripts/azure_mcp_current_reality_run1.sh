#!/usr/bin/env bash
set -euo pipefail

readonly ATTEMPT_ID="azure-mcp-current-reality-run1"
readonly EXPECTED_SUBSCRIPTION_NAME="Azure for Students"
readonly EXPECTED_RESOURCE_GROUP="rg-ai-msp-dev-eastus"
readonly EXPECTED_RESOURCE_GROUP_LOCATION="eastus"
readonly RECEIPT_PATH="/tmp/${ATTEMPT_ID}.json"
readonly MANIFEST_PATH="/tmp/${ATTEMPT_ID}.sha256"
readonly CONSUMPTION_MARKER="${HOME}/.${ATTEMPT_ID}.consumed"
readonly VENV_DIR="${HOME}/.azure-mcp-reality-run1-venv"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command is unavailable: $1"
}

require_command az
require_command git
require_command python3
require_command sha256sum

[[ -n "${AZURE_MCP_RUN1_SUBSCRIPTION_ID:-}" ]] \
  || fail "AZURE_MCP_RUN1_SUBSCRIPTION_ID is required"
[[ "$AZURE_MCP_RUN1_SUBSCRIPTION_ID" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]] \
  || fail "AZURE_MCP_RUN1_SUBSCRIPTION_ID must be an exact UUID"

[[ -n "${AZURE_MCP_RUN1_REVIEWED_COMMIT:-}" ]] \
  || fail "AZURE_MCP_RUN1_REVIEWED_COMMIT is required"
[[ "$AZURE_MCP_RUN1_REVIEWED_COMMIT" =~ ^[0-9a-f]{40}$ ]] \
  || fail "AZURE_MCP_RUN1_REVIEWED_COMMIT must be a lowercase 40-character commit"

readonly EXPECTED_CONFIRMATION="OBSERVE-AZURE-MCP-RUN1:${EXPECTED_SUBSCRIPTION_NAME}:${EXPECTED_RESOURCE_GROUP}:${AZURE_MCP_RUN1_REVIEWED_COMMIT}"
[[ "${AZURE_MCP_RUN1_CONFIRMATION:-}" == "$EXPECTED_CONFIRMATION" ]] \
  || fail "confirmation must exactly equal: ${EXPECTED_CONFIRMATION}"

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" \
  || fail "run from inside the azure-iac-msp-lab repository"
cd "$repo_root"

actual_commit="$(git rev-parse HEAD)"
[[ "$actual_commit" == "$AZURE_MCP_RUN1_REVIEWED_COMMIT" ]] \
  || fail "repository HEAD does not match the reviewed commit"

[[ ! -e "$CONSUMPTION_MARKER" ]] \
  || fail "the one-attempt authorization has already been consumed on this Cloud Shell home"

# Select the exact operator-supplied subscription in local Azure CLI state. This
# changes only the client context and does not mutate an Azure resource.
az account set --subscription "$AZURE_MCP_RUN1_SUBSCRIPTION_ID"
account_json="$(az account show --output json --only-show-errors)"

ACCOUNT_JSON="$account_json" \
EXPECTED_ID="$AZURE_MCP_RUN1_SUBSCRIPTION_ID" \
EXPECTED_NAME="$EXPECTED_SUBSCRIPTION_NAME" \
python3 - <<'PY'
import json
import os

account = json.loads(os.environ["ACCOUNT_JSON"])
expected_id = os.environ["EXPECTED_ID"].lower()
actual_id = str(account.get("id", "")).lower()
if actual_id != expected_id:
    raise SystemExit("active Azure subscription ID does not match the explicit run scope")
if account.get("name") != os.environ["EXPECTED_NAME"]:
    raise SystemExit("active Azure subscription name is not Azure for Students")
if str(account.get("state", "")).lower() != "enabled":
    raise SystemExit("active Azure subscription is not enabled")
if not account.get("tenantId"):
    raise SystemExit("Azure tenant identity was not returned")
PY

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/python" -m pip install --disable-pip-version-check \
  -r requirements/azure-mcp-reality-tool.txt

# The attempt becomes consumed immediately before the bounded Azure resource
# observation begins. Any later failure requires new human authorization.
(
  set -o noclobber
  printf '%s\n' \
    "attempt_id=${ATTEMPT_ID}" \
    "consumed_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    "reviewed_commit=${AZURE_MCP_RUN1_REVIEWED_COMMIT}" \
    "subscription_name=${EXPECTED_SUBSCRIPTION_NAME}" \
    "resource_group=${EXPECTED_RESOURCE_GROUP}" \
    > "$CONSUMPTION_MARKER"
) 2>/dev/null || fail "could not atomically claim the one-attempt authorization"

cleanup_env() {
  unset AZURE_MCP_ALLOWED_SUBSCRIPTION_ID || true
  unset AZURE_MCP_ALLOWED_RESOURCE_GROUP || true
  unset AZURE_MCP_REPOSITORY_ROOT || true
}
trap cleanup_env EXIT

export AZURE_MCP_ALLOWED_SUBSCRIPTION_ID="$AZURE_MCP_RUN1_SUBSCRIPTION_ID"
export AZURE_MCP_ALLOWED_RESOURCE_GROUP="$EXPECTED_RESOURCE_GROUP"
export AZURE_MCP_REPOSITORY_ROOT="$repo_root"

"$VENV_DIR/bin/python" -m azure_mcp_reality.cli > "$RECEIPT_PATH"

# Use validation-only environment names that cannot collide with readonly shell
# variables. Run 1 originally wrote the receipt successfully and then failed here
# because an environment-prefix assignment reused RECEIPT_PATH.
RUN1_RECEIPT_PATH="$RECEIPT_PATH" \
RUN1_EXPECTED_COMMIT="$AZURE_MCP_RUN1_REVIEWED_COMMIT" \
RUN1_EXPECTED_SUBSCRIPTION_NAME="$EXPECTED_SUBSCRIPTION_NAME" \
RUN1_EXPECTED_RESOURCE_GROUP="$EXPECTED_RESOURCE_GROUP" \
RUN1_EXPECTED_LOCATION="$EXPECTED_RESOURCE_GROUP_LOCATION" \
python3 - <<'PY'
import json
import os
from pathlib import Path

receipt = json.loads(
    Path(os.environ["RUN1_RECEIPT_PATH"]).read_text(encoding="utf-8")
)
status = receipt.get("observation_status")
if status not in {"observed", "not_present"}:
    raise SystemExit(f"unexpected observation status: {status}")
if receipt.get("mutations_performed") is not False:
    raise SystemExit("receipt does not prove zero Azure mutations")
if receipt.get("secrets_returned") is not False:
    raise SystemExit("receipt does not prove zero secret values")
if receipt.get("repository", {}).get("head") != os.environ["RUN1_EXPECTED_COMMIT"]:
    raise SystemExit("receipt repository head differs from the reviewed commit")
if receipt.get("scope", {}).get("subscription_name") != os.environ["RUN1_EXPECTED_SUBSCRIPTION_NAME"]:
    raise SystemExit("receipt subscription name differs from the authorized scope")
if receipt.get("scope", {}).get("resource_group") != os.environ["RUN1_EXPECTED_RESOURCE_GROUP"]:
    raise SystemExit("receipt resource group differs from the authorized scope")
if not str(receipt.get("raw_evidence_digest", "")).startswith("sha256:"):
    raise SystemExit("receipt evidence digest is missing")
if status == "observed":
    group = receipt.get("azure", {}).get("resource_group") or {}
    if group.get("name") != os.environ["RUN1_EXPECTED_RESOURCE_GROUP"]:
        raise SystemExit("observed resource-group name widened unexpectedly")
    if str(group.get("location", "")).lower() != os.environ["RUN1_EXPECTED_LOCATION"]:
        raise SystemExit("observed resource-group location differs from eastus")
PY

sha256sum "$RECEIPT_PATH" > "$MANIFEST_PATH"

printf 'Azure MCP current-reality run 1 completed.\n'
printf 'Receipt: %s\n' "$RECEIPT_PATH"
printf 'Manifest: %s\n' "$MANIFEST_PATH"
python3 - <<PY
import json
from pathlib import Path
receipt = json.loads(Path("$RECEIPT_PATH").read_text(encoding="utf-8"))
print("Observation status:", receipt["observation_status"])
print("Evidence digest:", receipt["raw_evidence_digest"])
print("Resource count:", receipt["azure"]["resource_count"])
PY
