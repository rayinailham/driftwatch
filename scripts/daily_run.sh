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

# (0) fixture DriftLab. Target `driftlab` menembak http://127.0.0.1:8100; server itu tidak
# pernah hidup sendiri saat unit dipicu timer, jadi tanpa langkah ini panen driftlab selalu
# 0 record dan unit selalu gagal. `lab_up.sh` idempoten (pid file), `lab_down.sh` hanya
# membunuh PID miliknya sendiri — run harian tidak meninggalkan server menyala.
LAB_UP=${DRIFTWATCH_LAB_UP:-scripts/lab_up.sh}
LAB_DOWN=${DRIFTWATCH_LAB_DOWN:-scripts/lab_down.sh}
LAB_STARTED=0

lab_teardown() {
  if [[ $LAB_STARTED -eq 1 ]]; then
    LAB_STARTED=0
    bash "$LAB_DOWN" || echo "ERROR driftlab: fixture gagal dimatikan" >&2
  fi
}

if [[ " $TARGETS " == *" driftlab "* ]]; then
  trap lab_teardown EXIT
  if bash "$LAB_UP"; then
    LAB_STARTED=1
  else
    echo "ERROR driftlab: fixture gagal dinyalakan; panen driftlab akan gagal" >&2
    FAIL=1
  fi
fi

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
  # (6) digest klien + notifikasi alarm critical. Kegagalannya tidak pernah
  # menghapus snapshot, tetapi selalu terlihat di journal dan menggagalkan unit.
  if uv run --no-sync python src/report.py --target "$TARGET" --date "$TODAY" --notify \
    --data-root "$DATA_ROOT" --reports-root "$REPORTS_ROOT"; then
    :
  else
    REPORT_STATUS=$?
    echo "ERROR target=$TARGET laporan harian gagal exit=$REPORT_STATUS; snapshot data tetap dipertahankan" >&2
    FAIL=1
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
