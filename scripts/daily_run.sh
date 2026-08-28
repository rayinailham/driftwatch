#!/usr/bin/env bash
set -uo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

exec 9>/tmp/driftwatch.lock
flock -n 9 || { echo "run lain masih jalan"; exit 0; }

FAIL=0
TODAY=$(date +%F)

for TARGET in driftlab books quotes seo; do
  echo "target=$TARGET start"
  uv run --no-sync python src/scrape.py --target "$TARGET" --resume || FAIL=1
  uv run --no-sync python src/validate.py "data/$TARGET/$TODAY/records.jsonl" || FAIL=1

  uv run --no-sync python src/diff.py --target "$TARGET" --today || FAIL=1
  uv run --no-sync python src/alarm.py --target "$TARGET" --today || FAIL=1
  if [[ -f src/report.py ]]; then
    uv run --no-sync python src/report.py --target "$TARGET" --today || true
  fi
  echo "target=$TARGET done"
done

# (6) publikasi halaman demo. Dijalankan sekali setelah loop, bukan per target,
# karena satu halaman memuat semua target publik dan pagar biaya D14 membatasi
# satu panggilan LLM per target per hari. Kegagalan di sini tidak pernah
# menggagalkan panen data.
uv run --no-sync python src/publish.py || true

exit "$FAIL"
