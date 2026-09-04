#!/usr/bin/env bash
# Segmen A video P12: scraper dibunuh kill -9 lalu dilanjutkan --resume.
# Deterministik, dijalankan di sandbox (bukan data produksi), fixture lokal saja —
# nol beban ke host publik. Dipanggil oleh helper device-screen-recording.
#
# Memanggil `.venv/bin/python` langsung, bukan `uv run`: `uv run` mem-fork python,
# sehingga `kill -9 $!` hanya membunuh pembungkusnya dan scraper tetap hidup —
# run akan tampak "dibunuh" padahal selesai normal. Di sini PID yang dibunuh
# benar-benar PID scraper.
set -uo pipefail
cd "${DEMO_ROOT:-/tmp/driftwatch-demo}"
export LAB_PORT=${LAB_PORT:-8102}
PY=.venv/bin/python

B="\033[1m"; G="\033[1;32m"; R="\033[1;31m"; Y="\033[1;33m"; C="\033[1;36m"; N="\033[0m"
banner() { printf "\n${C}%s${N}\n" "$1"; }
DATE=2026-09-04
OUT=demo/driftlab/$DATE
rm -rf demo; mkdir -p demo
# fixture dikembalikan ke keadaan sehat supaya segmen ini tidak bergantung urutan
# eksekusi terhadap scripts/demo_alarm.sh (yang sengaja merusaknya).
$PY scripts/drift_lab.py --reset >/dev/null

count_ok() { $PY -c "
import sqlite3;print(sqlite3.connect('$OUT/progress.db').execute(\"SELECT COUNT(*) FROM progress WHERE status='ok'\").fetchone()[0])"; }
field() { $PY -c "import json;print(json.load(open('$OUT/run.json'))['$1'])"; }

clear
printf "${B}DriftWatch — bukti tahan diputus${N}\n"
printf "fixture lokal 127.0.0.1:%s · folder sandbox, bukan data produksi\n" "$LAB_PORT"

banner "[1/5] scraper jalan — counter naik"
printf "  \$ python src/scrape.py --target driftlab --delay 0.12\n\n"
$PY src/scrape.py --target driftlab --date $DATE --out "$OUT" \
  --delay 0.12 --policy-delay 0.12 > demo/run1.log 2>&1 &
PID=$!
END=$(( $(date +%s) + 11 ))
while kill -0 $PID 2>/dev/null && [ "$(date +%s)" -lt $END ]; do
  printf "\r  PID %s   request terkirim: %-5s record tersimpan: %-5s" "$PID" \
    "$(grep -c 'HTTP Request' demo/run1.log)" \
    "$(grep -oP 'records_written=\K\d+' demo/run1.log | tail -1 || echo 0)"
  sleep 0.3
done
printf "\n"

banner "[2/5] DIBUNUH PAKSA"
printf "  ${R}\$ kill -9 %s${N}\n" "$PID"
kill -9 $PID 2>/dev/null
wait $PID 2>/dev/null
sleep 1
kill -0 $PID 2>/dev/null \
  && printf "  proses masih hidup?! %s\n" "$PID" \
  || printf "  ${R}PID %s: no such process — mati di tengah jalan, tanpa shutdown rapi${N}\n" "$PID"

banner "[3/5] berapa yang sudah aman di checkpoint SQLite?"
printf "  \$ sqlite3 %s/progress.db \"SELECT COUNT(*) FROM progress WHERE status='ok'\"\n" "$OUT"
N1=$(count_ok)
printf "  ${Y}N1 = %s${N}\n" "$N1"

banner "[4/5] dijalankan ulang dengan --resume"
printf "  \$ python src/scrape.py --target driftlab --resume\n\n"
$PY src/scrape.py --target driftlab --date $DATE --out "$OUT" \
  --delay 0.12 --policy-delay 0.12 --resume > demo/run2.log 2>&1 &
PID2=$!
while kill -0 $PID2 2>/dev/null; do
  printf "\r  melanjutkan… checkpoint ok: %-5s" "$(count_ok 2>/dev/null || echo "$N1")"
  sleep 0.3
done
wait $PID2
printf "\r  melanjutkan… checkpoint ok: %-5s\n" "$(count_ok)"

banner "[5/5] hasil"
printf "  ${Y}N1 sebelum dibunuh${N}      : %s\n" "$N1"
printf "  ${G}N2 sesudah --resume${N}     : %s\n" "$(count_ok)"
printf "  ${G}baris records.jsonl${N}     : %s\n" "$(wc -l < "$OUT/records.jsonl")"
printf "  ${G}record unik${N}             : %s\n" "$(field records_unique)"
printf "  ${G}duplikat ditolak${N}        : %s\n" "$(field duplicates_rejected)"
printf "  ${G}request run lanjutan${N}    : %s   (run penuh dari nol: %s)\n" \
  "$(grep -c 'HTTP Request' demo/run2.log)" "$(( $(grep -c 'HTTP Request' demo/run1.log) + $(grep -c 'HTTP Request' demo/run2.log) ))"
printf "\n  ${G}lanjut dari posisi terakhir — TIDAK mengulang dari nol.${N}\n"
sleep 6
