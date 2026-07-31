#!/usr/bin/env bash
set -euo pipefail

plan_dir="${1:?usage: verify_downloaded_plan_manifest.sh <downloaded-plan-directory>}"
manifest="$plan_dir/artifact-manifest.sha256"
normalized_manifest="$plan_dir/artifact-manifest.normalized.sha256"

[[ -s "$manifest" ]] || {
  echo "Accepted planning artifact manifest is missing: $manifest" >&2
  exit 1
}

# actions/download-artifact with merge-multiple flattens the uploaded artifact's
# root directory into plan_dir. The planner manifest intentionally records paths
# including its original evidence-directory prefix, so normalize only that known
# prefix before verifying the downloaded files.
sed -E 's#^([0-9a-f]{64}[[:space:]]+)servicetracer-demo-api-subproject-plan-evidence/#\1#' \
  "$manifest" > "$normalized_manifest"

if grep -q 'servicetracer-demo-api-subproject-plan-evidence/' "$normalized_manifest"; then
  echo "Planner manifest contains an unnormalized evidence-directory path" >&2
  exit 1
fi

(
  cd "$plan_dir"
  sha256sum --check "$(basename "$normalized_manifest")"
)
