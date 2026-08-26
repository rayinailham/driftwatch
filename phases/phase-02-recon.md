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
- [x] 4 `recon/*.json` ada, lolos validasi bentuk `docs/SCHEMA.md` §1
- [x] Tiap file punya `sample` berisi **3 record nyata**, bukan placeholder
- [x] Tiap file punya `engine_rationale`, `ethics_gate.passed == true`, `expected_volume`
- [x] Selector tiap target diverifikasi di **3 halaman berbeda** (buktinya ditempel)
- [x] `recon/quotes.json` `recommended_engine` = `httpx+json`, dengan endpoint yang terbukti
      jalan lewat `curl` tanpa browser (A10)
- [x] Keputusan Playwright: dipasang / tidak, beserta alasannya, tercatat di `STATE.md`
- [x] **Commit + push berhasil** (D19)

### Bukti — validasi bentuk (`scripts/validate_recon.py`, exit 0)

```
$ uv run --no-sync python scripts/validate_recon.py
target    render_mode    engine                volume  field  req  key_field     sample
books     server_html    httpx+selectolax        1000     11   10  upc           3
quotes    json_api       httpx+json               100      6    5  quote_id      3
seo       server_html    httpx+selectolax          23      9    8  url           3
driftlab  server_html    httpx+selectolax         200      5    4  item_id       3

VALIDASI LOLOS: 4/4 recon sah terhadap docs/SCHEMA.md 1
```

### Bukti — selector diverifikasi di 3 halaman berbeda per target

```
--- books LIST: article.product_pod ---
books_p1.html      pods= 20 lengkap= 20 next=ada
books_p25.html     pods= 20 lengkap= 20 next=ada
books_p50.html     pods= 20 lengkap= 20 next=TIDAK
--- books DETAIL (13 field) ---
a-light-in-the-attic_1000.html       fields_terisi=13/13
soumission_998.html                  fields_terisi=13/13
tipping-the-velvet_999.html          fields_terisi=13/13

--- quotes API (engine terpilih) ---
page=1 HTTP 200 {"has_next":true,"n":10}
page=5 HTTP 200 {"has_next":true,"n":10}
page=10 HTTP 200 {"has_next":false,"n":10}
page=11 HTTP 200 {"has_next":false,"n":0}
inti_lengkap 10/10 di page 1, 5, 10  →  30/30
tags kosong 1 record (Marilyn Monroe, page=5)  →  tags OPSIONAL (D6)
--- quotes HTML fallback: div.quote ---
qh_p1.html   quotes= 10 lengkap= 10 next=ada
qh_p5.html   quotes= 10 lengkap=  9 next=ada     ← record bertag kosong yang sama
qh_p10.html  quotes= 10 lengkap= 10 next=TIDAK

--- seo: python-httpx.org ---
h_.html                terisi=7/8  h1='HTTPX'                wc=447  links=12 h2=4
h_api_.html            terisi=7/8  h1='Developer Interface'  wc=2537 links=13 h2=9
h_async_.html          terisi=7/8  h1='Async Support'        wc=811  links=11 h2=4
og_title = null di 3/3 halaman  →  opsional + missing_reason (D6)

--- driftlab LIST: article.item-card ---
dlp1.html    cards= 20 lengkap_4_field=20
dlp5.html    cards= 20 lengkap_4_field=20
dlp10.html   cards= 20 lengkap_4_field=20
--- driftlab DETAIL: article.item-detail ---
dli_DW-0001.html       terisi=5/5
dli_DW-0100.html       terisi=5/5
dli_DW-0200.html       terisi=5/5
```

### Bukti — A10, turun lapis di `quotes`

MCP `chrome-devtools` → `list_network_requests` pada `https://quotes.toscrape.com/scroll`:

```
Showing 1-8 of 8
reqid=1 GET https://quotes.toscrape.com/scroll                 [200]
reqid=2 GET https://quotes.toscrape.com/static/bootstrap.min.css [200]
reqid=3 GET https://quotes.toscrape.com/static/main.css        [200]
reqid=4 GET https://quotes.toscrape.com/static/jquery.js       [200]
reqid=5 GET https://fonts.googleapis.com/css?family=Raleway    [200]
reqid=6 GET https://fonts.gstatic.com/s/raleway/…woff2         [200]
reqid=7 GET https://quotes.toscrape.com/api/quotes?page=1      [200]   ← XHR JSON
reqid=8 GET https://quotes.toscrape.com/favicon.ico            [404]
```

Diuji ulang **tanpa browser**, browser lalu ditutup:

```
$ curl -sS -A 'DriftWatch/1.0 (+mailto:rayinailham9@gmail.com)' \
    'https://quotes.toscrape.com/api/quotes?page=1' -H 'Accept: application/json'
HTTP 200 bytes=2860
keys: has_next, page, quotes, tag, top_ten_tags
```

**8 request browser → 1 request httpx** untuk data yang sama. Panen penuh 100 kutipan:
10 request httpx, 0 proses browser, tanpa cookie / Authorization / CSRF / Referer.

### Bukti — gerbang etika selama recon

```
books    robots HTTP 404 · sitemap HTTP 404 · jeda ≥1,0 dtk antar request
quotes   robots HTTP 404 · sitemap HTTP 404 · jeda ≥1,0 dtk antar request
seo      robots HTTP 404 · sitemap HTTP 200 · 23 URL · jeda ≥1,0 dtk antar request
driftlab robots HTTP 200 "User-agent: *  Allow: /" · lokal, jeda bebas
UA seragam: DriftWatch/1.0 (+mailto:rayinailham9@gmail.com)
0 HTTP 429 · 0 login · 0 proteksi ditembus · 0 mutasi ke host publik
fixture: baseline items=200 reproducible_sha256=b09a1d16…e5d3 · 2/11 PASS (sesuai fase; 11/11 milik P8)
```

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
