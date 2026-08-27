# DriftWatch — STATE

> Ditulis ulang di akhir tiap sesi. Satu-satunya memori antar sesi. Jaga < 100 baris.

**Diperbarui:** 2026-08-27 · **Status:** 🟨 JALAN — 7/13 fase · **Fase aktif:** — (P6 selesai)
**Fase berikutnya:** **P7 — Penjadwalan** · **soak_dibuka:** — (diisi di P7)

## Status fase

| Fase | Status | Catatan |
|---|---|---|
| P0 Bootstrap | ✅ selesai | `env-check.md`, 10 tool, `uv sync` 0 error · `02469f0` |
| P1 Target & Etika | ✅ selesai | 4 target; HTTPX 7/7; fixture 200; oracle 2/11 · `0f69f5f` |
| P2 Recon | ✅ selesai | 4 recon sah 4/4; quotes → `httpx+json` (8→1 request) · `2d1f585` |
| P3 Kontrak Data | ✅ selesai | 4 kontrak; 31 field (27 required); 12/12 sampel; 11/11 test · `9e81409` |
| P4 Mesin Scraper | ✅ selesai | 6/6 komponen; cicip 3/3 valid; gap publik min 1.000 ms · `eadb3b2` |
| P5 Validasi & Resume | ✅ selesai | 3/3 manual; resume 12→1.000 baris; dup 0; 17/17 test |
| P6 Panen Penuh | ✅ selesai | 4 target; 1.323 record; dup 0; required 100%; CSV BOM; 18/18 test |
| P7 Penjadwalan | ⬜ belum | systemd timer 09:00 WIB — **dahulukan**, membuka jam soak |
| P8 Diff & Alarm | ⬜ belum | 10 kode alarm, 11/11 drift oracle |
| P9 Soak 3 Hari | ⬜ belum | gerbang jam dinding, bukan sesi kerja |
| P10 Demo + LLM | ⬜ belum | halaman publik + insight Claude API ber-pagar |
| P11 Laporan Klien | ⬜ belum | `daily.md` 0 jargon + `REPORT.xlsx` 5 sheet |
| P12 Packaging | ⬜ belum | video 60 dtk, `make all`, README publik, audit |

Legenda: ⬜ belum · 🟨 jalan · ✅ selesai · 🟥 blocked
## Fakta mesin — DIVERIFIKASI P0, bukan warisan

- ✅ `systemctl --user` ADA (`systemd 261`), TZ `Asia/Jakarta` → **D9 berlaku**, bukan cron. Bukan blocker.
- ⚠️ Venv 3.13.13 ≠ sistem 3.14.6 → perintah produksi **wajib** `uv run`.
- tidak ada `just` (→ `make`, D10; `Makefile` wajib `.NOTPARALLEL:`, `MAKEFLAGS=-j16`) · tidak ada `pytest` (→ `unittest`)
- Docker tanpa sudo; `sudo` butuh password, tanpa askpass. Port user penuh → `driftlab` **8100**, salinan bersih **8101** (D8)

### 🚨 `9router.service` — JANGAN PERNAH DISENTUH (D22-A · AGENTS.md §0)

systemd **user** unit, port **20128**, proxy AI lokal — matinya bisa memutus sesi agent sendiri.
Dilarang stop/restart/kill/disable/mask/edit + dilarang pakai port 20128. **Satu direktori** dengan
`driftwatch.timer` (P7) → selalu sebut nama unit eksplisit, **jangan pernah wildcard**.
`daemon-reload` aman. Cek P2 (`is-active`, baca-saja) → `active`.

## Infra device (D21/D22-B)

Cache `uv` + Playwright jangan diprune · image siap: `plantuml/plantuml-server:jetty` (P12),
`pandoc/core` (PDF P12, **bukan** `texlive`). ⚠️ `crosscheck-tut-*` hidup — tanya dulu.
P0+P2: **0 `docker pull`, 0 start/stop service infra, 0 edit `infra/docker-compose.yml`.**
Tidak dipakai walau ada: MySQL/Redis/TiDB (checkpoint wajib SQLite), MCP `excel` (laporan wajib `openpyxl`).

## Fakta terverifikasi tentang target — DIKONFIRMASI P2

| Target | Engine | Baseline P6 | Kunci | Pagination / batas |
|---|---|---:|---|---|
| `books` | `httpx+selectolax` | **1.000** | `upc` | `page-{n}.html` 1..50, berhenti saat `li.next a` hilang |
| `quotes` | **`httpx+json`** | **100** | `quote_id` | `/api/quotes?page=N`, berhenti saat `has_next == false` (page 10) |
| `seo` | `httpx+selectolax` | **23** | `url` | 23 URL dari `sitemap.xml` |
| `driftlab` | `httpx+selectolax` | **200** | `item_id` | `page-{n}.html` 1..10 + 200 halaman detail |

**Keputusan Playwright: TIDAK dipasang.** Nol target `js_required` → lapis 2 tak pernah terpakai.
Browser dipakai sekali di P2 (MCP `chrome-devtools`, recon `quotes`) lalu dibuang; deliverable bebas
dependensi Playwright (D21). Kalau P4 ternyata butuh: salin `../crosscheck/scripts/arch_provision.sh`
ke `scripts/` dulu, jangan panggil lintas-project.

**`driftlab` sengaja TOLAK `/items.json`** (1 request vs 210): DO-04/05/07 memutasi HTML saja →
lewat JSON recall oracle mentok 8/11, padahal P8 minta 11/11.

Robots: `books`/`quotes`/`seo` HTTP 404 · `driftlab` 200 `Allow: /`. Nol `Crawl-delay` →
default D3 1,0 dtk untuk 3 host publik. Selama P2: 0 HTTP 429, 0 login, 0 proteksi ditembus.

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
| Drift oracle · kode alarm | 11/11 · 10 | — |
| `make all` salinan bersih · kebocoran rahasia | exit 0 · 0 | — |
| **Acceptance project** | 12/12 | **0/12** |

## Artefak yang sudah lahir

**Perencanaan:** `AGENTS.md`, `PLAN.md`, `KICKSTART.md`, `README.md`, `docs/` (8), `phases/` (13).
**Repo (D19):** `git@rayin-personal:rayinailham/driftwatch.git` — privat, personal, `main` → `origin/main`.
**P0:** `pyproject.toml`, `uv.lock`, `env-check.md`, `.env.example`, struktur folder; **tanpa `docker-compose.yml`** (D8).
**P1:** `docs/TARGETS.md`; generator + server fixture stdlib; CLI reset/verify/DO-01/DO-03; kait DO-06/DO-08.
**P2:** `recon/{books,quotes,seo,driftlab}.json` (4/4 sah) + `scripts/validate_recon.py` (gerbang bentuk, exit 0).
**P3:** `src/{contracts,validate,test_contracts}.py`; skema + D17 terkunci; 31/31 deskripsi dan source hint terisi.
**P4:** `src/scrape.py`, `store.py`, `engines/{http_html,http_json}.py`, `test_scrape.py`; run cicip di `data/` (gitignored); D11 dipulihkan.
**P5:** `docs/{MANUAL_VERIFY,RESUME_PROOF}.md`; 1.000 record books lokal (gitignored); rekaman video ditunda ke P12 agar merekam alur final sekali.
**P6:** `src/{export,test_export}.py`, `docs/DATA_DICTIONARY.md`; 4 snapshot JSONL+CSV BOM (gitignored); D12 dikunci.

## Blocker & keputusan terbuka
- **Blocker: tidak ada.**
- 🔓 **D18** publikasi demo → **P10** · 🔓 **D20** repo publik → **P12, butuh izin eksplisit user**
- ⚠️ D9/D10 belum punya entri sendiri; rapikan saat P7 memakai keduanya. D12–D15 ditulis saat pertama dipakai.
