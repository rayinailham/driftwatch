#!/usr/bin/env bash
# Bangun assets/v6_case_study.pdf — satu halaman A4.
#
# pandoc/core (image infra 305 MB, sudah ada) untuk markdown -> groff ms, lalu `groff`
# device pdf untuk penyusunan halaman. `pandoc/core` sendiri TIDAK memuat mesin PDF
# (tidak ada pdflatex/xelatex/weasyprint/wkhtmltopdf di dalamnya), jadi tahap penyusunan
# dikerjakan groff di device. `texlive/texlive` (8,73 GB) sengaja TIDAK dipakai (D21).
set -euo pipefail
cd "$(dirname "$0")/.."

docker run --rm -v "$PWD/assets:/data" -w /data pandoc/core:latest \
  v6_case_study.md -f markdown -t ms -s -o v6_case_study.raw.ms

# container menulis sebagai root; salin ulang supaya kepemilikannya kembali ke user
tmp=$(mktemp); cp assets/v6_case_study.raw.ms "$tmp"; rm -f assets/v6_case_study.raw.ms

# Muat satu halaman A4: font 9pt, leading 11pt, margin dirapatkan.
MS=$(mktemp --suffix=.ms)
python3 - "$tmp" "$MS" <<'PY'
import sys
source, target = sys.argv[1], sys.argv[2]
text = open(source, encoding="utf-8").read()
setup = ".nr PS 9\n.nr VS 11\n.nr LL 6.6i\n.nr PO 0.95i\n.nr HM 0.7i\n.nr FM 0.6i\n.nr PD 0.25v\n"
index = text.index(".TL")
open(target, "w", encoding="utf-8").write(text[:index] + setup + text[index:])
PY
rm -f "$tmp"

# -k preconv (sumber UTF-8) · -t tbl (tabel Angka) · -dpaper/-P-pa4 (A4)
groff -k -t -ms -Tpdf -dpaper=a4 -P-pa4 "$MS" > assets/v6_case_study.pdf
rm -f "$MS"
pdfinfo assets/v6_case_study.pdf | grep -E 'Pages|Page size'
