# DriftWatch — STATE

> Ditulis ulang di akhir tiap sesi. Satu-satunya memori antar sesi. Jaga < 100 baris.

**Diperbarui:** 2026-09-04 · **Status:** ✅ **PROJECT COMPLETE** — 13/13 fase · acceptance **12/12**
**Fase aktif:** — · **Sisa pekerjaan berkode:** tidak ada · **Jejak resource mesin:** nol (timer dimatikan).

## Status fase — 13/13 ✅

Satu fase = satu commit, tiap commit membawa metriknya (D19). `git log --oneline` adalah
riwayat lengkapnya. Tiga commit terakhir sesi ini:
`c769cd8` P09 soak · `20f7f60` P12 packaging · `711a69a` D20 repo publik.
Sebelumnya: `02469f0` P0 · `0f69f5f` P1 · `2d1f585` P2 · `9e81409` P3 · `eadb3b2` P4 ·
`e551205` P5 · `e6ad2f3` P6 · `c9978ec` P7 · `eb46245` P8 · `6f7409d` P10 · `49c80e1` P11.

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

**Repo:** <https://github.com/rayinailham/driftwatch> — akun personal `rayinailham`,
**PUBLIK sejak 2026-09-04** (D20).
**Kode:** `src/` 11 modul + 5 modul test (48 test); `env.py` baru di P12 (`.env` + `LAB_PORT`).
**Skrip:** 16 berkas; enam lahir di P12 (`secret_audit`, `make_visuals`, `build_case_study`,
`build_demo_video`, `demo_resume`, `demo_alarm`) dan semuanya **waktu-bangun**, bukan runtime.
**Makefile:** `setup lab-up lab-down oracles harvest diff report weekly publish test audit
prune all help` — `MAKEFLAGS := -j16` + `.NOTPARALLEL:` dipertahankan.
**Aset:** `v1_resume_demo.mp4` · `v2_architecture.png` · `v3_diff_timeline.png` ·
`v4_alarm_matrix.png` · `v5_tier_drop.png` · `v6_case_study.pdf` · 2 contoh laporan.
**Dokumen:** `README.md` publik 7 bagian · `docs/` 15 berkas, termasuk `SOAK_PROOF.md` dan `PITCH.md`.

## Fakta mesin yang masih berlaku

- `driftlab` **8100**, salinan bersih **8101**, sandbox video **8102**. `LAB_PORT` sekarang
  benar-benar dibaca (`src/env.py`); sebelum P12 ia ada di `.env` tapi tak pernah dipakai.
- Venv 3.13.13 ≠ sistem 3.14.6 → produksi wajib `uv run`; orkestrasi GNU Make (D10, `just` tidak ada).
- Nol Docker di jalur runtime; Docker hanya waktu-bangun (PlantUML `:20080`, `pandoc/core`).

### 🚨 `9router.service` — JANGAN PERNAH DISENTUH (D22-A · AGENTS.md §0)
systemd **user**, port **20128**, proxy AI lokal. Sesi ini tidak menyentuhnya sama sekali.

## Jejak resource: NOL (dibereskan 2026-09-04)

Project selesai dan **berhenti memakai resource mesin**:

| Tindakan | Hasil |
|---|---|
| `systemctl --user disable --now driftwatch.timer` · idem `driftwatch-watchdog.timer` | dua-duanya `disabled` + `inactive`; `list-timers \| grep driftwatch` **nihil** |
| `rm -rf /tmp/driftwatch-clean /tmp/driftwatch-demo` | **105 MB** dibebaskan |
| `docker stop plantuml-server` | kembali `Exited`, seperti sebelum sesi ini |
| port 8100 · 8101 · 8102 · 8103 · 20080 | semuanya **mati** |
| **`9router.service` (:20128)** | **`active` — tidak disentuh sama sekali** (D22-A) |

Unit `driftwatch{,-watchdog}.{service,timer}` tetap terpasang di `~/.config/systemd/user/`;
menyalakannya lagi cukup `systemctl --user enable --now driftwatch.timer
driftwatch-watchdog.timer` — sebut eksplisit, jangan pernah wildcard (D22-A).
`data/` 16 MB + `reports/` 396 KB tetap sebagai basis bukti (gitignored, tidak tumbuh lagi).

## Yang tersisa untuk user

**Satu, dan itu bukan pekerjaan mesin:** `docs/PITCH.md` belum pernah **diucapkan keras**.
138 kata → 53–59 detik itu **estimasi dari jumlah kata, bukan stopwatch**; agent tidak bisa
membunyikan suara. Baca sekali, ganti angkanya. Ini satu-satunya kotak DoD P12 bertanda
`[~]`, bukan `[x]`.

### Dua hal yang sudah ditutup sebagai keputusan sadar, bukan utang

- **Batas bukti P9.** 2 dari 3 pemicuan timer terbukti langsung di `journalctl`; pemicuan
  2026-09-01 terbukti lewat watchdog H+1 + `run.json` karena jurnal mesin tidak menjangkau
  lebih awal dari `2026-09-01T20:53:14`. Menutupnya menuntut timer jalan 3 hari lagi —
  ditukar dengan jejak resource nol, dan catatannya sudah tertulis apa adanya di
  `docs/SOAK_PROOF.md` serta `docs/ACCEPTANCE.md`. **Tidak dikejar.**
- **Alamat email di repo publik.** Ditanyakan 2026-09-04, user memilih membiarkannya:
  kontak yang bisa dihubungi adalah *fitur* D3, bukan kebocoran. Rinciannya di D3.
  Tidak ada rewrite history, tidak ada force-push.
- `ANTHROPIC_API_KEY` kosong → insight LLM 0 token, **$0**. Isi kunci lalu
  `uv run --no-sync python src/publish.py` kalau blok ringkasan AI ingin terisi (≈ $0,005/hari).

## Jebakan yang sudah dibayar (jangan diulang)

- Oracle alarm wajib lewat `make oracles` (server segar); `run_oracles.py` pada server bekas
  `--verify` membuat DO-06 gagal `alarms=[]` — server basi, bukan regresi detector.
- `kill -9 $!` pada `uv run …` hanya membunuh pembungkusnya; anak `python` lolos dan run
  selesai normal padahal terlihat "dibunuh". Panggil `.venv/bin/python` langsung.
- Audit yang memindai nol berkas akan selalu melapor LULUS. Gerbang wajib diuji dengan
  kunci palsu yang ditanam, bukan diasumsikan bekerja.
- Setiap perubahan `daily_run.sh` me-reset `soak_dibuka`. P12 sengaja tidak menyentuhnya.
