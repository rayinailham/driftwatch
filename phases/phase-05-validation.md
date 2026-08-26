# P5 — Validasi & Bukti Resume

**Tujuan sesi:** membuktikan scraper benar (bukan hanya jalan) dan menghasilkan
**bukti nomor satu portofolio**: diputus paksa → dilanjutkan → tidak mengulang.

**Prasyarat:** P4 selesai.
**Read-set:** `STATE.md`, file ini, `docs/ACCEPTANCE.md` (A3, A4, A5), `docs/DECISIONS.md` (D3, D7).
**Budget:** ringan. Banyak menunggu, sedikit menulis.

---

## Langkah

### 1. Verifikasi manual 3 record (A3)
Ambil 3 record dari `books` — satu dari halaman pertama, satu dari tengah, satu dari halaman
terakhir. Untuk tiap record, buka URL aslinya dan bandingkan **setiap field `required`**
satu per satu dengan yang ada di halaman.

Tulis hasilnya di `docs/MANUAL_VERIFY.md`: URL, tabel field (nilai di dataset vs nilai di
halaman), tanggal pengecekan, dan kesimpulan cocok/tidak.

Ini terlihat sepele dan justru inilah yang ditanyakan klien serius: *"kamu sudah cek
datanya benar, atau cuma cek script-nya tidak error?"*

### 2. Bukti kill → resume (A4) — ini yang direkam untuk video P12
```bash
D=$(date +%F)
rm -rf data/books/$D                                   # mulai bersih
uv run python src/scrape.py --target books &
PID=$!
sleep 30 && kill -9 $PID                               # putus paksa

N1=$(sqlite3 data/books/$D/progress.db "SELECT COUNT(*) FROM progress WHERE status='ok';")
L1=$(wc -l < data/books/$D/records.jsonl)
echo "sebelum resume: progress ok=$N1  baris=$L1"

uv run python src/scrape.py --target books --resume
N2=$(sqlite3 data/books/$D/progress.db "SELECT COUNT(*) FROM progress WHERE status='ok';")
L2=$(wc -l < data/books/$D/records.jsonl)
DUP=$(jq -r .record_id data/books/$D/records.jsonl | sort | uniq -d | wc -l)
echo "sesudah resume: progress ok=$N2  baris=$L2  duplikat=$DUP"
```
Yang harus benar: `N2 > N1`, `L2 > L1`, `DUP == 0`, dan `run.json.resume_used == true`.
Yang **tidak** boleh terjadi: `L2 ≈ L1 × 2` (artinya mengulang dari nol).

Simpan output lengkap ini di `docs/RESUME_PROOF.md` — nanti disalin ke README publik.

### 3. Bukti rate limit dihormati (A5)
```bash
jq '.rate_limit' data/books/$D/run.json
grep -oP '\d{2}:\d{2}:\d{2}' data/books/$D/run.log | head -20   # jeda terlihat di timestamp
```
`observed_min_gap_ms` ≥ `delay_sec × 1000 × 0,9`. Kalau lebih kecil, ada jalur kode yang
melewati semaphore — cari dan perbaiki, jangan longgarkan ambangnya.

### 4. Bukti 404/403 tidak di-retry
Arahkan satu unit kerja ke URL yang pasti 404, jalankan, lalu:
```bash
grep -c "RETRY" data/books/$D/run.log     # harus 0
grep -c "404" data/books/$D/run.log       # harus > 0
```

### 5. Unit test scraper
`src/test_scrape.py` — minimal 5 test dengan HTML fixture lokal (jangan hit jaringan di test):
parser menghasilkan field benar · field hilang → `missing_reason` terisi · dedupe menolak
`record_id` sama · `progress` menandai `ok` · klasifikasi retry benar (429 ya, 404 tidak).

```bash
uv run python -m unittest discover -s src -p 'test_*.py' -v
```

---

## Output fase
- `docs/MANUAL_VERIFY.md` (3 record, banding lengkap)
- `docs/RESUME_PROOF.md` (output kill→resume)
- `src/test_scrape.py`
- rekaman layar mentah untuk video P12, **atau** keputusan menundanya ke P12 (catat di `STATE.md`)

## Definition of Done
- [ ] 3 record diverifikasi manual, semua field `required` cocok, tertulis di `docs/MANUAL_VERIFY.md`
- [ ] Kill → resume terbukti: `N2 > N1`, `L2 > L1`, duplikat **0**, `resume_used == true`,
      output ditempel di `docs/RESUME_PROOF.md`
- [ ] `observed_min_gap_ms` ≥ ambang; angkanya ditulis
- [ ] `grep -c RETRY run.log` = 0 walaupun ada respons 404 (jumlah 404 disebut)
- [ ] `python -m unittest discover -s src` → ≥ 11 test total (6 dari P3 + ≥ 5 baru), semua lulus
- [ ] Keputusan rekaman video dicatat di `STATE.md`
- [ ] **Commit + push berhasil** (D19)

## Metrik selesai
`3/3 record cocok manual · resume N1→N2, duplikat 0 · gap X ms · Y test lulus`

## Jebakan
- Jangan pakai `kill` biasa untuk uji resume — pakai `kill -9`. `SIGTERM` bisa ditangani
  dengan rapi dan itu bukan simulasi mati listrik.
- Jangan hit jaringan di unit test. Pakai HTML fixture; test yang butuh internet akan
  gagal di `make all` salinan bersih (P12).
- Jangan menyimpulkan "resume jalan" hanya dari tidak adanya error. Buktinya adalah
  **angka**: berapa yang sudah selesai sebelum dibunuh, berapa sesudahnya.
- Kalau merekam layar: satu monitor saja (`wf-recorder -o eDP-1`), pastikan tidak ada
  kredensial atau jendela kerja user yang terlihat.

## Sebelum menutup sesi
1. Centang DoD dengan output nyata.
2. Update `STATE.md`: P5 ✅, angka resume, jumlah test.
3. `git add -A && git commit -m "P05: validasi manual + bukti kill/resume + unit test" && git push`
