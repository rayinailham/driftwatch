# DriftWatch — Drift Oracles (11 skenario)

Padanan `PLANTED_BUGS.md` di project 1. **Ini oracle untuk mengukur recall alarm,
bukan input detektor.** `src/diff.py` dan `src/alarm.py` tidak boleh tahu skenario mana
yang sedang aktif — kalau tahu, angka recall-nya palsu.

Dijalankan di atas fixture lokal `driftlab` (`127.0.0.1:8100`, D8) oleh
`scripts/drift_lab.py`. Fixture dasar: **200 item**, tiap item punya
`item_id`, `name`, `price`, `category`, `note`.

```bash
bash scripts/lab_up.sh                                  # http.server stdlib, bukan container (D8)
uv run python scripts/drift_lab.py --reset              # kembalikan ke keadaan dasar
uv run python scripts/drift_lab.py --scenario DO-04     # terapkan satu mutasi
uv run python scripts/drift_lab.py --verify             # wajib 11/11 skenario siap
make oracles                                            # jalankan semua 11, assert alarm
```

---

## Tabel oracle

| # | Skenario | Mutasi yang diterapkan | Alarm yang **wajib** terpicu (D4) | Severity |
|---|---|---|---|---|
| DO-01 | data bertambah | tambah 12 item baru | *tidak ada alarm*; `diff.counts.added == 12` | — |
| DO-02 | nilai berubah | ubah `price` di 4 item | *tidak ada alarm*; `changed == 4`, `fields_changed[].field == "price"` | — |
| DO-03 | data hilang | hapus 1 item | *tidak ada alarm*; `removed == 1` | — |
| DO-04 | **struktur patah** | ganti class `.item-card` → `.c-9f2a1` di semua halaman | `ZERO_RECORDS` + `RECORD_COUNT_DROP` | critical |
| DO-05 | field hilang sebagian | hapus `<h2 class="item-name">` di 30% halaman | `FIELD_COMPLETENESS_DROP` | critical |
| DO-06 | situs bermasalah | 15% request dibalas HTTP 503 (kait handler `lab_serve.py`) | `HTTP_ERROR_SPIKE` | critical |
| DO-07 | field asing muncul | tambah `data-promo` yang ikut terparse | `SCHEMA_UNKNOWN_FIELD` | warning |
| DO-08 | situs melambat | jeda 4 detik di 10% halaman (kait handler `lab_serve.py`) | `DURATION_ANOMALY` | warning |
| DO-09 | run terlewat | hapus folder run kemarin sebelum diff H+1 | `RUN_MISSING` | critical |
| DO-10 | restrukturisasi besar | ubah `category` di 40% item | `CHURN_SPIKE` | warning |
| DO-11 | scraper terlalu cepat | jalankan dengan `--delay 0.1` melawan `crawl_delay 1.0` | `RATE_LIMIT_VIOLATION` | warning |

`RUN_FAILED` tercakup sebagai efek samping DO-04 (`exit_code != 0` saat 0 record).
Kalau setelah implementasi ternyata tidak, tambahkan DO-12 khusus dan catat di `STATE.md`.

---

## Aturan pemakaian

1. **Satu skenario per run.** Menumpuk dua mutasi membuat penyebab alarm ambigu.
2. **Selalu `--reset` sebelum skenario berikutnya.** Kalau tidak, DO-05 akan mewarisi
   kerusakan DO-04 dan hasilnya tidak berarti.
3. Skenario ini **tidak pernah** dijalankan terhadap situs pihak ketiga. Hanya `driftlab`.
4. DO-06 dan DO-08 diterapkan lewat berkas penanda `fixtures/.scenario` yang dibaca
   handler `scripts/lab_serve.py` — **bukan** dengan mengubah kode scraper. Scraper tidak
   boleh tahu ia sedang diuji.
5. Fixture di-generate dari seed tetap (`--seed 1337`) supaya `driftlab` yang dibangun ulang
   di mesin lain menghasilkan 200 item yang identik. Tanpa itu, `make all` di salinan bersih
   tidak reproducible.
6. **Recall wajib 11/11 di P8.** Sepuluh dari sebelas memicu alarm; DO-01..DO-03 lulus dengan
   cara sebaliknya — mereka wajib **tidak** memicu alarm apa pun. Alarm yang berbunyi saat
   data normal (false positive) sama merusaknya dengan alarm yang diam saat rusak: klien
   berhenti membaca peringatan yang terlalu sering salah.

## Kenapa DO-01..DO-03 dihitung sebagai oracle

Karena "tidak berbunyi ketika seharusnya tidak" adalah persyaratan yang sama kerasnya.
Tiga skenario itu adalah uji false-positive: pipeline melihat 12 data baru, 4 berubah,
1 hilang — kondisi yang benar-benar normal untuk situs hidup — dan harus tetap melapor
`Status: SEHAT`.

## Format hasil `make oracles`

```
DO-01  added=12 changed=0 removed=0   alarms=[]                            PASS
DO-02  added=0  changed=4  removed=0   alarms=[]                           PASS
...
DO-04  records=0                       alarms=[ZERO_RECORDS,RECORD_COUNT_DROP]  PASS
...
11/11 PASS
```

Exit code 0 hanya kalau 11/11. Ini yang dipanggil di gerbang acceptance A8.
