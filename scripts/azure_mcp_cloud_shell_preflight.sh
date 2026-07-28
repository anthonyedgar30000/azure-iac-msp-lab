#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

readonly SCRIPT_VERSION="1.1.0"
readonly DEFAULT_TEMPLATE="azmcp-copilot-studio-aca-mi"
readonly DEFAULT_AZD_ENVIRONMENT_NAME="azmcp-preflight"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

need_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

fingerprint() {
  printf '%s' "$1" | sha256sum | awk '{print "sha256:" $1}'
}

for command_name in az azd jq sha256sum grep find sort awk sed xargs; do
  need_command "$command_name"
done

: "${AZURE_MCP_HOSTING_SUBSCRIPTION_ID:?Set AZURE_MCP_HOSTING_SUBSCRIPTION_ID to the exact hosting subscription UUID.}"
: "${AZURE_MCP_LOCATION:?Set AZURE_MCP_LOCATION to the proposed Azure region.}"
: "${AZURE_MCP_RESOURCE_GROUP:?Set AZURE_MCP_RESOURCE_GROUP to the proposed dedicated resource-group name.}"
: "${AZURE_MCP_TEMPLATE:=$DEFAULT_TEMPLATE}"
: "${AZURE_MCP_AZD_ENVIRONMENT_NAME:=$DEFAULT_AZD_ENVIRONMENT_NAME}"
: "${AZURE_MCP_WORKDIR:=$HOME/clouddrive/azure-mcp-preflight-$(date -u +%Y%m%dT%H%M%SZ)}"

[[ "$AZURE_MCP_HOSTING_SUBSCRIPTION_ID" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]] \
  || fail "hosting subscription ID is not a UUID"
[[ "$AZURE_MCP_LOCATION" =~ ^[a-z0-9]+$ ]] || fail "location contains unexpected characters"
[[ "$AZURE_MCP_RESOURCE_GROUP" =~ ^[A-Za-z0-9._()-]{1,90}$ ]] \
  || fail "resource-group name is invalid"
[[ "$AZURE_MCP_RESOURCE_GROUP" != *. ]] || fail "resource-group name must not end with a period"
[[ "$AZURE_MCP_AZD_ENVIRONMENT_NAME" =~ ^[a-z0-9-]{3,64}$ ]] \
  || fail "Azure Developer CLI environment name is invalid"

case "$AZURE_MCP_TEMPLATE" in
  azmcp-copilot-studio-aca-mi) ;;
  *) fail "template is not the selected managed-identity candidate" ;;
esac

umask 077
mkdir -p "$AZURE_MCP_WORKDIR/evidence" "$AZURE_MCP_WORKDIR/template"
evidence_dir="$AZURE_MCP_WORKDIR/evidence"
template_dir="$AZURE_MCP_WORKDIR/template"
observation_failures=0

az version > "$evidence_dir/azure-cli-version.json"
azd version > "$evidence_dir/azure-developer-cli-version.txt"

account_json="$(az account show --subscription "$AZURE_MCP_HOSTING_SUBSCRIPTION_ID" --output json)"
subscription_id="$(jq -r '.id' <<<"$account_json")"
subscription_name="$(jq -r '.name' <<<"$account_json")"
subscription_state="$(jq -r '.state' <<<"$account_json")"
tenant_id="$(jq -r '.tenantId' <<<"$account_json")"
principal_type="$(jq -r '.user.type // "unknown"' <<<"$account_json")"

[[ "$subscription_id" == "$AZURE_MCP_HOSTING_SUBSCRIPTION_ID" ]] \
  || fail "Azure CLI resolved a different subscription"
[[ "$subscription_state" == "Enabled" ]] || fail "hosting subscription is not enabled"

location_match="$(
  az account list-locations \
    --subscription "$subscription_id" \
    --query "[?name=='$AZURE_MCP_LOCATION'].name | [0]" \
    --output tsv
)"
[[ "$location_match" == "$AZURE_MCP_LOCATION" ]] \
  || fail "location is not available in the subscription location catalog"

jq -n \
  --arg observed_at_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg script_version "$SCRIPT_VERSION" \
  --arg subscription_name "$subscription_name" \
  --arg subscription_fingerprint "$(fingerprint "$subscription_id")" \
  --arg tenant_fingerprint "$(fingerprint "$tenant_id")" \
  --arg principal_type "$principal_type" \
  --arg location "$AZURE_MCP_LOCATION" \
  --arg resource_group "$AZURE_MCP_RESOURCE_GROUP" \
  '{
    observed_at_utc:$observed_at_utc,
    script_version:$script_version,
    subscription_name:$subscription_name,
    subscription_fingerprint:$subscription_fingerprint,
    tenant_fingerprint:$tenant_fingerprint,
    principal_type:$principal_type,
    location:$location,
    resource_group:$resource_group,
    raw_identifiers_persisted:false
  }' > "$evidence_dir/account-context.json"

: > "$evidence_dir/provider-states.jsonl"
for provider in \
  Microsoft.App \
  Microsoft.OperationalInsights \
  Microsoft.Insights \
  Microsoft.ManagedIdentity \
  Microsoft.Authorization
do
  provider_stderr="$AZURE_MCP_WORKDIR/provider-stderr.tmp"
  set +e
  provider_json="$(
    az provider show \
      --subscription "$subscription_id" \
      --namespace "$provider" \
      --output json \
      2>"$provider_stderr"
  )"
  provider_status=$?
  set -e

  if (( provider_status == 0 )); then
    jq -n \
      --arg namespace "$provider" \
      --arg registration_state "$(jq -r '.registrationState' <<<"$provider_json")" \
      '{namespace:$namespace,observation_status:"observed",registration_state:$registration_state}' \
      >> "$evidence_dir/provider-states.jsonl"
  else
    observation_failures=$((observation_failures + 1))
    jq -n \
      --arg namespace "$provider" \
      --argjson exit_status "$provider_status" \
      '{
        namespace:$namespace,
        observation_status:"observation_failed",
        exit_status:$exit_status,
        registration_state:null,
        stderr_persisted:false
      }' >> "$evidence_dir/provider-states.jsonl"
  fi
  rm -f "$provider_stderr"
done
jq -s '.' "$evidence_dir/provider-states.jsonl" > "$evidence_dir/provider-states.json"
rm "$evidence_dir/provider-states.jsonl"

group_stderr="$AZURE_MCP_WORKDIR/resource-group-stderr.tmp"
set +e
az group show \
  --subscription "$subscription_id" \
  --name "$AZURE_MCP_RESOURCE_GROUP" \
  --output json \
  > "$AZURE_MCP_WORKDIR/resource-group.raw.json" \
  2> "$group_stderr"
group_status=$?
set -e

if (( group_status == 0 )); then
  jq '{
    observation_status:"observed",
    name:.name,
    location:.location,
    provisioning_state:.properties.provisioningState
  }' "$AZURE_MCP_WORKDIR/resource-group.raw.json" > "$evidence_dir/resource-group-state.json"

  resource_stderr="$AZURE_MCP_WORKDIR/resource-list-stderr.tmp"
  set +e
  az resource list \
    --subscription "$subscription_id" \
    --resource-group "$AZURE_MCP_RESOURCE_GROUP" \
    --query '[].{name:name,type:type,location:location}' \
    --output json \
    > "$evidence_dir/existing-resource-summary.json" \
    2> "$resource_stderr"
  resource_status=$?
  set -e

  if (( resource_status != 0 )); then
    observation_failures=$((observation_failures + 1))
    jq -n \
      --argjson exit_status "$resource_status" \
      '{
        observation_status:"observation_failed",
        exit_status:$exit_status,
        resources:null,
        stderr_persisted:false
      }' > "$evidence_dir/existing-resource-summary.json"
  fi
  rm -f "$resource_stderr"
elif grep -Eqi 'ResourceGroupNotFound|could not be found' "$group_stderr"; then
  jq -n \
    --arg name "$AZURE_MCP_RESOURCE_GROUP" \
    '{observation_status:"not_present",name:$name,resources:null}' \
    > "$evidence_dir/resource-group-state.json"
  jq -n '{observation_status:"not_applicable",resources:null}' \
    > "$evidence_dir/existing-resource-summary.json"
else
  observation_failures=$((observation_failures + 1))
  jq -n \
    --arg name "$AZURE_MCP_RESOURCE_GROUP" \
    --argjson exit_status "$group_status" \
    '{
      observation_status:"observation_failed",
      name:$name,
      exit_status:$exit_status,
      resources:null,
      stderr_persisted:false
    }' > "$evidence_dir/resource-group-state.json"
  jq -n '{observation_status:"not_observed",resources:null}' \
    > "$evidence_dir/existing-resource-summary.json"
fi
rm -f "$AZURE_MCP_WORKDIR/resource-group.raw.json" "$group_stderr"

[[ -z "$(find "$template_dir" -mindepth 1 -maxdepth 1 -print -quit)" ]] \
  || fail "template directory is not empty"

(
  cd "$template_dir"
  AZD_NON_INTERACTIVE=true \
  AZD_SKIP_FIRST_RUN=true \
  azd init \
    --template "$AZURE_MCP_TEMPLATE" \
    --environment "$AZURE_MCP_AZD_ENVIRONMENT_NAME" \
    --no-prompt
)

(
  cd "$template_dir"
  find . -type f -not -path './.git/*' -print0 \
    | sort -z \
    | xargs -0 sha256sum
) > "$evidence_dir/template-files.sha256"

set +e
grep -RInE \
  'Mcp\.Tools\.ReadWrite|Microsoft\.Authorization/roleAssignments|roleAssignments|Microsoft\.Graph|app registration|managed identity|Subscription Reader|--namespace|--read-only|azd[[:space:]]+(up|provision|deploy|down)|az[[:space:]]+provider[[:space:]]+register|az[[:space:]]+role[[:space:]]+assignment' \
  "$template_dir" \
  > "$evidence_dir/template-risk-scan.txt"
risk_scan_status=$?
set -e
if (( risk_scan_status > 1 )); then
  fail "template risk scan failed"
fi

template_manifest_digest="$(
  sha256sum "$evidence_dir/template-files.sha256" | awk '{print "sha256:" $1}'
)"

preflight_status="passed"
if (( observation_failures > 0 )); then
  preflight_status="observation_failed"
fi

jq -n \
  --arg observed_at_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg workdir "$AZURE_MCP_WORKDIR" \
  --arg template "$AZURE_MCP_TEMPLATE" \
  --arg azd_environment_name "$AZURE_MCP_AZD_ENVIRONMENT_NAME" \
  --arg template_manifest_digest "$template_manifest_digest" \
  --arg preflight_status "$preflight_status" \
  --argjson observation_failures "$observation_failures" \
  '{
    observed_at_utc:$observed_at_utc,
    workdir:$workdir,
    template:$template,
    template_reference_kind:"azure_developer_cli_gallery_alias",
    template_source_pinned:false,
    azd_environment_name:$azd_environment_name,
    template_manifest_digest:$template_manifest_digest,
    preflight_status:$preflight_status,
    observation_failures:$observation_failures,
    azure_authentication_performed:true,
    azure_mutations_authorized:false,
    azure_mutations_performed:false,
    deployment_authorized:false,
    deployment_performed:false,
    openai_api_execution_performed:false,
    next_gate:"review_and_pin_template_identity_rbac_namespace_image_cost_quota_and_exact_digest"
  }' > "$evidence_dir/preflight-summary.json"

if (( observation_failures > 0 )); then
  fail "one or more Azure observations failed; inspect the protected evidence artifact"
fi

printf '\nRead-only preflight completed.\n'
printf 'Evidence directory: %s\n' "$evidence_dir"
printf 'Template directory: %s\n' "$template_dir"
printf 'STOP: review the evidence and template before any Azure provisioning command.\n'
