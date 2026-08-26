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
- [ ] `daily.md` lahir untuk **setiap** tanggal yang punya data, termasuk hari tanpa perubahan
- [ ] Validator jargon jalan; menyuntikkan kata terlarang → build **gagal** (dibuktikan)
- [ ] `daily.md` memuat status di baris pertama, tabel banding, ≤ 3 contoh per kategori,
      dan baris rate limit
- [ ] `REPORT.xlsx` punya **5 sheet** dengan urutan dan nama sesuai `docs/CLIENT_REPORT.md` §3
- [ ] Sheet "Kamus Data" digenerate dari `contracts.py`, bukan diketik manual
- [ ] Pewarnaan status hanya 3 warna; header dibekukan
- [ ] Templat notifikasi 4 baris terimplementasi dan sekali dipicu sungguhan (uji dengan oracle)
- [ ] `assets/sample_*` ada dan sudah disanitasi (0 path lokal, 0 email, 0 kunci)
- [ ] **Commit + push berhasil** (D19)

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
