# DriftWatch — STATE

> Ditulis ulang di akhir tiap sesi. Satu-satunya memori antar sesi. Jaga < 100 baris.

**Diperbarui:** 2026-08-28 · **Status:** 🟨 JALAN — 11/13 fase · **Fase aktif:** — (P11 selesai)
**Fase berikutnya:** **P9 — Soak 3 Hari** (jam dinding; P12 menunggu P9) · **soak_dibuka:** **2026-08-28**

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
| P9 Soak 3 Hari | ⬜ belum | soak_dibuka tetap 2026-08-28: versi ber-`report.py` mulai jalan hari yang sama |
| P10 Demo + LLM | ✅ selesai | 323 baris; 3 situs; D13/D14/D18 dikunci; 0 kebocoran · `6f7409d` |
| P11 Laporan Klien | ✅ selesai | 8 `daily.md`; 5 sheet; 0 jargon; 4 notifikasi terkirim · `49c80e1` |
| P12 Packaging | ⬜ belum | video 60 dtk, `make all`, README publik, audit |

Legenda: ⬜ belum · 🟨 jalan · ✅ selesai · 🟥 blocked
## Fakta mesin — DIVERIFIKASI P0, bukan warisan
- `systemctl --user` ada (`systemd 261`), TZ `Asia/Jakarta` → D9, bukan cron.
- Venv 3.13.13 ≠ sistem 3.14.6 → produksi wajib `uv run`; test `unittest`; orkestrasi GNU Make.
- Docker tanpa sudo; `driftlab` port **8100**, salinan bersih **8101** (D8).

### 🚨 `9router.service` — JANGAN PERNAH DISENTUH (D22-A · AGENTS.md §0)
systemd **user**, port **20128**, proxy AI lokal. Dilarang stop/restart/kill/disable/mask/edit/pakai port. Satu
direktori dengan `driftwatch.timer` → unit selalu eksplisit, tanpa wildcard. Cek pasca-P7 → `active`.

## Fakta terverifikasi tentang target — DIKONFIRMASI P2

| Target | Engine | Baseline P6 | Kunci | Pagination / batas |
|---|---|---:|---|---|
| `books` | `httpx+selectolax` | **1.000** | `upc` | `page-{n}.html` 1..50, berhenti saat `li.next a` hilang |
| `quotes` | **`httpx+json`** | **100** | `quote_id` | `/api/quotes?page=N`, berhenti saat `has_next == false` (page 10) |
| `seo` | `httpx+selectolax` | **23** | `url` | 23 URL dari `sitemap.xml` |
| `driftlab` | `httpx+selectolax` | **200** | `item_id` | `page-{n}.html` 1..10 + 200 halaman detail |

**Playwright TIDAK dipasang.** Nol target `js_required`; deliverable bebas dependency browser.

Robots: target publik HTTP 404; `driftlab` 200 `Allow: /`; default D3 1,0 dtk. P2: 0 HTTP 429.

## Halaman demo (D18 — berkas statis lokal, bukan URL publik)

`web/index.html`: berkas mandiri, payload ditanam, dibuka lewat `file://` tanpa server. 3 situs publik
(books 200 · quotes 100 · seo 23); `driftlab` tidak terbit (fixture lokal). Insight **`claude-haiku-4-5`** — $1/$5 per 1 juta token, termurah yang memadai (D14).

## Metrik

| Metrik | Target | Aktual |
|---|---|---|
| P0: tool terverifikasi · error `uv sync` | — · 0 | **10 · 0** |
| P1–P5 (ringkas) | — | **4 target · recon 4/4 · 31 field (27 req) · 12/12 sampel · resume 12→1.000 · gap 1.000 ms** |
| P6: record total · books · dup · required min · test · loop resume | ≥1.000 · ≥1.000 · 0 · ≥98% · — · — | **1.323 · 1.000 · 0 · 100% · 18/18 · 40,927 dtk** |
| P7: timer · NEXT · run unit · target · soak | aktif · waktu · sukses · 4/4 · tanggal | **aktif · 2026-08-28 09:04:10 WIB · 1/1 · 4/4 · 2026-08-27** |
| P8: oracle · kode · alarm sah · false positive · unit | 11/11 · 10 · N · 0 · sukses | **11/11 · 10 · 12 · 0 · sukses** |
| P10: baris terbit · situs · token insight · biaya/hari · kebocoran | ≤200/situs · 3 · N · rendah · 0 | **323 (200+100+23) · 3 · 0 · $0,00000 · 0** |
| P11: `daily.md` · sheet · jargon · notifikasi critical · kebocoran sampel · test | N · 5 · 0 · ≥1 · 0 · ≥6 | **8 · 5 · 0 · 4 · 0 · 9** |
| Gerbang P11: compile · unit · recon · oracle · hash fixture | 0 · lulus · 4/4 · 11/11 · tetap | **0 · 43/43 · 4/4 · 11/11 · `b09a1d…5d3`** |
| `make all` salinan bersih · kebocoran rahasia | exit 0 · 0 | — |
| **Acceptance project** | 12/12 | **3/12 (A8, A9, A10)** |

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
**P10:** `src/publish.py`, `web/{template,index}.html` + `data{,-books,-quotes,-seo}.json`; publikasi harian; D13/D14/D18 dikunci.
**P11:** `src/{report,test_report}.py`; 8 `daily.md` + `REPORT.xlsx` (gitignored); `assets/sample_{daily.md,REPORT.xlsx}`; `make report`/`make weekly`; langkah (6) `daily_run.sh`.

## Catatan P11 (2026-08-28)

Validator jargon jalan di dalam build (`exit 2`, `daily.md` tidak ditulis), tetapi nilai yang
dikutip apa adanya dari sumber dikecualikan — halaman HTTPX benar-benar berjudul "Exceptions".
Notifikasi hanya untuk `critical`; `next_action` (perintah + nama berkas kode) tidak pernah ikut
ke klien. `daily_run.sh` langkah (6) memanggil `report.py --notify`: gagal → pesan ke stderr +
unit systemd gagal, snapshot tetap utuh (`|| true` tanpa pesan sudah hilang seluruhnya).
Karena `report` masuk orkestrasi harian, `soak_dibuka` tetap **2026-08-28**: versi ini mulai
berjalan pada hari yang sama, jadi tidak ada bukti soak versi lama yang dipertahankan.

Oracle alarm **wajib** lewat `make oracles` (server segar): `run_oracles.py` langsung pada server
yang sudah dipakai `--verify` membuat DO-06 gagal `alarms=[]` — server basi, bukan regresi
detector. Dicatat di `AGENTS.md` §4.

## Blocker & keputusan terbuka
- **Blocker: tidak ada.**
- 🔓 **D20** repo publik → **P12, butuh izin eksplisit user**. D15 ditulis saat pertama dipakai.
- `ANTHROPIC_API_KEY` **kosong** → insight P10 = 0 token, $0. Isi kunci lalu `uv run --no-sync python src/publish.py` (≈ $0,005/hari).
