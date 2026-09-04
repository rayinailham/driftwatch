# DriftWatch — Bukti Soak 3 Hari (P9)

**Ditulis:** 2026-09-04 · **Jendela soak:** `2026-09-01` … `2026-09-03` (3 tanggal berturut-turut)
**`soak_dibuka`:** `2026-08-31` — di-reset oleh D24 karena `scripts/daily_run.sh` berubah hari itu.
**Kode yang berjalan selama soak:** `git:a11555c`, identik di keempat target × ketiga hari.

Semua blok di bawah adalah **output perintah apa adanya**, dijalankan 2026-09-04 pukul 07:2x WIB
dari `/home/rayin/Projects/Testing/driftwatch`.

---

## Pernyataan kejujuran

> **Tidak ada intervensi manual pada 2026-09-01, 2026-09-02, dan 2026-09-03.**

Ketiga run dipicu `driftwatch.timer` (`OnCalendar=*-*-* 09:00:00 Asia/Jakarta`,
`RandomizedDelaySec=300`, `Persistent=true`). Tidak ada `systemctl --user start
driftwatch.service` manual, tidak ada `src/scrape.py` dijalankan tangan, tidak ada perbaikan
kode di tengah jendela soak.

Empat bukti pendukung, masing-masing berdiri sendiri:

1. **Waktu mulai acak di dalam jendela timer.** `driftlab` (target pertama tiap run) mulai
   `09:00:53` · `09:03:07` · `09:03:54` — ketiganya di dalam `09:00:00 + RandomizedDelaySec=300`
   dan berbeda tiap hari. Itu tanda tangan `RandomizedDelaySec`, bukan pola perintah manusia.
2. **Tidak ada berkas kode yang berubah selama jendela soak** (blok 7). `mtime` terbaru di
   `scripts/` adalah `2026-08-31 11:22` (`daily_run.sh`), di `src/` adalah `2026-08-31 11:22`
   — dua-duanya **sebelum** soak dimulai.
3. **`code_version` identik di 12 `run.json`** — semua `git:a11555c` (blok 5b).
4. **Watchdog H+1 independen mengonfirmasi run kemarin ada** (blok 1d).

### ⚠️ Satu batas bukti yang dinyatakan terbuka

`journalctl` **hanya membuktikan 2 dari 3 pemicuan secara langsung** (2026-09-02 dan
2026-09-03) — bukan karena run 2026-09-01 tidak terjadi, melainkan karena **jurnal mesin ini
tidak menjangkau sejauh itu**. Entri jurnal user paling awal yang masih tersimpan adalah
`2026-09-01T20:53:14+07:00` (blok 1c), yakni **sesudah** run pukul 09:00 hari itu; boot yang
memuat run tersebut sudah tergilas rotasi (`journalctl --user --disk-usage` = 22,8 MB).

Pemicuan **2026-09-01 karena itu dibuktikan tidak langsung**, oleh tiga artefak yang lahir
dari run itu sendiri:

- `run.json` keempat target: `exit=0`, mulai `09:00:53`–`09:18:49` (blok 5b);
- folder `data/<target>/2026-09-01/` dan `reports/<target>/2026-09-01/` lengkap (blok 2, 4b);
- baris watchdog `check 2026-09-01: RUN_MISSING=[]` × 4 target pada 2026-09-02 10:01 (blok 1d).

Bukti itu kuat dan konsisten, tetapi **bukan baris `journalctl`** — dan dokumen ini tidak
mengakuinya sebagai baris `journalctl`.

## Alarm selama soak

**Nihil.** `reports/alerts.jsonl` tidak memuat satu pun baris dengan `date >= "2026-09-01"`
(blok 6). Baris terakhir di berkas itu bertanggal `2026-08-31`, seluruhnya sudah ber-`resolved_at`
`2026-08-31T11:22:36+07:00` — ditutup oleh perbaikan D24, bukan dihapus.

---

## 1. Berapa kali unit benar-benar dipicu

`phases/phase-09-soak.md` menulis pola `"Started DriftWatch"`. Pola itu **salah** untuk unit
`Type=oneshot`: systemd mencetak `Starting …` saat mulai dan `Finished …` saat selesai —
`Started` hanya dicetak untuk *timer*-nya. Pola yang dipakai di sini `"Starting DriftWatch"`.

```console
$ journalctl --user -u driftwatch.service --since "6 days ago" -o short-iso \
    | grep -c "Starting DriftWatch"
2
```

### 1b. Baris mentahnya

```console
$ journalctl --user -u driftwatch.service --since "6 days ago" -o short-iso \
    | grep -E "Starting DriftWatch|Finished"
2026-09-02T09:03:07+07:00 tarnished systemd[848]: Starting DriftWatch daily harvest...
2026-09-02T09:21:24+07:00 tarnished systemd[848]: Finished DriftWatch daily harvest.
2026-09-03T09:03:54+07:00 tarnished systemd[838]: Starting DriftWatch daily harvest...
2026-09-03T09:22:20+07:00 tarnished systemd[838]: Finished DriftWatch daily harvest.
```

### 1c. Batas jangkauan jurnal — kenapa 2026-09-01 tidak muncul

```console
$ journalctl --user -o short-iso --no-pager | head -1
2026-09-01T20:53:14+07:00 tarnished systemd[832]: Queued start job for default target Main User Target.
```

Entri jurnal user paling awal yang masih ada bertanggal 2026-09-01 **pukul 20:53** — sesudah
run pukul 09:00. Jurnal sebelum titik itu sudah tergilas rotasi, jadi ketiadaan baris
2026-09-01 adalah keterbatasan jurnal, bukan run yang hilang.

### 1d. Watchdog H+1 (D23) — konfirmasi independen bahwa run kemarin ada

```console
$ journalctl --user -u driftwatch-watchdog.service -o short-iso --no-pager \
    | grep -E "RUN_MISSING|Starting|Finished"
2026-09-02T10:01:33+07:00 tarnished systemd[848]: Starting DriftWatch missing-run watchdog...
2026-09-02T10:01:33+07:00 tarnished env[182532]: check 2026-09-01: RUN_MISSING=[]
2026-09-02T10:01:33+07:00 tarnished env[182540]: check 2026-09-01: RUN_MISSING=[]
2026-09-02T10:01:33+07:00 tarnished env[182544]: check 2026-09-01: RUN_MISSING=[]
2026-09-02T10:01:33+07:00 tarnished env[182548]: check 2026-09-01: RUN_MISSING=[]
2026-09-02T10:01:33+07:00 tarnished systemd[848]: Finished DriftWatch missing-run watchdog.
2026-09-03T10:02:54+07:00 tarnished systemd[838]: Starting DriftWatch missing-run watchdog...
2026-09-03T10:02:54+07:00 tarnished env[13094]: check 2026-09-02: RUN_MISSING=[]
2026-09-03T10:02:54+07:00 tarnished env[13102]: check 2026-09-02: RUN_MISSING=[]
2026-09-03T10:02:54+07:00 tarnished env[13110]: check 2026-09-02: RUN_MISSING=[]
2026-09-03T10:02:54+07:00 tarnished env[13118]: check 2026-09-02: RUN_MISSING=[]
2026-09-03T10:02:54+07:00 tarnished systemd[838]: Finished DriftWatch missing-run watchdog.
```

Baris `check 2026-09-01: RUN_MISSING=[]` ini dicetak oleh systemd pada 2026-09-02 10:01 —
mesin itu sendiri menyatakan run 2026-09-01 lengkap untuk keempat target, jauh sebelum
sesi ini membuka berkasnya.

---

## 2. Tanggal folder data yang lahir, per target

```console
$ for T in driftlab books quotes seo; do echo "== $T"; ls -1 data/$T/ | tail -5; done
== driftlab
2026-08-30
2026-08-31
2026-09-01
2026-09-02
2026-09-03
== books
2026-08-30
2026-08-31
2026-09-01
2026-09-02
2026-09-03
== quotes
2026-08-30
2026-08-31
2026-09-01
2026-09-02
2026-09-03
== seo
2026-08-30
2026-08-31
2026-09-01
2026-09-02
2026-09-03
```

---

## 3. Tanggal harus BERURUTAN, bukan sekadar ada 3

```console
$ ls -1 data/books/ | tail -3
2026-09-01
2026-09-02
2026-09-03
```

`2026-09-01`, `2026-09-02`, `2026-09-03` — berturut-turut tanpa lompatan.

---

## 4. Tiap tanggal punya diff dan digest

```console
$ ls -1 reports/books/*/diff.json | tail -3
$ ls -1 reports/books/*/daily.md  | tail -3
reports/books/2026-09-01/diff.json
reports/books/2026-09-02/diff.json
reports/books/2026-09-03/diff.json

reports/books/2026-09-01/daily.md
reports/books/2026-09-02/daily.md
reports/books/2026-09-03/daily.md
```

### 4b. Diperluas ke keempat target × ketiga tanggal (A7)

```console
$ for T in books quotes seo driftlab; do for D in 2026-09-01 2026-09-02 2026-09-03; do
    printf "%-9s %s diff=%s daily=%s\n" "$T" "$D" \
      "$([ -f reports/$T/$D/diff.json ] && echo ADA || echo TIDAK)" \
      "$([ -f reports/$T/$D/daily.md  ] && echo ADA || echo TIDAK)"; done; done
books     2026-09-01 diff=ADA daily=ADA
books     2026-09-02 diff=ADA daily=ADA
books     2026-09-03 diff=ADA daily=ADA
quotes    2026-09-01 diff=ADA daily=ADA
quotes    2026-09-02 diff=ADA daily=ADA
quotes    2026-09-03 diff=ADA daily=ADA
seo       2026-09-01 diff=ADA daily=ADA
seo       2026-09-02 diff=ADA daily=ADA
seo       2026-09-03 diff=ADA daily=ADA
driftlab  2026-09-01 diff=ADA daily=ADA
driftlab  2026-09-02 diff=ADA daily=ADA
driftlab  2026-09-03 diff=ADA daily=ADA
```

12 dari 12 lengkap.

---

## 5. Status run tiap hari

```console
$ for D in $(ls -1 data/books/ | tail -3); do echo -n "$D  "; \
    jq -r '"exit=\(.exit_code) records=\(.records_unique) durasi=\(.duration_sec)"' \
    data/books/$D/run.json; done
2026-09-01  exit=0 records=1000 durasi=1053.172
2026-09-02  exit=0 records=1000 durasi=1051.632
2026-09-03  exit=0 records=1000 durasi=1059.578
```

### 5b. Keempat target × ketiga tanggal, dengan waktu mulai dan versi kode

```console
$ for T in books quotes seo driftlab; do for D in 2026-09-01 2026-09-02 2026-09-03; do
    printf "%-9s %s  " "$T" "$D"
    jq -r '"exit=\(.exit_code) records=\(.records_unique) durasi=\(.duration_sec) mulai=\(.started_at) kode=\(.code_version)"' \
      data/$T/$D/run.json; done; done
books     2026-09-01  exit=0 records=1000 durasi=1053.172 mulai=2026-09-01T09:01:04+07:00 kode=git:a11555c
books     2026-09-02  exit=0 records=1000 durasi=1051.632 mulai=2026-09-02T09:03:19+07:00 kode=git:a11555c
books     2026-09-03  exit=0 records=1000 durasi=1059.578 mulai=2026-09-03T09:04:06+07:00 kode=git:a11555c
quotes    2026-09-01  exit=0 records=100 durasi=10.145 mulai=2026-09-01T09:18:38+07:00 kode=git:a11555c
quotes    2026-09-02  exit=0 records=100 durasi=10.054 mulai=2026-09-02T09:20:51+07:00 kode=git:a11555c
quotes    2026-09-03  exit=0 records=100 durasi=10.328 mulai=2026-09-03T09:21:47+07:00 kode=git:a11555c
seo       2026-09-01  exit=0 records=23 durasi=22.468 mulai=2026-09-01T09:18:49+07:00 kode=git:a11555c
seo       2026-09-02  exit=0 records=23 durasi=22.445 mulai=2026-09-02T09:21:01+07:00 kode=git:a11555c
seo       2026-09-03  exit=0 records=23 durasi=22.507 mulai=2026-09-03T09:21:57+07:00 kode=git:a11555c
driftlab  2026-09-01  exit=0 records=200 durasi=10.886 mulai=2026-09-01T09:00:53+07:00 kode=git:a11555c
driftlab  2026-09-02  exit=0 records=200 durasi=10.977 mulai=2026-09-02T09:03:07+07:00 kode=git:a11555c
driftlab  2026-09-03  exit=0 records=200 durasi=11.487 mulai=2026-09-03T09:03:54+07:00 kode=git:a11555c
```

**12/12 run `exit=0`.** Jumlah record stabil di baseline P6 tiap hari: books 1.000 ·
driftlab 200 · quotes 100 · seo 23 = **1.323 record/hari × 3 hari**. `kode` identik
(`git:a11555c`) → tidak ada kode yang diganti di tengah soak.

---

## 6. Alarm yang muncul selama soak

```console
$ jq -r 'select(.date >= "2026-09-01") | "\(.date) \(.target) \(.code) \(.severity)"' \
    reports/alerts.jsonl
(exit=0)
```

Keluaran kosong, exit 0 → **nihil alarm selama 2026-09-01 … 2026-09-03**.

---

## 7. Bukti tambahan: tidak ada berkas kode yang disentuh selama soak

```console
$ ls -la --time-style=long-iso scripts/ | grep -E 'daily_run|lab_up|lab_down'
$ ls -la --time-style=long-iso src/    | grep -E 'alarm.py|report.py|scrape.py|publish.py'
-rwxr-xr-x 1 rayin rayin 3932 2026-08-31 11:22 daily_run.sh
-rwxr-xr-x 1 rayin rayin  767 2026-08-28 08:56 lab_down.sh
-rwxr-xr-x 1 rayin rayin  922 2026-08-27 04:07 lab_up.sh
-rw-r--r-- 1 rayin rayin 16211 2026-08-31 11:20 alarm.py
-rw-r--r-- 1 rayin rayin 11088 2026-08-28 08:44 publish.py
-rw-r--r-- 1 rayin rayin 24342 2026-08-31 11:20 report.py
-rw-r--r-- 1 rayin rayin 15453 2026-08-28 08:46 scrape.py
-rw-r--r-- 1 rayin rayin  8642 2026-08-31 11:21 test_diff_alarm.py
-rw-r--r-- 1 rayin rayin  1941 2026-08-28 08:46 test_publish.py
-rw-r--r-- 1 rayin rayin 11040 2026-08-28 14:02 test_report.py
-rw-r--r-- 1 rayin rayin  7629 2026-08-28 09:07 test_scrape.py
```

Seluruh `mtime` berhenti di `2026-08-31` atau lebih awal — tidak ada satu pun berkas kode
yang ditulis pada 2026-09-01, 09-02, atau 09-03.

---

## Metrik selesai P9

`3 run terjadwal (2 terbukti langsung di journalctl + 1 terbukti lewat artefak run & watchdog)
· 3 tanggal berturut · 4/4 target tiap tanggal · 12/12 run exit 0 · 1.323 record/hari
· 0 alarm · 0 intervensi manual`
