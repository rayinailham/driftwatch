# P2 — Recon

**Tujuan sesi:** empat `recon/<target>.json` lengkap, tiap target punya keputusan engine
yang berdasar bukti. Belum ada scraper produksi.

**Prasyarat:** P1 selesai.
**Read-set:** `STATE.md`, file ini, `../skills/web-recon/SKILL.md`, `docs/SCHEMA.md` §1,
`docs/TARGETS.md`, `docs/DECISIONS.md` (D1, D3).
**Budget:** **berat** — ini satu-satunya fase yang boleh memakai MCP browser.

---

## Aturan hemat token untuk fase ini

MCP browser mahal. Urutannya wajib: **`curl` dulu, browser belakangan, dan hanya kalau
`curl` gagal menjawab.** Untuk `books` dan `driftlab`, `curl` hampir pasti cukup —
jangan buka browser untuk keduanya kecuali ada yang benar-benar tidak terjawab.

---

## Langkah per target

### 1. Pengecekan murah (semua target, selalu duluan)
```bash
BASE="https://books.toscrape.com"
curl -sS "$BASE/robots.txt"
curl -sS "$BASE/sitemap.xml" | head -30
curl -sSI "$BASE"
curl -sS "$BASE/catalogue/page-1.html" -o /tmp/r.html && wc -c /tmp/r.html
grep -o '__NEXT_DATA__\|__NUXT__\|application/ld+json\|window.__INITIAL' /tmp/r.html | sort -u
```
Peta hasil → `render_mode`:
`__NEXT_DATA__`/`__NUXT__`/`__INITIAL` → `embedded_json` · `ld+json` → `embedded_json` ·
data terlihat di HTML → `server_html` · hanya `<div id="root">` → `js_required`.

### 2. `quotes.toscrape.com` — target yang sengaja dipilih untuk membuktikan turun lapis
Situs ini punya varian yang datanya dimuat lewat JS. Alurnya:

1. `curl` halaman biasa → `server_html`
2. buka varian JS pakai MCP `playwright`, lalu MCP `chrome-devtools` →
   `list_network_requests` → cari XHR yang membalas JSON
3. begitu endpoint ketemu, **uji di luar browser**:
```bash
curl -sS "https://quotes.toscrape.com/api/quotes?page=1" -H 'Accept: application/json' | jq '.'
```
4. berhasil → tutup browser, `recommended_engine: "httpx+json"`,
   `engine_rationale` menyebut endpoint yang ditemukan dan berapa request yang dihemat

Momen ini adalah **acceptance A10** dan bahan video P12. Catat jumlah request browser
vs jumlah request httpx untuk data yang sama — angka itu yang dipakai di pitch.

### 3. Petakan selector (untuk target `server_html`)
Prioritas dari paling tahan banting: `data-*` > id semantik > class semantik > struktur DOM.
**Hindari** class hash (`.css-1x2y3z`) dan `nth-child` dalam.
**Verifikasi tiap selector di 3 halaman berbeda** sebelum dicatat.

### 4. Petakan pagination
Tentukan satu: `page` param (catat max page & cara tahu halaman terakhir) · cursor/token ·
infinite scroll · tombol "load more". Catat kondisi berhentinya secara eksplisit —
scraper tanpa kondisi berhenti yang jelas akan berputar selamanya atau berhenti terlalu cepat.

### 5. Ambil 3 record sampel lengkap per target
Isi `sample` di `recon.json`. **Jangan lanjut ke P3 kalau `sample` kosong** — schema yang
disusun tanpa sampel nyata selalu meleset.

### 6. Tiga field wajib tambahan (`docs/SCHEMA.md` §1)
- `engine_rationale` — kenapa engine itu dipilih, dan kenapa browser tidak dipakai
- `ethics_gate` — `passed: true` beserta tanggal & catatan
- `expected_volume` — jadi baseline awal alarm `RECORD_COUNT_DROP`

---

## Output fase
- `recon/books.json`, `recon/quotes.json`, `recon/seo.json`, `recon/driftlab.json`
- catatan di `STATE.md`: apakah ada target `js_required` (menentukan Playwright dipasang atau tidak)

## Definition of Done
- [ ] 4 `recon/*.json` ada, lolos validasi bentuk `docs/SCHEMA.md` §1
- [ ] Tiap file punya `sample` berisi **3 record nyata**, bukan placeholder
- [ ] Tiap file punya `engine_rationale`, `ethics_gate.passed == true`, `expected_volume`
- [ ] Selector tiap target diverifikasi di **3 halaman berbeda** (buktinya ditempel)
- [ ] `recon/quotes.json` `recommended_engine` = `httpx+json`, dengan endpoint yang terbukti
      jalan lewat `curl` tanpa browser (A10)
- [ ] Keputusan Playwright: dipasang / tidak, beserta alasannya, tercatat di `STATE.md`
- [ ] **Commit + push berhasil** (D19)

## Metrik selesai
`4 recon selesai · N target butuh browser · endpoint JSON ditemukan di quotes (X request → Y request)`

## Jebakan
- **Jangan pakai MCP browser untuk `books` atau `driftlab`.** `curl` cukup; memakai browser
  di sana membakar context tanpa hasil tambahan.
- Jangan catat selector yang hanya diuji di satu halaman. Itu penyebab nomor satu scraper
  yang patah minggu depan.
- Jangan lampaui 1 request/detik selama recon. Recon bukan alasan membanjiri server (D3).
- Kalau `robots.txt` target `seo` ternyata melarang path yang dibutuhkan: **berhenti,
  laporkan, ganti target.** Jangan cari celah.

## Sebelum menutup sesi
1. Centang DoD dengan output nyata.
2. Update `STATE.md`: P2 ✅, `render_mode` + engine per target, keputusan Playwright.
3. `git add -A && git commit -m "P02: recon 4 target + keputusan engine" && git push`
