# P8 — Mesin Diff & Alarm

**Tujuan sesi:** pipeline tahu apa yang berubah sejak kemarin, dan **berteriak** kalau
situs target berubah struktur. Ini pembeda terbesar project ini dari scraper biasa.

**Prasyarat:** P6 selesai (ada baseline) + P1 (fixture `driftlab` hidup).
**Read-set:** `STATE.md`, file ini, `docs/DECISIONS.md` (D4, D5, D7), `docs/SCHEMA.md` §5–§6,
`docs/DRIFT_ORACLES.md`.
**Budget:** sedang. Fase kedua-terbanyak menulis kode.

---

## Langkah

### 1. `src/diff.py`
Membandingkan snapshot hari ini dengan **run sukses terakhir** (baseline), bukan dengan
"kemarin" secara harfiah — kalau kemarin gagal, baseline-nya mundur lebih jauh.

```
added    = record_id hari ini \ baseline
removed  = record_id baseline \ hari ini
changed  = record_id sama, content_hash berbeda → daftar field yang berubah
unchanged= sisanya
```

Output `reports/<target>/<tanggal>/diff.json` sesuai `docs/SCHEMA.md` §5.
Ingat pemotongan: maksimal 50 entri per kategori di JSON, `counts` tetap penuh,
`"truncated": true` kalau terpotong.

**Uji kewarasan pertama, sebelum apa pun:** jalankan diff dua snapshot yang identik.
Hasilnya wajib `added=0 changed=0 removed=0`. Kalau `changed` ≠ 0, `VOLATILE` di D7 bocor
ke dalam hash — perbaiki di `src/validate.py`, bukan di `diff.py`.

### 2. `src/alarm.py` — 10 kode tertutup (D4), ambang persis di D5
Satu fungsi per kode, masing-masing menerima `(run_today, run_baseline, diff)` dan
mengembalikan `Alarm | None`. Jangan menulis satu fungsi raksasa berisi `if/elif` —
tiap kode harus bisa diuji sendiri oleh oracle-nya.

Tiap alarm yang lahir wajib punya:
- `message` — **bebas jargon**, ini yang dibaca klien
- `likely_cause` — boleh teknis, dibaca developer
- `next_action` — perintah atau langkah konkret, bukan "periksa lebih lanjut"

Keluaran: append ke `reports/alerts.jsonl` + `notify-send` + kode `alarms[]` di `diff.json`.
Exit code `1` kalau ada alarm `critical`, `0` kalau hanya `warning`/`info`.

Aturan baseline: kalau belum ada baseline, `baseline: null` dan **tidak ada** alarm
perbandingan yang boleh berbunyi. Run pertama sebuah target tidak pernah "anjlok".

### 3. Lengkapi `scripts/drift_lab.py` — 11 skenario
Sembilan skenario sisanya (P1 sudah membuat DO-01 dan DO-03). Tabel lengkapnya di
`docs/DRIFT_ORACLES.md`. Aturan yang mengikat:
- satu skenario per run
- selalu `--reset` di antara skenario
- mesin diff/alarm **tidak boleh tahu** skenario mana yang aktif

DO-06 (503) dan DO-08 (jeda 4 dtk) dipicu lewat berkas penanda `fixtures/.scenario`
yang dibaca handler `scripts/lab_serve.py` (kaitnya sudah dibuat di P1) — **bukan** dengan
mengubah kode scraper. Scraper tidak boleh tahu ia sedang diuji.

### 4. `make oracles` — gerbang A8
Menjalankan 11 skenario berurutan, tiap skenario: `--reset` → terapkan → panen `driftlab`
→ diff → alarm → **assert** alarm yang muncul persis sama dengan kolom "wajib terpicu".

```
DO-01  added=12 changed=0 removed=0   alarms=[]                              PASS
DO-04  records=0                       alarms=[ZERO_RECORDS,RECORD_COUNT_DROP]  PASS
...
11/11 PASS
```
Exit 0 hanya kalau **11/11**.

**DO-01..DO-03 lulus dengan cara sebaliknya: mereka wajib TIDAK memicu alarm apa pun.**
Alarm yang berbunyi saat data normal sama merusaknya dengan alarm yang diam saat rusak —
klien berhenti membaca peringatan yang terlalu sering salah.

### 5. Sambungkan ke `daily_run.sh`
Baris `src/diff.py` dan `src/alarm.py` sudah ditulis di P7. Pastikan sekarang benar-benar
jalan dan `journalctl` menunjukkannya.

---

## Output fase
- `src/diff.py`, `src/alarm.py`
- `scripts/drift_lab.py` lengkap (11 skenario)
- target `oracles` di `Makefile` (atau `scripts/run_oracles.sh` kalau `Makefile` belum ada)
- `reports/<target>/<tanggal>/diff.json` untuk 4 target
- `reports/alerts.jsonl`

## Definition of Done
- [ ] Diff dua snapshot identik → `added=0 changed=0 removed=0` (uji kewarasan D7)
- [ ] `diff.json` 4 target sesuai `docs/SCHEMA.md` §5, termasuk `counts` dan `health`
- [ ] Kesepuluh kode alarm terimplementasi dengan ambang **persis** seperti D5
- [ ] `make oracles` → **11/11 PASS**, exit 0 (output ditempel penuh) — **A8**
- [ ] DO-01..DO-03 lulus **tanpa** alarm apa pun (uji false positive)
- [ ] Tiap `message` alarm bebas jargon; ada validator yang menolak daftar kata terlarang
      (`docs/CLIENT_REPORT.md` §2 aturan 3)
- [ ] Tiap alarm punya `next_action` yang konkret
- [ ] `daily_run.sh` menjalankan diff + alarm; terlihat di `journalctl`
- [ ] **Commit + push berhasil** (D19)

## Metrik selesai
`11/11 oracle PASS · 10 kode alarm · N alarm sah, 0 false positive di DO-01..03`

## Jebakan
- **Uji kewarasan §1 dulu, sebelum menulis alarm.** Kalau hash tidak stabil, semua yang
  dibangun di atasnya salah dan kamu baru sadar setelah menulis 10 detektor.
- Jangan bandingkan dengan "kemarin" secara literal. Baseline = **run sukses terakhir**.
- Jangan biarkan alarm berbunyi pada run pertama (belum ada baseline). Itu false positive
  paling memalukan karena terjadi di hari pertama klien memakai pipeline.
- Jangan memasukkan stack trace ke `message`. Itu untuk `likely_cause`.
- Jangan longgarkan ambang D5 supaya oracle lulus. Kalau oracle gagal, **detektornya**
  yang salah — itu seluruh gunanya punya oracle.
- Jangan jalankan skenario mutasi ke situs pihak ketiga. Hanya `driftlab`.

## Sebelum menutup sesi
1. Centang DoD dengan output nyata (tempel output `make oracles` penuh).
2. Update `STATE.md`: P8 ✅, 11/11, jumlah alarm sah.
3. `git add -A && git commit -m "P08: mesin diff + 10 kode alarm + 11/11 drift oracle" && git push`
