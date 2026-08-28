# P11 — Laporan Klien

**Tujuan sesi:** apa yang dilihat klien tiap hari dan tiap minggu. Kode sebagus apa pun
tidak laku kalau laporannya tidak terbaca.

**Prasyarat:** P8 selesai (diff + alarm sudah menghasilkan angka).
**Read-set:** `STATE.md`, file ini, `docs/CLIENT_REPORT.md` (seluruhnya),
`docs/SCHEMA.md` §5–§7, `src/contracts.py`.
**Budget:** sedang.

---

## Langkah

### 1. `src/report.py --target X --today` → `daily.md`
Templat persisnya di `docs/CLIENT_REPORT.md` §2. Yang mengikat:

- baris pertama = **status**, bukan angka ("Status: SEHAT" / "PERLU PERHATIAN")
- tabel hari ini vs kemarin
- maksimal **3 contoh per kategori** (baru / berubah / hilang)
- perubahan ditulis "dari → ke", bukan diff teknis
- **baris rate limit selalu ada** — itu yang menenangkan bagian legal klien
- digenerate **setiap hari**, termasuk hari tanpa perubahan

### 2. Validator jargon — bagian terpenting fase ini
`report.py` menolak membangun laporan yang memuat: `selector`, `selectolax`, `tenacity`,
`XPath`, `stacktrace`, `traceback`, `regex`, `checkpoint`, `SQLite`, `exception`,
`storage_state`, `semaphore`.

Pola ini terbukti di project 1 (`qa/report.py` → hasil `0 jargon`). Validatornya jalan
sebagai bagian dari build, bukan sebagai catatan di dokumen — dokumen tidak menegakkan apa pun.

### 3. `src/report.py --weekly` → `REPORT.xlsx`
Lima sheet, urutan dikunci di `docs/CLIENT_REPORT.md` §3:
**Ringkasan · Perubahan · Data Baru · Kesehatan Pipeline · Kamus Data**

- Sheet 5 digenerate dari `src/contracts.py` — tidak diketik ulang, jadi tidak pernah basi.
- Pewarnaan hanya tiga: hijau sehat, kuning `warning`, merah `critical`. Tanpa grafik dekoratif.
- Kolom lebar otomatis, baris header dibekukan. Klien membukanya di Excel, bukan di editor teks.

### 4. Notifikasi alarm `critical` — templat 4 baris
`docs/CLIENT_REPORT.md` §4. Urutan yang selalu sama: **apa yang terjadi · seberapa parah ·
dugaan penyebab · apa yang sedang saya lakukan.** Yang terakhir itu yang membedakan alarm
otomatis dari alarm yang membuat klien panik.

Dilarang masuk ke notifikasi klien: stack trace, nama selector, nama file kode, nomor baris,
nama library. Semua itu tinggal di `reports/alerts.jsonl` field `likely_cause`.

### 5. Contoh tersanitasi untuk repo
Salin satu `daily.md` dan satu `REPORT.xlsx` ke `assets/sample_*` setelah dibersihkan dari
path lokal, nama host internal, email, dan kunci. Ini yang ditunjukkan ke calon klien
sebelum mereka membayar.

---

## Output fase
- `src/report.py`
- `reports/<target>/<tanggal>/daily.md` untuk semua tanggal yang sudah ada
- `REPORT.xlsx` mingguan
- `assets/sample_daily.md`, `assets/sample_REPORT.xlsx`

## Definition of Done
- [x] `daily.md` lahir untuk **setiap** tanggal yang punya data, termasuk hari tanpa perubahan
- [x] Validator jargon jalan; menyuntikkan kata terlarang → build **gagal** (dibuktikan)
- [x] `daily.md` memuat status di baris pertama, tabel banding, ≤ 3 contoh per kategori,
      dan baris rate limit
- [x] `REPORT.xlsx` punya **5 sheet** dengan urutan dan nama sesuai `docs/CLIENT_REPORT.md` §3
- [x] Sheet "Kamus Data" digenerate dari `contracts.py`, bukan diketik manual
- [x] Pewarnaan status hanya 3 warna; header dibekukan
- [x] Templat notifikasi 4 baris terimplementasi dan sekali dipicu sungguhan (uji dengan oracle)
- [x] `assets/sample_*` ada dan sudah disanitasi (0 path lokal, 0 email, 0 kunci)
- [x] **Commit + push berhasil** (D19)

---

## Bukti (sesi 2026-08-28)

### 8 `daily.md` untuk semua tanggal yang punya data

```
$ uv run --no-sync python src/report.py --all
reports/books/2026-08-27/daily.md
reports/books/2026-08-28/daily.md
reports/quotes/2026-08-27/daily.md
reports/quotes/2026-08-28/daily.md
reports/seo/2026-08-27/daily.md
reports/seo/2026-08-28/daily.md
reports/driftlab/2026-08-27/daily.md
reports/driftlab/2026-08-28/daily.md
$ ls reports/*/*/daily.md | wc -l
8
```

`reports/books/2026-08-28/daily.md` — hari sunyi (0 baru, 0 berubah, 0 hilang) tetap terbit,
status di baris pertama, baris rate limit ada:

```markdown
# books.toscrape.com — 28 Agustus 2026

**Status: PERLU PERHATIAN** ⚠️

| | Hari ini | Kemarin |
|---|---|---|
| Total data | 1.000 | 1.000 |
| Baru | 0 | 1.000 |
| Berubah | 0 | 0 |
| Hilang | 0 | 0 |
| Kelengkapan kolom | 100,0% | 100,0% |

**Yang perlu Anda tahu (1)**:
- Run hari ini memakan 1052.8 detik, lebih dari tiga kali durasi normal.

**Yang baru (0)**:
- tidak ada data baru hari ini
…
**Catatan pipeline:** run selesai 09:26, 0 detik, tanpa error.
Tidak ada permintaan baru ke situs sumber hari ini; kesepakatan jeda 1,00 detik per permintaan tetap berlaku.
```

Batas 3 contoh per kategori terbukti pada `seo` (23 baru → 3 baris) dan pada oracle DO-04
(200 hilang → 3 baris).

### Validator jargon menggagalkan build

Kata terlarang disuntikkan ke `message` sebuah alarm, lalu digest dibangun ulang:

```
$ uv run --no-sync python src/report.py --target books --date 2026-08-28 \
    --data-root $TMP/data --reports-root $TMP/reports
BUILD GAGAL books 2026-08-28: daily.md books 2026-08-28 memuat jargon terlarang: traceback
exit=2
$ ls $TMP/reports/books/2026-08-28/
diff.json          # daily.md TIDAK ditulis
```

Nilai yang dikutip apa adanya dari sumber dikecualikan: halaman HTTPX benar-benar berjudul
"Exceptions", jadi ia data klien, bukan kosakata pipeline (`test_forbidden_word_quoted_from_the_source_site_is_not_jargon`).

### `REPORT.xlsx` — 5 sheet, urutan terkunci, 3 warna, header beku

```
$ uv run --no-sync python src/report.py --weekly --date 2026-08-28
reports/REPORT.xlsx: Ringkasan 8 baris · Perubahan 0 baris · Data Baru 173 baris ·
                     Kesehatan Pipeline 8 baris · Kamus Data 31 baris

sheets: ['Ringkasan', 'Perubahan', 'Data Baru', 'Kesehatan Pipeline', 'Kamus Data']
Ringkasan: dim=A1:J9 freeze=A2 · Perubahan: freeze=A2 · Data Baru: freeze=A2
Kesehatan Pipeline: dim=A1:AK9 freeze=A2 · Kamus Data: dim=A1:G32 freeze=A2

2026-08-27 books    0 alarm  SEHAT            00C6EFCE (hijau)
2026-08-28 books    1 alarm  PERLU PERHATIAN  00FFEB9C (kuning, warning)
oracle DO-04        critical                  00FFC7CE (merah)  ← test_report
```

Kamus Data 31 baris = 31 field kontrak (`books` 11 + `quotes` 6 + `seo` 9 + `driftlab` 5, D17),
digenerate dari `src/contracts.py`; kolom `Contoh` diambil dari snapshot nyata:

```
('Target', 'Kolom', 'Tipe', 'Contoh', 'Sumber di halaman', 'Wajib/Opsional', 'Catatan')
('books', 'upc', 'teks', 'a897fe39b1053632', 'baris UPC pada tabel informasi produk', 'wajib', 'Kode produk universal buku')
('books', 'title', 'teks', 'A Light in the Attic', 'heading utama halaman detail', 'wajib', 'Judul buku')
```

### Notifikasi 4 baris — dipicu sungguhan lewat oracle DO-04

```
$ uv run --no-sync python scripts/drift_lab.py --scenario DO-04
DO-04 applied; items=200
$ uv run --no-sync python src/alarm.py --target driftlab --date 2026-08-02 …
driftlab 2026-08-02: alarms=['ZERO_RECORDS', 'RECORD_COUNT_DROP', 'FIELD_COMPLETENESS_DROP', 'RUN_FAILED', 'CHURN_SPIKE']
$ uv run --no-sync python src/report.py --target driftlab --date 2026-08-02 --notify …
…/notification-ZERO_RECORDS.txt
…/notification-RECORD_COUNT_DROP.txt
…/notification-FIELD_COMPLETENESS_DROP.txt
…/notification-RUN_FAILED.txt
```

Isi `notification-RECORD_COUNT_DROP.txt` — 4 baris, urutan tetap, dikirim juga lewat
`notify-send` (`/usr/bin/notify-send`):

```
[DriftWatch] driftlab (fixture uji lokal) — PERLU PERHATIAN

Hanya 0 data terkumpul, kurang dari 80% jumlah normal 200.
Tingkat keparahan: kritis — data hari ini belum layak dipakai sampai saya periksa.
Sebagian halaman atau tautan daftar kemungkinan tidak lagi terbaca.
Saya sudah mulai memeriksa; perkiraan perbaikan: hari ini. Data 1 Agustus 2026 tetap utuh dan aman.
```

`CHURN_SPIKE` (warning) sengaja tidak dikirim; hanya `critical` yang menotifikasi.
`next_action` (`make recon`, `run.log`, `--resume`) tidak pernah ikut ke klien.
Fixture direset setelah uji: `11/11 PASS; fixture reset to 200 items`,
`reproducible_sha256=b09a1d162a6608374fb26ad7c95cfa33f5e055217cb4c7b8be733bb8e22ce5d3`.

### `assets/sample_*` tersanitasi

```
assets/sample_daily.md: 0 temuan  path lokal=0 · host internal=0 · email=0 · kunci=0
sel teks diperiksa: 1950
assets/sample_REPORT.xlsx: 0 temuan  path lokal=0 · host internal=0 · email=0 · kunci=0
TOTAL KEBOCORAN: 0
```

`sample_daily.md` = `reports/seo/2026-08-27/daily.md` apa adanya (23 baru → 3 contoh teratas).
`sample_REPORT.xlsx` hanya memuat tiga target publik; `driftlab` tidak ikut karena
tautannya berisi alamat host lokal (sejalan dengan D13).

### Gerbang kesehatan

```
$ uv run --no-sync python -m compileall -q src scripts   → exit 0
$ uv run --no-sync python -m unittest discover -s src    → Ran 43 tests … OK
$ uv run --no-sync python scripts/validate_recon.py      → VALIDASI LOLOS: 4/4
$ uv run --no-sync python scripts/drift_lab.py --verify  → 11/11 PASS
$ uv run --no-sync python scripts/run_oracles.py         → 11/11 PASS
```

## Metrik selesai
`N daily.md · 5 sheet · 0 jargon · notifikasi terbukti terkirim sekali`

## Jebakan
- **Jangan melewatkan hari sunyi.** Digest "0 baru, 0 berubah, pipeline sehat" adalah bukti
  pipeline hidup. Klien yang 3 hari tidak menerima apa pun akan berasumsi buruk — dan benar.
- Jangan menaruh grafik dekoratif di XLSX. Klien butuh angka yang bisa difilter,
  bukan pie chart.
- Jangan menulis kamus data dengan tangan. Ia akan basi di perubahan kontrak pertama.
- Jangan lupa validator jargon berjalan **di dalam build**. Aturan yang hanya ada di
  dokumen tidak menegakkan apa pun.
- Jangan menaruh nama file kode di pesan ke klien.

## Sebelum menutup sesi
1. Centang DoD dengan output nyata.
2. Update `STATE.md`: P11 ✅, jumlah laporan, hasil validator jargon.
3. `git add -A && git commit -m "P11: digest harian + REPORT.xlsx 5 sheet + validator jargon" && git push`
