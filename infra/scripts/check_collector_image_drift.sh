#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check_collector_image_drift.sh \
  --mode guard|plan \
  --resource-group NAME \
  --prefix PREFIX \
  --environment dev|test \
  --desired-image-file PATH \
  --artifact-dir PATH \
  [--github-output PATH]

The script is read-only. It detects immutable collector image drift and, in
plan mode, captures a bounded replacement plan. It never deletes, detaches,
snapshots, creates, or updates Azure resources.
EOF
}

MODE='guard'
RESOURCE_GROUP=''
PREFIX=''
LAB_ENVIRONMENT=''
DESIRED_IMAGE_FILE=''
ARTIFACT_DIR=''
GITHUB_OUTPUT_PATH=''

while (($#)); do
  case "$1" in
    --mode) MODE="$2"; shift 2 ;;
    --resource-group) RESOURCE_GROUP="$2"; shift 2 ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    --environment) LAB_ENVIRONMENT="$2"; shift 2 ;;
    --desired-image-file) DESIRED_IMAGE_FILE="$2"; shift 2 ;;
    --artifact-dir) ARTIFACT_DIR="$2"; shift 2 ;;
    --github-output) GITHUB_OUTPUT_PATH="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

for required in RESOURCE_GROUP PREFIX LAB_ENVIRONMENT DESIRED_IMAGE_FILE ARTIFACT_DIR; do
  [[ -n "${!required}" ]] || {
    echo "Missing required value: $required" >&2
    exit 2
  }
done

[[ "$MODE" =~ ^(guard|plan)$ ]]
[[ "$LAB_ENVIRONMENT" =~ ^(dev|test)$ ]]
[[ "$PREFIX" =~ ^[a-z0-9]{2,12}$ ]]
[[ -f "$DESIRED_IMAGE_FILE" ]]
mkdir -p "$ARTIFACT_DIR"

jq -e '
  type == "object" and
  (.publisher | type == "string" and length > 0) and
  (.offer | type == "string" and length > 0) and
  (.sku | type == "string" and length > 0) and
  (.version | type == "string" and length > 0)
' "$DESIRED_IMAGE_FILE" >/dev/null

vm_name="vm-stcollector-${PREFIX}-${LAB_ENVIRONMENT}"
nic_name="nic-stcollector-${PREFIX}-${LAB_ENVIRONMENT}"
os_disk_name="disk-stcollector-os-${PREFIX}-${LAB_ENVIRONMENT}"
evidence_disk_name="disk-stcollector-evidence-${PREFIX}-${LAB_ENVIRONMENT}"
current_vm_file="$ARTIFACT_DIR/collector-current-vm.json"
current_vm_error="$ARTIFACT_DIR/collector-current-vm.stderr"
status_file="$ARTIFACT_DIR/collector-image-drift.json"
plan_file="$ARTIFACT_DIR/collector-replacement-plan.json"

vm_exists=false
if az vm show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$vm_name" \
  --output json > "$current_vm_file" 2> "$current_vm_error"; then
  vm_exists=true
else
  if grep -Eqi 'ResourceNotFound|could not be found|was not found' "$current_vm_error"; then
    printf '{}\n' > "$current_vm_file"
  else
    cat "$current_vm_error" >&2
    echo 'Unable to inspect the existing collector VM; refusing to guess about image drift.' >&2
    exit 1
  fi
fi

current_image='null'
if [[ "$vm_exists" == true ]]; then
  current_image="$(jq -c '.storageProfile.imageReference // null' "$current_vm_file")"
fi
desired_image="$(jq -c '.' "$DESIRED_IMAGE_FILE")"

image_status='absent'
image_drift=false
if [[ "$vm_exists" == true ]]; then
  current_identity="$(jq -r '[.publisher,.offer,.sku] | map(ascii_downcase) | join("|")' <<<"$current_image")"
  desired_identity="$(jq -r '[.publisher,.offer,.sku] | map(ascii_downcase) | join("|")' <<<"$desired_image")"
  desired_version="$(jq -r '.version' <<<"$desired_image")"
  current_version="$(jq -r '.version // ""' <<<"$current_image")"

  if [[ "$current_identity" == "$desired_identity" ]] && \
     { [[ "$desired_version" == 'latest' ]] || [[ "$current_version" == "$desired_version" ]]; }; then
    image_status='compatible'
  else
    image_status='replacement_required'
    image_drift=true
  fi
fi

jq -n \
  --arg vmName "$vm_name" \
  --arg status "$image_status" \
  --argjson vmExists "$vm_exists" \
  --argjson drift "$image_drift" \
  --argjson currentImage "$current_image" \
  --argjson desiredImage "$desired_image" \
  '{
    schema_version:"servicetracer.collector-image-drift.v1",
    collector_vm:$vmName,
    vm_exists:$vmExists,
    status:$status,
    immutable_image_drift:$drift,
    current_image:$currentImage,
    desired_image:$desiredImage,
    comparison_rule:"publisher_offer_sku_and_pinned_version; desired latest accepts any deployed version of the same image line"
  }' > "$status_file"

if [[ -n "$GITHUB_OUTPUT_PATH" ]]; then
  printf 'collector_image_status=%s\n' "$image_status" >> "$GITHUB_OUTPUT_PATH"
  printf 'collector_image_drift=%s\n' "$image_drift" >> "$GITHUB_OUTPUT_PATH"
  printf 'collector_replacement_plan=%s\n' "$plan_file" >> "$GITHUB_OUTPUT_PATH"
fi

if [[ "$MODE" == 'plan' ]]; then
  nic_file="$ARTIFACT_DIR/collector-current-nic.json"
  os_disk_file="$ARTIFACT_DIR/collector-current-os-disk.json"
  evidence_disk_file="$ARTIFACT_DIR/collector-current-evidence-disk.json"
  roles_file="$ARTIFACT_DIR/collector-current-role-assignments.json"
  roles_error="$ARTIFACT_DIR/collector-current-role-assignments.stderr"

  if [[ "$vm_exists" == true ]]; then
    az network nic show --resource-group "$RESOURCE_GROUP" --name "$nic_name" --output json > "$nic_file"
    az disk show --resource-group "$RESOURCE_GROUP" --name "$os_disk_name" --output json > "$os_disk_file"
    az disk show --resource-group "$RESOURCE_GROUP" --name "$evidence_disk_name" --output json > "$evidence_disk_file"

    principal_id="$(jq -r '.identity.principalId // empty' "$current_vm_file")"
    if [[ -n "$principal_id" ]]; then
      if ! az role assignment list --assignee-object-id "$principal_id" --all --output json > "$roles_file" 2> "$roles_error"; then
        printf '[]\n' > "$roles_file"
      fi
    else
      printf '[]\n' > "$roles_file"
    fi
  else
    printf '{}\n' > "$nic_file"
    printf '{}\n' > "$os_disk_file"
    printf '{}\n' > "$evidence_disk_file"
    printf '[]\n' > "$roles_file"
  fi

  evidence_disk_id="$(jq -r '.id // empty' "$evidence_disk_file")"
  os_disk_id="$(jq -r '.id // empty' "$os_disk_file")"
  nic_id="$(jq -r '.id // empty' "$nic_file")"
  principal_id="$(jq -r '.identity.principalId // empty' "$current_vm_file")"
  confirmation_phrase="REPLACE:${RESOURCE_GROUP}:${vm_name}"

  jq -n \
    --arg resourceGroup "$RESOURCE_GROUP" \
    --arg vmName "$vm_name" \
    --arg nicName "$nic_name" \
    --arg osDiskName "$os_disk_name" \
    --arg evidenceDiskName "$evidence_disk_name" \
    --arg status "$image_status" \
    --argjson currentImage "$current_image" \
    --argjson desiredImage "$desired_image" \
    --arg nicId "$nic_id" \
    --arg osDiskId "$os_disk_id" \
    --arg evidenceDiskId "$evidence_disk_id" \
    --arg principalId "$principal_id" \
    --arg confirmation "$confirmation_phrase" \
    --slurpfile roleAssignments "$roles_file" \
    '{
      schema_version:"servicetracer.collector-replacement-plan.v1",
      operation:"plan_only",
      execution_authorized:false,
      execution_performed:false,
      azure_mutations_performed:false,
      collector:{
        resource_group:$resourceGroup,
        vm_name:$vmName,
        nic_name:$nicName,
        os_disk_name:$osDiskName,
        evidence_disk_name:$evidenceDiskName,
        current_principal_id:(if $principalId=="" then null else $principalId end)
      },
      image_assessment:{status:$status,current:$currentImage,desired:$desiredImage},
      preservation_boundary:{
        evidence_disk_id:(if $evidenceDiskId=="" then null else $evidenceDiskId end),
        evidence_disk_must_be_preserved:true,
        snapshot_or_backup_required_before_future_execution:true,
        nic_id:(if $nicId=="" then null else $nicId end),
        os_disk_id:(if $osDiskId=="" then null else $osDiskId end),
        role_assignments:($roleAssignments[0] // [])
      },
      future_authorized_sequence:[
        "verify collector service and evidence-disk mount before maintenance",
        "create and verify an evidence-disk recovery point",
        "record the current VM, NIC, OS disk, identity, and role assignments",
        "detach or otherwise protect the evidence disk",
        "replace only disposable collector compute components",
        "recreate the collector from the desired image contract",
        "reattach the preserved evidence disk and verify retained evidence",
        "reapply report-publication access to the new managed identity",
        "run collector verification and publish post-replacement evidence"
      ],
      future_exact_confirmation:$confirmation,
      note:"This plan contains no delete, detach, snapshot, create, or update execution. A separately reviewed and explicitly authorized implementation is required."
    }' > "$plan_file"

  exit 0
fi

if [[ "$image_status" == 'replacement_required' ]]; then
  echo "Collector $vm_name uses an immutable image different from infra/config/collector-image.json." >&2
  echo 'Ordinary What-If/Deploy is blocked. Run the plan-collector-replacement operation to capture a non-mutating migration plan.' >&2
  exit 42
fi

exit 0
