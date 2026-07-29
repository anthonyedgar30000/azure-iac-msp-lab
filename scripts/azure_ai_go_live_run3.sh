#!/usr/bin/env bash
set -euo pipefail

SOURCE_SCRIPT="scripts/azure_ai_go_live_run2.sh"
EXPECTED_SOURCE_BLOB="33b5ef111cb4f7b73e2978e9371e59fe9295274b"
RUNTIME_SCRIPT="${RUNNER_TEMP}/azure_ai_go_live_run3.runtime.sh"

# Run 3 reuses the exact statically validated run-2 executor after the JSON-path
# repair. The Git blob assertion prevents silent execution if that source moves.
test "$(git hash-object "$SOURCE_SCRIPT")" = "$EXPECTED_SOURCE_BLOB"

sed \
  -e 's/azure-ai-go-live-run2/azure-ai-go-live-run3/g' \
  -e 's/azure-ai-live-run2/azure-ai-live-run3/g' \
  "$SOURCE_SCRIPT" > "$RUNTIME_SCRIPT"

bash -n "$RUNTIME_SCRIPT"
exec bash "$RUNTIME_SCRIPT"
