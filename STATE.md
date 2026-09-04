# DriftWatch — STATE

> Ditulis ulang di akhir tiap sesi. Satu-satunya memori antar sesi. Jaga < 100 baris.

**Diperbarui:** 2026-09-04 · **Status:** ✅ **PROJECT COMPLETE** — 13/13 fase · acceptance **12/12**
**Fase aktif:** — · **Sisa pekerjaan berkode:** tidak ada.

## Status fase

| Fase | Status | Catatan |
|---|---|---|
| P0 Bootstrap | ✅ | `env-check.md`, 10 tool, `uv sync` 0 error · `02469f0` |
| P1 Target & Etika | ✅ | 4 target; HTTPX 7/7; fixture 200; oracle 2/11 · `0f69f5f` |
| P2 Recon | ✅ | 4 recon sah 4/4; quotes → `httpx+json` (8→1 request) · `2d1f585` |
| P3 Kontrak Data | ✅ | 4 kontrak; 31 field (27 required); 12/12 sampel · `9e81409` |
| P4 Mesin Scraper | ✅ | 6/6 komponen; cicip 3/3 valid; gap publik min 1.000 ms · `eadb3b2` |
| P5 Validasi & Resume | ✅ | 3/3 manual; resume 12→1.000; 17/17 test · `e551205` |
| P6 Panen Penuh | ✅ | 4 target; 1.323 record; required 100% · `e6ad2f3` |
| P7 Penjadwalan | ✅ | timer aktif; unit sukses · `c9978ec` |
| P8 Diff & Alarm | ✅ | 10 kode; 11/11 oracle; 0 false positive · `eb46245` |
| P9 Soak 3 Hari | ✅ | 09-01…09-03 berturut; 12/12 run exit 0; 0 alarm; 0 intervensi · `c769cd8` |
| P10 Demo + LLM | ✅ | 323 baris; 3 situs; D13/D14/D18 dikunci · `6f7409d` |
| P11 Laporan Klien | ✅ | 8 `daily.md`; 5 sheet; 0 jargon · `49c80e1` |
| P12 Packaging | ✅ | `make all` salinan bersih exit 0 · v1–v6 lahir · README publik · audit 0 |

## Metrik final

| Metrik | Target | Aktual |
|---|---|---|
| Dataset harian | ≥ 1.000, dup 0 | **1.323 record/hari** · books 1.000 · driftlab 200 · quotes 100 · seo 23 · **0 duplikat** |
| Kelengkapan field `required` | ≥ 98% | **100,0%** di keempat target (27 field required dari 31) |
| Tahan diputus | lanjut, tak mengulang | `kill -9` → `--resume`: **12 → 1.000**, 0 duplikat (`docs/RESUME_PROOF.md`) |
| Kesopanan request | ≥ 900 ms | jeda minimum teramati **1.000–1.001 ms** di 3 target publik |
| Jalan sendiri | 3 hari berturut | **3 tanggal berturut · 12/12 run exit 0 · 0 alarm · 0 intervensi** (`docs/SOAK_PROOF.md`) |
| Alarm terbukti patah | 11/11 | **11/11 PASS, 0 false positive** (`make oracles`, exit 0) |
| Unit test | lulus | **48/48 OK** (`make test`), di repo utama dan salinan bersih |
| `make all` salinan bersih | exit 0 | **exit 0 dalam 1.086 dtk = 18 mnt 6 dtk**, 1.323 record, **0 pemanggilan `docker`** |
| Kebocoran rahasia | 0 | **0 kelas RAHASIA** (`make audit` exit 0, repo utama 91 berkas + salinan bersih 92) |
| Video demo | 60 dtk | **59,2 dtk · 1920×1080 · h264 · tanpa audio** (`assets/v1_resume_demo.mp4`) |
| Biaya LLM | terukur | **$0,00/hari** — `ANTHROPIC_API_KEY` kosong, jatuh ke mode tanpa LLM |
| **Acceptance project** | 12/12 | **12/12 ✅** |

## Artefak final

**Repo:** <https://github.com/rayinailham/driftwatch> — akun personal `rayinailham`, **PUBLIK sejak 2026-09-04** (D20).
**Kode (`src/`):** `contracts`, `validate`, `scrape`, `store`, `engines/{http_html,http_json}`,
`export`, `diff`, `alarm`, `publish`, `report`, **`env`** (baru P12: `.env` + `LAB_PORT`) + 5 modul test.
**Skrip:** `daily_run.sh`, `lab_{up,down}.sh`, `lab_serve.py`, `gen_fixture.py`, `drift_lab.py`,
`run_oracles.py`, `validate_recon.py`, `prune.sh`, `mark_run_failed.py`, `check_missing.sh`,
**`secret_audit.py`**, **`make_visuals.py`**, **`build_case_study.sh`**, **`build_demo_video.sh`**,
**`demo_resume.sh`**, **`demo_alarm.sh`** (enam terakhir lahir di P12, semuanya waktu-bangun).
**Makefile:** `setup lab-up lab-down oracles harvest diff report weekly publish test audit prune all help`
— `MAKEFLAGS := -j16` + `.NOTPARALLEL:` dipertahankan.
**Aset:** `v1_resume_demo.mp4`, `v2_architecture.png` (+`.puml`), `v3_diff_timeline.png`,
`v4_alarm_matrix.png`, `v5_tier_drop.png`, `v6_case_study.pdf` (+`.md`), 2 contoh laporan.
**Dokumen:** `README.md` publik 7 bagian · `docs/` 15 berkas termasuk **`SOAK_PROOF.md`** dan **`PITCH.md`**.

## Fakta mesin yang masih berlaku

- `driftlab` port **8100**; salinan bersih **8101**; sandbox video **8102**. `LAB_PORT` sekarang
  benar-benar dibaca (`src/env.py`) — sebelum P12 ia ada di `.env` tapi tidak pernah dipakai.
- Venv 3.13.13 ≠ sistem 3.14.6 → produksi wajib `uv run`; orkestrasi GNU Make (D10, `just` tidak ada).
- Nol Docker di jalur runtime. Docker hanya dipakai waktu-bangun: PlantUML `:20080` dan `pandoc/core`.

### 🚨 `9router.service` — JANGAN PERNAH DISENTUH (D22-A · AGENTS.md §0)
systemd **user**, port **20128**, proxy AI lokal. Sesi ini tidak menyentuhnya sama sekali.

## Yang tersisa untuk user (bukan pekerjaan berkode)

1. **`docs/PITCH.md` belum pernah diucapkan keras.** Panjangnya 138 kata → estimasi 53–59 detik
   dari jumlah kata, **bukan stopwatch**. Baca sekali, ganti angkanya. Ini satu-satunya kotak
   DoD P12 yang ditandai `[~]`, bukan `[x]`.
2. **Batas bukti P9 yang dinyatakan terbuka.** 2 dari 3 pemicuan timer terbukti langsung di
   `journalctl`; pemicuan 2026-09-01 terbukti lewat watchdog H+1 + `run.json` karena jurnal
   mesin ini tidak menjangkau lebih awal dari `2026-09-01T20:53:14`. Kalau bukti `journalctl`
   penuh dibutuhkan, biarkan timer jalan 3 hari lagi lalu panen ulang — pipeline-nya tidak
   perlu diubah apa pun.
3. **Email pribadi ada di repo publik** (repo sudah publik sejak 2026-09-04). `DRIFTWATCH_UA` memuat `mailto:` alamat Anda di
   12 berkas ter-track. Itu **diwajibkan D3** (User-Agent jujur berisi kontak) dan bukan
   kebocoran rahasia, tapi sejak repo publik alamat itu bisa dipanen bot spam. Kalau
   mengganggu, ganti ke alias kontak lalu `make audit` lagi.
4. **`ANTHROPIC_API_KEY` kosong** → insight LLM 0 token, $0. Isi kunci lalu
   `uv run --no-sync python src/publish.py` kalau ingin blok ringkasan AI terisi (≈ $0,005/hari).
5. Timer harian dan watchdog **masih menyala**. Matikan dengan
   `systemctl --user disable --now driftwatch.timer driftwatch-watchdog.timer` kalau tidak
   ingin panen berlanjut. **Sebut unitnya eksplisit, jangan pernah wildcard** (D22-A).

## Jebakan yang sudah dibayar (jangan diulang)

- Oracle alarm wajib lewat `make oracles` (server segar); `run_oracles.py` pada server bekas
  `--verify` membuat DO-06 gagal `alarms=[]` — server basi, bukan regresi detector.
- `kill -9 $!` pada `uv run …` hanya membunuh pembungkusnya; anak `python` lolos dan run
  selesai normal padahal terlihat "dibunuh". Panggil `.venv/bin/python` langsung.
- Audit yang memindai nol berkas akan selalu melapor LULUS. Gerbang wajib diuji dengan
  kunci palsu yang ditanam, bukan diasumsikan bekerja.
- Setiap perubahan `daily_run.sh` me-reset `soak_dibuka`. P12 sengaja tidak menyentuhnya.
