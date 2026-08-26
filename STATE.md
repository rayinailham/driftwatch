# DriftWatch — STATE

> Ditulis ulang di akhir tiap sesi. Satu-satunya memori antar sesi. Jaga < 100 baris.

**Diperbarui:** 2026-08-27 · **Status:** 🟨 JALAN — 2/13 fase · **Fase aktif:** — (P1 selesai)
**Fase berikutnya:** **P2 — Recon** · **soak_dibuka:** — (diisi di P7)

## Status fase

| Fase | Status | Catatan |
|---|---|---|
| P0 Bootstrap | ✅ selesai | `env-check.md`, 10 tool, `uv sync` 0 error, remote personal OK |
| P1 Target & Etika | ✅ selesai | 4 target; HTTPX lolos 7/7; fixture 200 item; oracle 2/11 |
| P2 Recon | ⬜ belum | 4 `recon/*.json`, keputusan engine per target |
| P3 Kontrak Data | ⬜ belum | `contracts.py` + `validate.py`, D17 dikunci |
| P4 Mesin Scraper | ⬜ belum | 6 komponen wajib, run cicip 2 halaman |
| P5 Validasi & Resume | ⬜ belum | 3 record manual, kill→resume, unit test (`unittest`) |
| P6 Panen Penuh | ⬜ belum | ≥ 1.000 record, CSV+JSONL, kamus data |
| P7 Penjadwalan | ⬜ belum | systemd timer 09:00 WIB — **dahulukan**, membuka jam soak |
| P8 Diff & Alarm | ⬜ belum | 10 kode alarm, 11/11 drift oracle |
| P9 Soak 3 Hari | ⬜ belum | gerbang jam dinding, bukan sesi kerja |
| P10 Demo + LLM | ⬜ belum | halaman publik + insight Claude API ber-pagar |
| P11 Laporan Klien | ⬜ belum | `daily.md` 0 jargon + `REPORT.xlsx` 5 sheet |
| P12 Packaging | ⬜ belum | video 60 dtk, `make all`, README publik, audit |

Legenda: ⬜ belum · 🟨 jalan · ✅ selesai · 🟥 blocked

## Fakta mesin — DIVERIFIKASI P0 (2026-08-27), bukan warisan

`uv` 0.12.1 · `python3` sistem 3.14.6 · **venv uv 3.13.13** · `node` 24.16.0 ·
`docker` 29.6.2 · `jq` 1.8.2 · `sqlite3` 3.53.4 · `ffmpeg` n8.1.2 · `git` 2.55.0 ·
`make` 4.4.1 — rincian penuh di `env-check.md`.

- ✅ **`systemctl --user` TERSEDIA** (`systemd 261`) → **D9 tetap berlaku**, tidak jatuh ke cron.
  TZ mesin `Asia/Jakarta` (cocok D3, 09:00 WIB). **Bukan blocker.**
- ⚠️ Venv Python (3.13.13) ≠ `python3` sistem (3.14.6) → perintah produksi **wajib** `uv run`.
- **tidak ada `just`** (→ `make`, D10; `Makefile` wajib `.NOTPARALLEL:` karena `MAKEFLAGS=-j16`)
  · **tidak ada `pytest`** (→ `unittest` stdlib)
- Docker tanpa sudo; `sudo` butuh password, tidak ada askpass di sesi agent
- Playwright build Ubuntu di Arch: jangan `install-deps`/`--with-deps`; jangan hapus
  `chromium-1228` (dipakai MCP `chrome-devtools`)
- Port terpakai user: 8000, 3000, 3100, 3170, 20080, 4000, 2379, 5540, 3306, 6379, 943, 9443,
  1194, **20128 (9router)** → `driftlab` memakai **8100**, salinan bersih **8101** (D8)

### 🚨 `9router.service` — JANGAN PERNAH DISENTUH (D22-A)

systemd **user** unit, port **20128**, `~/.config/systemd/user/9router.service`, 9Router local
AI proxy. Dicek P0 dengan `is-active` (baca-saja) → `active`. Dilarang
stop/restart/kill/disable/mask/edit dan dilarang memakai port 20128 — ia proxy AI, matinya bisa
memutus sesi agent sendiri. Ia **satu direktori** dengan `driftwatch.timer` (P7) → **selalu sebut
nama unit eksplisit, jangan pernah wildcard** `systemctl --user`. `daemon-reload` aman.

## Infra device (D21/D22-B) — dicek P0

Cache `uv` 1,6 GB · cache Playwright 2,0 GB (jangan diprune) · image sudah ada:
`plantuml/plantuml-server:jetty` (diagram P12), `pandoc/core` (PDF P12; **bukan** `texlive`).
Hidup saat cek: `crosscheck-tut-*` (⚠️ tanya dulu), `tidb-*`, `redis-db`.
Di P0: **0 `docker pull`, 0 start/stop service, 0 edit `infra/docker-compose.yml`.**
Tidak dipakai walau ada: MySQL/Redis/TiDB (checkpoint wajib SQLite), MCP `excel`
(laporan wajib `openpyxl`, jalan unattended dari systemd).

## Fakta terverifikasi tentang target

`books` robots 404 · `quotes` robots 404 · **`seo` = HTTPX docs** (D16, robots 404,
sitemap 23 URL, gerbang 7/7) · `driftlab` robots `Allow: /`, 200 item deterministik,
`127.0.0.1:8100`, stdlib. Host publik tetap default 1,0 dtk karena tanpa `Crawl-delay`.

## Metrik

| Metrik | Target | Aktual |
|---|---|---|
| P0: tool terverifikasi · error `uv sync` | — · 0 | **10 · 0** |
| P1: target · kandidat SEO · lolos · item · oracle | 4 · ≥3 · 1 · 200 · 2/11 | **4 · 3 · 1 · 200 · 2/11** |
| Record `books` · duplikat · field `required` | ≥1.000 · 0 · ≥98% | — |
| Record manual · kill→resume · gap · hari soak | 3 · dup 0 · ≥delay×900 · 3 | — |
| Drift oracle · kode alarm | 11/11 · 10 | — |
| `make all` salinan bersih · kebocoran rahasia | exit 0 · 0 | — |
| **Acceptance project** | 12/12 | **0/12** |

## Artefak yang sudah lahir

**Perencanaan:** `AGENTS.md`, `PLAN.md`, `KICKSTART.md`, `README.md`, `.gitignore`,
`docs/` (8 file), `phases/phase-00..12` (13 file).

**P0 (2026-08-27):** `pyproject.toml`, `uv.lock`, `env-check.md`, `.env.example`,
struktur folder lengkap; **tidak ada `docker-compose.yml`** (D8).

**Repo (D19):** `git@rayin-personal:rayinailham/driftwatch.git` — privat, akun personal
`rayinailham` (`ssh -T` menyapa benar), branch `main` → `origin/main`.
Commit P0: **`02469f0`** (+1 commit susulan pencatat hash).

**P1 (2026-08-27):** `docs/TARGETS.md`; D16 HTTPX; generator fixture; server stdlib +
PID aman; CLI reset/verify/DO-01/DO-03; kait DO-06/DO-08; hash fixture reproducible.

## Blocker & keputusan terbuka
- **Blocker: tidak ada.**
- 🔓 **D17** field final → **P3** · 🔓 **D18** publikasi demo
  → **P10** · 🔓 **D20** repo publik → **P12, butuh izin eksplisit user**
- ⚠️ D9/D10 belum punya entri sendiri; rapikan saat P7 memakai keduanya.
