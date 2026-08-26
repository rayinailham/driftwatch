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
journalctl --user -u driftwatch.service --since "5 days ago" -o short-iso \
  | grep -c "Started DriftWatch"

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
- [ ] `soak_dibuka` di `STATE.md` berjarak ≥ 3 hari dari hari ini
- [ ] **3 tanggal berturut-turut** punya folder data untuk keempat target
- [ ] `journalctl` menunjukkan unit dipicu ≥ 3 kali oleh **timer** (bukan `start` manual)
- [ ] Tiap tanggal punya `diff.json` dan `daily.md` (A7)
- [ ] Tidak ada intervensi manual selama periode itu — dinyatakan eksplisit di `docs/SOAK_PROOF.md`
- [ ] Alarm yang muncul selama soak dijelaskan satu per satu (atau dinyatakan "nihil")
- [ ] **Commit + push berhasil** (D19)

## Metrik selesai
`N run terjadwal · 3 tanggal berturut · X alarm · 0 intervensi manual`

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
