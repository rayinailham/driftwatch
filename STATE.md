# DriftWatch — STATE

> File hidup. Dibaca di awal tiap sesi, ditulis ulang di akhir tiap sesi.
> Ini satu-satunya memori antar sesi agent. Jaga tetap pendek (< 100 baris).

**Terakhir diperbarui:** 2026-08-27 (perencanaan; belum ada kode)
**Status project:** ⬜ **BELUM MULAI** — 0/13 fase selesai
**Fase aktif:** —
**Fase berikutnya:** **P0 — Bootstrap & Environment**
**soak_dibuka:** — (diisi di P7)

---

## Status fase

| Fase | Status | Catatan |
|---|---|---|
| P0 Bootstrap | ⬜ belum | uv project, struktur folder, `env-check.md`, repo git |
| P1 Target & Etika | ⬜ belum | 4 target, gerbang etika `seo`, fixture `driftlab` :8100 |
| P2 Recon | ⬜ belum | 4 `recon/*.json`, keputusan engine per target |
| P3 Kontrak Data | ⬜ belum | `contracts.py` + `validate.py`, D17 dikunci |
| P4 Mesin Scraper | ⬜ belum | 6 komponen wajib, run cicip 2 halaman |
| P5 Validasi & Resume | ⬜ belum | 3 record manual, kill→resume, unit test |
| P6 Panen Penuh | ⬜ belum | ≥ 1.000 record, CSV+JSONL, kamus data |
| P7 Penjadwalan | ⬜ belum | systemd timer 09:00 WIB — **dahulukan**, membuka jam soak |
| P8 Diff & Alarm | ⬜ belum | 10 kode alarm, 11/11 drift oracle |
| P9 Soak 3 Hari | ⬜ belum | gerbang jam dinding, dikerjakan di latar |
| P10 Demo + LLM | ⬜ belum | halaman publik + insight Claude API ber-pagar |
| P11 Laporan Klien | ⬜ belum | `daily.md` 0 jargon + `REPORT.xlsx` 5 sheet |
| P12 Packaging | ⬜ belum | video 60 dtk, `make all`, README publik, audit |

Legenda: ⬜ belum · 🟨 jalan · ✅ selesai · 🟥 blocked

## Fakta terverifikasi tentang mesin ini

*(diwarisi dari project 1 `../crosscheck/`; verifikasi ulang di P0 sebelum dipercaya)*

- `uv`, `python3`, `node`, `docker`, `ffmpeg`, `jq` → ada; `wf-recorder` 0.6.0 di `~/.local/bin`
- **tidak ada `just`** (→ `make`, D10) · **tidak ada `pytest`** (→ `unittest`)
- `MAKEFLAGS` di shell user memuat `-j16` → `Makefile` wajib `.NOTPARALLEL:`
- Docker jalan tanpa sudo; `sudo` butuh password dan tidak ada askpass di sesi agent
- Playwright: build Ubuntu di Arch; jangan `install-deps` / `--with-deps`.
  Jangan hapus `chromium-1228` (dipakai MCP `chrome-devtools`)
- Port terpakai user: 8000, 3000, 3100, 3170, 20080, 4000, 2379, 5540, 3306, 6379, 943, 9443, 1194
  → `driftlab` memakai **8100**, salinan bersih **8101** (D8)
- ⬜ **belum diverifikasi:** `systemctl --user` tersedia atau tidak (cek di P0; D9 bergantung padanya)

## Fakta terverifikasi tentang target

*(kosong — diisi P1 & P2)*

- `books.toscrape.com` — ⬜ robots belum dicek
- `quotes.toscrape.com` — ⬜ robots belum dicek
- `seo` — ⬜ situs belum dipilih (🔓 D16)
- `driftlab` — ⬜ fixture belum dibangun

## Metrik

| Metrik | Target | Aktual |
|---|---|---|
| Record dataset (`books`) | ≥ 1.000 | — |
| Duplikat | 0 | — |
| Kelengkapan field `required` | ≥ 98% | — |
| Record diverifikasi manual | 3 | — |
| Bukti kill → resume | ada, duplikat 0 | — |
| `observed_min_gap_ms` | ≥ delay × 900 | — |
| Hari soak berturut | 3 | — |
| Drift oracle | 11/11 | — |
| Kode alarm terimplementasi | 10 | — |
| Laporan diff harian | tiap hari | — |
| Halaman demo | hidup | — |
| `make all` salinan bersih | exit 0 | — |
| Kebocoran rahasia | 0 | — |
| **Acceptance project** | 12/12 | **0/12** |

## Artefak yang sudah lahir

**Perencanaan (2026-08-27):**
- `AGENTS.md`, `PLAN.md`, `KICKSTART.md`, `STATE.md`, `README.md`, `.gitignore`
- `docs/`: `DECISIONS.md` (D1–D19 terkunci, D16/D17/D18/D20 masih 🔓), `SCHEMA.md` (draf,
  dikunci P3), `ETHICS.md`, `PIPELINE.md`, `TOOLS.md`, `CLIENT_REPORT.md`, `ACCEPTANCE.md`
  (A1–A12), `DRIFT_ORACLES.md` (DO-01..DO-11)
- `phases/phase-00..12` (13 file)

**Kode:** belum ada.

## Catatan untuk user

1. **Git sudah diizinkan (D19):** akun personal `rayinailham` lewat SSH alias `rayin-personal`,
   repo `driftwatch` **privat**. Commit + push wajib di akhir tiap fase.
   Repo jadi publik masih butuh izin terpisah (🔓 D20).
2. **P7 sengaja didahulukan.** Begitu timer nyala, jam 3 hari untuk P9 berjalan sendiri
   sementara P8, P10, P11 dikerjakan. Jangan menunggu menganggur.
3. **Empat keputusan masih terbuka:** 🔓 D16 (situs `seo`, P1), 🔓 D17 (field final, P3),
   🔓 D18 (cara publikasi demo, P10), 🔓 D20 (repo publik, P12 — butuh izin user).
4. Mesin dipakai user untuk development paralel: jangan restart container di luar
   `driftwatch-lab`, jangan sentuh `/home/rayin/infra/`.
