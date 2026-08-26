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
- [ ] Perintah versi di langkah 1 dijalankan; hasilnya ditempel di `env-check.md`
- [ ] `uv sync` sukses dan `import` 5 paket inti berhasil
- [ ] Struktur folder sesuai langkah 3; **tidak ada `docker-compose.yml`** (D8)
- [ ] Cek langkah 2b dijalankan; 0 `docker pull`, 0 service infra dinyalakan tanpa izin
- [ ] `.env.example` ada, `.env` ada dan **tidak** ter-track (`git check-ignore` membuktikan)
- [ ] `env-check.md` berisi hasil nyata + status `systemctl --user`
- [ ] `ssh -T git@rayin-personal` menyapa `rayinailham`; `git remote -v` menunjuk alias itu
- [ ] **Commit + push berhasil** (D19)

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
