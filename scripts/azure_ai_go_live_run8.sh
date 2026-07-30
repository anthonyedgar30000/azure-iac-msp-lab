#!/usr/bin/env bash
set -euo pipefail

: "${RUNNER_TEMP:?RUNNER_TEMP is required}"

SOURCE_EXECUTOR="scripts/azure_ai_go_live_run7.sh"
EXPECTED_SOURCE_BLOB="21261d6e563fc3a55eae8cb1dd9306e69cacae5a"
DERIVED_EXECUTOR="${RUNNER_TEMP}/azure_ai_go_live_run8_executor.sh"

actual_source_blob="$(git hash-object "$SOURCE_EXECUTOR")"
if [[ "$actual_source_blob" != "$EXPECTED_SOURCE_BLOB" ]]; then
  printf 'Refusing derivation: historical run-7 executor blob changed. expected=%s actual=%s\n' \
    "$EXPECTED_SOURCE_BLOB" "$actual_source_blob" >&2
  exit 1
fi

python - "$SOURCE_EXECUTOR" "$DERIVED_EXECUTOR" <<'PY'
from __future__ import annotations

from pathlib import Path
import re
import sys

source = Path(sys.argv[1])
target = Path(sys.argv[2])
text = source.read_text(encoding="utf-8")

text = text.replace("azure-ai-go-live-run7", "azure-ai-go-live-run8")
text = text.replace("run7", "run8")
text = text.replace("RUN 7", "RUN 8")
text = text.replace("Run 7", "Run 8")
text = text.replace("run 7", "run 8")
text = text.replace(
    'Proceed with Azure AI run 8 using the existing account and existing account-scoped inference role.',
    'Fix and proceed',
)

scope_all_pattern = re.compile(
    r'(?m)(^\s+--scope "\$account_id" \\\n)\s+--all \\\n'
)
text, repair_count = scope_all_pattern.subn(r"\1", text)
if repair_count != 3:
    raise SystemExit(
        f"Refusing derivation: expected exactly 3 scoped --all repairs, observed {repair_count}"
    )

if '--assignee "$AZURE_CLIENT_ID" --all' not in text:
    raise SystemExit("Refusing derivation: unscoped principal-discovery fallback lost --all")
if 'ATTEMPT_ID="azure-ai-go-live-run8"' not in text:
    raise SystemExit("Refusing derivation: run-8 attempt identifier missing")
if 'REQUEST_FILE=".project/deployment-requests/azure-ai-go-live-run8.json"' not in text:
    raise SystemExit("Refusing derivation: run-8 request path missing")
if 'Reply with exactly: AZURE AI RUN 8 LIVE' not in text:
    raise SystemExit("Refusing derivation: run-8 verification prompt missing")
if '--arg instruction "Fix and proceed"' not in text:
    raise SystemExit("Refusing derivation: exact source instruction missing")
if re.search(r'--scope "\$account_id" \\\n\s+--all', text):
    raise SystemExit("Refusing derivation: invalid scoped --all combination remains")

target.write_text(text, encoding="utf-8")
target.chmod(0o700)
PY

exec bash "$DERIVED_EXECUTOR"
