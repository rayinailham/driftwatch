# DriftWatch — Alur Kerja Pipeline (satu halaman)

Dokumen ini menjawab: "apa yang sebenarnya terjadi, dari situs mentah sampai email klien?"

---

## 1. Peta besar

```
                    SEKALI DI AWAL (fase pembangunan)
 ┌──────────────────────────────────────────────────────────────────────┐
 │  situs target                                                        │
 │      │                                                               │
 │      ├─ robots.txt / sitemap.xml / header      ← cek termurah dulu    │
 │      ├─ HTML mentah: ada __NEXT_DATA__? ld+json?                     │
 │      └─ network tab: ada XHR yang balas JSON?  ← MCP chrome-devtools  │
 │            │                                                          │
 │            ▼                                                          │
 │      recon/<target>.json  ──── keputusan engine ────┐                 │
 └─────────────────────────────────────────────────────┼────────────────┘
                                                       ▼
                            ┌──────────────────────────────────────────┐
                            │ json_api      → httpx + json    (Lapis 4)│
                            │ embedded_json → httpx + json    (Lapis 4)│
                            │ server_html   → httpx+selectolax(Lapis 3)│
                            │ js_required   → Playwright      (Lapis 2)│
                            └──────────────────────────────────────────┘
                                                       │
                                                       ▼
                    SETIAP HARI, OTOMATIS (fase operasional)
 ┌──────────────────────────────────────────────────────────────────────┐
 │ systemd timer 09:00 WIB + watchdog H+1 10:00 WIB                     │
 │      │  Persistent=true → run yang terlewat dikejar saat mesin nyala  │
 │      ▼                                                                │
 │ scripts/daily_run.sh                                                  │
 │      │                                                                │
 │      ├─(0)─► src/alarm.py --check-missing <kemarin>                   │
 │      │        RUN_MISSING dedupe target+tanggal+kode                  │
 │      │                                                                │
 │      ├─(1)─► src/scrape.py --target X --resume                        │
 │      │        rate limit · retry · checkpoint · dedupe · log          │
 │      │        └─► data/X/<tanggal>/{records.jsonl,records.csv,run.json}│
 │      │                                                                │
 │      ├─(2)─► src/validate.py  ← tegakkan kontrak, hitung completeness │
 │      ├─(3)─► src/export.py    ← records.jsonl → records.csv BOM       │
 │      │                                                                │
 │      ├─(4)─► src/diff.py      ← hari ini vs baseline terakhir         │
 │      │        └─► reports/X/<tanggal>/diff.json                       │
 │      │                                                                │
 │      ├─(5)─► src/alarm.py     ← 10 kode alarm (D4/D5)                 │
 │      │        └─► reports/alerts.jsonl  + notify-send + exit code     │
 │      │                                                                │
 │      ├─(6)─► src/report.py    ← digest manusia                        │
 │      │        └─► reports/X/<tanggal>/daily.md                        │
 │      │                                                                │
 │      └─(7)─► src/publish.py   ← halaman demo + ringkasan Claude API   │
 │               └─► web/data.json → web/index.html                      │
 └──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    MINGGUAN (manual atau terjadwal)
                    src/report.py --weekly → REPORT.xlsx → klien
```

---

## 2. Delapan langkah harian, dijelaskan

### (0) Preflight run terlewat — `src/alarm.py --check-missing`

Memeriksa `run.json` tanggal kemarin sebelum panen hari ini. Jalur kedua,
`driftwatch-watchdog.timer`, menjalankan pemeriksaan H+1 pukul 10:00 WIB meski timer panen
utama mati total (D23). Alert dideduplikasi berdasarkan target, tanggal, dan kode.

### (1) Panen — `src/scrape.py`

Menulis ke folder **tanggal hari ini**, tidak pernah menimpa snapshot kemarin (D11).
Enam komponen wajibnya (tanpa ini, ia cuma script sekali pakai):

| Komponen | Wujudnya | Kenapa klien peduli |
|---|---|---|
| Rate limit | semaphore + `asyncio.sleep(delay)`, tercatat di `observed_min_gap_ms` | pipeline tidak diblokir bulan depan |
| Retry | `tenacity`, backoff eksponensial, **hanya** 429/5xx + error jaringan | gangguan sesaat tidak merusak seluruh run |
| Checkpoint | SQLite `progress` | Ctrl+C / mati listrik → lanjut, bukan ulang dari nol |
| Dedupe | SQLite `seen` PRIMARY KEY | nol duplikat, dijamin database bukan janji |
| Output streaming | append JSONL + flush berkala | run 100.000 baris tidak menghabiskan RAM |
| Log | `logging`, satu baris per N record | ada bukti apa yang terjadi kemarin jam 09:04 |

**404 dan 403 tidak pernah di-retry.** Itu temuan (halaman hilang / diblokir),
bukan kegagalan jaringan. Meretry-nya hanya membuang waktu dan terlihat seperti serangan.
Kegagalan unit listing boleh meninggalkan record parsial, checkpoint, status HTTP, dan log
untuk diagnosis, tetapi membuat `run.json.exit_code` nonzero. Khusus 404 setelah halaman
terakhir DriftLab adalah terminator pagination dan tidak dihitung sebagai kegagalan.

### (2) Validasi — `src/validate.py`

Menolak record yang melanggar `src/contracts.py`: key asing, tipe salah, field kosong tanpa
alasan (D6). Menghitung `field_completeness` yang dipakai alarm di langkah (4).
Kalau validasi gagal, status pipeline menjadi nonzero, ekspor dilewati, dan diff serta alarm
tetap berjalan. Manifest ditandai `exit_code=1` agar `RUN_FAILED` muncul—kegagalan itu sendiri
harus dilaporkan, bukan disembunyikan. Kegagalan ekspor memakai penanda yang sama.

### (3) Ekspor — `src/export.py`

Hanya berjalan bila scrape dan validasi target sukses serta `records.jsonl` ada. Menulis
`records.csv` dengan BOM UTF-8 sesuai D12. Kegagalan ekspor membuat pipeline nonzero dan
tidak pernah ditelan.

### (4) Diff — `src/diff.py`

Membandingkan snapshot hari ini dengan **run sukses terakhir** (baseline).

```
added    = record_id ada hari ini, tidak ada di baseline
removed  = record_id ada di baseline, tidak ada hari ini
changed  = record_id sama, content_hash berbeda  → daftar field yang berubah
unchanged= sisanya
```

Kunci kewarasannya ada di D7: field volatil (`fetched_at`, `run_id`) tidak ikut di-hash.
Tanpa aturan itu, 100% record akan tampak "berubah" setiap hari dan laporan jadi sampah.

### (5) Alarm — `src/alarm.py`

Sepuluh kode tertutup (D4), ambangnya di D5. Filosofinya satu kalimat:

> **Scraper yang rusak harus berisik. Diam adalah mode kegagalan terburuk.**

Pesaing mengirim script yang, ketika situs berubah, diam-diam mengembalikan 0 baris selama
tiga minggu sampai klien sadar sendiri. Pipeline ini berteriak di hari pertama.

Alarm `critical` → `exit 1` dari `daily_run.sh` → systemd menandai unit gagal →
terlihat di `systemctl --user --failed`. Plus `notify-send` di desktop dan baris di
`reports/alerts.jsonl`.

### (6) Laporan — `src/report.py`

`daily.md` untuk manusia. Aturan nadanya di `docs/CLIENT_REPORT.md`.
Digenerate **setiap hari**, termasuk hari yang tidak ada perubahannya.

### (7) Publikasi — `src/publish.py`

Menyegarkan `web/data.json` (metadata saja, D13) dan meminta satu ringkasan ke Claude API
(pagar biaya di D14). `--no-llm` mematikan bagian itu sepenuhnya.
Kegagalan publish tidak mengubah snapshot scraper atau exit pipeline, tetapi selalu menulis
pesan `ERROR publish gagal exit=...` ke stderr sehingga terlihat di journal systemd.

---

## 3. Apa yang terjadi kalau sesuatu rusak

| Kejadian | Yang terjadi | Yang dilihat klien |
|---|---|---|
| Laptop mati saat run | checkpoint tersimpan; run berikutnya `--resume` melanjutkan | tidak ada; data tetap lengkap |
| Mesin mati seharian | `Persistent=true` mengejar run yang terlewat saat nyala | catatan "run dikejar" di digest |
| Situs balas 503 sesaat | retry backoff 3× | tidak ada |
| Situs balas 503 terus | `HTTP_ERROR_SPIKE` critical | email: "situs sumber sedang bermasalah" |
| Situs ganti struktur HTML | record anjlok → `RECORD_COUNT_DROP` | email: "struktur situs berubah, saya perbaiki hari ini" |
| Satu field hilang di 30% halaman | `FIELD_COMPLETENESS_DROP` | email: "kolom tanggal mulai kosong di sebagian halaman" |
| Situs restrukturisasi besar | `CHURN_SPIKE` (warning, bukan critical) | email: "banyak perubahan, ini normal atau perlu ditinjau?" |
| Timer tidak jalan | watchdog terpisah memicu `RUN_MISSING` pada H+1 | email: "run kemarin tidak terjadi" |

Perbedaan `critical` vs `warning` bukan kosmetik: `critical` berarti **datanya tidak boleh
dipercaya hari ini**; `warning` berarti **datanya sah tapi ada yang perlu dilihat manusia**.

---

## 4. Kenapa urutan langkahnya begitu

Diff sebelum alarm, alarm sebelum laporan. Alasannya: alarm butuh angka dari diff
(berapa yang hilang vs baseline), dan laporan butuh keduanya. Membalik urutan berarti
laporan harian tidak bisa menyebut alarm — dan laporan tanpa alarm persis seperti yang
dijual pesaing.
