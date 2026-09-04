# DriftWatch

**Pipeline scraping yang memantau dirinya sendiri: mengambil data tiap pagi, membandingkannya
dengan kemarin, dan berteriak duluan saat situs sumber berubah — sebelum klien yang menemukan
datanya salah.**

---

## 1. Apa yang dilakukan

1. **Panen harian otomatis.** systemd timer 09:00 WIB memanen 4 situs — 1.323 record/hari —
   tanpa satu pun perintah manual. Terbukti jalan sendiri 3 hari berturut, 12/12 run `exit 0`.
2. **Tahan diputus.** Run yang dibunuh di tengah jalan bisa dilanjutkan `--resume` dari
   checkpoint SQLite: terbukti **12 → 1.000 record, 0 duplikat**, tidak ada halaman diambil dua kali.
3. **Diff harian, bukan sekadar dump.** Tiap record punya `content_hash`; pipeline tahu persis
   mana yang **baru**, **berubah**, dan **hilang** dibanding run sukses terakhir.
4. **Alarm yang sudah dibuktikan patah.** 10 kode alarm dengan ambang tertulis. Diuji lewat
   11 skenario kerusakan yang sengaja ditanam di fixture lokal → **11/11 lolos, 0 false positive**.
5. **Laporan yang bisa dibaca klien.** Digest harian tanpa jargon + `REPORT.xlsx` 5 sheet +
   halaman demo statis, semuanya lahir dari run yang sama tanpa pengawasan manusia.

---

## 2. Etika scraping

> Bagian ini sengaja diletakkan sebelum cara instalasi. Klien serius membaca bagian ini
> lebih dulu, dan itu yang membedakan pipeline yang bertahan setahun dari pipeline yang
> diblokir bulan depan.

### Aturan yang selalu berlaku

Disalin apa adanya dari [`docs/ETHICS.md`](docs/ETHICS.md) §1:

1. **Cek `robots.txt` sebelum request kedua.** Hasilnya dicatat di `recon.json`.
2. **Hormati `Crawl-delay`.** Kalau tidak disebut, pakai 1,0 detik per request per host.
   Tidak pernah lebih cepat dari itu untuk host publik.
3. **User-Agent jujur + kontak.** `DriftWatch/1.0 (+mailto:rayinailham9@gmail.com)`.
   Dilarang menyamar sebagai browser untuk mengelabui target.
4. **Concurrency maksimum 3** untuk host publik.
5. **Ambil metadata, bukan karya.** Untuk situs pihak ketiga: judul, H1, meta description,
   tanggal, jumlah kata, jumlah link, URL. Bukan isi artikel, bukan gambar, bukan HTML penuh.
6. **Tidak menembus apa pun.** Tidak ada captcha solver, bypass Cloudflare, stealth
   fingerprinting, atau rotasi proxy untuk menghindari rate limit.
7. **Tidak login ke akun milik orang lain.** Kalau klien minta scraping di balik login,
   minta konfirmasi tertulis bahwa mereka berwenang atas akun dan target itu.
8. **Berhenti kalau diminta berhenti.** HTTP 429 berulang, atau blokir IP, diperlakukan
   sebagai penolakan — pipeline berhenti dan melapor, bukan mencari jalan lain.

Pipeline ini mengawasi kesopanannya sendiri: pelanggaran jeda yang terdeteksi memicu alarm
`RATE_LIMIT_VIOLATION` pada run itu juga.

### Kalimat yang dipakai ke klien

Disalin apa adanya dari [`docs/ETHICS.md`](docs/ETHICS.md) §4:

> "Sebelum menulis kode, saya cek `robots.txt` dan ToS target. Kalau target melarang
> automated access, saya akan bilang di depan dan menawarkan jalur lain (API resmi,
> data partner, atau sumber alternatif) — bukan diam-diam menembusnya. Untuk situs yang
> boleh, saya jalan 1 request/detik dengan User-Agent yang bisa Anda tunjukkan ke mereka
> kalau ditanya. Itu yang membuat pipeline Anda tidak diblokir bulan depan."

---

## 3. Cara menjalankan

```bash
git clone <repo> driftwatch && cd driftwatch
cp .env.example .env          # ANTHROPIC_API_KEY boleh dibiarkan kosong
make all
```

`make all` = `setup` → `lab-up` → `harvest` → `diff` → `report` → `publish`.

**Tidak butuh Docker.** Fixture uji dilayani `http.server` stdlib, checkpoint memakai SQLite,
laporan memakai `openpyxl` — tidak ada satu pun langkah `make all` yang memanggil `docker`,
MySQL, Redis, atau layanan jaringan lain. Satu-satunya prasyarat adalah Python ≥ 3.12 dan
[`uv`](https://docs.astral.sh/uv/).

| Perintah | Kerjanya |
|---|---|
| `make setup` | `uv sync` + generate fixture DriftLab |
| `make lab-up` / `make lab-down` | nyalakan / matikan fixture lokal (port `LAB_PORT`, default 8100) |
| `make harvest` | panen 4 target: scrape → validate → export CSV |
| `make diff` | bandingkan dengan baseline + evaluasi 10 kode alarm |
| `make report` | digest harian `daily.md` + `REPORT.xlsx` mingguan |
| `make publish` | perbarui halaman demo `web/index.html` |
| `make oracles` | 11 skenario kerusakan → wajib 11/11 |
| `make test` | 48 unit test |
| `make audit` | pemindaian kebocoran rahasia → wajib 0 |

Menjalankan di mesin yang fixture-nya sudah terpakai? `LAB_PORT=8101 make all`.

Penjadwalan harian memakai systemd user timer (`deploy/driftwatch.timer`, 09:00 WIB,
`Persistent=true` sehingga run yang terlewat dikejar saat mesin menyala) plus watchdog H+1
pukul 10:00 yang berteriak kalau timer utama mati total.

---

## 4. Bentuk data

Tiap run menulis ke `data/<target>/<YYYY-MM-DD>/` dan **tidak pernah menimpa snapshot kemarin** —
menimpanya berarti menghapus baseline diff, yaitu bukti utama project ini.

| Berkas | Isi |
|---|---|
| `records.jsonl` | sumber data utama, satu record per baris |
| `records.csv` | turunan `records.jsonl`, `utf-8-sig` supaya langsung terbaca Excel |
| `run.json` | manifest: `exit_code`, `records_unique`, `duplicates_rejected`, `errors`, `retries`, `http_status_counts`, `field_completeness`, `rate_limit`, `code_version` |
| `reports/<target>/<tanggal>/diff.json` | `added` / `changed` / `removed` / `unchanged` + kode alarm |
| `reports/<target>/<tanggal>/daily.md` | digest untuk manusia, tanpa jargon |
| `reports/alerts.jsonl` | riwayat alarm, append-only; baris yang sembuh diberi `resolved_at`, tidak pernah dihapus |

Empat target, 31 field kontrak (27 wajib), semuanya beserta tipe, contoh nyata, dan asal
elemennya: **[`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md)**. Bentuk berkasnya dikunci
di [`docs/SCHEMA.md`](docs/SCHEMA.md); field kosong wajib punya `missing_reason` — "kosong tanpa
keterangan" dihitung cacat data, bukan data.

---

## 5. Bukti

Klaim di README ini punya perintah pembuktinya masing-masing di
[`docs/ACCEPTANCE.md`](docs/ACCEPTANCE.md) — dengan output perintahnya, bukan klaim.

| Bukti | Angka | Berkas |
|---|---|---|
| Video 60 detik: dibunuh `kill -9` → `--resume` → alarm berbunyi → halaman demo | 1920×1080, tanpa audio | [`assets/v1_resume_demo.mp4`](assets/v1_resume_demo.mp4) |
| Arsitektur pipeline | — | [`assets/v2_architecture.png`](assets/v2_architecture.png) |
| Timeline diff 8 hari × 4 target | termasuk hari gagal, tidak disembunyikan | [`assets/v3_diff_timeline.png`](assets/v3_diff_timeline.png) |
| Matriks alarm | **11/11 PASS · 0 false positive** | [`assets/v4_alarm_matrix.png`](assets/v4_alarm_matrix.png) |
| Turun lapis engine | **8 request browser → 1 request httpx** | [`assets/v5_tier_drop.png`](assets/v5_tier_drop.png) |
| Studi kasus satu halaman | — | [`assets/v6_case_study.pdf`](assets/v6_case_study.pdf) |
| Soak 3 hari tanpa disentuh | 3 tanggal berturut · 12/12 run `exit 0` · 0 alarm · 0 intervensi | [`docs/SOAK_PROOF.md`](docs/SOAK_PROOF.md) |
| Kill → resume | **12 → 1.000 record, 0 duplikat** | [`docs/RESUME_PROOF.md`](docs/RESUME_PROOF.md) |
| 3 record dicek manual ke halaman aslinya | 3/3 cocok field demi field | [`docs/MANUAL_VERIFY.md`](docs/MANUAL_VERIFY.md) |
| 11 skenario drift | definisi + ambang tiap kode alarm | [`docs/DRIFT_ORACLES.md`](docs/DRIFT_ORACLES.md) |

---

## 6. Batasan yang jujur

Diambil dari [`docs/ACCEPTANCE.md`](docs/ACCEPTANCE.md) §D. Bagian ini terasa berlawanan
dengan naluri menjual, dan justru itu yang membuat bagian 1–5 layak dipercaya.

**Yang project ini tidak lakukan:**

- Tidak ada dashboard interaktif, autentikasi multi-user, database eksternal
  (Postgres/MySQL/TiDB), antrian pekerjaan, deployment ke cloud, atau UI admin.
  Checkpoint tetap SQLite dan laporan tetap `openpyxl` supaya jalan tanpa pengawasan di
  mesin klien — bukan karena tidak bisa, tapi karena setiap layanan tambahan jadi syarat
  pasang di mesin mereka.
- Tidak menembus captcha, Cloudflare, atau WAF. Tidak scraping situs yang ToS-nya melarang.
  Tidak meredistribusi konten berhak cipta. Tidak mengambil data pribadi perorangan.
- **Halaman demo tidak punya URL publik.** `web/index.html` adalah berkas mandiri yang dibuka
  lewat `file://`; buktinya berupa halaman yang dirender lokal, bukan tautan yang bisa dibuka
  orang lain.
- **Target `seo` hanya 23 URL** (dokumentasi HTTPX). Dipilih justru karena beban host publiknya
  paling kecil di antara kandidat yang lolos gerbang etika — bukan karena pipeline tidak
  sanggup lebih.
- **Dibangun untuk Linux + systemd.** Tidak ada dukungan Windows/macOS, dan penjadwalannya
  memakai systemd user timer, bukan cron.
- **Ringkasan AI opsional dan mati secara default.** Tanpa `ANTHROPIC_API_KEY`, halaman demo
  tetap terbit lengkap dengan angka dan tabel; hanya blok ringkasannya kosong. Blok itu
  selalu berlabel jelas bahwa isinya dibuat AI.
- Bukan target: menambah situs kelima dan seterusnya. Empat target sudah membuktikan
  seluruh klaim di atas.
