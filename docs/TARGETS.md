# DriftWatch — Target & Gerbang Etika

Audit dilakukan 2026-08-27 dengan User-Agent tetap
`DriftWatch/1.0 (+mailto:rayinailham9@gmail.com)`. Untuk host publik, `robots.txt`
diambil sebelum halaman lain dan jeda minimum 1 detik per host dipertahankan. HTTP 404
berarti berkas tidak tersedia, bukan izin untuk mempercepat; default D3 tetap berlaku.

## Target yang ditetapkan

| Kode | URL | Peran | Render mode dugaan | Robots | Delay | Disallow | Sitemap | Volume |
|---|---|---|---|---|---:|---|---|---:|
| `books` | `https://books.toscrape.com/` | dataset volume | HTML statis | HTTP 404 | 1,0 dtk (D3) | tidak ada berkas | tidak ditemukan | 1.000 |
| `quotes` | `https://quotes.toscrape.com/` | bukti turun lapis | HTML statis; endpoint JSON dicari P2 | HTTP 404 | 1,0 dtk (D3) | tidak ada berkas | tidak ditemukan | ~100 |
| `seo` | `https://www.python-httpx.org/` | metadata SEO nyata | HTML statis | HTTP 404 | 1,0 dtk (D3) | tidak ada berkas | `/sitemap.xml`, HTTP 200 | 23 |
| `driftlab` | `http://127.0.0.1:8100/` | oracle drift lokal | HTML statis | HTTP 200, `Allow: /` | lokal, bebas | tidak ada | tidak perlu | 200 |

Render mode di atas masih dugaan; P2 mengonfirmasi engine paling rendah yang cukup.
Mutasi hanya berlaku pada `driftlab`, tidak pernah pada tiga host publik.

## Gerbang `seo`: HTTPX — dipilih

| Kotak ETHICS §2 | Hasil | Bukti |
|---|---|---|
| Path tidak dilarang robots | ✅ | `GET /robots.txt` → HTTP 404; tidak ada aturan `Disallow` |
| Crawl-delay sanggup dipenuhi | ✅ | tidak ada berkas robots; default D3 1,0 dtk dipakai |
| Sitemap tersedia | ✅ | `GET /sitemap.xml` → HTTP 200, XML valid |
| Bukan kompetitor yang dirugikan | ✅ | dokumentasi proyek OSS `encode/httpx`, tautan repo GitHub ada di halaman utama |
| Tanpa login/captcha/Cloudflare | ✅ | halaman utama HTTP 200; 0 penanda `captcha`, `cf-chl-`, atau `login wall` |
| Metadata saja | ✅ | kontrak: URL, title, H1, meta description, tanggal, jumlah kata/link; isi halaman tidak disimpan |
| Volume ≤500 | ✅ | sitemap XML berisi tepat 23 URL |

Dipilih karena seluruh situs hanya 23 URL: bukti monitoring SEO nyata dengan beban paling
kecil di antara kandidat lolos. Crawl dibatasi URL sitemap dan tetap 1 request/detik.

## Kandidat lain

### FastAPI docs — lolos gerbang, tidak dipilih

| Kotak ETHICS §2 | Hasil | Bukti |
|---|---|---|
| Path tidak dilarang robots | ✅ | `/robots.txt` HTTP 200, tanpa `Disallow` |
| Crawl-delay sanggup dipenuhi | ✅ | tidak ada `Crawl-delay`; default D3 1,0 dtk |
| Sitemap tersedia | ✅ | `/sitemap.xml` HTTP 200, XML valid |
| Bukan kompetitor yang dirugikan | ✅ | dokumentasi OSS; halaman utama menautkan `github.com/fastapi/fastapi` |
| Tanpa login/captcha/Cloudflare | ✅ | halaman utama HTTP 200; 0 penanda challenge |
| Metadata saja | ✅ | batas field teknis yang sama dengan target terpilih |
| Volume ≤500 | ✅ | sitemap berisi 151 URL |

Tidak dipilih: 151 request tidak memberi bukti tambahan dibanding HTTPX 23 URL; minimisasi
beban host publik menang.

### Pydantic docs — ditolak

| Kotak ETHICS §2 | Hasil | Bukti |
|---|---|---|
| Path tidak dilarang robots | ✅ | `/robots.txt` HTTP 200, `User-agent: *` + `Allow: /` |
| Crawl-delay sanggup dipenuhi | ✅ | tidak ada `Crawl-delay`; default D3 1,0 dtk |
| Sitemap tersedia | ✅ | robots menautkan `/docs/sitemap.xml`; endpoint HTTP 200 |
| Bukan kompetitor yang dirugikan | ✅ | dokumentasi proyek OSS Pydantic |
| Tanpa login/captcha/Cloudflare | ✅ | halaman docs HTTP 200; 0 penanda challenge |
| Metadata saja | ✅ | evaluasi dibatasi metadata teknis |
| Volume ≤500 | ❌ | sitemap docs berisi 1.796 URL |

Ditolak segera karena satu kotak gagal. Tidak dilakukan crawl halaman sitemap.

### Python docs — dikeluarkan dari kandidat formal

URL awal robots keliru (`/3/robots.txt`, HTTP 404), lalu sitemap sempat diminta sebelum
robots origin-root. Audit urutannya tidak sah menurut ETHICS §1, jadi kandidat dikeluarkan
dan tidak ada halaman konten yang diambil. Pemeriksaan korektif `/robots.txt` menemukan
larangan `/dev`, `/release`, dan versi EOL; tidak ada path itu yang diminta.

## Bukti audit ringkas

```text
books robots:       HTTP 404
quotes robots:      HTTP 404
HTTPX robots:       HTTP 404
HTTPX sitemap:      HTTP 200 · URL count: 23
FastAPI robots:     HTTP 200 · Disallow: none
FastAPI sitemap:    HTTP 200 · URL count: 151
Pydantic robots:    HTTP 200 · Allow: /
Pydantic sitemap:   HTTP 200 · URL count: 1796
driftlab robots:    HTTP 200 · Allow: /
```
