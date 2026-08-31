# DriftWatch — Acceptance Criteria & Metrik Selesai

Dua lapis: **acceptance project** (gerbang untuk menyebut portofolio ini layak dipajang)
dan **acceptance per fase** (gerbang untuk lanjut ke fase berikutnya).

Angka dan enum di file ini mengikuti `docs/DECISIONS.md`. Kalau berbeda, DECISIONS menang.

---

## Bagian A — Acceptance project (final)

Diambil dari `../portfolio/portfolio_02_scraper_pipeline.md`, diperketat dengan angka
dan perintah pembuktinya.

| # | Kriteria | Status | Perintah pembukti |
|---|---|---|---|
| A1 | Dataset ≥ 1.000 record, duplikat **nol** | ✅ | **Lulus 2026-08-31** (snapshot `2026-08-31`). `wc -l data/books/2026-08-31/records.jsonl` = **1000** · `jq -r .record_id … \| sort \| uniq -d \| wc -l` = **0**. Total empat target hari itu **1.323** (books 1.000 · driftlab 200 · quotes 100 · seo 23) |
| A2 | Kelengkapan field `required` ≥ 98%, yang kosong tercatat alasannya | ✅ | **Lulus 2026-08-31.** Kelengkapan **required 100,0% di keempat target** (titik terendah: books `availability_count` 100% · quotes `author_goodreads_link` 100% · seo `canonical` 100% · driftlab `category` 100%), dihitung atas 27 field `required` dari 31 field kontrak. Record dengan `missing_fields` tanpa `missing_reason` = **0** di keempat target. Yang kosong semuanya field **opsional** dan sengaja: seo `og_title` 0% (halaman sumber memang tidak memasang tag itu), quotes `tags` 97% |
| A3 | 3 record diverifikasi manual cocok dengan halaman aslinya | ✅ | **Lulus.** `docs/MANUAL_VERIFY.md` memuat **3 record** (baris 1, 500, dan 1.000 dari 1.000) — tiap record dibandingkan field demi field terhadap halaman sumbernya lewat parser produksi `parse_detail`, seluruh field `required` kontrak `books` **cocok** (mis. `upc` `a897fe39b1053632`, `0ff9d10864db8364`, `228ba5e7577e1d49`), lengkap dengan URL sumber dan perintah pembuktinya |
| A4 | Diputus paksa di tengah run → dijalankan ulang → lanjut, tidak mengulang | ✅ | **Lulus.** `docs/RESUME_PROOF.md`: run books diputus di tengah, `progress.db` dihitung sebelum (`N1`) dan sesudah (`N2`) lewat `SELECT COUNT(*) FROM progress WHERE status='ok'`, lalu dilanjutkan `--resume` → **12 → 1.000** record, **0 duplikat**, tidak ada halaman yang diambil dua kali. Dokumen yang sama memuat bukti rate limit dan bukti HTTP 404 tidak di-retry |
| A5 | Rate limit terbukti dihormati | ✅ | **Lulus 2026-08-31.** `jq '.rate_limit' run.json` pada tiga target publik: books `observed_min_gap_ms` **1000** · quotes **1001** · seo **1001**, semuanya ≥ `delay_sec × 1000 × 0,9` = **900**. `driftlab` sengaja `delay_sec 0` — fixture lokal milik sendiri, bukan situs pihak ketiga (D3) |
| A6 | Timer harian jalan **3 hari berturut** tanpa disentuh | ✅ | **Lulus 2026-08-31.** `journalctl --user -u driftwatch.service --since "6 days ago" \| grep -c "Starting DriftWatch"` = **5** pemicuan oleh `driftwatch.timer` (bukan `start` manual), dan **5 folder tanggal berurutan** `2026-08-27 … 2026-08-31` untuk keempat target. Catatan jujur: pada 3 dari 5 hari itu unit **exit 1** karena fixture `driftlab` tidak pernah dinyalakan saat timer memicu — bug itu diperbaiki 2026-08-31 di `scripts/daily_run.sh` langkah (0). Yang dibuktikan A6 adalah timernya menyala sendiri; kualitas panennya diuji terpisah di P9 |
| A7 | Laporan diff otomatis terbentuk tiap hari | ✅ | **Lulus 2026-08-31.** `ls reports/*/*/diff.json \| wc -l` = **20** dan `ls reports/*/*/daily.md \| wc -l` = **20** — 4 target × 5 tanggal, setiap tanggal punya keduanya, semuanya lahir dari `daily_run.sh` yang dipicu timer |
| A8 | Alarm patah terbukti: sengaja dirusak → sistem berteriak | ✅ | `make oracles` → **11/11 PASS**, exit 0 |
| A9 | Halaman demo bisa dibuka & memuat data asli hasil scraping | ✅ | `web/index.html` dirender `file://` → 200 baris nyata (D18 menggantikan "URL hidup" dengan berkas statis lokal) + `web/data.json` `generated_at` ≤ 24 jam + hanya metadata (D13) |
| A10 | Turun lapis terbukti: minimal 1 target pindah dari browser ke httpx | ✅ | **Lulus.** `jq -r .recommended_engine recon/quotes.json` = **`httpx+json`**; `engine_rationale` menyebut endpoint yang ditemukan: browser dipakai **sekali** untuk recon (MCP chrome-devtools membaca network → `XHR GET /api/quotes?page=N`), endpoint diuji ulang di luar browser dengan `curl` (HTTP 200, tanpa cookie/Authorization/CSRF/Referer), lalu browser dibuang. Untuk data yang sama: **8 request → 1 request**; panen penuh 100 kutipan = 10 request httpx, **0 proses browser, 0 dependensi Playwright** |
| A11 | Reproducible satu perintah di salinan bersih | ⬜ | `rsync` ke folder baru → `cp .env.example .env` → `make all` exit 0 |
| A12 | Nol kredensial bocor | ⬜ | `make audit` → 0 kebocoran · `.env`, `data/`, `reports/` tidak ter-track git |

Project baru boleh disebut **selesai** kalau A1–A12 semuanya ✅.

---

## Bagian B — Definition of Done per fase

Ringkasan. DoD lengkapnya ada di masing-masing `phases/phase-NN-*.md` dan **di sanalah**
kotaknya dicentang beserta output perintahnya.

| Fase | Gerbang lanjut | Menyumbang ke |
|---|---|---|
| P0 | `uv sync` sukses, `env-check.md` berisi hasil nyata, struktur folder berdiri | — |
| P1 | 4 target ditetapkan, gerbang etika lulus untuk `seo`, `driftlab` hidup di `:8100` | A8 |
| P2 | 4 `recon/*.json` lengkap + `sample` terisi + `engine_rationale` + `ethics_gate.passed` | A10 |
| P3 | `docs/SCHEMA.md` terkunci, `src/contracts.py` + `src/validate.py` jalan, D17 dikunci | A2 |
| P4 | `src/scrape.py` punya 6 komponen wajib, run 2 halaman menghasilkan JSONL valid | A1, A5 |
| P5 | 3 record dicek manual, kill→resume terbukti, unit test lulus, 0 retry pada 403/404 | A3, A4 |
| P6 | ≥ 1.000 record, duplikat 0, CSV+JSONL, `docs/DATA_DICTIONARY.md` lahir | A1, A2 |
| P7 | timer terpasang & `list-timers` menunjukkan jadwal berikutnya | A6 |
| P8 | `make oracles` 11/11, `diff.json` + `alerts.jsonl` sesuai skema | A7, A8 |
| P9 | 3 tanggal berturut ada datanya, tanpa intervensi manual | A6, A7 |
| P10 | halaman demo hidup dengan data nyata, hanya metadata, LLM ber-pagar | A9 |
| P11 | `daily.md` 0 jargon + `REPORT.xlsx` 5 sheet | — |
| P12 | video 60 dtk, `make all` exit 0 di salinan bersih, audit rahasia bersih | A11, A12 |

---

## Bagian C — Gerbang commit (D19)

Berlaku untuk **setiap** fase, tanpa kecuali:

- [ ] pemindaian rahasia bersih (`make audit`, atau cek manual sebelum P12)
- [ ] `git commit -m "PNN: <ringkas>"` berhasil
- [ ] `git push` berhasil ke `git@rayin-personal:rayinailham/driftwatch.git`
- [ ] baru setelah itu fase boleh ditandai ✅ di `STATE.md`

Riwayat commit adalah bagian dari deliverable: 13 fase → 13 commit, tiap commit
membawa metrik selesainya di body.

---

## Bagian D — Yang **bukan** kriteria selesai

Supaya tidak ada scope creep yang menyamar sebagai kualitas:

- Bukan target: dashboard interaktif, autentikasi multi-user, database eksternal
  (Postgres/TiDB), antrian pekerjaan, deployment ke cloud, atau UI admin.
- Bukan target: scraping situs kelima, keenam, dan seterusnya. Empat target sudah
  membuktikan semua klaim pitch.
- Bukan target: dukungan Windows/macOS. Pipeline ini dibangun untuk mesin ini.
