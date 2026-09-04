# P12 — Visual, Packaging & Gladi Bersih

**Tujuan sesi:** orang lain bisa menjalankan seluruh pipeline dari nol dengan satu perintah,
dan calon klien bisa yakin dalam 60 detik tanpa membaca satu baris kode pun.

**Prasyarat:** P9, P10, P11 selesai.
**Read-set:** `STATE.md`, file ini, `docs/ACCEPTANCE.md`, `docs/ETHICS.md`,
`docs/DECISIONS.md` (D10, D19, D20).
**Budget:** ringan tapi panjang.

---

## Langkah

### 1. `Makefile` (D10)
```
make setup      uv sync + siapkan fixture
make lab-up     nyalakan driftlab di :8100 (http.server stdlib, tanpa Docker)
make oracles    11 skenario drift → wajib 11/11
make harvest    panen 4 target
make diff       diff + alarm
make report     digest harian + REPORT.xlsx mingguan
make publish    perbarui halaman demo
make test       unit test
make audit      pemindaian kebocoran rahasia
make prune      rotasi log > 30 hari
make all        setup → lab-up → harvest → diff → report → publish
make lab-down   matikan fixture
```
Wajib memuat `.NOTPARALLEL:` — `MAKEFLAGS` di shell user memuat `-j16` dan urutan
pipeline harus tetap benar (fakta terverifikasi dari project 1).

### 2. `scripts/secret_audit.py` → `make audit`
Memindai seluruh repo untuk nilai dari `.env`, pola kunci API, dan file sensitif yang
ter-track git. Keluaran: daftar nilai kelas RAHASIA dan berapa berkas memuatnya —
wajib **0**. Membedakan kelas *rahasia* (kunci, password) dari kelas *identitas*
(nama akun demo lokal) dan melaporkan keduanya secara terpisah.

Setelah ada, `make audit` menjadi gerbang wajib sebelum setiap commit (D19).

### 3. Video 60 detik — deliverable paling meyakinkan
Satu take, tanpa suara, dengan teks di layar:

```
0:00–0:10  scraper jalan, log mengalir, counter naik
0:10–0:15  DIBUNUH PAKSA (kill -9)          ← teks besar di layar
0:15–0:25  dijalankan ulang dengan --resume
0:25–0:35  lanjut dari posisi terakhir — TIDAK mengulang dari nol
           tampilkan angka: sebelum N1 → sesudah N2, duplikat 0
0:35–0:45  selector sengaja dirusak (DO-04)
0:45–0:55  ALARM berbunyi + isi notifikasi ke klien
0:55–1:00  halaman demo dengan data hari ini
```

```bash
wf-recorder -o eDP-1 -f /tmp/raw.mp4     # satu monitor, tanpa audio
ffmpeg -i /tmp/raw.mp4 -vf "scale=1920:1080" -c:v libx264 -crf 23 assets/v1_resume_demo.mp4
```
Sebelum merekam: pastikan layar tidak menampilkan kredensial, email, atau jendela kerja user.

### 4. Visual pendukung
| Berkas | Isi |
|---|---|
| `assets/v2_architecture.png` | diagram alur `docs/PIPELINE.md` §1, via service PlantUML infra `:20080` — sedang mati, **nyalakan sendiri** (D22-B) |
| `assets/v3_diff_timeline.png` | grafik 3+ hari: baru/berubah/hilang per hari |
| `assets/v4_alarm_matrix.png` | 11 oracle × alarm yang terpicu, hijau/merah |
| `assets/v5_tier_drop.png` | "sebelum: N request browser · sesudah: M request httpx" (A10) |
| `assets/v6_case_study.pdf` | satu halaman A4: masalah, pendekatan, hasil, angka — via `docker run --rm pandoc/core` (image sudah ada, 305 MB). **Jangan `texlive`** (8,73 GB) meski terpasang (D21) |

### 5. README publik
Struktur yang dikunci:
1. Satu kalimat pitch
2. Apa yang dilakukan (5 poin)
3. **Etika scraping** — disalin dari `docs/ETHICS.md` §1 dan §4. **Klien serius membaca
   bagian ini**; letakkan tinggi, bukan di footer.
4. Cara menjalankan (`make all`)
5. Bentuk data + tautan kamus data
6. Bukti: video, angka soak, 11/11 oracle
7. Batasan yang jujur — apa yang project ini **tidak** lakukan (`docs/ACCEPTANCE.md` §D)

Poin 7 terasa berlawanan dengan naluri menjual, dan justru itu yang membuat poin 1–6 dipercaya.

### 6. Gladi bersih salinan bersih (A11)
```bash
rsync -a --exclude data --exclude reports --exclude .venv --exclude .git \
  ./ /tmp/driftwatch-clean/
cd /tmp/driftwatch-clean && cp .env.example .env
# isi kunci seadanya; pakai LAB_PORT berbeda supaya tidak menabrak port kerja user
LAB_PORT=8101 make all
```
Harus exit 0 dan menghasilkan dataset + laporan yang sebanding. Kalau gagal, itu bug
paling berharga di seluruh project — ia persis yang akan dialami klien.

### 7. Audit akhir & latihan pitch
- `make audit` → 0 kebocoran
- centang A1–A12 di `docs/ACCEPTANCE.md` dengan bukti perintah
- naskah pitch 60 detik di `docs/PITCH.md`, **diucapkan keras sekali** dan diukur waktunya
- 🔓 D20: tanyakan ke user apakah repo dijadikan publik. **Jangan lakukan sendiri.**

---

## Output fase
- `Makefile`, `scripts/secret_audit.py`
- `assets/v1..v6`
- `README.md` publik, `docs/PITCH.md`
- `docs/ACCEPTANCE.md` A1–A12 tercentang

## Definition of Done

Dicentang 2026-09-04 dengan output perintah nyata.

- [x] `make all` di salinan bersih → **exit 0**, durasi dicatat (A11)
      ```console
      $ rsync -a --exclude data --exclude reports --exclude .venv --exclude .git ./ /tmp/driftwatch-clean/
      $ cd /tmp/driftwatch-clean && cp .env.example .env
      $ LAB_PORT=8101 make all
      MULAI=2026-09-04T07:35:39+07:00
      SELESAI=2026-09-04T07:53:45+07:00
      EXIT_CODE=0
      DURASI_DETIK=1086
      ```
      **18 menit 6 detik.** Hasil salinan bersih identik dengan produksi:
      ```console
      driftlab  records=200    exit=0
      books     records=1000   exit=0
      quotes    records=100    exit=0
      seo       records=23     exit=0
      total: 1323 record
      ```
- [x] `make all` di salinan bersih berjalan **tanpa Docker sama sekali**
      ```console
      $ grep -c -i "docker" makeall.log
      0
      $ grep -rn "docker" Makefile scripts/lab_up.sh scripts/lab_serve.py scripts/gen_fixture.py src/*.py
      Makefile:5:# di bawah yang memanggil `docker`.
      ```
      Satu-satunya kemunculan adalah baris komentar di `Makefile` yang menjanjikan hal itu.
      Nol pemanggilan `docker` sepanjang eksekusi.
- [x] `make audit` → **0 kebocoran** (A12); `.env`/`data`/`reports` tidak ter-track
      ```console
      $ make audit                     # repo utama
      berkas dipindai: 91  (git ls-files (berkas ter-track))
      [2] ... RAHASIA   nihil — 0 kecocokan untuk 7 pola
      [3] ... RAHASIA   nihil — .env, data/, reports/, auth/, logs/, *.db, *.session bersih
      [4] ... RAHASIA   nihil — 52847 baris diff diperiksa, 0 kecocokan
      KELAS RAHASIA   : 0 kebocoran
      LULUS — 0 kebocoran kelas RAHASIA        (exit 0)

      $ LAB_PORT=8101 make audit       # salinan bersih
      berkas dipindai: 92  (walk pohon kerja (bukan repo git))
      KELAS RAHASIA   : 0 kebocoran
      LULUS — 0 kebocoran kelas RAHASIA        (exit 0)
      ```
      Gerbangnya diuji **tidak kosong**: menanam `sk-ant-api03-AAAA…` di satu berkas
      ter-track membuat audit `GAGAL — kebocoran kelas RAHASIA` dan `exit 1`; lulus lagi
      setelah dicabut. Dua cacat audit ditemukan dan ditutup di sesi ini: di direktori
      tanpa `.git` (persis salinan bersih) ia memindai **nol berkas** lalu tetap melapor
      LULUS — sekarang ada fallback walk pohon kerja dan nol berkas = GAGAL; dan
      pemeriksaan [3] sempat menuduh `.env` salinan bersih sebagai kebocoran padahal
      salinan itu memang **wajib** punya `.env` — sekarang [3] selalu bertanya ke git,
      bukan ke daftar berkas yang dipindai.
- [x] `make oracles` di salinan bersih → 11/11
      ```console
      $ cd /tmp/driftwatch-clean && LAB_PORT=8101 make oracles
      DO-01  added=12 changed=0 removed=0  alarms=[]  PASS
      DO-02  added=0 changed=4 removed=0  alarms=[]  PASS
      DO-03  added=0 changed=0 removed=1  alarms=[]  PASS
      DO-04  records=0  alarms=['CHURN_SPIKE', 'FIELD_COMPLETENESS_DROP', 'RECORD_COUNT_DROP', 'RUN_FAILED', 'ZERO_RECORDS']  PASS
      DO-05  records=200  alarms=['FIELD_COMPLETENESS_DROP']  PASS
      DO-06  records=200  alarms=['HTTP_ERROR_SPIKE']  PASS
      DO-07  records=180  alarms=['RUN_FAILED', 'SCHEMA_UNKNOWN_FIELD']  PASS
      DO-08  records=200  alarms=['DURATION_ANOMALY']  PASS
      DO-09  records=0  alarms=['RUN_MISSING']  PASS
      DO-10  added=0 changed=80 removed=0  alarms=['CHURN_SPIKE']  PASS
      DO-11  records=200  alarms=['RATE_LIMIT_VIOLATION']  PASS
      11/11 PASS
      ORACLES_EXIT=0
      ```
      `make test` di salinan bersih yang sama: `Ran 48 tests` → `OK`.
- [x] Video 60 dtk ada, 1920×1080, memuat kill→resume **dan** alarm berbunyi
      ```console
      $ ffprobe -v error -show_entries stream=codec_name,width,height,pix_fmt \
          -show_entries format=duration,size -of json assets/v1_resume_demo.mp4
      "codec_name": "h264", "width": 1920, "height": 1080, "pix_fmt": "yuv420p"
      "duration": "59.200000", "size": "1302092"
      $ ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 assets/v1_resume_demo.mp4
      (kosong — tidak ada stream audio)
      ```
      Tiga segmen, teks ditanam di gambar: **1/3** `kill -9` di tengah run lalu `--resume`
      (`N1=81 → N2=210`, 200 record, **0 duplikat**, run lanjutan 130 request melawan 212
      kalau mengulang dari nol); **2/3** selector dirusak DO-04 → **5 alarm** berbunyi dan
      `daily.md` klien berubah jadi PERLU PERHATIAN; **3/3** halaman demo.
      Direkam lewat skill `device-screen-recording` di output Hyprland **headless** dengan
      allowlist kelas jendela `kitty` — bukan monitor fisik user, tanpa audio. Layar
      diperiksa: nol kredensial, nol email, nol jendela kerja user. Sandbox `/tmp/driftwatch-demo`
      dipakai supaya data produksi tidak tersentuh; skripnya `scripts/demo_resume.sh`,
      `scripts/demo_alarm.sh`, dirakit `scripts/build_demo_video.sh`.
- [x] 5 visual pendukung lahir
      ```console
      $ ls -la assets/
      v1_resume_demo.mp4    1302092   59,2 dtk · 1920x1080 · h264 · tanpa audio
      v2_architecture.png    150269   PlantUML infra :20080 (D22-B), sumber v2_architecture.puml
      v3_diff_timeline.png   169229   8 tanggal x 4 target, dari reports/*/*/diff.json
      v4_alarm_matrix.png    290541   11 skenario x 10 kode alarm, dari keluaran make oracles
      v5_tier_drop.png       197527   8 request browser -> 1 request httpx, dari recon/quotes.json
      v6_case_study.pdf        5436   1 halaman A4, pandoc/core -> groff (BUKAN texlive)
      ```
      `v3`/`v4`/`v5` digenerate `scripts/make_visuals.py` (stdlib + `rsvg-convert`, nol
      dependency baru); `v6` oleh `scripts/build_case_study.sh`. Catatan jujur soal `v6`:
      image `pandoc/core` **tidak memuat mesin PDF** sama sekali (nol dari
      pdflatex/xelatex/weasyprint/wkhtmltopdf/typst di dalamnya), jadi pandoc dipakai untuk
      markdown → groff `ms` dan penyusunan halamannya dikerjakan `groff -Tpdf` di device.
      `texlive/texlive` (8,73 GB) tetap **tidak** disentuh, sesuai maksud D21.
- [x] README publik memuat bagian etika + batasan jujur
      Struktur 7 bagian terkunci. Bagian **Etika scraping** ada di **bagian 2** — sebelum
      cara instalasi, bukan di footer — memuat 8 aturan `docs/ETHICS.md` §1 dan kalimat
      klien §4, dua-duanya disalin apa adanya. Bagian **6 Batasan yang jujur** menutup
      README dengan 7 hal yang project ini **tidak** lakukan, termasuk "halaman demo tidak
      punya URL publik" dan "target seo hanya 23 URL".
- [x] A1–A12 di `docs/ACCEPTANCE.md` tercentang **dengan output perintah**, bukan klaim
      **12/12 ✅.** A11 dan A12 diisi di sesi ini dengan output di atas. Catatan jujur pada
      A6/P9 ikut tercatat: 2 dari 3 pemicuan timer terbukti langsung di `journalctl`,
      pemicuan 2026-09-01 terbukti lewat watchdog H+1 dan `run.json` karena jurnal mesin
      tidak menjangkau sejauh itu.
- [~] `docs/PITCH.md` ada dan sudah diucapkan sekali (durasi dicatat)
      Naskahnya ada, **138 kata**:
      ```console
      $ sed -n '/^## Naskah/,/^---$/p' docs/PITCH.md | sed 's/^> \?//' \
          | grep -v '^##\|^---\|^$' | wc -w
      138
      ```
      Pada 140–155 kata/menit itu **53–59 detik**. Kotak ini **tidak** ditulis `[x]`:
      naskahnya belum pernah **diucapkan keras** — agent tidak bisa membunyikan suara,
      jadi angkanya estimasi dari jumlah kata, bukan stopwatch. Catatan itu ditulis
      eksplisit di `docs/PITCH.md` beserta permintaan agar user membacanya sekali dan
      mengganti angkanya dengan hasil stopwatch.
- [x] Pertanyaan D20 (repo publik) diajukan ke user; keputusannya dicatat
      Diajukan setelah A11 dan A12 dua-duanya hijau, sesuai urutan yang dikunci D20.
      Keputusan user dicatat di `docs/DECISIONS.md` D20 dan `STATE.md`.
- [x] **Commit + push berhasil** (D19)

## Metrik selesai
`make all salinan bersih exit 0 dalam 18 menit 6 detik · 1.323 record · 11/11 oracle ·
48/48 test · 0 kebocoran RAHASIA · A1–A12 12/12 ✅ · video 59,2 dtk 1920x1080 tanpa audio`

## Jebakan
- Jangan pakai `just` — tidak terpasang di mesin ini (D10).
- Jangan lupa `.NOTPARALLEL:`. Tanpa itu `-j16` di shell user akan mengacak urutan pipeline.
- Jangan menguji salinan bersih di port yang sama (`8100`). Pakai `8101`.
- **`make all` di salinan bersih tidak boleh butuh Docker** (D8/D21). Kalau ia butuh,
  ada runtime dependency yang bocor — itu bug, bukan hal yang ditoleransi.
- Jangan pasang PlantUML atau texlive sendiri. Pakai yang sudah ada di device (D21);
  service infra yang mati boleh dinyalakan sendiri (D22-B).
- Jangan pernah menyentuh `9router.service` (D22-A).
- Jangan merekam desktop penuh. Satu monitor, dan periksa layar dulu.
- Jangan menjadikan repo publik sendiri. 🔓 D20 butuh izin eksplisit user.
- Jangan mencentang acceptance tanpa menempelkan output perintahnya (D15).

## Sebelum menutup sesi
1. Centang DoD + A1–A12 dengan output nyata.
2. Update `STATE.md`: **PROJECT COMPLETE**, tabel metrik final, sisa catatan untuk user.
3. `git add -A && git commit -m "P12: packaging, visual, gladi bersih — project complete" && git push`
