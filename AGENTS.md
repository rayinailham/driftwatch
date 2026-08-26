# AGENTS.md — DriftWatch

Aturan khusus project ini. Aturan lingkungan Arch/Playwright ada di `../AGENTS.md`
dan tetap berlaku penuh — baca itu dulu, jangan diasumsikan sudah hafal.

---

## 1. Larangan keras (tidak bisa dinegosiasi per sesi)

- **Jangan scraping situs yang `robots.txt`-nya melarang path target.** Kalau ketemu larangan,
  BERHENTI dan laporkan ke user. Jangan cari celah, jangan ganti User-Agent supaya lolos.
- **Jangan menembus proteksi.** Tidak ada captcha solver, tidak ada bypass Cloudflare,
  tidak ada stealth fingerprint, tidak ada login ke akun milik orang lain.
- **Jangan menyamar.** User-Agent wajib jujur dan berisi kontak (D3). Dilarang meniru
  string UA browser asli untuk mengelabui target.
- **Jangan redistribusi konten berhak cipta.** Dari situs pihak ketiga hanya boleh diambil
  **metadata** (judul, H1, meta description, tanggal, jumlah kata, jumlah link) — bukan isi artikel.
  Halaman demo publik hanya menampilkan metadata + tautan ke sumber aslinya.
- **Jangan naikkan kecepatan melebihi `crawl_delay` yang tercatat di `recon.json`.**
  Kalau tidak ada `Crawl-delay`, default 1,0 detik per request per host (D3).
- Jangan `sudo`, `pacman`, `playwright install-deps`, atau `--with-deps`. Selalu gagal di Arch.
- Jangan **edit** apa pun di `/home/rayin/infra/`, dan jangan `stop`/`restart`/`down`
  service yang sedang hidup di sana (mesin dipakai user untuk kerja paralel).
  Memakai service yang sudah hidup: bebas. Menyalakan yang mati: **minta izin dulu** (D22).
  `infra/latex/` sudah dipakai pekerjaan lain — jangan menulis ke sana.
- Jangan hapus revision browser lama di `~/.cache/ms-playwright` (MCP `chrome-devtools`
  memakai `chromium-1228`).
- Git **sudah diizinkan** untuk project ini (D19): repo privat
  `git@rayin-personal:rayinailham/driftwatch.git`, akun **personal** `rayinailham`.
  Commit dan push **wajib** di akhir tiap fase yang selesai. Jangan pakai akun work
  (`rayin-kantor`) atau sesi MCP GitHub milik akun itu.
  Masih butuh izin baru: repo jadi publik, `force-push`, hapus branch/repo, tambah remote,
  ubah history.

## 2. Urutan lapis engine — turun secepatnya

```
Lapis 1  MCP browser (playwright / chrome-devtools)  → recon saja, mahal token
Lapis 2  script Playwright headless                  → hanya kalau render_mode = js_required
Lapis 3  httpx + selectolax                          → HTML statis
Lapis 4  httpx + json                                → ada endpoint JSON. Target akhir.
```

Kalau recon menemukan endpoint JSON, **browser dibuang**. Menahan browser padahal httpx cukup
adalah kegagalan desain di project ini, bukan pilihan gaya. Catat alasan pemilihan engine
di `recon.json` field `recommended_engine` + `notes`.

## 3. Sebelum menyentuh browser di sesi mana pun

```bash
bash ../crosscheck/scripts/arch_provision.sh
```
Script itu idempotent, tanpa sudo. Kalau DriftWatch akhirnya butuh Playwright sendiri,
salin script itu ke `scripts/` di P4 — jangan panggil lintas-project di kode produksi.

## 4. Sebelum menyentuh fixture lokal (`driftlab`)

```bash
bash scripts/lab_up.sh                 # http.server stdlib di 127.0.0.1:8100 (BUKAN container)
uv run --no-sync python scripts/drift_lab.py --verify    # wajib 11/11 skenario siap
```
Fixture **tidak** auto-start. Kalau verifikasi < 11/11, berhenti dan laporkan:
oracle alarm tidak sah kalau fixture-nya bergeser.

**Project ini tidak punya `docker-compose.yml`** (D8). Fixture dilayani `http.server`
stdlib dengan handler kustom, karena DO-06 (503) dan DO-08 (jeda) butuh server yang bisa
diprogram, dan karena deliverable harus bisa jalan di mesin klien tanpa Docker.

Port `8100` dipilih supaya tidak menabrak service user (`8000`, `3000`, `3100`, `3170`,
`20080`, `4000`, `2379`, `5540`, `943`, `9443`). Jangan pindah port tanpa mengubah D8.

## 5. Hierarki dokumen (kalau ada konflik)

1. `docs/DECISIONS.md` — keputusan terkunci. Menang atas semua.
2. `docs/SCHEMA.md` — bentuk semua file hasil.
3. `docs/ETHICS.md` — batas legal. Menang atas kenyamanan teknis, selalu.
4. `phases/phase-NN-*.md` — instruksi kerja sesi.
5. `docs/ACCEPTANCE.md`, `PLAN.md`, `README.md`.

Menemukan file bawah bertentangan dengan file atas → **perbaiki file bawah di sesi yang sama**,
jangan diamkan, jangan diam-diam ikut yang salah.

## 6. Infra device: pakai ulang, jangan pasang ulang (D21)

Garis pemisahnya: **boleh dipakai saat MEMBANGUN, wajib berdiri sendiri saat BERJALAN.**
Pipeline ini dikirim ke klien — apa pun yang dipakai runtime ikut jadi syarat pasang di
mesin mereka.

| Sudah ada di device — pakai | Jangan pasang/pakai ulang |
|---|---|
| cache `uv` (`~/.cache/uv`, 1,6 GB) | jangan `pip install` global |
| cache Playwright (`~/.cache/ms-playwright`, 2,0 GB) | jangan hapus revisi lama |
| service `plantuml` infra `:20080` (image sudah ada) | jangan pasang PlantUML sendiri |
| image `pandoc/core` (`docker run --rm`) untuk PDF | jangan pakai `texlive` 8,73 GB |
| MCP `playwright` / `chrome-devtools` (recon, P2) | jangan pasang browser tambahan |

**Dilarang jadi runtime dependency deliverable:** MySQL `:3306`, Redis `:6379`,
TiDB `:4000`, MCP `excel`. Checkpoint tetap SQLite, laporan tetap `openpyxl` —
keduanya harus jalan tanpa pengawasan pukul 09:00 dan di mesin klien.

## 7. Aturan data

- Data mentah tidak pernah ditimpa. Tiap run menulis ke `data/<target>/<YYYY-MM-DD>/`.
  Menimpa snapshot kemarin = menghapus baseline diff = merusak bukti utama project ini.
- `data/` dan `reports/` **gitignored**. Yang masuk repo hanya kode, dokumen, dan
  contoh laporan yang sudah disanitasi (`assets/`).
- Setiap field kosong wajib punya alasan di `missing_reason` (D6). "Kosong tanpa keterangan"
  dihitung cacat, bukan data.

## 8. Gerbang commit (D19) — tidak boleh dilewat

Sebuah fase **belum** ✅ sebelum tiga hal ini berhasil, berurutan:

```bash
make audit                    # atau scripts/secret_audit.py; wajib 0 kebocoran
git add -A && git status --short
git commit -m "PNN: <ringkas>"
git push
```

- Kalau `make audit` belum ada (sebelum P12), pakai pemeriksaan manual:
  `git status --short` tidak boleh memuat `.env`, `data/`, `reports/`, `auth/`, `*.db`.
- Kalau `push` gagal, fase tetap 🟨 di `STATE.md` dan alasannya dicatat. Jangan klaim selesai.
- Satu fase = satu commit. Jangan menggabung dua fase dalam satu commit; riwayat commit
  adalah bagian dari bukti portofolio ("11 commit, 11 fase, tiap commit punya metrik").

## 9. Alur sesi

`KICKSTART.md` adalah prompt universalnya; `STATE.md` adalah satu-satunya memori antar sesi.
Satu fase per sesi. DoD dicentang hanya dengan output perintah nyata, bukan klaim,
lalu ditutup dengan commit + push (§8).
