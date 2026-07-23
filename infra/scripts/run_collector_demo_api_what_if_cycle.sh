#!/usr/bin/env bash
set -euo pipefail
umask 0077

fail() {
  printf 'collector-demo-api scheduler: %s\n' "$1" >&2
  logger -t collector-demo-api-scheduler -- "failure: $1" 2>/dev/null || true
  exit "${2:-1}"
}

write_local_transition() {
  local next_message="$1"
  local failure_class="$2"
  local reason="$3"
  local output="$4"
  jq -n \
    --arg next_control_message "$next_message" \
    --arg failure_class "$failure_class" \
    --arg reason "$reason" \
    --arg reviewed_commit "$REVIEWED_COMMIT" \
    --arg generated_at "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    '{schema_version:"servicetracer.scheduler-local-transition.v1",next_control_message:$next_control_message,failure_class:$failure_class,reasons:[$reason],reviewed_commit:$reviewed_commit,human_gate_required:"explicit_human_review",azure_mutations_authorized:false,workflow_dispatch_authorized:false,automatic_execution_authorized:false,generated_at:$generated_at}' \
    > "$output"
}

CONFIG_FILE="${SCHEDULER_CONFIG:-/etc/azure-iac-msp-lab/collector-demo-api-scheduler.env}"
[[ -r "$CONFIG_FILE" ]] || fail "configuration is not readable: $CONFIG_FILE" 2
# shellcheck source=/dev/null
source "$CONFIG_FILE"

required_variables=(
  GH_TOKEN_FILE
  REPOSITORY
  DEFAULT_BRANCH
  REVIEWED_COMMIT
  RESOURCE_GROUP
  LOCATION
  LAB_ENVIRONMENT
  PREFIX
  DNS_LABEL
  ALLOWED_ORIGIN
)
for variable_name in "${required_variables[@]}"; do
  [[ -n "${!variable_name:-}" ]] || fail "missing required configuration: $variable_name" 2
done

[[ "$REPOSITORY" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || fail 'REPOSITORY must be owner/name' 2
[[ "$DEFAULT_BRANCH" =~ ^[A-Za-z0-9._/-]+$ ]] || fail 'DEFAULT_BRANCH is invalid' 2
[[ "$REVIEWED_COMMIT" =~ ^[0-9a-f]{40}$ ]] || fail 'REVIEWED_COMMIT must be a full lowercase commit SHA' 2
[[ "$RESOURCE_GROUP" =~ ^rg-servicetracer-(dev|test)(-[a-z0-9-]+)?$ ]] || fail 'RESOURCE_GROUP is outside the ServiceTracer contract' 2
[[ "$LOCATION" =~ ^[a-z0-9]+$ ]] || fail 'LOCATION is invalid' 2
[[ "$LAB_ENVIRONMENT" =~ ^(dev|test)$ ]] || fail 'LAB_ENVIRONMENT must be dev or test' 2
[[ "$PREFIX" =~ ^[a-z0-9]{2,12}$ ]] || fail 'PREFIX is invalid' 2
[[ "$DNS_LABEL" =~ ^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$ ]] || fail 'DNS_LABEL is invalid' 2
[[ "$ALLOWED_ORIGIN" =~ ^https://[A-Za-z0-9.-]+(:[0-9]+)?$ ]] || fail 'ALLOWED_ORIGIN must be an HTTPS origin without a path' 2

WORKFLOW_FILE="${WORKFLOW_FILE:-collector-demo-api.yml}"
RETRY_BUDGET="${RETRY_BUDGET:-1}"
POLL_INTERVAL_SECONDS="${POLL_INTERVAL_SECONDS:-10}"
RUN_DISCOVERY_ATTEMPTS="${RUN_DISCOVERY_ATTEMPTS:-30}"
RUN_COMPLETION_ATTEMPTS="${RUN_COMPLETION_ATTEMPTS:-540}"
STATE_ROOT="${STATE_ROOT:-/var/lib/azure-iac-msp-lab/scheduler/collector-demo-api}"
RAW_EVIDENCE_ROOT="${RAW_EVIDENCE_ROOT:-/var/lib/azure-iac-msp-lab/evidence/raw/collector-demo-api}"
SANITIZED_EVIDENCE_ROOT="${SANITIZED_EVIDENCE_ROOT:-/var/lib/azure-iac-msp-lab/evidence/sanitized/collector-demo-api}"
LOCK_FILE="${LOCK_FILE:-/run/lock/collector-demo-api-scheduler.lock}"

for numeric_name in RETRY_BUDGET POLL_INTERVAL_SECONDS RUN_DISCOVERY_ATTEMPTS RUN_COMPLETION_ATTEMPTS; do
  [[ "${!numeric_name}" =~ ^[0-9]+$ ]] || fail "$numeric_name must be a non-negative integer" 2
done
((POLL_INTERVAL_SECONDS >= 5)) || fail 'POLL_INTERVAL_SECONDS must be at least 5' 2
((RUN_DISCOVERY_ATTEMPTS >= 1)) || fail 'RUN_DISCOVERY_ATTEMPTS must be at least 1' 2
((RUN_COMPLETION_ATTEMPTS >= 1)) || fail 'RUN_COMPLETION_ATTEMPTS must be at least 1' 2

for command_name in gh jq python3 flock find sha256sum logger date mkdir cp dirname seq sleep stat; do
  command -v "$command_name" >/dev/null 2>&1 || fail "required command is unavailable: $command_name" 127
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
artifact_verifier="$repo_root/infra/scripts/verify_collector_demo_api_scheduler_artifact.py"
persistence_controller="$repo_root/infra/scripts/governed_persistence.py"
[[ -f "$artifact_verifier" ]] || fail "artifact verifier is missing: $artifact_verifier"
[[ -f "$persistence_controller" ]] || fail "persistence controller is missing: $persistence_controller"

mkdir -p "$STATE_ROOT" "$RAW_EVIDENCE_ROOT" "$SANITIZED_EVIDENCE_ROOT" "$(dirname "$LOCK_FILE")"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  logger -t collector-demo-api-scheduler -- 'another scheduler cycle holds the lock; exiting without dispatch' 2>/dev/null || true
  exit 0
fi

[[ -r "$GH_TOKEN_FILE" ]] || fail "GitHub token file is not readable: $GH_TOKEN_FILE" 2
token_mode="$(stat -c '%a' "$GH_TOKEN_FILE")"
[[ "$token_mode" =~ ^[0-7]{3,4}$ ]] || fail 'GitHub token file mode could not be validated' 2
other_permissions=$((10#$token_mode % 10))
((other_permissions == 0)) || fail 'GitHub token file must not be world-readable or world-writable' 2
GH_TOKEN="$(<"$GH_TOKEN_FILE")"
[[ -n "$GH_TOKEN" ]] || fail 'GitHub token file is empty' 2
export GH_TOKEN
export GH_PAGER=cat
export GH_PROMPT_DISABLED=1

current_main="$(gh api "repos/${REPOSITORY}/commits/${DEFAULT_BRANCH}" --jq '.sha')"
if [[ "$current_main" != "$REVIEWED_COMMIT" ]]; then
  transition="$SANITIZED_EVIDENCE_ROOT/stale-reviewed-commit-$(date -u +'%Y%m%dT%H%M%SZ').json"
  write_local_transition \
    'sync_with_reality' \
    'stale_or_uncertain_state' \
    "configured reviewed commit ${REVIEWED_COMMIT} differs from current ${DEFAULT_BRANCH} ${current_main}" \
    "$transition"
  cp "$transition" "$STATE_ROOT/latest-transition.json"
  logger -t collector-demo-api-scheduler -- "reviewed commit stale; configured=$REVIEWED_COMMIT current=$current_main" 2>/dev/null || true
  exit 20
fi

gh api "repos/${REPOSITORY}/contents/.github/workflows/${WORKFLOW_FILE}?ref=${REVIEWED_COMMIT}" --silent >/dev/null

state_file="$STATE_ROOT/state.json"
attempt_number=1
if [[ -s "$state_file" ]]; then
  previous_commit="$(jq -r '.reviewed_commit // empty' "$state_file")"
  previous_next="$(jq -r '.next_control_message // empty' "$state_file")"
  previous_operation="$(jq -r '.recommended_next_operation // empty' "$state_file")"
  previous_gate="$(jq -r '.human_gate_required // empty' "$state_file")"
  previous_terminal="$(jq -r '.terminal // false' "$state_file")"
  previous_attempt="$(jq -r '.attempt_number // 0' "$state_file")"

  if [[ "$previous_commit" == "$REVIEWED_COMMIT" ]]; then
    if [[ "$previous_terminal" == true || -n "$previous_gate" || "$previous_next" =~ ^(proceed|fix|restrategize|escalate|complete)$ ]]; then
      logger -t collector-demo-api-scheduler -- "same commit already evaluated; next=$previous_next gate=${previous_gate:-none}; no duplicate dispatch" 2>/dev/null || true
      exit 0
    fi
    if [[ "$previous_next" == 'sync_with_reality' && "$previous_operation" == 'what-if' ]]; then
      attempt_number=$((previous_attempt + 1))
    else
      logger -t collector-demo-api-scheduler -- "same commit has no authorized automatic continuation; next=$previous_next operation=$previous_operation" 2>/dev/null || true
      exit 0
    fi
  fi
fi

if ((attempt_number > RETRY_BUDGET + 1)); then
  transition="$SANITIZED_EVIDENCE_ROOT/retry-budget-exhausted-$(date -u +'%Y%m%dT%H%M%SZ').json"
  write_local_transition \
    'escalate' \
    'retry_budget_exhausted' \
    "read-only What-If retry budget exhausted for ${REVIEWED_COMMIT}" \
    "$transition"
  cp "$transition" "$STATE_ROOT/latest-transition.json"
  exit 30
fi

dispatched_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
confirmation="COLLECTOR-DEMO-API:what-if:${RESOURCE_GROUP}:${DNS_LABEL}"
preexisting_run_ids="$(gh run list \
  --repo "$REPOSITORY" \
  --workflow "$WORKFLOW_FILE" \
  --event workflow_dispatch \
  --branch "$DEFAULT_BRANCH" \
  --limit 50 \
  --json databaseId \
  | jq '[.[].databaseId]')"

gh workflow run "$WORKFLOW_FILE" \
  --repo "$REPOSITORY" \
  --ref "$DEFAULT_BRANCH" \
  -f operation=what-if \
  -f reviewed_commit="$REVIEWED_COMMIT" \
  -f environment="$LAB_ENVIRONMENT" \
  -f resource_group="$RESOURCE_GROUP" \
  -f location="$LOCATION" \
  -f prefix="$PREFIX" \
  -f dns_label="$DNS_LABEL" \
  -f allowed_origin="$ALLOWED_ORIGIN" \
  -f confirmation="$confirmation"

run_id=''
for _ in $(seq 1 "$RUN_DISCOVERY_ATTEMPTS"); do
  runs_json="$(gh run list \
    --repo "$REPOSITORY" \
    --workflow "$WORKFLOW_FILE" \
    --event workflow_dispatch \
    --branch "$DEFAULT_BRANCH" \
    --limit 20 \
    --json databaseId,headSha,createdAt,status,conclusion,url)"
  candidate_count="$(jq \
    --argjson before "$preexisting_run_ids" \
    --arg started "$dispatched_at" \
    '[.[] | select(.createdAt >= $started and (.databaseId as $id | ($before | index($id)) == null))] | length' \
    <<<"$runs_json")"
  if ((candidate_count > 1)); then
    fail 'multiple new workflow runs appeared after dispatch; ownership is ambiguous' 21
  fi
  run_id="$(jq -r \
    --argjson before "$preexisting_run_ids" \
    --arg started "$dispatched_at" \
    '[.[] | select(.createdAt >= $started and (.databaseId as $id | ($before | index($id)) == null))] | first | .databaseId // empty' \
    <<<"$runs_json")"
  [[ -n "$run_id" ]] && break
  sleep "$POLL_INTERVAL_SECONDS"
done
[[ -n "$run_id" ]] || fail 'dispatched workflow run could not be identified' 21

identified_run="$(gh run view "$run_id" --repo "$REPOSITORY" --json headSha,status,url)"
identified_head="$(jq -r '.headSha' <<<"$identified_run")"
if [[ "$identified_head" != "$REVIEWED_COMMIT" ]]; then
  gh run cancel "$run_id" --repo "$REPOSITORY" >/dev/null 2>&1 || true
  transition="$SANITIZED_EVIDENCE_ROOT/stale-dispatched-run-${run_id}.json"
  write_local_transition \
    'sync_with_reality' \
    'stale_or_uncertain_state' \
    "dispatched run ${run_id} resolved head ${identified_head}, not reviewed commit ${REVIEWED_COMMIT}; cancellation requested" \
    "$transition"
  cp "$transition" "$STATE_ROOT/latest-transition.json"
  exit 24
fi

raw_run_dir="$RAW_EVIDENCE_ROOT/$run_id"
sanitized_run_dir="$SANITIZED_EVIDENCE_ROOT/$run_id"
mkdir -p "$raw_run_dir" "$sanitized_run_dir"

run_json="$raw_run_dir/run.json"
completed=false
for _ in $(seq 1 "$RUN_COMPLETION_ATTEMPTS"); do
  gh run view "$run_id" \
    --repo "$REPOSITORY" \
    --json databaseId,workflowName,event,headSha,status,conclusion,createdAt,updatedAt,url \
    > "$run_json"
  status="$(jq -r '.status' "$run_json")"
  if [[ "$status" == 'completed' ]]; then
    completed=true
    break
  fi
  sleep "$POLL_INTERVAL_SECONDS"
done

if [[ "$completed" != true ]]; then
  transition="$sanitized_run_dir/governed-transition.json"
  write_local_transition \
    'escalate' \
    'boundary_reached' \
    "workflow run ${run_id} did not complete within the bounded polling window" \
    "$transition"
  jq -n \
    --arg reviewed_commit "$REVIEWED_COMMIT" \
    --arg run_id "$run_id" \
    --argjson attempt_number "$attempt_number" \
    --slurpfile transition "$transition" \
    '{reviewed_commit:$reviewed_commit,run_id:$run_id,attempt_number:$attempt_number} + $transition[0]' \
    > "$state_file"
  exit 31
fi

conclusion="$(jq -r '.conclusion // "failure"' "$run_json")"
[[ "$(jq -r '.headSha' "$run_json")" == "$REVIEWED_COMMIT" ]] || fail 'completed run head SHA differs from the reviewed commit' 22

artifact_download_dir="$raw_run_dir/artifact"
mkdir -p "$artifact_download_dir"
gh run download "$run_id" \
  --repo "$REPOSITORY" \
  --pattern "collector-demo-api-${run_id}-*" \
  --dir "$artifact_download_dir"

request_path="$(find "$artifact_download_dir" -type f -name request.json -print -quit)"
[[ -n "$request_path" ]] || fail 'downloaded artifact does not contain request.json' 23
artifact_dir="$(dirname "$request_path")"

artifact_verification="$sanitized_run_dir/artifact-verification.json"
if [[ "$conclusion" == 'success' ]]; then
  if ! python3 "$artifact_verifier" \
    --artifact-dir "$artifact_dir" \
    --expected-run-id "$run_id" \
    --expected-commit "$REVIEWED_COMMIT" \
    --expected-resource-group "$RESOURCE_GROUP" \
    --expected-location "$LOCATION" \
    --expected-environment "$LAB_ENVIRONMENT" \
    --expected-prefix "$PREFIX" \
    --expected-dns-label "$DNS_LABEL" \
    --expected-allowed-origin "$ALLOWED_ORIGIN" \
    --output "$artifact_verification"; then
    transition="$sanitized_run_dir/governed-transition.json"
    write_local_transition \
      'escalate' \
      'evidence_integrity_failure' \
      "workflow run ${run_id} succeeded but its artifact failed scheduler verification" \
      "$transition"
    jq -n \
      --arg reviewed_commit "$REVIEWED_COMMIT" \
      --arg run_id "$run_id" \
      --arg conclusion "$conclusion" \
      --argjson attempt_number "$attempt_number" \
      --slurpfile transition "$transition" \
      '{reviewed_commit:$reviewed_commit,run_id:$run_id,workflow_conclusion:$conclusion,attempt_number:$attempt_number} + $transition[0]' \
      > "$state_file"
    cp "$transition" "$STATE_ROOT/latest-transition.json"
    exit 32
  fi
else
  jq -n \
    --arg run_id "$run_id" \
    --arg reviewed_commit "$REVIEWED_COMMIT" \
    --arg conclusion "$conclusion" \
    '{schema_version:"servicetracer.collector-demo-api-scheduler-verification.v1",status:"workflow_not_successful_strict_artifact_acceptance_not_attempted",run_id:$run_id,reviewed_commit:$reviewed_commit,workflow_conclusion:$conclusion,azure_mutations_authorized:false,deployment_authorized:false}' \
    > "$artifact_verification"
fi

governed_transition="$sanitized_run_dir/governed-transition.json"
python3 "$persistence_controller" evaluate-collector-demo-api \
  --operation what-if \
  --workflow-conclusion "$conclusion" \
  --attempt-number "$attempt_number" \
  --retry-budget "$RETRY_BUDGET" \
  --artifact-dir "$artifact_dir" \
  --output "$governed_transition"

jq -n \
  --arg schema_version 'servicetracer.collector-demo-api-scheduler-state.v1' \
  --arg reviewed_commit "$REVIEWED_COMMIT" \
  --arg run_id "$run_id" \
  --arg dispatched_at "$dispatched_at" \
  --arg conclusion "$conclusion" \
  --argjson attempt_number "$attempt_number" \
  --slurpfile verification "$artifact_verification" \
  --slurpfile transition "$governed_transition" \
  '{schema_version:$schema_version,reviewed_commit:$reviewed_commit,run_id:$run_id,dispatched_at:$dispatched_at,workflow_conclusion:$conclusion,attempt_number:$attempt_number,artifact_verification:$verification[0]} + $transition[0]' \
  > "$state_file"
cp "$governed_transition" "$STATE_ROOT/latest-transition.json"

next_control="$(jq -r '.next_control_message' "$governed_transition")"
human_gate="$(jq -r '.human_gate_required // empty' "$governed_transition")"
logger -t collector-demo-api-scheduler -- "run=$run_id conclusion=$conclusion next=$next_control gate=${human_gate:-none} commit=$REVIEWED_COMMIT" 2>/dev/null || true

# The scheduler intentionally stops at every human gate. In particular, an
# accepted What-If yields proceed + explicit_deploy_authorization and no deploy.
exit 0
