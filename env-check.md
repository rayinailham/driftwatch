# env-check.md — DriftWatch

**Tanggal verifikasi:** 2026-08-27
**Mesin:** CachyOS Linux (turunan Arch), kernel `7.1.5-1-cachyos`, Hyprland/Wayland
**Fase:** P0 — Bootstrap & Environment
**Metode:** semua angka di bawah adalah keluaran perintah nyata di sesi ini, bukan salinan dokumen.

---

## 1. Tool dasar

| Tool | Perintah | Hasil nyata |
|---|---|---|
| uv | `uv --version` | `uv 0.12.1 (329541a50 2026-07-31 x86_64-unknown-linux-gnu)` |
| Python (sistem) | `python3 --version` | `Python 3.14.6` |
| Node | `node --version` | `v24.16.0` |
| Docker | `docker --version` | `Docker version 29.6.2, build dfc4efb1e2` |
| jq | `jq --version` | `jq-1.8.2` |
| SQLite | `sqlite3 --version` | `3.53.4 2026-07-24` |
| ffmpeg | `ffmpeg -version \| head -1` | `ffmpeg version n8.1.2` |
| systemd (user) | `systemctl --user --version \| head -1` | `systemd 261 (261.2-1-arch)` |
| git | `git --version` | `git version 2.55.0` |
| make | `make --version \| head -1` | `GNU Make 4.4.1` |

**Terverifikasi: 10 tool.**

### Yang TIDAK ada (dan konsekuensinya)

| Hilang | Konsekuensi |
|---|---|
| `just` | Runner tugas memakai `make` (D10). `Makefile` wajib `.NOTPARALLEL:` karena `MAKEFLAGS` shell user memuat `-j16`. |
| `pytest` | Unit test P5 memakai `unittest` stdlib. Tidak dipasang — stdlib cukup dan menekan dependency deliverable. |

Tidak ada tool wajib yang hilang. Tidak ada `pip install` global, tidak ada `sudo`,
tidak ada `pacman`, tidak ada `playwright install-deps` di sesi ini.

---

## 2. `systemctl --user` — KEPUTUSAN

```
$ systemctl --user --version | head -1
systemd 261 (261.2-1-arch)
```

**Tersedia. D9 (penjadwalan systemd user timer 09:00 WIB) TETAP BERLAKU.**
Tidak perlu jatuh ke cron. P7 boleh memasang `driftwatch.timer` ke `~/.config/systemd/user/`.

Timezone mesin sudah benar untuk D3:
```
$ timedatectl show -p Timezone --value
Asia/Jakarta
```

### 🚨 `9router.service` — diperiksa, TIDAK disentuh (D22-A)

```
$ systemctl --user is-active 9router.service
active
```

Hanya `is-active` (baca-saja) yang dijalankan. Tidak ada `stop`/`restart`/`kill`/`disable`/
`mask`/edit unit, tidak ada wildcard `systemctl --user`, dan port `20128` tidak dipakai.
Ia tinggal satu direktori dengan `driftwatch.timer` yang akan dipasang P7 → di sesi mana pun
nama unit disebut eksplisit, tidak pernah `'*'`.

---

## 3. Runtime Python project

```
$ uv sync
Resolved 34 packages in 0.86ms
Checked 31 packages in 0.17ms
(exit 0, 0 error)

$ uv run --no-sync python -c "import httpx, selectolax, tenacity, typer, pydantic; print('deps ok')"
deps ok
```

| Paket | Versi terpasang |
|---|---|
| python (venv) | 3.13.13 |
| httpx | 0.28.1 |
| selectolax | 0.4.11 |
| tenacity | 9.1.4 |
| typer | 0.27.1 |
| pydantic | 2.13.4 |
| openpyxl | 3.1.5 |
| python-dateutil | 2.9.0.post0 |
| anthropic | 1.1.0 |

**Playwright sengaja TIDAK dipasang di P0.** Ia baru ditambahkan kalau P2 membuktikan ada
target `render_mode = js_required` (`AGENTS.md` §2). Memasang browser 2 GB untuk kemungkinan
yang belum terbukti adalah kebiasaan yang justru dihindari project ini.

### Anomali tercatat

- **Python venv (3.13.13) ≠ python3 sistem (3.14.6).** `uv` memilih interpreter miliknya
  sendiri untuk memenuhi `requires-python = ">=3.12"`. Bukan error, tapi berarti perintah
  produksi wajib lewat `uv run`, jangan `python3` langsung — hasilnya beda venv.

---

## 4. Infra device dipakai ulang, bukan dipasang ulang (D21/D22-B)

```
$ du -sh ~/.cache/uv              → 1.6G
$ du -sh ~/.cache/ms-playwright   → 2.0G
```

Image relevan yang **sudah ada** (nol unduhan):
- `plantuml/plantuml-server:jetty` — diagram P12
- `pandoc/core:latest` — PDF studi kasus P12 (bukan `texlive/texlive` 8,73 GB)

Container yang sedang hidup saat pemeriksaan:
`crosscheck-tut-wordpress-1`, `crosscheck-tut-db-1` (⚠️ target uji project 1 — tidak disentuh),
`tidb-server`, `tidb-tikv`, `tidb-pd`, `redis-db`.

**Di sesi ini: 0 `docker pull`, 0 service infra dinyalakan/dimatikan, 0 edit
`infra/docker-compose.yml`.** Cache Playwright tidak diprune (`chromium-1228` dipakai MCP
`chrome-devtools`).

Dilarang jadi runtime dependency deliverable dan memang tidak dipakai:
MySQL `:3306`, Redis `:6379`, TiDB `:4000`, MCP `excel`. Checkpoint tetap SQLite,
laporan tetap `openpyxl`, fixture tetap `http.server` stdlib.

---

## 5. Struktur & rahasia

Struktur berdiri sesuai P0 langkah 3:
`src/ scripts/ recon/ fixtures/ deploy/ web/ assets/ data/ reports/ docs/ phases/`
(direktori kosong dipertahankan di repo dengan `.gitkeep`; `data/` dan `reports/` gitignored).

**Tidak ada `docker-compose.yml` / `compose.yaml` / `docker-compose.yaml`** (D8) —
dibuktikan `ls` yang mengembalikan `No such file or directory` untuk ketiganya.

`.env` dan `.env.example` punya kunci yang identik (nilai `.env.example` kosong):
`ANTHROPIC_API_KEY`, `DRIFTWATCH_UA`, `LAB_PORT`, `TZ`.

```
$ git check-ignore -v .env data reports progress.db
.gitignore:2:.env        .env
.gitignore:7:data/       data
.gitignore:8:reports/    reports
.gitignore:10:progress.db progress.db

$ git check-ignore -v auth/ fixtures/site/ logs/ x.db .venv/ __pycache__/ .playwright-mcp/
.gitignore:3:auth/               auth/
.gitignore:24:fixtures/site/     fixtures/site/
.gitignore:11:logs/              logs/
.gitignore:9:*.db                x.db
.gitignore:14:.venv/             .venv/
.gitignore:15:__pycache__/       __pycache__/
.gitignore:21:.playwright-mcp/   .playwright-mcp/

$ git check-ignore -v .env.example pyproject.toml uv.lock recon/.gitkeep
(exit 1 — tidak ada yang cocok; benar, keempatnya memang harus masuk repo)
```

---

## 6. Repo (D19)

```
$ git remote -v
origin  git@rayin-personal:rayinailham/driftwatch.git (fetch)
origin  git@rayin-personal:rayinailham/driftwatch.git (push)

$ ssh -T git@rayin-personal
Hi rayinailham! You've successfully authenticated, but GitHub does not provide shell access.

$ git branch --show-current   → main
$ git rev-parse --abbrev-ref '@{upstream}'   → origin/main
```

Akun **personal** `rayinailham` lewat alias SSH `rayin-personal`. Akun work `rayin-kantor`
dan sesi MCP GitHub miliknya tidak dipakai. Repo tetap **privat** (🔓 D20 butuh izin terpisah).

---

## 7. Ringkasan

`10 tool terverifikasi · 0 error uv sync · 9 paket Python terpasang · systemctl --user tersedia (D9 aman) · 9router active & tidak disentuh · 0 docker pull · remote personal tersambung`
