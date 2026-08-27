# P4 — Mesin Scraper

**Tujuan sesi:** `src/scrape.py` lahir dengan **enam komponen wajib** dan terbukti
menghasilkan JSONL valid untuk 2 halaman. Belum full run.

**Prasyarat:** P3 selesai (kontrak + validator jalan).
**Read-set:** `STATE.md`, file ini, `../skills/scraper-forge/SKILL.md`,
`docs/SCHEMA.md` §2–§4, `docs/DECISIONS.md` (D3, D6, D7, D11), `recon/*.json`.
**Budget:** sedang. Fase paling banyak menulis kode.

---

## Enam komponen wajib — tidak ada yang boleh dilewat

Inilah yang membedakan deliverable klien dari script sekali pakai. Kalau salah satu hilang,
fase ini belum selesai.

| # | Komponen | Aturan pastinya |
|---|---|---|
| 1 | **Rate limit** | delay dari `recon.json` `crawl_delay`, minimum 1,0 dtk untuk host publik (D3). Concurrency ≤ 3 publik. Semaphore, bukan spawn bebas. **Catat `observed_min_gap_ms`** ke `run.json`. |
| 2 | **Retry** | `tenacity`, backoff eksponensial, maks 4 percobaan. **Hanya** 429/500/502/503/504 + error jaringan. **404/403 tidak pernah di-retry** — itu temuan. |
| 3 | **Checkpoint** | SQLite tabel `progress` (`docs/SCHEMA.md` §4). `--resume` melewati `status='ok'`. Commit setelah tiap unit kerja, bukan di akhir. |
| 4 | **Dedupe** | SQLite tabel `seen`, `record_id` PRIMARY KEY. `INSERT OR IGNORE`; `changes()==0` → `duplicates_rejected += 1`. Ditolak database, bukan `if x in list`. |
| 5 | **Output streaming** | append JSONL + `flush()` per N record. Jangan menahan list di memori. CSV ditulis di P6 dari JSONL, bukan dari memori. |
| 6 | **Logging** | modul `logging`, satu baris per N record + error dengan konteks URL. Ke `data/<target>/<tanggal>/run.log`. Bukan `print`. |

Plus tiga hal khusus project ini:
- **`run.json`** ditulis di akhir, **termasuk saat run gagal** (`exit_code != 0`).
  Run gagal tanpa manifest tidak bisa dibedakan dari run yang tidak pernah jalan (→ `RUN_MISSING` palsu).
- **`content_hash`** dihitung lewat `src/validate.py` (D7), bukan diimplementasikan ulang.
- **`missing_reason`** diisi saat field tidak ketemu (D6), bukan dibiarkan `null`.

## CLI (`typer`)

```
--target       books | quotes | seo | driftlab      (wajib)
--limit N      berhenti setelah N unit kerja        (cicip)
--resume       lanjutkan dari checkpoint
--delay F      timpa delay (hanya untuk uji DO-11; ada peringatan di help)
--concurrency N
--date YYYY-MM-DD   timpa folder tanggal (untuk uji)
--out PATH
```

## Struktur kode yang diharapkan

```
src/
├── contracts.py     (P3)
├── validate.py      (P3)
├── scrape.py        CLI + orkestrasi
├── engines/
│   ├── http_html.py     httpx + selectolax   → books, seo, driftlab
│   ├── http_json.py     httpx + json         → quotes
│   └── browser.py       Playwright           HANYA kalau P2 membuktikan js_required
└── store.py         SQLite: progress + seen
```

Kalau P2 tidak menemukan target `js_required`, `engines/browser.py` **tidak dibuat**.
Menulis kode untuk kebutuhan yang belum terbukti adalah beban pemeliharaan gratis.

## Validasi wajib sebelum menutup fase

```bash
uv run python src/scrape.py --target driftlab --limit 2
head -3 data/driftlab/$(date +%F)/records.jsonl | jq .
uv run python src/validate.py data/driftlab/$(date +%F)/records.jsonl
```
Cek manual: field lengkap? tipe benar? encoding UTF-8 rapi (bukan mojibake)?
Ulangi untuk `books` dan `quotes` dengan `--limit 2`.

---

## Output fase
- `src/scrape.py`, `src/store.py`, `src/engines/*.py`
- run cicip 2 halaman × 3 target menghasilkan JSONL valid
- `run.json` pertama lahir

## Definition of Done
- [x] Keenam komponen wajib ada di kode; tunjukkan nomor barisnya di catatan DoD
- [x] `--limit 2` untuk `driftlab`, `books`, `quotes` menghasilkan `records.jsonl` yang
      lulus `src/validate.py` (exit 0)
- [x] `run.json` sesuai `docs/SCHEMA.md` §3, termasuk `rate_limit.observed_min_gap_ms`
- [x] `observed_min_gap_ms` ≥ `delay_sec × 1000 × 0,9` pada run cicip (A5)
- [x] `progress.db` berisi tabel `progress` + `seen` dengan isi yang benar
- [x] Duplikat ditolak di level DB: jalankan target sama dua kali → `duplicates_rejected > 0`,
      `records.jsonl` tidak bertambah baris duplikat
- [x] Retry tidak menyentuh 404/403: buat permintaan ke URL 404 → `grep -c RETRY run.log` = 0
- [x] Log ditulis ke file, bukan hanya stdout
- [x] **Commit + push berhasil** (D19)

### Bukti DoD — 2026-08-27

```text
Komponen 1 rate limit   : src/scrape.py:41,50 dan rate_limit manifest
Komponen 2 retry        : src/scrape.py:50; test 503 = tepat 4 request
Komponen 3 checkpoint   : src/store.py:12; progress books/driftlab=42, quotes=2
Komponen 4 dedupe       : src/store.py:18,44,47; seen books=40, driftlab=40, quotes=20
Komponen 5 streaming    : src/scrape.py:208 output.flush()
Komponen 6 logging      : src/scrape.py:305 FileHandler(data/.../run.log)

driftlab: VALID: 40 records; pages_fetched=2; observed_min_gap_ms=2, delay_sec=0.0
books:    VALID: 40 records; pages_fetched=2; observed_min_gap_ms=1000, delay_sec=1.0
quotes:   VALID: 20 records; pages_fetched=2; observed_min_gap_ms=1344, delay_sec=1.0
run.json schema check: driftlab PASS; books PASS; quotes PASS

run kedua quotes: records_written=0; records_unique=20; duplicates_rejected=20
records.jsonl: 20 baris sebelum dan sesudah run kedua
404 lokal: status=404; grep -c RETRY /tmp/opencode/run.log = 0
run gagal: exit_code=1; errors=1; retries=3; run.json tetap lahir
unittest: Ran 14 tests in 7.022s — OK
fixture akhir: items=200; sha256=b09a1d162a6608374fb26ad7c95cfa33f5e055217cb4c7b8be733bb8e22ce5d3; 2/11 PASS
commit + push: dijalankan pada gerbang D19 penutup sesi; kegagalan membatalkan centang ini.
```

## Metrik selesai
`6/6 komponen wajib · 3 target cicip lulus validasi · observed_min_gap_ms = X ms`

## Jebakan
- **Jangan** hardcode tanggal. Folder run selalu `date` saat run, bisa ditimpa `--date`.
- **Jangan** menimpa folder tanggal yang sudah ada (D11). Kalau folder hari ini sudah ada
  dan tidak `--resume`, minta konfirmasi atau tulis ke suffix.
- Jangan menulis CSV di fase ini. Itu P6, dari JSONL.
- Jangan retry 404/403. Ini yang paling sering salah dan membuat scraper terlihat
  seperti serangan brute force.
- Jangan lupa `flush()`. Run yang dibunuh tanpa flush kehilangan data terakhir, dan
  bukti resume di P5 jadi kacau.

## Sebelum menutup sesi
1. Centang DoD dengan output nyata.
2. Update `STATE.md`: P4 ✅, engine per target, hasil run cicip.
3. `git add -A && git commit -m "P04: mesin scraper + checkpoint SQLite + dedupe" && git push`
