# P9 — Soak 3 Hari

**Tujuan sesi:** membuktikan pipeline jalan sendiri **3 hari berturut-turut tanpa disentuh**.

**Prasyarat:** P7 selesai (timer aktif, `soak_dibuka` tercatat).
**Read-set:** `STATE.md` + file ini saja.
**Budget:** sangat ringan. Ini gerbang, bukan sesi kerja.

---

## Cara kerja fase ini

Fase ini **tidak dikerjakan**, ia **ditunggu**. Aturannya:

1. Buka `STATE.md`, baca `soak_dibuka`.
2. Hitung umur soak = hari ini − `soak_dibuka`.
3. **Kalau < 3 hari data berturut:** fase ini dilewat. Kerjakan fase tersedia berikutnya
   (P8, P10, atau P11) dan biarkan timer terus jalan. Ini bukan kemunduran — memang begitu
   rancangannya (`PLAN.md` §Ketergantungan).
4. **Kalau ≥ 3 hari berturut:** kumpulkan bukti di bawah, centang DoD, tutup.

---

## Perintah pengumpul bukti

```bash
# 1. berapa kali unit benar-benar jalan
# KOREKSI 2026-09-04: unit bertipe `oneshot` → systemd mencetak "Starting …" lalu "Finished …".
# "Started DriftWatch" hanya dicetak untuk TIMER-nya, bukan service-nya, jadi pola lama selalu 0.
journalctl --user -u driftwatch.service --since "6 days ago" -o short-iso \
  | grep -c "Starting DriftWatch"

# 2. tanggal folder data yang lahir, per target
for T in driftlab books quotes seo; do echo "== $T"; ls -1 data/$T/ | tail -5; done

# 3. tanggal harus BERURUTAN, bukan sekadar ada 3
ls -1 data/books/ | tail -3

# 4. tiap tanggal punya diff dan digest
ls -1 reports/books/*/diff.json | tail -3
ls -1 reports/books/*/daily.md  | tail -3

# 5. status run tiap hari
for D in $(ls -1 data/books/ | tail -3); do
  echo -n "$D  "; jq -r '"exit=\(.exit_code) records=\(.records_unique) durasi=\(.duration_sec)"' \
    data/books/$D/run.json
done

# 6. alarm yang muncul selama soak (kalau ada, jelaskan — jangan disembunyikan)
jq -r 'select(.date >= "<soak_dibuka>") | "\(.date) \(.target) \(.code) \(.severity)"' \
  reports/alerts.jsonl
```

---

## Aturan kejujuran

- **"Tanpa disentuh" berarti tanpa disentuh.** Kalau selama 3 hari itu ada intervensi
  manual (restart unit, jalankan `scrape.py` tangan, perbaiki bug), soak **diulang dari nol**
  dan tanggal `soak_dibuka` diperbarui. Klaim ini adalah salah satu dari tiga bukti utama
  portofolio; mengarangnya membatalkan nilai seluruh project.
- Kalau ada hari yang gagal, itu **boleh** — asalkan dilaporkan apa adanya beserta alarmnya.
  Pipeline yang gagal lalu melaporkan kegagalannya justru membuktikan alarm bekerja.
  Yang tidak boleh adalah hari gagal yang tidak terlihat di mana pun.
- Kalau mesin mati semalam dan `Persistent=true` mengejar run yang terlewat: itu **bukti
  bagus**, bukan cacat. Catat sebagai bukti terpisah — ini persis klaim "tahan mati listrik".

---

## Output fase
- `docs/SOAK_PROOF.md` — output keenam perintah di atas, apa adanya, dengan tanggalnya

## Definition of Done

Dicentang 2026-09-04. Bukti lengkap apa adanya di `docs/SOAK_PROOF.md`.

- [x] `soak_dibuka` di `STATE.md` berjarak ≥ 3 hari dari hari ini
      — `soak_dibuka = 2026-08-31`, hari ini `2026-09-04`; jendela sah `2026-09-01 … 2026-09-03`.
- [x] **3 tanggal berturut-turut** punya folder data untuk keempat target
      ```console
      $ ls -1 data/books/ | tail -3
      2026-09-01
      2026-09-02
      2026-09-03
      ```
      Sama persis untuk `quotes`, `seo`, `driftlab` (SOAK_PROOF blok 2).
- [~] `journalctl` menunjukkan unit dipicu ≥ 3 kali oleh **timer** (bukan `start` manual)
      — **terbukti langsung 2 dari 3.** Pola fase ini (`"Started DriftWatch"`) salah untuk unit
      `Type=oneshot`; pola benarnya `"Starting DriftWatch"`:
      ```console
      $ journalctl --user -u driftwatch.service --since "6 days ago" -o short-iso \
          | grep -c "Starting DriftWatch"
      2
      ```
      ```console
      $ journalctl --user -u driftwatch.service --since "6 days ago" -o short-iso \
          | grep -E "Starting DriftWatch|Finished"
      2026-09-02T09:03:07+07:00 tarnished systemd[848]: Starting DriftWatch daily harvest...
      2026-09-02T09:21:24+07:00 tarnished systemd[848]: Finished DriftWatch daily harvest.
      2026-09-03T09:03:54+07:00 tarnished systemd[838]: Starting DriftWatch daily harvest...
      2026-09-03T09:22:20+07:00 tarnished systemd[838]: Finished DriftWatch daily harvest.
      ```
      Pemicuan `2026-09-01` **tidak ada di jurnal karena jurnalnya sendiri tidak menjangkau
      sejauh itu**, bukan karena run-nya tidak terjadi:
      ```console
      $ journalctl --user -o short-iso --no-pager | head -1
      2026-09-01T20:53:14+07:00 tarnished systemd[832]: Queued start job for default target Main User Target.
      ```
      Run `2026-09-01` dibuktikan tidak langsung oleh watchdog H+1 milik systemd sendiri:
      ```console
      $ journalctl --user -u driftwatch-watchdog.service -o short-iso --no-pager | grep RUN_MISSING
      2026-09-02T10:01:33+07:00 tarnished env[182532]: check 2026-09-01: RUN_MISSING=[]
      2026-09-02T10:01:33+07:00 tarnished env[182540]: check 2026-09-01: RUN_MISSING=[]
      2026-09-02T10:01:33+07:00 tarnished env[182544]: check 2026-09-01: RUN_MISSING=[]
      2026-09-02T10:01:33+07:00 tarnished env[182548]: check 2026-09-01: RUN_MISSING=[]
      2026-09-03T10:02:54+07:00 tarnished env[13094]: check 2026-09-02: RUN_MISSING=[]
      ...
      ```
      ditambah `run.json` keempat target 2026-09-01 (`exit=0`, mulai `09:00:53`–`09:18:49`,
      di dalam jendela `09:00:00 + RandomizedDelaySec=300`). Kotak ini sengaja **tidak** ditulis
      `[x]`: klaimnya benar, tapi salah satu dari tiga pemicuan tidak punya baris `journalctl`.
- [x] Tiap tanggal punya `diff.json` dan `daily.md` (A7)
      ```console
      $ for T in books quotes seo driftlab; do for D in 2026-09-01 2026-09-02 2026-09-03; do ... done; done
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
      12/12 lengkap.
- [x] Tidak ada intervensi manual selama periode itu — dinyatakan eksplisit di `docs/SOAK_PROOF.md`
      — pernyataannya ada di §"Pernyataan kejujuran". Tiga bukti pendukung yang bisa diperiksa:
      `code_version` = `git:a11555c` di **12/12** `run.json`; `mtime` terbaru di `scripts/` dan
      `src/` berhenti di `2026-08-31 11:22` (sebelum soak); waktu mulai acak `09:00:53` ·
      `09:03:07` · `09:03:54` — tanda tangan `RandomizedDelaySec`, bukan pola tangan manusia.
- [x] Alarm yang muncul selama soak dijelaskan satu per satu (atau dinyatakan "nihil")
      ```console
      $ jq -r 'select(.date >= "2026-09-01") | "\(.date) \(.target) \(.code) \(.severity)"' \
          reports/alerts.jsonl
      (keluaran kosong, exit 0)
      ```
      **Nihil.** Baris terakhir `alerts.jsonl` bertanggal `2026-08-31` dan semuanya sudah
      ber-`resolved_at` `2026-08-31T11:22:36+07:00` (ditutup D24, tidak dihapus).
- [x] **Commit + push berhasil** (D19) — commit `P09: bukti soak 3 hari timer harian`.

## Metrik selesai
`3 run terjadwal (2 terbukti langsung di journalctl + 1 lewat watchdog H+1 & run.json)
· 3 tanggal berturut · 4/4 target tiap tanggal · 12/12 run exit 0 · 1.323 record/hari
· 0 alarm · 0 intervensi manual`

## Jebakan
- Jangan menghitung `systemctl --user start` manual sebagai bukti timer. Yang dihitung
  hanya pemicuan oleh timer.
- Jangan "memperbaiki" sesuatu di tengah soak lalu tetap mengklaim 3 hari. Ulangi.
- Jangan menunggu dengan menganggur. Fase ini dirancang berjalan **di latar** sementara
  P8, P10, P11 dikerjakan.

## Sebelum menutup sesi
1. Centang DoD dengan output nyata.
2. Update `STATE.md`: P9 ✅, tanggal soak, jumlah run.
3. `git add -A && git commit -m "P09: bukti soak 3 hari timer harian" && git push`
