# DriftWatch — Keputusan Terkunci

Sumber kebenaran untuk hal yang dulu ambigu atau bisa bergeser antar sesi.
Kalau file lain berbeda dengan file ini, **file ini menang** — dan file itu yang diperbaiki.
Jangan ubah keputusan di sini tanpa persetujuan user; catat tanggal kalau diubah.

Dikunci: 2026-08-27 (D1–D15 ditetapkan bersama plan).
Tanda 🔓 = sengaja dibiarkan terbuka, wajib dikunci di fase yang disebut.

---

## D1 — Empat target, dengan peran berbeda

| Kode | Target | Peran | Volume |
|---|---|---|---|
| `books` | `books.toscrape.com` | dataset volume (bukti ≥ 1.000 baris) | 1.000 buku |
| `quotes` | `quotes.toscrape.com` | bukti "turun lapis": temukan endpoint JSON, buang browser | ~100 kutipan |
| `seo` | 1 situs publik nyata, dipilih & digerbang di P1 | realisme job 22 (metadata SEO) | 50–500 URL |
| `driftlab` | fixture lokal `127.0.0.1:8100` | **oracle** untuk diff & alarm | 200 record |

`books.toscrape.com` dan `quotes.toscrape.com` adalah sandbox yang memang dibuat untuk
latihan scraping — nol risiko ToS. Target `seo` **wajib** lolos gerbang `docs/ETHICS.md` §2.

## D2 — Kenapa ada fixture lokal (`driftlab`)

`books.toscrape.com` tidak pernah berubah. Kalau diff hanya diuji di sana, hasilnya selalu
"0 baru, 0 berubah, 0 hilang" — tidak membuktikan apa pun, dan alarm tidak pernah terpicu.

`driftlab` adalah situs statis lokal yang **sengaja dimutasi** oleh `scripts/drift_lab.py`
menurut 11 skenario di `docs/DRIFT_ORACLES.md`. Ia adalah padanan `PLANTED_BUGS` di project 1:
oracle untuk mengukur recall, **bukan** input detektor. Mesin diff tidak boleh tahu skenario
mana yang sedang aktif.

## D3 — Etika request (angka pasti)

- Delay default **1,0 detik per request per host**. Kalau `robots.txt` menyebut `Crawl-delay`
  lebih besar, yang lebih besar menang. Tidak pernah lebih kecil dari 1,0 dtk untuk host publik.
- Concurrency maksimum **3** untuk host publik, bebas untuk `driftlab` (lokal).
- User-Agent tetap: `DriftWatch/1.0 (+mailto:rayinailham9@gmail.com)`. Jujur, ada kontak,
  tidak meniru browser.
- Jam jalan terjadwal: **09:00 WIB** (`Asia/Jakarta`), dengan `RandomizedDelaySec=300`.
- Pelanggaran delay yang terdeteksi sendiri memicu alarm `RATE_LIMIT_VIOLATION` (D9).
  Pipeline ini mengawasi kesopanannya sendiri.

## D4 — Enum kode alarm tertutup (10 nilai)

`ZERO_RECORDS`, `RECORD_COUNT_DROP`, `FIELD_COMPLETENESS_DROP`, `SCHEMA_UNKNOWN_FIELD`,
`HTTP_ERROR_SPIKE`, `RUN_MISSING`, `RUN_FAILED`, `DURATION_ANOMALY`,
`RATE_LIMIT_VIOLATION`, `CHURN_SPIKE`.

Nilai di luar daftar ini **dilarang** masuk `reports/alerts.jsonl`. Enum tertutup ini yang
membuat laporan klien bisa dibaca konsisten dan alarm bisa di-dedupe.

## D5 — Ambang alarm (kunci; jangan diubah per sesi)

| Kode | Aturan pasti | Severity |
|---|---|---|
| `ZERO_RECORDS` | `records_unique == 0` | critical |
| `RECORD_COUNT_DROP` | `records_unique < baseline × 0,80` | critical |
| `FIELD_COMPLETENESS_DROP` | field `required` mana pun turun ke `< 98%`, **atau** turun `> 10` poin persen vs baseline | critical |
| `SCHEMA_UNKNOWN_FIELD` | parser menghasilkan key di luar `contracts.py` | warning |
| `HTTP_ERROR_SPIKE` | `≥ 10%` request non-2xx (setelah retry habis) | critical |
| `RUN_MISSING` | tidak ada `run.json` untuk tanggal terjadwal, dicek pada H+1 | critical |
| `RUN_FAILED` | `run.json.exit_code != 0` | critical |
| `DURATION_ANOMALY` | `duration_sec > 3 ×` median 7 run terakhir **dan** `> 60` dtk | warning |
| `RATE_LIMIT_VIOLATION` | `observed_min_gap_ms < delay_sec × 1000 × 0,9` | warning |
| `CHURN_SPIKE` | `(changed + removed) > 30%` dari baseline | warning |

`baseline` = run sukses terakhir sebelum run yang sedang dinilai. Kalau belum ada baseline,
run pertama ditandai `baseline: null` dan **tidak** memicu alarm perbandingan.

## D6 — Field kosong wajib beralasan

Record boleh punya field kosong, tapi `missing_fields` harus menyebut nama field dan
`missing_reason` harus menyebut sebabnya (mis. `"elemen #product_description tidak ada"`).
Kosong tanpa keterangan = cacat data, dihitung gagal di `src/validate.py`.

## D7 — Identitas & deteksi perubahan

- `record_id` = `"{target}:{key_field}:{nilai}"`, stabil antar run. Ini kunci dedupe (`PRIMARY KEY`).
- `content_hash` = `sha256` atas JSON kanonik `fields` (key terurut, tanpa spasi).
  Diff menyatakan sebuah record **changed** kalau `record_id` sama tapi `content_hash` beda.
- Field yang volatil (`fetched_at`, `run_id`, `scrape_duration_ms`) **dikecualikan** dari hash.
  Kalau tidak, semua record akan tampak berubah tiap hari dan diff jadi sampah.

## D8 — Fixture `driftlab` dilayani Python stdlib, bukan container

Diubah 2026-08-27 (semula: nginx lewat `docker-compose.yml` milik project ini).

`scripts/lab_serve.py` — `http.server` dari stdlib dengan handler kustom,
bind `127.0.0.1:8100`. **Project ini tidak punya `docker-compose.yml` sama sekali.**

Tiga alasan, berurutan dari yang paling mengikat:

1. **Dua skenario oracle butuh server yang bisa diprogram.** DO-06 (15% request dibalas
   HTTP 503) dan DO-08 (jeda 4 detik di 10% halaman) mustahil dilakukan nginx statis tanpa
   mengarang konfigurasi bersyarat. Dengan handler Python, keduanya jadi lima baris yang
   membaca berkas penanda skenario.
2. **Deliverable harus berdiri sendiri.** A11 menuntut `make all` jalan di salinan bersih,
   dan klien harus bisa menjalankannya di mesin mereka. Menuntut Docker untuk sebuah
   *fixture uji* adalah beban yang tidak dibayar apa pun.
3. **Nol pemasangan.** `http.server`, `sqlite3`, `csv`, `json` semuanya stdlib.

Tetap: bind `127.0.0.1` (jangan `0.0.0.0`), port **8100**, salinan bersih **8101**.
Ganti port berarti mengubah D8 ini.

## D16 — Target `seo`: dokumentasi HTTPX

Dikunci 2026-08-27 di P1: `https://www.python-httpx.org/` menjadi target `seo`.

Alasan: seluruh tujuh kotak `docs/ETHICS.md` §2 lolos, sitemap valid hanya memuat 23 URL,
dan situs adalah dokumentasi proyek open-source. Dibanding kandidat FastAPI (151 URL),
HTTPX memberi bukti monitoring SEO nyata dengan beban host publik paling kecil. Robots
tidak tersedia (HTTP 404), jadi default D3 tetap berlaku: 1,0 detik/request, concurrency
maksimum 3, User-Agent jujur. Hanya metadata teknis yang disimpan.

## D21 — Infra device dipakai untuk tooling waktu-bangun, bukan runtime deliverable

Ditetapkan user 2026-08-27: "manfaatkan tools yang ada di infrastruktur device ini,
jangan tiap project pasang ulang."

**Garis pemisahnya satu:**

| | Boleh pakai infra device | Wajib berdiri sendiri |
|---|---|---|
| Kapan | saat **membangun** portofolio (diagram, PDF, recon) | saat pipeline **berjalan** tiap hari & di mesin klien |
| Contoh | PlantUML `:20080`, `pandoc/core`, MCP browser, cache `uv`, cache Playwright | scraper, checkpoint, diff, alarm, laporan |

Alasan garis itu ada: pipeline ini **dikirim ke klien**. Apa pun yang dipakai saat runtime
ikut jadi syarat pemasangan di mesin mereka. Diagram arsitektur tidak ikut dikirim, jadi
alat pembuatnya bebas.

**Konsekuensi yang mengikat:**

- **Checkpoint & dedupe tetap SQLite.** Dilarang memakai MySQL `:3306`, Redis `:6379`,
  atau TiDB `:4000` yang ada di device. Jaminan "bisa diputus lalu lanjut" tidak boleh
  bergantung pada layanan jaringan yang tidak dimiliki klien.
- **Laporan XLSX tetap `openpyxl`**, bukan MCP `excel`. Laporan dibangun tanpa pengawasan
  pukul 09:00 oleh systemd; MCP butuh sesi agent yang hidup.
- **Diagram pakai service `plantuml` milik infra** (image `plantuml/plantuml-server:jetty`
  sudah ada, 1,13 GB — nol unduhan).
- **PDF studi kasus pakai `pandoc/core`** (`docker run --rm`, image sudah ada, 305 MB),
  **bukan** `texlive/texlive` (8,73 GB) meski dua-duanya terpasang. Pandoc cukup untuk
  satu halaman A4.
- **Dependency Python lewat `uv`** — venv per project, tapi cache paket global di
  `~/.cache/uv` (1,6 GB terisi). Paket yang sama tidak pernah diunduh dua kali.
- **Browser Playwright** dari `~/.cache/ms-playwright` (2,0 GB) yang sudah ada.
  Jangan sekali-kali menghapus revisi lama.

## D22 — Mengatur infra device: boleh, kecuali `9router`

Diperbarui user 2026-08-27: *"kalau ada infra device yang mati atau hidup gak kepakai kamu
boleh kok atur-atur sesuai kebutuhan, dan yang penting 9router jangan pernah dimatikan."*

### 🚨 D22-A — `9router.service` TIDAK PERNAH DISENTUH

```
unit    : 9router.service          (systemd USER unit, bukan container)
berkas  : ~/.config/systemd/user/9router.service
port    : 20128
kerja di: /home/rayin/infra/apps/9router   ·   data: /home/rayin/infra/data/9router
peran   : 9Router — local AI proxy
```

**Dilarang mutlak:** `stop`, `restart`, `kill`, `disable`, `mask`, mengedit atau menghapus
berkas unit-nya, menyentuh `apps/9router/` atau `data/9router/`, dan memakai port `20128`.

Dua alasan kenapa ini lebih berbahaya dari kelihatannya:

1. **Ia proxy AI lokal.** Mematikannya bisa memutus koneksi sesi agent itu sendiri.
   Gejalanya akan tampak seperti sesi mati acak, bukan seperti "salah matikan service" —
   jadi penyebabnya sulit ditemukan justru oleh yang menyebabkannya.
2. **Ia tinggal satu direktori dengan unit DriftWatch.** P7 memasang
   `driftwatch.timer` ke `~/.config/systemd/user/` — direktori yang sama.
   Perintah sapu-bersih (`systemctl --user stop '*'`, `reset-failed` massal, membersihkan
   isi direktori itu) akan ikut membunuhnya. **Selalu sebut nama unit secara eksplisit:**
   `systemctl --user restart driftwatch.timer`, tidak pernah wildcard.

`systemctl --user daemon-reload` aman — ia hanya memuat ulang definisi, tidak menghentikan
apa pun.

### D22-B — Sisanya bebas diatur

| Tindakan | |
|---|---|
| `up` / `start` service infra yang mati (`plantuml`, `mysql`, `redisinsight`, dst) | ✅ tanpa tanya |
| `stop` / `restart` service infra yang hidup tapi tidak dipakai | ✅ tanpa tanya |
| `docker run --rm` image yang sudah ada | ✅ |
| Membaca `/home/rayin/infra/docker-compose.yml` | ✅ |
| Menyentuh container `crosscheck-tut-*` (project 1, masih hidup) | ⚠️ tanya dulu — itu target uji project lain |
| Mengedit `docker-compose.yml` | ⚠️ tanya dulu — konfigurasi bersama, dipakai pekerjaan lain. DriftWatch tidak membutuhkannya (D8). |
| Menulis ke `infra/latex/` | ❌ sudah dipakai pekerjaan lain (skripsi) |
| Apa pun terhadap `9router` | ❌ **D22-A** |

Keadaan saat plan ditulis (2026-08-27) — **hidup:** `9router.service` (jangan sentuh),
`redis-db`, `tidb-pd/tikv/server`, `crosscheck-tut-*`.
**Mati:** `plantuml-server`, `infra-dashboard`, `mysql-db`, `redisinsight`, dan ±20
container project lain yang sudah `Exited`.

---

## 🔓 Terbuka — wajib dikunci

| Kode | Pertanyaan | Dikunci di |
|---|---|---|
| 🔓 D17 | Field wajib final per target (setelah recon nyata) | P3 |
| 🔓 D18 | Halaman demo dipublikasikan lewat Artifact claude.ai atau file statis? | P10 |
| 🔓 D20 | Repo dijadikan publik? | P12, **butuh izin user terpisah** |
