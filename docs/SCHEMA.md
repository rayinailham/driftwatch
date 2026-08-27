# DriftWatch — Skema File Hasil

Semua fase menulis dan membaca bentuk di bawah ini apa adanya.
Perubahan skema harus lewat `docs/DECISIONS.md` dulu.
Enum kode alarm ada di D4, ambangnya di D5, aturan identitas di D7.

**Status: terkunci (D17).** Dicocokkan dengan `recon.json` nyata di P3 dan
`src/validate.py` menegakkannya secara otomatis.

---

## 0. Tata letak folder hasil

```
data/
└── <target>/                       books | quotes | seo | driftlab
    └── <YYYY-MM-DD>/
        ├── records.jsonl           satu record per baris
        ├── records.csv             turunan, utf-8-sig (D12)
        ├── run.json                manifest run
        └── run.log                 log mentah (rotasi 30 hari)
reports/
├── alerts.jsonl                    semua alarm, append-only
└── <target>/
    └── <YYYY-MM-DD>/
        ├── diff.json               mesin
        └── daily.md                untuk manusia / klien
recon/
└── <target>.json                   hasil skill web-recon (P2)
```

---

## 1. `recon/<target>.json` (P2)

Mengikuti skill `web-recon` apa adanya, dengan **tiga field tambahan wajib**:

```json
{
  "target": "books",
  "base_url": "https://books.toscrape.com",
  "recon_at": "2026-08-27",
  "robots": { "allowed": true, "crawl_delay": null, "disallow": [], "checked_url": "…/robots.txt" },
  "sitemap": null,
  "render_mode": "server_html",
  "api": { "works_without_browser": true },
  "selectors": { "list_item": "article.product_pod", "title": "h3 a[title]" },
  "pagination": { "type": "page_param", "param": "page", "start": 1, "stop_when": "tombol next hilang" },
  "auth": { "required": false },
  "protection": { "cloudflare": false, "captcha": false, "rate_limit_observed": null },
  "schema": [ { "field": "upc", "type": "string", "required": true } ],
  "sample": [ { "upc": "a897fe39b1053632", "title": "A Light in the Attic" } ],
  "recommended_engine": "httpx+selectolax",

  "engine_rationale": "HTML server-rendered; tidak ada XHR JSON. Browser tidak diperlukan.",
  "ethics_gate": { "passed": true, "checked_at": "2026-08-27", "notes": "sandbox latihan resmi" },
  "expected_volume": 1000
}
```

- `engine_rationale` wajib menyebut **kenapa browser tidak dipakai**, atau kalau dipakai,
  bukti apa yang memaksanya.
- `ethics_gate.passed` harus `true`. Kalau `false`, target dibuang di P1/P2 dan alasannya
  dicatat di `docs/TARGETS.md`. Scraper **dilarang** dibangun untuk target yang gagal gerbang.
- `expected_volume` jadi baseline awal alarm `RECORD_COUNT_DROP` pada run pertama.

---

## 2. `data/<target>/<date>/records.jsonl` — satu record per baris

```json
{
  "record_id": "books:upc:a897fe39b1053632",
  "target": "books",
  "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "run_id": "2026-08-27T09-00-00",
  "fetched_at": "2026-08-27T09:00:12+07:00",
  "content_hash": "sha256:6f1c…",
  "fields": {
    "upc": "a897fe39b1053632",
    "title": "A Light in the Attic",
    "price_incl_tax": 51.77,
    "availability_count": 22,
    "rating": 3,
    "category": "Poetry"
  },
  "missing_fields": ["description"],
  "missing_reason": { "description": "elemen #product_description tidak ada di halaman" }
}
```

Aturan:
- `record_id` — D7. Unik dalam satu target. Duplikat ditolak di level SQLite, bukan di Python.
- `content_hash` — sha256 atas `json.dumps(fields, sort_keys=True, separators=(",",":"), ensure_ascii=False)`.
  `fetched_at`, `run_id`, `scrape_duration_ms` **tidak** ikut di-hash (D7). Field bisnis
  `url` milik target `seo` tetap ikut.
- `fields` hanya boleh memuat key yang terdaftar di `src/contracts.py`. Key asing memicu
  `SCHEMA_UNKNOWN_FIELD`.
- `missing_fields` kosong = `[]`, bukan `null`. Tiap entri wajib punya pasangan di
  `missing_reason` (D6).
- Tidak ada HTML mentah di nilai field mana pun. String dipangkas maksimal 2.000 karakter.

### 2b. Field per target (D17)

| Target | Kunci identitas | Field `required` | Field opsional |
|---|---|---|---|
| `books` | `upc` | `upc`, `title`, `price_incl_tax_gbp`, `price_excl_tax_gbp`, `tax_gbp`, `availability_count`, `in_stock`, `rating`, `category`, `num_reviews` | `description_words` |
| `quotes` | `quote_id` (`sha256(text)[:16]`) | `quote_id`, `author_name`, `author_slug`, `author_goodreads_link`, `quote_word_count` | `tags` |
| `seo` | `url` | `url`, `title`, `h1`, `meta_description`, `canonical`, `h2_count`, `word_count`, `link_count` | `og_title` |
| `driftlab` | `item_id` | `item_id`, `name`, `price`, `category` | `note` |

Untuk `quotes`, teks karya hanya dipakai sementara untuk menurunkan `quote_id` dan
`quote_word_count`, lalu dibuang. Dataset tidak menyimpan atau meredistribusikan teks kutipan.

---

## 3. `data/<target>/<date>/run.json` — manifest run

```json
{
  "run_id": "2026-08-27T09-00-00",
  "target": "books",
  "started_at": "2026-08-27T09:00:00+07:00",
  "finished_at": "2026-08-27T09:18:41+07:00",
  "duration_sec": 1121.4,
  "engine": "httpx+selectolax",
  "exit_code": 0,
  "resume_used": false,
  "pages_fetched": 51,
  "records_written": 1000,
  "records_unique": 1000,
  "duplicates_rejected": 0,
  "errors": 0,
  "http_status_counts": { "200": 1051, "404": 0, "503": 0 },
  "retries": 3,
  "field_completeness": { "upc": 1.0, "title": 1.0, "description": 0.987 },
  "rate_limit": { "delay_sec": 1.0, "concurrency": 3, "observed_min_gap_ms": 1004 },
  "code_version": "git:9a3f1c2"
}
```

- `field_completeness` — pecahan 0–1 per field, dihitung atas `records_unique`.
  Ini yang dipakai alarm `FIELD_COMPLETENESS_DROP`.
- `observed_min_gap_ms` — jeda **terkecil** yang benar-benar terjadi antar request ke host yang
  sama. Ini bukti "rate limit dihormati" untuk klien, dan pemicu `RATE_LIMIT_VIOLATION`.
- `exit_code` ≠ 0 memicu `RUN_FAILED`. `run.json` tetap ditulis meski run gagal —
  run yang gagal tanpa manifest tidak bisa dibedakan dari run yang tidak pernah jalan.

---

## 4. `data/<target>/<date>/progress.db` (SQLite, checkpoint)

```sql
CREATE TABLE IF NOT EXISTS progress (
  key        TEXT PRIMARY KEY,   -- unit kerja: "page:3" | "detail:<url>"
  status     TEXT,               -- pending | ok | error
  fetched_at TEXT,
  error      TEXT
);
CREATE TABLE IF NOT EXISTS seen (
  record_id    TEXT PRIMARY KEY, -- dedupe, D7
  content_hash TEXT
);
```

`--resume` melewati semua `progress.status='ok'`. Dedupe memakai `INSERT OR IGNORE` ke `seen`;
`changes()` = 0 berarti duplikat → `duplicates_rejected += 1`.

---

## 5. `reports/<target>/<date>/diff.json`

```json
{
  "target": "books",
  "date": "2026-08-28",
  "baseline_date": "2026-08-27",
  "counts": { "added": 12, "changed": 4, "removed": 1, "unchanged": 983, "baseline_total": 988 },
  "added": [ { "record_id": "books:upc:…", "url": "…", "summary": "Judul Buku Baru" } ],
  "changed": [
    { "record_id": "books:upc:…", "url": "…",
      "fields_changed": [ { "field": "price_incl_tax", "from": 51.77, "to": 48.5 } ] }
  ],
  "removed": [ { "record_id": "books:upc:…", "url": "…", "summary": "Judul Lama", "last_seen": "2026-08-27" } ],
  "health": {
    "records_unique": 995, "baseline_unique": 988, "duration_sec": 1108.2,
    "error_rate": 0.0, "field_completeness_delta": { "description": -0.004 }
  },
  "alarms": [ "RECORD_COUNT_DROP" ]
}
```

- `added` / `changed` / `removed` dipotong maksimal **50 entri** di JSON; jumlah penuh tetap
  akurat di `counts`. Kalau terpotong, ada field `"truncated": true`.
- `fields_changed.from` / `.to` dipangkas 200 karakter.
- `alarms` hanya memuat **kode** (D4). Detail alarm ada di `reports/alerts.jsonl`.

---

## 6. `reports/alerts.jsonl` — append-only, satu alarm per baris

```json
{
  "raised_at": "2026-08-28T09:20:03+07:00",
  "target": "books",
  "date": "2026-08-28",
  "code": "RECORD_COUNT_DROP",
  "severity": "critical",
  "observed": 412,
  "expected": 790.4,
  "baseline": 988,
  "message": "Hanya 412 record terkumpul, di bawah ambang 80% dari 988 baseline.",
  "likely_cause": "Selector `article.product_pod` kemungkinan sudah berubah di situs sumber.",
  "next_action": "Jalankan `make recon TARGET=books` lalu bandingkan selector dengan recon lama."
}
```

- `severity` ∈ `critical` | `warning` | `info` (D5).
- `message` **wajib bebas jargon** — ini yang dibaca klien. Dilarang memuat kata seperti
  `selectolax`, `tenacity`, `storage_state`, `stacktrace`. `likely_cause` boleh teknis
  karena dibaca developer.
- `next_action` wajib berupa perintah atau langkah konkret, bukan "periksa lebih lanjut".

---

## 7. `reports/<target>/<date>/daily.md` — digest harian untuk klien

Bentuk pastinya di `docs/CLIENT_REPORT.md` §2. Yang dikunci di sini: file itu **wajib ada
setiap hari**, bahkan ketika tidak ada perubahan sama sekali. Hari yang sunyi tetap dilaporkan
("0 baru, 0 berubah, 0 hilang, pipeline sehat") — justru itu yang membangun kepercayaan.

---

## 8. `web/data.json` (P10, halaman demo)

```json
{
  "generated_at": "2026-08-28T09:25:00+07:00",
  "target": "books",
  "source": { "name": "books.toscrape.com", "url": "https://books.toscrape.com", "attribution": "sandbox latihan scraping" },
  "counts": { "total": 1000, "added_today": 12, "changed_today": 4, "removed_today": 1 },
  "insight": { "model": "…", "text": "…", "generated_at": "…", "input_tokens": 0, "output_tokens": 0 },
  "rows": [ { "…": "maksimal 200 baris, metadata saja (D13)" } ]
}
```

Kunci API, path lokal, dan nama host internal **tidak boleh** muncul di file ini.
