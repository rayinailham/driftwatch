#!/usr/bin/env bash
# Segmen B video P12: selector sengaja dirusak (DO-04) -> alarm berbunyi.
# Deterministik, sandbox, fixture lokal. Dipanggil oleh helper device-screen-recording.
set -uo pipefail
cd "${DEMO_ROOT:-/tmp/driftwatch-demo}"
export LAB_PORT=${LAB_PORT:-8102}

B="\033[1m"; G="\033[1;32m"; R="\033[1;31m"; Y="\033[1;33m"; C="\033[1;36m"; N="\033[0m"
banner() { printf "\n${C}%s${N}\n" "$1"; }
BASE=2026-09-03
BREAK=2026-09-04
D=demo2; R2=demo2r
rm -rf $D $R2; mkdir -p $D $R2

clear
printf "${B}DriftWatch — alarm patah yang sudah dibuktikan${N}\n"
printf "skenario DO-04: struktur halaman berubah, class .item-card diganti\n"

banner "[1/4] baseline sehat kemarin"
uv run --no-sync python scripts/drift_lab.py --reset >/dev/null
uv run --no-sync python src/scrape.py --target driftlab --date $BASE \
  --out $D/driftlab/$BASE >/dev/null 2>&1
printf "  ${G}%s: %s record, exit 0${N}\n" "$BASE" \
  "$(uv run --no-sync python -c "import json;print(json.load(open('$D/driftlab/$BASE/run.json'))['records_unique'])")"

banner "[2/4] situs sumber berubah diam-diam"
printf "  \$ uv run python scripts/drift_lab.py --scenario DO-04\n"
uv run --no-sync python scripts/drift_lab.py --scenario DO-04 >/dev/null
printf "  ${Y}class .item-card  ->  .c-9f2a1  di seluruh halaman${N}\n"
printf "  scraper tidak diberi tahu apa pun. detektor tidak tahu skenario mana yang aktif.\n"

banner "[3/4] panen harian jalan seperti biasa"
printf "  \$ uv run python src/scrape.py --target driftlab\n"
uv run --no-sync python src/scrape.py --target driftlab --date $BREAK \
  --out $D/driftlab/$BREAK >/dev/null 2>&1
printf "  ${R}%s: %s record, exit_code %s${N}\n" "$BREAK" \
  "$(uv run --no-sync python -c "import json;print(json.load(open('$D/driftlab/$BREAK/run.json'))['records_unique'])")" \
  "$(uv run --no-sync python -c "import json;print(json.load(open('$D/driftlab/$BREAK/run.json'))['exit_code'])")"

banner "[4/4] ALARM"
uv run --no-sync python src/diff.py --target driftlab --date $BREAK \
  --data-root $D --reports-root $R2 >/dev/null 2>&1
uv run --no-sync python src/alarm.py --target driftlab --date $BREAK \
  --data-root $D --reports-root $R2 --no-notify >/dev/null 2>&1
uv run --no-sync python -c "
import json
d=json.load(open('$R2/driftlab/$BREAK/diff.json'))
for code in sorted(d['alarms']):
    print(f'  \033[1;31m● {code}\033[0m')
"
printf "\n${B}yang sampai ke klien:${N}\n"
uv run --no-sync python src/report.py --target driftlab --date $BREAK \
  --data-root $D --reports-root $R2 --no-send >/dev/null 2>&1
sed -n '1,14p' $R2/driftlab/$BREAK/daily.md | sed 's/^/  /'
sleep 6
# fixture dikembalikan sehat: segmen lain tidak boleh mewarisi kerusakan DO-04.
uv run --no-sync python scripts/drift_lab.py --reset >/dev/null
