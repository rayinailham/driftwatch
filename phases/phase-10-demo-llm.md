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

**Terkunci 2026-08-28 sebagai D18: berkas statis lokal**, jalur ketiga di luar dua kolom di
atas. User memilihnya setelah ditawari ketiganya. GitHub Pages ditolak karena menuntut repo
publik (🔓 D20, izin terpisah, belum diberikan); Artifact ditolak karena menuntut redeploy
manual tiap data berubah. Konsekuensi yang diterima sadar: **tidak ada URL publik**, jadi
bukti A9 adalah halaman yang dirender lokal, bukan tautan yang bisa dibuka orang lain.

### 5. Sambungkan ke pipeline harian
Tambahkan `src/publish.py` sebagai langkah (6) di `scripts/daily_run.sh`, dengan `|| true`
supaya kegagalan publikasi tidak pernah menggagalkan panen data.

---

## Output fase
- `src/publish.py`
- `web/index.html`, `web/data.json`
- D18 terkunci
- halaman demo yang bisa dibuka lewat `file://`, tanpa server (D18)

## Definition of Done
- [x] `web/data.json` lahir dari data nyata; `generated_at` ≤ 24 jam
- [x] Hanya metadata untuk target `seo` (D13) — dibuktikan dengan memeriksa isi file
- [x] Tidak ada kunci API / path lokal / nama host internal di `web/data.json` maupun HTML
- [x] Halaman terbuka dan menampilkan data asli (A9); lokasinya ditulis di `STATE.md`
      (D18: berkas statis lokal, jadi lokasi berkas menggantikan URL publik)
- [x] Blok atribusi + catatan etika terlihat di halaman
- [x] `--no-llm` menjalankan seluruh alur tanpa satu pun panggilan API
- [x] Model & pagar biaya dipilih **berdasarkan skill `claude-api`**, bukan ingatan;
      model id yang dipakai ditulis di `STATE.md`
- [x] `input_tokens`/`output_tokens` tercatat di `web/data.json`
- [x] D18 terkunci di `docs/DECISIONS.md`
- [x] **Commit + push berhasil** (D19)

## Metrik selesai
`halaman hidup di <URL> · N baris ditampilkan · insight X token · biaya per hari ≈ Y`

**Aktual 2026-08-28:** `web/index.html` (berkas statis lokal, D18) · **323 baris** ditampilkan
(books 200 + quotes 100 + seo 23) · insight **0 token** (kunci API kosong → mode tanpa LLM) ·
biaya per hari **$0,00000**; dengan kunci terisi diperkirakan **≈ $0,005/hari**
(3 target × ~600 token masuk + ~200 token keluar, `claude-haiku-4-5` $1/$5 per 1 juta token).

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

---

## Bukti DoD — dijalankan 2026-08-28

### 1. Payload lahir dari data nyata (`generated_at` ≤ 24 jam)

```
$ uv run --no-sync python src/publish.py --no-llm
books: 200 baris · insight 0+0 token
quotes: 100 baris · insight 0+0 token
seo: 23 baris · insight 0+0 token
web/index.html + web/data.json ditulis · 0+0 token · ~$0.00000/hari

web/data-books.json  | target books  | generated_at 2026-08-28T08:13:27+07:00 | snapshot 2026-08-27 | rows 200 | counts {'total': 1000, 'added_today': 1000, 'changed_today': 0, 'removed_today': 0}
web/data-quotes.json | target quotes | generated_at 2026-08-28T08:13:27+07:00 | snapshot 2026-08-27 | rows 100 | counts {'total': 100, 'added_today': 100, 'changed_today': 0, 'removed_today': 0}
web/data-seo.json    | target seo    | generated_at 2026-08-28T08:13:27+07:00 | snapshot 2026-08-27 | rows 23  | counts {'total': 23, 'added_today': 23, 'changed_today': 0, 'removed_today': 0}
web/data.json        | target books  | generated_at 2026-08-28T08:13:27+07:00 | snapshot 2026-08-27 | rows 200 | counts {'total': 1000, 'added_today': 1000, 'changed_today': 0, 'removed_today': 0}
```

### 2. Target `seo` hanya metadata (D13)

```
kunci baris : ['fields', 'record_id', 'status', 'url']
field seo   : ['canonical', 'h1', 'h2_count', 'link_count', 'meta_description', 'og_title', 'title', 'url', 'word_count']
contoh baris: {"record_id": "seo:url:https://www.python-httpx.org/", "url": "https://www.python-httpx.org/",
               "status": "baru", "fields": {"url": "…", "title": "HTTPX", "h1": "HTTPX",
               "meta_description": "A next-generation HTTP client for Python.", "canonical": "…"}}
```

Sembilan field itu persis kontrak `seo` di `src/contracts.py`. Nol isi artikel.

### 3. Nol kunci API / path lokal / host internal

```
$ grep -rniE "sk-ant|ANTHROPIC|/home/rayin|127\.0\.0\.1|localhost|:8100|:8101|:20128|driftlab|\.venv|/tmp/|/Projects/" \
    web/data*.json web/index.html web/template.html
0 kecocokan -> BERSIH
```

### 4. Halaman terbuka dan menampilkan data asli (A9)

Dirender `file://` dengan `chrome-headless-shell` dari cache Playwright yang sudah ada (D21,
nol pemasangan); DOM hasil render:

```
tr terender: 200
kolom: ['status', 'upc', 'title', 'price incl tax gbp', 'price excl tax gbp', 'tax gbp',
        'availability count', 'in stock', 'rating', 'category', 'num reviews',
        'description words', 'tautan']
[kartu]  [('1000','total record'), ('1000','baru hari ini'), ('0','berubah'), ('0','hilang')]
[tab]    ['books.toscrape.com', 'quotes.toscrape.com', 'python-httpx.org']
[hitung] 200 dari 200 baris ditampilkan (maksimal 200 per situs)
[stempel] Dibuat 2026-08-28T08:12:45+07:00 (WIB), dari panen 2026-08-27
```

### 5. Atribusi + catatan etika terlihat (ETHICS §3)

```
Sumber data books.toscrape.com — Sandbox latihan scraping milik Scraping Hub. Metadata katalog saja.
Dikumpulkan dengan menghormati robots.txt, 1 permintaan per detik per situs, maksimal 3 permintaan
bersamaan, dan User-Agent jujur yang memuat alamat kontak. Halaman ini hanya menampilkan metadata
beserta tautan ke sumber aslinya, bukan isi karya. Pemilik situs yang keberatan dapat meminta
penghapusan lewat alamat kontak pada User-Agent.

ai-tag ada: True     ← blok insight berlabel "Ringkasan dibuat AI"
```

### 6. `--no-llm` = nol panggilan API

Diuji dengan kunci palsu terpasang dan `base_url` diarahkan ke alamat mati; kalau ada satu
saja panggilan, ia akan gagal:

```
$ ANTHROPIC_API_KEY="kunci-palsu-untuk-uji" ANTHROPIC_BASE_URL="http://127.0.0.1:1" \
    uv run --no-sync python … src/publish.py --no-llm
books: 200 baris · insight 0+0 token
quotes: 100 baris · insight 0+0 token
seo: 23 baris · insight 0+0 token
exit_code: 0
modul 'anthropic' termuat? False
```

SDK-nya bahkan tidak pernah diimpor — `import anthropic` berada di dalam `generate_insight()`.

### 7. Kunci kosong tidak membuat crash

```
$ uv run --no-sync python src/publish.py        # ANTHROPIC_API_KEY kosong (0 karakter)
peringatan: ANTHROPIC_API_KEY kosong, books jatuh ke mode tanpa LLM
peringatan: ANTHROPIC_API_KEY kosong, quotes jatuh ke mode tanpa LLM
peringatan: ANTHROPIC_API_KEY kosong, seo jatuh ke mode tanpa LLM
web/index.html + web/data.json ditulis · 0+0 token · ~$0.00000/hari
```

### 8. Model & pagar biaya dari skill `claude-api`

`claude-haiku-4-5` — $1,00 masuk / $5,00 keluar per 1 juta token, tarif terendah pada tabel
model skill (cache 2026-06-24) dan cukup untuk meringkas ~20 baris agregat menjadi 4 kalimat.
Pagar lengkap dikunci sebagai **D14**. `input_tokens`/`output_tokens` tercatat per target.

### 9. Tersambung ke pipeline harian

```
$ tail -7 scripts/daily_run.sh
# (6) publikasi halaman demo. Dijalankan sekali setelah loop, bukan per target,
# karena satu halaman memuat semua target publik dan pagar biaya D14 membatasi
# satu panggilan LLM per target per hari. Kegagalan di sini tidak pernah
# menggagalkan panen data.
uv run --no-sync python src/publish.py || true

exit "$FAIL"
$ bash -n scripts/daily_run.sh && echo OK
OK
```

### Catatan penyimpangan yang disengaja

- **Dijalankan sekali setelah loop, bukan di dalamnya.** Fase menulis "langkah (6)"; loop
  `daily_run.sh` berjalan per target, sedangkan satu halaman memuat tiga target sekaligus.
  Memanggilnya di dalam loop akan menulis ulang `index.html` tiga kali dan menyisakan hanya
  target terakhir. Urutannya tetap keenam, posisinya sesudah loop.
- **`web/data.json` tetap satu target** persis seperti `docs/SCHEMA.md` §8. Target lain lahir
  sebagai `web/data-<target>.json` dengan bentuk yang sama, dan `web/data.json` adalah salinan
  target unggulan (`books`). Skema tidak dilanggar, halaman tetap memuat tiga situs.
- **`web/template.html`** adalah kerangka halaman; `publish.py` menanamkan payload JSON ke
  dalamnya dan menulis hasilnya ke `web/index.html`. Yang dibaca manusia tetap satu berkas.
