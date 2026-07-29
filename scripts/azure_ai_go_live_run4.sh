#!/usr/bin/env bash
set -euo pipefail

SOURCE_SCRIPT="scripts/azure_ai_go_live_run2.sh"
EXPECTED_SOURCE_BLOB="33b5ef111cb4f7b73e2978e9371e59fe9295274b"
RUNTIME_SCRIPT="${RUNNER_TEMP}/azure_ai_go_live_run4.runtime.sh"

# Run 4 reuses the exact repaired executor, changes the attempt identity, and
# narrows the candidate loop to West US 2 only. The blob assertion prevents
# silent execution if the reviewed source moves.
test "$(git hash-object "$SOURCE_SCRIPT")" = "$EXPECTED_SOURCE_BLOB"

sed \
  -e 's/azure-ai-go-live-run2/azure-ai-go-live-run4/g' \
  -e 's/azure-ai-live-run2/azure-ai-live-run4/g' \
  -e 's/for location in canadaeast eastus2; do/for location in westus2; do/' \
  "$SOURCE_SCRIPT" > "$RUNTIME_SCRIPT"

grep -F 'for location in westus2; do' "$RUNTIME_SCRIPT" >/dev/null
if grep -Eq 'for location in (canadaeast|eastus2)|rg-ai-msp-dev-(canadaeast|eastus2)' "$RUNTIME_SCRIPT"; then
  echo "Run 4 contains an unauthorized regional candidate." >&2
  exit 1
fi

bash -n "$RUNTIME_SCRIPT"
exec bash "$RUNTIME_SCRIPT"
