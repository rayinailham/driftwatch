# DriftWatch — STATE

> Ditulis ulang di akhir tiap sesi. Satu-satunya memori antar sesi. Jaga < 100 baris.

**Diperbarui:** 2026-09-04 · **Status:** 🟨 JALAN — 12/13 fase · **Fase aktif:** P12 — Packaging
**Fase berikutnya:** **P12 — Packaging** (fase terakhir) · **soak_dibuka:** **2026-08-31** → **P9 DITUTUP 2026-09-04**
(jendela sah 2026-09-01 … 2026-09-03 dipanen penuh; bukti di `docs/SOAK_PROOF.md`.)

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
| P9 Soak 3 Hari | ✅ selesai | 3 tanggal berturut 09-01…09-03 · 12/12 run `exit 0` · 1.323 rec/hari · 0 alarm · 0 intervensi · `docs/SOAK_PROOF.md` |
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
`driftlab` = fixture lokal `:8100`, dinyalakan `daily_run.sh` langkah (0) — **bukan** server yang hidup sendiri (D24).
Demo (D18): `web/index.html` mandiri, payload ditanam, `file://` tanpa server; 3 situs publik saja
(`driftlab` tidak terbit). Insight **`claude-haiku-4-5`** — $1/$5 per 1 juta token (D14).

## Metrik

| Metrik | Target | Aktual |
|---|---|---|
| P0–P5 (ringkas) | — | **10 tool · 0 error `uv sync` · 4 target · recon 4/4 · 31 field (27 req) · 12/12 sampel · resume 12→1.000 · gap 1.000 ms** |
| P6 panen · P7 timer · P8 alarm | — | **1.323 record · 0 dup · required 100% · timer aktif 4/4 target · 11/11 oracle · 10 kode · 12 alarm sah · 0 false positive** |
| P9 soak · P10 terbit · P11 laporan | — | **3 tanggal berturut · 12/12 run exit 0 · 0 alarm · 0 intervensi · 323 baris / 3 situs · $0,00000/hari · 8 `daily.md` · 5 sheet · 0 jargon · 4 notifikasi** |
| Gerbang sesi 2026-08-31 | lulus | **48/48 test · oracle 11/11 · recon 4/4 · hash fixture `b09a1d…5d3` tetap** |
| `make all` salinan bersih · kebocoran rahasia | exit 0 · 0 | — (lahir di P12) |
| **Acceptance project** | 12/12 | **10/12 ✅** — sisa **A11 & A12**, dua-duanya menunggu P12 |

## Artefak yang sudah lahir

**Perencanaan:** `AGENTS.md`, `PLAN.md`, `KICKSTART.md`, `README.md`, `docs/` (8), `phases/` (13).
**Repo (D19):** `git@rayin-personal:rayinailham/driftwatch.git` — privat, personal, `main` → `origin/main`.
**Kode (`src/`):** `contracts`, `validate`, `scrape`, `store`, `engines/{http_html,http_json}`,
`export`, `diff`, `alarm`, `publish`, `report` + 5 modul test (48 test).
**Skrip:** `daily_run.sh` (7 langkah + langkah (0) fixture), `lab_{up,down}.sh`, `lab_serve.py`,
`gen_fixture.py`, `drift_lab.py`, `run_oracles.py`, `validate_recon.py`, `prune.sh`, `mark_run_failed.py`.
**Deploy:** `deploy/driftwatch.{service,timer}` + `driftwatch-watchdog.{service,timer}` (D23); `Makefile`
(`oracles`/`report`/`weekly`/`prune`) — **belum ada `all`/`audit`** (P12).
**Data & terbitan:** `recon/*.json` 4/4 sah · `data/`+`reports/` 5 tanggal × 4 target (gitignored) ·
`web/index.html` mandiri (D18) · `assets/sample_{daily.md,REPORT.xlsx}`.
**Dokumen:** `docs/` 12 berkas (TARGETS, SCHEMA, DATA_DICTIONARY, MANUAL_VERIFY, RESUME_PROOF,
DRIFT_ORACLES, PIPELINE, ETHICS, CLIENT_REPORT, DECISIONS D1–D24, ACCEPTANCE, TOOLS, **SOAK_PROOF**).

## Jebakan yang sudah dibayar (jangan diulang)

- Validator jargon mengecualikan nilai yang dikutip apa adanya dari sumber — halaman HTTPX
  memang berjudul "Exceptions". Notifikasi hanya `critical`; `next_action` tidak pernah ke klien.
- Oracle alarm **wajib** lewat `make oracles` (server segar). `run_oracles.py` langsung pada
  server bekas `--verify` membuat DO-06 gagal `alarms=[]` — server basi, bukan regresi detector.
- Setiap perubahan `daily_run.sh` me-reset `soak_dibuka`: bukti soak versi lama tidak dipakai.

## Sesi 2026-08-31 — dua cacat ditutup (D24, teks lengkap di `docs/DECISIONS.md`)

1. **`driftlab` mati diam-diam 29–31 Agu** — `daily_run.sh` tidak menyalakan fixture `:8100`.
   Fix: langkah (0) `lab_up.sh` + `trap EXIT lab_down.sh`. Sesudah: **200 record · exit 0 · alarms=[]**.
2. **Laporan membantah dirinya sendiri** — alert append-only masih dikutip setelah run sembuh.
   Fix: `resolved_at` berlingkup `evaluated_codes()`; `report.py` mengabaikan baris tertutup.

## Blocker & keputusan terbuka
- **Blocker: tidak ada.** P9 ditutup 2026-09-04; sisa hanya P12.
- ⚠️ Jurnal mesin ini hanya menjangkau sejak `2026-09-01 20:53` → pemicuan 09-01 terbukti lewat
  watchdog H+1 + `run.json`, bukan baris `journalctl`. Dinyatakan terbuka di `docs/SOAK_PROOF.md`.
- ✅ **D20** repo publik: **izin user sudah diberikan 2026-08-31**, tetapi flip **ditunda** —
  gerbangnya (`make audit` A12 + salinan bersih A11) baru lahir di P12. Jangan dibalik urutannya.
- `ANTHROPIC_API_KEY` **kosong** → insight P10 = 0 token, $0. Isi kunci lalu `uv run --no-sync python src/publish.py` (≈ $0,005/hari).
