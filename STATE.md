# DriftWatch — STATE

> Ditulis ulang di akhir tiap sesi. Satu-satunya memori antar sesi. Jaga < 100 baris.

**Diperbarui:** 2026-08-28 · **Status:** 🟨 JALAN — 10/13 fase · **Fase aktif:** — (P10 selesai)
**Fase berikutnya:** **P11 — Laporan Klien** (P9 menunggu soak) · **soak_dibuka:** **2026-08-27**

## Status fase

| Fase | Status | Catatan |
|---|---|---|
| P0 Bootstrap | ✅ selesai | `env-check.md`, 10 tool, `uv sync` 0 error · `02469f0` |
| P1 Target & Etika | ✅ selesai | 4 target; HTTPX 7/7; fixture 200; oracle 2/11 · `0f69f5f` |
| P2 Recon | ✅ selesai | 4 recon sah 4/4; quotes → `httpx+json` (8→1 request) · `2d1f585` |
| P3 Kontrak Data | ✅ selesai | 4 kontrak; 31 field (27 required); 12/12 sampel; 11/11 test · `9e81409` |
| P4 Mesin Scraper | ✅ selesai | 6/6 komponen; cicip 3/3 valid; gap publik min 1.000 ms · `eadb3b2` |
| P5 Validasi & Resume | ✅ selesai | 3/3 manual; resume 12→1.000; 17/17 test · `e551205` |
| P6 Panen Penuh | ✅ selesai | 4 target; 1.323 record; required 100%; 18/18 test · `e6ad2f3` |
| P7 Penjadwalan | ✅ selesai | timer aktif; NEXT 2026-08-28 09:04:10 WIB; unit sukses · `c9978ec` |
| P8 Diff & Alarm | ✅ selesai | 10 kode; 11/11 oracle; 12 alarm sah; 0 false positive · `eb46245` |
| P9 Soak 3 Hari | ⬜ belum | gerbang jam dinding; 1/3 tanggal (2026-08-27). Buka ≥ 2026-08-30 |
| P10 Demo + LLM | ✅ selesai | 323 baris; 3 situs; D13/D14/D18 dikunci; 0 kebocoran · `6f7409d` |
| P11 Laporan Klien | ⬜ belum | `daily.md` 0 jargon + `REPORT.xlsx` 5 sheet |
| P12 Packaging | ⬜ belum | video 60 dtk, `make all`, README publik, audit |

Legenda: ⬜ belum · 🟨 jalan · ✅ selesai · 🟥 blocked
## Fakta mesin — DIVERIFIKASI P0, bukan warisan

- ✅ `systemctl --user` ADA (`systemd 261`), TZ `Asia/Jakarta` → **D9 berlaku**, bukan cron. Bukan blocker.
- ⚠️ Venv 3.13.13 ≠ sistem 3.14.6 → perintah produksi **wajib** `uv run`. Tidak ada `just` (→ `make`, D10)
  maupun `pytest` (→ `unittest`); `Makefile` wajib `.NOTPARALLEL:` + `MAKEFLAGS=-j16`.
- Docker tanpa sudo; `sudo` butuh password, tanpa askpass. Port user penuh → `driftlab` **8100**, salinan bersih **8101** (D8)

### 🚨 `9router.service` — JANGAN PERNAH DISENTUH (D22-A · AGENTS.md §0)
systemd **user**, port **20128**, proxy AI lokal. Dilarang stop/restart/kill/disable/mask/edit/pakai port. Satu
direktori dengan `driftwatch.timer` → unit selalu eksplisit, tanpa wildcard. Cek pasca-P7 → `active`.

## Infra device (D21/D22-B)

Cache `uv` + Playwright jangan diprune · image siap: `plantuml/plantuml-server:jetty` + `pandoc/core` (P12,
**bukan** `texlive`). ⚠️ `crosscheck-tut-*` hidup — tanya dulu. Tidak dipakai walau ada: MySQL/Redis/TiDB
(checkpoint wajib SQLite), MCP `excel` (laporan wajib `openpyxl`).

## Fakta terverifikasi tentang target — DIKONFIRMASI P2

| Target | Engine | Baseline P6 | Kunci | Pagination / batas |
|---|---|---:|---|---|
| `books` | `httpx+selectolax` | **1.000** | `upc` | `page-{n}.html` 1..50, berhenti saat `li.next a` hilang |
| `quotes` | **`httpx+json`** | **100** | `quote_id` | `/api/quotes?page=N`, berhenti saat `has_next == false` (page 10) |
| `seo` | `httpx+selectolax` | **23** | `url` | 23 URL dari `sitemap.xml` |
| `driftlab` | `httpx+selectolax` | **200** | `item_id` | `page-{n}.html` 1..10 + 200 halaman detail |

**Playwright TIDAK dipasang.** Nol target `js_required`; browser dipakai sekali di P2 lalu dibuang. Deliverable
bebas dependensi Playwright (D21) — hanya cache-nya dipinjam untuk merender halaman P10.

Robots: `books`/`quotes`/`seo` HTTP 404 · `driftlab` 200 `Allow: /`. Nol `Crawl-delay` → default D3 1,0 dtk
untuk 3 host publik. Selama P2: 0 HTTP 429, 0 login, 0 proteksi ditembus.

## Halaman demo (D18 — berkas statis lokal, bukan URL publik)

`web/index.html`: berkas mandiri, payload ditanam, dibuka lewat `file://` tanpa server. 3 situs publik
(books 200 · quotes 100 · seo 23); `driftlab` tidak terbit (fixture lokal). Insight **`claude-haiku-4-5`** — $1/$5 per 1 juta token, termurah yang memadai (D14).

## Metrik

| Metrik | Target | Aktual |
|---|---|---|
| P0: tool terverifikasi · error `uv sync` | — · 0 | **10 · 0** |
| P1: target · kandidat SEO · lolos · item · oracle | 4 · ≥3 · 1 · 200 · 2/11 | **4 · 3 · 1 · 200 · 2/11** |
| P2: recon sah · butuh browser · quotes request | 4/4 · 0 · turun | **4/4 · 0 · 8 → 1** |
| P3: kontrak · field (required) · sampel · test | 4 · N · 12/12 · ≥6 | **4 · 31 (27) · 12/12 · 11/11** |
| P4: komponen · target valid · record cicip · gap publik min | 6/6 · 3/3 · — · ≥900 ms | **6/6 · 3/3 · 100 · 1.000 ms** |
| Record `books` · duplikat · field `required` | ≥1.000 · 0 · ≥98% | **1.000 · 0 · 100%** |
| P5: manual · resume unit/baris · gap · test | 3/3 · naik/naik · ≥900 ms · ≥11 | **3/3 · 12→1050/12→1000 · 1.000 ms · 17/17** |
| P6: record total · books · dup · required min · test · loop resume | ≥1.000 · ≥1.000 · 0 · ≥98% · — · — | **1.323 · 1.000 · 0 · 100% · 18/18 · 40,927 dtk** |
| P7: timer · NEXT · run unit · target · soak | aktif · waktu · sukses · 4/4 · tanggal | **aktif · 2026-08-28 09:04:10 WIB · 1/1 · 4/4 · 2026-08-27** |
| P8: oracle · kode · alarm sah · false positive · unit | 11/11 · 10 · N · 0 · sukses | **11/11 · 10 · 12 · 0 · sukses** |
| P10: baris terbit · situs · token insight · biaya/hari · kebocoran | ≤200/situs · 3 · N · rendah · 0 | **323 (200+100+23) · 3 · 0 · $0,00000 · 0** |
| `make all` salinan bersih · kebocoran rahasia | exit 0 · 0 | — |
| **Acceptance project** | 12/12 | **2/12 (A8, A9)** |

## Artefak yang sudah lahir

**Perencanaan:** `AGENTS.md`, `PLAN.md`, `KICKSTART.md`, `README.md`, `docs/` (8), `phases/` (13).
**Repo (D19):** `git@rayin-personal:rayinailham/driftwatch.git` — privat, personal, `main` → `origin/main`.
**P0:** `pyproject.toml`, `uv.lock`, `env-check.md`, `.env.example`, struktur folder; **tanpa `docker-compose.yml`** (D8).
**P1:** `docs/TARGETS.md`; generator + server fixture stdlib; CLI reset/verify/DO-01/DO-03; kait DO-06/DO-08.
**P2:** `recon/{books,quotes,seo,driftlab}.json` (4/4 sah) + `scripts/validate_recon.py` (gerbang bentuk, exit 0).
**P3:** `src/{contracts,validate,test_contracts}.py`; skema + D17 terkunci; 31/31 deskripsi dan source hint terisi.
**P4:** `src/scrape.py`, `store.py`, `engines/{http_html,http_json}.py`, `test_scrape.py`; run cicip di `data/` (gitignored); D11 dipulihkan.
**P5:** `docs/{MANUAL_VERIFY,RESUME_PROOF}.md`; 1.000 record books lokal (gitignored); rekaman video ditunda ke P12.
**P6:** `src/{export,test_export}.py`, `docs/DATA_DICTIONARY.md`; 4 snapshot JSONL+CSV BOM (gitignored); D12 dikunci.
**P7:** `scripts/{daily_run,prune}.sh`, `deploy/driftwatch.{service,timer}`, `Makefile`; D9/D10 dikunci; timer aktif.
**P8:** `src/{diff,alarm,test_diff_alarm}.py`, `scripts/run_oracles.py`; 4 `diff.json`; `alerts.jsonl`; 10 detector; oracle 11/11.
**P10:** `src/publish.py`, `web/{template,index}.html` + `data{,-books,-quotes,-seo}.json`; langkah (6) `daily_run.sh`; D13/D14/D18 dikunci.

## Blocker & keputusan terbuka
- **Blocker: tidak ada.**
- 🔓 **D20** repo publik → **P12, butuh izin eksplisit user**. D15 ditulis saat pertama dipakai.
- `ANTHROPIC_API_KEY` **kosong** → insight P10 = 0 token, $0. Isi kunci lalu `uv run --no-sync python src/publish.py` (≈ $0,005/hari).
