# P10 — Halaman Demo + Insight LLM

**Tujuan sesi:** halaman yang bisa dibuka orang lain, memuat data asli hasil scraping,
plus satu ringkasan dari LLM. Ini sekaligus bukti untuk job 25.

**Prasyarat:** P6 selesai (ada data nyata). Tidak butuh P8.
**Read-set:** `STATE.md`, file ini, `docs/DECISIONS.md` (D13, D14), `docs/SCHEMA.md` §8,
`docs/ETHICS.md` §3, **skill `claude-api`** (wajib, untuk model id & harga yang berlaku).
**Budget:** sedang.

---

## Langkah

### 1. `src/publish.py` → `web/data.json`
Membaca snapshot terbaru + `diff.json` terbaru → menulis `web/data.json`
(bentuk di `docs/SCHEMA.md` §8).

Batas yang mengikat (D13, `docs/ETHICS.md` §3):
- maksimal **200 baris**
- untuk target `seo`: **metadata saja** — judul, H1, meta description, tanggal,
  jumlah kata, jumlah link, URL. Bukan isi artikel.
- ada blok `source` berisi nama situs + tautan + atribusi
- **tidak ada** kunci API, path lokal, atau nama host internal di file ini

### 2. Ringkasan LLM (D14) — baca skill `claude-api` dulu
**Jangan menulis model id atau angka harga dari ingatan.** Baca skill `claude-api`
untuk model yang berlaku dan biayanya, lalu pilih yang paling murah yang cukup untuk
tugas ini (meringkas ~20 baris agregat — ini tugas ringan, bukan tugas penalaran berat).

Pagar biaya yang sudah dikunci:
- maksimum **1 panggilan per target per hari**
- input = **ringkasan agregat** (`counts`, 10 baris teratas, delta harga/kelengkapan),
  **bukan** seluruh dataset
- flag `--no-llm` membuat seluruh pipeline jalan tanpa biaya sama sekali
- `ANTHROPIC_API_KEY` dari `.env`; kalau kosong, jatuh otomatis ke `--no-llm` dengan
  peringatan, bukan crash
- catat `input_tokens` + `output_tokens` di `web/data.json` — biaya yang tidak diukur
  adalah biaya yang membengkak

Prompt ringkasan diarahkan ke pertanyaan yang berguna untuk klien, bukan basa-basi:
*"apa yang berubah hari ini, dan mana yang layak dilihat manusia?"*

### 3. `web/index.html`
Satu file statis, tanpa dependency eksternal. Isi:
- header: nama sumber + tautan + baris atribusi + catatan etika ("dikumpulkan dengan
  menghormati robots.txt, 1 request/detik")
- kartu ringkasan: total, baru hari ini, berubah, hilang
- blok insight LLM (dengan label jelas bahwa itu dibuat AI)
- tabel data, bisa dicari & diurutkan (JS polos, tanpa library)
- footer: `generated_at`, tautan ke repo

Harus terbaca di layar sempit dan hormat pada tema terang/gelap pembacanya.

### 4. Publikasi (🔓 D18 — kunci di fase ini)
Dua jalur:

| Jalur | Kelebihan | Kekurangan |
|---|---|---|
| **Artifact claude.ai** | URL publik langsung, tanpa hosting | perlu di-redeploy tiap data berubah |
| **File statis + GitHub Pages** | otomatis ikut push harian | butuh repo publik (🔓 D20, izin terpisah) |

Pilih satu, kunci sebagai D18 di `docs/DECISIONS.md`, catat alasannya.
Kalau memilih GitHub Pages, **berhenti dan minta izin user** — itu menjadikan repo publik.

### 5. Sambungkan ke pipeline harian
Tambahkan `src/publish.py` sebagai langkah (6) di `scripts/daily_run.sh`, dengan `|| true`
supaya kegagalan publikasi tidak pernah menggagalkan panen data.

---

## Output fase
- `src/publish.py`
- `web/index.html`, `web/data.json`
- D18 terkunci
- URL halaman demo yang hidup

## Definition of Done
- [ ] `web/data.json` lahir dari data nyata; `generated_at` ≤ 24 jam
- [ ] Hanya metadata untuk target `seo` (D13) — dibuktikan dengan memeriksa isi file
- [ ] Tidak ada kunci API / path lokal / nama host internal di `web/data.json` maupun HTML
- [ ] Halaman terbuka dan menampilkan data asli (A9); URL-nya ditulis di `STATE.md`
- [ ] Blok atribusi + catatan etika terlihat di halaman
- [ ] `--no-llm` menjalankan seluruh alur tanpa satu pun panggilan API
- [ ] Model & pagar biaya dipilih **berdasarkan skill `claude-api`**, bukan ingatan;
      model id yang dipakai ditulis di `STATE.md`
- [ ] `input_tokens`/`output_tokens` tercatat di `web/data.json`
- [ ] D18 terkunci di `docs/DECISIONS.md`
- [ ] **Commit + push berhasil** (D19)

## Metrik selesai
`halaman hidup di <URL> · N baris ditampilkan · insight X token · biaya per hari ≈ Y`

## Jebakan
- **Jangan kirim seluruh dataset ke LLM.** 1.000 record per hari adalah cara tercepat
  membakar biaya untuk nilai tambah nol.
- Jangan menampilkan konten penuh milik situs sumber (D13). Portofolio yang melanggar
  hak cipta bukan portofolio, itu liability.
- Jangan biarkan pipeline crash kalau `ANTHROPIC_API_KEY` kosong. Jatuh ke `--no-llm`.
- Jangan menjadikan repo publik untuk GitHub Pages tanpa izin user (🔓 D20).
- Jangan menaruh kunci API di HTML. Pemanggilan LLM terjadi di `publish.py` (server-side),
  hasilnya saja yang masuk ke `data.json`.

## Sebelum menutup sesi
1. Centang DoD dengan output nyata.
2. Update `STATE.md`: P10 ✅, URL, model, biaya per hari.
3. `git add -A && git commit -m "P10: halaman demo + insight LLM ber-pagar" && git push`
