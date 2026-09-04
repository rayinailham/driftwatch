#!/usr/bin/env bash
# Rakit assets/v1_resume_demo.mp4 dari tiga segmen yang direkam terpisah.
# Alat waktu-bangun, bukan runtime deliverable (D21). Tanpa audio, 1920x1080, H.264.
#
#   segA  scripts/demo_resume.sh  direkam lewat helper device-screen-recording (kelas kitty)
#   segB  scripts/demo_alarm.sh   idem
#   segC  tangkapan layar web/index.html (halaman demo D18)
set -euo pipefail

REC=${REC_DIR:-/tmp/driftwatch-demo/rec}
OUT=${1:-assets/v1_resume_demo.mp4}
FONT=/usr/share/fonts/TTF/DejaVuSans-Bold.ttf
BAR="drawbox=x=0:y=ih-92:w=iw:h=92:color=#0b1220@0.88:t=fill"
cap() { printf "%s,drawtext=fontfile=%s:text='%s':fontcolor=#e6edf3:fontsize=30:x=48:y=h-62" "$BAR" "$FONT" "$1"; }

norm="scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#0b1220,fps=30,setsar=1"
enc=(-an -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p)

# 1/3 — kill -9 lalu --resume. Dipakai apa adanya, tanpa percepatan.
ffmpeg -v error -y -i "$REC/segA.mkv" \
  -vf "$norm,$(cap '1/3 · scraper dibunuh kill -9 di tengah run, lalu dilanjutkan --resume')" \
  "${enc[@]}" "$REC/a.mp4"

# 2/3 — wf-recorder hanya menulis frame saat layar berubah, jadi segmen ini padat
# (7 dtk untuk cerita 50 dtk). setpts melebarkannya supaya teksnya sempat terbaca.
ffmpeg -v error -y -i "$REC/segB.mkv" \
  -vf "setpts=2.6*PTS,$norm,$(cap '2/3 · selector sengaja dirusak (DO-04) — 5 alarm berbunyi, laporan klien ikut berubah')" \
  "${enc[@]}" "$REC/b.mp4"

# 3/3 — halaman demo, berkas statis mandiri (D18), hanya metadata (D13).
ffmpeg -v error -y -loop 1 -t 7 -i "$REC/segC_page.png" \
  -vf "$norm,$(cap '3/3 · halaman demo dari panen harian — metadata saja, plus atribusi dan catatan etika')" \
  "${enc[@]}" "$REC/c.mp4"

printf "file '%s'\n" "$REC/a.mp4" "$REC/b.mp4" "$REC/c.mp4" > "$REC/concat.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$REC/concat.txt" \
  -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -movflags +faststart -an "$OUT"

ffprobe -v error -show_entries stream=codec_name,width,height,pix_fmt \
  -show_entries format=duration,size -of json "$OUT"
