#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

LOCK_FILE=${DRIFTWATCH_LOCK_FILE:-/tmp/driftwatch.lock}
exec 9>"$LOCK_FILE"
flock -n 9 || { echo "run DriftWatch lain masih jalan"; exit 0; }

TARGET_DATE=${1:-$(date -d yesterday +%F)}
DATA_ROOT=${DRIFTWATCH_DATA_ROOT:-data}
REPORTS_ROOT=${DRIFTWATCH_REPORTS_ROOT:-reports}
TARGETS=${DRIFTWATCH_TARGETS:-"driftlab books quotes seo"}
FAIL=0

for TARGET in $TARGETS; do
  uv run --no-sync python src/alarm.py --target "$TARGET" --check-missing "$TARGET_DATE" \
    --data-root "$DATA_ROOT" --reports-root "$REPORTS_ROOT" || FAIL=1
done

exit "$FAIL"
