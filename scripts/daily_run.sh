#!/usr/bin/env bash
set -uo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

LOCK_FILE=${DRIFTWATCH_LOCK_FILE:-/tmp/driftwatch.lock}
exec 9>"$LOCK_FILE"
flock -n 9 || { echo "run lain masih jalan"; exit 0; }

FAIL=0
TODAY=${DRIFTWATCH_DATE:-$(date +%F)}
MISSING_DATE=${DRIFTWATCH_MISSING_DATE:-$(date -d "$TODAY - 1 day" +%F)}
DATA_ROOT=${DRIFTWATCH_DATA_ROOT:-data}
REPORTS_ROOT=${DRIFTWATCH_REPORTS_ROOT:-reports}
WEB_ROOT=${DRIFTWATCH_WEB_ROOT:-web}
TARGETS=${DRIFTWATCH_TARGETS:-"driftlab books quotes seo"}

mark_failed() {
  local manifest=$1
  if [[ -f "$manifest" ]]; then
    uv run --no-sync python scripts/mark_run_failed.py "$manifest" || FAIL=1
  fi
}

for TARGET in $TARGETS; do
  uv run --no-sync python src/alarm.py --target "$TARGET" --check-missing "$MISSING_DATE" \
    --data-root "$DATA_ROOT" --reports-root "$REPORTS_ROOT" || FAIL=1
done

for TARGET in $TARGETS; do
  echo "target=$TARGET start"
  SCRAPE_OK=1
  VALIDATE_OK=1
  uv run --no-sync python src/scrape.py --target "$TARGET" --date "$TODAY" \
    --out "$DATA_ROOT/$TARGET/$TODAY" --resume || { FAIL=1; SCRAPE_OK=0; }
  if [[ ! -f "$DATA_ROOT/$TARGET/$TODAY/records.jsonl" ]]; then
    echo "ERROR target=$TARGET records.jsonl tidak ada; validasi dan ekspor dilewati" >&2
    FAIL=1
    VALIDATE_OK=0
  elif ! uv run --no-sync python src/validate.py "$DATA_ROOT/$TARGET/$TODAY/records.jsonl"; then
    FAIL=1
    VALIDATE_OK=0
    mark_failed "$DATA_ROOT/$TARGET/$TODAY/run.json"
  fi
  if [[ $SCRAPE_OK -eq 1 && $VALIDATE_OK -eq 1 ]]; then
    uv run --no-sync python src/export.py --target "$TARGET" --date "$TODAY" \
      --data-root "$DATA_ROOT" || {
        FAIL=1
        mark_failed "$DATA_ROOT/$TARGET/$TODAY/run.json"
      }
  fi

  uv run --no-sync python src/diff.py --target "$TARGET" --date "$TODAY" \
    --data-root "$DATA_ROOT" --reports-root "$REPORTS_ROOT" || FAIL=1
  uv run --no-sync python src/alarm.py --target "$TARGET" --date "$TODAY" \
    --data-root "$DATA_ROOT" --reports-root "$REPORTS_ROOT" || FAIL=1
  if [[ -f src/report.py ]]; then
    uv run --no-sync python src/report.py --target "$TARGET" --today || true
  fi
  echo "target=$TARGET done"
done

# (7) publikasi halaman demo. Dijalankan sekali setelah loop, bukan per target,
# karena satu halaman memuat semua target publik dan pagar biaya D14 membatasi
# satu panggilan LLM per target per hari. Kegagalan di sini tidak pernah
# menggagalkan panen data.
if uv run --no-sync python src/publish.py --data-root "$DATA_ROOT" \
  --reports-root "$REPORTS_ROOT" --web-root "$WEB_ROOT"; then
  :
else
  PUBLISH_STATUS=$?
  echo "ERROR publish gagal exit=$PUBLISH_STATUS; snapshot scraper tetap dipertahankan" >&2
fi

exit "$FAIL"
