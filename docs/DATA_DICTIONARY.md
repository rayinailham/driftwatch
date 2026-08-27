# DriftWatch — Kamus Data

Digenerate oleh `src/export.py` dari `src/contracts.py`; contoh berasal dari snapshot nyata `2026-08-27`.

## `books`

| Kolom | Tipe | Status | Contoh nyata | Penjelasan | Sumber |
|---|---|---|---|---|---|
| `upc` | `str` | wajib | a897fe39b1053632 | Kode produk universal buku | baris UPC pada tabel informasi produk |
| `title` | `str` | wajib | A Light in the Attic | Judul buku | heading utama halaman detail |
| `price_incl_tax_gbp` | `float` | wajib | 51.77 | Harga termasuk pajak dalam GBP | baris Price (incl. tax) pada tabel informasi produk |
| `price_excl_tax_gbp` | `float` | wajib | 51.77 | Harga sebelum pajak dalam GBP | baris Price (excl. tax) pada tabel informasi produk |
| `tax_gbp` | `float` | wajib | 0.0 | Nilai pajak dalam GBP | baris Tax pada tabel informasi produk |
| `availability_count` | `int` | wajib | 22 | Jumlah stok yang tersedia | baris Availability pada tabel informasi produk |
| `in_stock` | `bool` | wajib | True | Status ketersediaan buku | status stok halaman detail |
| `rating` | `str` | wajib | Three | Peringkat buku dalam kata bahasa Inggris | kelas rating halaman detail |
| `category` | `str` | wajib | Poetry | Kategori katalog buku | breadcrumb kategori halaman detail |
| `num_reviews` | `int` | wajib | 0 | Jumlah ulasan buku | baris Number of reviews pada tabel informasi produk |
| `description_words` | `int` | opsional | 164 | Jumlah kata deskripsi tanpa menyimpan isi | teks deskripsi halaman detail, dihitung lalu dibuang |

## `quotes`

| Kolom | Tipe | Status | Contoh nyata | Penjelasan | Sumber |
|---|---|---|---|---|---|
| `quote_id` | `str` | wajib | d3a0b108aa2c0249 | 16 karakter awal SHA-256 teks kutipan | sha256(text)[:16] dari respons API |
| `author_name` | `str` | wajib | Albert Einstein | Nama penulis kutipan | author.name |
| `author_slug` | `str` | wajib | Albert-Einstein | Slug stabil penulis | author.slug |
| `author_goodreads_link` | `str` | wajib | /author/show/9810.Albert_Einstein | Tautan profil Goodreads penulis | author.goodreads_link |
| `quote_word_count` | `int` | wajib | 21 | Jumlah kata kutipan tanpa menyimpan isi | jumlah token whitespace pada text |
| `tags` | `list` | opsional | change; deep-thoughts; thinking; world | Tag topik kutipan | tags[].name |

## `seo`

| Kolom | Tipe | Status | Contoh nyata | Penjelasan | Sumber |
|---|---|---|---|---|---|
| `url` | `str` | wajib | https://www.python-httpx.org/ | URL halaman yang dipantau | URL dari sitemap.xml |
| `title` | `str` | wajib | HTTPX | Judul dokumen HTML | elemen title dokumen |
| `h1` | `str` | wajib | HTTPX | Judul utama halaman | heading h1 konten utama |
| `meta_description` | `str` | wajib | A next-generation HTTP client for Python. | Deskripsi halaman untuk mesin pencari | meta description dokumen |
| `canonical` | `str` | wajib | https://www.python-httpx.org/ | URL kanonis halaman | tautan canonical dokumen |
| `h2_count` | `int` | wajib | 4 | Jumlah heading tingkat dua | jumlah heading h2 konten utama |
| `word_count` | `int` | wajib | 416 | Jumlah kata konten utama | teks konten utama, dihitung lalu dibuang |
| `link_count` | `int` | wajib | 12 | Jumlah tautan pada konten utama | jumlah tautan konten utama |
| `og_title` | `str` | opsional |  | Judul Open Graph | meta og:title dokumen |

## `driftlab`

| Kolom | Tipe | Status | Contoh nyata | Penjelasan | Sumber |
|---|---|---|---|---|---|
| `item_id` | `str` | wajib | DW-0001 | Identitas stabil item fixture | article[data-item-id] |
| `name` | `str` | wajib | Fine Lamp 001 | Nama item fixture | h1.item-name |
| `price` | `float` | wajib | 114.04 | Harga item fixture | nilai harga halaman detail |
| `category` | `str` | wajib | office | Kategori item fixture | .item-category |
| `note` | `str` | opsional | Fixture note 6895 | Catatan detail item fixture | .item-note |
