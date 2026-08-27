"""Locked data contracts for every DriftWatch target."""

from typing import NamedTuple


class Field(NamedTuple):
    name: str
    type: type | tuple[type, ...]
    required: bool
    description: str
    source_hint: str


CONTRACTS = {
    "books": {
        "key": "upc",
        "fields": [
            Field("upc", str, True, "Kode produk universal buku", "baris UPC pada tabel informasi produk"),
            Field("title", str, True, "Judul buku", "heading utama halaman detail"),
            Field("price_incl_tax_gbp", float, True, "Harga termasuk pajak dalam GBP", "baris Price (incl. tax) pada tabel informasi produk"),
            Field("price_excl_tax_gbp", float, True, "Harga sebelum pajak dalam GBP", "baris Price (excl. tax) pada tabel informasi produk"),
            Field("tax_gbp", float, True, "Nilai pajak dalam GBP", "baris Tax pada tabel informasi produk"),
            Field("availability_count", int, True, "Jumlah stok yang tersedia", "baris Availability pada tabel informasi produk"),
            Field("in_stock", bool, True, "Status ketersediaan buku", "status stok halaman detail"),
            Field("rating", str, True, "Peringkat buku dalam kata bahasa Inggris", "kelas rating halaman detail"),
            Field("category", str, True, "Kategori katalog buku", "breadcrumb kategori halaman detail"),
            Field("num_reviews", int, True, "Jumlah ulasan buku", "baris Number of reviews pada tabel informasi produk"),
            Field("description_words", int, False, "Jumlah kata deskripsi tanpa menyimpan isi", "teks deskripsi halaman detail, dihitung lalu dibuang"),
        ],
    },
    "quotes": {
        "key": "quote_id",
        "fields": [
            Field("quote_id", str, True, "16 karakter awal SHA-256 teks kutipan", "sha256(text)[:16] dari respons API"),
            Field("author_name", str, True, "Nama penulis kutipan", "author.name"),
            Field("author_slug", str, True, "Slug stabil penulis", "author.slug"),
            Field("author_goodreads_link", str, True, "Tautan profil Goodreads penulis", "author.goodreads_link"),
            Field("quote_word_count", int, True, "Jumlah kata kutipan tanpa menyimpan isi", "jumlah token whitespace pada text"),
            Field("tags", list, False, "Tag topik kutipan", "tags[].name"),
        ],
    },
    "seo": {
        "key": "url",
        "fields": [
            Field("url", str, True, "URL halaman yang dipantau", "URL dari sitemap.xml"),
            Field("title", str, True, "Judul dokumen HTML", "elemen title dokumen"),
            Field("h1", str, True, "Judul utama halaman", "heading h1 konten utama"),
            Field("meta_description", str, True, "Deskripsi halaman untuk mesin pencari", "meta description dokumen"),
            Field("canonical", str, True, "URL kanonis halaman", "tautan canonical dokumen"),
            Field("h2_count", int, True, "Jumlah heading tingkat dua", "jumlah heading h2 konten utama"),
            Field("word_count", int, True, "Jumlah kata konten utama", "teks konten utama, dihitung lalu dibuang"),
            Field("link_count", int, True, "Jumlah tautan pada konten utama", "jumlah tautan konten utama"),
            Field("og_title", str, False, "Judul Open Graph", "meta og:title dokumen"),
        ],
    },
    "driftlab": {
        "key": "item_id",
        "fields": [
            Field("item_id", str, True, "Identitas stabil item fixture", "article[data-item-id]"),
            Field("name", str, True, "Nama item fixture", "h1.item-name"),
            Field("price", float, True, "Harga item fixture", "nilai harga halaman detail"),
            Field("category", str, True, "Kategori item fixture", ".item-category"),
            Field("note", str, False, "Catatan detail item fixture", ".item-note"),
        ],
    },
}

VOLATILE = {"fetched_at", "run_id", "scrape_duration_ms"}
