# P0 — Bootstrap & Environment

**Tujuan sesi:** runtime Python siap, struktur folder berdiri, bukti verifikasi tercatat.
Tidak ada logika scraping apa pun di fase ini.

**Prasyarat:** tidak ada.
**Read-set:** `STATE.md` + file ini saja.
**Budget:** ringan. Sesi ini seharusnya < 15% context.

---

## Langkah

### 1. Verifikasi tool dasar
```bash
uv --version && python3 --version && node --version && docker --version \
  && jq --version && sqlite3 --version && ffmpeg -version | head -1 \
  && systemctl --user --version | head -1
```
```bash
systemctl --user is-active 9router.service    # WAJIB `active` — jangan pernah diubah (D22-A)
```
Catat yang tidak ada. `systemctl --user` wajib ada — kalau tidak, D9 gugur dan
penjadwalan jatuh ke cron; catat itu sebagai blocker di `STATE.md`.

### 2. Inisialisasi project Python
`pyproject.toml` dengan dependency:
`httpx`, `selectolax`, `tenacity`, `typer`, `pydantic`, `openpyxl`, `python-dateutil`, `anthropic`

Semua paket ini sudah pernah diunduh ke cache global `~/.cache/uv` (1,6 GB terisi),
jadi `uv sync` di sini hampir tidak menyentuh jaringan — venv per project, cache paket
bersama (D21).

Playwright **tidak** dipasang di P0. Ia hanya ditambahkan kalau P2 membuktikan ada target
`js_required` (D-lapis di `AGENTS.md` §2). Memasang browser 2 GB untuk kemungkinan yang
belum terbukti adalah kebiasaan yang justru dihindari project ini.

```bash
cd /home/rayin/Projects/Testing/driftwatch
uv sync
uv run python -c "import httpx, selectolax, tenacity, typer, pydantic; print('deps ok')"
```

### 2b. Jangan pasang ulang yang sudah ada (D21)

Sebelum menambah tool apa pun, cek dulu apakah device sudah punya:
```bash
ls ~/.cache/uv >/dev/null && du -sh ~/.cache/uv          # cache paket Python bersama
du -sh ~/.cache/ms-playwright                            # browser bersama, jangan diprune
docker images --format '{{.Repository}}' | sort -u | head -40
docker ps --format '{{.Names}}'                          # apa yang SEDANG hidup
```
Image yang sudah ada dan relevan: `plantuml/plantuml-server:jetty`, `pandoc/core`.
Jangan `docker pull` apa pun di fase ini. Service infra yang mati boleh dinyalakan
sesuai kebutuhan (D22-B) — **kecuali** `9router.service` yang tidak pernah disentuh (D22-A).

### 3. Struktur folder
```
driftwatch/
├── src/          kode produksi (diisi P3–P4)
├── scripts/      helper: lab_up.sh, drift_lab.py, daily_run.sh
├── recon/        hasil P2 (masuk repo — ini bukti "saya memetakan dulu")
├── fixtures/     sumber fixture driftlab
├── deploy/       unit systemd
└── (TIDAK ada docker-compose.yml — fixture pakai http.server stdlib, D8)
├── data/         GITIGNORED
├── reports/      GITIGNORED
├── web/          halaman demo (P10)
├── assets/       visual portofolio (P12)
├── docs/         sudah ada
└── phases/       sudah ada
```

### 4. `.env.example` + `.env`
```
ANTHROPIC_API_KEY=
DRIFTWATCH_UA=DriftWatch/1.0 (+mailto:rayinailham9@gmail.com)
LAB_PORT=8100
TZ=Asia/Jakarta
```
`.env.example` masuk repo (nilai kosong). `.env` tidak pernah.

### 5. Verifikasi `.gitignore`
Pastikan memuat: `.env`, `data/`, `reports/`, `auth/`, `*.db`, `.venv/`, `__pycache__/`,
`.playwright-mcp/`, `fixtures/site/`.
Buktikan: `git check-ignore -v .env data reports` (setelah `git init` di langkah 7).

### 6. Tulis `env-check.md`
Isi: versi tiap tool (hasil nyata, bukan salinan perintah), daftar yang tidak ada,
tanggal, catatan anomali, dan keputusan apakah `systemctl --user` tersedia.

### 7. Verifikasi repo (D19) — **sudah dibuat saat perencanaan**

Repo sudah ada dan commit pertama sudah di-push. Fase ini hanya memverifikasinya:
```bash
git remote -v                # origin = git@rayin-personal:rayinailham/driftwatch.git
ssh -T git@rayin-personal    # harus menyapa "rayinailham"
git log --oneline | head -3
git check-ignore -v .env data reports
```
Jangan pakai akun work. Jangan menjadikan repo publik (butuh izin terpisah, 🔓 D20).

---

## Output fase
- `pyproject.toml`, `uv.lock`
- `env-check.md`
- struktur folder + `.env.example`
- repo git terverifikasi terhubung ke remote personal

## Definition of Done

*(Dicentang 2026-08-27 dengan keluaran perintah nyata; rincian penuh di `env-check.md`.)*

- [x] **Perintah versi di langkah 1 dijalankan; hasilnya ditempel di `env-check.md`**
  ```
  uv 0.12.1 (329541a50 2026-07-31 x86_64-unknown-linux-gnu)
  Python 3.14.6
  v24.16.0
  Docker version 29.6.2, build dfc4efb1e2
  jq-1.8.2
  3.53.4 2026-07-24 19:02:57 ... (64-bit)
  ffmpeg version n8.1.2 Copyright (c) 2000-2026 the FFmpeg developers
  systemd 261 (261.2-1-arch)
  ```
  Tambahan: `git version 2.55.0`, `GNU Make 4.4.1`. **10 tool terverifikasi.**
  Tidak ada: `just` (→ `make`, D10), `pytest` (→ `unittest`).
  `systemctl --user is-active 9router.service` → `active` (baca-saja, tidak disentuh, D22-A).

- [x] **`uv sync` sukses dan `import` 5 paket inti berhasil**
  ```
  $ uv sync
  Resolved 34 packages in 0.86ms
  Checked 31 packages in 0.17ms          (exit 0)

  $ uv run --no-sync python -c "import httpx, selectolax, tenacity, typer, pydantic; print('deps ok')"
  deps ok
  ```
  Versi terpasang: httpx 0.28.1 · selectolax 0.4.11 · tenacity 9.1.4 · typer 0.27.1 ·
  pydantic 2.13.4 · openpyxl 3.1.5 · python-dateutil 2.9.0.post0 · anthropic 1.1.0.
  Venv Python 3.13.13 (≠ `python3` sistem 3.14.6 — dicatat sebagai anomali di `env-check.md`).
  Playwright **tidak** dipasang, sesuai jebakan fase ini.

- [x] **Struktur folder sesuai langkah 3; tidak ada `docker-compose.yml` (D8)**
  ```
  $ ls -d src scripts recon fixtures deploy web assets data reports docs phases
  assets  data  deploy  docs  fixtures  phases  recon  reports  scripts  src  web

  $ ls docker-compose.yml compose.yaml docker-compose.yaml
  ls: cannot access 'docker-compose.yml': No such file or directory
  ls: cannot access 'compose.yaml': No such file or directory
  ls: cannot access 'docker-compose.yaml': No such file or directory
  ```
  Direktori kosong dipertahankan di repo lewat `.gitkeep`
  (`src/ scripts/ recon/ fixtures/ deploy/ web/ assets/`); `data/` dan `reports/` gitignored.

- [x] **Cek langkah 2b dijalankan; 0 `docker pull`, 0 service infra dinyalakan tanpa izin**
  ```
  $ du -sh ~/.cache/uv              → 1.6G
  $ du -sh ~/.cache/ms-playwright   → 2.0G
  ```
  Image relevan sudah ada: `plantuml/plantuml-server:jetty`, `pandoc/core:latest`.
  Container hidup saat cek: `crosscheck-tut-wordpress-1`, `crosscheck-tut-db-1` (tidak disentuh),
  `tidb-server`, `tidb-tikv`, `tidb-pd`, `redis-db`.
  Sesi ini: **0 `docker pull`, 0 `start`/`stop` service infra, 0 edit `docker-compose.yml`,
  0 prune cache Playwright.**

- [x] **`.env.example` ada, `.env` ada dan tidak ter-track**
  ```
  $ git check-ignore -v .env data reports progress.db
  .gitignore:2:.env         .env
  .gitignore:7:data/        data
  .gitignore:8:reports/     reports
  .gitignore:10:progress.db progress.db

  $ git check-ignore -v auth/ fixtures/site/ logs/ x.db .venv/ __pycache__/ .playwright-mcp/
  .gitignore:3:auth/             auth/
  .gitignore:24:fixtures/site/   fixtures/site/
  .gitignore:11:logs/            logs/
  .gitignore:9:*.db              x.db
  .gitignore:14:.venv/           .venv/
  .gitignore:15:__pycache__/     __pycache__/
  .gitignore:21:.playwright-mcp/ .playwright-mcp/

  $ git check-ignore -v .env.example pyproject.toml uv.lock recon/.gitkeep
  (exit 1 — tidak ada yang cocok; benar, keempatnya memang masuk repo)
  ```
  Kunci `.env` dan `.env.example` identik: `ANTHROPIC_API_KEY`, `DRIFTWATCH_UA`,
  `LAB_PORT`, `TZ`.

- [x] **`env-check.md` berisi hasil nyata + status `systemctl --user`**
  `env-check.md` (185 baris) berisi 7 bagian: tool dasar, keputusan `systemctl --user`,
  runtime Python, infra dipakai-ulang, struktur & rahasia, repo, ringkasan.
  **Keputusan: `systemctl --user` TERSEDIA (`systemd 261`) → D9 tetap berlaku, tidak jatuh
  ke cron.** Timezone mesin `Asia/Jakarta` (cocok D3, jadwal 09:00 WIB).

- [x] **`ssh -T git@rayin-personal` menyapa `rayinailham`; `git remote -v` menunjuk alias itu**
  ```
  $ git remote -v
  origin  git@rayin-personal:rayinailham/driftwatch.git (fetch)
  origin  git@rayin-personal:rayinailham/driftwatch.git (push)

  $ ssh -T git@rayin-personal
  Hi rayinailham! You've successfully authenticated, but GitHub does not provide shell access.

  $ git branch --show-current            → main
  $ git rev-parse --abbrev-ref '@{upstream}'  → origin/main
  ```
  Akun work `rayin-kantor` tidak dipakai. Repo tetap privat (🔓 D20).

- [x] **Commit + push berhasil (D19)** — lihat blok "Bukti gerbang commit" di bawah.

## Metrik selesai
`N tool terverifikasi · 0 error uv sync · remote personal tersambung`

## Jebakan
- Jangan `pip install` global. Semua lewat `uv` supaya P12 reproducible.
- Jangan pasang Playwright "untuk jaga-jaga". Tunggu bukti dari P2.
- Jangan `sudo`, `pacman`, `playwright install-deps` (`../AGENTS.md`).

## Sebelum menutup sesi
1. Centang DoD di file ini dengan output nyata.
2. Update `STATE.md`: P0 ✅, versi tool, status `systemctl --user`.
3. `git add -A && git commit -m "P00: bootstrap environment + struktur project" && git push -u origin main`
