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
| A1 | Dataset ≥ 1.000 record, duplikat **nol** | ⬜ | `wc -l data/books/<d>/records.jsonl` ≥ 1000 · `jq -r .record_id … \| sort \| uniq -d \| wc -l` = 0 |
| A2 | Kelengkapan field `required` ≥ 98%, yang kosong tercatat alasannya | ⬜ | `jq '.field_completeness' run.json` · `jq 'select((.missing_fields\|length)>0) \| select(.missing_reason==null)' … \| wc -l` = 0 |
| A3 | 3 record diverifikasi manual cocok dengan halaman aslinya | ⬜ | `docs/MANUAL_VERIFY.md` berisi 3 record + screenshot/URL + hasil banding |
| A4 | Diputus paksa di tengah run → dijalankan ulang → lanjut, tidak mengulang | ⬜ | log kill + `progress.db` sebelum/sesudah + total akhir benar + duplikat 0 |
| A5 | Rate limit terbukti dihormati | ⬜ | `jq '.rate_limit' run.json` → `observed_min_gap_ms` ≥ `delay_sec×1000×0,9` |
| A6 | Timer harian jalan **3 hari berturut** tanpa disentuh | ⬜ | `journalctl --user -u driftwatch.service --since "4 days ago" \| grep -c Started` ≥ 3 · 3 folder tanggal berurutan |
| A7 | Laporan diff otomatis terbentuk tiap hari | ⬜ | `ls reports/*/*/diff.json \| wc -l` ≥ 3 · tiap tanggal punya `daily.md` |
| A8 | Alarm patah terbukti: sengaja dirusak → sistem berteriak | ⬜ | `make oracles` → **11/11 PASS**, exit 0 |
| A9 | Halaman demo bisa dibuka & memuat data asli hasil scraping | ⬜ | URL hidup + `web/data.json` `generated_at` ≤ 24 jam + hanya metadata (D13) |
| A10 | Turun lapis terbukti: minimal 1 target pindah dari browser ke httpx | ⬜ | `recon/quotes.json` `recommended_engine` = `httpx+json` + `engine_rationale` menyebut endpoint yang ditemukan |
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
