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
- Pelanggaran delay yang terdeteksi sendiri memicu alarm `RATE_LIMIT_VIOLATION` (D5).
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

## D9 — Penjadwalan memakai systemd user timer

Dikunci 2026-08-27 di P7 setelah `systemctl --user` diverifikasi tersedia. Pipeline berjalan
setiap 09:00 WIB (`Asia/Jakarta`) dengan `RandomizedDelaySec=300` dan `Persistent=true`.
Unit bertipe `oneshot`, memakai `flock`, dan menyimpan exit gagal bila target mana pun gagal
tanpa membatalkan target berikutnya. Cron tidak dipakai karena kehilangan catch-up dan log
terstruktur. Unit DriftWatch selalu disebut eksplisit; `9router.service` tidak disentuh (D22-A).

## D10 — Orkestrasi operator memakai Make

Dikunci 2026-08-27 di P7 karena GNU Make tersedia sedangkan `just` tidak. `Makefile` memakai
`MAKEFLAGS := -j16` untuk target aman yang dapat diparalelkan dan `.NOTPARALLEL:` sebagai
gerbang konservatif sampai target paralel eksplisit lahir. P7 membuka `make prune`; P12 akan
melengkapi gerbang publik tanpa menambah runtime dependency.

## D11 — Snapshot tanggal tidak pernah ditimpa diam-diam

Setiap run menulis ke `data/<target>/<YYYY-MM-DD>/`. Kalau folder sudah berisi hasil,
run tanpa `--resume` wajib meminta konfirmasi eksplisit; run tanpa konfirmasi berhenti.
`--resume` memakai checkpoint SQLite dan append JSONL, sehingga baseline lama tetap utuh.

Alasan: menimpa snapshot menghapus baseline diff dan merusak bukti monitoring. Perilaku ini
sudah diwajibkan aturan data serta fase P4; entri D11 dipulihkan 2026-08-27 karena daftar
keputusan sebelumnya mengklaim D1–D15 terkunci tetapi tidak memuat teks D11.

## D12 — CSV kompatibel Excel dan mengikuti kontrak

Dikunci 2026-08-27 di P6 saat format ekspor pertama kali dipakai. `records.csv` ditulis
dengan encoding `utf-8-sig`; kolom bisnis mengikuti urutan field di `src/contracts.py`;
nilai list seperti `tags` digabung dengan `"; "`; kolom teknis berada di sisi kanan,
dengan `content_hash` dan `run_id` sebagai dua kolom terakhir. CSV selalu diturunkan dari
`records.jsonl`, sehingga JSONL tetap sumber data utama dan tidak pernah diubah oleh ekspor.

## D17 — Kontrak field final per target

Dikunci 2026-08-27 di P3 setelah dicocokkan dengan 12 sampel recon nyata. Bentuk final
ada di `docs/SCHEMA.md` §2b dan ditegakkan oleh `src/contracts.py` + `src/validate.py`:

- `books`: 11 field (10 required), kunci `upc`.
- `quotes`: 6 field (5 required), kunci `quote_id = sha256(text)[:16]`.
- `seo`: 9 field (8 required), kunci `url`.
- `driftlab`: 5 field (4 required), kunci `item_id`.

Khusus `quotes`, teks kutipan tidak disimpan karena batas metadata-only. Parser hanya
memakainya sementara untuk menghitung `quote_id` dan `quote_word_count`, lalu membuangnya.
`tags` tetap opsional karena 1/100 sampel recon kosong. `books.description_words`,
`seo.og_title`, dan `driftlab.note` juga opsional; field lain terbukti stabil di recon.

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

## D13 — Halaman demo: metadata saja, maksimal 200 baris per situs

Dikunci 2026-08-28 di P10 saat halaman demo pertama kali dibangun.

`web/data.json` dan `web/index.html` hanya memuat **metadata kontrak** (`src/contracts.py`)
plus `record_id`, `url` sumber, dan status diff (`baru` / `berubah` / `tetap`). Tidak ada isi
karya: teks kutipan tidak disimpan sejak D17, deskripsi buku hanya dihitung katanya, dan
halaman `seo` hanya menyumbang judul, H1, meta description, jumlah kata, dan jumlah tautan.

Batas keras: **200 baris per situs**, diurutkan agar baris `baru`/`berubah` naik lebih dulu —
yang layak dilihat manusia harus ada di layar pertama, bukan di baris ke-800.

Target `driftlab` **tidak** dipublikasikan. Ia fixture lokal di `127.0.0.1`, dan alamat host
internal dilarang muncul di halaman publik. Yang terbit hanya `books`, `quotes`, `seo`.

Setiap halaman wajib memuat baris atribusi (nama situs + tautan) dan catatan etika
(`robots.txt` dihormati, 1 permintaan/detik, User-Agent jujur berisi kontak) — `docs/ETHICS.md` §3.

## D14 — Insight LLM: model termurah yang memadai, dengan pagar biaya

Dikunci 2026-08-28 di P10. Model dan tarif diambil dari skill `claude-api`
(tabel model, cache 2026-06-24), bukan dari ingatan.

**Model: `claude-haiku-4-5`** — $1,00 / 1 juta token masuk, $5,00 / 1 juta token keluar;
tarif terendah pada tabel dan cukup untuk tugasnya, yaitu meringkas ~20 baris agregat menjadi
maksimal empat kalimat. Ini bukan tugas penalaran berat, jadi model kelas Opus tidak dibayar
apa pun di sini. Pemilihan "termurah yang memadai" adalah instruksi eksplisit fase P10.

Pagar biaya, semuanya ditegakkan di `src/publish.py`:

| Pagar | Cara ditegakkan |
|---|---|
| Maks 1 panggilan per target per hari | insight hari ini dipakai ulang dari `web/data-<target>.json` |
| Input = agregat, bukan dataset | hanya `counts`, delta kelengkapan, kode alarm, dan 10 baris teratas |
| `max_tokens` 400 | ringkasan pendek; tidak ada jalan membengkak |
| Biaya nol atas permintaan | `--no-llm` — SDK `anthropic` bahkan tidak diimpor |
| Kunci kosong bukan crash | jatuh otomatis ke mode tanpa LLM dengan peringatan |
| Biaya terukur | `input_tokens` + `output_tokens` dicatat di `web/data.json` |

Kegagalan API (status error atau tidak bisa terhubung) juga jatuh ke mode tanpa LLM.
Halaman tetap terbit dengan angka dan tabel dari data asli; hanya blok ringkasannya kosong,
dan blok itu selalu berlabel jelas bahwa isinya dibuat AI.

## D18 — Halaman demo terbit sebagai berkas statis lokal, bukan hosting publik

Dikunci 2026-08-28 di P10 atas keputusan user, dari tiga jalur yang ditawarkan
(Artifact claude.ai · GitHub Pages · berkas statis lokal).

`web/index.html` adalah satu berkas mandiri: payload JSON ditanam langsung di dalamnya, tanpa
`fetch`, tanpa pustaka pihak ketiga, sehingga bisa dibuka lewat `file://` tanpa server apa pun.
Ia ikut masuk repo dan diperbarui otomatis oleh langkah (7) `scripts/daily_run.sh`.

Alasan jalur ini dipilih: GitHub Pages menuntut repo publik (🔓 D20, izin terpisah dan belum
diberikan), sedangkan Artifact menuntut redeploy manual tiap data berubah — keduanya membayar
ongkos untuk sesuatu yang belum dibutuhkan. Konsekuensi yang diterima sadar: **tidak ada URL
publik**, jadi bukti A9 berupa halaman yang dirender lokal, bukan tautan yang bisa dibuka orang
lain. Kalau nanti dibutuhkan URL hidup, `web/index.html` sudah siap terbit apa adanya —
keputusan ini yang diubah, bukan kodenya.

## D23 — Deteksi run terlewat memakai preflight dan watchdog H+1

Dikunci 2026-08-28 saat remediasi audit reliability. `RUN_MISSING` diperiksa untuk tanggal
kemarin dengan dua jalur lokal: preflight di awal `scripts/daily_run.sh`, dan timer terpisah
`driftwatch-watchdog.timer` pukul 10:00 WIB. Watchdog diperlukan karena preflight pipeline
utama tidak pernah berjalan bila timer harian mati total. Keduanya memanggil detector yang
sama, tanpa daemon Python, cron, layanan jaringan, atau database eksternal.

Alert tetap append-only, tetapi identitas `(target, date, code)` dideduplikasi sebelum tulis
dan notifikasi. Pemeriksaan berulang tetap mengembalikan status kritis agar systemd terlihat
gagal, tanpa menambah baris `RUN_MISSING` identik. Tanggal target selalu diberikan eksplisit
ke detector; test tidak bergantung jam nyata.

## D24 — Fixture DriftLab dinyalakan pipeline, dan alarm yang sembuh ditutup

Dikunci 2026-08-31 saat menutup dua cacat yang saling menyamarkan.

**(a) Fixture.** Target `driftlab` menembak `http://127.0.0.1:8100`, tetapi `scripts/daily_run.sh`
tidak pernah menyalakan server itu. Saat unit dipicu timer (bukan sesi manual yang kebetulan
sudah menjalankan `lab_up.sh`), panen `driftlab` selalu 0 record dan unit selalu `exit 1` —
tiga hari berturut (29, 30, 31 Agustus 2026). Perbaikan: langkah (0) memanggil `lab_up.sh`
sebelum loop target dan `lab_down.sh` lewat `trap EXIT`, hanya bila `driftlab` ada di
`$TARGETS`. Keduanya bisa ditimpa (`DRIFTWATCH_LAB_UP`/`DRIFTWATCH_LAB_DOWN`) supaya uji shell
tidak butuh server sungguhan. Run harian tidak meninggalkan fixture menyala.

**(b) Alarm yang sembuh.** `alerts.jsonl` tetap append-only (D23), tetapi run ulang yang
berhasil sekarang menandai baris lamanya `resolved_at` alih-alih membiarkannya. Tanpa ini,
`daily.md` hasil run yang sudah sembuh masih mengutip alarm run gagal — tabel angkanya
menunjukkan "200 data, kelengkapan 100%" sementara ringkasannya berkata "tidak ada data yang
berhasil dikumpulkan hari ini". Baris tidak pernah dihapus, hanya diberi stempel, supaya jejak
kegagalan tetap bisa diaudit; `report.py` mengabaikan baris ber-`resolved_at`.

Penutupan itu **berlingkup**: `append_alerts(scope=…)` hanya boleh menutup kode yang benar-benar
diuji run tersebut (`evaluated_codes()`). Pemeriksaan sempit `--check-missing` berlingkup
`{"RUN_MISSING"}` saja — tanpa pagar itu, watchdog H+1 akan diam-diam menutup temuan panen
yang masih sah. Dua test regresi mengunci keduanya, ditambah satu test yang mengunci bahwa
nama detector = kode alarmnya.

## D20 — Repo publik: DIJALANKAN 2026-09-04, setelah gerbangnya lulus

Izin user diberikan **2026-08-31**, eksekusinya ditahan sampai gerbangnya ada. Gerbang itu
lahir di P12 dan lulus **2026-09-04**:

- **A12** `make audit` → `KELAS RAHASIA : 0 kebocoran`, exit 0, di repo utama (91 berkas,
  mode `git ls-files`) **dan** salinan bersih (92 berkas, mode walk pohon kerja). Riwayat
  commit ikut dipindai: 52.847 baris diff, 0 kecocokan untuk 7 pola kunci.
- **A11** `LAB_PORT=8101 make all` di `/tmp/driftwatch-clean` → exit 0 dalam 1.086 detik,
  1.323 record, 0 pemanggilan `docker`; `make oracles` 11/11; `make test` 48/48.

User ditanya **sekali lagi** setelah keduanya hijau, sesuai urutan yang dikunci entri ini,
dan menjawab **"balik jadi publik sekarang"**. Flip dijalankan dengan akun personal
`rayinailham` (`gh auth status` → `Logged in to github.com account rayinailham`), **sesudah**
commit P12 di-push supaya repo tidak pernah publik dalam keadaan setengah jadi:

```console
$ gh repo view rayinailham/driftwatch --json visibility        # sebelum
PRIVATE
$ gh repo edit rayinailham/driftwatch --visibility public --accept-visibility-change-consequences
$ gh repo view rayinailham/driftwatch --json visibility,url    # sesudah
PUBLIC  https://github.com/rayinailham/driftwatch
```

**Konsekuensi yang diterima sadar, dan sudah disampaikan sebelum user memutuskan:**
`DRIFTWATCH_UA` memuat alamat email pribadi di 12 berkas ter-track. Itu **kelas IDENTITAS**,
bukan RAHASIA, dan D3 justru **mewajibkannya** (User-Agent jujur berisi kontak) — tetapi
sejak repo publik alamat itu bisa dipanen bot. Mengubahnya berarti mengubah D3, bukan
menambal repo.

---

## 🔓 Terbuka — wajib dikunci

| Kode | Pertanyaan | Dikunci di |
|---|---|---|
| ✅ D20 | Repo dijadikan publik? | **Ya — dijalankan 2026-09-04** setelah A11+A12 lulus dan user ditanya ulang. Tidak ada keputusan yang masih terbuka. |
