# Verifikasi Manual Dataset Books

**Tanggal pengecekan:** 2026-08-27  
**Snapshot:** `data/books/2026-08-27/records.jsonl`  
**Metode:** record posisi 1, 500, dan 1.000 dibandingkan dengan halaman detail sumber. Request memakai User-Agent D3 dan berjeda 1 detik. Semua halaman merespons HTTP 200.

## Record 1 dari 1.000

Sumber: <https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html>

| Field required | Dataset | Halaman | Hasil |
|---|---:|---:|---|
| `upc` | `a897fe39b1053632` | `a897fe39b1053632` | cocok |
| `title` | `A Light in the Attic` | `A Light in the Attic` | cocok |
| `price_incl_tax_gbp` | `51.77` | `51.77` | cocok |
| `price_excl_tax_gbp` | `51.77` | `51.77` | cocok |
| `tax_gbp` | `0.0` | `0.0` | cocok |
| `availability_count` | `22` | `22` | cocok |
| `in_stock` | `true` | `true` | cocok |
| `rating` | `Three` | `Three` | cocok |
| `category` | `Poetry` | `Poetry` | cocok |
| `num_reviews` | `0` | `0` | cocok |

## Record 500 dari 1.000

Sumber: <https://books.toscrape.com/catalogue/the-whale_501/index.html>

| Field required | Dataset | Halaman | Hasil |
|---|---:|---:|---|
| `upc` | `0ff9d10864db8364` | `0ff9d10864db8364` | cocok |
| `title` | `The Whale` | `The Whale` | cocok |
| `price_incl_tax_gbp` | `35.96` | `35.96` | cocok |
| `price_excl_tax_gbp` | `35.96` | `35.96` | cocok |
| `tax_gbp` | `0.0` | `0.0` | cocok |
| `availability_count` | `7` | `7` | cocok |
| `in_stock` | `true` | `true` | cocok |
| `rating` | `Four` | `Four` | cocok |
| `category` | `Childrens` | `Childrens` | cocok |
| `num_reviews` | `0` | `0` | cocok |

## Record 1.000 dari 1.000

Sumber: <https://books.toscrape.com/catalogue/1000-places-to-see-before-you-die_1/index.html>

| Field required | Dataset | Halaman | Hasil |
|---|---:|---:|---|
| `upc` | `228ba5e7577e1d49` | `228ba5e7577e1d49` | cocok |
| `title` | `1,000 Places to See Before You Die` | `1,000 Places to See Before You Die` | cocok |
| `price_incl_tax_gbp` | `26.08` | `26.08` | cocok |
| `price_excl_tax_gbp` | `26.08` | `26.08` | cocok |
| `tax_gbp` | `0.0` | `0.0` | cocok |
| `availability_count` | `1` | `1` | cocok |
| `in_stock` | `true` | `true` | cocok |
| `rating` | `Five` | `Five` | cocok |
| `category` | `Travel` | `Travel` | cocok |
| `num_reviews` | `0` | `0` | cocok |

## Bukti perintah

Pemeriksa mengambil tiga baris JSONL tersebut, meminta URL sumber dengan `httpx`, mem-parsing HTML melalui parser produksi `parse_detail`, lalu membandingkan seluruh field yang ditandai `required` oleh `CONTRACTS["books"]`.

```text
position=1    status=200  required_match=10/10  all_match=true
position=500  status=200  required_match=10/10  all_match=true
position=1000 status=200  required_match=10/10  all_match=true
```

**Kesimpulan:** 3/3 record dan 30/30 nilai field required cocok dengan halaman sumber.
