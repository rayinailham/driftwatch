# P6 — Panen Penuh & Dataset

**Tujuan sesi:** dataset ≥ 1.000 record dengan duplikat nol, tersedia dalam CSV + JSONL,
plus kamus data. Ini baseline pertama untuk seluruh mesin diff.

**Prasyarat:** P5 selesai.
**Read-set:** `STATE.md`, file ini, `docs/DECISIONS.md` (D11, D12), `docs/SCHEMA.md` §2–§3,
`docs/ACCEPTANCE.md` (A1, A2).
**Budget:** sedang. Sebagian besar waktu adalah menunggu run.

---

## Matematika beban

```
books    1.000 buku ÷ 20 per halaman = 50 halaman listing + 1.000 halaman detail
         1.050 request × 1,0 dtk delay ÷ 3 concurrency ≈ 6 menit
quotes   ~100 kutipan lewat endpoint JSON ≈ 10 request ≈ 10 detik
seo      50–500 URL dari sitemap × 1,0 dtk ÷ 3 ≈ 3 menit
driftlab 200 item lokal, tanpa delay ≈ 5 detik
```
Rumus: `total_request × delay ÷ concurrency`. Kalau meleset jauh dari perkiraan, **ukur**,
jangan menebak — dan cek apakah semaphore benar-benar bekerja.

`books` sendirian sudah memenuhi A1 (≥ 1.000 record). Tiga target lain memperkuat klaim
lain, bukan jumlahnya.

---

## Langkah

### 1. Full run keempat target
```bash
for T in driftlab quotes books seo; do
  uv run python src/scrape.py --target $T --resume
done
```
Urutan sengaja: yang murah dan lokal duluan, supaya kalau ada bug ia ketahuan sebelum
membuang 6 menit request ke host publik.

### 2. Verifikasi A1 & A2
```bash
D=$(date +%F)
wc -l data/books/$D/records.jsonl                                   # ≥ 1000
jq -r .record_id data/books/$D/records.jsonl | sort | uniq -d | wc -l   # 0
jq '.field_completeness' data/books/$D/run.json                     # required ≥ 0,98
jq 'select((.missing_fields|length)>0) | select(.missing_reason==null)' \
   data/books/$D/records.jsonl | wc -l                              # 0  (D6)
```

### 3. Ekspor CSV (D12)
`src/export.py` membaca JSONL → menulis `records.csv`:
- encoding **`utf-8-sig`** (BOM) supaya Excel Windows tidak merusak karakter non-ASCII
- field bersarang (`tags`) digabung dengan `"; "`
- urutan kolom mengikuti urutan di `src/contracts.py`, bukan urutan dict Python
- kolom teknis (`content_hash`, `run_id`) ikut, tapi di paling kanan

Verifikasi: `head -2 records.csv` dan cek jumlah baris = jumlah baris JSONL + 1 (header).

### 4. `docs/DATA_DICTIONARY.md`
Digenerate dari `src/contracts.py` (`description` + `source_hint` yang ditulis di P3),
bukan diketik ulang. Isinya per target: nama kolom, tipe, wajib/opsional, contoh nilai
nyata dari dataset, penjelasan satu kalimat, dan dari bagian halaman mana ia diambil.

Ini file yang diminta klien tiga bulan kemudian dan paling sering tidak dimiliki pesaing.

### 5. Catat baseline
Angka `records_unique` tiap target hari ini adalah **baseline pertama** untuk alarm
`RECORD_COUNT_DROP` (D5). Tulis di `STATE.md`.

---

## Output fase
- `data/<target>/<tanggal>/{records.jsonl,records.csv,run.json,run.log}` untuk 4 target
- `src/export.py`
- `docs/DATA_DICTIONARY.md`

## Definition of Done
- [ ] `books` ≥ **1.000** record; duplikat **0** (perintah §2 ditempel)
- [ ] Keempat target selesai dengan `exit_code == 0`
- [ ] Semua field `required` kelengkapan ≥ **98%**; angkanya ditulis per target
- [ ] Field kosong tanpa `missing_reason` = **0** (D6)
- [ ] `records.csv` ada untuk 4 target, `utf-8-sig`, jumlah baris = JSONL + 1
- [ ] CSV dibuka dan karakter non-ASCII tampil benar (bukan mojibake) — sebutkan contohnya
- [ ] `docs/DATA_DICTIONARY.md` lahir, digenerate dari `contracts.py`, memuat contoh nilai nyata
- [ ] Baseline `records_unique` per target dicatat di `STATE.md`
- [ ] **Commit + push berhasil** (D19)

## Metrik selesai
`books N record · duplikat 0 · kelengkapan X% · 4 target · durasi Y dtk`

## Jebakan
- **Jangan baca `records.jsonl` mentah-mentah ke context.** Pakai `jq`, `wc -l`, `uniq -c`.
- Jangan menjalankan full run berkali-kali tanpa alasan. Tiap run adalah 1.000+ request ke
  host orang lain — dan D3 bukan hanya angka di dokumen.
- Jangan menimpa folder tanggal (D11). Kalau perlu mengulang di hari yang sama, pakai
  `--date` dengan suffix atau hapus folder secara sadar.
- Jangan lupa `utf-8-sig`. CSV UTF-8 polos akan tampak rusak di Excel Windows dan klien
  akan menyimpulkan datanya yang rusak.
- Kalau `books` menghasilkan < 1.000, jangan melonggarkan A1 — cari halaman yang terlewat.

## Sebelum menutup sesi
1. Centang DoD dengan output nyata.
2. Update `STATE.md`: P6 ✅, tabel metrik per target, baseline.
3. `git add -A && git commit -m "P06: panen penuh 4 target + CSV + kamus data" && git push`
